# Optimierungsmöglichkeiten aus dem Algebra Agent

Stand: 5. November 2026. Dieses Dokument ist eine **Landkarte**, keine Zusage.
Es sammelt, was aus dem Algebra-Agent-Umfeld auf `papier-abgleich` übertragbar
ist, was bereits umgesetzt wurde und was bewusst nicht kommt.

Legende:

- **UMGESETZT** — in PR [#11](https://github.com/smlfg/papier-abgleich/pull/11) (offen, alle Checks grün).
- **OFFEN** — nächster sinnvoller Schritt mit klarer Abnahme.
- **NICHT EMPFOHLEN** — bewusst nicht, mit Begründung.

## Übersicht

| # | Optimierung | Warum | Aufwand | Abnahme | Status |
|---|---|---|---|---|---|
| 1 | `.vpen`-Eingang statt PNG/`.rm` | Rohstrom enthält Kontaktkanten, X/Y und Druck; `.rm` ist nur ein Snapshot | M | Parser + Build + Tests | UMGESETZT |
| 2 | Offline-Test-Gate + CI | 46 Tests, beide Beispiele, Python 3.9/3.12 | S | CI grün | UMGESETZT |
| 3 | macOS-Prüfwerkzeuge | `google-chrome`/`realpath` waren Linux-only | S | `verify.py` + `shots.sh` laufen auf macOS | UMGESETZT |
| 4 | Geräteabnahme der Aufnahme | Offline-Tests beweisen nicht `event2`-Lesbarkeit oder Sichtbarkeit | M | eine bewusste echte Aufnahme, SVG zeigt dieselben Striche | OFFEN |
| 5 | Seitenkalibrierung | Digitizer liefert Screen-, nicht Page-Koordinaten | M | Probe-Punkte, Affine Map, Verifikationsprobe ≤ 2 % | OFFEN |
| 6 | Zwei-Lesungen-Transkription | eine Lesung kann falsch, zwei können zu streng sein | M | `NOTIZEN.md` mit Konfidenz; keine erfundenen Labels | OFFEN |
| 7 | Link-/Beleg-Gate | „alle Links 200“ ist heute manuell | S | Offline-Schema + optionaler HTTP-Check | OFFEN |
| 8 | Beispiel-Benchmark | Regressionen in Knoten/Pfeilen/Stufen/Bytes fallen sonst nicht auf | S | deterministisches JSON + CI-Vergleich | OFFEN |
| 9 | `.rm`-Parser als Eingabe | Snapshot-Grenze und Formatrisiko | L | — | NICHT EMPFOHLEN |
| 10 | FIFO `/tmp/vpen.fifo` als Input | unbestätigter Schreib-Mux, kein belegter Reader | — | — | NICHT EMPFOHLEN |

Aufwand: S ≈ ein halber Tag, M ≈ ein bis zwei Tage, L ≈ mehr.

## Die offenen Punkte im Detail

### 4. Geräteabnahme der Aufnahme

**Was:** Eine echte, bewusst gestartete `.vpen`-Aufnahme mit drei Strichen; danach
`tools/vpen.py` und `build.py` darauf laufen lassen und die SVG-Ausgabe mit der
Handschrift vergleichen.

**Warum:** Die Offline-Tests beweisen Parser, Renderer und Build. Sie beweisen
nicht, dass das Gerät die Frames lesbar liefert, dass die Aufnahme vollständig
ist oder dass die Striche auf dem Display sichtbar sind. Der Flywheel-Logger hat
`BTN_TOUCH` natürlich beobachtet, aber keine Koordinaten und keine Latenz
gemessen.

**Abnahme:** `vpen_capture.py --seconds 30` erzeugt eine parsebare Datei; die
Zahl der Striche und die Form stimmen mit der Handschrift überein; die
Originalseite bleibt unverändert; kein Dienst wird gestartet; genau ein Lauf,
nur mit ausdrücklichem Ja des Owners.

**Beleg:** `Flywheelliveinput/README.md` (Event-Knoten, root, `BTN_TOUCH`-Probe);
`algebra-agent/LEARNINGS.md` (evdev-Schreibweg am Gerät, Lesen als Kandidat).

### 5. Seitenkalibrierung

**Was:** Eine Kalibrierungsdatei und ein Werkzeug, das die Abbildung von
Digitizer-/Screen-Koordinaten auf Seitenpixel pro Achse misst — analog zu
`tools/live_probe.py` im Algebra Agent.

**Warum:** Der Digitizer liefert Screen-Koordinaten. Die Abbildung auf die Seite
hängt von Zoom, Scrollposition und Toolbar ab. Die frühere `0.867`-Zahl war nie
gemessen. Gesichert ist dagegen: eine `.rm`-Document-Unit entspricht einer
Seitenpixel (IoU 0,81 gegen xochitls Thumbnail, Maximum auf 15/15 Seiten).

**Abnahme:** Mehrere Probe-Punkte, Rücklesen aus der gespeicherten Seite, affine
Map pro Achse und eine Verifikationsprobe, die innerhalb von 2 % landet. Ohne
bestandene Probe wird nichts geschrieben.

**Beleg:** `algebra-agent/LEARNINGS.md`, Einträge zu Digitizer/Viewport und
`DOC_WIDTH 1620`.

### 6. Zwei-Lesungen-Transkription

**Was:** Die Skizzen-Beschriftung mit zwei unabhängigen Lesungen transkribieren;
nur übereinstimmende Lesungen gelten als sicher, sonst `[?]` und eine offene
Frage.

**Warum:** Eine einzelne Lesung kann falsch sein; zwei Lesungen können aber auch
zu streng sein. Der Algebra-Agent-Benchmark zeigt beides: Roh-VLM 86,4 %
(19/22), Zwei-Leser-Gate im Status quo nur 45,5 % (10/22) auf den alten fünf
Seiten, nach den Fixes 87,5 % (49/56) auf zehn Seiten. Die Lehre ist nicht
„immer zwei Leser“, sondern **messen, ob der Gate hilft**.

**Abnahme:** `NOTIZEN.md` mit Konfidenz pro Skizzen-Punkt; keine erfundenen
Labels; ein kleiner Benchmark über 5 Skizzen vergleicht eine Lesung gegen zwei.

**Beleg:** `mlops-gedanken/5-seiten-labor/BENCHMARK-CHANGES.md`;
`algebra-agent/README.md` (zwei unabhängige Lesungen, unsicher nie grün).

### 7. Link-/Beleg-Gate

**Was:** `tools/check_links.py` prüft die URLs in `flow.json` (HTTP 200) und
stellt sicher, dass nicht gepushte Commits `url: null` tragen. Die
Schema-Prüfung läuft offline, der HTTP-Teil optional mit `--online`.

**Warum:** Der Workflow verlangt „alle Links liefern HTTP 200“, aber heute prüft
das niemand automatisch. Ein toter Permalink ist ein Beleg, der nicht mehr
prüfbar ist.

**Abnahme:** Fixtures mit guten und kaputten URLs; CI prüft offline; der
Online-Lauf ist ein eigener, bewusst gestarteter Schritt.

### 8. Beispiel-Benchmark

**Was:** `tools/benchmark.py` baut die vorhandenen Beispiele und schreibt ein
deterministisches JSON mit Knoten, Pfeilen, Stufen, Bytes und Dauer. CI
vergleicht gegen eine eingecheckte Baseline.

**Warum:** Der Algebra Agent hat mit einem 10-Seiten-Benchmark eine
Verschlechterung von 86,4 % auf 45,5 % sichtbar gemacht und die Fixes auf 87,5 %
gebracht. `papier-abgleich` hat heute nur „baut oder baut nicht“; stille
Regressionen in Knoten oder Einzeldatei-Größe fallen nicht auf.

**Abnahme:** JSON ist stabil (keine Zeit als Pflichtfeld), CI schlägt bei
Abweichung an, beide Beispiele sind abgedeckt.

## Nicht empfohlen

- **`.rm` als primäre Eingabe:** Der Poll liest einen gespeicherten Zustand;
  Stiftkontakt, Pen-up und Zwischenstände zwischen Polls bleiben unsichtbar.
  `.vpen` ist die nähere Quelle; `.rm` bleibt Fallback.
- **FIFO `/tmp/vpen.fifo` als Input:** Im Algebra Agent ist sie ein
  Schreib-Mux; ein lesender Dienst, ein bestandener Test und ein Gerätestart
  sind nicht belegt. Diese Lücke wird nicht als Feature verkleidet.
- **OCR direkt in `build.py`:** Der Build bleibt offline und ohne
  Netzwerkzugriffe. Eine Transkription ist ein separater Agenten-Schritt, kein
  Build-Schritt.

## Reihenfolge

1. **#11 mergen** — `.vpen`-Eingang, Tests, CI und macOS-Gate sind fertig.
2. **Geräteabnahme (4)** — nur mit ausdrücklichem Ja, genau ein Lauf.
3. **Seitenkalibrierung (5)** — erst danach sind page-genaue Aussagen erlaubt.
4. **Zwei-Lesungen (6) + Benchmark (8)** — gemeinsam messen, nicht blind
   übernehmen.
5. **Link-Gate (7)** — kleine, unabhängige Härtung.

## Nicht behaupten

- Es gab in PR #11 keine echte Geräteaufnahme und keinen Live-Lauf.
- Die Digitizer→Seite-Abbildung ist ohne Kalibrierung nicht page-genau.
- Die OCR-/Gate-Zahlen aus dem Algebra Agent belegen nichts über
  `papier-abgleich`; sie begründen nur, warum gemessen werden soll.
- `.vpen` ist kein offizielles reMarkable-Format.
