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
  el.classList.remove("hidden");
  el.className = `mt-4 p-3 rounded-xl text-xs leading-relaxed border ${isError
    ? "bg-red-900/20 border-red-500/30 text-red-400"
    : "bg-black/30 border-white/10 text-foreground/70"
    }`;
}

function setResultHtml(html, isError = false) {
  const el = document.getElementById("result");
  el.innerHTML = html;
  el.classList.remove("hidden");
  el.className = `mt-4 p-0 rounded-xl text-sm leading-relaxed space-y-0 overflow-hidden border ${isError
    ? "bg-red-900/20 border-red-500/30"
    : "bg-black/20 border-white/10"
    }`;
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
      sourcesChecked: result.sourcesChecked || 0,
    },
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
    const sourceDomain =
      item && item.sourceDomain ? String(item.sourceDomain) : "unknown";
    const key = sourceUrl || sourceDomain;
    if (!key || seen.has(key)) {
      return;
    }
    seen.add(key);
    deduped.push({
      sourceUrl,
      sourceDomain,
      stance: item && item.stance ? item.stance : "neutral",
      trustScore: item && item.trustScore ? Number(item.trustScore) : 0,
    });
  });

  deduped.sort((a, b) => b.trustScore - a.trustScore);

  const top = deduped.slice(0, 3);
  const rest = deduped.slice(3);

  const topHtml = top
    .map((source) => {
      const link = source.sourceUrl
        ? `<a href="${escapeHtml(source.sourceUrl)}" target="_blank" rel="noopener noreferrer">Open</a>`
        : `<span class="no-link">No link</span>`;
      return `<div class="source-row">
      <span class="source-domain">${escapeHtml(source.sourceDomain)}</span>
      <span class="source-stance" style="color:${stanceColor(source.stance)}">${escapeHtml(String(source.stance).toUpperCase())}</span>
      ${link}
    </div>`;
    })
    .join("");

  const restHtml = rest.length
    ? `<details class="source-more"><summary>Show ${rest.length} more</summary>${rest
      .map((source) => {
        const link = source.sourceUrl
          ? `<a href="${escapeHtml(source.sourceUrl)}" target="_blank" rel="noopener noreferrer">Open</a>`
          : `<span class="no-link">No link</span>`;
        return `<div class="source-row">
          <span class="source-domain">${escapeHtml(source.sourceDomain)}</span>
          <span class="source-stance" style="color:${stanceColor(source.stance)}">${escapeHtml(String(source.stance).toUpperCase())}</span>
          ${link}
        </div>`;
      })
      .join("")}</details>`
    : "";

  if (!topHtml) {
    return `<div class="source-empty">Source links unavailable.</div>`;
  }

  return `<div class="sources-wrap">${topHtml}${restHtml}</div>`;
}

function verdictColor(verdict) {
  const v = String(verdict || "").toLowerCase();
  if (v.includes("true") || v.includes("support")) return { bg: "rgba(16,185,129,0.12)", border: "rgba(16,185,129,0.3)", text: "#10b981" };
  if (v.includes("false") || v.includes("refut")) return { bg: "rgba(239,68,68,0.12)", border: "rgba(239,68,68,0.3)", text: "#f87171" };
  if (v.includes("unverified") || v.includes("mixed")) return { bg: "rgba(234,179,8,0.12)", border: "rgba(234,179,8,0.3)", text: "#eab308" };
  return { bg: "rgba(148,163,184,0.08)", border: "rgba(148,163,184,0.2)", text: "#94a3b8" };
}

