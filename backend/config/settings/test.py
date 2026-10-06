import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-key-never-use-in-production")
os.environ.setdefault(
    "DATABASE_URL", "postgresql://newsletter:newsletter@127.0.0.1:55435/newsletter"
)
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:6385/0")
from .base import *  # noqa: E402, F403

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
