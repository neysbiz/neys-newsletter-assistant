from django.core.management.base import BaseCommand

from apps.consents.delivery import dispatch_confirmations


class Command(BaseCommand):
    help = "Process pending DOI messages with the explicitly configured email backend."

    def handle(self, *args, **options):
        count = dispatch_confirmations()
        self.stdout.write(f"Processed {count} confirmation jobs")
