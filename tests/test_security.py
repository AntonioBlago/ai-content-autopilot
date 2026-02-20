"""Tests for HMAC-SHA256 webhook signature verification."""

import hashlib
import hmac

import pytest

from ai_content_autopilot.security import verify_webhook_signature


class TestVerifyWebhookSignature:
    """Test verify_webhook_signature function."""

    def _make_signature(self, payload: bytes, secret: str) -> str:
        """Helper: compute a valid sha256=... signature."""
        mac = hmac.new(secret.encode('utf-8'), payload, hashlib.sha256)
        return f"sha256={mac.hexdigest()}"

    def test_valid_signature(self):
        """Correct HMAC should return True."""
        payload = b'{"event": "article.approved", "article_id": 42}'
        secret = 'test_secret_abc123'
        sig = self._make_signature(payload, secret)
        assert verify_webhook_signature(payload, secret, sig) is True

    def test_wrong_secret(self):
        """Wrong secret should return False."""
        payload = b'{"event": "article.approved"}'
        sig = self._make_signature(payload, 'correct_secret')
        assert verify_webhook_signature(payload, 'wrong_secret', sig) is False

    def test_tampered_payload(self):
        """Tampered payload should return False."""
        payload = b'{"amount": 100}'
        sig = self._make_signature(payload, 'secret')
        tampered = b'{"amount": 999}'
        assert verify_webhook_signature(tampered, 'secret', sig) is False

    def test_empty_signature_header(self):
        """Empty signature header should return False."""
        assert verify_webhook_signature(b'{}', 'secret', '') is False

    def test_none_signature_header(self):
        """None signature header should return False."""
        assert verify_webhook_signature(b'{}', 'secret', None) is False

    def test_missing_sha256_prefix(self):
        """Signature without sha256= prefix should return False."""
        payload = b'{"test": true}'
        secret = 'secret'
        mac = hmac.new(secret.encode('utf-8'), payload, hashlib.sha256)
        sig_no_prefix = mac.hexdigest()
        assert verify_webhook_signature(payload, secret, sig_no_prefix) is False

    def test_wrong_prefix(self):
        """Signature with wrong prefix should return False."""
        payload = b'test'
        secret = 'secret'
        mac = hmac.new(secret.encode('utf-8'), payload, hashlib.sha256)
        sig = f"md5={mac.hexdigest()}"
        assert verify_webhook_signature(payload, secret, sig) is False

    def test_empty_payload(self):
        """Empty payload with valid signature should verify."""
        payload = b''
        secret = 'secret'
        sig = self._make_signature(payload, secret)
        assert verify_webhook_signature(payload, secret, sig) is True

    def test_unicode_secret(self):
        """Secret with unicode characters should work."""
        payload = b'{"data": "test"}'
        secret = 'geheim-schluessel-2026'
        sig = self._make_signature(payload, secret)
        assert verify_webhook_signature(payload, secret, sig) is True

    def test_large_payload(self):
        """Large payload should verify correctly."""
        payload = b'x' * 100_000
        secret = 'secret'
        sig = self._make_signature(payload, secret)
        assert verify_webhook_signature(payload, secret, sig) is True