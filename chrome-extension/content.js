const MIN_SELECTION_LENGTH = 18;

let selectedClaim = "";
let buttonEl = null;
let cardEl = null;

function sendRuntimeMessage(payload) {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage(payload, (response) => {
      if (chrome.runtime.lastError) {
        resolve({ ok: false, error: chrome.runtime.lastError.message });
        return;
      }
      resolve(response || { ok: false, error: "No response from extension." });
    });
  });
}

function cleanupFloatingUi() {
  if (buttonEl) {
    buttonEl.remove();
    buttonEl = null;
  }
}

function renderResultCard(html) {
  if (!cardEl) {
    cardEl = document.createElement("div");
    cardEl.id = "truthlens-result-card";
    cardEl.style.position = "fixed";
    cardEl.style.right = "16px";
    cardEl.style.bottom = "16px";
    cardEl.style.zIndex = "2147483647";
    cardEl.style.width = "340px";
    cardEl.style.maxWidth = "92vw";
    cardEl.style.maxHeight = "62vh";
    cardEl.style.overflowY = "auto";
    cardEl.style.padding = "12px";
    cardEl.style.borderRadius = "14px";
    cardEl.style.border = "1px solid rgba(96, 130, 180, 0.34)";
    cardEl.style.background = "linear-gradient(165deg, rgba(8,18,36,0.96), rgba(4,9,20,0.95))";
    cardEl.style.backdropFilter = "blur(8px)";
    cardEl.style.boxShadow = "0 24px 46px rgba(3,8,18,0.66), 0 0 24px rgba(47,124,255,0.2)";
    cardEl.style.fontFamily = "\"Sora\", \"Space Grotesk\", sans-serif";
    cardEl.style.color = "#e8f1ff";

    const closeBtn = document.createElement("button");
    closeBtn.textContent = "×";
    closeBtn.setAttribute("aria-label", "Close TruthLens panel");
    closeBtn.style.position = "absolute";
    closeBtn.style.right = "11px";
    closeBtn.style.top = "8px";
    closeBtn.style.border = "none";
    closeBtn.style.background = "transparent";
    closeBtn.style.cursor = "pointer";
    closeBtn.style.color = "#8fb8ff";
    closeBtn.style.fontSize = "16px";
    closeBtn.addEventListener("click", () => cardEl.remove());

    cardEl.appendChild(closeBtn);
    document.body.appendChild(cardEl);
  }

  cardEl.innerHTML = `<button aria-label="Close TruthLens panel" style="position:absolute;right:11px;top:8px;border:none;background:transparent;cursor:pointer;color:#8fb8ff;font-size:16px;">×</button>${html}`;
  const closeBtn = cardEl.querySelector("button");
  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      if (cardEl) {
        cardEl.remove();
        cardEl = null;
      }
    });
  }
}

function verdictColor(verdict) {
  const value = String(verdict || "").toLowerCase();
  if (value.includes("true") || value.includes("supports")) {
    return "#0b8f4d";
  }
  if (value.includes("false") || value.includes("refute") || value.includes("misleading")) {
    return "#d14343";
  }
  if (value.includes("mixed") || value.includes("uncertain")) {
    return "#b07a00";
  }
  return "#334155";
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
      evidenceSummary: result.evidenceSummary || "No summary available.",
      evidenceCount: result.evidenceCount || 0,
      sourcesChecked: result.sourcesChecked || 0
    }
  ];
}

function stanceBadgeColor(stance) {
  const value = String(stance || "").toLowerCase();
  if (value.includes("support")) {
    return "#00c39a";
  }
  if (value.includes("refut")) {
    return "#ff5f84";
  }
  return "#89a6cf";
}

function getRankedSources(claim) {
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
      sourceType: item && item.sourceType ? item.sourceType : "web_search",
      stance: item && item.stance ? item.stance : "neutral",
      trustScore: item && item.trustScore ? Number(item.trustScore) : 0,
      stanceConfidence: item && item.stanceConfidence ? Number(item.stanceConfidence) : 0,
      textPreview: item && item.textPreview ? item.textPreview : ""
    });
  });

  return deduped.sort((a, b) => {
    if (b.trustScore !== a.trustScore) {
      return b.trustScore - a.trustScore;
    }
    return b.stanceConfidence - a.stanceConfidence;
  });
}

