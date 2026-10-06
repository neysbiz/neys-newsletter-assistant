from apps.contacts.models import Suppression


def can_send_campaign(contact_id):
    # Fresh query at every delivery attempt; never rely on a cached recipient snapshot.
    from apps.consents.models import Subscription

    return (
        Subscription.objects.filter(contact_id=contact_id, status="active").exists()
        and not Suppression.objects.filter(contact_id=contact_id).exists()
    )
