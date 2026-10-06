from .models import Campaign


def campaign_list():
    return Campaign.objects.order_by("-updated_at")[:100]