function formatResultHtml(result) {
  const claims = normalizedClaims(result);
  const meta = `<div style="padding:10px 14px 8px;border-bottom:1px solid rgba(255,255,255,0.06);font-size:11px;color:rgba(255,255,255,0.45)">Analyzed ${claims.length} claim(s)${result.segmentsAnalyzed ? ` across ${result.segmentsAnalyzed} segment(s)` : ""}</div>`;

  const claimHtml = claims.slice(0, 6).map((claim, index) => {
    const confidence = Math.round((Number(claim.confidence) || 0) * 100);
    const vc = verdictColor(claim.verdict);
    const evidence = claim.evidence && Array.isArray(claim.evidence) ? claim.evidence : [];
    const topSources = evidence.slice(0, 3).map(e => {
      const domain = e.sourceUrl
        ? `<a href="${escapeHtml(e.sourceUrl)}" target="_blank" rel="noopener noreferrer" style="color:#60a5fa;text-decoration:underline;font-size:11px">${escapeHtml(e.sourceDomain || e.sourceUrl)}</a>`
        : `<span style="color:rgba(255,255,255,0.35);font-size:11px">${escapeHtml(e.sourceDomain || "unknown")}</span>`;
      const stanceC = e.stance && e.stance.includes("support") ? "#10b981" : e.stance && e.stance.includes("refut") ? "#f87171" : "#94a3b8";
      return `<div style="display:flex;align-items:center;gap:8px;padding:4px 0">${domain}<span style="color:${stanceC};font-size:10px;font-weight:600">${escapeHtml((e.stance || "neutral").toUpperCase())}</span></div>`;
    }).join("");

    return `<div style="padding:12px 14px;border-bottom:1px solid rgba(255,255,255,0.05)">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">
        <span style="font-size:10px;color:rgba(255,255,255,0.4);font-weight:600">CLAIM ${index + 1}</span>
        <span style="font-size:10px;font-weight:700;padding:2px 8px;border-radius:999px;background:${vc.bg};border:1px solid ${vc.border};color:${vc.text}">${escapeHtml(String(claim.verdict || "unknown").toUpperCase())} · ${confidence}%</span>
      </div>
      <div style="font-size:12px;color:rgba(255,255,255,0.8);margin-bottom:6px;line-height:1.5">${escapeHtml(String(claim.claim || "").slice(0, 180))}</div>
      <div style="font-size:11px;color:rgba(255,255,255,0.5);line-height:1.5;margin-bottom:${topSources ? 8 : 0}px">${escapeHtml(claim.evidenceSummary || "No explanation returned.")}</div>
      ${topSources ? `<div style="border-top:1px solid rgba(255,255,255,0.05);padding-top:6px">${topSources}</div>` : ""}
    </div>`;
  }).join("");

  const extra = claims.length > 6
    ? `<div style="padding:8px 14px;font-size:11px;color:rgba(255,255,255,0.35)">Showing first 6 of ${claims.length} claims.</div>`
    : "";
  const warning = Array.isArray(result.errors) && result.errors.length
    ? `<div style="padding:8px 14px;font-size:11px;color:#f87171">⚠ ${escapeHtml(result.errors[0])}</div>`
    : "";

  return `${meta}${claimHtml}${extra}${warning}`;
}