function renderSourceRow(source) {
  const domain = escapeHtml(source.sourceDomain || "unknown");
  const sourceType = escapeHtml(String(source.sourceType || "web_search").replace(/_/g, " "));
  const stance = escapeHtml(String(source.stance || "neutral").toUpperCase());
  const stanceColor = stanceBadgeColor(source.stance);
  const preview = escapeHtml((source.textPreview || "").slice(0, 120));
  const linkHtml = source.sourceUrl
    ? `<a href="${escapeHtml(source.sourceUrl)}" target="_blank" rel="noopener noreferrer" style="color:#7dd9ff;text-decoration:none;font-size:12px;font-weight:600;">Open</a>`
    : `<span style="color:#6f87aa;font-size:12px;">No link</span>`;

  return `
    <div style="border:1px solid rgba(98,126,164,0.26);background:rgba(5,14,29,0.74);border-radius:8px;padding:7px;margin-top:6px;">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">
        <span style="font-size:12px;color:#d8e6fb;font-weight:600;">${domain}</span>
        ${linkHtml}
      </div>
      <div style="display:flex;gap:6px;align-items:center;margin-top:4px;flex-wrap:wrap;">
        <span style="font-size:10px;color:${stanceColor};background:rgba(22,36,64,0.72);border:1px solid rgba(117,146,184,0.36);padding:2px 6px;border-radius:999px;">${stance}</span>
        <span style="font-size:10px;color:#8aa6cd;">${sourceType}</span>
        <span style="font-size:10px;color:#8aa6cd;">trust ${source.trustScore || 0}</span>
      </div>
      ${preview ? `<div style="font-size:11px;color:#9ab4d8;margin-top:4px;line-height:1.35;">${preview}${source.textPreview && source.textPreview.length > 120 ? "..." : ""}</div>` : ""}
    </div>
  `;
}

function renderSourcesSection(claim) {
  const sources = getRankedSources(claim);
  if (!sources.length) {
    return `<div style="font-size:11px;color:#7f9ac2;margin-top:8px;">Source links unavailable for this claim.</div>`;
  }

  const top = sources.slice(0, 3).map(renderSourceRow).join("");
  const rest = sources.slice(3);
  const restHtml = rest.length
    ? `<details style="margin-top:6px;">
        <summary style="cursor:pointer;color:#86dfff;font-size:11px;">Show ${rest.length} more source(s)</summary>
        <div>${rest.map(renderSourceRow).join("")}</div>
      </details>`
    : "";

  return `
    <div style="margin-top:8px;">
      <div style="font-size:11px;color:#90abcf;">Sources (${sources.length})</div>
      ${top}
      ${restHtml}
    </div>
  `;
}

function formatClaimRow(claim, index) {
  const color = verdictColor(claim.verdict);
  const confidencePct = Math.round((Number(claim.confidence) || 0) * 100);
  const claimText = escapeHtml(claim.claim || "");
  const summary = escapeHtml(claim.evidenceSummary || "No summary available.");

  return `
    <div style="border:1px solid rgba(117,146,184,0.3);border-radius:10px;padding:8px;margin-bottom:8px;background:rgba(9,20,40,0.72);">
      <div style="font-size:11px;color:#99b8e8;margin-bottom:6px;">Claim ${index + 1}</div>
      <div style="margin-bottom:8px;font-size:13px;color:#d8e6fb;">${claimText.slice(0, 220)}</div>
      <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px;flex-wrap:wrap;">
        <span style="display:inline-block;padding:4px 8px;border-radius:999px;background:rgba(31,56,102,0.62);color:${color};font-weight:700;font-size:12px;border:1px solid rgba(94,130,185,0.4);">${escapeHtml(String(claim.verdict || "unknown").toUpperCase())}</span>
        <span style="font-size:12px;color:#9fb8dc;">Confidence: ${confidencePct}%</span>
      </div>
      <div style="font-size:13px;line-height:1.4;margin-bottom:8px;color:#bed2ef;">${summary}</div>
      <div style="font-size:12px;color:#90abcf;">Evidence: ${claim.evidenceCount || 0} | Sources: ${claim.sourcesChecked || 0}</div>
      ${renderSourcesSection(claim)}
    </div>
  `;
}

function formatVerificationResult(result) {
  const claims = normalizedClaims(result);
  const errors = result && Array.isArray(result.errors) ? result.errors : [];
  const items = claims.slice(0, 6).map((claim, index) => formatClaimRow(claim, index)).join("");
  const truncated = claims.length > 6
    ? `<div style="font-size:12px;color:#90abcf;margin-top:4px;">Showing first 6 of ${claims.length} claims.</div>`
    : "";
  const errorNote = errors.length
    ? `<div style="font-size:12px;color:#ff9bb0;background:rgba(67,8,23,0.78);border:1px solid rgba(255,99,138,0.45);border-radius:8px;padding:8px;margin-top:6px;">Some claim checks failed: ${escapeHtml(errors[0])}</div>`
    : "";

  return `
    <div style="padding-right:20px;">
      <div style="font-size:12px;font-weight:700;letter-spacing:0.06em;color:#86e7ff;">TRUTHLENS</div>
      <h3 style="margin:4px 0 4px;font-size:16px;color:#eef4ff;">Claim Verification</h3>
      <div style="font-size:12px;color:#90abcf;margin-bottom:8px;">Analyzed ${claims.length} claim(s)${result.segmentsAnalyzed ? ` across ${result.segmentsAnalyzed} sentence segment(s)` : ""}.</div>
      ${items}
      ${truncated}
      ${errorNote}
    </div>
  `;
}

