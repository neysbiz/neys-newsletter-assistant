from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.consents.models import RateLimitBucket


class Command(BaseCommand):
    help = "Delete expired, hashed rate-limit buckets; never deletes consent evidence."

    def handle(self, *args, **options):
        count, _ = RateLimitBucket.objects.filter(expires_at__lt=timezone.now()).delete()
        self.stdout.write(f"Deleted {count} expired rate-limit buckets")
