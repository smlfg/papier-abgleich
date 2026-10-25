#!/usr/bin/env python3
"""Rendert eine gebaute Seite headless (Chrome) und meldet Knoten, Pfeile, Stufen, JS-Fehler und 'undefined'.

Aufruf: python3 tools/verify.py <html> [#hash] [--text]
  --text  gibt zusätzlich den sichtbaren Text aus (für Diffs zweier Builds)
"""
import html, json, os, re, subprocess, sys, tempfile
from pathlib import Path

PROBE = """<script>window.__errs=[];window.addEventListener('error',e=>window.__errs.push(String(e.message)));
setTimeout(()=>{const r={nodes:document.querySelectorAll('.node').length,arrows:document.querySelectorAll('#arrows path').length,
lanes:document.querySelectorAll('.lane-band').length,undefined:document.body.innerText.includes('undefined'),errors:window.__errs};
const p=document.createElement('pre');p.id='__probe';p.textContent=JSON.stringify(r);document.body.appendChild(p);},1500)</script>"""

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    src = Path(args[0]).resolve(); h = args[1] if len(args) > 1 else ""
    page = src.read_text(encoding="utf-8")
    page = page.replace("<head>", "<head>" + PROBE.split("setTimeout")[0] + "</script>", 1).replace(
        "</body>", "<script>setTimeout" + PROBE.split("setTimeout", 1)[1] + "</body>", 1)
    with tempfile.NamedTemporaryFile("w", suffix=".html", dir=src.parent, delete=False, encoding="utf-8") as t:
        t.write(page)
    try:
        dom = subprocess.run([os.environ.get("CHROME", "google-chrome"), "--headless=new", "--no-sandbox", "--disable-gpu",
                              "--virtual-time-budget=4000", "--dump-dom", f"file://{t.name}{h}"],
                             capture_output=True, text=True, timeout=60).stdout
    finally:
        os.unlink(t.name)
    m = re.search(r'<pre id="__probe">(.*?)</pre>', dom, re.S)
    result = json.loads(html.unescape(m.group(1))) if m else {"error": "keine Probe im DOM"}
    print(json.dumps(result, ensure_ascii=False))
    if "--text" in sys.argv:
        body = re.sub(r"<script.*?</script>|<pre id=\"__probe\">.*?</pre>", "", dom, flags=re.S)
        body = html.unescape(re.sub(r"<[^>]+>", "\n", body))
        print("\n".join(l.strip() for l in body.splitlines() if l.strip()))
    ok = m and not result["errors"] and not result["undefined"] and result["nodes"] > 0
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
