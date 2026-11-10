# Timeline, clock and panels — Spec

**Status:** draft · **Target repo:** vauseware/field-glass · **Sources:** issue #73 and its comments; the mock Dave chose on 2026-11-09 (option B of three; its renders are in the build issue)

## Summary

The battle screen's chrome is rebuilt to cover less of the map: a docked one-row timeline, the story as a caption
strip above it, the battle's details and a chapter list in a drawer, and the clock with its speed and Time-lapse
controls in the top-right corner. It is for someone watching a battle play, Dave's father first, who should see the
map and still find every control without hovering. It comes before sound and narration (#88,
`docs/specs/battle-sound.md`), which need the caption strip and the settings panel.

## The design

Measures are the mock's, at 1536 x 830. The build issue shows each piece in all five skins, watching and open.

| Piece | Place | Size | Holds |
|---|---|---|---|
| Title chip (`#top`, closed) | top left, 14 px down, 16 px in | one row | the battle's title at 23 px, a **Chapters** button; no kicker |
| Drawer (`#top`, open) | left edge, top of the window to the bar | 404 px wide | kicker, title, **Close**; place and date; the sides; Outcome; the chapter list; the hint line; All battles, Legend, Sources at its foot |
| Clock cluster (`#clock-box`) | top right, 14 px down, 16 px in | one row, 400 to 470 px wide by skin | a 40 px dial, the time over its date, the speed, the Time-lapse switch |
| Caption strip (`#caption`) | centred on the map, 48 px above the bar | at most 900 px wide | the chapter's time and name on one line, up to three lines of story at 20 px, page dots |
| Bar (`#bar`) | docked to the bottom edge, full width | 58 px high | Play, the scrubber, **Settings** |
| Settings (`#settings`) | over the Settings button | 320 px wide | Follow the action, Chapter titles, Captions |

### The timeline

- One tick per chapter above the groove, the current chapter's taller and in the skin's accent. The slanted labels,
  their leader lines and the code that spreads them are removed.
- The pointer over the scrubber shows the nearest tick's chapter within 12 px: its name and time on one line, in a
  tip just above the bar. The tip is hover only. A click on the scrubber seeks as it does now.
- The scale of hours stays under the groove. Each skin keeps its groove and knob as they are today.
- Ticks are not controls and take no focus. The chapter list is the way to jump by keyboard.

### The chapter list

- Lives in the drawer under a heading that counts the place, "Chapters 9 of 24".
- One row per chapter, 44 px high: the time of day as the skin writes it, then the name. A battle of more than one
  day groups its rows under day headings ("17 Sep").
- A click seeks to the chapter's start and turns Follow on, as a label click does now. The drawer stays open.
- The current chapter's row is marked and opens to show its whole story beneath it. When the chapter changes, the
  list scrolls so the new row shows.

### The drawer

- **Chapters** on the chip opens it; **Close** and Esc close it. Pressing Play closes it, as Play folds the top
  panel now.
- Outcome stays a `details` element inside it. A `,outcome` link opens the drawer and Outcome. A `,play` link
  opens with the drawer closed.
- Open, the caption strip centres in the space to its right and narrows to fit.

### The caption strip

- Shows while a chapter is current and Captions is on. It replaces the story panel in the top-right corner, and has
  no Hide button.
- The story is cut into pages of whole sentences, as many as fit three lines at the strip's width. A sentence too
  long for three lines breaks at a semicolon; if it still does not fit, the strip grows. Nothing is clipped.
- The page showing depends only on the battle time. The chapter's playing time (real seconds at its speed with
  Time-lapse on, counted as `playTime` counts) is shared among its pages by their length. Scrubbing back shows the
  earlier page.
- Dots under the text show how many pages there are and which one shows. They are not controls. One page shows no
  dots.
- In the Second World War skin the strip is the teleprinter tape, in capitals, and only the last page ends STOP.

### The clock cluster

- The time and date are the skin's `clock(t)`, held at the width of the widest time it can show, as now.
- Each skin has a dial that shows the battle's time (see the table).
- The speed is the current `#speed` menu, drawn as a chip. While time-lapse is running, the chip reads
  `» <lapse>×` in the skin's accent in place of the chosen speed.
- The Time-lapse switch sits last. Key `t` still turns it.

### Settings

- **Settings** opens a panel over the button; the button, Esc or a click outside closes it.
- Follow the action (key `f`). Chapter titles (key `c`): the name that fades in over the map when a chapter begins
  (ADR-0010). Captions: the caption strip.
