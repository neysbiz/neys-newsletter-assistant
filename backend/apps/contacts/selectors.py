from .models import Contact


def contact_list(query=""):
    contacts = Contact.objects.select_related("subscription").order_by("email_key")
    if query:
        contacts = contacts.filter(email_key__icontains=query.casefold())
    return contacts[:300]
