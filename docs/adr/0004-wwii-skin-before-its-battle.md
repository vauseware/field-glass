# ADR-0004: The Second World War skin is built before its first battle

**Status:** accepted, 2026-10-17

## Context

ADR-0002 chose a skin for each war and deferred the Civil War and Second World War skins until a battle of their war
arrived, with no registry entries until then. The user asked for the Second World War skin now, while Sidi Bou Zid
(ADR-0003) is still being researched, so it can be judged and refined before the data lands. Until then there is no
battle to show it on.

## Decision

- **The registry holds `ww2` now.** A battle wears the skin its `theme` names; with none, a battle dated 1939 to 1945
  wears `ww2` and any other wears `revolution`. There is still no Civil War entry, and none is stubbed.
- **`?theme=<id>` previews a skin on any battle.** The query outranks `theme` and the year. Under a preview only, the
  skin may recolour the sides through its `preview(b)` hook; `ww2` paints them olive drab against field grey, the last
  side listed as the enemy.
- **Chinagraph and tracer colours come from the sides.** A side may set `wax` (its grease pencil) and `tracer` (an
  `[r, g, b]`) in `battle.json`. Without them the last side listed draws in red with green tracer and the others in
  yellow with orange-red tracer, as a US staff map marks the enemy in red. Order the sides with that in mind.
- **No engraved tracks.** Where the Revolution engraves each unit's path into the layer, `ww2` draws a hollow
  chinagraph arrow from where each unit stood at the start of the previous chapter. The layer needs no clean copy, so a
  battle's layer costs its size once, not twice.
- **The lamp blends from `#fx` itself.** A fixed element forms an isolated group, so a child's `mix-blend-mode` never
  reaches the map. `body.theme-ww2 #fx` carries the multiply; the lamp inside it sways with a CSS transform.
- **Four optional hooks join the skin contract:** `label.place(l)` moves a unit's label before overlaps are tested (the
  counter sits behind the unit); `fire(ctx, V, pops, n)` draws before the muzzle flashes (tracer), with each flash's
  side, line of fire and a random draw; `when(event, b)` words the caption's time and a tag (the teleprinter's
  time of origin); `preview(b)` as above. The unit hook also gets the unit's `type`, so an `armor` drawing is one more
  case inside a skin.
- **The grid numbers are UTM.** The 1 km grid is numbered with the last two figures of the UTM kilometre at the
  battle's `origin`, so a position can be found on a modern map. Period sheets used other grids (the British Modified
  grid, Lambert zones in France and North Africa); the lines are drawn square to the map and lean off true UTM by the
  grid convergence, under a degree on these sheets.

## Consequences

- `?theme=ww2` shows the skin on every Revolution battle today, recoloured, with the 1781 date on the print captions.
  When Sidi Bou Zid lands it wears the skin with no flag, in its own colours unless it sets `wax` and `tracer`.
- A frame costs about what a Revolution frame does on this Mac's GPU (Guilford 0.50 ms against 0.57, Yorktown at night
  0.44 against 0.39, median of 3 alternating runs of 7 batches each). On the software rasteriser it costs about 0.6 ms
  more at Guilford (3.9 ms against 3.3), mostly the brackets, the counters and the arrows. The layer builds in 45 to
  170 ms on the GPU and 790 to 980 ms in software, against the Revolution's 75 to 240 ms and 830 to 950 ms.
- Counters are painted once per unit and text size and cached, so a long battle holds a few hundred small canvases.
