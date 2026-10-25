# Recherche: „Papier-Abgleich“ (Faktenbasis für Drehbuch und Skript)

Regeln: Jede Zeile hat eine Quelle. Was nicht belegt ist, steht als **LÜCKE**. Die private Notiz „/Frust“ wurde nicht gelesen und wird nicht zitiert; der Moment gegen 20 Uhr heißt hier nur „Frust-Moment“. Zeiten in Europe/Berlin.

Quellen-Kürzel:
- **GIT** = `git log --all` im inkpartner-Repo (github.com/smlfg/inkpartner, öffentlich)
- **FLOW** = `examples/inkpartner-grillme/flow.json` (dieses Repo)
- **S1–S8** = Cursor-Session-Transkripte (`inkpartner-sessions/txt/<id>.txt`, Zuordnung siehe FLOW `sessions`)
- **GY** = Graveyard-Retrospektive (`graveyard/README.md`, `graveyard/analysis/CURRENT_STATE.md`)
- **SKILL** = `skills/papier-abgleich/SKILL.md`

## Zeitleiste

| Zeit | Ereignis | Quelle |
|---|---|---|
| 17.–24.10. | Ältere Phase „reMarkable Algebra Agent“ (PenEcho / algebra-agent): 25 Versuche, 63 Fehler, 34 Sackgassen | GY README |
| 21.10. | Definition of Done gemessen: 0 von 14 Punkten; danach nicht neu gemessen | GY CURRENT_STATE §1 |
| 24.10. 00:23 | Erster inkpartner-Commit `a27bee7` „one vocabulary of marks for every subject, rules outside the model“ | GIT |
| 24.10. 03:47–06:41 | Nacht-Runden: Regeln, Prompts, „Messstand rounds 1–7“ | GIT (`b470cff` … `f17645d`) |
| 24.10. 17:41–19:26 | Live-Test-Block mit Gerät: Viewport, Stift-Takt, Kalibrier-L, `dd bs=24` statt `cat`; Branch `claude/focused-planck-2ml7jl` | GIT (`f5b3915` … `357da13`) |
| 24.10. 19:14 | Letzter Stand `main` vor der Cursor-Phase (`a48470f`) | FLOW commits |
| 24.10. ~20 Uhr | Frust-Moment (nur allgemein erwähnen) | Auftraggeber; **LÜCKE:** kein öffentlicher Beleg, bewusst nicht recherchiert |
| 24.10. 22:10–00:12 | S1: Stift-Fehler sichtbar machen, „erst erkennen“-Versuch | FLOW sessions S1 |
| 24.10. 22:25 | Commit `29c7a55` „pen: keep cat's stderr when the inject pipe breaks“ | GIT |
| 24.10. 22:25–23:47 | S3: Watcher-Start, Test „3 + 3 = 7“ | FLOW S3 |
| 24.10. 22:32–00:20 | S2: Lese-Pipeline, Timeout, Viewport | FLOW S2 |
| 24.10. 22:32–00:27 | S5: Schreib-Pipeline, Metriken, Guards (+ 1 Subagent) | FLOW S5 |
| 24.10. 22:44 | Commit `6aa80de` „docs: keep the read pipeline …“ | GIT |
| 24.10. 23:01–23:43 | S4: Stift-Zustellung, 24-Byte-Grenze | FLOW S4 |
| 24.10. 23:27–23:45 | S6: Refactor `draw` → `draw.py` | FLOW S6 |
| 24.10. 23:53–00:15 | S7: py-spy-Profil des Watchers | FLOW S7 |
| 25.10. 00:10–00:14 | S8: Event-Tracer (hunter) | FLOW S8 |
| 25.10. 00:29 | Commit `0bfccb4` „watch: wait 10s after a write …“ (Code-Stand des Abgleichs) | GIT, FLOW |
| 25.10. | Lokaler Commit `9ba24a5` (Branch try/recognize-then-prompt), nicht auf GitHub | FLOW commits |
| 25.10. ~00:30 | Grillme-Skizze auf dem reMarkable (Notiz Inkpartnertest S. 3) | Seite: „Notiz /Inkpartnertest S. 3, 25.10.2026 00:30 Berlin“ |
| 25.10. nachts | Faktenseite (FAKTEN.md, Hermes), Abgleich, Website v1 → v2 → v3, Repo papier-abgleich | Repo-Verlauf; **LÜCKE:** genaue Uhrzeiten v1/v2 nicht protokolliert |

## Zahlen

