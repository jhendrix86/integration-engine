"""
Real HMAC-SHA256 webhook signature verification against a Webhook's own
`secret` column - previously that column existed and nothing ever read
it, so any payload was accepted regardless of origin.

Header convention: `X-Webhook-Signature: sha256=<hex digest>` (the same
shape GitHub/Stripe-style webhooks use), computed over the raw request
body using the registered secret.
"""

import hmac
import hashlib


def verify_signature(secret: str, raw_body: bytes, signature_header: str | None) -> bool:
    """True if the signature is valid. If no secret is registered, verification is skipped (returns True)."""
    if not secret:
        return True

    if not signature_header:
        return False

    prefix = "sha256="
    provided = signature_header[len(prefix):] if signature_header.startswith(prefix) else signature_header

    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, provided)
