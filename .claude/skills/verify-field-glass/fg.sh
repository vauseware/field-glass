#!/bin/bash
# Field Glass verification harness: serve the page on a private port, check it, drive it in headless Chrome, stop it.
#   bash fg.sh up <dir> [src|dist]      serve the repo (src, default) or a fresh tools/build.sh output (dist); prints the URL
#   bash fg.sh doctor <dir>             read-only: is the instance in <dir> ours, up, and serving this checkout?
#   bash fg.sh drive <dir> <journey.cjs> [args...]   run a puppeteer journey; output to <dir>/<journey>.log; exit 1 on any FAIL
#   bash fg.sh shot <dir> '<path#hash>' <name> [w] [h]   screenshot via ~/bin/shot.sh to <dir>/<name>.png
#   bash fg.sh down <dir>               stop the server this run started; <dir> and its evidence stay
# <dir> is the run's own folder (use the session scratchpad). It holds server.pid, port, server.log and all evidence.
set -euo pipefail
REPO=$(cd "$(dirname "$0")/../../.." && pwd)
cmd=${1:?usage: fg.sh up|doctor|drive|shot|down <dir> ...}; DIR=${2:?run dir required}
HS=$(/bin/ls -d "$HOME"/.cache/puppeteer/chrome-headless-shell/*/*/chrome-headless-shell 2>/dev/null | sort -V | tail -1 || true)
get() { python3 -c "import sys,urllib.request; r=urllib.request.urlopen(sys.argv[1], timeout=10); sys.stdout.write(r.read().decode())" "$1"; }
ours() { # the pid in <dir> is alive and is the http.server on our port
  [ -f "$DIR/server.pid" ] && ps -p "$(cat "$DIR/server.pid")" -o command= 2>/dev/null | grep -q "http.server $(cat "$DIR/port")"
}

case "$cmd" in
up)
  mode=${3:-src}; mkdir -p "$DIR"
  ours && { echo "already up: http://127.0.0.1:$(cat "$DIR/port")/"; exit 0; }
  root=$REPO
  if [ "$mode" = dist ]; then (cd "$REPO" && bash tools/build.sh); root=$REPO/dist; fi
  port=$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])')
  python3 -m http.server "$port" --bind 127.0.0.1 --directory "$root" </dev/null >"$DIR/server.log" 2>&1 &
  echo $! >"$DIR/server.pid"; echo "$port" >"$DIR/port"; echo "$mode" >"$DIR/mode"
  for _ in $(seq 50); do get "http://127.0.0.1:$port/battles/index.json" >/dev/null 2>&1 && break; sleep 0.1; done
  get "http://127.0.0.1:$port/battles/index.json" >/dev/null || { echo "fg: server did not answer on $port" >&2; exit 1; }
  echo "http://127.0.0.1:$port/" ;;
doctor)
  base="http://127.0.0.1:$(cat "$DIR/port" 2>/dev/null)/"; bad=0
  chk() { if eval "$2" >/dev/null 2>&1; then echo "ok   $1"; else echo "FAIL $1"; bad=1; fi; }
  chk "server pid $(cat "$DIR/server.pid" 2>/dev/null) is our http.server" ours
  chk "page answers at $base" "get '$base' | grep -q '<section id=\"splash\"'"
  chk "battles/index.json lists battles" "get '${base}battles/index.json' | python3 -c 'import json,sys; assert len(json.load(sys.stdin)) > 0'"
  chk "splash.js served" "get '${base}splash.js' | grep -q 'export const WARS'"
  chk "served from $(cat "$DIR/mode" 2>/dev/null) of $(git -C "$REPO" rev-parse --short HEAD)$(git -C "$REPO" diff --quiet || echo ' + uncommitted edits')" true
  chk "chrome-headless-shell present" "[ -x '$HS' ]"
  exit $bad ;;
drive)
  js=${3:?journey.cjs required}; shift 3
  case "$js" in /*) ;; *) js=$(cd "$(dirname "$js")" && pwd)/$(basename "$js") ;; esac
  log="$DIR/$(basename "$js" .cjs).log"
  # NODE_PATH lets the journey require the puppeteer-core that npx installed (~/.claude/CLAUDE.md: never bare node)
  npx -y -p puppeteer-core@23.11.1 -c "NODE_PATH=\${PATH%%/.bin:*} node '$js' '$HS' 'http://127.0.0.1:$(cat "$DIR/port")/' '$DIR' $*" 2>&1 | tee "$log"
  ! grep -q '^FAIL' "$log" ;;
shot)
  path=${3:?path required}; name=${4:?name required}
  bash ~/bin/shot.sh "http://127.0.0.1:$(cat "$DIR/port")/${path#/}" "$DIR/$name.png" "${5:-1440}" "${6:-900}" ;;
down)
  if ours; then kill "$(cat "$DIR/server.pid")"; echo "stopped server $(cat "$DIR/server.pid")"; else echo "no server of ours running"; fi ;;
*) echo "fg.sh: unknown command $cmd" >&2; exit 2 ;;
esac