async function loadSettings() {
  const response = await sendMessage({ type: "GET_SETTINGS" });
  if (!response.ok) {
    setStatus(response.error || "Could not load extension settings.", true);
    return;
  }

  const { backendUrl, hasToken, authEmail } = response.data;
  document.getElementById("backendUrl").value =
    backendUrl || "http://localhost:8000";

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
    password: document.getElementById("password").value,
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
  // Clear the password field for security
  document.getElementById("password").value = "";
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
  setStatus("Scanning for TruthLens web session...");

  // Find ANY open TruthLens tab automatically (doesn't need to be active)
  let tabs = [];
  try {
    tabs = await chrome.tabs.query({ url: "http://localhost:5173/*" });
  } catch {
    tabs = [];
  }

  // Fallback: also search http://127.0.0.1:5173/*
  if (!tabs.length) {
    try {
      const fallback = await chrome.tabs.query({ url: "http://127.0.0.1:5173/*" });
      tabs = fallback;
    } catch {
      tabs = [];
    }
  }

  if (!tabs.length) {
    setStatus("TruthLens web app isn't open. Open it at localhost:5173 and try again.", true);
    return;
  }

  const tab = tabs[0];
  let token = "";
  try {
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        try {
          // Try all common storage keys used by auth libs
          return (
            localStorage.getItem("token") ||
            localStorage.getItem("access_token") ||
            localStorage.getItem("authToken") ||
            sessionStorage.getItem("token") ||
            sessionStorage.getItem("access_token") ||
            ""
          );
        } catch {
          return "";
        }
      },
    });
    token = results && results[0] && results[0].result ? String(results[0].result) : "";
  } catch {
    setStatus("Could not read from TruthLens tab. Check extension permissions.", true);
    return;
  }

  if (!token) {
    setStatus("Not logged in on TruthLens web app. Please login there first.", true);
    return;
  }

  const backendUrl = (document.getElementById("backendUrl").value.trim() || "http://localhost:8000").replace(/\/$/, "");

  let profile;
  try {
    const response = await fetch(`${backendUrl}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
      throw new Error("Token is invalid or backend is offline.");
    }
    profile = await response.json();
  } catch (error) {
    setStatus(error instanceof Error ? error.message : "Failed to validate web token.", true);
    return;
  }

  try {
    await new Promise((resolve, reject) => {
      chrome.storage.local.set(
        { authToken: token, authEmail: profile && profile.email ? profile.email : "", backendUrl },
        () => {
          if (chrome.runtime.lastError) {
            reject(new Error(chrome.runtime.lastError.message));
          } else {
            resolve();
          }
        },
      );
    });
  } catch (error) {
    setStatus("Failed to save credentials: " + (error instanceof Error ? error.message : "Unknown error"), true);
    return;
  }

  const email = profile && profile.email ? profile.email : "user";
  setStatus(`✅ Synced! Logged in as ${email}.`);

  // Update the auth status badge
  const statusEl = document.getElementById("authStatus");
  if (statusEl) {
    statusEl.textContent = `Logged in as ${email}`;
    statusEl.classList.remove("text-foreground/60");
    statusEl.classList.add("text-success");
  }

  // Show logout button, hide login/register
  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) logoutBtn.classList.remove("hidden");
}

async function useSelectedText() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || typeof tab.id !== "number") {
    setResult("Could not access active tab.", true);
    return;
  }

  const response = await chrome.tabs
    .sendMessage(tab.id, { type: "GET_SELECTION" })
    .catch(() => null);
  const selected =
    response && response.ok && response.data ? response.data.selection : "";

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

  const btn = document.getElementById("verifyBtn");
  const originalText = btn.textContent;
  btn.textContent = "Analyzing...";
  btn.disabled = true;

  setResult("⏳ Running forensic analysis... this takes 5–30 seconds.");

  const response = await sendMessage({ type: "VERIFY_CLAIM", claim });
  btn.textContent = originalText;
  btn.disabled = false;

  if (!response.ok) {
    setResult(response.error || "Verification failed.", true);
    if (response.code === "AUTH_REQUIRED") {
      setStatus("Please login (or Sync Web Auth) before verifying.", true);
    }
    return;
  }

  setResultHtml(formatResultHtml(response.data));
}

async function verifyMedia() {
  const fileInput = document.getElementById("mediaInput");
  const file = fileInput && fileInput.files && fileInput.files[0];
  if (!file) {
    showMediaResult("Please choose an image or video file first.", true);
    return;
  }

  const settings = await sendMessage({ type: "GET_SETTINGS" });
  if (!settings.ok || !settings.data.hasToken) {
    showMediaResult("Login required. Use Sync Web Auth first.", true);
    return;
  }

  const { backendUrl, authToken } = settings.data;
  const mediaBtn = document.getElementById("mediaVerifyBtn");
  mediaBtn.textContent = "Analyzing...";
  mediaBtn.disabled = true;

  showMediaResult("⏳ Running deepfake detection...");

  try {
    // Use multipart FormData — the correct way to call /api/v1/analyze-media
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${backendUrl}/api/v1/analyze-media`, {
      method: "POST",
      headers: { Authorization: `Bearer ${authToken}` },
      // NO Content-Type header — browser sets it automatically with boundary for FormData
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      showMediaResult(`Error: ${data.detail || "Media analysis failed."}`, true);
      return;
    }

    // Render deepfake result card
    renderDeepfakeResult(data);
  } catch (err) {
    showMediaResult(`Error: ${err.message || "Unexpected error."}`, true);
  } finally {
    mediaBtn.textContent = "Analyze Media";
    mediaBtn.disabled = false;
  }
}

