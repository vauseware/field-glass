// The skins, one per war. A skin owns everything that differs between wars: the terrain recipe baked into the layer,
// how units, fire, the fallen and the night are drawn, what lies beyond the map edge, the ambient layers over the map,
// the clock, the legend's swatches, and the chrome (index.html styles `body.theme-<id>`). app.js calls these hooks and
// never asks which skin it has. See docs/adr/0002-per-war-skins.md.
//
// A skin: { id, fonts (stylesheet URL), faces (canvas fonts to load first), kicker, paper (legend ground), night ([r, g, b]
// multiplied over the map at full dark), ring ([halo, line] round the selected unit),
// build(b, terrain, dpr) => sheet { layer, iv, smoke: { sprites, alpha, grow, life, rate? (share of firing smoke drawn) }, flash, ... },
// surround(ctx, mapRect, V), feature(g, type, pts, k, closed), placeName(ctx, f, x, y), fallen: { color(side), mark(ctx, x, y, d) },
// unit(ctx, U), label: { place?(l), measure(ctx, l), draw(ctx, l) }, under?(ctx, V), over?(ctx, V), fire?(ctx, V, pops, n),
// air?(ctx, V, f, clock, D) (the aircraft of an air strike `f`, D null; or an airborne drop, D its sim.dropAt frame in world
// metres: transports, canopies, gliders and the men walking in; clock is real seconds of play),
// ambient(el, sheet), clock(t) => [main html (its dial, then the time), small], hours?(t), when?(event, b) => caption time,
// time?(t) => the time of day for the chapter list and the tick tip (else "6:30 AM"),
// preview?(b) (recolours another war's battle shown in this skin), legend: { text, swatch, extra(b, sheet) } }.
import revolution from './themes/revolution.js';
import civilWar from './themes/civil-war.js';
import ww2 from './themes/ww2.js';
import ww1 from './themes/ww1.js';
import warOf1812 from './themes/war-of-1812.js';

export const THEMES = { revolution, 'civil-war': civilWar, 'war-of-1812': warOf1812, ww1, ww2 };

// The years each war's skin covers. A battle dated outside every war wears the Revolution's.
const YEARS = [[1812, 1815, warOf1812], [1861, 1865, civilWar], [1914, 1918, ww1], [1939, 1945, ww2]];

// The skin asked for (the `?theme=` preview), else the battle's `theme`, else its war's by the year.
export function themeFor(b, want = null) {
  const year = +String(b.date ?? '').slice(0, 4);
  return THEMES[want] ?? THEMES[b.theme] ?? YEARS.find(([from, to]) => year >= from && year <= to)?.[2] ?? revolution;
}
