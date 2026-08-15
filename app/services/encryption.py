"""
Real Fernet-based encryption for stored integration credentials.

Credential.encrypted_data was named "encrypted" but nothing ever
encrypted it - config.encryption_key existed but had zero consumers
anywhere in the app. This closes that gap. Falls back to storing
plaintext (with a logged warning) if no real key is configured, rather
than crashing - an honest degraded state, matching how the rest of this
fleet's optional-but-important config gaps are handled.
"""

import json

from cryptography.fernet import Fernet
from loguru import logger

from app.config import settings


def _get_fernet():
    if not settings.encryption_key:
        return None
    try:
        return Fernet(settings.encryption_key.encode())
    except (ValueError, TypeError) as exc:
        logger.error(f"ENCRYPTION_KEY is set but not a valid Fernet key ({exc}) - storing credentials unencrypted")
        return None


def encrypt_credentials(data: dict) -> dict:
    """Real encryption when a key is configured; honest plaintext fallback (flagged) otherwise."""
    fernet = _get_fernet()
    if fernet is None:
        logger.warning("ENCRYPTION_KEY not configured - storing integration credentials unencrypted")
        return {"encrypted": False, "data": data}

    token = fernet.encrypt(json.dumps(data).encode())
    return {"encrypted": True, "ciphertext": token.decode()}


def decrypt_credentials(stored: dict) -> dict:
    if not stored.get("encrypted"):
        return stored.get("data", {})

    fernet = _get_fernet()
    if fernet is None:
        raise ValueError("Cannot decrypt stored credentials: ENCRYPTION_KEY is not configured")

    return json.loads(fernet.decrypt(stored["ciphertext"].encode()).decode())
