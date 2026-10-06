# ADR 0001 – Projektbasis

06.10.2026. Modularer Django-Monolith nach Original-Neys-Baseline. SSR-Templates und zentrale CSS/Layoutkomponenten sind für Verwaltung und öffentliche Formulare ausreichend. Keine SPA/WebSockets ohne konkreten Bedarf. Standardtests pytest/pytest-django auf PostgreSQL.

Python 3.13 für Docker und CI; 3.12 ebenfalls unterstützt. Django 5.2 LTS/Celery 5.6 nach offiziellen Release-/Integrationsdokumenten geprüft:
- https://docs.djangoproject.com/en/5.2/releases/5.2/
- https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html

Lokale Defaultports 8005/55435/6385 sind neue, konfigurierbare Projektdefaults, keine zugesicherte Prüfung der Mac-Portbelegung. Testsettings wählen keine SQLite-Ersatzdatenbank. Console-E-Mail ist ein expliziter Entwicklungsadapter, kein stiller SMTP-Fallback. Produktionsversand und Tracking folgen späteren Entscheidungen.

Roadmap im Git ist seit Repo-Anbindung führend. Notion-Synchronisierung ist ohne projektspezifische Zuordnung nicht eingerichtet.