function showMediaResult(text, isError = false) {
  const el = document.getElementById("mediaResult");
  el.textContent = text;
  el.style.display = "block";
  el.style.color = isError ? "#f87171" : "rgba(255,255,255,0.6)";
  el.style.padding = "10px 12px";
  el.style.border = `1px solid ${isError ? "rgba(239,68,68,0.2)" : "rgba(255,255,255,0.08)"}`;
  el.style.borderRadius = "12px";
  el.style.background = "rgba(0,0,0,0.3)";
}

function renderDeepfakeResult(data) {
  const el = document.getElementById("mediaResult");
  el.style.display = "block";
  el.style.padding = "0";
  el.style.border = "1px solid rgba(255,255,255,0.1)";
  el.style.borderRadius = "12px";
  el.style.overflow = "hidden";
  el.style.background = "rgba(0,0,0,0.2)";

  const verdict = String(data.verdict || "UNKNOWN").toUpperCase();
  const isFake = verdict === "FAKE";
  const verdictColor = isFake ? "#f87171" : "#10b981";
  const verdictBg = isFake ? "rgba(239,68,68,0.12)" : "rgba(16,185,129,0.12)";

  const fakePct = Math.round(data.fake_probability || 0);
  const realPct = Math.round(data.real_probability || 0);
  const conf = Math.round(data.confidence || 0);

  const evidenceHtml = (data.evidence || []).map(e =>
    `<div style="display:flex;align-items:flex-start;gap:6px;font-size:11px;color:rgba(255,255,255,0.5);margin-bottom:4px">
      <span style="color:#14b8a6;flex-shrink:0">›</span>${e}
    </div>`
  ).join("");

  el.innerHTML = `
    <div style="padding:12px 14px 8px;border-bottom:1px solid rgba(255,255,255,0.06)">
      <div style="font-size:10px;color:rgba(255,255,255,0.35);margin-bottom:6px">DEEPFAKE DETECTION · ${data.model || "EfficientNet-B0"}</div>
      <div style="display:flex;align-items:center;justify-content:space-between">
        <span style="font-size:18px;font-weight:700;color:${verdictColor}">${verdict}</span>
        <span style="font-size:11px;padding:3px 10px;border-radius:999px;background:${verdictBg};color:${verdictColor};border:1px solid ${verdictColor}33">${conf}% confidence</span>
      </div>
    </div>
    <div style="padding:10px 14px;border-bottom:1px solid rgba(255,255,255,0.06)">
      <div style="font-size:10px;color:rgba(255,255,255,0.35);margin-bottom:6px">PROBABILITY BREAKDOWN</div>
      <div style="display:flex;gap:8px;margin-bottom:6px">
        <div style="flex:1">
          <div style="font-size:10px;color:#f87171;margin-bottom:3px">FAKE ${fakePct}%</div>
          <div style="height:4px;border-radius:999px;background:rgba(255,255,255,0.06)">
            <div style="height:100%;width:${fakePct}%;background:#f87171;border-radius:999px"></div>
          </div>
        </div>
        <div style="flex:1">
          <div style="font-size:10px;color:#10b981;margin-bottom:3px">REAL ${realPct}%</div>
          <div style="height:4px;border-radius:999px;background:rgba(255,255,255,0.06)">
            <div style="height:100%;width:${realPct}%;background:#10b981;border-radius:999px"></div>
          </div>
        </div>
      </div>
    </div>
    ${evidenceHtml ? `<div style="padding:10px 14px">${evidenceHtml}</div>` : ""}
  `;
}


document.getElementById("saveUrl").addEventListener("click", saveBackendUrl);
document.getElementById("loginBtn").addEventListener("click", login);
document.getElementById("registerBtn").addEventListener("click", register);
document.getElementById("logoutBtn").addEventListener("click", logout);
document.getElementById("importWebToken").addEventListener("click", importWebSessionToken);
document.getElementById("grabSelection").addEventListener("click", useSelectedText);
document.getElementById("verifyBtn").addEventListener("click", verify);
document.getElementById("mediaVerifyBtn").addEventListener("click", verifyMedia);

// Preview selected file name
document.getElementById("mediaInput").addEventListener("change", (e) => {
  const file = e.target.files && e.target.files[0];
  const label = document.getElementById("mediaLabel");
  if (label) label.textContent = file ? `📁 ${file.name}` : "Choose image or video";
});

loadSettings();
