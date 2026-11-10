# Field Glass verification map

This folder is the maintained source for verifying what a Field Glass viewer can see and do. Read this index before you drive the page, then use the matching feature file as the recipe. Canonical skill path for Cursor and Claude Code is `.claude/skills/verify-field-glass/` (not `.cursor/skills/`).

## Baseline preconditions

- Run `bash .claude/skills/verify-field-glass/fg.sh up <dir>` with a new `<dir>` in the session scratchpad.
- Require `fg.sh doctor <dir>` to print only `ok` lines, and note the commit it reports.
- Use the battles listed in `battles/index.json` at that commit. The recipes use `cowpens` (Revolution) and `sidi-bou-zid` (Second World War) because both exist today.
- Never drive a server this run did not start.

## Driving conventions

- Drive through `fg.sh drive` journeys (puppeteer-core in chrome-headless-shell) or `fg.sh shot` links.
- Use the handles named in each feature file: element ids, `data-war`, `data-id` and `aria-label`, not coordinates.
- Wait for a state (`waitForFunction` on the hash, `#splash` hidden, `#title` loaded), not a fixed sleep. Use fixed sleeps only to let the clock run.
- Before keyboard input, blur the focused element. After a click, focus stays on that button: the app then ignores the arrow keys, and Space triggers the button's own click.
- A bare or `@time` link opens with the drawer open over the left of the map; `,play` opens with it shut. Legend, Sources and All battles live in the drawer.

## Proof and skip reporting

- Each check prints `PASS` or `FAIL` with the observed before and after values.
- Save a screenshot after each step that changes what the viewer sees, and look at it.
- Record the entry point you used. Do not report a path as verified through a different path.
- Report an unreachable path with the command you ran and the precondition it lacked.

## Feature entry contract

Each feature file starts with an H1 title and one paragraph describing the viewer-visible behavior. It then has exactly four H2 sections in this order: `Sub-features`, `How to get to it (user POV)`, `Driving it with fg.sh`, and `Gotchas`.

## Features

- [Start screen](./start-screen.md) covers the war timeline, each war's card, opening a battle, All battles and Back.
- [Battle playback](./battle-playback.md) covers play and pause, Space, the scrubber, the arrow keys, speed, Follow, Time-lapse, Legend and Sources.
- [Chrome](./chrome.md) covers the docked bar, the ticks and their tip, the caption strip and its pages, the clock cluster, the volume sliders and how much of the map the chrome covers.
- [Opening shot](./opening-shot.md) covers the whole field, the title and the ease in that open a battle from its start, what skips it, reduced motion and the dawn cap.
- [Chapters](./chapters.md) covers the drawer and its chapter list, the Settings panel with Chapter titles and Captions, and the chapter title that fades in over the map.
- [Screenshot links](./screenshot-links.md) covers `#<battle>@<time>,play,select=,warp,title,legend,outcome,opening` links that open a battle at a set moment.
