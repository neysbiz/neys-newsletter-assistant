# Kontakte, Mailchimp-Quelldaten und neuer DOI

Stand: 09.10.2026. Datenstruktur und Services implementiert; Datei-Upload, Importvorschau und Freigabeoberfläche sind das nächste M2-Paket. Keine realen Adressen übernommen und keine Bestätigungskampagne gestartet.

## Importvertrag

Der bereitgestellte Export enthält laut Betreiber ausschließlich aktive Abonnenten. Die separate Datei mit zurückgenommenen Adressen ist aktuell nicht Bestandteil der Umsetzung. Wiederholungsimporte dürfen vorhandene lokale Abmeldungen/Sperren nicht überschreiben. Vor der Umstellung ist der aktive Export frisch zu erstellen; während des Übergangs erfolgte Abmeldungen müssen vor einer Kontaktaufnahme berücksichtigt werden.

| Spalte | Pflicht / Interpretation | Speicherung |
|---|---|---|
| Emailadresse | Pflicht; Aliase `E-Mail-Adresse`, `Email Address`; widersprüchliche Mehrfachspalten abweisen | Contact.email, normalisierter eindeutiger email_key |
| Status | Mailchimp-Quellstatus; `aktiv`, `active` oder `subscribed`; fehlt die Spalte, gilt der ausdrücklich vereinbarte aktive Export | MailchimpRecord.source_status = subscribed |
| Vorname, Name | Optional | Contact.first_name/last_name; Originalwerte zusätzlich im Quellsnapshot |
| Erlaubnis zum Marketing | Historisches separates Flag; X/true/1 = ja, leer/false/0 = nein, fehlende Spalte = unbekannt | MailchimpRecord.marketing_flag und Originalwert |
| OPTIN_TIME/IP, CONFIRM_TIME/IP | Unveränderte historische Quellangaben, kein neuer DOI | MailchimpRecord.source_data |
| SOURCE, LEID, EUID | Herkunft/externe Referenzen | Eigene Felder und Quellsnapshot |
| MEMBER_RATING, GMTOFF, DSTOFF, TIMEZONE, CC, REGION, LAST_CHANGED, NOTES, TAGS | Optional; originale Zeichenfolgen, keine erfundene Zeitzoneninterpretation oder Tags-Aufteilung | MailchimpRecord.source_data |
| Importlauf-ID, importiert_am | Vom System erzeugt bzw. von der Import-Orchestrierung übergeben | batch_id, imported_at |
| Newsletterstatus | Vom System verwaltet, keine importierbare Freigabe | Subscription.status |

`prepare_mailchimp_row` validiert ohne Schreiboperation. `stage_mailchimp_contact` übernimmt eine validierte Zeile atomar und bewahrt lokale Namen/Status bei bereits bestehenden Kontakten. Identische Zeilen pro Adresse/Importlauf sind idempotent; widersprüchliche Zeilen werden abgewiesen. Separate Importläufe erhalten separate Quellnachweise, aber keinen zweiten Kontakt.

Neue importierte Kontakte erhalten `imported` (neue Bestätigung erforderlich), keine ConsentEvidence und keinen Mailauftrag. Das Marketingflag schaltet weder Newsletter, Tracking noch Kundenkonten frei. Eine zukünftige Kundenkonto-/Marketingfunktion benötigt eigene Regeln und zweckbezogene Nachweise.

## Neue Bestätigung

Geplanter Wechsel: erneute, ausdrückliche Newsletter-Anmeldung mit dem freigegebenen neuen Text → `pending` plus DOI-Auftrag → signierter Link → Bestätigungsseite → CSRF-geschützter POST → `active`. Öffnen des Links allein bestätigt nichts. Importierte Kontakte können diesen bestehenden öffentlichen Ablauf nutzen. Eine automatisierte Einladung an alle bisherigen Abonnenten ist weder implementiert noch gestartet; Kanal, zulässiger Empfängerkreis und Formulierung werden vor der Umstellung festgelegt. Der Import ist kein Ersatz für die neue Anmeldung. Tracking bleibt ausgeschaltet.

## Nachweisstruktur

