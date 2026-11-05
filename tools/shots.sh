#!/usr/bin/env bash
# Screenshots einer gebauten Seite mit Chrome headless.
#   tools/shots.sh <html-datei> <ausgabeordner> [knoten-id]
set -euo pipefail
[ $# -ge 2 ] || { echo "Aufruf: tools/shots.sh <html-datei> <ausgabeordner> [knoten-id]" >&2; exit 2; }
F="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"; O="$2"; N="${3:-}"; mkdir -p "$O"
resolve_chrome(){
  local c p
  if [ -n "${CHROME:-}" ]; then
    if [ -x "$CHROME" ] || command -v "$CHROME" >/dev/null 2>&1; then printf '%s\n' "$CHROME"; return 0; fi
    echo "Fehler: CHROME=$CHROME ist nicht ausführbar." >&2; return 1
  fi
  for c in google-chrome google-chrome-stable chromium chromium-browser; do
    if p="$(command -v "$c" 2>/dev/null)"; then printf '%s\n' "$p"; return 0; fi
  done
  for c in "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
           "/Applications/Chromium.app/Contents/MacOS/Chromium" \
           "$HOME/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
           "$HOME/Applications/Chromium.app/Contents/MacOS/Chromium"; do
    if [ -x "$c" ]; then printf '%s\n' "$c"; return 0; fi
  done
  echo "Fehler: Kein Chrome/Chromium gefunden. Bitte CHROME=/pfad/zu/chrome setzen." >&2
  return 1
}
CHROME="$(resolve_chrome)" || exit 2
s(){ "$CHROME" --headless=new --no-sandbox --disable-gpu --hide-scrollbars --virtual-time-budget=4000 \
       --window-size="$1" --screenshot="$O/$2" "file://$F$3" >/dev/null 2>&1; }
s 1440,4200 overview.png ""
s 1440,2400 dark.png "?theme=dark"
s 390,844   mobile.png "${N:+#$N}"
if [ -n "$N" ]; then
  s 1440,4200 panel-fakt.png "#$N"
  s 1440,4200 panel-code.png "#$N/code"
  s 1440,4200 panel-verlauf.png "#$N/verlauf"
fi
echo "Screenshots in $O"
