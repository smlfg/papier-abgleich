#!/usr/bin/env bash
# Vorschau einer reMarkable-Seite (.rm, v6) als PNG, bevor sie aufs Tablet geht.
#   tools/rm-preview.sh <seite.rm> <ausgabe.png>
# rmc -t svg -> viewBox auf -230 0 460 600 (ganze Seite, Mitte = 0) -> PNG mit Chrome headless.
# Läuft auf macOS (BSD) und Linux (GNU): kein sed -i, das SVG wird mit python3 umgeschrieben.
set -euo pipefail
RM="${1:?Aufruf: rm-preview.sh <seite.rm> <ausgabe.png>}"
PNG="${2:?Aufruf: rm-preview.sh <seite.rm> <ausgabe.png>}"
[ -f "$RM" ] || { echo "Datei fehlt: $RM" >&2; exit 1; }

# Chrome suchen: CHROME=, dann Linux-Namen, dann macOS-App (siehe Issue #1)
find_chrome() {
  [ -n "${CHROME:-}" ] && { echo "$CHROME"; return; }
  for c in google-chrome chromium chromium-browser; do
    command -v "$c" >/dev/null 2>&1 && { command -v "$c"; return; }
  done
  for c in "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
           "/Applications/Chromium.app/Contents/MacOS/Chromium"; do
    [ -x "$c" ] && { echo "$c"; return; }
  done
}
CHROME="$(find_chrome)"
[ -n "$CHROME" ] || { echo "Chrome nicht gefunden. CHROME=/pfad/zu/chrome setzen." >&2; exit 1; }

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
rmc -t svg -o "$TMP/page.svg" "$RM"

python3 -I - "$TMP/page.svg" <<'PY'
import re, sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
m = re.search(r"<svg\b[^>]*>", s)
if not m:
    sys.exit("kein <svg>-Kopf in der rmc-Ausgabe")
head = re.sub(r'\s(?:width|height|viewBox)="[^"]*"', "", m.group(0))
head = head.replace("<svg", '<svg width="1404" height="1831" viewBox="-230 0 460 600"', 1)
open(p, "w", encoding="utf-8").write(s[:m.start()] + head + s[m.end():])
PY

mkdir -p "$(dirname "$PNG")"
"$CHROME" --headless=new --no-sandbox --disable-gpu --hide-scrollbars --window-size=1404,1831 \
  --default-background-color=ffffffff --screenshot="$TMP/page.png" "file://$TMP/page.svg" >/dev/null 2>&1 || true
[ -s "$TMP/page.png" ] || { echo "Chrome hat kein PNG erzeugt" >&2; exit 1; }
mv "$TMP/page.png" "$PNG"
echo "$PNG: $(wc -c < "$PNG" | tr -d ' ') bytes png"
