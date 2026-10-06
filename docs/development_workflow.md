# Entwicklungsworkflow – Neys Newsletter Assistant

Abgeglichen am 06.10.2026 mit `neysbiz/project-template`, main `11c4f3e3b5de936cc259f1188b08a01257ba719a`, `AGENTS.md` und `docs/development_workflow.md`; Architekturoriginal aus `neysbiz/neys-game-world/main/docs/django_architecture_baseline.md` übernommen. Game-spezifische Regeln gelten hier nicht.

Vor technischen Eingriffen: `git status`, `git branch --show-current`, `git log -1 --oneline`, Remote prüfen. Pull ausschließlich `git pull --ff-only`. Divergenz analysieren; keine ungeprüften Resets/Rebases, kein Force-Push. Einen fachlichen Kontext in einem Branch abschließen und integrieren, bevor der nächste beginnt.

Runtime: Python 3.13 in Docker/CI; Python 3.12–3.14 unterstützt. Django 5.2 LTS, PostgreSQL 17, Redis 7, Celery 5.6. Frontend: Django-Templates/CSS, Vanilla-JS nur bei konkretem Bedarf. Kein Realtime-Bedarf, daher kein Channels/ASGI.

`pyproject.toml` definiert direkte und Dev-Abhängigkeiten. `requirements.lock` und `requirements-dev.lock` fixieren Auflösungen. Änderungen kontrolliert über `uv pip compile pyproject.toml -o requirements.lock` und `uv pip compile pyproject.toml --extra dev -o requirements-dev.lock` aktualisieren.

Standardgates im Repository-Root mit aktivierter `.venv`:

```bash
python backend/manage.py check
python backend/manage.py makemigrations --check --dry-run
pytest -q
ruff check .
ruff format --check .
```

Tests: `config.settings.test`, eigene von pytest angelegte PostgreSQL-Testdatenbank; niemals produktive DATABASE_URL. CI migriert zusätzlich eine frische Datenbank. Development nutzt `.env`; Produktion `config.settings.production`. Schemaänderungen vor Codefreigabe migrieren und Rollbackauswirkung dokumentieren.

Deploymentziel: IONOS, konkrete Instanz/Domain/Deploymentbranch noch nicht festgelegt. Kein automatischer Deploy. Vor Deploy Ziel, Branch, Commit, Working Tree, Tests/Migrationen prüfen; danach `migrate`, `check`, Healthcheck und Worker-Prüfung. `docker compose down -v` löscht lokale Daten und ist kein Routinebefehl.

Diagnose vor Reparatur: Fehler reproduzieren, Pfad/Branch/Commit/venv/Abhängigkeiten/Konfiguration prüfen, funktionierenden Stand vergleichen, erst dann ändern. Dokumentation wird im selben Commit aktualisiert. Keine Secrets oder Empfängerdaten im Git. Implementiert, lokal geprüft, remote integriert und produktiv eingesetzt sind getrennte Zustände.
