# Grillme-Notizen – Abschrift

Quelle: reMarkable-Notizbuch `/Inkpartnertest` (8194ca66), Seite 3 von 7, 1044 Striche.
Notizbuch zuletzt geändert 25.10.2026 00:30 (Berlin-Zeit).
Gerendert: `zeichnungen/inkpartnertest-s3-grillme.png` (2255×14214 px), in 12 Streifen gelesen.
Nur gelesen, das Tablet wurde nicht beschrieben. Schreibweise wie im Original, unklare Stellen mit [?].
Einzelne kleine Haken (✓) und Wellen am rechten Rand sind vermutlich Agenten-Tinte, nicht Samuels Schrift [?].

## Abschrift (von oben nach unten)

**Testaufgaben ganz oben** (Haken bzw. Bogen darunter, vermutlich Agentenmarken [?]):
- `3 + 1 = 2`
- `3 + 3 = 4`

**Skizze 1:** `Bild → VLM`. Ein Bogenpfeil vom VLM führt zu **Agent**. Vom Agent verzweigt es in zwei Äste:
- links: **Fach** „List“ [?]
- rechts: **Element** – Text / Bild / Frag[e]

Darunter steht „klassifiziert“. Ein Bogenpfeil führt weiter zu:
- **Fach „Klasse“**, „mit Satz an Hilfsmitteln“, „Profil“

**Def: Judge promts – erlaubte Zeichen**

**Skizze 2:**
- `3+3=4` ist eingekreist, rechts daneben `Bild → VLM`.
- Ein Pfeil zurück nach links führt zu **Fach: Mathe / Art: Rechnung**.
- Von dort ein Pfeil nach rechts → **VLM** mit „Promptvorlagen“.
- Ein Pfeil nach unten mit „output“ führt zu:
  - **Vorschlag**, ein Bogen verweist auf „Element“.
  - **URTEIL = Bolean**
  - **Zeichen = Korrekturmarke**

**für Mathe: 6 Stück**
1. ✓ = Haken
2. ___ = unterstreichen
3. ○ = Kreis
4. ~~~ = unlesbar
5. ? = check aber schwer [?]
6. Wort/text

Neben „Wort/text“ steht eingekreist: (nicht Text) [?, Bezug unklar]

**Pro Runde max 4 Zeichen ≙ watcher 1,5 sek → review**

**Agent wählt Zeichen daher:**
- `return → judge.py → plan.py →`
- Ein Pfeil zeigt auf plan.py: „dort fängt validate an“
- **validate.py ist harter check**
- „funktioniert so:“ [?, auch „funktioniert 80 %“ möglich] … „ist zu streng“
- Rechts daneben, Eingaben für validate: „→ Vorschläge vom Judge + Element-Liste + Fach-Profil“

**Skizze 3 (Raute, Entscheidung):**
- **yes** → „gesammelt + sortier nach prio“ → **draw**
- **no** → „verworfen List“ → (Pfeil ins Leere)

„so funktioniert“ (Pfeil auf draw):
- **Zeich → Pixel** pos (Element) → Schüler-Tinte, passend dazu Agententinte
- Kasten **USER: `3+3=?`**
- **Draw → Strich-Dictionary**
- **Delivery → vipen [virtueller Stift?] → RM**
- **schreiben vom Agenten**
- **SSH Tablet.send → schreibt**
- „nach schreiben“ → Notiz-App, „Native Device Editor“ [?]
- `return None`
- **cat ( ließ .RM)**

**Wenn schreiben fehlschlägt:** watcher → „element implodiert“ [?] (daneben ein Lupen-Symbol bzw. „Q“ [?])

## Abgleich mit dem Code (Stand 25.10.2026 ~00:40 Berlin-Zeit)

