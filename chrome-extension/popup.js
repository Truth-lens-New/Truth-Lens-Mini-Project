function sendMessage(payload) {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage(payload, (response) => {
      if (chrome.runtime.lastError) {
        resolve({ ok: false, error: chrome.runtime.lastError.message });
        return;
      }
      resolve(response || { ok: false, error: "No response" });
    });
  });
}

function setStatus(text, isError = false) {
  const el = document.getElementById("authStatus");
  el.textContent = text;
  el.style.color = isError ? "#991b1b" : "#475569";
}

function setResult(text, isError = false) {
  const el = document.getElementById("result");
  el.textContent = text;
  el.classList.toggle("error", isError);
}

function setResultHtml(html, isError = false) {
  const el = document.getElementById("result");
  el.innerHTML = html;
  el.classList.toggle("error", isError);
}

function escapeHtml(value) {
  const text = String(value || "");
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function normalizedClaims(result) {
  if (result && Array.isArray(result.claims) && result.claims.length) {
    return result.claims;
  }

  return [
    {
      claim: result.claim || result.input || "",
      verdict: result.verdict || "unknown",
      confidence: Number(result.confidence) || 0,
      evidenceSummary: result.evidenceSummary || "No explanation returned.",
      evidenceCount: result.evidenceCount || 0,
      sourcesChecked: result.sourcesChecked || 0
    }
  ];
}

function stanceColor(stance) {
  const value = String(stance || "").toLowerCase();
  if (value.includes("support")) {
    return "#2de6c0";
  }
  if (value.includes("refut")) {
    return "#ff8ba8";
  }
  return "#9bb1cf";
}

function sourceRows(claim) {
  const evidence = claim && Array.isArray(claim.evidence) ? claim.evidence : [];
  const deduped = [];
  const seen = new Set();

  evidence.forEach((item) => {
    const sourceUrl = item && item.sourceUrl ? String(item.sourceUrl) : "";
    const sourceDomain = item && item.sourceDomain ? String(item.sourceDomain) : "unknown";
    const key = sourceUrl || sourceDomain;
    if (!key || seen.has(key)) {
      return;
    }
    seen.add(key);
    deduped.push({
      sourceUrl,
      sourceDomain,
      stance: item && item.stance ? item.stance : "neutral",
      trustScore: item && item.trustScore ? Number(item.trustScore) : 0
    });
  });

  deduped.sort((a, b) => b.trustScore - a.trustScore);

  const top = deduped.slice(0, 3);
  const rest = deduped.slice(3);

  const topHtml = top.map((source) => {
    const link = source.sourceUrl
      ? `<a href="${escapeHtml(source.sourceUrl)}" target="_blank" rel="noopener noreferrer">Open</a>`
      : `<span class="no-link">No link</span>`;
    return `<div class="source-row">
      <span class="source-domain">${escapeHtml(source.sourceDomain)}</span>
      <span class="source-stance" style="color:${stanceColor(source.stance)}">${escapeHtml(String(source.stance).toUpperCase())}</span>
      ${link}
    </div>`;
  }).join("");

  const restHtml = rest.length
    ? `<details class="source-more"><summary>Show ${rest.length} more</summary>${rest.map((source) => {
        const link = source.sourceUrl
          ? `<a href="${escapeHtml(source.sourceUrl)}" target="_blank" rel="noopener noreferrer">Open</a>`
          : `<span class="no-link">No link</span>`;
        return `<div class="source-row">
          <span class="source-domain">${escapeHtml(source.sourceDomain)}</span>
          <span class="source-stance" style="color:${stanceColor(source.stance)}">${escapeHtml(String(source.stance).toUpperCase())}</span>
          ${link}
        </div>`;
      }).join("")}</details>`
    : "";

  if (!topHtml) {
    return `<div class="source-empty">Source links unavailable.</div>`;
  }

  return `<div class="sources-wrap">${topHtml}${restHtml}</div>`;
}

function formatResultHtml(result) {
  const claims = normalizedClaims(result);
  const header = `<div class="result-header">Analyzed ${claims.length} claim(s)${result.segmentsAnalyzed ? ` across ${result.segmentsAnalyzed} segment(s)` : ""}.</div>`;

  const claimHtml = claims.slice(0, 6).map((claim, index) => {
    const confidence = Math.round((Number(claim.confidence) || 0) * 100);
    return `<div class="claim-block">
      <div class="claim-index">Claim ${index + 1}</div>
      <div class="claim-text">${escapeHtml(String(claim.claim || "").slice(0, 170))}</div>
      <div class="claim-meta">
        <span class="claim-verdict">${escapeHtml(String(claim.verdict || "unknown").toUpperCase())}</span>
        <span>${confidence}%</span>
        <span>evidence ${claim.evidenceCount || 0}</span>
      </div>
      <div class="claim-summary">${escapeHtml(claim.evidenceSummary || "No explanation returned.")}</div>
      ${sourceRows(claim)}
    </div>`;
  }).join("");

  const extra = claims.length > 6
    ? `<div class="result-note">Showing first 6 of ${claims.length} claims.</div>`
    : "";
  const warning = Array.isArray(result.errors) && result.errors.length
    ? `<div class="result-warning">Warnings: ${escapeHtml(result.errors[0])}</div>`
    : "";

  return `${header}${claimHtml}${extra}${warning}`;
}

async function loadSettings() {
  const response = await sendMessage({ type: "GET_SETTINGS" });
  if (!response.ok) {
    setStatus(response.error || "Could not load extension settings.", true);
    return;
  }

  const { backendUrl, hasToken, authEmail } = response.data;
  document.getElementById("backendUrl").value = backendUrl || "http://localhost:8000";

  if (hasToken) {
    setStatus(`Logged in as ${authEmail || "user"}.`);
  } else {
    setStatus("Not logged in.");
  }
}

async function saveBackendUrl() {
  const backendUrl = document.getElementById("backendUrl").value.trim();
  const response = await sendMessage({ type: "SAVE_BACKEND_URL", backendUrl });
  if (!response.ok) {
    setStatus(response.error || "Could not save backend URL.", true);
    return;
  }

  setStatus(`Backend URL saved: ${response.data.backendUrl}`);
}

function credentials() {
  return {
    email: document.getElementById("email").value.trim(),
    password: document.getElementById("password").value
  };
}

function validateCredentials(email, password) {
  if (!email || !password) {
    setStatus("Email and password are required.", true);
    return false;
  }

  if (password.length < 6) {
    setStatus("Use a password with at least 6 characters.", true);
    return false;
  }

  return true;
}

async function login() {
  const { email, password } = credentials();
  if (!validateCredentials(email, password)) {
    return;
  }

  setStatus("Logging in...");
  const response = await sendMessage({ type: "LOGIN", email, password });

  if (!response.ok) {
    setStatus(response.error || "Login failed.", true);
    return;
  }

  setStatus(`Logged in as ${email}.`);
}

async function register() {
  const { email, password } = credentials();
  if (!validateCredentials(email, password)) {
    return;
  }

  setStatus("Creating account...");
  const regResponse = await sendMessage({ type: "REGISTER", email, password });
  if (!regResponse.ok) {
    setStatus(regResponse.error || "Registration failed.", true);
    return;
  }

  const loginResponse = await sendMessage({ type: "LOGIN", email, password });
  if (!loginResponse.ok) {
    setStatus(`Registered, but login failed: ${loginResponse.error}`, true);
    return;
  }

  setStatus(`Registered and logged in as ${email}.`);
}

async function logout() {
  const response = await sendMessage({ type: "LOGOUT" });
  if (!response.ok) {
    setStatus(response.error || "Logout failed.", true);
    return;
  }

  setStatus("Logged out.");
}

async function importWebSessionToken() {
  setStatus("Importing web session...");

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || typeof tab.id !== "number") {
    setStatus("Could not access active tab.", true);
    return;
  }

  let token = "";
  try {
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        try {
          return localStorage.getItem("token") || "";
        } catch {
          return "";
        }
      }
    });
    token = results && results[0] && results[0].result ? String(results[0].result) : "";
  } catch {
    setStatus("Open the TruthLens web app tab first, then try again.", true);
    return;
  }

  if (!token) {
    setStatus("No web token found on this tab. Login on the web app first.", true);
    return;
  }

  const backendUrlInput = document.getElementById("backendUrl").value.trim() || "http://localhost:8000";
  const backendUrl = backendUrlInput.replace(/\/$/, "");

  let profile;
  try {
    const response = await fetch(`${backendUrl}/auth/me`, {
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });
    if (!response.ok) {
      throw new Error("Web token is invalid for this backend.");
    }
    profile = await response.json();
  } catch (error) {
    setStatus(error instanceof Error ? error.message : "Failed to validate web token.", true);
    return;
  }

  await new Promise((resolve) => {
    chrome.storage.local.set(
      {
        authToken: token,
        authEmail: profile && profile.email ? profile.email : "",
        backendUrl
      },
      resolve
    );
  });

  setStatus(`Synced with web login as ${profile && profile.email ? profile.email : "user"}.`);
}

