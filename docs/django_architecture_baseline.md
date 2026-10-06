# Django Architecture Baseline

Status: verbindliche Entwicklungsgrundlage

Dieses Dokument definiert die Architekturregeln fuer Neys-Django-Projekte. Es gilt fuer bestehende Projekte beim Refactoring und fuer neue Django-Projekte ab der Neuanlage. Abweichungen muessen bewusst begruendet und dokumentiert werden.

## 1. Grundprinzipien

- Modularer Monolith als Default. Keine Microservices ohne konkreten betrieblichen Grund.
- Fachliche Django-Apps besitzen klare Verantwortlichkeiten und explizite Abhaengigkeitsrichtungen.
- Views, Consumers und Transport-Handler orchestrieren; sie enthalten keine umfangreiche Businesslogik.
- Schreibende Businesslogik liegt in Services.
- Komplexe lesende Queries liegen in Selectors.
- Serialisierung von Runtime-/Client-State liegt in einer expliziten State-/Serializer-Schicht.
- Modelle beschreiben Persistenz, Constraints und kleine modellnahe Invarianten; keine versteckten Workflows.
- Infrastruktur kennt keine konkrete Fachimplementierung.
- Keine zweite Wahrheit fuer dieselbe Konfiguration.
- Refactorings aendern zuerst Struktur, nicht Verhalten.

## 2. Abhaengigkeitsrichtung

Fuer eine typische Anwendung:

```text
Presentation / API / WebSocket
            |
            v
Application / Handler / Views
            |
            v
Domain Services ----> Selectors
            |              |
            v              v
Domain / Engine / Models / Persistence
```

Querschnittsdienste wie Auth, Tenant, Observability und externe Integrationen werden explizit angebunden. Zirkulaere Imports zwischen Fach-Apps sind nicht zulaessig.

Fuer Neys Party gilt zusaetzlich:

```text
Clients
  |
  v
Lobby / Connection
  |
  v
Game Engine <---- Game registration
  ^
  |
Game Apps ----> Content Engine
```

Die Game Engine darf keine konkreten `apps.games.*` importieren. Lobby darf keine konkreten Spiele importieren.

## 3. Standardstruktur einer Django-App

Eine normale fachliche App soll sich an folgendem Aufbau orientieren:

```text
apps/<domain>/
|-- __init__.py
|-- apps.py
|-- admin.py
|-- models.py
|-- selectors.py
|-- services.py
|-- state.py            # falls Client-/Runtime-State existiert
|-- handlers.py         # falls Transport-/Event-Handler existieren
|-- urls.py             # falls HTTP-Routen existieren
|-- views.py            # duenne HTTP-Orchestrierung
|-- migrations/
|-- management/
|   `-- commands/
`-- tests/
    |-- __init__.py
    |-- factories.py
    |-- test_models.py
    |-- test_selectors.py
    |-- test_services.py
    `-- test_integration.py
```

Nicht jede Datei ist Pflicht. Leere Schichten werden nicht prophylaktisch angelegt. Komplexe Apps duerfen fachliche Unterpakete erhalten.

## 4. Game-App-Vertrag fuer Neys Party

Ein Standardspiel verwendet bevorzugt:

```text
apps/games/<game>/
|-- apps.py
|-- admin.py
|-- models.py
|-- config.py
|-- selectors.py
|-- services.py
|-- state.py
|-- handler.py
|-- migrations/
|-- tests/
`-- docs/
```

Verantwortlichkeiten:

- `config.py`: deklarative Spiel-/Engine-Konfiguration.
- `selectors.py`: lesende Queries ohne Seiteneffekte.
- `services.py`: Spielregeln, Transaktionen und Zustandsaenderungen.
- `state.py`: oeffentlicher/privater Client-State.
- `handler.py`: Event-Routing, Rechtepruefung, Service-Aufruf, Broadcast.
- `models.py`: spielbezogene Persistenz.

Komplexe Spiele duerfen z. B. `playback/`, `content/` oder `runtime/` als Unterpakete besitzen. Das ist einer erzwungenen Einheitsstruktur vorzuziehen.

## 5. Transportregel

HTTP-Views, REST-Endpunkte und WebSocket-Handler sollen:

