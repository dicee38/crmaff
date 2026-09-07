import hashlib
import hmac


def compute_hmac_signature(secret: str, payload: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def verify_hmac_signature(secret: str, payload: bytes, signature: str | None) -> bool:
    if not signature:
        return False
    expected = compute_hmac_signature(secret, payload)
    return hmac.compare_digest(expected, signature)
