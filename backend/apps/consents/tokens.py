from uuid import UUID

from django.core import signing


def encode_reference(reference, purpose):
    return signing.Signer(salt=f"newsletter.{purpose}.v1").sign(str(reference))


def decode_reference(token, purpose):
    try:
        value = signing.Signer(salt=f"newsletter.{purpose}.v1").unsign(token)
        return UUID(value)
    except (signing.BadSignature, ValueError, TypeError):
        return None
