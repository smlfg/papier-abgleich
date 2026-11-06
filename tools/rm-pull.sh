#!/usr/bin/env bash
# rm-pull.sh "<notebook name>" [outdir]
# Pulls one notebook live from the reMarkable over SSH (alias `remarkable`,
# override with RM_HOST) and renders every page to SVG + PNG for the agent.
set -euo pipefail
command -v rmc >/dev/null 2>&1 || { echo "rmc fehlt (python3 -m pip install rmc==0.3.0)" >&2; exit 1; }
NAME="${1:?usage: rm-pull.sh \"<notebook name>\" [outdir]}"
OUT="${2:-$PWD/papier-pulls/$(echo "$NAME" | tr ' /' '__')}"
HOST="${RM_HOST:-remarkable}"
XO=/home/root/.local/share/remarkable/xochitl
CHROME="${CHROME:-$(command -v google-chrome || command -v chromium || command -v chromium-browser || echo "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")}"
[ -x "$CHROME" ] || command -v "$CHROME" >/dev/null 2>&1 || { echo "Chrome nicht gefunden. CHROME=/pfad/zu/chrome setzen." >&2; exit 1; }
SSH=(ssh -o BatchMode=yes -o ConnectTimeout=5 "$HOST")
"${SSH[@]}" true >/dev/null 2>&1 || { echo "Tablet nicht erreichbar: $HOST (RM_HOST setzen)" >&2; exit 1; }
TOOLS="$(cd "$(dirname "$0")" && pwd)"

ID=$("${SSH[@]}" "cd $XO && grep -l '\"visibleName\": *\"$NAME\"' *.metadata | xargs -r ls -t | head -n 1" | sed 's/\.metadata$//')
[ -n "$ID" ] || { echo "Notebook '$NAME' not found on tablet" >&2; exit 1; }

mkdir -p "$OUT/raw"
rm -f "$OUT"/page-*.svg "$OUT"/page-*.png
"${SSH[@]}" "cd $XO && tar cf - $ID.content $ID.metadata $ID" | tar xf - -C "$OUT/raw"

# Page order from .content (v2 cPages or legacy pages array)
python3 -I - "$OUT/raw/$ID.content" > "$OUT/raw/order.txt" <<'PY'
import json, sys
c = json.load(open(sys.argv[1]))
if "cPages" in c:
    for p in c["cPages"]["pages"]:
        if not p.get("deleted"):
            print(p["id"])
else:
    print("\n".join(c.get("pages", [])))
PY

i=0
while read -r PID; do
  i=$((i+1)); RM="$OUT/raw/$ID/$PID.rm"; N=$(printf "%02d" $i)
  [ -f "$RM" ] || { echo "page $N: empty (no strokes)"; continue; }
  rmc -t svg -o "$OUT/page-$N.svg" "$RM" 2>/dev/null || { echo "page $N: rmc failed"; continue; }
  # rmc's viewBox clips strokes left of the page origin: pad it and scale to window width
  HEIGHT="$(python3 -I "$TOOLS/rm_svg_fit.py" "$OUT/page-$N.svg" --width 1404 --pad-x 0.5)" \
    || { echo "page $N: SVG-Fit failed"; continue; }
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --window-size="1404,$HEIGHT" \
    --default-background-color=ffffffff --screenshot="$OUT/page-$N.png" "file://$(cd "$OUT" && pwd)/page-$N.svg" >/dev/null 2>&1 \
    || { echo "page $N: Chrome failed"; continue; }
  echo "page $N: $(wc -c < "$OUT/page-$N.png") bytes png"
done < "$OUT/raw/order.txt"
echo "OUT=$OUT  ID=$ID  pages=$i"
