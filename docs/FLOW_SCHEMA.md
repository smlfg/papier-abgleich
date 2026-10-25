# `flow.json` und `project.json`: Datenformat

`build.py` liest zwei Dateien aus einem Projektordner:

| Datei | Pflicht | Inhalt |
|---|---|---|
| `flow.json` | ja | Die Skizze als Graph: Stufen, Knoten, Status, Belege, Code-Ausschnitte, Verlauf |
| `project.json` | nein | Texte der Seite (Titel, Einleitung, Labels), Bildname, wörtliche Skizzen-Punkte |

`flow.json` ist die **einzige Inhaltsquelle**. Die Seite bettet die Datei unverändert ein (`<script type="application/json" id="flow">`); nur fehlende Kennzahlen unter `stats` ergänzt `build.py` aus den Daten.

Ein vollständiges Mini-Beispiel steht in [`examples/minimal/`](../examples/minimal/), ein echtes mit 24 Knoten in [`examples/inkpartner-grillme/`](../examples/inkpartner-grillme/).

---

## `flow.json`

### Oberste Ebene

| Feld | Typ | Pflicht | Bedeutung |
|---|---|---|---|
| `stages` | `Stage[]` | ja | Stufen in Lesereihenfolge der Skizze. Jede Stufe wird ein Band im Diagramm. |
| `nodes` | `Node[]` | ja | Ein Knoten pro Skizzen-Punkt (oder Teil davon). |
| `commit` | string | nein | Voller SHA des geprüften Code-Stands. |
| `branch` | string | nein | Branch des geprüften Code-Stands. |
| `sessions` | `{ [ref]: Session }` | nein | Agenten-Sessions, auf die `verlauf[].ref` verweist (z. B. `"S1"`). |
| `commits` | `Commit[]` | nein | Commits für die Tabelle und den Verlauf. |
| `offen` | `Offen[]` | nein | Offene Fragen; Knoten verweisen über `node.offen` darauf. |
| `regeln` | `{ [code]: string }` | nein | Regeln/Guards, die im Code gelten (z. B. `"R-RATE": "…"`). |
| `regeln_quelle` | `{ [präfix]: string }` | nein | Woher die Regeln stammen, je Präfix. |
| `docs` | `{ [name]: url }` | nein | Projekt-Dokumente. |
| `stats` | `Stats` | nein | Kennzahlen für den Kopf; fehlende Werte rechnet `build.py` aus. |

### `Stage`

| Feld | Typ | Pflicht | Bedeutung |
|---|---|---|---|
| `id` | string | ja | Kennung, auf die `node.stage` verweist |
| `name` | string | ja | Anzeigename (z. B. „Lesen“) |

Stufen ohne Knoten werden ausgeblendet (`build.py` warnt).

### `Node`

| Feld | Typ | Pflicht | Bedeutung |
|---|---|---|---|
| `id` | string | ja | Eindeutig; erscheint im Deep-Link `#id`, `#id/code`, `#id/verlauf` |
| `label` | string | ja | Text **wie in der Skizze** (Original-Schreibweise) |
| `stage` | string | ja | `Stage.id` |
| `status` | enum | ja | `stimmt-noch` · `geaendert` · `anders` · `teilweise` · `unklar` |
| `row` | int ≥ 0 | ja | Zeile innerhalb der Stufe (relativ; der kleinste Wert je Stufe ist die erste Zeile) |
| `col` | 0–2 | ja | Spalte (links, Mitte, rechts) |
| `punkt` | string | nein | Nummer des Skizzen-Punkts (`"11"`, `"8 · 9"`, `"—"`) |
| `was` | string | nein | Was der Schritt tut, in Klartext (1 Satz; erscheint auch im Knoten) |
| `warum` | string | nein | Begründung des Status |
| `fakt` | string | nein | Fakt in 1–3 Sätzen (Langfassung) |
| `zahlen` | string[] | nein | Kennzahlen als kurze Chips (`"Timeout 600 s → 45 s"`) |
| `regeln` | string[] | nein | Schlüssel aus `regeln` |
| `offen` | string[] | nein | `Offen.id`s |
| `next` | string[] | nein | Ziel-Knoten der Pfeile (Reihenfolge zählt bei Rauten) |
| `shape` | `"raute"` \| `"notiz"` | nein | `raute` = Entscheidung (Raute, erster Pfeil „yes“, weitere „no“); `notiz` = Randnotiz |
| `edge_labels` | `{ [nodeId]: string }` | nein | Eigene Pfeil-Beschriftungen, überschreibt yes/no |
| `snippets` | `Snippet[]` | nein | Code-Ausschnitte für den Tab **Code** |
| `verlauf` | `Verlauf[]` | nein | Einträge für den Tab **Verlauf** |
| `commits` | string[] | nein | Kurz-SHAs, die diesen Knoten betreffen |
| `docs` | `{name, url}[]` | nein | Dokumente zu diesem Knoten |
| `belege` | `Beleg[]` | nein | **Belegmodell**, siehe unten |

Für Rückwärtskompatibilität gelten die ids `raute` und `user` auch ohne `shape` als Raute bzw. Randnotiz.

### `Snippet`

| Feld | Typ | Pflicht | Bedeutung |
|---|---|---|---|
| `file` | string | ja | Pfad im Repo |
| `start`, `end` | int | ja | Zeilen (1-basiert, inklusive) |
| `code` | string | ja | Wörtlicher Inhalt, **aus `git show <sha>:<pfad>`**, nie aus dem Gedächtnis |
| `url` | string \| null | nein | Permalink auf den SHA mit `#Lstart-Lend`; `null`, wenn der Commit nicht gepusht ist |

