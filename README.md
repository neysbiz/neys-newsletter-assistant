# Neys Newsletter Assistant

Eigenes Newsletter-Werkzeug für Text/Bilder, nachvollziehbare Zustimmung und kontrollierten Versand. Einstieg: [Roadmap](docs/ROADMAP.md), [Workflow](docs/development_workflow.md), [Benutzerführung](docs/userGuide.md), [Technik](docs/technicalDescription.md).

## Lokal auf dem Mac

Im Repository-Root mit Python 3.13 und Docker Desktop:

```bash
git pull --ff-only
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.lock
cp .env.example .env
```

In `.env` lokale Secret-/Datenbankpasswörter ersetzen; Passwort in `DATABASE_URL` und `POSTGRES_PASSWORD` identisch setzen (URL-Sonderzeichen percent-encodieren).

```bash
docker compose up -d postgres redis
python backend/manage.py migrate
python backend/manage.py createsuperuser
python backend/manage.py runserver 127.0.0.1:8005
```

Verwaltung: http://localhost:8005/manage/ · Admin: /admin/ · Health: /health/.
In zwei weiteren Terminals jeweils venv aktivieren, dann:

```bash
cd backend
celery -A config worker --loglevel=INFO --concurrency=2
# Im anderen Terminal:
celery -A config beat --loglevel=INFO
```

Alternativ alle Prozesse in Docker: `docker compose up --build -d`, dann `docker compose exec web python manage.py migrate` und `docker compose exec web python manage.py createsuperuser`. Compose ist die lokale Entwicklungsumgebung. Kein produktiver Deploymentbefehl.

## Prüfen

```bash
DJANGO_SETTINGS_MODULE=config.settings.test python backend/manage.py check
DJANGO_SETTINGS_MODULE=config.settings.test python backend/manage.py makemigrations --check --dry-run
pytest -q
ruff check .
ruff format --check .
```

Tests benötigen laufendes PostgreSQL; pytest erzeugt/löscht eine eigene Testdatenbank. Niemals Produktionszugang für Tests verwenden. Console-Backend sendet keine echte E-Mail. SMTP-Anbieter, öffentliche Domain und Trackingfreigabe sind offen.
