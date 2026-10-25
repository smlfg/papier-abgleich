# Drehbuch: „Ich habe meinen Code nicht mehr verstanden. Also habe ich ihn gezeichnet.“

Länge: **10:00** (600 s). Format 16:9, 1920×1080. Sprache Deutsch, Voiceover laut `SKRIPT.md` (gleiche Szenennummern). Alle Fakten: `RECHERCHE.md`.

Asset-Pfade relativ zum Repo `papier-abgleich/`:

| Kürzel | Pfad |
|---|---|
| SEITE | `examples/inkpartner-grillme/site/inkpartner-fakten.html` (oder Pages-URL) |
| SKIZZE | `examples/inkpartner-grillme/zeichnungen/inkpartnertest-s3-grillme.png` |
| S1/S5/S6 | `examples/inkpartner-grillme/zeichnungen/inkpartnertest-s{1,5,6}-*.png` |
| HERO | `docs/img/hero.png` |
| SPLIT | `docs/img/zeichnung-ergebnis.png` |
| PANEL | `examples/inkpartner-grillme/shots/panel-code.png`, `panel-verlauf.png`, `mobile.png` |
| GY | Graveyard-Seite `graveyard/index.html` (lokal, nicht im Repo; nur Screenshot der Kopfzeile/Zahlen) |
| LOG | `git log --oneline` des inkpartner-Repos (Terminal-Aufnahme) |
| MIN | `examples/minimal/site/minimal.html`, `docs/img/minimal-belege.png` |

## Szenen

| Nr | Shot | Visual | On-Screen-Text | Dauer (s) |
|---|---|---|---|---|
| 1 | Kalter Einstieg, Nah | SKIZZE langsam von oben nach unten gescrollt (Ken-Burns) | „Ich habe meinen Code nicht mehr verstanden.“ | 25 |
| 2 | Titel | HERO, weicher Zoom | „Papier-Abgleich“ · „Zeichnung gegen Code“ | 15 |
| 3 | Kontext | S1-Seite (Agent schreibt aufs Papier), dann S5 | „inkpartner: ein Lernpartner auf dem reMarkable“ | 45 |
| 4 | Vorgeschichte | GY-Kopfzeile mit Zahlen | „17.–24.10.: 25 Versuche · 63 Fehler · 34 Sackgassen“ · „DoD: 0 / 14“ | 45 |
| 5 | Ein Tag Code | LOG scrollt schnell durch 75 Commits; Branch `claude/…` hervorheben | „24.10.: 75 Commits“ · „Codex / Claude Code“ | 50 |
| 6 | Bruch | Schwarzblende, nur Uhrzeit | „~20:00 · Frust-Moment“ | 15 |
| 7 | Cursor-Nacht | Split-Screen: Session-Titel S1–S8 als Karten erscheinen nacheinander; Zitat-Einblendungen | „6 Sessions (+ Werkzeug-Sessions)“ · Zitate: „3 + 3 = 7“, „ein Stift-Event ist 24 Byte“, „600 Sekunden“ | 80 |
| 8 | Wendepunkt | Hand-/Stift-Optik: SKIZZE baut sich Zeile für Zeile auf (Maske) | „Statt noch einer Zusammenfassung: zeichnen.“ | 50 |
| 9 | Abgleich | SPLIT; Pfeil animiert von Skizzen-Zeile zum Knoten | „Jeder Punkt: Status · Beleg · Code“ | 60 |
| 10 | Die Seite | Screen-Recording SEITE: Urteil-Box, Filter `?status=geaendert`, Klick auf Knoten „dort fängt validate an“, Tab Code, Tab Verlauf; kurz mobil | „11 stimmen · 5 geändert · 4 teilweise · 2 anders · 2 unklar“ | 80 |
| 11 | Werkzeug | Terminal: `python3 build.py examples/minimal` → Browser MIN, Belege-Panel | „flow.json → build.py → eine HTML-Datei“ · Marker BELEGT / GERAET / OFFLINE / HYPOTHESE | 45 |
| 12 | Versionen | Drei Screenshots nebeneinander v1 → v2 → v3 | „v1 Bild · v2 Flussdiagramm · v3 Stufen + Panel“ | 30 |
| 13 | Einsicht | SKIZZE neben GY-Zahlen, dann Text auf ruhigem Hintergrund | „Hauptaufgabe: noch nicht gelöst.“ · „Meta-Aufgabe: Mensch–Agent-Zusammenarbeit gestalten.“ | 40 |
| 14 | Abschluss | Hand legt Stift auf Tablet (Stock/Eigenaufnahme) oder SKIZZE, Repo-Link | „Ownership durch Papier“ · github.com/smlfg/papier-abgleich | 20 |
| | | | **Summe** | **600** |

## YouTube-Kapitel

```
0:00 Ich verstehe meinen Code nicht mehr
0:40 Was ist inkpartner?
1:25 Eine Woche Versuche
2:10 Ein Tag, 75 Commits
3:15 Die Cursor-Nacht
4:35 Zeichnen statt lesen
5:25 Skizze gegen Code
6:25 Die Seite
7:45 Selbst ausprobieren
8:30 v1 → v3
9:00 Was ich eigentlich gebaut habe
9:40 Ownership durch Papier
```

(Kapitelzeiten = kumulierte Szenendauern: 1–2 = 0:00, 3 = 0:40, 4 = 1:25, 5 = 2:10, 6–7 = 3:00/3:15, 8 = 4:35, 9 = 5:25, 10 = 6:25, 11 = 7:45, 12 = 8:30, 13 = 9:00, 14 = 9:40.)

## Fehlende Assets (vor Produktion klären)

- v1: `inkpartner-sessions/flow/index_v1_backup.html` per Chrome headless rendern (Box, nicht im Repo).
- v2: `inkpartner-sessions/flow/shot_flow.png` und `shot_panel.png` (Box, vermutlich v2-Stand; vor Schnitt prüfen).
- Graveyard-Screenshot: lokal erzeugen (`graveyard/shot.png` existiert auf der Box).
- Realaufnahme Tablet/Stift: optional; ohne sie Szene 1 und 14 nur mit SKIZZE.
