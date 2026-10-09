from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parents[2]
ROOT_DIR = BASE_DIR.parent
env = environ.Env()
environ.Env.read_env(ROOT_DIR / ".env", overwrite=False)
SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = False
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.accounts",
    "apps.operations",
    "apps.contacts",
    "apps.consents",
    "apps.campaigns",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "apps.consents.middleware.ConsentPagePrivacyMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {"default": env.db("DATABASE_URL")}
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "de"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = ROOT_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/manage/"
LOGOUT_REDIRECT_URL = LOGIN_URL
REDIS_URL = env("REDIS_URL")
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_RESULT_SERIALIZER = "json"
CELERY_RESULT_EXPIRES = 300
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="newsletter@example.invalid")
EMAIL_TIMEOUT = 10
PUBLIC_BASE_URL = env("PUBLIC_BASE_URL", default="http://localhost:8005").rstrip("/")
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"sensitive_paths": {"()": "apps.operations.logging.SensitivePathFilter"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "filters": ["sensitive_paths"]}},
    "root": {"handlers": ["console"], "level": "INFO"},
    # Public token paths must not enter access logs; configure proxy logs likewise.
    "loggers": {"django.server": {"handlers": ["console"], "level": "ERROR", "propagate": False}},
}

NEWSLETTER_CONSENT_VERSION = env("NEWSLETTER_CONSENT_VERSION", default="development-v1")
NEWSLETTER_CONSENT_TEXT = env(
    "NEWSLETTER_CONSENT_TEXT",
    default=(
        "Entwicklungsformular: Ich möchte den Newsletter per E-Mail erhalten "
        "und kann mich jederzeit abmelden."
    ),
)
NEWSLETTER_PRIVACY_VERSION = env("NEWSLETTER_PRIVACY_VERSION", default="development-v1")
NEWSLETTER_PRIVACY_TEXT = env(
    "NEWSLETTER_PRIVACY_TEXT",
    default=(
        "Entwicklung: E-Mail-Adresse und Einwilligungsnachweis werden für den Newsletter "
        "gespeichert. Keine echte Zustellung."
    ),
)
# Enable only with a documented retention policy and corresponding privacy notice.
NEWSLETTER_STORE_EVIDENCE_IP = env.bool("NEWSLETTER_STORE_EVIDENCE_IP", default=False)
CELERY_BEAT_SCHEDULE = {
    "clear-import-previews": {
        "task": "apps.contacts.tasks.clear_expired_import_previews",
        "schedule": 1800.0,
    },
    "dispatch-confirmations": {
        "task": "apps.consents.tasks.dispatch_pending_confirmations",
        "schedule": 30.0,
    },
}

MEDIA_URL = "/media-images/"
MEDIA_ROOT = ROOT_DIR / "media"
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