async function useSelectedText() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || typeof tab.id !== "number") {
    setResult("Could not access active tab.", true);
    return;
  }

  const response = await chrome.tabs.sendMessage(tab.id, { type: "GET_SELECTION" }).catch(() => null);
  const selected = response && response.ok && response.data ? response.data.selection : "";

  if (!selected) {
    setResult("No text selected. Highlight text on the page first.", true);
    return;
  }

  document.getElementById("claimInput").value = selected;
  setResult("Selected text loaded.");
}

async function verify() {
  const claim = document.getElementById("claimInput").value.trim();
  if (!claim) {
    setResult("Enter or select a claim first.", true);
    return;
  }

  setResult("Verifying... this may take several seconds.");
  const response = await sendMessage({ type: "VERIFY_CLAIM", claim });

  if (!response.ok) {
    setResult(response.error || "Verification failed.", true);
    if (response.code === "AUTH_REQUIRED") {
      setStatus("Please login before verifying claims.", true);
    }
    return;
  }

  setResultHtml(formatResultHtml(response.data));
}

document.getElementById("saveUrl").addEventListener("click", saveBackendUrl);
document.getElementById("loginBtn").addEventListener("click", login);
document.getElementById("registerBtn").addEventListener("click", register);
document.getElementById("logoutBtn").addEventListener("click", logout);
document.getElementById("importWebToken").addEventListener("click", importWebSessionToken);
document.getElementById("grabSelection").addEventListener("click", useSelectedText);
document.getElementById("verifyBtn").addEventListener("click", verify);

loadSettings();
