# ADR-0008: The First World War skin

**Status:** accepted, 2026-10-24

## Context

The timeline runs from the Revolution to the Second World War, and the First World War is the one gap. Each war
wears its own skin, in the dress of its own maps (ADR-0002). The Western Front was fought from trench maps: sheets
at 1:10,000 or 1:20,000, printed by the Ordnance Survey and later by the AEF, squared for map references and
overprinted with the trenches and wire. No WWI battle is built yet, so the skin comes first, as the Second World
War's did (ADR-0004).

Three prototypes were built as skins and shown on Guilford Courthouse, Fort Fisher, and Yorktown at night:

- **A, a trench map.** A 1:10,000 trench map: cream paper, brown contours, woods as tree signs, a squared grid of
  numbered 1000-yard squares inside lettered 6000-yard squares, trenches in red with fire bays and traverses, and
  wire as crosses before them.
- **B, a situation map.** A staff officer's situation map: a grey base map with the units and their arrows in red
  and blue, the names lettered by hand, on an olive board.
- **C, a poster.** A wartime poster: a dark, shell-pocked mud ground, names in heavy condensed capitals, a black bar
  with mustard buttons.

## Decision

- **The trench map (A).** It is the map the war is remembered by, and no other war can wear it. B sits too close to
  the Second World War skin's coloured marks over grey, and its hand lettering reads worse at 16 px. C is not a map,
  which breaks ADR-0002's rule that a war wears the dress of its maps, and its dark ground costs the units contrast.
- **The registry holds `ww1`.** A battle dated 1914 to 1918 wears it unless its `theme` says otherwise;
  `?theme=ww1` previews it on any battle. Under a preview, `preview(b)` paints the first side blue and the last
  side red. `themeFor` now reads the war years from a table, so a new war is a row, not another branch.
- **Every trench and work is red.** Real trench maps drew the enemy's trenches in red and their own in blue, or left
  their own off. Features in `battle.json` carry no side, so the skin cannot tell whose line is whose. Colouring them
  by side needs a `side` on each feature and a change to `paint.js`, and waits until a WWI battle needs it.
- **The grid is the real system, placed by the battle's extent.** The squares start at the map's top left corner,
  not at any real sheet's origin, and the letters run A to X across the extent. A reference such as "22" names a
  square on this map only.
- **One ground recipe.** The skin exports `ground(b, T)`, and the start screen draws its backdrop from it, as the
  Civil War and the War of 1812 do. The backdrop adds the trenches dug during the battle, which the layer leaves out
  because they come and go, and centres on them.
- **The start screen samples Yorktown.** Until a WWI battle lands, the war shows an in-preparation card over
  Yorktown's siege works, the nearest thing the app has to a trench system. `sample` in `WARS` already does this for
  a war with no battles.
- **The clock reads as the war diaries wrote it**, "2.15 p.m.", and the scale of hours as "2 p.m.".
- **A star shell lights the field at night.** It is a page layer that drifts and dims with CSS, not a canvas pass,
  per ADR-0002.

## Consequences

- `?theme=ww1` shows the skin on every battle today, recoloured. A WWI battle will wear it in its own colours.
- The British side's red and the trench red are the same colour under a preview, and so are a red side's units and
  the works they hold. A WWI battle's `sides` should keep its red side off the trench red.
- On a large battle such as Sidi Bou Zid the grid figures shrink to specks at the battle's usual zoom; the lines and
  letters still read.
- The start screen loads Crimson Pro and Archivo Narrow with the other wars' fonts.
- The skin keeps a clean copy of the layer for the dashed tracks, as the other skins do, so a battle's layer costs
  twice its memory.
