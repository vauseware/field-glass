# ADR-0010: Chapter titles, and a switch for the chapter labels

**Status:** accepted, 2026-10-25

## Context

The chapter labels slant up from the timeline over the bottom of the map. On a battle with many chapters (Sidi
Bou Zid has 18, New Orleans 27) they cover a third of it, and a viewer who knows the battle wants them gone. A
viewer who hides them still needs to see when a new chapter begins. A prototype tried three backings for a
chapter title over the map on Cowpens, Sidi Bou Zid and New Orleans:

- **A halo** round the letters alone. Where the title landed on map lettering, both blurred (on Sidi Bou Zid
  "Dive bombers" sat on "CCA COMMAND POST").
- **A solid ribbon.** It read best, but looked like another card.
- **A soft band** of the skin's paper, an elliptical radial gradient at 80% in the middle, 55% at half its width
  and clear at three quarters.

The prototype also set the chapter's time under its name. It landed on unit labels and could not be read.

## Decision

- **A Chapters checkbox** in the bar, key `c`. Off hides the labels by running the same layout with every label
  hidden, so each chapter keeps its tick. It starts on for 15 chapters or fewer and off for more. The viewer's
  choice, once made, holds for every battle and reload in that browser, read and written inside `try` so blocked
  storage falls back to the chapter count. The labels never show on a phone, so neither does the switch.
- **The band**, which read on all three battles and still let the map show at its edges. Name only; the story panel
  already gives the time.
- **One DOM element** over the canvas, `#chapter-title`, `aria-hidden` since the story panel carries the chapter.
  Showing a title sets its text and restarts one CSS animation (0.6 s in, 2 s held, 1 s out, on the page's clock),
  so there is no timer to clean up and the canvas draws nothing more. Each skin dresses it in CSS. Under reduced
  motion it appears and goes with no fade.
- **What shows it.** The chapter change `updateHud()` already detects, unless the scrubber or an arrow key moved
  the clock since the last frame (`quiet`, cleared every frame). Play, a label click and the page opening show
  it; a drag through many chapters does not flash one each.
- **The opening shot comes first.** No title while it runs (ADR-0009); when it ends or is skipped, the current
  chapter's title shows once. `,warp` never shows one, so screenshots stay clean; `,warp,title` holds it at full
  opacity for screenshots of its place and dress.
- **Place.** Its box sits 14 px above the tallest label showing, or the bar when the labels are off, so the baseline
  is about 24 px above them; on a phone, above the story panel. It is centred across the map less 48 px each side
  (17 px on a phone). Where the top panel or the story panel reaches down level with it, as on a 1280 x 700 laptop
  with the details open, it is centred in the gap between them instead, and a name too long for the gap is cut
  with an ellipsis.

## Consequences

- A title can cover units for 3.6 s. There is no switch for the title itself; add one only if it proves
  distracting in use.
- A battle of more than 15 chapters opens with its labels off until the viewer turns them on, so journeys that
  need the labels (`stacking.cjs`) press `c`.
- Off-centre placement and an ellipsis are rare: they need a tall panel level with the title, which play avoids by
  folding the top panel.
