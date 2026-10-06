from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from .rendering import render_revision


def send_test_mail(revision, recipient):
    content = render_revision(
        revision,
        email=recipient,
        unsubscribe_url=settings.PUBLIC_BASE_URL + "/test-unsubscribe/",
    )
    message = EmailMultiAlternatives(
        content.subject,
        content.text,
        settings.DEFAULT_FROM_EMAIL,
        [recipient],
    )
    message.attach_alternative(content.html, "text/html")
    return message.send(fail_silently=False)