- Chapter titles and Captions start on, and the browser keeps the viewer's choice for every battle.
- Sound, music and narration volume go here when they exist. This spec builds no volume control.

### The switches

Checkboxes become switches: a track with a knob, the knob to the right when on. Each stays an
`<input type="checkbox">` with its label, so the keyboard and screen readers work as now.

### Each skin

| Skin | Dial | Switch | Bar and clock ground | Caption strip |
|---|---|---|---|---|
| revolution | a brass watch: cream face, ink hour marks, blued hands | a brass knob in an ink-ruled groove, red when on | parchment with the double rule | a parchment slip |
| war-of-1812 | a chronometer: white face, navy marks, a brass outer ring | a square cream knob in a navy slot, red when on | the chart's blue backing | a cream slip with the navy inner rule |
| civil-war | a gilt-rimmed watch, cream face | a brass knob, the track gilt when on | blue cloth with the gilt rule | a linen slip, the name in small capitals |
| ww1 | a trench watch: black face, luminous marks and hands | a square slot; a grey block when off, a red block when on | cream with the ink rule | a cream slip with the ink rule |
| ww2 | the sector clock, as now | a dark slot; the knob is an amber lamp, lit when on | the dark board | the teleprinter tape |

### What else moves

- The chapter title (ADR-0010) sits 14 px above the caption strip when it shows, else above the bar, centred on the
  map. It still narrows past the drawer when the drawer is open.
- The camera's clear rect is measured from the chip or drawer, the clock cluster, the caption strip and the bar.
- The opening shot hides and fades back the clock cluster with the other panels.
- The unit hover tip and the unit card stay above every piece here.

## Goals & success criteria

`F` is `.claude/skills/verify-field-glass`. Journeys run as `bash $F/fg.sh drive <dir> $F/journeys/<name>.cjs`.

- The page still validates every battle — check: `npm run check`.
- The scrubber is at least 1250 px wide at 1536 x 830 and 1000 px at 1280 x 700 — check: new `chrome.cjs`.
- The bar is at most 60 px high, and with the drawer closed the chrome covers at most 22% of the window at
  1536 x 830 on Antietam at 8 AM with its caption showing — check: `chrome.cjs`.
- The clock cluster lies wholly in the right 40% of the window at both laptop sizes — check: `chrome.cjs`.
- No chapter label is drawn over the map; there is one tick per chapter; the pointer on a tick shows its name and
  time — check: `chrome.cjs` on Sidi Bou Zid, New Orleans, Antietam and the Somme.
- A click on a chapter row moves the clock to that chapter's start and turns Follow on; the row opens with the
  whole story — check: `chapters.cjs`, rewritten.
- Play closes the drawer; Esc closes the drawer and Settings — check: `chapters.cjs`.
- Every page of every chapter of those four battles fits the strip unclipped at both laptop sizes, and no page is
  under 25 characters — check: `chrome.cjs` steps through the chapters and pages.
- `captionPage` is 0 at a chapter's start, the last page just before the next chapter, and never falls as time
  rises — check: cases in `tools/check.mjs`.
- Keys `f`, `t`, `c`, Space, the arrows and Esc work; Chapter titles and Captions survive a reload — check:
  `playback.cjs` and `chapters.cjs`.
- No scroll, nothing covered, text 16 px or more, controls 44 px or more, in every skin at both laptop sizes —
  check: `laptop.cjs` over one battle per skin.
- The hover tip and unit card stay on top — check: `stacking.cjs`, rewritten for the caption strip and tick tip.
- The opening shot hides every piece and lands as before — check: `opening.cjs` and
  `node tools/formal/opening-landing.mjs`.
- Each skin matches the mock's renders: dial, switch, grounds, caption strip — [human check: Dave, the ten
  screenshots the build PR posts against the ten in the build issue].

## Non-goals

