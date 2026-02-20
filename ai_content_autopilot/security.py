"""
HMAC-SHA256 signature verification for webhook payloads.

No external dependencies - uses only Python stdlib.
"""

import hashlib
import hmac


def verify_webhook_signature(payload_bytes: bytes, secret: str, signature_header: str) -> bool:
    """
    Verify HMAC-SHA256 webhook signature.

    Args:
        payload_bytes: Raw request body bytes
        secret: Webhook secret (plaintext)
        signature_header: Value of X-Webhook-Signature header (e.g. 'sha256=abc...')

    Returns:
        True if signature is valid, False otherwise
    """
    if not signature_header or not signature_header.startswith('sha256='):
        return False

    expected_mac = hmac.new(
        secret.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    )
    expected_sig = f"sha256={expected_mac.hexdigest()}"

    return hmac.compare_digest(expected_sig, signature_header)