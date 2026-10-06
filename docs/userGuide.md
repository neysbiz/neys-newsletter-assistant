# Benutzerführung

Verwaltung unter `/manage/`: Anmeldung mit aktivem Staff-Account erforderlich. Normale Accounts haben keinen Verwaltungszugriff. Superuser lokal über `python backend/manage.py createsuperuser` anlegen. Abmelden über den Button (POST).

Projektbasis enthält zentrale Seitenlayouts und Statusanzeige. Kontakt-/Kampagnenabläufe folgen in den jeweiligen Roadmap-Paketen.

## Anmeldung und Abmeldung

Öffentliches Entwicklungsformular unter `/`. E-Mail und Zustimmung angeben; identische Antwort unabhängig vom vorhandenen Status. Worker/Beat bzw. `python backend/manage.py dispatch_confirmations` verarbeitet die dauerhaft gespeicherte Bestätigungsmail. Console-Backend zeigt den Link im Terminal. Öffnen des Links zeigt einen Button; erst dessen Klick bestätigt. Link gilt 24 Stunden; erneute Anforderung nach 10 Minuten möglich, mit Stundenlimits.

Verwaltung → Kontakte zeigt Status und Suche. Admin-Nachweise sind lesbar, Status wird nicht direkt im Admin verändert. Abmeldung über signierten Link ohne Login; danach sperrt die zentrale Versandprüfung jeden weiteren Kampagnenversuch. Keine Trackingauswertung aktiv.

Vor echtem Betrieb sind Einwilligungs-/Datenschutzhinweise, Impressum, Absender, Domain und Versandweg festzulegen. Das aktuelle Formular ist für Entwicklung gekennzeichnet.

## Newsletter vorbereiten

Verwaltung → Kampagnen → Neuer Entwurf. Betreff und Vorschautext angeben, Text/Bild/Link als Inhaltsart wählen und Inhalt ausfüllen. Reihenfolge über die Positionsfelder ändern; ungenutzte Zusatzzeile leer lassen. Jeder gespeicherte Entwurf bietet eine weitere Zusatzzeile, bis maximal 20 Blöcke. Löschen über das Feld am jeweiligen Block.

Bilder vorab unter Kampagnen → Bilder hochladen: JPEG/PNG, höchstens 8 MB und 20 Megapixel. Nur zur Veröffentlichung bestimmte Motive verwenden. Für jeden Bildblock ist eine Bildbeschreibung nötig. Links verwenden HTTPS. In Texten/Betreff/Vorschautext ist `{{email}}` der einzige unterstützte Platzhalter.

Revision freigeben erzeugt einen unveränderlichen Stand, startet aber keinen Kampagnenversand. Revision öffnen → Vorschau oder Testmail. Testempfänger erhält Text- und HTML-Version dieser Revision; der Abmeldelink ist ein wirkungsloser Testlink. Mit dem Entwicklungs-Console-Backend erscheint die Mail im Terminal. Aktuelle Mailclient- und SimplyNeys-CI-Prüfung noch offen.
