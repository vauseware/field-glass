# ADR-0014: The battle chrome as a lower third

**Status:** accepted, 2026-11-10

## Context

The battle screen's chrome covered too much of the map. A top panel with the battle's details sat at the top left,
the story panel at the top right, and a bar at the foot held the clock, the speed, three checkboxes and chapter labels
slanting up over the map (ADR-0010). Dave's father, who watches the battles, should see the map and still find every
control without hovering for it. Issue #73 showed Dave three layouts, each in all five skins:

- **A, slim bar.** The panels stay in the corners, and the bar shrinks to one row.
- **B, lower third.** The story becomes a caption over a bar docked to the foot. The details and the chapters go in a
  drawer behind a title chip, and the clock moves to the top right corner.
- **C, quiet field.** While the battle plays, only a hairline timeline and a slug with the chapter's name show. The
  bar and the record come back when it stops.

## Decision

Dave chose B (2026-11-09). It covers the least of the map while it plays and still shows every control: the caption
sits low where a television puts its lower third, the clock is small and out of the way, and nothing hides until it is
hovered. A keeps the two corner panels over the map. C hides the controls, so a viewer must know where to look for
them.

- **The bar** docks to the foot, 58 px high and full width: Play, the scrubber and **Settings**. Each skin keeps its
  groove and knob.
- **The chapters** are ticks above the groove, the current one taller in the skin's accent. The pointer on the
  scrubber shows the nearest chapter's name and time within 12 px, in a tip above the bar. The tip is hover only; a
  click seeks as before. Ticks are not controls. The way to jump by keyboard is the chapter list.
- **The chip and drawer.** The title sits in a chip at the top left with a **Chapters** button. That opens a 404 px
  drawer with the place and date, the sides, Outcome, the chapter list, the hint line, and All battles, Legend and
  Sources. The list gives each chapter's time and name under day headings; a click jumps there and turns Follow on, and
  the current row opens to its whole story. Close, Esc and Play when play starts close the drawer; a pause leaves it as
  it is, so a viewer can pause, open it and read. A bare or `@time` link opens with it open, `,play` with it shut, and
  `,outcome` opens it on the Outcome. The opening shot closes it first, so the landing is worked out against the
  layout play shows.
- **The caption strip** replaces the story panel: the time and the chapter's name on one line, then the story in pages
  of whole sentences, three lines each, with a dot a page. A sentence too long breaks at a semicolon; if it still does
  not fit, the strip grows, so nothing is clipped. Pages are measured on the real strip, so each skin's face, capitals
  and suffix count, and only when the chapter or the strip's width changes. The strip is held at its tallest page, so a
  page turn never moves the camera. The page showing depends only on the battle clock: the chapter's playing time,
  counted as `playTime` counts it, is shared among its pages by their length (`captionPage` in `sim.js`). The Second
  World War tape ends only its last page STOP.
- **The clock cluster** sits at the top right: a dial per skin, the time over its date, the speed, and the Time-lapse
  switch. While time-lapse runs, the speed reads `»` and the lapse rate in the accent.
- **Settings** opens over its button: Follow the action (`f`), Chapter titles (`c`) and Captions. The browser keeps
  Chapter titles and Captions for every battle. Three volume sliders, Sound, Music and Narration, store their values
  in `fieldglass.volume` (60, 40 and 80 to start) and do nothing else until sound ships. Esc closes one layer a press:
  Settings, then the drawer, then the unit card.
- **Checkboxes become switches,** dressed per skin. Each is still an `<input type="checkbox">` inside its label, so
  the keyboard and screen readers work as before.
- **The DOM holds the state.** `#top.open`, `hidden` on `#settings`, and the inputs' `checked` and `value` are each the
  only copy; nothing mirrors them in JS, except the chosen speed, which may have no menu entry. Stored settings are
  markup: `data-pref` (and `data-field` for the volume object). The panels that frame the map carry `data-clear`, and
  the opening shot hides every `.panel`, so neither list is kept by hand.
- **Skins.** The Revolution's dial is a brass watch, the War of 1812's a chronometer, the Civil War's a gilt-rimmed
  watch, the First World War's a luminous trench watch, and the Second World War keeps its sector clock. The First and
  Second World Wars word chapter times as their clocks do (a `time` hook: "7.30 a.m.", "0730"); the others use
  "7:30 AM". The Second World War's tape head is one line, as in the mock.

What this replaces in ADR-0010:

- **The Chapters checkbox** becomes Chapter titles, which shows or hides the name that fades in over the map, under
  a new storage key (`fieldglass.titles`). The rule that turned labels off past 15 chapters goes, and
  `fieldglass.chapters` is no longer read.
- **The slanted labels,** their leader lines and the code that spread them go. The ticks, the tip and the chapter
  list replace them.
- **The title's place** is 14 px above the caption strip, or above the bar when Captions is off. It still narrows past
  the open drawer.

Dave approved these assumptions on 2026-11-10: `c` turns Chapter titles on and off; a Captions switch replaces the
story's Hide button; the sliders are built now and only store values, starting at 60, 40 and 80 under one key; pages
follow the battle clock until narration gives them cue times; the hint line moves into the drawer; and a tick's tip
names its chapter, but a click on the scrubber does not snap to it.

## Consequences

- At 1536 x 830 with the drawer closed, the chrome covers 20.7% of the window on Antietam at 8 AM (`chrome.cjs`;
  the spec's limit is 22%). The scrubber is 1298 px wide there and 1042 px at 1280 x 700.
- A chapter told in one long sentence with no semicolon grows the strip past three lines for that chapter: on
  Sidi Bou Zid "Frühlingswind" reaches five lines at 1536 x 830, and two Antietam chapters four at 1280 x 700.
- The Somme's dawn chapters sit about 3 px apart on the scrubber. The tip names the nearest one; the list is the sure
  way to pick one. Dave will judge the hover there.
- A chapter that plays in a few seconds turns its pages faster than they can be read. The drawer holds the whole
  story.
- Until sound ships, the sliders move and nothing changes. `docs/specs/battle-sound.md` still describes a speaker
  button in the bar and an `m` key; that spec must come into line with `fieldglass.volume` before it is built.
- Chapter titles and Captions use `:has()` in CSS (Chrome 105, Firefox 121, Safari 15.4).
- Phones are not fitted (ADR-0012). The narrow-screen rules for the old chrome are gone.