1. Input lesen und validieren,
2. Berechtigung pruefen,
3. Service/Selector aufrufen,
4. Ergebnis serialisieren,
5. Response/Event senden.

Sie sollen keine umfangreichen ORM-Workflows, Scoring-Regeln oder Match-Lifecycle-Logik implementieren.

## 6. Service-/Selector-Regel

Services:
- duerfen schreiben,
- definieren Transaktionsgrenzen,
- implementieren fachliche Aktionen,
- liefern fachliche Resultate, keine transportabhaengigen Responses.

Selectors:
- sind read-only,
- kapseln nicht-triviale QuerySets und Lookup-Konventionen,
- vermeiden duplizierte Session-/Match-/Tenant-Aufloesung.

Kleine triviale Queries muessen nicht kuenstlich ausgelagert werden.

## 7. Registry und Konfiguration

Registrierungen sind deklarativ und besitzen genau eine kanonische Quelle. Aus ihr sollen Handler, UI, Varianten, Lifecycle-/Availability-Metadaten und technische Anforderungen abgeleitet werden.

Runtime-Mutation globaler Django-Settings in `AppConfig.ready()` ist kein Zielmuster. Compatibility-Code darf temporaer bestehen, benoetigt aber Test und dokumentierten Entfernungspfad.

## 8. Core-Regel

Eine App namens `core` ist keine Ablage fuer fachlich unklare Funktionen.

Jedes Core-Objekt wird regelmaessig klassifiziert:
- wirklich projektweit -> core/platform,
- Account/Tenant -> accounts/organizations,
- Session/Connection -> lobby/connection,
- Match/Reaction/Scoring -> game_engine,
- Telemetrie -> analytics/observability,
- konkrete Spielregel -> Game-App.

Neue Fachmodelle duerfen nicht allein aus Bequemlichkeit in `core` landen.

## 9. Tests

Tests folgen der Verantwortlichkeit der Produktionsmodule. Fuer zentrale Architekturregeln werden Architecture Tests gepflegt.

Mindestens zu schuetzen:
- keine konkreten Game-Imports aus Lobby,
- keine konkreten Game-Imports aus Game Engine,
- registrierte Alpha/Ready-Komponenten sind vollstaendig,
- Scaffolds werden nicht versehentlich produktiv,
- Konfiguration besitzt keine widerspruechlichen Wahrheiten,
- persistierte Compatibility-Keys bleiben lesbar.

Refactoring-Gate:

```bash
python manage.py check
python manage.py makemigrations --check
pytest
```

## 10. Refactoring-Regel

Strukturrefactoring erfolgt inkrementell:

1. Ist-Zustand und Verhalten durch Tests sichern.
2. Eine Architekturgrenze pro Commit/Sprint bearbeiten.
3. Keine Featureaenderung im selben Refactoring-Commit.
4. Bestehende URLs, Events, DB-Semantik und Client-Vertraege erhalten.
5. Nach jedem Schritt volles Test-Gate.
6. Legacy erst entfernen, wenn keine produktive Abhaengigkeit mehr existiert.

## 11. Definition of Done fuer neue Django-Projekte

Bereits bei Projektanlage:
- Apps nach Fachdomänen statt nach technischen Sammelbegriffen schneiden.
- Service-/Selector-Konvention dokumentieren.
- zentrale Settings nach Umgebung aufteilen, falls Projektgroesse dies erfordert.
- Ruff/Formatter konfigurieren; den Test-Runner projektbezogen festlegen (bei Neys Party: Django `manage.py test`).
- `check`, `makemigrations --check` und Tests als CI-Gate.
- `.env.example`, README, Deployment- und Migrationsregeln anlegen.
- DB-Constraints fuer fachliche Eindeutigkeit bevorzugen.
- Logging/Fehlerbehandlung nicht erst nach Go-live planen.
- ASGI/Channels nur bei echtem Realtime-Bedarf einsetzen.
- Architekturentscheidungen als ADR oder Architecture Decisions fortschreiben.

## 12. Entscheidungsregel

Bevor neue Funktionalitaet implementiert wird, wird sie einer Schicht und einem Owner-Modul zugeordnet. Wenn zwei Module dieselbe Verantwortung beanspruchen, wird die Grenze vor der Implementierung geklaert.