### `Verlauf`

| Feld | Typ | Pflicht | Bedeutung |
|---|---|---|---|
| `ref` | string | ja | Session-Schlüssel (`"S3"`) oder Kurz-SHA |
| `text` | string | ja | Was sich dort geändert oder gezeigt hat |
| `url` | string \| null | nein | Link (Commit, Doku) |
| `commit` | string | nein | Kurz-SHA, falls der Eintrag zu einem Commit gehört |

### `Session`, `Commit`, `Offen`

```jsonc
"sessions": { "S1": { "id": "77114ae4", "zeit": "24.10. 22:10–00:12", "titel": "Stift-Fehler sichtbar machen" } },
"commits":  [ { "short": "29c7a55", "url": "https://github.com/…/commit/29c7a55…", "msg": "pen: keep cat's stderr …", "wo": "watch/write-gap" },
              { "short": "9ba24a5", "url": null, "msg": "…", "wo": "nur lokal" } ],
"offen":    [ { "id": "drift", "titel": "…", "text": "…", "quelle": "S5",
                "snippet": { "file": "…", "start": 1, "end": 3, "code": "…", "url": null } } ]
```

`url: null` heißt **nur lokal** und wird ohne Link angezeigt. Nie einen Link auf einen nicht gepushten Commit bauen.

### `Stats` (optional)

| Feld | Standard, wenn es fehlt |
|---|---|
| `sessions` | Anzahl `sessions` |
| `subagent` | – (Zusatzzeile entfällt) |
| `commits_auf_github` | Commits mit `url` |
| `commits_lokal` | Commits ohne `url` |
| `offene_punkte` | Anzahl `offen` |
| `skizzen_punkte` (alt: `grillme_punkte`) | Anzahl verschiedener `node.punkt` |
| `status_count` | Zählung über `nodes[].status` |

---

## Belegmodell (`belege`)

Jeder Fakt soll ohne Öffnen der Quelle prüfbar sein: **wörtliches Zitat der Belegstelle plus Marker**, wie es den Grad des Nachweises angibt.

```json
"belege": [
  { "quote": "return [Task.from_line(l) for l in lines]", "marker": "BELEGT",    "quelle": "todo/parse.py:12", "url": null },
  { "quote": "Mit 10 000 Zeilen getestet: 0,4 s",         "marker": "OFFLINE",   "quelle": "tests/test_perf.py" },
  { "quote": "Auf dem Laptop sortiert ausgegeben",        "marker": "GERAET",    "quelle": "Session 2, 14:10" },
  { "quote": "Wahrscheinlich in einem älteren Branch",    "marker": "HYPOTHESE", "quelle": "—" }
]
```

| Feld | Typ | Pflicht | Bedeutung |
|---|---|---|---|
| `quote` | string | ja | Wörtliches Zitat (Code-Zeile, Log-Zeile, Transkript-Satz) |
| `marker` | enum | ja | siehe Tabelle |
| `quelle` | string | nein | Datei:Zeile, Commit, Session + Uhrzeit |
| `url` | string \| null | nein | Permalink, falls öffentlich |

| Marker | Bedeutung | Anzeige |
|---|---|---|
| `BELEGT` | im Code oder Commit nachgewiesen | grün |
| `GERAET` | auf dem echten Gerät beobachtet | orange |
| `OFFLINE` | nur in Tests oder Simulation | grau-blau |
| `HYPOTHESE` | plausibel, nicht nachgewiesen | violett |

Das Feld ist optional: bestehende Daten (wie das inkpartner-Beispiel) bauen weiter, der Abschnitt **Belege** erscheint im Tab **Fakt** nur, wenn `belege` gefüllt ist. `build.py` bricht ab, wenn ein Marker nicht in der Liste steht, und warnt bei fehlendem Zitat.

---

## `project.json`

Alle Felder optional; Standardwerte stehen in `DEFAULT_META` in `build.py`.

| Feld | Bedeutung |
|---|---|
| `title`, `description` | `<title>` und Meta-Beschreibung |
| `brand`, `brand_sub` | Schriftzug oben links |
| `eyebrow`, `headline` | Kopfzeile und Überschrift |
| `lede_html`, `subtitle_html` | Einleitung und Unterzeile; **HTML erlaubt** (nur eigene, vertrauenswürdige Texte) |
| `note_ref` | Bezeichnung der Notiz (z. B. `/Inkpartnertest S. 3`) |
| `image` | Dateiname des Notizbilds im Projektordner (Standard `notiz.png`) |
| `footer` | Fußzeile |
| `point_label`, `points_label` | „Skizzen-Punkt“ / „Skizzen-Punkte“, z. B. „Grillme-Punkt“ |
| `code_ref` | Name des Code-Stands im Urteil (z. B. `watch/write-gap`) |
| `callout_offen_id` | `Offen.id`, die als Hinweiskasten unter dem Urteil erscheint |
| `example_node` | Knoten für den Beispiel-Deep-Link im Hilfetext |
| `theme_key` | `localStorage`-Schlüssel für den Dunkelmodus |
| `points` | Wörtliche Skizzen-Punkte als Tabelle: `[[nr, notiz, status, beleg], …]` |

Alle Texte außer `*_html` werden HTML-maskiert.
