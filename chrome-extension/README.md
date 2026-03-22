# TruthLens Chrome Extension (Local)

This extension lets you verify claims directly from any webpage using your local TruthLens backend.

## What it does

- Login/register against `http://localhost:8000`.
- Highlight text on a webpage and click **Verify claim**.
- Multi-sentence selections are split and verified claim-by-claim.
- Fetches verdicts from `POST /api/v3/investigate`.
- Shows clickable source links per claim (top sources + expand for more).

## Load in Chrome

1. Open `chrome://extensions`.
2. Turn on **Developer mode**.
3. Click **Load unpacked**.
4. Select this folder: `chrome-extension/`.

## Use it

1. Make sure backend is running on `http://localhost:8000`.
2. Open the extension popup and register/login.
3. To sync with web-app history, open the TruthLens web app tab and click **Use Web Login** in the extension popup.
4. Visit any `http/https` page.
5. Select text (at least ~18 chars).
6. Click the floating **Verify claim** button.

## Notes

- If verification fails with auth errors, login again in the popup.
- On restricted pages (`chrome://`, Web Store), content scripts are blocked by Chrome.
