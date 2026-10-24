"""
Twilio Webhook Signature Validation

Verifies the X-Twilio-Signature header of inbound webhook requests so the
WhatsApp endpoint cannot be spoofed. Implemented with the standard library so it
works without importing the twilio SDK at request time.

Signature algorithm (Twilio docs):
    signature = Base64(HMAC-SHA1(auth_token, url + concat(sorted(key + value))))

The URL must be the exact externally-visible URL Twilio called (scheme, host,
and path). When running behind a proxy/tunnel that changes the scheme, set
TWILIO_WEBHOOK_PUBLIC_URL in settings to the public webhook URL.
"""

import base64
import hashlib
import hmac
from typing import Optional


def compute_twilio_signature(auth_token: str, url: str, params: dict) -> str:
    """Compute the expected X-Twilio-Signature for a request."""
    data = url + "".join(
        key + str(value) for key, value in sorted(params.items())
    )
    mac = hmac.new(
        auth_token.encode("utf-8"),
        data.encode("utf-8"),
        hashlib.sha1,
    )
    return base64.b64encode(mac.digest()).decode("ascii")


def is_valid_twilio_signature(
    auth_token: str,
    url: str,
    params: dict,
    signature: Optional[str],
) -> bool:
    """
    Validate an inbound Twilio request.

    Args:
        auth_token: Twilio auth token configured for this integration.
        url: The external URL Twilio requested (see module docstring).
        params: All POST form parameters of the request.
        signature: The X-Twilio-Signature header value (may be None/empty).

    Returns:
        True only when the signature matches; False for missing/invalid ones.
    """
    if not auth_token or not signature:
        return False
    expected = compute_twilio_signature(auth_token, url, params)
    return hmac.compare_digest(expected, str(signature))