| Wert | Zahl | Quelle |
|---|---|---|
| Commits im inkpartner-Repo (alle Branches) | 75 (74 am 24.10., 1 am 25.10.) | GIT |
| Zeitspanne Commits | 24.10. 00:23 → 25.10. 00:29 | GIT |
| „~20 Stunden Projekt“ | Aussage Samuel | **LÜCKE:** Arbeitszeit nicht gemessen; Commit-Spanne ist ~24 h |
| Cursor-Sessions | 8 + 1 Subagent laut FLOW; Samuel spricht von 6 | FLOW stats; **Abweichung:** S7/S8 sind kurze Werkzeug-Sessions (py-spy, hunter), wohl daher „6“ |
| Grillme-Punkte | 18 | FLOW stats |
| Knoten / Stufen | 24 / 7 | FLOW |
| Status | 11 stimmt noch · 5 geändert · 4 teilweise · 2 anders · 2 unklar | FLOW stats.status_count (nachgezählt) |
| Offene Fragen | 9 | FLOW stats |
| Commits im Abgleich | 6 auf GitHub + 1 lokal | FLOW stats |
| Graveyard | 25 Versuche, 63 Fehler, 34 Sackgassen, 69 Belege | GY README |
| DoD | 0 von 14 (gemessen 21.10.) | GY CURRENT_STATE |

## Beste Momente (mit Zitat)

1. **Der Testsatz.** Samuel schreibt „3 + 3 = 7 auf neuer seite“; der Agent: „Seit drei Minuten keine Reaktion auf `3 + 3 = 7`.“ (S3, `229b241d.txt:280–283`)
2. **Falsch gelesen.** „Die Seite in Inkpartnertest wurde als Code gelesen, nicht als Rechnung: 5 Elemente, 0 Zeichen.“ (S4, `8008a735.txt:224`)
3. **Die 24-Byte-Grenze.** „`cat` liest 4096 Byte, ein Stift-Event ist 24 Byte. Fällt die Grenze mitten ins Event, verwirft das Tablet den Rest und der Strich bleibt offen.“ (S4, `8008a735.txt:68`)
4. **Der Fix im Commit.** `37dd2e8` „Pen events through dd bs=24 iflag=fullblock instead of cat“ (GIT)
5. **600 Sekunden.** „Der Ollama-Aufruf darf bis zu 600 Sekunden blockieren. In der Zeit läuft kein Scan.“ (S5, `9b291812.txt:893`)
6. **Wo man eingreift.** „Der sichere Eingriff sitzt am Timeout, nicht in `plan.py` oder `review.py`.“ (S5, `9b291812.txt:911`)
7. **Profiler statt Raten.** „Ich richte py-spy ein.“ (S7, `4e18d5fd.txt:7`)
8. **Die Skizze.** Grillme, Inkpartnertest S. 3: „Bild → VLM → Agent“, „Pro Runde max 4 Zeichen ≙ watcher 1,5 s → review“, „dort fängt validate an“ (Notizbild; Transkription `examples/inkpartner-grillme/NOTIZEN.md`)
9. **Das Urteil.** 11 von 24 Knoten stimmen noch; „dort fängt validate an“ ist inzwischen geändert (FLOW, Seite „Das Urteil“)
10. **Die Bilanz davor.** „The Definition of Done stands at 0 of 14 checkboxes.“ (GY CURRENT_STATE §1)
11. **Ehrlich zum Stand.** „Zero device sessions completed a write-back.“ (GY CURRENT_STATE §1, Stand 21.10.)
12. **Der Ablauf als Regel.** „Der Mensch zeichnet sein mentales Modell, der Agent hält den echten Code dagegen.“ (SKILL, Zweck)

## Kernaussage (Interpretation, als solche kennzeichnen)

- Hauptaufgabe (Lernen mit dem Tablet / Algebra-Tutor): noch nicht erreicht (GY: DoD 0/14; Live-Tests 24.10. zeigen Lese- und Stiftfehler, S3/S4).
- Meta-Aufgabe: gestalten, wie Mensch und Agenten zusammenarbeiten (Skizze → Abgleich → Seite). Das ist angewandte Human-Agent-Interaction: Ownership entsteht über Papier. *Deutung von Samuel, keine Messung.*

## Lücken

- LÜCKE: Arbeitszeit „20 h“ nicht gemessen.
- LÜCKE: Welche Arbeit am 24.10. mit Codex vs. Claude Code lief: Branch-Name `claude/…` belegt Claude Code; Codex-Anteil nicht aus Commits ablesbar.
- LÜCKE: Uhrzeiten von Website v1/v2.
- LÜCKE: „6 vs. 8 Sessions“ mit Samuel klären.
- Bewusst ausgelassen: Inhalt des Frust-Moments.
