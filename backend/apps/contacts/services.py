import uuid

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction

from .models import Contact, MailchimpRecord


def normalize_email(email):
    email = email.strip()
    validate_email(email)
    if len(email) > 254:
        raise ValidationError("E-Mail-Adresse zu lang")
    # Application policy: case-insensitive, no provider-specific rewrites.
    return email, email.casefold()


SOURCE_FIELDS = (
    "Vorname",
    "Name",
    "Erlaubnis zum Marketing",
    "MEMBER_RATING",
    "OPTIN_TIME",
    "OPTIN_IP",
    "CONFIRM_TIME",
    "CONFIRM_IP",
    "GMTOFF",
    "DSTOFF",
    "TIMEZONE",
    "CC",
    "REGION",
    "LAST_CHANGED",
    "LEID",
    "EUID",
    "NOTES",
    "TAGS",
    "SOURCE",
)


def prepare_mailchimp_row(row):
    """Validate a source row without writes. This contract accepts active exports only."""
    emails = [
        row[key].strip()
        for key in ("Emailadresse", "E-Mail-Adresse", "Email Address")
        if key in row
    ]
    if not emails or len({value.casefold() for value in emails}) != 1:
        raise ValidationError("Eine eindeutige Spalte Emailadresse ist erforderlich.")
    email, email_key = normalize_email(emails[0])
    source_status = row.get("Status", "subscribed").strip().casefold()
    if source_status not in ("active", "aktiv", "subscribed"):
        raise ValidationError("Diese Struktur akzeptiert nur aktive Mailchimp-Abonnenten.")
    flag = row.get("Erlaubnis zum Marketing")
    if flag is not None and flag.strip().casefold() not in ("", "x", "true", "false", "1", "0"):
        raise ValidationError("Unbekannte Marketingkennzeichnung.")
    data = {
        "email": email,
        "email_key": email_key,
        "first_name": row.get("Vorname", "").strip(),
        "last_name": row.get("Name", "").strip(),
        "source_status": "subscribed",
        "marketing_flag": None if flag is None else flag.strip().casefold() in ("x", "true", "1"),
        "leid": row.get("LEID", "").strip(),
        "euid": row.get("EUID", "").strip(),
        "source": row.get("SOURCE", "").strip(),
        "source_data": {key: row[key] for key in SOURCE_FIELDS if key in row},
    }
    for key, maximum in (
        ("first_name", 150),
        ("last_name", 150),
        ("leid", 80),
        ("euid", 80),
        ("source", 254),
    ):
        if len(data[key]) > maximum:
            raise ValidationError(f"Importfeld {key} ist zu lang.")
    return data


@transaction.atomic
def stage_mailchimp_contact(row, batch_id):
    """Stage a validated contact; never queue mail or create a consent evidence."""
    from apps.consents.models import Subscription

    data = prepare_mailchimp_row(row)
    batch_id = uuid.UUID(str(batch_id))
    contact, _ = Contact.objects.get_or_create(
        email_key=data["email_key"],
        defaults={key: data[key] for key in ("email", "first_name", "last_name")},
    )
    contact = Contact.objects.select_for_update().get(pk=contact.pk)
    Subscription.objects.get_or_create(
        contact=contact, defaults={"status": Subscription.Status.IMPORTED}
    )
    record, created = MailchimpRecord.objects.get_or_create(
        contact=contact,
        batch_id=batch_id,
        defaults={
            key: data[key]
            for key in ("source_status", "marketing_flag", "leid", "euid", "source", "source_data")
        },
    )
    if not created and any(
        getattr(record, key) != data[key]
        for key in ("source_status", "marketing_flag", "leid", "euid", "source", "source_data")
    ):
        raise ValidationError("Widersprüchliche Zeilen für dieselbe Adresse im Importlauf.")
    return contact, record, created
