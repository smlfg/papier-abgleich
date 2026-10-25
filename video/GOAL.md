# /goal: Video „Papier-Abgleich“ produzieren

```
/goal Produziere aus video/DREHBUCH.md und video/SKRIPT.md im Repo smlfg/papier-abgleich ein
10-minütiges deutsches Erklärvideo (1920×1080, 30 fps, MP4/H.264 + AAC) samt Untertiteln,
Thumbnail und YouTube-Metadaten. Lade nichts hoch und veröffentliche nichts.
```

## Ziel

Ein fertig geschnittenes Video, das zeigt, wie ein Entwickler nach einem Tag agentischer Arbeit sein Projekt durch eine Handzeichnung zurückholt. Länge 9–11 Minuten. Alle Aussagen stammen aus `video/SKRIPT.md`; jede Zahl ist in `video/RECHERCHE.md` belegt.

## Inputs

| Was | Pfad |
|---|---|
| Szenen, Dauern, On-Screen-Texte, Kapitel | `video/DREHBUCH.md` |
| Voiceover-Text pro Szene | `video/SKRIPT.md` |
| Faktenbasis und Lücken | `video/RECHERCHE.md` |
| Fertige Seite | `examples/inkpartner-grillme/site/inkpartner-fakten.html` |
| Skizze und Testseiten | `examples/inkpartner-grillme/zeichnungen/*.png` |
| Standbilder | `docs/img/hero.png`, `docs/img/zeichnung-ergebnis.png`, `examples/inkpartner-grillme/shots/*.png` |
| Werkzeug-Demo | `build.py`, `examples/minimal/` |

## Schritte

1. **Prüfen:** Drehbuch-Summe = 600 s; jede Szene im Skript hat eine Szene im Drehbuch. Fehlende Assets (siehe „Fehlende Assets“ im Drehbuch) auflisten und Ersatz wählen, nichts erfinden.
2. **Screen-Recordings der Seite** mit Playwright oder Chrome headless (1920×1080): Scrollen durch das Urteil, Filter `?status=geaendert`, Klick auf Knoten `#validate`, Tabs `#validate/code` und `#validate/verlauf`, mobile Ansicht 390×844 `#max4`. Jede Aufnahme als eigene Datei in `video/build/rec/`.
3. **Skizzen-Animationen:** Ken-Burns über die Grillme-Skizze (Szene 1, 8), Split-Bild mit Pfeil (Szene 9), mit ffmpeg `zoompan` oder einem Python-Skript.
4. **Terminal-Szene** (Szene 11): echte Aufnahme von `python3 build.py examples/minimal` (z. B. asciinema → agg), danach Browser mit `minimal.html`.
5. **Voiceover:** bevorzugt Samuels eigene Stimme (Aufnahmeplan pro Szene als `video/build/vo/NN.txt` ausgeben). Fallback lokal per TTS (z. B. Piper, Stimme „Thorsten“), klar als Platzhalter-VO kennzeichnen.
6. **Schnitt** mit ffmpeg: Szenen nach Drehbuch-Dauer, VO darüber, Pausen mit Bild statt Stille füllen, leise Musik nur, wenn lizenzfrei und ≤ −24 LUFS unter der Stimme. Lautheit gesamt −14 LUFS.
7. **On-Screen-Texte** exakt laut Drehbuch, gut lesbar (≥ 42 px, Kontrast AA).
8. **Untertitel** `video/build/papier-abgleich.de.srt` aus dem Skript, an VO-Timing ausgerichtet.
9. **Thumbnail** 1280×720: links Ausschnitt der Skizze, rechts Ausschnitt der Seite, Text „Zeichnung vs. Code“.
10. **YouTube-Metadaten** in `video/build/youtube.md`: Titel (≤ 70 Zeichen), Beschreibung mit Repo-Link, Kapitel aus dem Drehbuch, Tags.
11. **Abnahme-Bericht** `video/build/REPORT.md`: Länge, Liste aller Assets mit Pfad, Liste offener Lücken, 3 Standbilder (Anfang, Mitte, Ende).

## Akzeptanzkriterien

- Länge 9:00–11:00; Kapitelmarker stimmen mit dem Video überein (±2 s).
- Jede gesprochene Zahl steht in `RECHERCHE.md`; nichts aus „Lücken“ wird als Fakt gesprochen.
- Untertitel vollständig, max. 2 Zeilen à 42 Zeichen.
- Keine Ruckler in Recordings, keine Konsolen-Fehler sichtbar.
- Alle Ausgaben unter `video/build/` (nicht committen, Dateien groß).

## Verbote

- Die private Notiz „/Frust“ weder öffnen noch zeigen noch zitieren. Szene 6 bleibt eine Schwarzblende mit Uhrzeit.
- Keine Zugangsdaten, Tokens, Mailadressen oder Pfade aus dem Home-Verzeichnis im Bild (Terminal-Prompt neutral setzen).
- Keine Aufnahmen vom echten Tablet ohne Samuels Freigabe; keine Schreibzugriffe aufs Tablet.
- **Nichts veröffentlichen** (YouTube, Social Media, Pages) ohne ausdrückliches OK von Samuel.
