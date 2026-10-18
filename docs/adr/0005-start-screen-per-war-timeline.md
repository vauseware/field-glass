# ADR-0005: One start screen per war, chosen on a timeline

**Status:** accepted, 2026-10-18

## Context

The start screen was one parchment card listing every battle under a heading per war, over a sepia plan of a random
battle. With Sidi Bou Zid in, a Second World War battle sat under a Revolution card on a Revolution backdrop, and the
Civil War, planned next, had no place at all. Each war's battles already wear their own skin (ADR-0002); the start
screen did not.

A prototype pass built three layouts over the same three wars, each war's card and backdrop in the dress of its maps:

- **A, tabs on the card.** One tab per war along the card's top edge.
- **B, three doors.** A first screen split into one panel per war; choosing one opens that war's card.
- **C, a timeline.** The war's card over its backdrop, with the wars placed on a ruled scale of the years along the
  foot, the battle screen's scrubber in miniature.

## Decision

- **One screen per war, chosen on a timeline of the years (C).** The screen shows one war: its card, in that war's
  type and paper, over a backdrop drawn in its style. A bar along the foot rules 1770 to 1950 every ten years, marks
  each war's span, and holds a button per war with its years and number of battles. On a phone the scale is dropped
  and the three buttons sit in a row.
- **Rejected: tabs on the card (A).** At 390 px the three tabs were cramped, and the unselected tabs, dimmed to read
  as behind the card, read as disabled.
- **Rejected: three doors (B).** It costs a click on every visit before any battle can be chosen.
- **`WARS` in `splash.js` is the registry**, in date order: `{ id, name, years, from, to, war, draw(cv, o) }`. `war`
  is the `battles/index.json` string, so a war's battles are the index entries that carry it. Ids match the skins in
  `themes.js` where a war has one (`revolution`, `ww2`); the Civil War is `civil-war`. `npm run check` fails when a
  battle names a war with no entry, since that battle would not be listed anywhere.
- **The only state is the war on show, kept in the hash.** `#<war id>` opens the start screen on that war; choosing a
  war replaces the hash rather than adding a history entry per click. A bare URL opens the Revolution. All battles
  sets the hash to the battle's war, and any hash change that names something other than the battle on screen
  reloads the page, so All battles, Back and Forward all land where the URL says.
- **Backdrops.** The Revolution draws a random battle of its own as a sepia plan, at the chapter when both sides are
  most engaged (a moment after one side broke read as a one-sided plan); `?plan=<id>` picks it. The Second World War
  lays Sidi Bou Zid's recon mosaic under the lamp, with the skin's own counters and chinagraph arrows.
- **A war with no battles shows an in-preparation card.** The Civil War, until its first battle, says its battles
  are in preparation, offers the wars that have battles, and sits on a sample of the survey style: Guilford
  Courthouse's ground drawn as a topographical engineer's sheet.

## Consequences

- Adding a war is one `WARS` entry, its backdrop function and a block of `#splash.war-<id>` CSS. Its first battle
  in `battles/index.json` replaces the in-preparation card with a list.
- The start screen loads the Civil War's and the Second World War's fonts with the Revolution's, whichever war is on
  show.
- Backdrops are drawn at the window's size in CSS pixels, once per war and size, and redrawn on resize. The
  Second World War's builds the skin's whole layer the first time, about a second on a software rasteriser.
