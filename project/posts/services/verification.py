from django.core import signing
from django.conf import settings
from django.utils import timezone

# Purpose is user verification or post verification, can be extended to other use cases as needed
def generate_signed_token(user_id: int, purpose: str) -> str:
    payload = {
        "uid": str(user_id),
        "purpose": purpose,
        "iat": int(timezone.now().timestamp())
    }
    signer = signing.TimestampSigner(salt="posts-signed-tokens")  # use an app-specific salt
    signed = signer.sign_object(payload)
    return signed


def verify_signed_token(token: str, expected_purpose: str, max_age_seconds: int = 600) -> int:
    signer = signing.TimestampSigner(salt="posts-signed-tokens")
    try:
        payload = signer.unsign_object(token, max_age=max_age_seconds)
    except signing.SignatureExpired:
        raise ValueError("Token expired")
    except signing.BadSignature:
        raise ValueError("Invalid token")

    if payload.get("purpose") != expected_purpose:
        raise ValueError("Token purpose mismatch")

    uid = payload.get("uid")
    if not uid:
        raise ValueError("Invalid token payload")
    return uid
