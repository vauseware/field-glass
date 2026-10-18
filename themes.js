// The skins, one per war. A skin owns everything that differs between wars: the terrain recipe baked into the layer,
// how units, fire, the fallen and the night are drawn, what lies beyond the map edge, the ambient layers over the map,
// the clock, the legend's swatches, and the chrome (index.html styles `body.theme-<id>`). app.js calls these hooks and
// never asks which skin it has. See docs/adr/0002-per-war-skins.md.
//
// A skin: { id, fonts (stylesheet URL), faces (canvas fonts to load first), kicker, paper (legend ground), night ([r, g, b]
// multiplied over the map at full dark), ring ([halo, line] round the selected unit),
// build(b, terrain, dpr) => sheet { layer, iv, smoke: { sprites, alpha, grow, life }, flash, ... },
// surround(ctx, mapRect, V), feature(g, type, pts, k, closed), placeName(ctx, f, x, y), fallen: { color(side), mark(ctx, x, y, d) },
// unit(ctx, U), label: { measure(ctx, l), draw(ctx, l) }, under?(ctx, V), over?(ctx, V), ambient(el, sheet),
// clock(t) => [main, small], hours?(t), legend: { text, swatch, extra(b, sheet) } }.
import revolution from './themes/revolution.js';

export const THEMES = { revolution };

// The battle's `theme`, else the Revolution's: the only skin built so far.
export const themeFor = b => THEMES[b.theme] ?? THEMES.revolution;
