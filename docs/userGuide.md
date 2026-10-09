# Benutzerführung

Verwaltung unter `/manage/`: Anmeldung mit aktivem Staff-Account erforderlich. Normale Accounts haben keinen Verwaltungszugriff. Superuser lokal über `python backend/manage.py createsuperuser` anlegen. Abmelden über den Button (POST).

Projektbasis enthält zentrale Seitenlayouts und Statusanzeige. Kontaktliste, Kampagneneditor und Mailchimp-Upload mit Importvorschau sind vorhanden.

## Anmeldung und Abmeldung

Öffentliches Entwicklungsformular unter `/`. E-Mail und Zustimmung angeben; identische Antwort unabhängig vom vorhandenen Status. Worker/Beat bzw. `python backend/manage.py dispatch_confirmations` verarbeitet die dauerhaft gespeicherte Bestätigungsmail. Console-Backend zeigt den Link im Terminal. Öffnen des Links zeigt einen Button; erst dessen Klick bestätigt. Link gilt 24 Stunden; erneute Anforderung nach 10 Minuten möglich, mit Stundenlimits.

Verwaltung → Kontakte zeigt Status und Suche. Admin-Nachweise sind lesbar, Status wird nicht direkt im Admin verändert. Abmeldung über signierten Link ohne Login; danach sperrt die zentrale Versandprüfung jeden weiteren Kampagnenversuch. Keine Trackingauswertung aktiv.

Vor echtem Betrieb sind Einwilligungs-/Datenschutzhinweise, Impressum, Absender, Domain und Versandweg festzulegen. Das aktuelle Formular ist für Entwicklung gekennzeichnet.

## Newsletter vorbereiten

Verwaltung → Kampagnen → Neuer Entwurf. Betreff und Vorschautext angeben, Text/Bild/Link als Inhaltsart wählen und Inhalt ausfüllen. Reihenfolge über die Positionsfelder ändern; ungenutzte Zusatzzeile leer lassen. Jeder gespeicherte Entwurf bietet eine weitere Zusatzzeile, bis maximal 20 Blöcke. Löschen über das Feld am jeweiligen Block.

Bilder vorab unter Kampagnen → Bilder hochladen: JPEG/PNG, höchstens 8 MB und 20 Megapixel. Nur zur Veröffentlichung bestimmte Motive verwenden. Für jeden Bildblock ist eine Bildbeschreibung nötig. Links verwenden HTTPS. In Texten/Betreff/Vorschautext ist `{{email}}` der einzige unterstützte Platzhalter.

Revision freigeben erzeugt einen unveränderlichen Stand, startet aber keinen Kampagnenversand. Revision öffnen → Vorschau oder Testmail. Testempfänger erhält Text- und HTML-Version dieser Revision; der Abmeldelink ist ein wirkungsloser Testlink. Mit dem Entwicklungs-Console-Backend erscheint die Mail im Terminal. Aktuelle Mailclient- und SimplyNeys-CI-Prüfung noch offen.

## Importierte Kontakte und Nachweise

Kontakte zeigt E-Mail, Vorname, Nachname, lokalen Newsletterstatus und Mailchimp-Quellstatus/Marketingflag. Neue importierte Kontakte sind bis zur neuen DOI-Bestätigung nicht versandberechtigt. Import erzeugt keine Mails. Das zusätzliche Marketingflag ist keine Newsletter-, Tracking- oder Konto-Freigabe.

Im Django-Admin sind Mailchimp-Quelldaten, Einwilligungsereignisse, Tokenreferenzen und DOI-Versandaufträge schreibgeschützt einsehbar. Datenfelder und Grenzen: [contact-import-and-doi.md](contact-import-and-doi.md).

## Mailchimp-Datei importieren

1. Verwaltung → Kontakte → **Mailchimp-Datei importieren** (`/manage/contacts/import/`).
2. CSV/TSV in UTF-8 auswählen. Komma, Semikolon oder Tabulator entsprechend der Datei wählen. Bestätigen, dass der Export ausschließlich aktive Abonnenten enthält. E-Mail-Spalte: `Emailadresse`, `E-Mail-Adresse` oder `Email Address`.
3. **Vorschau erstellen**: noch keine Kontakte übernommen. Fehler, widersprüchliche Adressen, identische Duplikatzeilen, unbekannte Spalten und vorhandenen lokalen Status prüfen. Unbekannte Spalten werden ausdrücklich angezeigt und nicht gespeichert. Fehlt Status, gilt die bestätigte aktive Exportdatei als subscribed.
4. Bei Fehlern: Datei korrigieren und neu hochladen. Es gibt bewusst keinen stillen Teilimport. Identische Duplikatzeilen werden übersprungen.
5. Checkbox unter der Vorschau aktivieren und **Kontakte ohne Versandfreigabe übernehmen** wählen. Die Übernahme erfolgt vollständig oder gar nicht. Neue Kontakte benötigen einen neuen DOI; vorhandene Namen/Status/Sperren bleiben bestehen. Kein Mailversand.

Die Vorschau ist 30 Minuten gültig und nur für den hochladenden Benutzer zugänglich. Verwerfen löscht die vorläufigen Zeilendaten. Nach Übernahme bleiben nur die Quellsnapshots bei den Kontakten und die Importmetadaten/Ergebniszahlen erhalten. Erneutes Bestätigen desselben Laufs erzeugt keine weiteren Datensätze. Eine erneut hochgeladene Datei erzeugt einen neuen Quellenlauf, aber keine doppelten Kontakte.

Grenzen: 2 MiB, 2000 Datenzeilen, 100 Spalten, 4096 Zeichen pro Feld. XLSX, ZIP und andere Zeichencodierungen werden nicht unterstützt. Excel-Dateien als UTF-8-CSV speichern; keine zusätzliche `sep=`-Zeile vor der Kopfzeile.

Worker/Beat bereinigt abgelaufene Vorschauen alle 30 Minuten. Wenn nur runserver läuft, im backend-Ordner mit aktiver venv regelmäßig `python manage.py discard_import_previews` ausführen. Abgelaufene Zeilen werden nicht mehr angezeigt oder übernommen; ihre physische Bereinigung benötigt den laufenden Job oder diesen Befehl. Dateiname/Prüfsumme und Ergebnis-Metadaten bleiben erhalten; die endgültige Aufbewahrungsregel ist vor Produktivbetrieb festzulegen.
