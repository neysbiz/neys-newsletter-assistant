from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

if len(SECRET_KEY) < 50 or SECRET_KEY.startswith("replace-"):  # noqa: F405
    raise ImproperlyConfigured(
        "Production requires a random DJANGO_SECRET_KEY of at least 50 chars"
    )
if not PUBLIC_BASE_URL.startswith("https://"):  # noqa: F405
    raise ImproperlyConfigured("PUBLIC_BASE_URL must use HTTPS in production")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False

if NEWSLETTER_CONSENT_VERSION.startswith("development-"):  # noqa: F405
    raise ImproperlyConfigured("Production requires an approved newsletter consent text/version")
if NEWSLETTER_PRIVACY_VERSION.startswith("development-"):  # noqa: F405
    raise ImproperlyConfigured("Production requires an approved privacy notice text/version")
