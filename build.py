#!/usr/bin/env python3
"""Papier-Abgleich: baut aus flow.json + Notizbild eine klickbare Abgleich-Seite.

Aufruf:
    python3 build.py <projektordner> [--out DIR] [--name DATEI.html] [--lang de|en]

Der Projektordner enthält:
    flow.json      Pflicht. Knoten, Stufen, Status, Belege (siehe docs/FLOW_SCHEMA.md)
    project.json   optional. Texte der Seite (Titel, Lede, Labels) und Skizzen-Punkte
    <bild>         Notizbild, Name in project.json "image" (Standard: notiz.png)

Sprache (--lang, Standard de): steuert die festen Texte der Seite. Mit --lang en werden
flow.en.json und project.en.json gelesen, falls vorhanden (sonst flow.json/project.json).

Ausgabe (Standard: <projektordner>/site):
    index.html, style.css, app.js, <bild>   Mehrdateien-Version (bei --lang en: index.en.html)
    <name>.html                             selbsttragende Einzeldatei (alles inline)

Nur Standardbibliothek, keine Netzwerkzugriffe.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import mimetypes
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEMPLATES = ROOT / "templates"
STATUSES = ["stimmt-noch", "geaendert", "anders", "teilweise", "unklar"]
MARKERS = {"BELEGT", "GERAET", "OFFLINE", "HYPOTHESE"}
NUMBER_WORDS = {1: "Eine", 2: "Zwei", 3: "Drei", 4: "Vier", 5: "Fünf", 6: "Sechs", 7: "Sieben",
                8: "Acht", 9: "Neun", 10: "Zehn", 11: "Elf", 12: "Zwölf"}
DEFAULT_META = {
    "title": "Papier-Abgleich: Skizze gegen den Code",
    "description": "Interaktiver Abgleich einer handgezeichneten Skizze mit dem Code.",
    "brand": "papier-abgleich",
    "brand_sub": "Code-Abgleich",
    "eyebrow": "Papier-Abgleich",
    "headline": "Die Skizze, gegen den Code gehalten",
    "lede_html": "Eine handgezeichnete Pipeline als Diagramm, Knoten für Knoten mit dem Code verglichen.",
    "subtitle_html": "",
    "note_ref": "Notiz",
    "footer": "Quelle: flow.json",
    "point_label": "Skizzen-Punkt",
    "points_label": "Skizzen-Punkte",
    "code_ref": "",
    "callout_offen_id": "",
    "theme_key": "papier-abgleich-theme",
    "image": "notiz.png",
    "example_node": "",
    "points": [],
}
DEFAULT_META_EN = {
    "title": "Paper Check: sketch vs. code",
    "description": "Interactive check of a hand-drawn sketch against the code.",
    "brand_sub": "code check",
    "eyebrow": "Paper Check",
    "headline": "The sketch, held against the code",
    "lede_html": "A hand-drawn pipeline as a diagram, compared with the code node by node.",
    "note_ref": "Note",
    "footer": "Source: flow.json",
    "point_label": "Sketch point",
    "points_label": "Sketch points",
}
NUMBER_WORDS_EN = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven",
                   8: "Eight", 9: "Nine", 10: "Ten", 11: "Eleven", 12: "Twelve"}
# Feste Texte der Seite je Sprache (Platzhalter ui_* in templates/index.html).
UI = {
    "de": {
        "lang": "de", "original_note": "Original-Notiz", "dark_toggle": "Dunkelmodus umschalten",
        "metrics": "Kennzahlen", "status_dist": "Status-Verteilung",
        "status_dist_aria": "Status-Verteilung der 24 Knoten", "verdict": "Das Urteil",
        "pipeline": "Die Pipeline nach Skizze",
        "flow_sub": "{stages} Stufen in der Reihenfolge der Notiz. Knoten anklicken (oder ←/→, 1/2/3 für Tabs, "
                    "Esc schließt, / sucht). Links lassen sich teilen: <code>#{node}/code</code>.",
        "explorer": "Diagramm und Werkzeuge", "toolbar": "Diagramm-Werkzeuge", "filter": "Nach Status filtern",
        "search": "Knoten, Text oder Code suchen …", "stage_nav": "Stufen-Navigation",
        "node_details": "Knotendetails", "prev": "Vorheriger Knoten", "next": "Nächster Knoten",
        "close_panel": "Panel schließen", "tab_fakt": "Fakt", "tab_code": "Code", "tab_verlauf": "Verlauf",
        "open": "Was ist offen", "archive": "Vertiefende Materialien", "commits": "Commits",
        "entries": "Einträge", "th_short": "Kürzel", "th_msg": "Nachricht", "th_where": "Ort",
        "sessions": "Sessions", "th_session": "Session", "th_time": "Zeit", "th_title": "Titel",
        "rules": "Regeln", "verbatim": "wörtliche Abschrift", "th_no": "Nr.", "th_note": "Notiz",
        "th_status": "Status", "th_evidence": "Beleg", "original_close": "Original-Notiz schließen",
    },
    "en": {
        "lang": "en", "original_note": "Original note", "dark_toggle": "Toggle dark mode",
        "metrics": "Key figures", "status_dist": "Status distribution",
        "status_dist_aria": "Status distribution of the nodes", "verdict": "The verdict",
        "pipeline": "The pipeline, as sketched",
        "flow_sub": "{stages} stages in the order of the note. Click a node (or use ←/→, 1/2/3 for tabs, "
                    "Esc to close, / to search). Links are shareable: <code>#{node}/code</code>.",
        "explorer": "Diagram and tools", "toolbar": "Diagram tools", "filter": "Filter by status",
        "search": "Search nodes, text or code …", "stage_nav": "Stage navigation",
        "node_details": "Node details", "prev": "Previous node", "next": "Next node",
        "close_panel": "Close panel", "tab_fakt": "Fact", "tab_code": "Code", "tab_verlauf": "History",
        "open": "What is still open", "archive": "Background material", "commits": "Commits",
        "entries": "entries", "th_short": "Hash", "th_msg": "Message", "th_where": "Where",
        "sessions": "Sessions", "th_session": "Session", "th_time": "Time", "th_title": "Title",
        "rules": "Rules", "verbatim": "verbatim transcript, translated", "th_no": "No.", "th_note": "Note",
        "th_status": "Status", "th_evidence": "Evidence", "original_close": "Close original note",
    },
}


class BuildError(Exception):
    pass


def validate(flow: dict) -> list[str]:
    """Prüft die Pflichtfelder aus docs/FLOW_SCHEMA.md. Gibt Warnungen zurück, wirft bei Fehlern."""
    errors, warnings = [], []
    for key in ("stages", "nodes"):
        if not isinstance(flow.get(key), list) or not flow[key]:
            errors.append(f"'{key}' fehlt oder ist leer")
    if errors:
        raise BuildError("; ".join(errors))
    stage_ids = {s.get("id") for s in flow["stages"]}
    node_ids = [n.get("id") for n in flow["nodes"]]
    if len(set(node_ids)) != len(node_ids):
        errors.append("Knoten-ids sind nicht eindeutig")
    offen_ids = {o.get("id") for o in flow.get("offen", [])}
    for n in flow["nodes"]:
        nid = n.get("id", "?")
        for key in ("id", "label", "stage", "status", "row", "col"):
            if key not in n:
                errors.append(f"Knoten {nid}: Feld '{key}' fehlt")
        if n.get("stage") not in stage_ids:
            errors.append(f"Knoten {nid}: unbekannte Stufe '{n.get('stage')}'")
        if n.get("status") not in STATUSES:
            errors.append(f"Knoten {nid}: Status '{n.get('status')}' nicht in {STATUSES}")
        for target in n.get("next", []):
            if target not in node_ids:
                errors.append(f"Knoten {nid}: next → unbekannter Knoten '{target}'")
        for oid in n.get("offen", []):
            if oid not in offen_ids:
                errors.append(f"Knoten {nid}: offen → unbekannte id '{oid}'")
        for b in n.get("belege", []):
            if str(b.get("marker", "")).upper() not in MARKERS:
                errors.append(f"Knoten {nid}: Beleg-Marker '{b.get('marker')}' nicht in {sorted(MARKERS)}")
            if not b.get("quote"):
                warnings.append(f"Knoten {nid}: Beleg ohne Zitat")
        for s in n.get("snippets", []):
            if not s.get("code"):
                warnings.append(f"Knoten {nid}: Snippet {s.get('file')} ohne Code")
    for s in flow["stages"]:
        if not any(n.get("stage") == s.get("id") for n in flow["nodes"]):
            warnings.append(f"Stufe {s.get('id')}: keine Knoten, wird ausgeblendet")
    if errors:
        raise BuildError("\n  ".join(["flow.json ungültig:"] + errors))
    return warnings


def fill_stats(flow: dict) -> None:
    """Ergänzt fehlende Kennzahlen aus den Daten; vorhandene Werte bleiben unverändert."""
    stats = flow.setdefault("stats", {})
    counts = {s: 0 for s in STATUSES}
    for n in flow["nodes"]:
        counts[n["status"]] += 1
    stats.setdefault("status_count", counts)
    stats.setdefault("sessions", len(flow.get("sessions", {})))
    commits = flow.get("commits", [])
    stats.setdefault("commits_auf_github", sum(1 for c in commits if c.get("url")))
    stats.setdefault("commits_lokal", sum(1 for c in commits if not c.get("url")))
    stats.setdefault("offene_punkte", len(flow.get("offen", [])))
    if "grillme_punkte" not in stats:
        stats.setdefault("skizzen_punkte", len({n.get("punkt") for n in flow["nodes"] if n.get("punkt") not in (None, "", "—")}))


def script_json(obj) -> str:
    """JSON für <script type="application/json">: '</' maskieren, damit der Block nicht endet."""
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def render(template: str, values: dict) -> str:
    def sub(match):
        raw, key = match.group(1) is not None, match.group(1) or match.group(2)
        if key not in values:
            raise BuildError(f"Template-Platzhalter ohne Wert: {key}")
        value = str(values[key])
        return value if raw else html.escape(value, quote=True)
    return re.sub(r"\{\{\{(\w+)\}\}\}|\{\{(\w+)\}\}", sub, template)


def localized(project: Path, base: str, lang: str) -> Path:
    """flow.json → flow.en.json bei --lang en, falls vorhanden; sonst die Standarddatei."""
    if lang != "de":
        candidate = project / base.replace(".json", f".{lang}.json")
        if candidate.exists():
            return candidate
    return project / base


def build(project: Path, out: Path, name: str | None, lang: str = "de") -> dict:
    if lang not in UI:
        raise BuildError(f"Sprache '{lang}' nicht in {sorted(UI)}")
    flow_path = localized(project, "flow.json", lang)
    if not flow_path.exists():
        raise BuildError(f"{flow_path} nicht gefunden")
    flow = json.loads(flow_path.read_text(encoding="utf-8"))
    meta_path = localized(project, "project.json", lang)
    meta = dict(DEFAULT_META)
    if lang == "en":
        meta.update(DEFAULT_META_EN)
    if meta_path.exists():
        meta.update(json.loads(meta_path.read_text(encoding="utf-8")))
    warnings = validate(flow)
    fill_stats(flow)
    image = project / meta["image"]
    if not image.exists():
        raise BuildError(f"Notizbild {image} nicht gefunden (project.json → image)")

    points = meta.pop("points")
    page_meta = {k: meta[k] for k in ("point_label", "points_label", "code_ref", "callout_offen_id", "theme_key")}
    if lang != "de":
        page_meta["lang"] = lang
    n_stages = len(flow["stages"])
    values = {k: v for k, v in meta.items() if isinstance(v, str)}
    ui = UI[lang]
    words = NUMBER_WORDS_EN if lang == "en" else NUMBER_WORDS
    example = meta["example_node"] or flow["nodes"][0]["id"]
    values.update({f"ui_{k}": v for k, v in ui.items() if k != "flow_sub"})
    values["ui_flow_sub"] = ui["flow_sub"].format(stages=html.escape(words.get(n_stages, str(n_stages))),
                                                  node=html.escape(example, quote=True))
    switch = meta.get("lang_switch")  # {"href": "...", "label": "English"}: Link zur anderen Sprachfassung
    values["ui_lang_switch_line"] = (
        f'      <a class="button" href="{html.escape(switch["href"], quote=True)}" hreflang="{html.escape(switch.get("hreflang", ""), quote=True)}">'
        f'{html.escape(switch["label"])}</a>\n' if isinstance(switch, dict) and switch.get("href") else "")
    values.update(
        FLOW_JSON=script_json(flow),
        META_JSON=script_json(page_meta),
        POINTS_JSON=script_json(points),
        stage_count_word=words.get(n_stages, str(n_stages)),
        example_node=example,
        commit_count=len(flow.get("commits", [])),
        session_count=len(flow.get("sessions", {})),
        point_count=len(points),
    )

    template = (TEMPLATES / "index.html").read_text(encoding="utf-8")
    css = (TEMPLATES / "style.css").read_text(encoding="utf-8")
    js = (TEMPLATES / "app.js").read_text(encoding="utf-8")

    out.mkdir(parents=True, exist_ok=True)
    index_name = "index.html" if lang == "de" else f"index.{lang}.html"  # Sprachen teilen sich style.css/app.js
    (out / index_name).write_text(render(template, {**values, "image_src": image.name}), encoding="utf-8")
    (out / "style.css").write_text(css, encoding="utf-8")
    (out / "app.js").write_text(js, encoding="utf-8")
    if image.resolve() != (out / image.name).resolve():
        shutil.copyfile(image, out / image.name)

    mime = mimetypes.guess_type(image.name)[0] or "image/png"
    data_url = f"data:{mime};base64," + base64.b64encode(image.read_bytes()).decode("ascii")
    single = render(template, {**values, "image_src": data_url})
    single = single.replace('<link rel="stylesheet" href="style.css">', f"<style>\n{css}\n</style>")
    single = single.replace('<script src="app.js"></script>', "<script>\n" + js.replace("</script", "<\\/script") + "\n</script>")
    # Der Sprachumschalter verweist absichtlich auf die Schwesterdatei im selben Ordner.
    leftovers = re.findall(r'(?:src|href)="(?!#|data:|https?:|\$\{)[^"]+"', single.replace(values["ui_lang_switch_line"], ""))
    if leftovers:
        raise BuildError(f"Einzeldatei enthält noch lokale Verweise: {leftovers}")
    single_name = name or (project.name + ".html")
    (out / single_name).write_text(single, encoding="utf-8")
    return {"out": str(out), "index": index_name, "single": str(out / single_name), "nodes": len(flow["nodes"]),
            "stages": n_stages, "warnings": warnings, "bytes_single": len(single.encode())}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("project", type=Path, help="Ordner mit flow.json, project.json, Notizbild")
    parser.add_argument("--out", type=Path, help="Zielordner (Standard: <project>/site)")
    parser.add_argument("--name", help="Dateiname der Einzeldatei (Standard: <ordnername>.html)")
    parser.add_argument("--lang", default="de", choices=sorted(UI), help="Sprache der festen Seitentexte (Standard: de)")
    args = parser.parse_args(argv)
    try:
        result = build(args.project, args.out or args.project / "site", args.name, args.lang)
    except BuildError as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1
    for w in result["warnings"]:
        print(f"Warnung: {w}", file=sys.stderr)
    print(f"OK: {result['nodes']} Knoten in {result['stages']} Stufen → {result['out']}/{result['index']}")
    print(f"    Einzeldatei: {result['single']} ({result['bytes_single'] // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
