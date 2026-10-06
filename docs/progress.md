# Fortschritt

## 06.10.2026 – M0 Projektbasis

Branch `feat/m0-project-basis`, Ausgangscommit `f640a04` (nur Roadmap). Repository sauber und Remote identisch vor Start. Mac-Dateisystem ist hier nicht erreichbar.

Original-Neys-Workflow/AGENTS aus project-template gelesen; Architekturbaseline aus neys-game-world übernommen. pytest/pytest-django/Ruff, getrennte Settings, Staff-Verwaltungszugang, zentrale Templates/CSS, PostgreSQL 17/Redis 7/Celery Worker/Beat in Development-Compose, Lockfiles und CI eingerichtet.

Lokal: Django-Systemcheck und Ruff erfolgreich, `git diff --check` sauber. Laufzeit Python 3.12.14, Django 5.2.17/Celery 5.6.3. Docker fehlt; lokale PostgreSQL-Installation/-Benutzerwechsel nicht möglich. Keine SQLite-Ersatzprüfung. Vollständige Test-/Migrations-/Broker-/Worker-Abnahme in CI noch offen. Kein Deployment, keine echten Mails/Daten.
