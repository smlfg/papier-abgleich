# `.vpen`: Skizzen als Stift-Ereignisstrom

Diese Seite begründet, warum `papier-abgleich` neben PNG/SVG/JPG auch eine
`.vpen`-Aufnahme liest, was darin steht und was die Tests beweisen — und was
ausdrücklich **nicht**.

## Warum nicht `.rm` oder ein Screenshot?

Ein `.rm`-Poll liest einen **gespeicherten Zustand**: `stat` + `cat` liefern
Bytes, aber keine Stiftzeit. Zwischen zwei Polls können Stiftkontakt,
Schreibbeginn, Pen-up und überschriebene Zwischenstände unsichtbar bleiben.
Das ist im Workspace dokumentiert in
`Flywheelliveinput/README.md` („Vorhandene Input-Signalwege“, Stand 29.10.2026):
Der implementierte `.rm`-Leser beobachtet, *wann* ein Poll einen neuen Stand
findet; die Zeitstempel sind Beobachtungszeiten, keine Stiftzeiten. Ein
lesender `BTN_TOUCH`-Kantenlogger existiert daneben in
`Flywheelliveinput/activity_logger.py`; er protokolliert aber nur
Kontaktanfang/-ende, keine Koordinaten.

`cat` ist dabei nur der Transport. Es sagt nicht, wo ein Strich anfängt, wo er
aufhört und wie viel Druck an jedem Punkt lag. Ein Screenshot ist noch später:
Er zeigt das Ergebnis, nicht die Ereignisse.

Der Ereignisstrom ist die nähere Quelle. Deshalb ist die Reihenfolge:

1. **`.vpen`** — rohe Stift-Ereignisse, offline und deterministisch gerendert.
2. **`.svg`/`.png`/`.jpg`** — vorhandenes Bild, wenn keine Aufnahme möglich ist.
3. **`.rm`** — nur als Snapshot-Fallback, nie als Behauptung über Stiftzeiten.

## Was ist eine `.vpen`-Datei?

**Kein offizielles reMarkable-Format.** `.vpen` ist hier eine
Aufnahme-Konvention für denselben Rohstrom, den das Stift-Device
`/dev/input/event2` liefert. Der Name kommt vom virtuellen Stift (`vpen2`) aus
dem Algebra-Agent-Umfeld; die FIFO `/tmp/vpen.fifo` ist dort ein
**Schreib-Mux**, kein belegter Input-Reader. Diese Datei behauptet nicht, dass
man aus der FIFO lesen kann.

Die Datei ist eine Folge von 24-Byte-Frames im Format `<qqHHi`. Format und
Konstanten stammen aus dem Algebra-Agent-Modul `inject.py`; die lesende
Device-Erkennung aus `Flywheelliveinput/activity_logger.py`.

| Feld | Typ | Bedeutung |
|---|---|---|
| `sec`, `usec` | `int64` | Zeitstempel des Events |
| `type` | `uint16` | `EV_SYN=0`, `EV_KEY=1`, `EV_ABS=3` |
| `code` | `uint16` | z. B. `BTN_TOUCH=330`, `ABS_X=0`, `ABS_Y=1`, `ABS_PRESSURE=24` |
| `value` | `int32` | Kontakt 0/1, Koordinate oder Druck |

Ein Strich sieht typischerweise so aus:

```
BTN_TOOL_PEN 1
ABS_X, ABS_Y, ABS_PRESSURE, BTN_TOUCH 1, SYN_REPORT   (erster Punkt)
ABS_X, ABS_Y, ABS_PRESSURE, SYN_REPORT                (weitere Punkte)
...
ABS_PRESSURE 0, BTN_TOUCH 0, SYN_REPORT
BTN_TOOL_PEN 0, SYN_REPORT
```

Das ist die Reihenfolge aus `inject.py`; echte Aufnahmen können `BTN_TOUCH`
auch vor den ABS-Werten setzen. `tools/vpen.py` akzeptiert beide. Ein Punkt
zählt bei `SYN_REPORT` oder beim Pen-up, sobald X und Y im laufenden Paket
waren; ein bereits abgeschlossenes Hover-Paket vor dem Kontakt wird verworfen.
Ein angebrochener Frame am Dateiende ist ein Fehler, kein stilles Verwerfen.

## Aufnehmen

`tools/vpen_capture.py` liest **nur lesend** über SSH:

```bash
python3 tools/vpen_capture.py --out mein-projekt/skizze.vpen --seconds 90
```

Das Skript

- findet das Device über den exakten Namen `Elan marker input`,
- öffnet `/dev/input/eventN` read-only und bestätigt das Öffnen,
- schreibt lokal eine `.vpen`-Datei und bricht nach `--seconds` ab,
- schreibt nichts auf das Tablet, startet keinen Dienst und löscht nichts.

