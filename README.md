# Field Glass

A browser app that replays historical battles from the written record. Regiment-sized units follow
keyframed timelines on real terrain; the viewer pans, zooms and scrubs time. Nothing is simulated
that would change the outcome. Built for a laptop with integrated graphics.

![The start screen](docs/screenshots/start-screen.png)

The start screen lists every battle with its running time and draws one of them, at random, as a sepia
battle plan from its own terrain and troop positions. `npm run check` measures each running time by playing
the battle through at the default settings (Follow and Time-lapse on, chapter speeds honoured) and writes it
to `battles/index.json`. A link with a battle in it (`#cowpens`) skips the start screen; `?plan=yorktown`
picks the backdrop.

![Cowpens, the main line engaged](docs/screenshots/cowpens-main-line.jpg)
![Kings Mountain, the columns close round the ridge](docs/screenshots/kings-mountain-noose.jpg)
![Guilford Courthouse, the first line](docs/screenshots/guilford-first-line.jpg)
![The Waxhaws, the charge](docs/screenshots/waxhaws-charge.jpg)
![Yorktown, the night of 14 October](docs/screenshots/yorktown-redoubts.jpg)
![Bunker Hill, the first assault](docs/screenshots/bunker-hill-first-assault.jpg)
![Princeton, the orchard](docs/screenshots/princeton-orchard.jpg)

Battles so far: Bunker Hill (17 June 1775), Trenton and Princeton (25 December 1776 to 3 January 1777), the Waxhaws (29 May 1780), Kings Mountain (7 October 1780), Cowpens (17 January 1781),
Guilford Courthouse (15 March 1781) and the siege of Yorktown (28 September to 19 October 1781).

## Run locally

```
npm run serve      # python3 -m http.server 8000
open http://localhost:8000/#cowpens
npm run check      # validates every battle and self-checks sim.js
```

On claw-mini the launch agent `com.vauseware.battle-sim` serves this folder on 127.0.0.1:8803 and
`tailscale serve --https=8803` proxies it, so the tailnet URL is https://claw-mini.tailcaa12e.ts.net:8803/.

## Deploy

`npm run deploy` copies the page, `app.js`, `sim.js`, the skins and each battle's `battle.json` and `terrain.json`
into `dist/` (`tools/build.sh`) and uploads it as the Worker `fieldglass`, served at https://fieldglass.vause.io/.
The vause.io zone redirects only the bare domain and www to vauseware.com.

Static files only. `index.html` is the shell, `app.js` runs the camera, the clock and the panels, the skins in
`themes/` draw, `sim.js` is the DOM-free timeline logic. `#cowpens@07:45` opens a battle at a time of day
(`#yorktown@1781-10-14T20:00` for a dated one); `#cowpens@07:45,play` starts it playing. `,warp` pre-runs five
seconds of frames, which is how headless screenshots see smoke and the camera; `,select=howard` opens a unit's card;
`,legend` opens the legend.

The chapters sit above the scrubber as ticks, their titles slanting up over the map on leader lines
so crowded chapters can be spread apart: click one to jump there (the camera follows again). **Legend** in the
top panel lists only the symbols the current battle uses. The story panel opens at each new chapter with the chapter's approximate hour; **Hide** folds it to the title. **Outcome** in the top panel opens to the result and each side's losses (`outcome` in `make.py`).
Every unit carries its name when there is
room; labels that would overlap are dropped, biggest unit first.

## Skins

Each war gets its own look, a skin (`themes.js`, with the drawing in `themes/`). A skin owns the terrain baked into
the map layer, how units, fire, the fallen and the night are drawn, what shows beyond the map edge, the ambient layers
over the map, the clock, the legend's swatches and the panels' dress (`body.theme-<id>` in `index.html`). A battle
wears the skin its `theme` field names, and the Revolution skin when it names none.

Only the Revolution skin is built: an engraved and hand-coloured plan on laid paper. Hachures shade the slopes, woods
are clumped engraved canopies, fields are ruled with furrows, fences zig-zag, creeks and shores are water-lined, and a
compass rose and scale of yards sit in a free corner. Each unit's path is engraved behind it as the battle plays, the
last quarter hour darker than the rest. At night an umber dark falls over the map and a candle lights its middle. The
scrubber is ruled as a scale of hours. Drifting cloud shadows, paper grain and the candle are page layers the browser
composites, so the map canvas never redraws them.

