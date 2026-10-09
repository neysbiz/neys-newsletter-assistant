# Neys Newsletter Assistant — Entwicklungsroadmap

Stand: 06.10.2026 (Europe/Berlin) · Version 1.2

## 1. Zweck und Verwendung

Diese Roadmap steuert die Umsetzung von `neys-newsletter-assistant`. Sie ist der Einstiegspunkt für Planung, Fortschritt und nächste Arbeitspakete. Nach jeder abgeschlossenen Umsetzungseinheit werden Status, tatsächliche Prüfungen, verbleibende Probleme und nächste Schritte aktualisiert. Ein Chat ersetzt keine versionierte Projektdokumentation.

Zielablage auf dem Mac:
`/Users/andreas/Documents/Development/Django/django-projects/neys-newsletter-assistant/docs/ROADMAP.md`

Aktueller Stand (09.10.2026): M0/M1 und der funktionale Teil von M3 sind auf main integriert; Bootstrap- und CSRF-CI erfolgreich. M2-Datenstruktur/Validierungs- und Stagingservice sowie erweiterte DOI-Nachweise umgesetzt. Datei-Upload/Importvorschau und produktiver Import offen. Details in docs/contact-import-and-doi.md. Kein Produktivdeploy, keine echten Mails oder Kundendaten übernommen.

## 2. Bestätigter Umfang

- Eigenes Newsletter-Werkzeug mit Bildern und Text wie bei einer gewöhnlichen E-Mail.
- Start mit rund 300 Empfängern und etwa vier Newslettern pro Monat.
- Bestehende, offiziell angemeldete Mailchimp-Abonnenten übernehmen.
- Double-Opt-in, nachvollziehbare Einwilligungen und Abmeldung.
- Editor mit Betreff, Vorschautext, Text, Bildern und Links; Vorschau und Testmail.
- Sofortiger und geplanter Versand; Warteschlange und Fehlerbehandlung.
- Öffnungs- und Klickauswertung sowie Versandfehler, Rückläufer, Abmeldungen und Anmeldeentwicklung.
- Geschützter Verwaltungsbereich, Datenexport und Löschprozesse.
- Datenhaltung auf IONOS; Django, PostgreSQL, Redis/Celery, Docker Compose und später eigenes GitHub-Repository.
- Projektübergreifende Neys-Entwicklungs- und Dokumentationsvorgaben; Schichten und Ereignisse als Architekturprinzip, kontrollierte Branchführung und Fast-Forward-Pulls.

Tracking ist gewünschter Funktionsumfang. Seine konkrete Einwilligungs- und Datenschutzgestaltung sowie der Versandweg sind noch offen. Datenhaltung auf IONOS legt den Versandanbieter nicht fest. Die bestehende Newsletter-Anmeldung wird nicht automatisch als Einwilligung in neue Trackingfunktionen behandelt.

## 3. Ausgangslage und offene Entscheidungen

