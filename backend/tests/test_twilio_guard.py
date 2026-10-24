"""
Tests for Twilio webhook signature validation (app/core/twilio_guard.py).
Pure stdlib: signatures are computed both with the module and an independent
reference HMAC implementation to cross-check correctness.
"""

import base64
import hashlib
import hmac

import pytest

from import_utils import isolated_imports


@pytest.fixture(scope="module")
def guard():
    with isolated_imports(["app", "app.core"]) as imp:
        yield imp("app.core.twilio_guard")


def _reference_signature(auth_token: str, url: str, params: dict) -> str:
    """Independent re-implementation of Twilio's documented algorithm."""
    data = url + "".join(k + v for k, v in sorted(params.items()))
    mac = hmac.new(auth_token.encode(), data.encode(), hashlib.sha1)
    return base64.b64encode(mac.digest()).decode()


AUTH_TOKEN = "test-auth-token-123"
URL = "https://demo.example.com/api/v1/whatsapp"


class TestSignatureValidation:
    def test_valid_signature_is_accepted(self, guard):
        params = {"To": "whatsapp:+15551234567", "From": "whatsapp:+14155238886", "Body": "hello"}
        sig = _reference_signature(AUTH_TOKEN, URL, params)
        assert guard.is_valid_twilio_signature(AUTH_TOKEN, URL, params, sig) is True

    def test_module_signature_matches_reference(self, guard):
        params = {"a": "1", "b": "2", "c": "3"}
        assert guard.compute_twilio_signature(AUTH_TOKEN, URL, params) == _reference_signature(AUTH_TOKEN, URL, params)

    def test_tampered_signature_is_rejected(self, guard):
        params = {"Body": "hello"}
        good = _reference_signature(AUTH_TOKEN, URL, params)
        bad = ("A" if good[0] != "A" else "B") + good[1:]
        assert guard.is_valid_twilio_signature(AUTH_TOKEN, URL, params, bad) is False

    def test_wrong_url_is_rejected(self, guard):
        params = {"Body": "hello"}
        sig = _reference_signature(AUTH_TOKEN, URL, params)
        assert guard.is_valid_twilio_signature(AUTH_TOKEN, URL + "/", params, sig) is False

    def test_missing_signature_is_rejected(self, guard):
        assert guard.is_valid_twilio_signature(AUTH_TOKEN, URL, {"Body": "hi"}, None) is False
        assert guard.is_valid_twilio_signature(AUTH_TOKEN, URL, {"Body": "hi"}, "") is False

    def test_missing_auth_token_is_rejected(self, guard):
        params = {"Body": "hi"}
        sig = _reference_signature(AUTH_TOKEN, URL, params)
        assert guard.is_valid_twilio_signature("", URL, params, sig) is False

    def test_param_injection_is_rejected(self, guard):
        """Adding params changes the signature: replay with extra fields fails."""
        params = {"Body": "hi"}
        sig = _reference_signature(AUTH_TOKEN, URL, params)
        injected = dict(params, From="whatsapp:+9999999")
        assert guard.is_valid_twilio_signature(AUTH_TOKEN, URL, injected, sig) is False
