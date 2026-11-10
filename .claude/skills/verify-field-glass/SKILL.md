---
name: verify-field-glass
description: Drive the real Field Glass web page in headless Chrome on this Mac mini and capture proof. Poteto Feature/Bug-fix step "verify on the matching surface" means this skill (fg.sh), not IDE browser tools. Use before claiming a UI or battle change works, for PR screenshots, or when a change touches app.js, splash.js, index.html, themes/ or a battle's data.
---

# Verify Field Glass

## Under poteto

When `/poteto-mode` reaches "Verify on the matching surface" for Field Glass UI, run **this skill** (`fg.sh` journeys and shots). That is poteto's **Prove It Works** on the real page. Do not substitute Cursor IDE browser, computer-use, or Claude for Chrome. For the ADR-0009 opening-landing property (not a journey), also run **formal-verify-opening-landing** (`node tools/formal/opening-landing.mjs`).

## Contract

Field Glass is a static web page: `index.html` loads `app.js`, `splash.js` and the skins in `themes/`, and fetches `battles/index.json` plus each battle's `battle.json` and `terrain.json`. There is no backend, database or login. The only surface is the browser page, drawn on a canvas with HTML panels over it.

All commands below run from the repo root. The harness is `.claude/skills/verify-field-glass/fg.sh`; call it with `bash`. Every command takes a run folder `<dir>`: make it a new folder in your session scratchpad, one per run. It holds the server's pid, port and log, and all evidence.

This machine is headless. Never use `file://` (blocked), interactive browser tools (Claude for Chrome, Cursor IDE browser, computer-use — they need a display or drive the wrong surface), or bare `node` (use `fg.sh drive`, which runs node through `npx`). `fg.sh` is the only allowed driver.

## Launch

```bash
F=.claude/skills/verify-field-glass
bash $F/fg.sh up <dir>          # serves the working tree; prints http://127.0.0.1:<port>/
bash $F/fg.sh up <dir> dist     # runs tools/build.sh and serves dist/, exactly what `npm run deploy` uploads
```

`up` picks a free port, starts `python3 -m http.server` bound to 127.0.0.1, and returns once `battles/index.json` answers. It is ready when it prints the URL. Running `up` twice on the same `<dir>` reuses the running server. Separate `<dir>`s give separate servers, so two runs never share an instance. Do not use `npm run serve`: it takes the fixed port 8000, which may belong to someone else.

## Doctor

```bash
bash $F/fg.sh doctor <dir>
```

Read-only. Exits non-zero unless every line says `ok`: the pid in `<dir>` is our `http.server` on our port, the page and `battles/index.json` answer, `splash.js` is served, and `chrome-headless-shell` exists. It also prints the commit being served and whether the working tree has uncommitted edits. Run it first, and again whenever a journey fails strangely.

## Drive

Journeys are puppeteer-core scripts in `journeys/`. Each prints one `PASS` or `FAIL` line per check and saves screenshots into `<dir>`.

```bash
bash $F/fg.sh drive <dir> $F/journeys/start-screen.cjs           # the war timeline, opening a battle, All battles, Back
bash $F/fg.sh drive <dir> $F/journeys/playback.cjs [battle id]   # play, pause, Space, scrubber, arrow keys, speed, f and t, Legend, Sources
bash $F/fg.sh drive <dir> $F/journeys/laptop.cjs [ids]           # the target laptop: 1536x830 at DPR 1.25 and 1280x700 at 1.5, one battle per skin, drawer open, closed and Settings open; no scroll, nothing covered, 16 px text, 44 px targets, sharp canvas
bash $F/fg.sh drive <dir> $F/journeys/chrome.cjs                   # the bar and scrubber, coverage, the clock's place, ticks and their tip, every caption page, the volume sliders
bash $F/fg.sh drive <dir> $F/journeys/stacking.cjs                 # the unit hover tip and card stay on top of the caption strip and the tick tip
bash $F/fg.sh drive <dir> $F/journeys/opening.cjs [ids] [clip]     # the opening shot: beats, what starts and skips it, reduced motion, dawn cap; field, title and landing shots
bash $F/fg.sh drive <dir> $F/journeys/chapters.cjs                 # the drawer and chapter list, Settings, Chapter titles and Captions kept; the chapter title: what shows it, its place, the opening, reduced motion
```

`drive` writes the output to `<dir>/<journey>.log` and exits 1 if any line starts with `FAIL`. To prove something new, copy the closest journey, keep its `ok()` and `shot()` helpers, and drive the page the way a user would: click the real buttons and type real keys. Handles worth using are `#splash`, `.tl-war[data-war=<war id>]`, `.row[data-id=<battle id>]`, `#play` (its `aria-label` is `Play` or `Pause`), `#speed`, `#scrub`, `#clock`, `#cap-title`, `#home` (All battles), `#legend-btn` with `#legend-dlg`, `#src-btn` with `#sources` (both in the drawer: `#chapters-btn` opens it, `#top-close` closes it), `#chapter-list`, `#settings-btn` with `#settings`, `#follow`, `#lapse`, `#titles`, `#captions`, `#tick-tip` and `#chapter-title`. The feature files name more.

For a still frame of a moment in a battle, use a screenshot link (see `features/screenshot-links.md`):

```bash
bash $F/fg.sh shot <dir> '#cowpens@07:30,play,warp' cowpens-0730 [width=1440] [height=900]
```

## Evidence

Everything goes in `<dir>`: the journey logs, `start-screen-*.png`, `playback-<battle>-*.png`, `shot` PNGs, and `server.log`. A proof must:

- drive the user's path (clicks, keys, links), not call app functions from `page.evaluate`. Reading state with `evaluate` is fine.
- capture the action and the state it led to: a screenshot after each step that matters, and a `PASS` line that names the before and after values.
- for a battle data change, show the moment it affects, with a `shot` link at that time, and run `npm run check`, which validates every battle and rewrites the running times in `battles/index.json`.
- look at the screenshots. A `PASS` from a blank canvas is not proof.

To show the user, put the PNG paths in chat (Cursor: attach or Read the files; Claude Code: SendUserFile). For a PR, use `bash ~/bin/pr-shot.sh <pr#> <png>...` with desktop shots only: phones are out of scope (ADR-0012).

## Cleanup

```bash
bash $F/fg.sh down <dir>
```

Stops only the server whose pid is in `<dir>`, and only if it is still our `http.server` on our port. The browser in each journey closes itself; `shot.sh` cleans up its own. `<dir>` and its evidence stay. `up <dir> dist` leaves `dist/` behind; it is gitignored and the next build replaces it.

## Feature map

`features/README.md` indexes the user-facing features with their entry points and proof. Read it before driving, and keep it current with `/maintain-verification-skill` (Claude Code: `/pstack:maintain-verification-skill`) when the page changes. This skill lives at `.claude/skills/verify-field-glass/` for both Cursor and Claude Code; pstack's maintain step that looks under `.cursor/skills/verify-*` should accept this path too.
