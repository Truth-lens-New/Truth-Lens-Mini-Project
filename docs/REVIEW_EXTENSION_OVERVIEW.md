# Chrome Extension Review Notes

This file explains how the TruthLens extension works end-to-end.

## 1) Manifest and Runtime Model

Source: `chrome-extension/manifest.json`

```json
{
  "manifest_version": 3,
  "background": { "service_worker": "background.js" },
  "action": { "default_popup": "popup.html" },
  "permissions": ["storage", "activeTab", "scripting"],
  "content_scripts": [{ "matches": ["http://*/*", "https://*/*"], "js": ["content.js"] }]
}
```

What to say:
- MV3 architecture with service worker (`background.js`) as main coordinator.
- `popup.js` is control panel, `content.js` handles on-page selection and floating UI.

## 2) Background Service Worker (Core Logic)

Source: `chrome-extension/background.js`

```javascript
async function verifyClaim(claimText) {
  const { authToken } = await getSettings();
  if (!authToken) {
    const authError = new Error("Please login in the TruthLens extension popup first.");
    authError.code = "AUTH_REQUIRED";
    throw authError;
  }

  const segments = splitIntoCandidateClaims(claimText);
  const results = await Promise.allSettled(
    segments.map((segment) => investigateText(segment, authToken))
  );
  ...
}
```

```javascript
function splitIntoCandidateClaims(text) {
  const parts = normalized.match(/[^.!?]+[.!?]?/g) || [normalized];
  const meaningful = unique.filter((part) => part.length >= 12);
  return (meaningful.length ? meaningful : unique).slice(0, 8);
}
```

```javascript
function mapEvidenceItem(item) {
  const sourceUrl = normalizeEvidenceUrl(item && item.source_url, domain);
  return {
    sourceUrl,
    sourceDomain: domain,
    sourceType: item && item.source_type ? item.source_type : "web_search",
    stance: item && item.stance ? item.stance : "neutral"
  };
}
```

What to say:
- Claim text is split into multiple sentence-level candidates to avoid missing later statements.
- Evidence items are normalized and include source links (`sourceUrl`) for opening references directly.

## 3) Message Bus Contract

Source: `chrome-extension/background.js`

```javascript
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  switch (message.type) {
    case "GET_SETTINGS":
    case "SAVE_BACKEND_URL":
    case "REGISTER":
    case "LOGIN":
    case "SET_AUTH_TOKEN":
    case "LOGOUT":
    case "VERIFY_CLAIM":
      ...
  }
});
```

What to say:
- Popup and content script talk only through typed runtime messages.
- This keeps API calls/auth logic centralized in one place.

## 4) Popup UX + Web Login Sync

Source: `chrome-extension/popup.js`

```javascript
async function importWebSessionToken() {
  const results = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => localStorage.getItem("token") || ""
  });

  const response = await fetch(`${backendUrl}/auth/me`, {
    headers: { "Authorization": `Bearer ${token}` }
  });

  chrome.storage.local.set({ authToken: token, authEmail, backendUrl });
}
```

What to say:
- Extension can import existing web app token so users do not log in twice.
- Token is validated against backend (`/auth/me`) before saving.

## 5) Content Script In-Page Verification

Source: `chrome-extension/content.js`

```javascript
async function verifyCurrentSelection() {
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
```

What to say:
- User highlights text -> content script sends verify request -> renders floating card with verdict + sources.
- The same structured claim/evidence payload powers both popup and in-page card.

## 6) Styling Alignment with Website

Source: `chrome-extension/popup.css`

```css
:root {
  --bg: #040812;
  --cyan: #05d5ff;
  --blue: #2f7cff;
  --violet: #7d3cff;
}

button {
  background: linear-gradient(90deg, #00b9ff 0%, #2f7cff 48%, #6b39ff 100%);
}
```

What to say:
- Extension theme reuses dark neon palette and gradients similar to the web app hero aesthetic.

## 30-Second Review Pitch

- "Background service worker is the brain; popup and content are thin clients."
- "We split long text into candidate claims so each statement gets verified independently."
- "Results include source links and can be shown in popup or directly on the webpage."