Geprüft gegen GitHub smlfg/inkpartner:
- `main` = a48470f
- `pen/cat-stderr` = 29c7a55
- `docs/read-pipeline` = 6aa80de
- `watch/write-gap` = [0bfccb4](https://github.com/smlfg/inkpartner/commit/0bfccb439cf2d628fcf241d6caae3b4738015037), 25.10. 00:29 Berlin-Zeit
- `claude/focused-planck-2ml7jl` = 357da13

Außerdem gegen die Cursor-Transkripte.

| # | Notiz | Status | Beleg |
|---|---|---|---|
| 1 | Bild → VLM → Agent | stimmt noch | `agent.read` rendert nur die Schülertinte als ein Bild → VLM |
| 2 | Agent klassifiziert Fach + Elemente (Text/Bild/Frage) | stimmt im Kern, Details anders | `read()` gibt `(subject, elements)` zurück. Elementarten: line, formula, code, text, node, edge, arrow, box, table, drawing, printed – kein „Bild“/„Frage“; Hilfe-Fragen erkennt `asks_for_help`. „Erst erkennen, dann Prompt“ (9ba24a5) ist nur lokal, nicht auf GitHub |
| 3 | Fach-„Klasse“ mit Hilfsmitteln = Profil | stimmt noch | `profiles.py`: math, code, diagram, pm, prose mit Judge-Prompt, Zeichen, max_actions |
| 4 | Def: Judge-Prompt + erlaubte Zeichen | stimmt noch | `Profile.judge` + `Profile.marks` |
| 5 | Fach Mathe / Art Rechnung → VLM mit Promptvorlage | stimmt teilweise | Mathe-Profil (sympy als Prüfer) ja; eine eigene „Art“ (Rechnung) gibt es nicht |
| 6 | Output: Vorschlag → Urteil = Boolean, Zeichen = Korrekturmarke | geändert / anders | Urteil ist 5-wertig: correct, wrong, hint, help, unreadable; die Farbe folgt dem Urteil (`marks.COLOR`) |
| 7 | Mathe: 6 Zeichen (Haken, unterstreichen, Kreis, Welle = unlesbar, ?, Text) | stimmt noch | `ALL_MARKS` = check, underline, circle, wavy, question, note (main und write-gap gleich) |
| 8 | Pro Runde max. 4 Zeichen | stimmt für Mathe | `max_actions=4` (Default, gilt für Mathe); pm/prose 3; zusätzlich höchstens 1 Hilfe-Notiz pro Runde |
| 9 | Watcher 1,5 s → review | stimmt noch (Takt) | `--interval` Default 1.5 s. Neu seit 0bfccb4: 10 s R-COOLDOWN nach jedem Schreiben, Modell-Timeout 45 s im Watcher (vorher 600 s) |
| 10 | return → judge.py → plan.py | anders benannt | Es gibt kein judge.py: Judge ist `agent.judge` (agent.py), Ablauf in `review.run` |
| 11 | validate.py = harter Check, „zu streng“ | Datei anders, Inhalt stimmt | Kein validate.py; `plan.validate()` in plan.py. „Zu streng“: R-VIEWPORT 0.00 und R-RATE blockierten laut Sessions; R-PEN-NEAR in 0bfccb4 per `if False` abgeschaltet |
| 12 | Eingaben: Judge-Vorschläge + Element-Liste + Fach-Profil | stimmt noch | `validate(actions, elements, profile, …)` |
| 13 | Raute yes → gesammelt + nach Prio sortiert → draw; no → Verworfen-Liste | stimmt noch | `out.accepted.sort` (help < wrong < unreadable < hint < correct), `out.rejected` mit Grund |
| 14 | draw: Zeichen → Pixel an Element-Position, Schüler- vs. Agententinte, Strich-Dictionary | stimmt, seit 0bfccb4 eigenes Modul | `draw.py` (neu in 0bfccb4) gibt `list[dict]` Striche mit Action-Key zurück; auf main noch in plan.py |
| 15 | Delivery → virtueller Stift → RM, SSH Tablet.send | stimmt, Weg geändert | Per SSH an /dev/input. main: `cat`; write-gap und planck: `dd bs=24 iflag=fullblock` (37dd2e8, 0bfccb4) |
| 16 | Nach Schreiben: Notiz-App / Native Device Editor | unklar | Bezug nicht eindeutig. Der Dateiweg mit Neustart von xochitl existiert noch als Rückfall (`systemctl stop xochitl …`) |
| 17 | return None; cat (ließ .rm) | stimmt noch | `.rm` wird per `ssh cat` gelesen; diverse `return None` in watch.py |
| 18 | Wenn Schreiben fehlschlägt: Watcher → Element „implodiert“ [?] | unklar / anders | Code: pending + retry_pending, nach 2 Fehlschlägen Stift-Pause; Eskalation nach Codex-Sitzung 23.10. (watch.py ~595) |
