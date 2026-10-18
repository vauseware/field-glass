# ADR-0006: The Civil War skin

**Status:** accepted, 2026-10-18

## Context

ADR-0002 chose the Civil War look, the Hotchkiss and Bachelder topographical engineer's survey, and deferred it until a
battle of that war arrived. First Manassas (21 July 1861) is being built now. The start screen already drew Guilford in
this style as a specimen sheet behind the Civil War card (ADR-0005), with its own copy of the ground recipe. The skin is
read by a non-technical historian on a cheap laptop, who must read it without hovering.

## Decision

- **The registry holds `civil-war`.** A battle dated 1861 to 1865 wears it unless its `theme` says otherwise.
  `?theme=civil-war` previews it on any battle. Under a preview, `preview(b)` paints the first side Union blue, the
  last side Confederate red and any side between a lighter blue, after Bachelder. A Civil War battle keeps the colours
  in its `battle.json`, so it should set Union blue and Confederate red itself.
- **One ground recipe.** The survey ground moves from `splash.js` into the skin as `ground(b, T, s)`. The skin's layer
  and the start screen's specimen sheet both draw from it, so the card shows exactly what a battle will.
- **Marks are sized for the farthest zoom.** The follow camera never pulls back past the whole map filling the window.
  At Guilford that is 0.48 screen px per layer px on a 1440 px window, so contour figures drawn 11 layer px high came out
  at 5 px and vanished. `s` is layer px per screen px at that zoom (clamped to 1 to 2). Figures are drawn `s` times
  larger; woods, roads, fences and other marks only `√s` times, because at `s` they crowded the regiments once the
  camera closed in to twice that zoom; and the contour count is divided by `s`, so Guilford's 5 ft interval becomes
  10 ft. The start screen passes `s = 1` and keeps its look.
- **A regiment is a block ruled into companies under a flag.** Ten companies, fewer where a company would be under
  6 px wide. The front rank is a heavy rule; a point appears only on the march. The flag stands upright on the screen
  from the centre of the front, whatever the facing, so it never reads upside down, and the regiment's name is lifted
  above it. Cavalry fly a swallow-tailed guidon; a battery has no flag, only its guns.
- **Fences zig-zag.** The specimen sheet drew fences as a line with cross ticks, which period sheets use for a
  railroad. Fences are now worm fences, which changes the card's fences too.
- **Named buildings get a black square,** as the survey sheets mark a house beside its owner's name.
- **Lettering is Old Standard TT with Playfair Display SC for titles,** the faces the start screen's card already uses.
- **Night is a blue-grey wash with a lantern page layer.** No cloud layer, so the skin adds one page layer, not two.

## Consequences

- A frame costs about what a Revolution frame does. On this Mac's GPU: Guilford 0.54 ms against 0.56, Yorktown at
  night 0.48 against 0.37 (median of 3 alternating runs). The flags are 0.03 ms of Yorktown's difference (measured with
  them removed). The rest is not isolated; the Civil War story panel is taller, so the camera frames the battle
  differently and the two runs do not draw the same view. On the software rasteriser: Guilford 3.16 ms against 3.32,
  Yorktown at night 3.66 against 3.60.
- The layer builds in 82 to 118 ms on the GPU and 249 to 496 ms in software, against the Revolution's 126 to 170 ms and
  812 to 838 ms. It has no engraved tracks, so it costs its size once.
- When the first Civil War battle lands, the start screen's card can draw it instead of Guilford by changing the battle
  `drawSurvey` loads.
