---
name: papier-abgleich
description: >-
  use this when: after a phase of agentic work the human should sketch their
  understanding of a project/code on paper (e.g. reMarkable), and the sketch
  is mapped point by point against the real code (still true / changed /
  different / partial / unclear), with evidence and a clickable website that
  follows the structure of the sketch. Also for 'ownership check',
  'Grillme check', 'does my understanding still hold?', agentic sprawl.
---
# Papier-Abgleich (Human-Agent Ownership Check)

*English version of `skills/papier-abgleich/SKILL.md`. Status IDs and marker IDs stay German, because they are the values used in `flow.json`.*

## Purpose
Agentic work quickly produces more code than the human understands. This workflow restores understanding and ownership: **The human draws their mental model, the agent holds the real code against it.** The result is a measurable answer to "Does my picture still hold?" and a map that helps you take the project back.

Principle: *The human provides the structure, the agent provides the evidence.* The agent does not silently correct the sketch; it marks deviations.

## When to trigger
- After roughly 4–8 agentic sessions on the same problem, or when several parallel solutions to the same problem emerge (agentic sprawl).
- When the human expresses frustration, disorientation, or "I no longer understand my own code".
- Before a merge, a handover, or a freeze.
- The brake is deliberate: **"Enough agentic work, now onto paper."**

## Roles
- **Human:** draws the pipeline/architecture from memory, without looking at the code. Confirms which page is meant. Decides in the end what they take over.
- **Agent (content):** reads the sketch and the sources, maps, provides evidence, builds the view. Invents nothing.
- **Worker (optional):** takes on the heavy reading/build work; the agent checks its result itself.

## Workflow

### 0. Prompt for the human
Short and open: "Draw how you think the system works – from input to output, with the names, numbers, and boundaries you have in your head. Don't look anything up." 10–20 minutes are enough.

### 1. Secure and confirm the source
- Fetch the most recent handwritten page (e.g. tablet sync, read-only) and render it.
- **Confirm the page with the human** before reading it. Do not guess which note is meant; name the notebook, the page, and the modification time.
- Personal notes (feelings, self-doubt) do not belong in the comparison. They are addressed, but not published.

### 2. Transcription
- For tall/small pages, cut into strips and enlarge, then read from top to bottom.
- Verbatim, with the original spelling. Mark uncertain readings with `[?]`. Describe sketches as a flow (A → B, branches, yes/no diamonds).
- Break down into numbered **sketch points** (one claim per point). Stored in: `NOTIZEN.md`.

### 3. Gather context
- Code: all relevant branches, not just `main` (the newest work often sits on feature branches). Snippets only via `git show <sha>:<path>`, never from memory.
- History: session transcripts, commits (message, time, branch), separate local from pushed commits.
- Use existing fact documents as a starting point, but check them for currency.

### 4. Comparison per point
Each sketch point gets exactly one status:

| Status (ID) | Meaning |
|---|---|
| **still true** (`stimmt-noch`) | sketch and current code agree |
| **changed** (`geaendert`) | it was true back then, the code has changed since (name commit/session) |
| **different** (`anders`) | the sketch contradicts the code (e.g. the file/type does not exist that way) |
| **partial** (`teilweise`) | the core is right, the details differ |
| **unclear** (`unklar`) | not provable, ask the human |

For every point: fact in 1–3 sentences, **evidence** (file:line + link, commit link, or session time), numbers where available, affected rules/guards, open questions.

**Evidence model (mandatory):** every fact with a verbatim quote of the source plus a marker:
- `BELEGT` (verified in code): proven in the code or commit
- `GERAET` (seen on device): observed on the real device
- `OFFLINE` (offline only): only in tests or simulation
- `HYPOTHESE` (hypothesis): plausible, not proven

Quotes stay in the language of the source. A translated page may add a gloss, but it never replaces the quote.
This way every point can be checked without opening the source.

### 5. Build the view (sketch = structure)
- **The structure of the page follows the human's sketch**, not some agent architecture. Same order, same branches, same names (even if they are called something else in the code; then that is noted as a deviation in the node).
- Nodes = sketch points, grouped into stages (e.g. Read → Understand → Judge → Check → Draw → Write → Failure case). Every node shows a status dot.
- A click opens a side panel with the tabs **Fact / Code / History**.
- Header: key figures (sessions, commits, open points, sketch points), two verdict cards, “Where the sketch still holds” and “Where the code has moved on”, and a section “What is still open”.
- The "Original note" switch shows the handwriting sharply.
- Handling: search, status filter, keyboard (arrows, Esc, `/`), deep links (`#node/code`), mobile view.
- Data-driven: `flow.json` as the single source, the build script generates the page. Additionally a **self-contained single file** (CSS/JS/image inline, no CDNs) for sharing.
- Optional second language: `build.py --lang en` with `flow.en.json` / `project.en.json` next to the originals. Translate labels, but keep the verbatim sketch wording in `label_orig`, and keep evidence quotes in their original language. Use `lang_switch` to link the two pages.

### 6. Check (before handover)
- All links return HTTP 200; unpushed commits get no link and are marked as "local only".
- Embedded data = `flow.json`; code snippets come from `git show`.
- Browser render (headless) without JS errors, without "undefined"; screenshots of overview, panel, filter, mobile.
- No writing into the repo, no push, source (tablet) read only.

### 7. Handover to the human
- Single file + 1–2 screenshots, 3–5 sentences of result: how many points hold, what has changed, what is open.
- Iterate until the human says it matches their picture. Feedback like "thin" or "UX suboptimal" means: more evidenced content per node and clearer structure, not more features.
- Then ask the human: Which deviation surprised you? What do you take over into your picture, what into the code?

## Quality rules
- Never invent facts, SHAs, numbers, or code. Prefer "unclear".
- Actively mark outdated documents as outdated instead of adopting them.
- The human's sketch is the main thing. The agent's view is only evidence.
- Token budget: hand heavy reading rounds to a worker, check the results yourself by sampling.

## Artefacts (standard layout)
```
abgleich/
  NOTIZEN.md        Transcription + sketch points
  ABGLEICH.md       Status table with evidence
  flow.json         Data (nodes, edges, statuses, evidence, snippets)
  build.py          generates site/
  site/index.html   + style.css, app.js, notiz.png
  site/<name>.html  self-contained single file
  shots/            Verification screenshots
```
