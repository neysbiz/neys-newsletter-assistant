# Benutzerführung

Verwaltung unter `/manage/`: Anmeldung mit aktivem Staff-Account erforderlich. Normale Accounts haben keinen Verwaltungszugriff. Superuser lokal über `python backend/manage.py createsuperuser` anlegen. Abmelden über den Button (POST).

Projektbasis enthält zentrale Seitenlayouts und Statusanzeige. Kontakt-/Kampagnenabläufe folgen in den jeweiligen Roadmap-Paketen.

## Anmeldung und Abmeldung

Öffentliches Entwicklungsformular unter `/`. E-Mail und Zustimmung angeben; identische Antwort unabhängig vom vorhandenen Status. Worker/Beat bzw. `python backend/manage.py dispatch_confirmations` verarbeitet die dauerhaft gespeicherte Bestätigungsmail. Console-Backend zeigt den Link im Terminal. Öffnen des Links zeigt einen Button; erst dessen Klick bestätigt. Link gilt 24 Stunden; erneute Anforderung nach 10 Minuten möglich, mit Stundenlimits.

Verwaltung → Kontakte zeigt Status und Suche. Admin-Nachweise sind lesbar, Status wird nicht direkt im Admin verändert. Abmeldung über signierten Link ohne Login; danach sperrt die zentrale Versandprüfung jeden weiteren Kampagnenversuch. Keine Trackingauswertung aktiv.

Vor echtem Betrieb sind Einwilligungs-/Datenschutzhinweise, Impressum, Absender, Domain und Versandweg festzulegen. Das aktuelle Formular ist für Entwicklung gekennzeichnet.
