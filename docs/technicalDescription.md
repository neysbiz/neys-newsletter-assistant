# Technische Beschreibung

Modularer Django-Monolith. `accounts` besitzt Verwaltungszugang; `operations` Health-/Workerdiagnose. Fachliche Schreibabläufe gehören in Services, komplexe Leseabfragen in Selectors. PostgreSQL ist die Datenquelle; Redis ist Celery-Broker/Resultbackend. Celery Beat einmal pro Umgebung betreiben. `/health/` prüft Datenbank und Redis, nicht den Worker; Worker separat mit `celery -A config inspect ping` prüfen.

Development/Test/Production-Settings getrennt. Production erzwingt HTTPS und sichere Cookies. Reverse-Proxy-Vertrauen erst mit konkreter IONOS-Konfiguration festlegen; keine ungeprüfte Forwarded-Header-Freigabe. Token-URLs nicht in Proxy-/Zugriffslogs speichern. Laufzeit-Logs zeigen keine Exceptiondetails im öffentlichen Healthcheck.

Docker Compose ist nur für lokale Entwicklung. Ports binden an Loopback; PostgreSQL/Redis haben getrennte persistente Volumes. Produktionshosting, Secretversorgung, Backups/Restore und Domain sind M6, derzeit nicht eingerichtet.

`contacts`: Identität und Suppression. `consents`: Anmeldung/Nachweise/Tokens, persistente DOI-Aufträge, Ereignisse und Rate-Limits. Beat verarbeitet DOI-Pendingjobs alle 30 Sekunden; der Auftrag in PostgreSQL übersteht Brokerverlust. `prune_rate_limits` entfernt alte Rate-Buckets, derzeit als Managementcommand auszuführen. Vollständige Aufbewahrung/Löschung der Kontakte/Nachweise ist M6.

`campaigns`: strukturierte Entwürfe, Assets, unveränderliche freigegebene Revisionen und Rendering. Bilddateien in persistentem Compose-Medienvolume; produktive öffentliche HTTPS-Medienauslieferung muss IONOS bereitstellen. Keine Cache-/Messparameter pro Empfänger an Bild-URLs. SMTP-Konfiguration, Header/DKIM und Zustellung sind M4; Testmail ist ein expliziter Bedienvorgang über das konfigurierte Django-Mailbackend. Console-/Locmem-Adapter transportieren keine externen Mails. Produktionsproxy muss Uploadgrößen ebenfalls begrenzen (z. B. 10 MB); die App prüft die Bildgröße nach Einlesen.

CI-Gates sind vorbereitet, bisher nicht remote ausgeführt. Portable Prüfungen dieser Umsetzung nutzen ausschließlich einen externen temporären SQLite-Harness und ersetzen weder PostgreSQL noch Parallelitäts-/Infrastrukturabnahme. Die Anwendung selbst hat keinen SQLite-Fallback.
