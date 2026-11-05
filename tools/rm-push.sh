#!/usr/bin/env bash
# Schreibt eine .rm-Seite aufs reMarkable (USB/SSH 10.11.99.1), aber nur auf eine leere Seite.
#   tools/rm-push.sh "<Notizbuch>" <Seitennummer, ab 1> <datei.rm>
# Ablauf: Notizbuch-ID wie rm-pull.sh -> Seiten-ID aus .content -> Leer-Check (keine .rm
# oder <= 500 Bytes) -> Backup nach /home/root/<seiten-id>.rm.bak -> schreiben per cat | ssh
# -> xochitl neu starten -> Status und Byte-Größe zurücklesen.
# Auf dem Tablet läuft BusyBox: nur einfache Befehle (head -n, wc -c <), keine GNU-Flags (#4).
set -euo pipefail
NAME="${1:?Aufruf: rm-push.sh \"<Notizbuch>\" <Seitennummer> <datei.rm>}"
PAGE="${2:?Aufruf: rm-push.sh \"<Notizbuch>\" <Seitennummer> <datei.rm>}"
FILE="${3:?Aufruf: rm-push.sh \"<Notizbuch>\" <Seitennummer> <datei.rm>}"
HOST="${RM_HOST:-root@10.11.99.1}"
XO=/home/root/.local/share/remarkable/xochitl
EMPTY_MAX=500   # leere Seiten: keine .rm oder ~424 Bytes ohne Striche (#5)
SSH=(ssh -o BatchMode=yes -o ConnectTimeout=5 "$HOST")

case "$PAGE" in ''|*[!0-9]*|0) echo "Seitennummer muss eine Zahl ab 1 sein: $PAGE" >&2; exit 1 ;; esac
[ -s "$FILE" ] || { echo "Datei fehlt oder ist leer: $FILE" >&2; exit 1; }
LOCAL=$(wc -c < "$FILE" | tr -d ' ')

ID=$("${SSH[@]}" "cd $XO && grep -l '\"visibleName\": *\"$NAME\"' *.metadata | xargs -r ls -t | head -n 1" | sed 's/\.metadata$//')
[ -n "$ID" ] || { echo "Notizbuch '$NAME' nicht auf dem Tablet gefunden" >&2; exit 1; }

# Seitenreihenfolge bei jedem Aufruf neu lesen (v2 cPages oder altes pages-Array), wie rm-pull.sh
PID=$("${SSH[@]}" "cat $XO/$ID.content" | python3 -I -c '
import json, re, sys
c = json.load(sys.stdin); n = int(sys.argv[1])
if "cPages" in c:
    pages = [p["id"] for p in c["cPages"]["pages"] if not p.get("deleted")]
else:
    pages = c.get("pages", [])
if n > len(pages):
    sys.exit(f"Seite {n} gibt es nicht, das Notizbuch hat {len(pages)} Seiten")
pid = pages[n - 1]
if not re.fullmatch(r"[0-9A-Za-z-]+", pid):
    sys.exit(f"unerwartete Seiten-ID: {pid!r}")
print(pid)' "$PAGE")
DST="$XO/$ID/$PID.rm"
echo "Notizbuch $ID, Seite $PAGE = $PID"

# Leer-Check: nie eine Seite mit Strichen überschreiben
REMOTE=$("${SSH[@]}" "if [ -f $DST ]; then wc -c < $DST; else echo none; fi" | tr -d ' ')
if [ "$REMOTE" = none ]; then
  echo "Zielseite hat keine .rm (leer)"
elif [ "$REMOTE" -le "$EMPTY_MAX" ]; then
  echo "Zielseite hat $REMOTE Bytes (leer, <= $EMPTY_MAX)"
  "${SSH[@]}" "cp $DST /home/root/$PID.rm.bak"
  echo "Backup: /home/root/$PID.rm.bak"
else
  echo "Abbruch: Zielseite hat $REMOTE Bytes (> $EMPTY_MAX), dort sind schon Striche. Bitte eine leere Seite anlegen." >&2
  exit 2
fi

"${SSH[@]}" "mkdir -p $XO/$ID && cat > $DST" < "$FILE"
echo "Geschrieben: $LOCAL Bytes"

echo "Achtung: xochitl startet neu, die Tablet-Oberfläche lädt etwa 10 s neu."
"${SSH[@]}" "systemctl restart xochitl"

STATE=$("${SSH[@]}" "systemctl is-active xochitl" || true)
AFTER=$("${SSH[@]}" "wc -c < $DST" | tr -d ' ')
echo "xochitl: $STATE"
echo "Tablet: $AFTER Bytes, lokal: $LOCAL Bytes"
[ "$AFTER" = "$LOCAL" ] || { echo "Fehler: Größe weicht ab" >&2; exit 1; }
[ "$STATE" = active ] || { echo "Fehler: xochitl läuft nicht" >&2; exit 1; }
