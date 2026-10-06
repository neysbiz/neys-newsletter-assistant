# Fortschritt

## 06.10.2026 – M0 Projektbasis

Branch `feat/m0-project-basis`, Ausgangscommit `f640a04` (nur Roadmap). Repository sauber und Remote identisch vor Start. Mac-Dateisystem ist hier nicht erreichbar.

Original-Neys-Workflow/AGENTS aus project-template gelesen; Architekturbaseline aus neys-game-world übernommen. pytest/pytest-django/Ruff, getrennte Settings, Staff-Verwaltungszugang, zentrale Templates/CSS, PostgreSQL 17/Redis 7/Celery Worker/Beat in Development-Compose, Lockfiles und CI eingerichtet.

Lokal: Django-Systemcheck und Ruff erfolgreich, `git diff --check` sauber. Laufzeit Python 3.12.14, Django 5.2.17/Celery 5.6.3. Docker fehlt; lokale PostgreSQL-Installation/-Benutzerwechsel nicht möglich. Keine SQLite-Ersatzprüfung. Vollständige Test-/Migrations-/Broker-/Worker-Abnahme in CI noch offen. Kein Deployment, keine echten Mails/Daten.

## 06.10.2026 – M1 Zustimmung/DOI/Abmeldung

Branch `feat/m1-consent`, lokale Basis M0 `7d597c4`. Kontakte/Newsletterstatus/Nachweise/Sperren, signierte zweckgebundene Referenzen, DOI-Ablauf/Cooldown/Rate-Limits, durable ConfirmationMessage-Aufträge mit sichtbarem unklaren Ausgang, schreibende Services, Staff-Kontaktliste und idempotente Abmeldung implementiert. Token-Pfade in Logs maskiert, Referrer/Cache auf öffentlichen Token-Seiten eingeschränkt. Tracking deaktiviert. Migrationen erzeugt.

Portable lokale Funktionsprüfungen mit temporärem SQLite-Harness bestehen (keine PostgreSQL- oder Locking-Bestätigung); echte Infrastruktur und Parallelitätsprüfung nur in obligatorischer PostgreSQL/Redis-CI. Produktionsformulierung/DNS/Versandweg/Importdaten bleiben offen. Automatische Freigabeprüfung hat GitHub-Push als nicht ausdrücklich autorisierte Veröffentlichung blockiert; kein Umgehungsversuch, Remote verbleibt bei `f640a04`. Mac unverändert.

## 06.10.2026 – M3 Editor/Rendering

Branch `feat/m3-editor`, Basis `0bea0a8`, Implementierungscommit `7071d88`. Formset-Editor, Bildverwaltung, sichere URLs/Platzhalter, neu kodierte PNG/JPEG-Uploads, eingefrorene CampaignRevision-Snapshots, Asset-Löschschutz, identisches Rendering für Vorschau/Testmail implementiert. Permissiondecorator und ReadOnlyAdmin zentral in accounts, Bildvolume in Compose ergänzt. Plaintext-Rendering ohne HTML-Escaping, HTML-Rendering mit Escaping. Neutrale Entwicklungsvorlage, SimplyNeys-CI-Abgleich offen.

Tatsächlich geprüft: 47 Funktionsprüfungen erfolgreich in temporärem SQLite-Harness unter Python 3.12.14 und sauberer Python-3.13.15-Umgebung mit requirements-dev.lock. Django check, Migrationsdelta-Check (temporäres SQLite), Ruff lint/format, pip check, git diff --check erfolgreich. Echter Celery-Broker/Worker-Rundlauf separat gegen lokalen Redis 6.2.14 erfolgreich (1 Test). Erstversuch aus getrennten Prozessumgebungen scheiterte an fehlender Verbindung; im gemeinsamen isolierten Prozess mit laufendem Redis erfolgreich. Produktions-/Compose-Ziel Redis 7 nicht damit als geprüft ausweisen.

PostgreSQL/Parallelitätsgate, Docker-Start und GitHub CI bleiben offen. SSR-Seiten für Editor, öffentliche Anmeldung und Revisionvorschau tatsächlich mit Django Client gerendert (HTTP 200); keine Browser-Screenshot-/Mobile-Abnahme, Chromium-Download hier gescheitert. Outlook/Apple-Mail/Gmail ebenfalls nicht praktisch geprüft. Kein Produktivdeploy und keine echten Mails. Remote ausschließlich Ausgangsroadmap, Mac unverändert.

Lokale Integrationsreihenfolge: M0 `7d597c4` → M1 `0bea0a8` → M3 `7071d88`, jeweils lokaler Fast-Forward auf main. Kein paralleler aktiver Featurekontext. Lokale Integration ist keine vollständige Abnahme. Handoff-Dokumentation auf eigenem docs-Branch.
