# Technische Beschreibung

Modularer Django-Monolith. `accounts` besitzt Verwaltungszugang; `operations` Health-/Workerdiagnose. Fachliche Schreibabläufe gehören in Services, komplexe Leseabfragen in Selectors. PostgreSQL ist die Datenquelle; Redis ist Celery-Broker/Resultbackend. Celery Beat einmal pro Umgebung betreiben. `/health/` prüft Datenbank und Redis, nicht den Worker; Worker separat mit `celery -A config inspect ping` prüfen.

Development/Test/Production-Settings getrennt. Production erzwingt HTTPS und sichere Cookies. Reverse-Proxy-Vertrauen erst mit konkreter IONOS-Konfiguration festlegen; keine ungeprüfte Forwarded-Header-Freigabe. Token-URLs nicht in Proxy-/Zugriffslogs speichern. Laufzeit-Logs zeigen keine Exceptiondetails im öffentlichen Healthcheck.

Docker Compose ist nur für lokale Entwicklung. Ports binden an Loopback; PostgreSQL/Redis haben getrennte persistente Volumes. Produktionshosting, Secretversorgung, Backups/Restore und Domain sind M6, derzeit nicht eingerichtet.
