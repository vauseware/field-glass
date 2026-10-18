#!/bin/bash
# Per-frame draw cost of the real page (tools/bench.js), one line per link. Serves the repo, opens each link in headless
# Chrome with ,bench added, and prints the result the page sends back. Run from the repo root:
#   bash tools/bench.sh 'guilford@14:02,play,warp' '?theme=ww2#guilford@14:02,play,warp'
# DPR=2 prices a HiDPI laptop. Uses desktop Chrome, which draws on the GPU; chrome-headless-shell (BROWSER=...) falls
# back to a software rasteriser and reads several times slower. The gl column says which ran.
set -u
BROWSER=${BROWSER:-"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"}
MODE=(--headless=new); [ "$(basename "$BROWSER")" = chrome-headless-shell ] && MODE=()
WORK=$(mktemp -d "${TMPDIR:-/tmp}/bench.XXXXXX")
PORT=$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])')
python3 -m http.server "$PORT" --bind 127.0.0.1 >"$WORK/server.log" 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null; pkill -f "$WORK/p" 2>/dev/null' EXIT
sleep 0.5
for link in "$@"; do
  case "$link" in \?*) url="http://127.0.0.1:$PORT/index.html$link,bench" ;; *) url="http://127.0.0.1:$PORT/index.html#$link,bench" ;; esac
  before=$(grep -c 'GET /bench?' "$WORK/server.log")
  "$BROWSER" ${MODE[@]+"${MODE[@]}"} --user-data-dir="$WORK/p$RANDOM" --no-first-run --disable-extensions --window-size=1440,900 --force-device-scale-factor="${DPR:-1}" "$url" >"$WORK/browser.log" 2>&1 &
  BR=$!
  for _ in $(seq 1 300); do [ "$(grep -c 'GET /bench?' "$WORK/server.log")" -gt "$before" ] && break; sleep 0.2; done
  kill $BR 2>/dev/null; pkill -f "$WORK/p" 2>/dev/null; sleep 0.5
done
grep -o 'GET /bench?r=[^ ]*' "$WORK/server.log" | python3 -c "
import sys, urllib.parse, json
for l in sys.stdin:
    r = json.loads(urllib.parse.parse_qs(l.split('?', 1)[1])['r'][0])
    print(f\"{r['name']:10} dpr {r['dpr']}  {r['median']:5.2f} ms/frame (range {r['min']}-{r['max']}, lin {r['lin']})  layer {r['build']} ms  {r['page'].split('/', 3)[3]}  [{r['gl'][:40]}]\")"
