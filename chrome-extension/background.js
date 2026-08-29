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
    chrome.storage.local.get(keys, (result) => {
      if (chrome.runtime.lastError) {
        console.error("Storage error:", chrome.runtime.lastError);
        resolve({});
        return;
      }
      resolve(result);
    });
  });
}

function setStorage(values) {
  return new Promise((resolve, reject) => {
    chrome.storage.local.set(values, () => {
      if (chrome.runtime.lastError) {
        console.error("Storage error:", chrome.runtime.lastError);
        reject(new Error(chrome.runtime.lastError.message));
      } else {
        resolve();
      }
    });
  });
}

async function getSettings() {
  const data = await getStorage(["backendUrl", "authToken", "authEmail"]);
  return {
    backendUrl: normalizeUrl(data.backendUrl),
    authToken: data.authToken || "",
    authEmail: data.authEmail || "",
    hasToken: Boolean(data.authToken),
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
    const detail =
      payload && payload.detail ? payload.detail : `HTTP ${response.status}`;
    throw new Error(detail);
  }

  return payload;
}

async function registerUser(email, password) {
  return apiRequest("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

async function loginUser(email, password) {
  const loginResponse = await apiRequest("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  const token =
    loginResponse && loginResponse.access_token
      ? loginResponse.access_token
      : "";

  if (!token) {
    throw new Error("Login succeeded but no access token was returned.");
  }

  try {
    await setStorage({ authToken: token, authEmail: email });
  } catch (error) {
    throw new Error(
      "Failed to save login credentials: " +
      (error instanceof Error ? error.message : "Unknown error"),
    );
  }

  return { email, hasToken: true };
}

async function fetchProfileForToken(token) {
  const { backendUrl } = await getSettings();
  const response = await fetch(`${backendUrl}/auth/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(
      "Invalid web session token. Please login in the web app and try again.",
    );
  }

  return response.json();
}

async function investigateText(content, authToken) {
  return apiRequest("/api/v3/investigate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${authToken}`,
    },
    body: JSON.stringify({
      input_type: "text",
      content,
    }),
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
    evidence: [],
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
    stanceConfidence:
      item && item.stance_confidence ? Number(item.stance_confidence) : 0,
    trustScore: item && item.trust_score ? Number(item.trust_score) : 0,
    textPreview: item && item.text_preview ? item.text_preview : "",
  };
}

function mapVerifiedClaim(rawClaim, fallbackInput) {
  const rawEvidence =
    rawClaim && Array.isArray(rawClaim.evidence) ? rawClaim.evidence : [];
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
    evidence,
  };
}

async function verifyClaim(claimText) {
  const text = (claimText || "").trim();
  if (!text) {
    throw new Error("Select or enter a claim first.");
  }

  const { authToken } = await getSettings();
  if (!authToken) {
    const authError = new Error(
      "Please login in the TruthLens extension popup first.",
    );
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
    const verified =
      response && Array.isArray(response.verified_claims)
        ? response.verified_claims
        : [];
    if (!verified.length) {
      claims.push(noResultClaim(segments[0]));
    } else {
      verified.forEach((item) =>
        claims.push(mapVerifiedClaim(item, segments[0])),
      );
    }
  } else {
    const results = await Promise.allSettled(
      segments.map((segment) => investigateText(segment, authToken)),
    );

    results.forEach((result, index) => {
      const sourceText = segments[index];
      if (result.status === "fulfilled") {
        const verified =
          result.value && Array.isArray(result.value.verified_claims)
            ? result.value.verified_claims
            : [];

        if (!verified.length) {
          claims.push(noResultClaim(sourceText));
          return;
        }

        verified.forEach((item) =>
          claims.push(mapVerifiedClaim(item, sourceText)),
        );
        return;
      }

      const reason =
        result.reason instanceof Error
          ? result.reason.message
          : "Unknown failure";
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
    temporalContext: first.temporalContext,
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
          try {
            await setStorage({ backendUrl });
          } catch (error) {
            throw new Error(
              "Failed to save backend URL: " +
              (error instanceof Error ? error.message : "Unknown error"),
            );
          }
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
          try {
            await setStorage({
              authToken: token,
              authEmail: profile && profile.email ? profile.email : "",
            });
          } catch (error) {
            throw new Error(
              "Failed to save token: " +
              (error instanceof Error ? error.message : "Unknown error"),
            );
          }

          sendResponse({
            ok: true,
            data: {
              hasToken: true,
              authEmail: profile && profile.email ? profile.email : "",
            },
          });
          return;
        }
        case "LOGOUT": {
          try {
            await setStorage({ authToken: "", authEmail: "" });
          } catch (error) {
            throw new Error(
              "Failed to logout: " +
              (error instanceof Error ? error.message : "Unknown error"),
            );
          }
          sendResponse({ ok: true, data: { hasToken: false } });
          return;
        }
        case "VERIFY_CLAIM": {
          const result = await verifyClaim(message.claim);
          sendResponse({ ok: true, data: result });
          return;
        }
        default:
          sendResponse({
            ok: false,
            error: `Unknown message type: ${message.type}`,
          });
      }
    } catch (error) {
      const messageText =
        error instanceof Error ? error.message : "Unexpected error";
      const code =
        error && typeof error === "object" && "code" in error
          ? error.code
          : undefined;
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

  // Set up side panel to open on action click
  chrome.sidePanel
    .setPanelBehavior({ openPanelOnActionClick: true })
    .catch((error) => console.error("SidePanel Error:", error));

  // Create context menu item for right-clicking images
  chrome.contextMenus.create({
    id: "truthlens-analyze-image",
    title: "🔍 Analyse image with TruthLens",
    contexts: ["image"],
  });
});

// Handle context menu click — do analysis in background, push result to page
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== "truthlens-analyze-image") return;
  if (!tab || !tab.id) return;

  const imageUrl = info.srcUrl;
  if (!imageUrl) return;

  const settings = await getSettings();

  // Helper: inject a function into the page (works even if content.js isn't running)
  const injectFn = async (fn, args = []) => {
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: fn,
      args,
    }).catch(() => { });
  };

  // First: show a loading toast on the page immediately
  await injectFn((src) => {
    // Remove any existing TruthLens card
    const old = document.getElementById("truthlens-result-card");
    if (old) old.remove();

    const card = document.createElement("div");
    card.id = "truthlens-result-card";
    card.style.cssText = `
      position:fixed;bottom:16px;right:16px;z-index:2147483647;
      width:320px;max-width:92vw;max-height:70vh;overflow-y:auto;
      padding:14px 16px;border-radius:14px;
      border:1px solid rgba(96,130,180,0.34);
      background:linear-gradient(165deg,rgba(8,18,36,0.97),rgba(4,9,20,0.96));
      backdrop-filter:blur(10px);
      box-shadow:0 24px 46px rgba(3,8,18,0.66),0 0 24px rgba(20,184,166,0.25);
      font-family:system-ui,sans-serif;color:#e8f1ff;
    `;

    // Inject spinner keyframe once
    if (!document.getElementById("tl-style")) {
      const s = document.createElement("style");
      s.id = "tl-style";
      s.textContent = "@keyframes tl-spin{to{transform:rotate(360deg)}}";
      document.head.appendChild(s);
    }

    card.innerHTML = `
      <button id="tl-close" style="position:absolute;right:10px;top:8px;border:none;background:transparent;cursor:pointer;color:#8fb8ff;font-size:18px;">×</button>
      <div style="font-size:11px;font-weight:700;letter-spacing:0.07em;color:#14b8a6;margin-bottom:4px;">TRUTHLENS ✦ IMAGE</div>
      <div style="font-size:13px;color:#eef4ff;margin-bottom:10px;">Analysing image...</div>
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
        <div style="width:18px;height:18px;border:2px solid rgba(20,184,166,0.3);border-top-color:#14b8a6;border-radius:50%;animation:tl-spin 0.8s linear infinite;flex-shrink:0"></div>
        <span style="font-size:12px;color:#14b8a6;" id="tl-step">Fetching image...</span>
      </div>
      <div style="height:3px;border-radius:999px;background:rgba(255,255,255,0.06);overflow:hidden;">
        <div id="tl-bar" style="height:100%;width:5%;border-radius:999px;background:linear-gradient(90deg,#14b8a6,#3b82f6);transition:width 0.8s ease;"></div>
      </div>
      <div style="margin-top:6px;font-size:10px;color:rgba(255,255,255,0.3);">Image: ${src.slice(0, 55)}...</div>
    `;
    document.body.appendChild(card);
    document.getElementById("tl-close").addEventListener("click", () => card.remove());
  }, [imageUrl]);

  // Step update helpers injected into page
  const setStep = (text, pct) => injectFn((t, p) => {
    const el = document.getElementById("tl-step");
    const bar = document.getElementById("tl-bar");
    if (el) el.textContent = t;
    if (bar) bar.style.width = p + "%";
  }, [text, pct]);

  if (!settings.authToken) {
    await injectFn(() => {
      const card = document.getElementById("truthlens-result-card");
      if (card) card.innerHTML = `
        <button onclick="this.closest('[id]').remove()" style="position:absolute;right:10px;top:8px;border:none;background:transparent;cursor:pointer;color:#8fb8ff;font-size:18px;">×</button>
        <div style="font-size:11px;font-weight:700;color:#14b8a6;margin-bottom:4px;">TRUTHLENS</div>
        <div style="font-size:14px;color:#ffd4dd;margin-bottom:6px;">Login required</div>
        <div style="font-size:12px;color:#ff9bb0;line-height:1.5;">Open the TruthLens side panel and click <strong>Sync Web Auth</strong> first, then try again.</div>
      `;
    });
    return;
  }

  const { backendUrl, authToken } = settings;

  try {
    await setStep("Downloading image...", 15);

    // Fetch image as base64 (ArrayBuffer → base64) in background service worker
    const imgResp = await fetch(imageUrl);
    if (!imgResp.ok) throw new Error("Could not download the image.");

    const buffer = await imgResp.arrayBuffer();
    // Convert ArrayBuffer to Blob for multipart FormData upload
    const contentType = imgResp.headers.get("content-type") || "image/jpeg";
    const blob = new Blob([buffer], { type: contentType });
    const formData = new FormData();
    formData.append("file", blob, "image.jpg");

    await setStep("Running deepfake detection...", 40);

    const apiResp = await fetch(`${backendUrl}/api/v1/analyze-media`, {
      method: "POST",
      headers: { Authorization: `Bearer ${authToken}` },
      // No Content-Type — browser sets multipart boundary automatically
      body: formData,
    });

    await setStep("Finalizing results...", 90);

    const data = await apiResp.json();

    if (!apiResp.ok) {
      throw new Error(data.detail || "Analysis failed.");
    }

    // Render deepfake result inline via scripting
    await injectFn((d) => {
      const card = document.getElementById("truthlens-result-card");
      if (!card) return;

      const verdict = String(d.verdict || "UNKNOWN").toUpperCase();
      const isFake = verdict === "FAKE";
      const vc = isFake ? "#f87171" : "#10b981";
      const vbg = isFake ? "rgba(239,68,68,0.12)" : "rgba(16,185,129,0.12)";
      const fakePct = Math.round(d.fake_probability || 0);
      const realPct = Math.round(d.real_probability || 0);
      const conf = Math.round(d.confidence || 0);
      const evidenceHtml = (d.evidence || []).map(e =>
        `<div style="font-size:11px;color:rgba(255,255,255,0.5);margin-bottom:4px;display:flex;gap:6px"><span style="color:#14b8a6">›</span>${e}</div>`
      ).join("");

      card.innerHTML = `
        <button onclick="this.closest('[id]').remove()" style="position:absolute;right:10px;top:8px;border:none;background:transparent;cursor:pointer;color:#8fb8ff;font-size:18px;">×</button>
        <div style="padding-right:20px">
          <div style="font-size:10px;color:rgba(255,255,255,0.35);margin-bottom:6px">DEEPFAKE DETECTION · ${d.model || "EfficientNet-B0"}</div>
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
            <span style="font-size:20px;font-weight:700;color:${vc}">${verdict}</span>
            <span style="font-size:11px;padding:3px 10px;border-radius:999px;background:${vbg};color:${vc};border:1px solid ${vc}55">${conf}% confidence</span>
          </div>
          <div style="display:flex;gap:8px;margin-bottom:${evidenceHtml ? 10 : 0}px">
            <div style="flex:1">
              <div style="font-size:10px;color:#f87171;margin-bottom:3px">FAKE ${fakePct}%</div>
              <div style="height:4px;border-radius:999px;background:rgba(255,255,255,0.07)"><div style="height:100%;width:${fakePct}%;background:#f87171;border-radius:999px"></div></div>
            </div>
            <div style="flex:1">
              <div style="font-size:10px;color:#10b981;margin-bottom:3px">REAL ${realPct}%</div>
              <div style="height:4px;border-radius:999px;background:rgba(255,255,255,0.07)"><div style="height:100%;width:${realPct}%;background:#10b981;border-radius:999px"></div></div>
            </div>
          </div>
          ${evidenceHtml}
        </div>
      `;
    }, [data]);

    // Also try to notify content.js (fires if content.js is available, silently ignored if not)
    chrome.tabs.sendMessage(tab.id, { type: "SHOW_DEEPFAKE_RESULT", data }).catch(() => { });

  } catch (err) {
    await injectFn((msg) => {
      const card = document.getElementById("truthlens-result-card");
      if (card) card.innerHTML = `
        <button onclick="this.closest('[id]').remove()" style="position:absolute;right:10px;top:8px;border:none;background:transparent;cursor:pointer;color:#8fb8ff;font-size:18px;">×</button>
        <div style="font-size:11px;font-weight:700;color:#14b8a6;margin-bottom:4px;">TRUTHLENS</div>
        <div style="font-size:14px;color:#ffd4dd;margin-bottom:6px;">Analysis Error</div>
        <div style="font-size:12px;color:#ff9bb0;line-height:1.5;">${msg}</div>
      `;
    }, [err && err.message ? err.message : "Unexpected error."]);
  }
});
