---
name: papier-abgleich
description: >-
  use this when: Nach einer Phase agentischer Arbeit soll der Mensch sein
  Verständnis eines Projekts/Codes auf Papier (z. B. reMarkable) skizzieren, und
  die Skizze wird Punkt für Punkt gegen den echten Code gemappt (stimmt noch /
  geändert / anders / teilweise / unklar), mit Belegen und einer klickbaren
  Website, die der Struktur der Skizze folgt. Auch bei 'Ownership-Check',
  'Grillme-Abgleich', 'stimmt mein Verständnis noch?', Agentic Sprawl.
---
# Papier-Abgleich (Human-Agent Ownership Check)

## Zweck
Agentische Arbeit erzeugt schnell mehr Code, als der Mensch versteht. Dieser Ablauf stellt Verständnis und Ownership wieder her: **Der Mensch zeichnet sein mentales Modell, der Agent hält den echten Code dagegen.** Ergebnis ist eine messbare Antwort auf „Stimmt mein Bild noch?“ und eine Karte, mit der man das Projekt wieder greifen kann.

Prinzip: *Der Mensch liefert die Struktur, der Agent liefert die Belege.* Der Agent korrigiert die Skizze nicht stillschweigend, er markiert Abweichungen.

## Wann auslösen
- Nach ca. 4–8 agentischen Sessions am selben Problem, oder wenn mehrere parallele Lösungen für dasselbe Problem entstehen (Agentic Sprawl).
- Wenn der Mensch Frust, Orientierungslosigkeit oder „ich verstehe meinen eigenen Code nicht mehr“ äußert.
- Vor einem Merge, einer Übergabe oder einem Freeze.
- Die Bremse ist bewusst: **„Genug agentisch – jetzt aufs Papier.“**

## Rollen
- **Mensch:** zeichnet die Pipeline/Architektur aus dem Kopf, ohne Code anzusehen. Bestätigt, welche Seite gemeint ist. Entscheidet am Ende, was er übernimmt.
- **Agent (Inhalt):** liest Skizze und Quellen, mappt, belegt, baut die Ansicht. Erfindet nichts.
- **Worker (optional):** übernimmt schwere Lese-/Build-Arbeit; der Agent prüft dessen Ergebnis selbst.

## Ablauf

### 0. Prompt an den Menschen
Kurz und offen: „Zeichne, wie das System deiner Meinung nach funktioniert – von Eingabe bis Ausgabe, mit Namen, Zahlen und Grenzen, die du im Kopf hast. Nicht nachschauen.“ 10–20 Minuten reichen.

### 1. Quelle sichern und bestätigen
- Neueste handschriftliche Seite holen (z. B. Tablet-Sync, nur lesend) und rendern.
- **Seite mit dem Menschen bestätigen**, bevor gelesen wird. Nicht raten, welche Notiz gemeint ist; Notizbuchname, Seite und Änderungszeit nennen.
- Persönliche Notizen (Gefühle, Selbstzweifel) gehören nicht in den Abgleich. Sie werden angesprochen, aber nicht veröffentlicht.

### 2. Abschrift
- Bei hohen/kleinen Seiten in Streifen schneiden und vergrößern, dann von oben nach unten lesen.
- Wörtlich mit Original-Schreibweise. Unsicheres mit `[?]` markieren. Skizzen als Fluss beschreiben (A → B, Verzweigungen, Rauten yes/no).
- In nummerierte **Skizzen-Punkte** zerlegen (eine Behauptung pro Punkt). Ablage: `NOTIZEN.md`.

### 3. Kontext sammeln
- Code: alle relevanten Branches, nicht nur `main` (neueste Arbeit liegt oft auf Feature-Branches). Ausschnitte nur per `git show <sha>:<pfad>`, nie aus dem Gedächtnis.
- Verlauf: Session-Transkripte, Commits (Message, Zeit, Branch), lokale vs. gepushte Commits trennen.
- Bestehende Fakten-Dokumente als Ausgangspunkt, aber auf Aktualität prüfen.

### 4. Abgleich pro Punkt
Jeder Skizzen-Punkt bekommt genau einen Status:

