#!/usr/bin/env bash
# rm-pull.sh "<notebook name>" [outdir]
# Pulls one notebook live from the reMarkable over USB (SSH 10.11.99.1)
# and renders every page to SVG + PNG for the agent to read.
set -euo pipefail
NAME="${1:?usage: rm-pull.sh \"<notebook name>\" [outdir]}"
OUT="${2:-$PWD/papier-pulls/$(echo "$NAME" | tr ' /' '__')}"
HOST="${RM_HOST:-root@10.11.99.1}"
XO=/home/root/.local/share/remarkable/xochitl
CHROME="${CHROME:-$(command -v google-chrome || command -v chromium || command -v chromium-browser || echo "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")}"
SSH=(ssh -o BatchMode=yes -o ConnectTimeout=5 "$HOST")

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
  python3 -I - "$OUT/page-$N.svg" <<'PY'
import re, sys
p = sys.argv[1]; s = open(p).read()
m = re.search(r'viewBox="([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+)"', s)
x, y, w, h = map(float, m.groups()); pad = w * 0.5
vb = f'viewBox="{x-pad} {y} {w+2*pad} {h}"'
s = re.sub(r'<svg ([^>]*?)height="[^"]*" width="[^"]*" viewBox="[^"]*"', rf'<svg \1width="1404" {vb}', s, count=1)
open(p, "w").write(s)
PY
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --window-size=1404,1872 \
    --default-background-color=ffffffff --screenshot="$OUT/page-$N.png" "file://$(cd "$OUT" && pwd)/page-$N.svg" >/dev/null 2>&1
  echo "page $N: $(wc -c < "$OUT/page-$N.png") bytes png"
done < "$OUT/raw/order.txt"
echo "OUT=$OUT  ID=$ID  pages=$i"
