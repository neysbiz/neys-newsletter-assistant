from django.db.models import Q
from django.utils import timezone

from .models import Contact, ImportBatch


def contact_list(query=""):
    contacts = (
        Contact.objects.select_related("subscription")
        .prefetch_related("mailchimprecord_set")
        .order_by("email_key")
    )
    if query:
        contacts = contacts.filter(
            Q(email_key__icontains=query.casefold())
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
        )
    return contacts[:300]


def import_preview(batch):
    if batch.expires_at <= timezone.now() and batch.status == "preview":
        return {"rows": [], "errors": 0, "duplicates": 0, "can_apply": False}
    keys = [entry["email"].strip().casefold() for entry in batch.rows if not entry["errors"]]
    existing = {
        key: ("Gesperrt" if reason else status or "Kein Abonnement")
        for key, status, reason in Contact.objects.filter(email_key__in=keys).values_list(
            "email_key", "subscription__status", "suppression__reason"
        )
    }
    rows = []
    for entry in batch.rows:
        row = dict(entry)
        row["local_status"] = existing.get(entry["email"].strip().casefold(), "new")
        rows.append(row)
    return {
        "rows": rows,
        "errors": sum(bool(entry["errors"]) for entry in rows),
        "duplicates": sum(entry["duplicate"] for entry in rows),
        "can_apply": batch.status == "preview"
        and batch.expires_at > timezone.now()
        and bool(rows)
        and not any(entry["errors"] for entry in rows),
    }


def recent_imports(actor):
    return ImportBatch.objects.filter(owner=actor).order_by("-created_at")[:10]