Two more skins are chosen and deferred until a battle of their war arrives: the Civil War as a topographical
engineer's survey (brown contours in feet, scalloped woods, red-ochre roads, units ruled into companies under small
flags), and the Second World War as a recon photo mosaic on a lamp-lit operations table (painted counters, chinagraph
frontages and advance arrows, a 1 km grid). See `docs/adr/0002-per-war-skins.md`.

`,bench` on a link measures the cost of a frame; `bash tools/bench.sh 'guilford@14:02,play,warp'` runs it in headless
Chrome and prints milliseconds per frame and the time the layer took to build.

**Time-lapse** (on by default, key `t`) hurries through stretches where nothing moves: the clock runs
at the battle's `lapse` rate until 90 seconds before the next movement, appearance or fight. A siege
bombardment does not count as movement, so Yorktown's days of gunnery pass in seconds.

## Add a battle

1. Add `battles/<id>/battle.json` and list it in `battles/index.json` with `id`, `name`, `date`
   (ISO) and `war`; the selector sorts by date and groups by war. Each existing battle is
   generated by its `make.py`, which is the easier way to author a timeline: edit it, run it, check.
2. Fetch terrain: `python3 tools/fetch_terrain.py LAT LON HALF_METRES COLS battles/<id>/terrain.json`.
   HALF_METRES must be half of `extent` in battle.json. US battlefields come from USGS 3DEP at 10 m.
   Elsewhere add `--copernicus` for the Copernicus GLO-30 surface model at 30 m, and put its licence
   credit (the `source` in terrain.json) in the battle's `sources`.
3. `npm run check`.

### battle.json

Coordinates are metres from `origin` (the lat/lon at the map centre): x east, y north. Headings are
compass degrees. Times are the local clock, `HH:MM`, or `YYYY-MM-DD HH:MM` for a battle that runs more
than a day; one battle uses one form throughout.

| field | meaning |
|---|---|
| `extent` | map width and height in metres, centred on `origin` |
| `theme` | the skin (`themes.js`); `revolution`, the default, is the only one so far |
| `start`, `end`, `sunrise`, `sunset` | battle clock; the map is tinted before sunrise and, if `sunset` is given, every night |
| `speed`, `lapse` | default playback multiplier, and the multiplier for quiet stretches under time-lapse (default `speed × 6`) |
| `water` | elevation in metres at or below which the DEM is drawn as water (rivers are flattened to about 0) |
| `menPerDot` | men per drawn dot (5 for a small battle, 10 or 20 for a large one) |
| `sides` | `{ id: { name, color, light, dark } }` |
| `units[]` | `id, side, name, short?, commander, type, strength, guns?, loose?, ranks?, keys[]`; `short` is the map label; `loose` keeps a unit in open order; `ranks` defaults to 2 |
| `keys[]` | `{ t, x, y, h, state, strength }`; omitted fields carry forward from the previous key |
| `events[]` | `{ t, title, text, at: [x, y], view, speed, when }` captions; the story gives `t` to the nearest hour ("About 3 PM") unless `when` holds a time the sources record; `at` and `view` (metres across) steer the auto-camera; `speed` sets the playback rate for that chapter while Follow is on (each chapter resets to the battle's `speed`) |
| `features[]` | `{ type: road|creek|fence|works|trench, name, pts }` lines, `{ type: redoubt|battery|ship|camp|water, poly }` polygons (`water` draws a shoreline the modern ground no longer shows), `{ type: smoke, at, rate, spread }` a burning town or ship, `{ type: airstrike, at, spread, h, from, until }` aircraft bombing round `at` (radius `spread` m, flying on heading `h`), cosmetic like smoke, or `{ name, at, rot }` labels; `from` and `until` show a feature only between those times, which is how siege lines get dug |
| `tints[]` | `{ from, until, color }` weather washes over the whole map, such as a snowstorm, fading in and out over ten minutes |
| `trees` | `density` in trees per square metre; `clear` is a list of polygons left bare, such as a summit |
| `fields` | polygons of cleared farmland, tinted lighter and kept free of trees |
| `sources[]` | shown in the Sources dialog |

Unit types: `infantry`, `light_infantry`, `militia`, `riflemen`, `cavalry`, `artillery`, `armor`.
An `armor` unit's `strength` counts vehicles, not men: one dot per vehicle whatever `menPerDot` is, about
50 m apart in line and 30 m apart in column, and a casualty marker for each vehicle lost.
States: `hidden`, `column`, `line`, `skirmish`, `firing`, `charge`, `retreat`, `rout`, `surrender`.
A `firing` or `skirmish` state makes the unit smoke; a falling `strength` leaves casualty markers.
Positions between keys are straight-line interpolation, so add keys where a unit follows a road.