| ID | Entscheidung / Nachweis | Zeitpunkt | Auswirkung bei fehlender Klärung |
|---|---|---|---|
| D01 | Originale Neys-Richtlinien, insbesondere `docs/development_workflow.md`, `docs/django_architecture_baseline.md` und vorhandene `AGENTS.md`, im zugänglichen Projektbestand lesen | Vor Anwendungscode / M0 | Originalbaseline am 06.10.2026 gelesen und übernommen; Herkunft in development_workflow.md |
| D02 | Repo `https://github.com/neysbiz/neys-newsletter-assistant.git`, Standardbranch `main`; Lese-/Schreibzugriff bestätigt, Ausgangsstand leer | Erledigt am 06.10.2026 | Lokale Mac-Anbindung noch ausstehend |
| D03 | Konkreter Mailtarif/Versanddienst, erlaubte Nutzung, Limits, Rückläufer-/Beschwerdekanal | Vor M4-Integration | Providerunabhängige Entwicklung möglich; echter Kampagnenversand wartet |
| D04 | Absenderdomain/-adresse, Reply-To, DNS-Zugang und öffentlich erreichbare HTTPS-Domain | Vor Testversand / M4 | Keine produktiven Versand- oder DOI-URLs festlegen |
| D05 | Tracking-Einwilligung, Widerruf, Hinweistexte und Aufbewahrungsregeln anhand aktueller Primärquellen prüfen und festlegen | Vor M5-Aktivierung | Tracking bleibt ausgeschaltet; Newsletter ohne Tracking bleibt möglich |
| D06 | Mailchimp-Exportfelder, Nachweise und Sperrstatus tatsächlich prüfen | Vor produktivem Import / M2 | Keine fehlenden Nachweise rekonstruieren oder erfinden |
| D07 | Aktueller IONOS-Standort, Verträge, Backupziel und Datenflüsse einschließlich Versandanbieter prüfen | Vor produktiver Datenübernahme / M6 | DSGVO-Konformität nicht allein aus dem Hostinganbieter ableiten |
| D08 | Templates/CSS, Python 3.13 (3.12–3.14 unterstützt), Django 5.2, pytest/Ruff; konfigurierbare lokale Ports 8005/55435/6385 | Abgleich erledigt; ADR 0001 | Mac-Portbelegung und produktives Deployment noch nicht geprüft |

Die Entscheidungen werden später in `docs/decisions/` mit Datum, Begründung und Auswirkungen festgehalten. Rechtliche Anforderungen und aktuelle Anbieterbedingungen werden im jeweiligen Arbeitspaket anhand verifizierter Quellen geprüft; diese Roadmap liefert keine rechtliche Freigabe.

## 4. Zielarchitektur für die Umsetzung

Ein modularer Django-Monolith genügt für den Startumfang. PostgreSQL ist die führende Datenquelle; Redis/Celery transportiert Arbeit, ersetzt aber keinen dauerhaften Versandstatus. Kein eigener Mailserver und keine zusätzliche Microservice-Infrastruktur für den MVP geplant.

| Schicht | Verantwortung | Grenze |
|---|---|---|
| Oberfläche / HTTP | Verwaltung, öffentliche Anmeldung, Bestätigung und Abmeldung; Authentifizierung, Eingabeprüfung und Darstellung | Keine Versand- oder Einwilligungslogik in Views/Templates |
| Application Services | Fachliche Schreiboperationen, Transaktionen, Statusübergänge, Berechtigungs- und Versandprüfungen | Gemeinsame Regeln für Admin, Import und Worker |
| Selectors / Read Models | Abfragen, Listen, Vorschau- und Auswertungsdaten | Keine versteckten Zustandsänderungen |
| Domänenmodelle / Policies | Kontakte, Einwilligungen, Kampagnen, Sperren und Versandregeln | Keine direkte Abhängigkeit von einem SMTP-Anbieter |
| Rendering | Validierte Inhaltsbausteine, HTML-/Textversion, Personalisierung, Abmeldelinks | Keine Zustellung oder Trackingentscheidung im Editor |
| Infrastrukturadapter | SMTP/API, Speicher, Rückläufer und externe Integrationen | Austauschbarer Versandanschluss; explizite Fähigkeiten statt stiller Fallbacks |
| Hintergrundverarbeitung / Events | Planung, Versandjobs, Rückmeldungen, Wiederholungen und Aggregate | Dünne Tasks rufen Services auf; kein zweiter Fachlogikpfad |

Geplante Django-Bereiche: `accounts`, `contacts`, `consents`, `campaigns`, `delivery`, `analytics`. Erst aufteilen, wenn das konkrete Arbeitspaket es erfordert. Gemeinsame UI-Bausteine und Regeln werden zentral umgesetzt. Eine SPA oder WebSockets sind durch den Newsletter-Use-Case bisher nicht festgelegt.

### Daten- und Ereignisverträge