Die Aufnahme ist ein **bewusst gestarteter** Schritt. Der Build selbst bleibt
offline und braucht weder Tablet noch Netz.

## Fertige `.rm`-Seite → Bild

Wenn du schon gezeichnet hast und die Seite als `.rm` gespeichert ist, brauchst
du keine neue Aufnahme. Der Algebra-Agent-Renderer liest die Striche und
schreibt ein PNG:

```bash
cd ~/Projects/01_WORK/Remarkable/algebra-agent
PYTHONPATH=src .venv/bin/python -c 'from algebra_agent.rm_page import read_page; from algebra_agent.drawback.render import render_page; page = read_page("zeichnung.rm"); render_page(page, None, "zeichnung.png", scale=1.0)'
```

Dann `"image": "zeichnung.png"` in `project.json` setzen und bauen.

Grenze: Eine `.rm` ist ein Snapshot. Sie enthält Striche und Druck, aber nicht
die Pen-up-/Zeitfolge. Für ein statisches Bild reicht das; für Timing oder
Live-Auswertung braucht es `.vpen`.

## Rendern und bauen

```bash
python3 tools/vpen.py mein-projekt/skizze.vpen --out mein-projekt/skizze.svg
# oder direkt im Build:
# project.json:  "image": "skizze.vpen"
python3 build.py mein-projekt --name mein-projekt.html
```

`build.py` rendert die Aufnahme beim Bauen nach `site/<stamm>.svg` und bettet
sie in die Einzeldatei ein. Es gibt keine neue Abhängigkeit; alles bleibt
Standardbibliothek.

### Koordinaten

Standardmäßig wird linear vom Digitizer `11180 × 15340` auf die Seite
`1620 × 2160` abgebildet und auf die Seitenfläche geklemmt. Das ist für die
Anzeige der Skizze ausreichend, aber **keine kalibrierte Seitenabbildung**:
Der Digitizer liefert Bildschirmkoordinaten; die Abbildung auf die Seite hängt
bei einer echten Sitzung von Zoom, Scrollposition und Toolbar ab. Wer eine
bereits in Seitenpixeln vorliegende Aufnahme hat, setzt
`--digitizer 1620x2160`. Eine page-genaue Abbildung braucht eine eigene
Gerätekalibrierung und wird hier nicht behauptet.

## Was der Test gezeigt hat

Die erste Parser-Fassung ging davon aus, dass `BTN_TOUCH` vor den ABS-Werten
kommt. Gegen den echten `inject.build_stream` verlor sie den ersten Punkt und
verdoppelte den letzten mit Druck 0. Deshalb puffert der Parser ABS-Werte ab
`BTN_TOOL_PEN`, verwirft ein bereits abgeschlossenes Hover-Paket vor dem
Kontakt und übernimmt einen Punkt nur, wenn X und Y im Paket waren. Die
Regressionstests `test_inject_reihenfolge_*` und
`test_abgeschlossenes_hover_paket_wird_verworfen` halten das fest.

Die Reihenfolge bleibt bewusst: erst das minimale Beispiel offline bauen und
prüfen, dann eine echte Aufnahme als separater, bewusster Geräteschritt.

## Was die Tests beweisen

```bash
python3 -m unittest discover -s tests -v
```

Die Testsuite prüft unter anderem:

- 24-Byte-Frame, Feldlayout und Little-Endian-Parsing (auch hartcodiert),
- Striche mit `BTN_TOUCH`, mit `BTN_TOOL_PEN` und in der echten `inject.py`-Reihenfolge,
- Pen-up, Hover-Paket vor dem Kontakt, Ereignisse außerhalb des Kontakts,
  doppelte `SYN_REPORT`-Pakete,
- angebrochene Frames und leere Aufnahmen,
- Druck → Strichbreite, Koordinatenabbildung und Klemmen,
- `.vpen` → SVG im Build, Einzeldatei ohne lokale Verweise,
- beide Beispiele (`minimal`, `inkpartner-grillme`) bauen weiter,
- die Chrome-Suche von `tools/verify.py` ohne Browserstart.

**Nicht bewiesen** sind: eine echte Aufnahme auf dem Tablet, die Sichtbarkeit
auf dem Display, die Latenz zwischen Stift und Datei oder eine page-genaue
Koordinatenabbildung. Diese Punkte bleiben Geräteabnahmen.

## Beleglage in einem Satz

`BELEGT` sind Frame-Format und Event-Konstanten aus dem Algebra-Agent-Modul
`inject.py`; die `.rm`-Snapshot-Grenze steht in `Flywheelliveinput/README.md`,
die lesende Device-Erkennung in `Flywheelliveinput/activity_logger.py`.
`OFFLINE` ist der Parser-, Renderer- und Build-Pfad durch die Tests;
`HYPOTHESE` bleibt die page-genaue Abbildung ohne Gerätekalibrierung. Was
daraus **nicht** folgt, steht oben unter „Nicht bewiesen“.
