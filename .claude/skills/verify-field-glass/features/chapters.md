# Chapters

The chapter labels slant up from the bar over the map. The Chapters checkbox in the bar hides them and keeps each chapter's tick. When a chapter begins, its name fades in just above the labels (or the bar), holds and fades out, on a soft band of the skin's paper.

## Sub-features

- `ch-switch` is the Chapters checkbox and the `c` key. It starts on for a battle of 15 chapters or fewer and off for more.
- `ch-stored` keeps the viewer's choice in `localStorage` (`fieldglass.chapters`) for every battle and reload; blocked storage falls back to the chapter count.
- `ch-title` fades the chapter's name in over 0.6 s, holds it 2 s and fades it over 1 s, on the page's clock, when play runs into a chapter, a label is clicked or the page opens. A scrubber drag or an arrow key shows none.
- `ch-place` sits the title 14 px above the tallest label showing, the bar, or on a phone the story panel, clear of the top panel and the story panel.
- `ch-opening` shows no title during the opening shot, and the current chapter's title once when it ends or is skipped.

## How to get to it (user POV)

- Click Chapters in the bar, or press `c`. The switch is hidden on a phone, where the labels never show.
- Play a battle, click a chapter label, or open a battle link.

## Driving it with fg.sh

Preconditions:

- The baseline from `README.md` holds.

- **Whole journey.** Run `bash .claude/skills/verify-field-glass/fg.sh drive <dir> .claude/skills/verify-field-glass/journeys/chapters.cjs`. Every line is `PASS`, and `<dir>/chapters-*.png` show the labels on and off, a label click, the title's place at each size, the bar at both laptop sizes and the opening held.
- **Still frame.** Run `fg.sh shot <dir> '#cowpens@07:31,play,warp,title' cowpens-title 1536 830` for the title held at full opacity.
- **Labels off.** Run `fg.sh shot <dir> '#new-orleans@1815-01-08T07:00,play,warp' no-labels 1536 830`. New Orleans has 27 chapters, so it opens with Chapters unchecked and only ticks in the bar.

## Gotchas

- Each journey's browser starts with empty storage, but a `c` press or a click on Chapters stores the choice for every later battle on that origin. Clear `localStorage` between checks that need the default.
- Read the title's opacity with `getComputedStyle`, which follows the CSS animation. Under `,warp` it is `visibility: hidden` unless `,title` holds it.
- A battle of more than 15 chapters opens with its labels off, so a check that needs them presses `c` first.