- `Contact`, `Subscription`, `ConsentEvidence`: Kontakt und Newsletter-/Trackingzustimmung getrennt; Ursprung, Zeitpunkt und versionierter Zustimmungstext nachvollziehbar.
- `ConfirmationToken`: Zweckbindung, Ablauf, sichere Aufbewahrung und kontrollierte Wiederverwendung; keine personenbezogenen Angaben im Token.
- `Campaign`, `CampaignRevision`, `Asset`: Inhalt, Vorschautext und referenzierte Bilder; freigegebene Versandrevision unveränderlich.
- `Delivery`, `DeliveryAttempt`, `Suppression`: Empfängerbezogener Versandstatus, einzelne Versuche und zentrale Versandsperren.
- `Event` / Outbox: fachliche Ereignisse mit ID, Version, Zeit, Ursache und fachlicher Referenz; keine unnötigen personenbezogenen Payloads.
- Beispiele: `subscription.confirmed`, `subscription.withdrawn`, `campaign.scheduled`, `delivery.accepted`, `delivery.failed`, `delivery.bounced`, `tracking.observed`.

Ereignisverarbeitung muss Wiederholung und verspätete Rückmeldungen vertragen. Dauerhafte Aufträge werden zusammen mit fachlichen Änderungen gespeichert; ein Dispatcher übergibt sie nach Commit an Celery und holt liegen gebliebene Aufträge nach. Genau-einmal-Zustellung einer E-Mail wird nicht zugesichert: Bei SMTP-Annahme und anschließendem Timeout kann der Ausgang unklar sein. Solche Fälle werden sichtbar behandelt, statt blind erneut zu senden.

## 5. Roadmap und Abnahmekriterien

Reihenfolge: M0 → M1 → M2 → M3 → M4 → M6 → M7. M5 folgt auf M4 und D05; der Pilot kann ohne aktiviertes Tracking starten. Termine werden erst nach Sichtung des realen Projektstands vergeben.

| Meilenstein | Ergebnis | Abhängigkeit | Status |
|---|---|---|---|
| M0 | Baseline und Projektbasis | Richtlinien, lokaler Bestand, später Repo | Implementiert; CI erfolgreich |
| M1 | Anmeldung, DOI und Abmeldung | M0 | Implementiert; PostgreSQL/Redis-CI erfolgreich; Nachweise erweitert |
| M2 | Mailchimp-Übernahme und Kontakte | M1, Export/Nachweise | Struktur/Staging umgesetzt; Datei-Upload/Importvorschau offen |
| M3 | Editor und E-Mail-Rendering | M1 | Funktional implementiert; technische CI erfolgreich; SimplyNeys-Design/Mailclients offen |
| M4 | Kontrollierter Versand und Rückmeldungen | M2 + M3; Anbieter für Integration | Offen |
| M5 | Auswertung und einwilligungsabhängiges Tracking | M4; D05 für Tracking | Offen |
| M6 | Produktionsbetrieb und Datenschutzprozesse | M4, Betriebsentscheidungen | Offen |
| M7 | Pilot und erster produktiver Newsletter | M6; M5 soweit aktiviert | Offen |

### M0 — Baseline und Projektbasis

- Lokalen Bestand und Originalrichtlinien lesen; Abweichungen/Unklarheiten dokumentieren.
- Bereitgestelltes Repo lokal anbinden; bestehenden lokalen Inhalt erhalten und Remote prüfen.
- Django-Projektbasis, PostgreSQL, Redis, Celery Worker und Scheduler mit Docker Compose; getrennte Entwicklung/Tests/Produktion.
- Versionen und Abhängigkeiten festlegen; `.env.example` ohne Geheimnisse, README, Start-/Testbefehle und CI.
- Geschützten Verwaltungszugang, Berechtigungskonzept, gemeinsame Layout-/Listenbausteine und Statusanzeigen vorbereiten.
- Frontend und Testkommando aus Baseline übernehmen; keine projektspezifische Game-World-Testvorgabe pauschal übertragen.