function showError(message) {
  renderResultCard(`
    <div style="padding-right:20px;">
      <div style="font-size:12px;font-weight:700;letter-spacing:0.06em;color:#86e7ff;">TRUTHLENS</div>
      <h3 style="margin:4px 0 8px;font-size:16px;color:#ffd4dd;">Verification Error</h3>
      <div style="font-size:13px;line-height:1.5;color:#ff9bb0;">${message}</div>
      <div style="margin-top:8px;font-size:12px;color:#90abcf;">Open the extension popup to login or update backend URL.</div>
    </div>
  `);
}

function showLoading() {
  renderResultCard(`
    <div style="padding-right:20px;">
      <div style="font-size:12px;font-weight:700;letter-spacing:0.06em;color:#86e7ff;">TRUTHLENS</div>
      <h3 style="margin:4px 0 8px;font-size:16px;color:#eef4ff;">Verifying claim...</h3>
      <div style="font-size:13px;color:#90abcf;line-height:1.4;">This can take a few seconds while TruthLens investigates sources.</div>
    </div>
  `);
}

async function verifyCurrentSelection() {
  if (!selectedClaim) {
    return;
  }

  showLoading();

  const response = await sendRuntimeMessage({
    type: "VERIFY_CLAIM",
    claim: selectedClaim
  });

  if (!response || !response.ok) {
    showError(response && response.error ? response.error : "Could not verify claim.");
    return;
  }

  renderResultCard(formatVerificationResult(response.data));
}

function renderVerifyButton(x, y) {
  cleanupFloatingUi();

  buttonEl = document.createElement("button");
  buttonEl.textContent = "Verify claim";
  buttonEl.id = "truthlens-verify-button";
  buttonEl.style.position = "absolute";
  buttonEl.style.left = `${x}px`;
  buttonEl.style.top = `${y}px`;
  buttonEl.style.zIndex = "2147483647";
  buttonEl.style.padding = "8px 12px";
  buttonEl.style.border = "1px solid rgba(44, 141, 255, 0.38)";
  buttonEl.style.borderRadius = "999px";
  buttonEl.style.background = "linear-gradient(90deg, #00bfff 0%, #2f7cff 52%, #7a3dff 100%)";
  buttonEl.style.color = "#eef6ff";
  buttonEl.style.fontFamily = "\"Sora\", \"Space Grotesk\", sans-serif";
  buttonEl.style.fontSize = "12px";
  buttonEl.style.fontWeight = "650";
  buttonEl.style.cursor = "pointer";
  buttonEl.style.boxShadow = "0 8px 22px rgba(20, 92, 255, 0.44), 0 0 14px rgba(0, 202, 255, 0.35)";
  buttonEl.addEventListener("click", verifyCurrentSelection);

  document.body.appendChild(buttonEl);
}

function getSelectionText() {
  const text = window.getSelection ? window.getSelection().toString() : "";
  return (text || "").replace(/\s+/g, " ").trim();
}

function updateSelectionUi() {
  const selection = window.getSelection();
  const claim = getSelectionText();

  if (!selection || !claim || claim.length < MIN_SELECTION_LENGTH || selection.rangeCount === 0) {
    selectedClaim = "";
    cleanupFloatingUi();
    return;
  }

  selectedClaim = claim;
  const range = selection.getRangeAt(0);
  const rect = range.getBoundingClientRect();

  if (!rect || (rect.width === 0 && rect.height === 0)) {
    cleanupFloatingUi();
    return;
  }

  const x = window.scrollX + rect.left;
  const y = window.scrollY + rect.bottom + 8;
  renderVerifyButton(x, y);
}

document.addEventListener("mouseup", () => {
  setTimeout(updateSelectionUi, 10);
});

document.addEventListener("keyup", (event) => {
  if (event.key === "Shift" || event.key === "ArrowLeft" || event.key === "ArrowRight" || event.key === "ArrowUp" || event.key === "ArrowDown") {
    setTimeout(updateSelectionUi, 10);
  }
});

document.addEventListener("scroll", () => {
  if (buttonEl && selectedClaim) {
    updateSelectionUi();
  }
}, true);

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (!message || !message.type) {
    return;
  }

  if (message.type === "GET_SELECTION") {
    sendResponse({ ok: true, data: { selection: getSelectionText() } });
  }
});
