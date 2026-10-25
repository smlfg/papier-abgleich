Deutsch: [FLOW_SCHEMA.md](FLOW_SCHEMA.md)

# `flow.json` and `project.json`: data format

Field names, status IDs and marker IDs are German, and they are the same in every language version. Only the displayed text is translated.

`build.py` reads two files from a project folder:

| File | Required | Content |
|---|---|---|
| `flow.json` | yes | The sketch as a graph: stages, nodes, statuses, evidence, code snippets, history |
| `project.json` | no | Page texts (title, intro, labels), image name, verbatim sketch points |

`flow.json` is the **single source of content**. The page embeds the file unchanged (`<script type="application/json" id="flow">`); `build.py` only fills in missing key figures under `stats` from the data.

A complete mini example is in [`examples/minimal/`](../examples/minimal/), a real one with 24 nodes in [`examples/inkpartner-grillme/`](../examples/inkpartner-grillme/).

---

## `flow.json`

### Top level

| Field | Type | Required | Meaning |
|---|---|---|---|
| `stages` | `Stage[]` | yes | Stages in the reading order of the sketch. Each stage becomes a lane in the diagram. |
| `nodes` | `Node[]` | yes | One node per sketch point (or part of one). |
| `commit` | string | no | Full SHA of the checked code state. |
| `branch` | string | no | Branch of the checked code state. |
| `sessions` | `{ [ref]: Session }` | no | Agent sessions that `verlauf[].ref` points to (e.g. `"S1"`). |
| `commits` | `Commit[]` | no | Commits for the table and the history. |
| `offen` | `Offen[]` | no | Open questions; nodes refer to them via `node.offen`. |
| `regeln` | `{ [code]: string }` | no | Rules/guards that apply in the code (e.g. `"R-RATE": "…"`). |
| `regeln_quelle` | `{ [präfix]: string }` | no | Where the rules come from, per prefix. |
| `docs` | `{ [name]: url }` | no | Project documents. |
| `stats` | `Stats` | no | Key figures for the header; missing values are computed by `build.py`. |

### `Stage`

| Field | Type | Required | Meaning |
|---|---|---|---|
| `id` | string | yes | Identifier that `node.stage` refers to |
| `name` | string | yes | Display name (e.g. "Read") |

Stages without nodes are hidden (`build.py` warns).

### `Node`

| Field | Type | Required | Meaning |
|---|---|---|---|
| `id` | string | yes | Unique; appears in the deep link `#id`, `#id/code`, `#id/verlauf` |
| `label` | string | yes | Text **as in the sketch** (original wording) |
| `label_orig` | string | no | Original sketch wording, if `label` is a translation. It is shown in the panel as “Original sketch label”. |
| `stage` | string | yes | `Stage.id` |
| `status` | enum | yes | `stimmt-noch` · `geaendert` · `anders` · `teilweise` · `unklar` (shown as still true · changed · different · partial · unclear) |
| `row` | int ≥ 0 | yes | Row within the stage (relative; the smallest value per stage is the first row) |
| `col` | 0–2 | yes | Column (left, centre, right) |
| `punkt` | string | no | Number of the sketch point (`"11"`, `"8 · 9"`, `"—"`) |
| `was` | string | no | What the step does, in plain language (1 sentence; also shown in the node) |
| `warum` | string | no | Reasoning for the status |
| `fakt` | string | no | Fact in 1–3 sentences (long form) |
| `zahlen` | string[] | no | Key figures as short chips (`"Timeout 600 s → 45 s"`) |
| `regeln` | string[] | no | Keys from `regeln` |
| `offen` | string[] | no | `Offen.id`s |
| `next` | string[] | no | Target nodes of the arrows (order matters for diamonds) |
| `shape` | `"raute"` \| `"notiz"` | no | `raute` = decision (diamond, first arrow "yes", further ones "no"); `notiz` = margin note |
| `edge_labels` | `{ [nodeId]: string }` | no | Custom arrow labels, override yes/no |
| `snippets` | `Snippet[]` | no | Code snippets for the tab **Code** |
| `verlauf` | `Verlauf[]` | no | Entries for the tab **History** |
| `commits` | string[] | no | Short SHAs that affect this node |
| `docs` | `{name, url}[]` | no | Documents for this node |
| `belege` | `Beleg[]` | no | **Evidence model**, see below |

For backward compatibility, the ids `raute` and `user` also count as diamond and margin note respectively even without `shape`.

### `Snippet`

| Field | Type | Required | Meaning |
|---|---|---|---|
| `file` | string | yes | Path in the repo |
| `start`, `end` | int | yes | Lines (1-based, inclusive) |
| `code` | string | yes | Verbatim content, **from `git show <sha>:<path>`**, never from memory |
| `url` | string \| null | no | Permalink to the SHA with `#Lstart-Lend`; `null` if the commit was not pushed |

### `Verlauf`

| Field | Type | Required | Meaning |
|---|---|---|---|
| `ref` | string | yes | Session key (`"S3"`) or short SHA |
| `text` | string | yes | What changed or was shown there |
| `url` | string \| null | no | Link (commit, doc) |
| `commit` | string | no | Short SHA, if the entry belongs to a commit |

### `Session`, `Commit`, `Offen`