Abnahme: reproduzierbarer Start, erreichbare Datenbank/Worker, Django-Systemcheck, dokumentiertes Testkommando, erste aussagekräftige Smoke-/Berechtigungsprüfungen und keine Secrets in versionierten Dateien.

### M1 — Einwilligung, Anmeldung und Abmeldung

- Öffentliches Anmeldeformular; Status `pending`, `active`, `unsubscribed`; Versandsperren separat.
- DOI-Nachricht, Bestätigung, Ablauf und begrenztes erneutes Anfordern; Rate-Limits gegen Missbrauch.
- Versionierte Einwilligungsnachweise, getrennte Trackingpräferenz und Widerrufspfad.
- Bestätigungsablauf gegen automatische Linkscanner prüfen; eine bloße Vorschau darf keine unbeabsichtigte Zustimmung auslösen.
- Abmeldeseite und interoperable Abmeldeheader; Ein-Klick-Protokoll mit aktuellen Standards abgleichen.
- Zentraler Versandberechtigungsservice, den jeder Versandpfad verwendet.

Abnahme: unbestätigte oder abgemeldete Kontakte erhalten keine Kampagne; abgelaufene/ungültige Tokens ändern nichts; doppelte Vorgänge sind kontrolliert; Abmeldung sperrt auch bereits geplante Empfänger vor ihrem Versand.

### M2 — Mailchimp-Import und Kontaktverwaltung

- Originalexport sichten; Feldmapping und Importvorschau mit Fehlerbericht.
- E-Mail-Normalisierung und Duplikatregeln explizit festlegen; keine providerabhängigen Adressumschreibungen.
- Herkunft, vorhandene Zustimmungsdaten und Nachweise erhalten; Unbekanntes als unbekannt ausweisen.
- Abgemeldete, bereinigte und gesperrte Kontakte nicht reaktivieren; erneuter Import überschreibt keine spätere Abmeldung.
- Kontakte suchen/filtern/bearbeiten, Export; einfache Versandselektion mit nachvollziehbaren Ausschlüssen.

Abnahme: Wiederholungsimport ohne Duplikate; Sperren bleiben bestehen; Bericht erklärt importierte, ausgeschlossene und ungeklärte Datensätze. Produktivdaten werden erst nach den dazugehörigen Betriebsentscheidungen übernommen.

### M3 — Editor, Vorschau und Rendering

- Strukturierte Bausteine für Text, Bild und Link/CTA; Betreff, Vorschautext und Absenderdaten.
- Validiertes HTML mit begrenztem Formatierungsumfang, sicheren URLs und definierter Personalisierung; Textversion als gleichwertiger Versandbestandteil.
- Bildverwaltung mit Dateityp-/Größenprüfung, Alternativtext und HTTPS-Auslieferung; keine ausführbaren Uploads.
- Mobile Vorschau, Testmail, Entwurf und unveränderliche freigegebene Revision.
- SimplyNeys-Stil über zentrale Vorlage; Texte und Buttons als HTML, nicht ausschließlich im Bild. Kanalbezogene Bildvorgaben aus der aktuellen CI separat abgleichen.

Abnahme: Vorschau/Testmail entsprechen derselben Revision; Darstellung in relevanten Mailclients praktisch geprüft; Bilderblockierung lässt wesentliche Inhalte und Abmeldung lesbar; Textversion und ungültige Platzhalter geprüft.

### M4 — Planung, Queue, Versand und Rückläufer

