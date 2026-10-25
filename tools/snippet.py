#!/usr/bin/env python3
"""Code-Ausschnitt wörtlich aus einem Commit holen und als flow.json-Snippet ausgeben.

    python3 tools/snippet.py <repo> <sha> <pfad> <start> <end> [--github owner/name]

Der Code kommt immer aus `git show <sha>:<pfad>`, nie aus dem Arbeitsverzeichnis.
Mit --github wird ein Permalink gebaut; nur verwenden, wenn der Commit gepusht ist
(sonst bleibt url null und die Seite zeigt "nur lokal").
"""
import argparse, json, subprocess, sys

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo"); ap.add_argument("sha"); ap.add_argument("path")
    ap.add_argument("start", type=int); ap.add_argument("end", type=int)
    ap.add_argument("--github", metavar="OWNER/NAME")
    a = ap.parse_args()
    if a.start < 1 or a.end < a.start:
        sys.exit("start/end ungültig")
    full = subprocess.check_output(["git", "-C", a.repo, "rev-parse", a.sha], text=True).strip()
    lines = subprocess.check_output(["git", "-C", a.repo, "show", f"{full}:{a.path}"], text=True).split("\n")
    if a.end > len(lines):
        sys.exit(f"{a.path} hat nur {len(lines)} Zeilen")
    if a.github:
        pushed = subprocess.run(["git", "-C", a.repo, "branch", "-r", "--contains", full],
                                capture_output=True, text=True).stdout.strip()
        if not pushed:
            print(f"Warnung: {full[:7]} ist auf keinem Remote-Branch, url bleibt null", file=sys.stderr)
    url = (f"https://github.com/{a.github}/blob/{full}/{a.path}#L{a.start}-L{a.end}"
           if a.github and pushed else None)
    print(json.dumps({"file": a.path, "start": a.start, "end": a.end,
                      "code": "\n".join(lines[a.start - 1:a.end]), "url": url},
                     ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
