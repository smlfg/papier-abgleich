#!/usr/bin/env bash
# Screenshots einer gebauten Seite mit Chrome headless.
#   tools/shots.sh <html-datei> <ausgabeordner> [knoten-id]
set -euo pipefail
F="$(realpath "$1")"; O="$2"; N="${3:-}"; mkdir -p "$O"
CHROME="${CHROME:-$(command -v google-chrome || command -v chromium || command -v chromium-browser)}"
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
