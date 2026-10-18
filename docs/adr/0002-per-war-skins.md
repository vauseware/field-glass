# ADR-0002: Each war wears its own skin

**Status:** accepted, 2026-10-17

## Context

Field Glass began with Revolutionary War battles and one look: a green-tan shaded relief with Georgia labels. Civil
War and Second World War battles are planned, and a battle reads best in the dress of its own war's maps: a plan
engraved for a London publisher, a topographical engineer's survey, a recon photo on an operations table. The user
asked for a look that is captivating on the cheap laptop with integrated graphics that the app is built for.

A prototype pass built six throwaway directions (two per war) over Guilford Courthouse and measured each. The user
chose three:

- Revolution: the engraved plan already in use, refined (hachures, engraved woods, ruled fields, worm fences,
  water-lining, compass rose and scale of yards, paper grain), with three grafts from the second Revolution sketch:
  each unit's path dotted behind it, a candlelit night, and the scrubber ruled as a scale of hours.
- Civil War: the Hotchkiss and Bachelder survey (brown contours in feet, scalloped woods, red-ochre roads,
  Prussian-blue streams, units ruled into companies with small flags, crosses for the fallen).
- Second World War: a grey-green recon photo mosaic under a lamp (painted counters, chinagraph frontages, tracers,
  a teleprinter caption), with the 1 km grid and chinagraph advance arrows from the other sketch.

Not chosen: the Civil War "illustrated weekly" sketch, whose wood-engraving line screen shimmers into moiré as the
follow camera zooms, and which Canvas 2D cannot redraw at each zoom without WebGL; the second Revolution sketch as a
whole, because the user kept today's Revolution look; the Second World War acetate overlay as a whole, because the
photo table read better, though its grid and arrows were kept.

## Decision

Skins are per war. `themes.js` holds the registry; each skin is one module in `themes/` that owns everything that
differs between wars: the terrain recipe baked into the layer, how units, fire, the fallen and the night are drawn,
what lies beyond the map edge, the ambient layers, the clock, the legend's swatches. `app.js` calls the skin's hooks
and never branches on which skin it has. The chrome follows a `theme-<id>` class on `<body>`. A battle names its skin
in `battle.json` (`theme`) and gets the Revolution skin otherwise.

Only the Revolution skin ships now. The Civil War and Second World War skins are chosen but deferred until the first
battle of their war arrives; the registry holds no entries for them until then.

Performance rules from the prototype measurements:

- Everything static is baked into the per-battle layer once: relief, contours, hachures, woods, fields, water and
  every feature that does not come and go.
- Ambient motion and full-window effects (cloud shadows, paper grain and vignette, the candle at night) are page
  layers the browser composites and animates with CSS, never redrawn on the canvas. The prototype's lamp sway cost
  3.3 ms a frame when drawn on the canvas.
- At most one full-window canvas pass beyond the layer: the night wash. Muzzle flashes draw above it.
- A unit's dotted track would cost a dash per few pixels if redrawn every frame (2 ms at Yorktown, measured). The
  older part is engraved into the layer itself every second and a half; each frame draws only the last quarter hour.

## Consequences

- Adding a war is one module and one block of CSS, and app.js does not change.
- A Revolution frame costs about what the old look cost: on this Mac's GPU 0.35 to 0.9 ms a frame against 0.4 to
  0.75 ms before, and the layer builds in 70 to 200 ms instead of 15 to 25 ms. A parchment loading sheet covers the
  build on slower machines.
- The engraved tracks keep a clean copy of the layer, so a battle's layer costs twice its memory (about 38 MB more
  at the largest size).
- The map layer is still scaled to the camera every frame, as before; that blit is most of the frame on a weak GPU.