| Tabelle | Gespeicherter Nachweis |
|---|---|
| ConsentEvidence (requested) | E-Mail-Snapshot, Zweck, Aktion, Zeitpunkt, Herkunft, exakter Zustimmungstext + Version + SHA-256, angezeigter Datenschutzhinweis + Version, optional direkte Client-IP |
| ConfirmationToken | Zufällige Referenz, Bezug zur Anmeldung, Ablauf und Verbrauchszeitpunkt; kein vollständiger signierter Bearer-Link gespeichert |
| ConfirmationMessage | Interne eindeutige Nachrichtenreferenz, Empfänger, Absender, Betreff und Textsnapshot mit Linkplatzhalter; SHA-256 des tatsächlich verwendeten Textes, Versuchsbeginn, Adapterstatus und Annahmezeit |
| ConsentEvidence (confirmed) | Bezug zur ursprünglichen Anmeldung und Tokenreferenz, Zeitpunkt und bestätigter Text-/Datenschutzhinweis-Snapshot; optional direkte Client-IP |
| ConsentEvidence (withdrawn) | Widerrufszeitpunkt/-quelle und Bezug zur vorherigen Anmeldung |
| ConsentEvent | Idempotente fachliche Bestätigung/Widerruf mit Ursache |

Annahmezeit bedeutet Annahme durch den konfigurierten Adapter, keine nachgewiesene Zustellung. Auch das lokale Console-Backend kann annehmen. Die Nachrichtenreferenz wird bei neuen Versuchen als Message-ID gesetzt; für alte Datensätze ist die durch Migration erzeugte ID nur eine interne Referenz, kein rekonstruierter historischer Mailheader. Der Textsnapshot speichert einen Linkplatzhalter; der Hash allein ermöglicht keine unabhängige Wiederherstellung des vollständigen versandten Textes einschließlich des damaligen signierten Links.

IP-Speicherung ist standardmäßig aus (`NEWSLETTER_STORE_EVIDENCE_IP=false`). Bei Aktivierung werden nur gültige direkte REMOTE_ADDR-Werte erfasst; Forwarded-Header werden nicht ungeprüft vertraut. Vor Aktivierung müssen Zweck, Hinweis und Aufbewahrung festgelegt werden. Importierte IPs bleiben als historische Quelldaten erkennbar. Keine User-Agent-/Trackingdaten werden zusätzlich erhoben.

Vor Produktion sind Zustimmungstext, Betreiberangaben und vollständiger Datenschutzhinweis freizugeben (`NEWSLETTER_CONSENT_*`, `NEWSLETTER_PRIVACY_*`). Die Entwicklungsfassung ist keine produktive Freigabe. Settings werden für jeden neuen Antrag eingefroren; spätere Änderungen ersetzen keinen bestehenden Antrag. Alte Nachweise werden nicht nachträglich mit unbekannten E-Mail-, IP-, Datenschutz- oder Versandangaben aufgefüllt. Ausstehende alte Mailaufträge erhalten ihren tatsächlichen Mailtext erst beim nächsten Versandversuch.

Die Adminansichten sind schreibgeschützt; das ist kein manipulationssicheres Archiv gegen Datenbankadministratoren. Produktiver Zugriffsschutz, Backups, Aufbewahrung/Löschung, Nachweisexport und gegebenenfalls zusätzliche Archivierung bleiben M6. Ein Text-Hash garantiert weder wirksame Einwilligung noch Rechtssicherheit.

## Grundlage und Grenzen

Art. 7 Abs. 1 DSGVO verlangt, die Einwilligung nachweisen zu können. Die DSK-Orientierungshilfe Direktwerbung (Februar 2022), Abschnitt 3.3, behandelt DOI/Protokollierung; eine IP-Adresse allein reicht nicht. Daraus leiten wir die technische Trennung von Quellangaben, Einwilligungsinhalt und Bestätigung ab. Konkrete Rechtsgrundlage, Betreibertexte und Aufbewahrung sind damit nicht abschließend geprüft.

Primärquellen, am 09.10.2026 geprüft:
- https://eur-lex.europa.eu/legal-content/DE/TXT/HTML/?uri=CELEX:02016R0679-20160504
- https://www.datenschutzkonferenz-online.de/media/oh/OH-Werbung_Februar%202022_final.pdf

## Migration/Betrieb

Nach Pull: `python manage.py migrate` im backend-Ordner mit aktiver venv. Migrationen erweitern die Tabellen ohne Statusänderung bestehender Abonnements. Nachrichten-IDs werden pro Altzeile separat erzeugt, dann eindeutig erzwungen. Vor einer produktiven Migration Backup und Schreibpause einplanen. Ein Rückrollen entfernt neue Nachweisfelder/Importdaten; der alte Status-Constraint akzeptiert imported nicht, daher Daten vor einem Rollback gesondert behandeln. Kein ungeprüfter produktiver Rückwärtslauf.