- Sofort-/Terminversand mit UTC-Speicherung und verständlicher Anzeige in Europe/Berlin.
- Empfängerselektion bei Freigabe nachvollziehbar speichern; Einwilligung/Sperren unmittelbar vor jedem Versand erneut prüfen.
- Pro Kampagne/Empfänger eindeutiger Versandauftrag; atomare Reservierung gegen konkurrierende Worker.
- Versandadapter mit begrenzter Rate/Parallelität, Timeouts und klassifizierten Fehlern.
- Begrenzte Wiederholungen nur für geeignete Fehler; unklarer Versandstatus braucht ausdrückliche Behandlung.
- Pause/Abbruch stoppt noch nicht versandte Aufträge; bereits angenommene Mails lassen sich nicht zurückholen.
- Absenderauthentifizierung und reale Tarifgrenzen prüfen; Rückläufer-/Beschwerdeeingang nach Anbieterfähigkeit integrieren.
- Harte Rückläufer und Beschwerden sperren weitere Sendungen; temporäre Probleme nach dokumentierter Policy behandeln.

Abnahme: Worker-Neustart, doppelte Jobs, Broker-Ausfall, SMTP-Timeout, Abmeldung während Versand und verspätete Providerereignisse geprüft. 300 synthetische Empfänger ohne echten Massenversand durchlaufen Queue/Abrechnung. Annahme durch SMTP wird als Annahme angezeigt, nicht als belegte Zustellung.

### M5 — Auswertung und Tracking

- Übersicht über Kontakte, DOI, Kampagnen, angenommene/fehlgeschlagene Nachrichten, nachgewiesene Zustellereignisse, Rückläufer und Abmeldungen.
- Öffnungs-/Klickmessung nur entsprechend festgelegter und dokumentierter Einwilligung aktivieren; ohne Trackingzustimmung keine personalisierten Messlinks/-bilder.
- Widerruf auch am Messendpunkt prüfen; gewöhnliche Bilder dürfen nicht als versteckter Ersatz für deaktiviertes Tracking dienen.
- Signierte/opaque Messreferenzen, sichere Linkziele und keine frei nutzbaren Redirects.
- Sicherheitscrawler, Bildproxies und automatische Abrufe berücksichtigen; beobachtete Abrufe nicht als sicher menschliche Öffnungen darstellen.
- Kennzahlen, Nenner, Zeitraum und Messgrenzen dokumentieren; Trackingfähige Teilmenge getrennt ausweisen.
- Datenminimierung, Aufbewahrung und Bereinigung der Rohereignisse.

Abnahme: Tracking aus/ohne Zustimmung erzeugt keine personenbezogene Messung; Widerruf wirkt auf weitere Abrufe; doppelte Ereignisse verzerren eindeutige Kennzahlen nicht; Bericht beschreibt, was tatsächlich gemessen wurde.

### M6 — Betriebsfähigkeit, Sicherheit und Datenschutzprozesse

- IONOS-Deployment, HTTPS, persistente Volumes und Medien; Worker/Scheduler eindeutig betreiben.
- Betreiberrollen, sichere Sitzungskonfiguration, Adminschutz und gegebenenfalls zusätzlicher Zugangsschutz nach Baseline.
- Secretverwaltung, Protokollierung ohne Tokens/unnötige personenbezogene Daten und überwachbare Fehler-/Queuezustände.
- Backups von Datenbank und Medien mit dokumentiertem Restore; Wiederherstellung praktisch testen.
- Auskunft/Export/Löschung einschließlich Behandlung notwendiger Nachweis-/Sperrdaten und Backups anhand festgelegter Regeln.
- Aufbewahrungsjobs, Betriebshandbuch, Deployment-/Rollbackverfahren; IONOS und Versanddienst in Datenflussübersicht erfassen.

Abnahme: Restore erfolgreich; unberechtigter Zugriff geprüft; Gesundheits-/Fehlerüberwachung funktioniert; Datenflüsse, Verträge, Löschregeln und Produktionskonfiguration sind konkret dokumentiert.

### M7 — Pilot und Freigabe für den ersten Newsletter

