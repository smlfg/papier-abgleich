#!/usr/bin/env bash
# Vorschau einer reMarkable-Seite (.rm, v6) als PNG, bevor sie aufs Tablet geht.
#   tools/rm-preview.sh <seite.rm> <ausgabe.png>
# rmc -t svg -> viewBox aus rmc (ganze Seite) -> PNG mit Chrome headless.
# Läuft auf macOS (BSD) und Linux (GNU); die SVG-Anpassung macht tools/rm_svg_fit.py.
set -euo pipefail
command -v rmc >/dev/null 2>&1 || { echo "rmc fehlt (python3 -m pip install rmc==0.3.0)" >&2; exit 1; }
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

TOOLS="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
rmc -t svg -o "$TMP/page.svg" "$RM"

# viewBox aus rmc behalten; nur Breite/Hoehe setzen. Kein festes 460x600-Fenster:
# das hat Paper-Pro-Seiten rechts/unten abgeschnitten (Exit 0, Inhalt weg).
HEIGHT="$(python3 -I "$TOOLS/rm_svg_fit.py" "$TMP/page.svg" --width 1404)" || exit 1

mkdir -p "$(dirname "$PNG")"
"$CHROME" --headless=new --no-sandbox --disable-gpu --hide-scrollbars --window-size="1404,$HEIGHT" \
  --default-background-color=ffffffff --screenshot="$TMP/page.png" "file://$TMP/page.svg" >/dev/null 2>&1 || true
[ -s "$TMP/page.png" ] || { echo "Chrome hat kein PNG erzeugt" >&2; exit 1; }
mv "$TMP/page.png" "$PNG"
echo "$PNG: $(wc -c < "$PNG" | tr -d ' ') bytes png"
