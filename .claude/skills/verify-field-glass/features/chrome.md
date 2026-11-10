# Chrome

The pieces round the map: a bar docked to the foot with Play, the scrubber and Settings; a tick a chapter above the groove with a tip naming the chapter under the pointer; the story as a caption strip above the bar, a page at a time; the clock, speed and Time-lapse switch in the top right corner with each skin's dial; three volume sliders in Settings that only store their values. With the drawer closed they cover at most 22% of a 1536 x 830 window.

## Sub-features

- `cr-bar` is 58 px high and full width; the scrubber is at least 1250 px wide at 1536 x 830 and 1000 px at 1280 x 700.
- `cr-ticks` draws one `#marks i` a chapter at the knob's centre for its time (`--f`, `--thumb`); the current one is taller in the accent. Ticks are not controls.
- `cr-tip` shows `#tick-tip` with the nearest chapter's name and time when the pointer is within 12 px of a tick on the scrubber, and hides it when the pointer leaves. A click seeks as before.
- `cr-caption` shows the chapter's time and name on one line and its story in pages of whole sentences, three lines each, turned by the battle clock (`captionPage` in `sim.js`), with a dot a page. A sentence too long for three lines breaks at a semicolon, else the strip grows. The Second World War tape ends its last page STOP.
- `cr-clock` is `#clock-box`, in the right 40% of the window: the skin's dial, the time over its date, `#speed`, and the `#lapse` switch. While time-lapse runs the speed reads `» <lapse>×`.
- `cr-volume` is `#vol-sound`, `#vol-music` and `#vol-narration`, 0 to 100, starting at 60, 40 and 80, kept as `fieldglass.volume` JSON.

## How to get to it (user POV)

- Open any battle and press Play.
- Run the pointer along the scrubber.
- Click Settings and move a slider.

## Driving it with fg.sh

Preconditions:

- The baseline from `README.md` holds.

- **Whole journey.** Run `bash .claude/skills/verify-field-glass/fg.sh drive <dir> .claude/skills/verify-field-glass/journeys/chrome.cjs`. Every line is `PASS`. It measures the scrubber, the bar and the coverage on Antietam at 8 AM, the clock's place at both laptop sizes, hovers ticks on Sidi Bou Zid, New Orleans, Antietam and every tick of the Somme's dense run, pages every chapter of those four at both sizes with the drawer open and closed, and drives the sliders. `<dir>/chrome-4-somme-tip.png` shows the tip where the Somme's chapters bunch.
- **Still frame.** Run `fg.sh shot <dir> '#somme@1916-07-01T07:33,play,warp' somme-strip 1536 830` for the WW1 strip on its second page.

## Gotchas

- The page showing depends on the battle time only, not the speed: scrub back and the earlier page shows.
- The strip is held at its tallest page for the chapter, so a short last page leaves space under it.
- `page.mouse.move` onto a tick needs the tick's centre from `#marks i`'s rect and the scrubber's vertical middle; the tip ignores the pointer anywhere else.