```jsonc
"sessions": { "S1": { "id": "77114ae4", "zeit": "24.10. 22:10–00:12", "titel": "Stift-Fehler sichtbar machen" } },
"commits":  [ { "short": "29c7a55", "url": "https://github.com/…/commit/29c7a55…", "msg": "pen: keep cat's stderr …", "wo": "watch/write-gap" },
              { "short": "9ba24a5", "url": null, "msg": "…", "wo": "nur lokal" } ],
"offen":    [ { "id": "drift", "titel": "…", "text": "…", "quelle": "S5",
                "snippet": { "file": "…", "start": 1, "end": 3, "code": "…", "url": null } } ]
```

`url: null` means **local only** and is shown without a link. Never build a link to a commit that was not pushed.

### `Stats` (optional)

| Field | Default when missing |
|---|---|
| `sessions` | number of `sessions` |
| `subagent` | – (the extra line is omitted) |
| `commits_auf_github` | commits with `url` |
| `commits_lokal` | commits without `url` |
| `offene_punkte` | number of `offen` |
| `skizzen_punkte` (old: `grillme_punkte`) | number of distinct `node.punkt` |
| `status_count` | count over `nodes[].status` |

---

## Evidence model (`belege`)

Every fact should be checkable without opening the source: **a verbatim quote of the source plus a marker** that indicates the degree of proof.

```json
"belege": [
  { "quote": "return [Task.from_line(l) for l in lines]", "marker": "BELEGT",    "quelle": "todo/parse.py:12", "url": null },
  { "quote": "Mit 10 000 Zeilen getestet: 0,4 s",         "marker": "OFFLINE",   "quelle": "tests/test_perf.py" },
  { "quote": "Auf dem Laptop sortiert ausgegeben",        "marker": "GERAET",    "quelle": "Session 2, 14:10" },
  { "quote": "Wahrscheinlich in einem älteren Branch",    "marker": "HYPOTHESE", "quelle": "—" }
]
```

| Field | Type | Required | Meaning |
|---|---|---|---|
| `quote` | string | yes | Verbatim quote (code line, log line, transcript sentence) |
| `marker` | enum | yes | see table |
| `quelle` | string | no | File:line, commit, session + time |
| `url` | string \| null | no | Permalink, if public |

| Marker | English label | Meaning | Display |
|---|---|---|---|
| `BELEGT` | verified in code | proven in the code or commit | green |
| `GERAET` | seen on device | observed on the real device | orange |
| `OFFLINE` | offline only | only in tests or simulation | grey-blue |
| `HYPOTHESE` | hypothesis | plausible, not proven | violet |

Quotes are verbatim, so they stay in the language of the source, as in the German examples above. A translated `flow.en.json` keeps the `quote` unchanged. If needed, it adds an English gloss in `quelle` or in the node text.

The field is optional: existing data (such as the inkpartner example) keeps building; the **Evidence** section appears in the tab **Fact** only when `belege` is filled. `build.py` aborts if a marker is not in the list and warns on a missing quote.

---

## `project.json`

All fields optional; defaults are in `DEFAULT_META` (German) and `DEFAULT_META_EN` (English) in `build.py`.

| Field | Meaning |
|---|---|
| `title`, `description` | `<title>` and meta description |
| `brand`, `brand_sub` | wordmark at the top left |
| `eyebrow`, `headline` | header line and heading |
| `lede_html`, `subtitle_html` | intro and subline; **HTML allowed** (only your own, trustworthy texts) |
| `note_ref` | designation of the note (e.g. `/Inkpartnertest p. 3`) |
| `image` | file name of the note image in the project folder (default `notiz.png`) |
| `footer` | footer |
| `point_label`, `points_label` | "sketch point" / "sketch points", e.g. "Grillme point" |
| `code_ref` | name of the code state in the verdict (e.g. `watch/write-gap`) |
| `callout_offen_id` | `Offen.id` that appears as a hint box below the verdict |
| `example_node` | node for the example deep link in the help text |
| `theme_key` | `localStorage` key for dark mode |
| `points` | verbatim sketch points as a table: `[[nr, notiz, status, beleg], …]` |
| `lang_switch` | optional link to the other language version in the top bar: `{"href": "…", "label": "English", "hreflang": "en"}` |

All texts except `*_html` are HTML-escaped.

---

## Language versions (`--lang`)

`build.py --lang en` builds the page with an English interface. This covers statuses, markers, tabs, headings, key figures and the verdict sentences. The default is `--lang de`.

| File | Used with `--lang en` |
|---|---|
| `flow.en.json` | instead of `flow.json`, if it exists |
| `project.en.json` | instead of `project.json`, if it exists |

Without these files, the content is taken from `flow.json`/`project.json` unchanged, and only the interface is English. The multi-file build is written as `site/index.en.html` and shares `style.css` and `app.js` with the German version.

Translation rules:

- Translate `label`, but keep the verbatim sketch wording in `label_orig`.
- Never translate code, snippets, SHAs, URLs or evidence quotes.
- Keep `id`, `status`, `marker` and all field names unchanged, so that deep links like `#validate/code` work in both versions.
- Link the two pages with `lang_switch` in both project files.

Example from the repo:

```bash
python3 build.py examples/inkpartner-grillme --name inkpartner-fakten.html
python3 build.py examples/inkpartner-grillme --lang en --name inkpartner-fakten.en.html
```
