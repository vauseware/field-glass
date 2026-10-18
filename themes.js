// The skins, one per war. A skin owns everything that differs between wars: the terrain recipe baked into the layer,
// how units, fire, the fallen and the night are drawn, what lies beyond the map edge, the ambient layers over the map,
// the clock, the legend's swatches, and the chrome (index.html styles `body.theme-<id>`). app.js calls these hooks and
// never asks which skin it has. See docs/adr/0002-per-war-skins.md.
//
// A skin: { id, fonts (stylesheet URL), faces (canvas fonts to load first), kicker, paper (legend ground), night ([r, g, b]
// multiplied over the map at full dark), ring ([halo, line] round the selected unit),
// build(b, terrain, dpr) => sheet { layer, iv, smoke: { sprites, alpha, grow, life }, flash, ... },
// surround(ctx, mapRect, V), feature(g, type, pts, k, closed), placeName(ctx, f, x, y), fallen: { color(side), mark(ctx, x, y, d) },
// unit(ctx, U), label: { place?(l), measure(ctx, l), draw(ctx, l) }, under?(ctx, V), over?(ctx, V), fire?(ctx, V, pops, n),
// ambient(el, sheet), clock(t) => [main html, small], hours?(t), when?(event, b) => [caption time, tag],
// preview?(b) (recolours another war's battle shown in this skin), legend: { text, swatch, extra(b, sheet) } }.
import revolution from './themes/revolution.js';
import ww2 from './themes/ww2.js';

export const THEMES = { revolution, ww2 };

// The skin asked for (the `?theme=` preview), else the battle's `theme`, else its war's by the year: 1939 to 1945 is the
// Second World War, and anything else the Revolution, the other skin built so far.
export function themeFor(b, want = null) {
  const year = +String(b.date ?? '').slice(0, 4);
  return THEMES[want] ?? THEMES[b.theme] ?? (year >= 1939 && year <= 1945 ? THEMES.ww2 : THEMES.revolution);
}
