const DEFAULT_BACKEND_URL = "http://localhost:8000";

function normalizeUrl(url) {
  const trimmed = (url || "").trim();
  if (!trimmed) {
    return DEFAULT_BACKEND_URL;
  }
  return trimmed.replace(/\/$/, "");
}

function getStorage(keys) {
  return new Promise((resolve) => {
    chrome.storage.local.get(keys, (result) => resolve(result));
  });
}

function setStorage(values) {
  return new Promise((resolve) => {
    chrome.storage.local.set(values, () => resolve());
  });
}

async function getSettings() {
  const data = await getStorage(["backendUrl", "authToken", "authEmail"]);
  return {
    backendUrl: normalizeUrl(data.backendUrl),
    authToken: data.authToken || "",
    authEmail: data.authEmail || "",
    hasToken: Boolean(data.authToken)
  };
}

async function apiRequest(path, options = {}) {
  const { backendUrl } = await getSettings();
  const response = await fetch(`${backendUrl}${path}`, options);
  let payload = null;

  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    const detail = payload && payload.detail ? payload.detail : `HTTP ${response.status}`;
    throw new Error(detail);
  }

  return payload;
}

async function registerUser(email, password) {
  return apiRequest("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
}

async function loginUser(email, password) {
  const loginResponse = await apiRequest("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });

  const token = loginResponse && loginResponse.access_token ? loginResponse.access_token : "";

  if (!token) {
    throw new Error("Login succeeded but no access token was returned.");
  }

  await setStorage({ authToken: token, authEmail: email });

  return { email, hasToken: true };
}

async function fetchProfileForToken(token) {
  const { backendUrl } = await getSettings();
  const response = await fetch(`${backendUrl}/auth/me`, {
    headers: {
      "Authorization": `Bearer ${token}`
    }
  });

  if (!response.ok) {
    throw new Error("Invalid web session token. Please login in the web app and try again.");
  }

  return response.json();
}

async function investigateText(content, authToken) {
  return apiRequest("/api/v3/investigate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${authToken}`
    },
    body: JSON.stringify({
      input_type: "text",
      content
    })
  });
}

function splitIntoCandidateClaims(text) {
  const normalized = (text || "").replace(/\s+/g, " ").trim();
  if (!normalized) {
    return [];
  }

  const parts = normalized.match(/[^.!?]+[.!?]?/g) || [normalized];
  const cleaned = parts.map((part) => part.trim()).filter(Boolean);
  const unique = [...new Set(cleaned)];

  if (unique.length <= 1) {
    return unique;
  }

  const meaningful = unique.filter((part) => part.length >= 12);
  return (meaningful.length ? meaningful : unique).slice(0, 8);
}

function noResultClaim(inputText) {
  return {
    claim: inputText,
    verdict: "no_result",
    confidence: 0,
    evidenceSummary: "No checkable claim was found in this text.",
    evidenceCount: 0,
    sourcesChecked: 0,
    processingTimeMs: 0,
    temporalContext: null,
    evidence: []
  };
}

function normalizeEvidenceUrl(sourceUrl, sourceDomain) {
  const rawUrl = String(sourceUrl || "").trim();
  const rawDomain = String(sourceDomain || "").trim();

  if (rawUrl.startsWith("http://") || rawUrl.startsWith("https://")) {
    return rawUrl;
  }

  if (rawDomain && rawDomain.includes(".") && !rawDomain.includes(" ")) {
    return `https://${rawDomain.replace(/^https?:\/\//, "")}`;
  }

  return null;
}

function mapEvidenceItem(item) {
  const domain = item && item.source_domain ? item.source_domain : "unknown";
  const sourceUrl = normalizeEvidenceUrl(item && item.source_url, domain);
  return {
    sourceUrl,
    sourceDomain: domain,
    sourceType: item && item.source_type ? item.source_type : "web_search",
    stance: item && item.stance ? item.stance : "neutral",
    stanceConfidence: item && item.stance_confidence ? Number(item.stance_confidence) : 0,
    trustScore: item && item.trust_score ? Number(item.trust_score) : 0,
    textPreview: item && item.text_preview ? item.text_preview : ""
  };
}

function mapVerifiedClaim(rawClaim, fallbackInput) {
  const rawEvidence = rawClaim && Array.isArray(rawClaim.evidence) ? rawClaim.evidence : [];
  const evidence = rawEvidence.map(mapEvidenceItem);
  return {
    claim: rawClaim.original_text || fallbackInput,
    verdict: rawClaim.verdict || "unknown",
    confidence: Number(rawClaim.confidence) || 0,
    evidenceSummary: rawClaim.evidence_summary || "No explanation returned.",
    evidenceCount: rawClaim.evidence_count || 0,
    sourcesChecked: rawClaim.sources_checked || 0,
    processingTimeMs: rawClaim.investigation_time_ms || 0,
    temporalContext: rawClaim.temporal_context || null,
    evidence
  };
}

