import re
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from .models import Asset

PLACEHOLDER = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")


def validate_copy(text, max_length):
    if not isinstance(text, str) or len(text) > max_length:
        raise ValidationError("Text fehlt oder ist zu lang.")
    for name in PLACEHOLDER.findall(text):
        if name != "email":
            raise ValidationError(f"Unbekannter Platzhalter: {name}")
    remainder = PLACEHOLDER.sub("", text)
    if "{{" in remainder or "}}" in remainder:
        raise ValidationError("Unvollständiger Platzhalter.")
    return text


def validate_https_url(value):
    if not isinstance(value, str) or len(value) > 2000:
        raise ValidationError("Ungültige URL.")
    URLValidator(schemes=["https"])(value)
    parts = urlsplit(value)
    if parts.username or parts.password or any(ord(c) < 32 for c in value):
        raise ValidationError("URL darf keine Zugangsdaten oder Steuerzeichen enthalten.")
    return value


def validate_blocks(blocks):
    if not isinstance(blocks, list) or not 1 <= len(blocks) <= 20:
        raise ValidationError("Bitte 1 bis 20 Inhaltsblöcke anlegen.")
    result = []
    for block in blocks:
        if not isinstance(block, dict):
            raise ValidationError("Ungültiger Inhaltsblock.")
        kind = block.get("type")
        if kind == "text":
            text = validate_copy(block.get("text"), 10000)
            if not text.strip():
                raise ValidationError("Textblock ist leer.")
            result.append({"type": kind, "text": text})
        elif kind == "link":
            label = validate_copy(block.get("label"), 200)
            if not label.strip():
                raise ValidationError("Linkbeschriftung fehlt.")
            result.append(
                {"type": kind, "label": label, "url": validate_https_url(block.get("url"))}
            )
        elif kind == "image":
            alt = validate_copy(block.get("alt"), 300)
            if not alt.strip():
                raise ValidationError("Alternativtext fehlt.")
            try:
                asset = Asset.objects.get(pk=block.get("asset_id"))
            except (Asset.DoesNotExist, ValidationError, ValueError, TypeError) as error:
                raise ValidationError("Bild wurde nicht gefunden.") from error
            result.append({"type": kind, "asset_id": str(asset.id), "alt": alt})
        else:
            raise ValidationError("Unbekannter Inhaltstyp.")
    return result
