import csv
import hashlib
import io
from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Contact, ImportBatch, Suppression
from .services import SOURCE_FIELDS, prepare_mailchimp_row, stage_mailchimp_contact

MAX_BYTES = 2 * 1024 * 1024
MAX_ROWS = 2000
EMAIL_COLUMNS = ("Emailadresse", "E-Mail-Adresse", "Email Address")
KNOWN_COLUMNS = (*EMAIL_COLUMNS, "Status", *SOURCE_FIELDS)


def require_operator(actor):
    if not actor.is_authenticated or not actor.is_active or not actor.is_staff:
        raise PermissionDenied


def parse_export(content, delimiter):
    if delimiter not in (",", ";", "\t"):
        raise ValidationError("Bitte ein unterstütztes Trennzeichen wählen.")
    if len(content) > MAX_BYTES:
        raise ValidationError("Die Datei darf höchstens 2 MiB groß sein.")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValidationError("Bitte die Datei als UTF-8-CSV oder UTF-8-TSV speichern.") from error
    if "\x00" in text:
        raise ValidationError("Die Datei enthält unzulässige Nullzeichen.")
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter, strict=True)
    rows, seen = [], {}
    try:
        headers = [value.strip() for value in next(reader, [])]
        if not headers or any(not value for value in headers) or len(set(headers)) != len(headers):
            raise ValidationError("Spaltenüberschriften fehlen oder sind doppelt vorhanden.")
        if len(headers) > 100 or any(len(value) > 254 for value in headers):
            raise ValidationError("Höchstens 100 Spalten mit Überschriften bis 254 Zeichen.")
        if not any(value in headers for value in EMAIL_COLUMNS):
            raise ValidationError(
                "E-Mail-Spalte nicht gefunden. Bitte auch das Trennzeichen prüfen."
            )
        for values in reader:
            if not values or all(not value.strip() for value in values):
                continue
            if len(rows) >= MAX_ROWS:
                raise ValidationError("Höchstens 2000 Datenzeilen pro Import.")
            number = reader.line_num
            entry = {"line": number, "email": "", "row": {}, "errors": [], "duplicate": False}
            if len(values) != len(headers):
                entry["errors"] = ["Die Zahl der Werte stimmt nicht mit den Spalten überein."]
            elif any(len(value) > 4096 for value in values):
                entry["errors"] = ["Ein Feld überschreitet 4096 Zeichen."]
            else:
                row = {
                    key: value
                    for key, value in zip(headers, values, strict=True)
                    if key in KNOWN_COLUMNS
                }
                entry["row"] = row
                entry["email"] = next((row[key] for key in EMAIL_COLUMNS if key in row), "")
                try:
                    prepared = prepare_mailchimp_row(row)
                    key = prepared["email_key"]
                    prepared["email"] = key  # Casing is not a conflicting address.
                    if key in seen:
                        if seen[key] == prepared:
                            entry["duplicate"] = True
                        else:
                            entry["errors"] = [
                                "Widersprüchliche Angaben zur selben E-Mail-Adresse."
                            ]
                    else:
                        seen[key] = prepared
                except ValidationError as error:
                    entry["errors"] = error.messages
            rows.append(entry)
    except csv.Error as error:
        raise ValidationError(
            "Ungültige CSV-Struktur. Trennzeichen und Anführungszeichen prüfen."
        ) from error
    if not rows:
        raise ValidationError("Die Datei enthält keine Datenzeilen.")
    return rows, [key for key in headers if key not in KNOWN_COLUMNS]


def create_import_preview(upload, delimiter, actor, active_export):
    require_operator(actor)
    if not active_export:
        raise ValidationError("Bitte bestätigen, dass die Datei nur aktive Abonnenten enthält.")
    content = upload.read(MAX_BYTES + 1)
    rows, ignored = parse_export(content, delimiter)
    return ImportBatch.objects.create(
        owner=actor,
        filename=upload.name[:254],
        file_sha256=hashlib.sha256(content).hexdigest(),
        delimiter=delimiter,
        ignored_columns=ignored,
        rows=rows,
        expires_at=timezone.now() + timedelta(minutes=30),
    )


@transaction.atomic
def apply_import(batch_id, actor):
    require_operator(actor)
    batch = ImportBatch.objects.select_for_update().get(pk=batch_id, owner=actor)
    if batch.status == "completed":
        return batch
    if batch.status != "preview" or batch.expires_at <= timezone.now():
        raise ValidationError("Die Vorschau ist verworfen oder abgelaufen. Bitte neu hochladen.")
    if not batch.rows or any(entry["errors"] for entry in batch.rows):
        raise ValidationError("Bitte alle Dateifehler korrigieren und die Datei neu hochladen.")
    result = {"new": 0, "existing": 0, "duplicates": 0, "blocked": 0}
    # Deterministic order reduces lock inversion for simultaneous imports.
    entries = sorted(batch.rows, key=lambda entry: prepare_mailchimp_row(entry["row"])["email_key"])
    for entry in entries:
        if entry["duplicate"]:
            result["duplicates"] += 1
            continue
        key = prepare_mailchimp_row(entry["row"])["email_key"]
        existed = Contact.objects.filter(email_key=key).exists()
        contact, _, _ = stage_mailchimp_contact(entry["row"], batch.id)
        result["existing" if existed else "new"] += 1
        if (
            contact.subscription.status == "unsubscribed"
            or Suppression.objects.filter(contact=contact).exists()
        ):
            result["blocked"] += 1
    batch.status = "completed"
    batch.completed_at = timezone.now()
    batch.result = result
    batch.rows = []  # Source snapshots now live in MailchimpRecord, not two copies.
    batch.save(update_fields=["status", "completed_at", "result", "rows"])
    return batch


@transaction.atomic
def cancel_import(batch_id, actor):
    require_operator(actor)
    batch = ImportBatch.objects.select_for_update().get(pk=batch_id, owner=actor)
    if batch.status == "preview":
        batch.status = "cancelled"
        batch.rows = []
        batch.save(update_fields=["status", "rows"])
    return batch


def discard_expired_previews():
    return ImportBatch.objects.filter(status="preview", expires_at__lte=timezone.now()).update(
        status="cancelled", rows=[]
    )
