# Chapters

The battle's title sits in a chip at the top left. Its **Chapters** button opens a drawer down the left edge with the details and a list of the chapters, the current one open to its whole story. **Settings** on the bar opens a panel with Follow the action, Chapter titles and Captions. When a chapter begins, its name fades in just above the caption strip (or the bar), holds and fades out, on a soft band of the skin's paper.

## Sub-features

- `ch-drawer` opens from Chapters on the chip; Close, Esc and Play (when play starts) close it. A bare or `@time` link opens with it open, `,play` with it shut, `,outcome` opens it and Outcome.
- `ch-list` is one row a chapter, 44 px high, the time of day as the skin writes it and the name, under day headings for a battle of more than one day. A click seeks to the chapter's start and turns Follow on; the drawer stays open. The current row (`.on`) opens to its story and scrolls into the list's view; the heading reads "Chapters 9 of 24".
- `ch-settings` opens over the Settings button; the button, Esc or a click outside closes it. Esc closes one layer a press: Settings, then the drawer, then the unit card.
- `ch-titles` is the Chapter titles switch and key `c`; `ch-captions` the Captions switch, which hides the strip. Both start on and are kept in `localStorage` (`fieldglass.titles`, `fieldglass.captions`, `on` or `off`); blocked storage leaves them on.
- `ch-title` fades the chapter's name in over 0.6 s, holds it 2 s and fades it over 1 s, on the page's clock, when play runs into a chapter, a row is clicked or the page opens. A scrubber drag or an arrow key shows none.
- `ch-place` sits the title 14 px above the caption strip, or the bar with Captions off, clear of every panel, and centred right of the open drawer.
- `ch-opening` shows no title during the opening shot, and the current chapter's title once when it ends or is skipped.

## How to get to it (user POV)

- Click Chapters on the chip, then a row. Press Esc or Close.
- Click Settings on the bar, then a switch. Press `c`.
- Play a battle, or open a battle link.

## Driving it with fg.sh

Preconditions:

- The baseline from `README.md` holds.

- **Whole journey.** Run `bash .claude/skills/verify-field-glass/fg.sh drive <dir> .claude/skills/verify-field-glass/journeys/chapters.cjs`. Every line is `PASS`, and `<dir>/chapters-*.png` show a row click, the drawer and Settings closed, Captions off, the title's place at each size with the drawer open and closed, and the opening held.
- **Still frame.** Run `fg.sh shot <dir> '#cowpens@07:31,play,warp,title' cowpens-title 1536 830` for the title held at full opacity above the strip.
- **Drawer open.** Run `fg.sh shot <dir> '#antietam@1862-09-17T08:09,warp' antietam-drawer 1536 830`: the drawer with the 17 Sep heading and "Greene to the Dunker Church" open.

## Gotchas

- Each journey's browser starts with empty storage, but `c` or a click on Chapter titles or Captions stores the choice for every later battle on that origin. Clear `localStorage` between checks that need the default.
- Read the title's opacity with `getComputedStyle`, which follows the CSS animation. Under `,warp` it is `visibility: hidden` unless `,title` holds it, and Chapter titles off hides it with `visibility: hidden` too.
- After a click focus stays on that control, and the app ignores `c`, `f`, `t`, Space and the arrows aimed at a control. Blur first. Esc works from a control.
- A bare link opens with the drawer covering the left 404 px, so a click meant for the map at the left lands in the drawer. Close it first, or use `,play`.