- End-to-End mit Testkontakten: Anmeldung → DOI → Vorschau/Test → Planung → Versand → Rückmeldung → Abmeldung.
- Praktische Prüfung ausgewählter Mailclients, Mobilansicht, Links, Absenderauthentifizierung und Zeitplanung.
- Kleinen Pilot mit ausdrücklich vorgesehenen Testempfängern durchführen; danach reale Import-/Sperrlisten und Kampagne kontrollieren.
- Versandfreigabe separat von Codefreigabe behandeln; Entwicklung startet keinen echten Kundenversand.
- Nach erstem produktivem Versand Fehler, Rückläufer, beobachtete Kennzahlen und Betriebsaufwand auswerten.

Abnahme: alle für den gewählten Funktionsumfang notwendigen Gates bestanden; offene Restpunkte transparent; freigegebene Revision und Empfängerliste nachvollziehbar. Kein pauschales Versprechen perfekter Zustellung oder DSGVO-Konformität.

## 6. Entwicklungs- und Dokumentationsführung

Die Original-Neys-Baseline hat Vorrang; ihr vollständiger Abgleich ist M0/D01. Bis dahin gelten die belegten Vorgaben und diese projektspezifischen Arbeitsregeln:

1. Vor Änderungen Repo/Verzeichnis, Branch, HEAD, Working Tree und Remote prüfen. Lokalen, Remote- und Deploymentstand getrennt benennen.
2. Ein fachlicher Kontext in einem aktiven Branch. Kontext abschließen, integrieren und bereinigen, bevor der nächste beginnt; keine vermischten parallelen Features.
3. Pull ausschließlich mit `git pull --ff-only`. Divergenz analysieren, nicht mit ungeprüftem Merge/Rebase/Reset übergehen. Kein erzwungenes Pushen.
4. Diagnose mit Belegen vor Reparatur. Keine spekulativen Fallbacks, stillen Ersatzpfade oder unnötigen Frameworks hinzufügen.
5. Fachlogik zentral in Services/Policies; dünne Views und Tasks. Änderungen am gemeinsamen Versand-/Einwilligungsablauf nicht im Editor oder einzelnen Provideradapter verstecken.
6. Prüfen, was für die Änderung relevant ist: fachliche Tests, Django-Checks, Migrationskonsistenz und bei Frontendänderungen dessen vorhandene Checks. Sicherheits-/Versand-/Einwilligungsregeln brauchen aussagekräftige Tests; reine Dokumentänderung braucht keine künstlichen Tests.
7. Status nur mit tatsächlichem Ergebnis aktualisieren. Nicht ausgeführte Prüfungen, Annahmen und Einschränkungen ausdrücklich nennen.
8. Dokumentation im selben Arbeitspaket aktualisieren; keine Secrets, echten Empfängerlisten oder ungefilterten Exporte committen.

### Geplante Dokumente

| Datei | Inhalt / Aktualisierung |
|---|---|
| `README.md` | Projektziel, reproduzierbarer Start, relevante Dokumentlinks |
| `docs/ROADMAP.md` | Diese Roadmap; Status, Abhängigkeiten, nächstes Paket |
| `docs/development_workflow.md` | Abgeglichene Neys-Arbeitsregeln und echte Prüfkommandos |
| `docs/django_architecture_baseline.md` | Übernommene gültige Baseline mit Herkunft/Stand |
| `docs/architecture/newsletter.md` | Schichten, Zustandsmodelle, Transaktionen, Adapter und Ereignisverträge |
| `docs/decisions/` | Kurze nummerierte Architektur-/Betriebsentscheidungen |
| `docs/privacy-data-flow.md` | Datenarten, Zwecke, Einwilligungen, Aufbewahrung und externe Datenflüsse |
| `docs/operations.md` | Deployment, Konfiguration, Monitoring, Backup/Restore und Fehlerbehandlung |
| `docs/progress.md` | Pro Arbeitspaket Änderung, Branch/Commit, tatsächliche Validierung, Restpunkte |

Weitere Dokumente erst bei konkretem Bedarf erstellen; parallele widersprüchliche Roadmaps vermeiden. Nach Repo-Anbindung wird `docs/ROADMAP.md` im Projekt die führende Fassung.