| Status | Bedeutung |
|---|---|
| **stimmt noch** | Skizze und aktueller Code stimmen überein |
| **geändert** | stimmte damals, Code hat sich seitdem verändert (Commit/Session nennen) |
| **anders** | Skizze widerspricht dem Code (z. B. Datei/Typ existiert nicht so) |
| **teilweise** | Kern stimmt, Details weichen ab |
| **unklar** | nicht belegbar, Mensch fragen |

Zu jedem Punkt: Fakt in 1–3 Sätzen, **Beleg** (Datei:Zeile + Link, Commit-Link oder Session-Zeit), Zahlen falls vorhanden, betroffene Regeln/Guards, offene Fragen.

**Belegmodell (Pflicht):** jeder Fakt mit wörtlichem Zitat der Belegstelle plus Marker:
- `BELEGT` – im Code/Commit nachgewiesen
- `GERAET` – auf dem echten Gerät beobachtet
- `OFFLINE` – nur in Tests/Simulation
- `HYPOTHESE` – plausibel, nicht nachgewiesen
So lässt sich jeder Punkt prüfen, ohne die Quelle zu öffnen.

### 5. Ansicht bauen (Skizze = Struktur)
- **Die Struktur der Seite folgt der Skizze des Menschen**, nicht einer Agenten-Architektur. Gleiche Reihenfolge, gleiche Verzweigungen, gleiche Namen (auch wenn sie im Code anders heißen; dann steht das als Abweichung im Knoten).
- Knoten = Skizzen-Punkte, gruppiert in Stufen (z. B. Lesen → Verstehen → Urteilen → Prüfen → Zeichnen → Schreiben → Fehlerfall). Jeder Knoten zeigt einen Status-Punkt.
- Klick öffnet Seitenpanel mit Tabs **Fakt / Code / Verlauf**.
- Kopf: Kennzahlen (Sessions, Commits, offene Punkte, Skizzen-Punkte), zwei Urteilskarten „Was die Skizze noch trifft“ / „Wo der Code inzwischen anders ist“, Abschnitt „Was ist offen“.
- Schalter „Original-Notiz“ zeigt die Handschrift scharf.
- Bedienung: Suche, Statusfilter, Tastatur (Pfeile, Esc, `/`), Deep-Links (`#knoten/code`), Mobil-Ansicht.
- Datengetrieben: `flow.json` als einzige Quelle, Build-Skript erzeugt die Seite. Zusätzlich eine **selbsttragende Einzeldatei** (CSS/JS/Bild inline, keine CDNs) zum Teilen.

### 6. Prüfen (vor Übergabe)
- Alle Links liefern HTTP 200; nicht gepushte Commits ohne Link, als „nur lokal“ markiert.
- Eingebettete Daten = `flow.json`; Code-Ausschnitte stammen aus `git show`.
- Browser-Render (headless) ohne JS-Fehler, ohne „undefined“; Screenshots von Übersicht, Panel, Filter, Mobil.
- Kein Schreiben ins Repo, kein Push, Quelle (Tablet) nur gelesen.

### 7. Übergabe an den Menschen
- Einzeldatei + 1–2 Screenshots, 3–5 Sätze Ergebnis: wie viele Punkte stimmen, was sich geändert hat, was offen ist.
- Iterieren, bis der Mensch sagt, es trifft seine Vorstellung. Rückmeldungen wie „dünn“ oder „UX suboptimal“ heißen: mehr belegter Inhalt pro Knoten und klarere Struktur, nicht mehr Features.
- Danach den Menschen fragen: Welche Abweichung überrascht dich? Was übernimmst du in dein Bild, was im Code?

## Qualitätsregeln
- Nie Fakten, SHAs, Zahlen oder Code erfinden. Lieber „unklar“.
- Veraltete Dokumente aktiv als veraltet markieren, statt sie zu übernehmen.
- Die Skizze des Menschen ist die Hauptsache. Die Agenten-Sicht ist nur Beleg.
- Token-Budget: schwere Leserunden an einen Worker geben, Ergebnisse selbst stichprobenartig prüfen.

## Artefakte (Standard-Layout)
```
abgleich/
  NOTIZEN.md        Abschrift + Skizzen-Punkte
  ABGLEICH.md       Statustabelle mit Belegen
  flow.json         Daten (Knoten, Kanten, Status, Belege, Snippets)
  build.py          erzeugt site/
  site/index.html   + style.css, app.js, notiz.png
  site/<name>.html  selbsttragende Einzeldatei
  shots/            Prüf-Screenshots
```