- Sound, music, narration and their volume controls (#88, `docs/specs/battle-sound.md`).
- The unit list (#83).
- Phones (ADR-0012, #90). The narrow-screen rules may go; nothing is checked under 1280 px wide.
- The start screen, the map, the skins' canvas drawing and the battles' data.
- Any setting not named here.

## Users & scenarios

- Watching: the viewer presses Play. The drawer closes. They see the map, the clock, the caption turning its pages
  and the bar.
- Jumping: they press Chapters, read the list and click a chapter. The clock moves there and the camera follows.
- Reading: they pause, open the drawer and read the current chapter's whole story.
- Pacing: they change the speed or turn Time-lapse off at the clock.
- Finding a moment: they run the pointer along the scrubber, read the chapter names, and drag the knob.

## Design constraints

- Vanilla JS, Canvas 2D, static files, no framework or bundler. The chrome is DOM and CSS; the canvas draws none
  of it.
- A skin's dress is CSS under `body.theme-<id>` in `index.html`. `app.js` never asks which skin it has
  (ADR-0002); anything a skin words differently is a hook in `themes.js`.
- Text 16 px or more. Controls 44 px or more. Ticks are not controls.
- Visible labels over tooltips: Chapters and Settings carry their names.
- Reduced motion: no slide or fade on the drawer, the settings panel or the caption's page turns.
- Runs on a laptop with integrated graphics: no per-frame layout reads; measure only when a piece or the window
  changes size, as `measureSafe` does now.

## Data & interfaces

Frozen for the build and its journeys:

- Kept ids: `#top`, `#title`, `#kicker`, `#sub`, `#legend`, `#outcome`, `#home`, `#legend-btn`, `#src-btn`,
  `#caption`, `#cap-when`, `#cap-title`, `#cap-text`, `#chapter-title`, `#bar`, `#play`, `#speed`, `#scrub`,
  `#hours`, `#marks` (ticks only), `#clock`, `#follow`, `#lapse`.
- New ids: `#clock-box` (the cluster), `#chapters-btn`, `#top-close`, `#chapter-list`, `#cap-pips`, `#tick-tip`,
  `#settings-btn`, `#settings`, `#titles`, `#captions`.
- Removed ids: `#top-fold`, `#cap-fold`, `#chapters`.
- `#top` carries class `open` when the drawer is open. The current chapter's row carries class `on`.
- `sim.js`: `captionPage(b, ev, t, weights) => index`, DOM-free. `weights` are the pages' character counts.
- `themes.js`: an optional skin hook `time(t) => string`, the time of day without the date, for the chapter list
  and the tick tip. Without it: `6:30 AM`, `8 AM`.
- `localStorage`: `fieldglass.titles` and `fieldglass.captions`, each `on` or `off`, read and written inside
  `try`. `fieldglass.chapters` is no longer read.
- No change to battle data, `battles/index.json` or the link hash.

## Human-only work

- P0: none. The design is chosen.
- P-Final: Dave compares the build PR's screenshots with the mock's; `npm run deploy`; an annotated tag on `main`
  (the README contract changes).

## On ship

- An ADR for this decision: the three options shown, why B, and what it replaces in ADR-0010 (the Chapters
  checkbox, the labels, the title's place).
- README: the paragraphs on the chapters, the bar and each skin's clock. Retake every image under
  `docs/screenshots/` that shows the chrome.
- `.claude/skills/verify-field-glass`: the feature files and journeys named above.
- Delete this spec in the same commit.

## Risks & open questions

- Sentence splitting. Names such as "S. D. Lee" and "Brig. Gen." hold full stops. The splitter must not break
  after a single capital or a rank; the 25-character check catches a miss.
- Reading time. A chapter that plays in a few seconds turns its pages faster than they can be read. This is true
  of the story panel today; the drawer holds the whole text.
- Dense ticks. The Somme has 13 chapters in 3% of its length, about 3 px apart. The tip names the nearest; the
  list is the sure way to pick one.
- The widest clock cluster (about 470 px) and the longest title's chip share the top row at 1280 px wide.
  `laptop.cjs` must prove they do not meet.

## Assumptions

- Key `c` turns Chapter titles on and off, under a new storage key, and the 15-chapter rule goes — PENDING
- A Captions switch replaces the story panel's Hide button — PENDING
- No volume controls until sound ships — PENDING
- Pages follow the battle clock by the rule above until narration gives them cue times — PENDING
- The hint line moves into the drawer — PENDING
- Tick hover names the chapter but a click does not snap to it — PENDING

## Decisions log

- 2026-11-09: Which of the three layouts? → B, the lower third.
- 2026-11-09: Does the story panel stay in the top-right corner? → No. The caption strip replaces it.
- 2026-11-09: Where does a long story go? → Both: paged in the strip, whole in the drawer under the current chapter.
- 2026-11-09: The clock at top centre covers the middle of the map. → It moves to the top-right corner, smaller.
- 2026-11-09: Does Time-lapse stay in the bar? → No. It sits with the clock and the speed.
- Issue #73 comments: chapters are ticks with a hover function; the clickable list goes in the info panel; Follow
  the action goes in a settings panel with the volume controls to come; each skin may have its own clock.