### Definition of Done

Ein Arbeitspaket ist abgeschlossen, wenn seine Abnahmekriterien erfüllt, passende Prüfungen erfolgreich, Migrationen konsistent, relevante Doku aktuell und Änderung/Restpunkte nachvollziehbar sind. Implementiert, getestet, integriert und produktiv eingesetzt sind getrennte Zustände.

## 7. Fortschritt und nächstes Arbeitspaket

| Datum | Ergebnis | Validierung | Noch offen |
|---|---|---|---|
| 06.10.2026 | Roadmap v1.0 erstellt; Umfang und offene Entscheidungen aus bisherigem Projektkontext nachvollzogen | Dokumentprüfung; kein Anwendungscode, daher keine Anwendungstests | Übernahme auf Mac; Originalbaseline; Repo; M0 |

| 06.10.2026 | Roadmap v1.1 für Repository-Synchronisierung vorbereitet; Remote erreichbar und leer | GitHub-Metadaten, Branchprüfung und `git ls-remote`; Dokumentprüfung | Commit-Synchronisierung verifizieren; Mac-Abgleich und Originalbaseline weiterhin offen |

M0 umgesetzt: Settings, Django-Verwaltung, PostgreSQL/Redis/Celery-Compose, Lockfiles, Ruff und CI. Django-Check/Ruff lokal erfolgreich. Docker/PostgreSQL sind lokal nicht startbar; vollständige Abnahme über GitHub CI offen.

Nächstes Arbeitspaket: M2-Datei-Upload mit Importvorschau und expliziter Übernahme auf Basis des aktiven Exports. Vor der Umstellung neue DOI-Anmeldung und produktive Hinweise festlegen. Vor M4 Versanddienst/Domain festlegen; M3-Design-/Mailclient-Abgleich abschließen. Frühere Validierungsabschnitte unten dokumentieren den damaligen Stand.

## 8. Spätere Erweiterungen

Automationen/Serien, A/B-Tests, umfangreiche Segmentierung, KI-Inhaltserzeugung, Multi-Mandanten-Betrieb und Integrationen in weitere Neys-Produkte sind kein zusätzlicher Auftrag dieser Roadmap. Falls benötigt, nach dem stabilen Pilotbetrieb mit eigenen Anforderungen und Abnahmekriterien einplanen.

## Umsetzungsstand 06.10.2026

M0/M1 lokal implementiert. Django-Systemcheck/Ruff und portable Funktionsprüfungen erfolgreich. Eine temporäre, nicht versionierte SQLite-Prüfumgebung prüft die Fachabläufe; sie ist keine unterstützte Anwendungs- oder Testkonfiguration und ersetzt keine PostgreSQL-Abnahme. PostgreSQL-Parallelitäts- und Redis/Worker-Gates sind separat markiert und in CI obligatorisch. Push wurde automatisch blockiert; deshalb noch keine CI-Ergebnisse und kein Remote-Codeupdate. M2 wartet auf Originalexport/Nachweise. M3 funktional implementiert; gestalterische und praktische Abnahme offen.

M3: Formset-Editor mit Text/Bild/CTA, validierte Platzhalter/Links, Bildprüfung/Neu-Kodierung, eingefrorene Revisionen, gemeinsame Text-/HTML-Renderfunktion und Testmail implementiert. 47 portable Funktionsprüfungen unter Python 3.12 und 3.13 erfolgreich; 1 echter Redis-6.2/Celery-Rundlauf erfolgreich (Redis 7 bleibt CI-Gate). Django-Systemcheck, Migrationsdelta-Prüfung auf temporärem SQLite-Harness, Ruff und Dependencycheck erfolgreich. Der vollständige CI-Lauf einschließlich PostgreSQL/Parallelität bleibt offen; praktischer Mailclient-/CI-Design-Abgleich ebenfalls. Keine echten Kundenmails oder Daten übernommen.
