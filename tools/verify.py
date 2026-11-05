#!/usr/bin/env python3
"""Rendert eine gebaute Seite headless (Chrome) und meldet Knoten, Pfeile, Stufen, JS-Fehler und 'undefined'.

Aufruf: python3 tools/verify.py <html> [#hash] [--text] [--chrome PFAD]
  --text         gibt zusätzlich den sichtbaren Text aus (für Diffs zweier Builds)
  --chrome PFAD  Browser-Binary; sonst $CHROME, PATH, macOS-Bundle oder Windows-Pfad
"""
import html, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

PROBE = """<script>window.__errs=[];window.addEventListener('error',e=>window.__errs.push(String(e.message)));
setTimeout(()=>{const r={nodes:document.querySelectorAll('.node').length,arrows:document.querySelectorAll('#arrows path').length,
lanes:document.querySelectorAll('.lane-band').length,undefined:document.body.innerText.includes('undefined'),errors:window.__errs};
const p=document.createElement('pre');p.id='__probe';p.textContent=JSON.stringify(r);document.body.appendChild(p);},1500)</script>"""

CHROME_NAMES = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge")
MAC_APPS = ("Google Chrome.app/Contents/MacOS/Google Chrome",
            "Chromium.app/Contents/MacOS/Chromium",
            "Microsoft Edge.app/Contents/MacOS/Microsoft Edge")
WIN_APPS = ("Google/Chrome/Application/chrome.exe",
            "Chromium/Application/chrome.exe",
            "Microsoft/Edge/Application/msedge.exe")


def find_chrome(explicit=None, env=None, which=None, exists=None):
    """Findet Chrome/Chromium: explizit, $CHROME, PATH, macOS-Bundles, Windows-Pfade."""
    env = os.environ if env is None else env
    which = shutil.which if which is None else which
    exists = os.path.exists if exists is None else exists

    for cand in (explicit, env.get("CHROME")):
        if cand:
            return cand
    for name in CHROME_NAMES:
        path = which(name)
        if path:
            return path
    home = env.get("HOME") or os.path.expanduser("~")
    for root in ("/Applications", os.path.join(home, "Applications")):
        for app in MAC_APPS:
            path = os.path.join(root, app)
            if exists(path):
                return path
    for base in (env.get("PROGRAMFILES"), env.get("PROGRAMFILES(X86)"), env.get("LOCALAPPDATA")):
        if not base:
            continue
        for app in WIN_APPS:
            path = os.path.join(base, *app.split("/"))
            if exists(path):
                return path
    return None


def parse_args(argv):
    """Liest <html> [#hash] [--text] [--chrome PFAD]; gibt (html, hash, text, chrome)."""
    explicit, text, rest = None, False, []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--text":
            text = True
        elif arg == "--chrome":
            if i + 1 >= len(argv):
                sys.exit("Fehler: --chrome braucht einen Pfad")
            i += 1
            explicit = argv[i]
        elif arg.startswith("--chrome="):
            explicit = arg.split("=", 1)[1]
        elif not arg.startswith("--"):
            rest.append(arg)
        i += 1
    if not rest:
        sys.exit("Aufruf: python3 tools/verify.py <html> [#hash] [--text] [--chrome PFAD]")
    return rest[0], rest[1] if len(rest) > 1 else "", text, explicit


def main():
    src_arg, h, show_text, explicit = parse_args(sys.argv[1:])
    src = Path(src_arg).resolve()
    chrome = find_chrome(explicit=explicit)
    if not chrome:
        print("Fehler: Kein Chrome/Chromium gefunden. Bitte --chrome PFAD angeben oder CHROME setzen\n"
              "  (macOS: /Applications/Google Chrome.app/Contents/MacOS/Google Chrome, Linux: google-chrome).",
              file=sys.stderr)
        sys.exit(2)
    page = src.read_text(encoding="utf-8")
    page = page.replace("<head>", "<head>" + PROBE.split("setTimeout")[0] + "</script>", 1).replace(
        "</body>", "<script>setTimeout" + PROBE.split("setTimeout", 1)[1] + "</body>", 1)
    with tempfile.NamedTemporaryFile("w", suffix=".html", dir=src.parent, delete=False, encoding="utf-8") as t:
        t.write(page)
    try:
        dom = subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu",
                              "--virtual-time-budget=4000", "--dump-dom", f"file://{t.name}{h}"],
                             capture_output=True, text=True, timeout=60).stdout
    except OSError as e:
        print(f"Fehler: {chrome} konnte nicht gestartet werden: {e}", file=sys.stderr)
        sys.exit(2)
    finally:
        os.unlink(t.name)
    m = re.search(r'<pre id="__probe">(.*?)</pre>', dom, re.S)
    result = json.loads(html.unescape(m.group(1))) if m else {"error": "keine Probe im DOM"}
    print(json.dumps(result, ensure_ascii=False))
    if show_text:
        body = re.sub(r"<script.*?</script>|<pre id=\"__probe\">.*?</pre>", "", dom, flags=re.S)
        body = html.unescape(re.sub(r"<[^>]+>", "\n", body))
        print("\n".join(l.strip() for l in body.splitlines() if l.strip()))
    ok = m and not result["errors"] and not result["undefined"] and result["nodes"] > 0
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
