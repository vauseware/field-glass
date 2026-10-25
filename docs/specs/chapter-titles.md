# Chapter titles over the map, and a switch for the chapter labels

**Status:** draft

## Why

The chapter labels slant up from the timeline over the bottom of the map. On a battle with many chapters
(Sidi Bou Zid has 18, New Orleans 28) they cover a third of the map. A viewer who knows the battle wants
them gone. A viewer who hides them still needs to see when a new chapter begins.

## What the viewer gets

1. **A Chapters switch in the bar.** A third checkbox after Follow the action and Time-lapse, labelled
   "Chapters", with the tooltip "Show the chapter names over the map". The `c` key toggles it, as `f` and
   `t` toggle the other two. Off hides the slanted labels and their leader lines. Each chapter keeps its
   short tick on the scale, so the viewer still sees where chapters fall. The ticks are not clickable.
2. **A chapter title when a chapter begins.** The chapter's name fades in at the bottom of the map, just
   above the timeline, holds, and fades out. It has no panel behind it: the lettering sits on a soft band
   of the skin's paper colour that fades out at its edges. It shows whether the labels are on or off.

## Behaviour

### The switch

- It starts on, so nothing changes for a viewer who never touches it.
- The page remembers it per browser (`localStorage`, key `fieldglass.chapters`), across battles and
  reloads. Read and write it inside `try`. When storage fails, the switch starts on and still works.
- On a phone (640 px wide or less) the labels are hidden already, so the switch is not shown.
- Hiding the labels runs the same layout as today with every label hidden, so the ticks come from the
  existing code path in `layoutMarks()`.

### The title

| What started the chapter | Title |
|---|---|
| Play runs into it, at any speed or under time-lapse | shows |
| A click on its chapter label | shows |
| The page opens at it, from a link, Back or All battles | shows, once the map has drawn |
| A drag of the scrubber, or the arrow keys | does not show |
| Play crosses several chapters faster than a title lasts | each new one replaces the one showing and restarts the fade |

- **Timing.** Fade in over 0.6 s, hold 2 s, fade out over 1 s: 3.6 s in all, measured on the page's
  clock, not battle time, so it lasts the same at every speed. Pause does not hold it.
- **Place.** Centred across the window, its baseline 24 px above the timeline: above the bar when the
  labels are off, and above the tallest visible label when they are on, since the labels fill the strip
  over the bar (on Sidi Bou Zid they reach about 210 px above the bar at 1536x830). It moves when the labels are switched or laid
  out again, and never covers a panel or a label. On a phone it sits just above the story panel.
- **Name only.** The prototype also set the chapter's time under the name. It landed on unit labels and
  could not be read, and the story panel already gives the time.
- **Size.** About 2.75 times the panel title size (44 px on the laptop, 30 px on a phone), one line, cut
  with an ellipsis if wider than the map area less 48 px each side.
- **Dress.** Each skin dresses it in CSS under `body.theme-<id> #chapter-title`, with its own display face
  and ink, as each skin already dresses the panels. Starting points from the prototype: the Revolution in
  IM Fell with a fine rule above and below; the War of 1812 in Cardo; the Civil War in Playfair Display
  SC; the First World War in spaced Archivo Narrow capitals with a short red trench trace under it; the
  Second World War stencilled in chalk on the dark board.
- **Backing.** A band of the skin's `--paper-solid` behind the lettering, as an elliptical radial gradient
  at about 80% opacity in the middle, 55% at half its width and clear at three quarters, reaching about
  140 px past each end of the name. The prototype tried three backings on Cowpens, Sidi Bou Zid and New
  Orleans. A halo alone failed where the title landed on map lettering (on Sidi Bou Zid "Dive bombers"
  sat on "CCA COMMAND POST" and both blurred). A solid ribbon read best but looked like a card. The band
  read on all three and still let the map show at its edges.
- **No new skin hook.** The title is a DOM element over the canvas, like the panels. The canvas never
  draws it, so it costs no frame time, and `themes/*.js` do not change.
- **Reduced motion.** Under `prefers-reduced-motion: reduce` the title appears and disappears with no fade.
- **Screen readers.** The story panel already carries the chapter, so the title is `aria-hidden`.

### Screenshots

A `,warp` link (`#cowpens@07:45,play,warp`) never shows the title, so verification and PR screenshots
stay clean. A new `,title` flag after `,warp` (`#cowpens@07:45,play,warp,title`) shows the chapter's
title at full opacity, held, to prove its place and dress. The hash pattern in `app.js` and
`.claude/skills/verify-field-glass/features/screenshot-links.md` gain the flag.

## Data shape

- `chapterLabels: boolean`, beside `follow` and `lapse` in `app.js`, mirrored by the checkbox.
- One `#chapter-title` element in `index.html` beside `#caption`. Showing a title sets its text and
  restarts one CSS animation. The page's state is only "the title element's text and whether its
  animation is running", so there is no timer state to clean up when a battle changes.
- The trigger is the existing chapter change at `if (curEvent !== shownEvent)` in `app.js`, plus one
  flag set by the cause of the change: `seek()` from the scrubber or arrow keys clears it; play, a label
  click and the page opening set it.

## Verification

A new journey, `.claude/skills/verify-field-glass/journeys/chapters.cjs`, drives the page as a viewer
does and prints PASS or FAIL for each of these:

1. The Chapters checkbox shows and is checked on first load; visible labels > 0.
2. A click on it hides every label; the ticks remain; visible labels = 0.
3. `c` turns the labels back on.
4. A reload keeps the setting off; a different battle opens with it off.
5. With storage blocked, the page loads, the switch starts on and still toggles.
6. Playing across a chapter boundary at 20×, the title's opacity rises above 0.9 within 1 s and falls to
   0 by 4 s, and its text is the new chapter's title.
7. A scrubber drag across three chapters shows no title.
8. A chapter-label click shows that chapter's title.
9. The title's box overlaps no panel and no visible chapter label, and its bottom sits within 30 px of
   the top of the labels (on) or of the bar (off), at 1536x830, 1280x700 and 390x844.
10. `laptop.cjs` passes at both laptop sizes with the new checkbox, and the bar does not wrap.

Shots for the PR: `,warp,title` on one battle in each of the five skins at 1536x830, one at 390x844,
and the bar with Chapters off on a battle with many chapters.

## Out of scope

- A switch for the title itself. Add one only if the title proves distracting in use.
- Changing what the story panel shows.
- Hiding the chapter ticks.

## Open decisions

- Whether the switch should start off on battles with more than 15 chapters, where the labels crowd the
  map most. Default: starts on everywhere, as written above.