async function verifyClaim(claimText) {
  const text = (claimText || "").trim();
  if (!text) {
    throw new Error("Select or enter a claim first.");
  }

  const { authToken } = await getSettings();
  if (!authToken) {
    const authError = new Error("Please login in the TruthLens extension popup first.");
    authError.code = "AUTH_REQUIRED";
    throw authError;
  }

  const segments = splitIntoCandidateClaims(text);
  if (!segments.length) {
    throw new Error("Could not detect any valid claim text to verify.");
  }

  const claims = [];
  const errors = [];

  if (segments.length === 1) {
    const response = await investigateText(segments[0], authToken);
    const verified = response && Array.isArray(response.verified_claims) ? response.verified_claims : [];
    if (!verified.length) {
      claims.push(noResultClaim(segments[0]));
    } else {
      verified.forEach((item) => claims.push(mapVerifiedClaim(item, segments[0])));
    }
  } else {
    const results = await Promise.allSettled(
      segments.map((segment) => investigateText(segment, authToken))
    );

    results.forEach((result, index) => {
      const sourceText = segments[index];
      if (result.status === "fulfilled") {
        const verified = result.value && Array.isArray(result.value.verified_claims)
          ? result.value.verified_claims
          : [];

        if (!verified.length) {
          claims.push(noResultClaim(sourceText));
          return;
        }

        verified.forEach((item) => claims.push(mapVerifiedClaim(item, sourceText)));
        return;
      }

      const reason = result.reason instanceof Error ? result.reason.message : "Unknown failure";
      errors.push(`"${sourceText.slice(0, 70)}": ${reason}`);
    });
  }

  if (!claims.length) {
    const errorMessage = errors.length
      ? `Could not verify selected text. ${errors[0]}`
      : "Could not verify selected text.";
    throw new Error(errorMessage);
  }

  const first = claims[0];

  return {
    input: text,
    segmentsAnalyzed: segments.length,
    claims,
    errors,
    claim: first.claim,
    verdict: first.verdict,
    confidence: first.confidence,
    evidenceSummary: first.evidenceSummary,
    evidenceCount: first.evidenceCount,
    sourcesChecked: first.sourcesChecked,
    processingTimeMs: first.processingTimeMs,
    temporalContext: first.temporalContext
  };
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (!message || !message.type) {
    sendResponse({ ok: false, error: "Invalid message." });
    return false;
  }

  (async () => {
    try {
      switch (message.type) {
        case "GET_SETTINGS": {
          const settings = await getSettings();
          sendResponse({ ok: true, data: settings });
          return;
        }
        case "SAVE_BACKEND_URL": {
          const backendUrl = normalizeUrl(message.backendUrl);
          await setStorage({ backendUrl });
          sendResponse({ ok: true, data: { backendUrl } });
          return;
        }
        case "REGISTER": {
          await registerUser(message.email, message.password);
          sendResponse({ ok: true, data: { registered: true } });
          return;
        }
        case "LOGIN": {
          const data = await loginUser(message.email, message.password);
          sendResponse({ ok: true, data });
          return;
        }
        case "SET_AUTH_TOKEN": {
          const token = String(message.token || "").trim();
          if (!token) {
            throw new Error("No token provided.");
          }

          const profile = await fetchProfileForToken(token);
          await setStorage({
            authToken: token,
            authEmail: profile && profile.email ? profile.email : ""
          });

          sendResponse({
            ok: true,
            data: {
              hasToken: true,
              authEmail: profile && profile.email ? profile.email : ""
            }
          });
          return;
        }
        case "LOGOUT": {
          await setStorage({ authToken: "", authEmail: "" });
          sendResponse({ ok: true, data: { hasToken: false } });
          return;
        }
        case "VERIFY_CLAIM": {
          const result = await verifyClaim(message.claim);
          sendResponse({ ok: true, data: result });
          return;
        }
        default:
          sendResponse({ ok: false, error: `Unknown message type: ${message.type}` });
      }
    } catch (error) {
      const messageText = error instanceof Error ? error.message : "Unexpected error";
      const code = error && typeof error === "object" && "code" in error ? error.code : undefined;
      sendResponse({ ok: false, error: messageText, code });
    }
  })();

  return true;
});

chrome.runtime.onInstalled.addListener(async () => {
  const current = await getSettings();
  if (!current.backendUrl) {
    await setStorage({ backendUrl: DEFAULT_BACKEND_URL });
  }
});
