from apps.contacts.imports import discard_expired_previews
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Clear personal row data from expired, unconfirmed import previews."

    def handle(self, *args, **options):
        self.stdout.write(f"Discarded {discard_expired_previews()} expired previews")
