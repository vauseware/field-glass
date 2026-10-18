# Battle playback

A battle opens paused at its first moment with its map, the top panel (title, sides, outcome, All battles, Legend, Sources) and the story caption. The bar at the foot plays and pauses, sets the speed, scrubs time across chapter marks, and toggles Follow the action and Time-lapse. The clock and the caption follow the battle's time.

## Sub-features

- `pb-play` starts and pauses the clock with the Play button or Space.
- `pb-scrub` seeks with the scrubber; the caption changes to that moment's chapter.
- `pb-step` steps forward and back with the arrow keys.
- `pb-speed` sets the speed from the Speed menu.
- `pb-toggles` turns Follow the action (`f`) and Time-lapse (`t`) on and off.
- `pb-legend` opens the Legend dialog with the skin's key.
- `pb-sources` opens the Sources dialog listing the battle's sources.

## How to get to it (user POV)

- Choose a battle on the start screen.
- Open a battle link such as `#cowpens`.
- Use the bar at the foot, the top panel's buttons, or the keys Space, ←, →, `f` and `t`.

## Driving it with fg.sh

Preconditions:

- The baseline from `README.md` holds.

- **Whole journey.** Run `bash .claude/skills/verify-field-glass/fg.sh drive <dir> .claude/skills/verify-field-glass/journeys/playback.cjs cowpens`. Every line is `PASS`, and `<dir>/playback-cowpens-*.png` show the opening, the midway seek, the Legend and the Sources.
- **Opens paused.** Load `#cowpens`. `#play` has `aria-label="Play"`, and `#scrub` is at its `min`.
- **Play and pause.** Click `#play` and wait 3 s. The label is `Pause` and `#scrub`'s value has grown. Click again, and the value holds still.
- **Space.** Blur the focused element, then press Space. Play toggles, and the value grows while playing.
- **Scrub.** Set `#scrub` halfway and fire `input`. `#clock` and `#cap-title` change to the chapter at that time.
- **Arrow keys.** Blur, then press ArrowRight. `#scrub` moves forward by at least 30 s.
- **Speed.** Choose the last option in `#speed`. Its value is that option. The options are `1, 2, 5, 10, 20, 30, 60, 120`.
- **Legend.** Click `#legend-btn`. `#legend-dlg` is open and `#legend-list` has entries. Press Escape to close it.
- **Sources.** Click `#src-btn`. `#sources` is open and `#src-list` has entries.

## Gotchas

- `#clock` shows minutes only, so a few seconds of play may not change it. Compare `#scrub`'s value in seconds.
- After clicking a button, the arrow keys do nothing until focus leaves the button. Space then clicks the button itself rather than going through the app's key handler. Blur first, or a passing check proves the wrong path.
- The canvas animates with requestAnimationFrame, which runs in puppeteer but not under `shot.sh`'s virtual time. Use a `warp` link for still frames (see `screenshot-links.md`).
- A battle defaults to a speed above 1×, so a short wait can cover a minute or more of battle time.
