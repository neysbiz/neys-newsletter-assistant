from django.db.models import Q

from .models import Contact


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
