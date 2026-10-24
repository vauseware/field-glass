# ADR-0007: The War of 1812 skin

**Status:** accepted, 2026-10-24

## Context

New Orleans (8 January 1815) is the next battle to build, and the first of the War of 1812. Each war wears its own
skin (ADR-0002), and the war's battles were fought on coasts, rivers and lakes: New Orleans on the Mississippi and
Lake Borgne, Baltimore on the Patapsco, Lake Erie, Plattsburgh, the Niagara. The Revolution plate would have served
by default, but it would not have told the war apart from 1781.

Three prototypes were built as skins and shown on Guilford Courthouse (inland) and Fort Fisher (coast):

- **A, pen and wash.** Latour's 1816 atlas of the Louisiana campaign: iron-gall ink on wove paper, the ground and
  woods as watercolour washes, no contours or hachures, a fleur-de-lis north arrow.
- **B, a coastal chart.** A blue-back chart as Blunt and the Admiralty sold them: navy ink on cream, the coast washed
  yellow, white water lined and figured with soundings, hachure caterpillars for hills, rhumb lines from a rose, a
  graduated border, the blue backing beyond.
- **C, an engineer's field sketch.** A Corps of Engineers notebook: a squared page, pencil shading and hachures,
  scribbled woods, units as ink boxes hatched in red and blue, the book on a leather board.

## Decision

- **The chart (B).** It is the one look no other war can wear, and it is strongest on exactly the ground the war's
  battles were fought over. A was too close to the Revolution plate to earn a second skin; C's pencil ground ran dark
  on flat coast and read as a different app rather than a different war.
- **The registry holds `war-of-1812`.** A battle dated 1812 to 1815 wears it unless its `theme` says otherwise;
  `?theme=war-of-1812` previews it on any battle. Under a preview, `preview(b)` paints the first side blue and the
  last side red.
- **One ground recipe.** The skin exports `ground(b, T)`, and the start screen's War of 1812 backdrop draws from it,
  as the Civil War's does (ADR-0006). `WARS` in `splash.js` gains the war, with an in-preparation card until New
  Orleans lands.
- **The coast wash is by height.** The yellow band is the ground within a small share of the relief above the
  water level, not a buffer round the shoreline, so it costs nothing beyond the relief pass. On flat coast it reads as
  the chart's tint; on a battle with no water it never appears.
- **Soundings are not real.** They are random figures of two to nine fathoms scattered over water cells, decoration
  in the chart's manner. A chart of the real soundings would need a source and is not promised.
- **Four wars on the timeline.** The start screen's war buttons alternate between two rows so the Revolution's and
  the War of 1812's, three decades apart, never overlap; on a phone the buttons sit two to a row.

## Consequences

- `?theme=war-of-1812` shows the skin on every battle today, recoloured. When New Orleans lands it wears the skin in
  its own colours.
- The start screen loads Cardo with the other wars' fonts.
- The skin keeps a clean copy of the layer for the pecked tracks, as the Revolution does, so a battle's layer costs
  twice its memory.
