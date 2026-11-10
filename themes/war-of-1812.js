// The War of 1812: a coastal chart, as Blunt and the Admiralty sold them with a blue paper back. Navy ink on cream; the
// land washed yellow along its shore, the water white and lined, figured with soundings; hills as short hachure
// caterpillars; rhumb lines fanning from a compass rose across the sheet; a graduated border. A unit is a block in its
// side's colour under a navy rule, a pennant on its front; its track is pecked behind it. At night a binnacle lamp
// lights the chart. See docs/adr/0007-war-of-1812-skin.md.
import { tracks, mulberry32, clockParts, MONTHS } from '../sim.js';
import * as P from './paint.js';

export const INK = '#1e2a38', PAPER = '#eee9d8', BACK = '#9fb3bd';
const COAST = '#e6c86a', SEA = '#f6f3ea';
const CASLON = '"Cardo", Georgia, serif';

const feature = (g, type, pts, k, closed) => {
  switch (type) {
    case 'road': P.stroke(g, pts, INK, 3.2 * k, 0.9); P.stroke(g, pts, PAPER, 1.6 * k); break;
    case 'creek': P.stroke(g, pts, INK, 1.1 * k, 0.9); P.stroke(g, pts, INK, 0.5 * k, 0.5, [1, 0]); break;
    case 'fence': P.stroke(g, pts, INK, 0.7 * k, 0.6, [3 * k, 3 * k]); break;
    case 'works': P.stroke(g, pts, INK, 5.5 * k, 0.95); P.stroke(g, pts, COAST, 2.4 * k); break;
    case 'trench': P.stroke(g, pts, INK, 3.5 * k, 0.9); P.stroke(g, pts, COAST, 1.4 * k); break;
    case 'water': P.polyPath(g, pts); g.fillStyle = SEA; g.fill(); P.stroke(g, [...pts, pts[0]], INK, 1.3 * k); break;
    default: if (closed) { // redoubt, battery, ship, camp
      const fill = { ship: INK, camp: 'rgba(238,233,216,0.5)' }[type] ?? COAST;
      P.polyPath(g, pts); g.fillStyle = fill; g.fill();
      if (type !== 'camp' && type !== 'ship') P.rule(g, pts, Math.PI / 4, 2.6 * k, INK, 0.5 * k, 0.6);
      g.save(); if (type === 'camp') g.setLineDash([3 * k, 2 * k]); P.polyPath(g, pts); g.strokeStyle = INK; g.lineWidth = 1.2 * k; g.stroke(); g.restore();
    }
  }
};

// The chart's ground: the land, its coast wash, the hills, woods, water with its soundings, the rhumb lines and the
// features. The start screen draws its War of 1812 backdrop from this (splash.js).
export function ground(b, T) {
  const dem = P.makeDem(b, T), L = P.layerSpace(b, dem), cv = P.canvas(L.size, L.size), g = cv.getContext('2d'), size = L.size;
  g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high';
  // The land: near white, and washed yellow for a band above the water's level, as the chart tints its coast.
  const fw = dem.water == null ? -1 : (dem.water - dem.zmin) / (dem.zmax - dem.zmin || 1), coast = P.hex(COAST), land = P.hex('#ece6d4');
  g.drawImage(P.reliefCanvas(dem, f => (f < fw + 0.06 ? P.mix(coast, land, P.clamp((f - fw) / 0.06, 0, 1)) : land), { k0: 0.88, k1: 0.14 }), 0, 0, size, size);
  for (const poly of b.fields ?? []) { const p = L.pts(poly); g.fillStyle = 'rgba(236,222,180,0.35)'; P.polyPath(g, p); g.fill(); P.stroke(g, [...p, p[0]], INK, 0.7, 0.7, [5, 3]); }
  const iv = P.interval(dem, b.contourInterval ?? 3), hiv = Math.max(0.6, (dem.zmax - dem.zmin) / 30);
  P.hachures(g, dem, L, P.contourLines(dem, hiv), hiv, { step: 3.2, maxLen: 8, minSlope: 0.03, color: INK, wMin: 0.5, wMax: 1.2, aMin: 0.3, aMax: 0.8 });
  g.drawImage(P.woodsSheet(b, L, { lo: 0.3, hi: 0.5, color: [120, 140, 110], alpha: 0.38, edge: 6 }), 0, 0);
  g.strokeStyle = INK; g.lineWidth = 0.7; g.globalAlpha = 0.7; g.beginPath(); // trees as the chart marks them: a ring on a stem
  for (const [x, y] of P.treePoints(b, dem, L, { scale: 0.8, lo: 0.3, hi: 0.5 })) { g.moveTo(x + 2.2, y); g.arc(x, y, 2.2, 0, 7); g.moveTo(x, y + 2.2); g.lineTo(x, y + 5); }
  g.stroke(); g.globalAlpha = 1;
  P.water(g, b, dem, L, { fill: SEA, line: INK, lw: 1.4, liningColor: INK, lining: [[3, 0.5], [6, 0.36], [9.5, 0.24], [14, 0.14], [20, 0.08]] });
  if (dem.water != null) { // soundings in fathoms, figured in italic across the water
    const rnd = mulberry32(31); g.fillStyle = INK; g.font = `italic 11px ${CASLON}`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.globalAlpha = 0.8;
    for (let i = 0; i < 2600; i++) {
      const x = rnd() * size, y = rnd() * size, wx = L.wx(x), wy = L.wy(y), z = dem.sample(dem.Z, wx, wy);
      if (z > dem.water || z > dem.sample(dem.Z, wx + 60, wy) || z > dem.sample(dem.Z, wx, wy + 60)) continue;
      g.fillText(String(2 + Math.floor(rnd() * 7)), x, y);
    }
    g.globalAlpha = 1;
  }
  { // rhumb lines from a rose placed off the middle of the sheet
    const cx = size * 0.68, cy = size * 0.3; g.strokeStyle = INK; g.lineWidth = 0.6; g.beginPath();
    for (let i = 0; i < 32; i++) { const a = (i / 32) * Math.PI * 2; g.moveTo(cx, cy); g.lineTo(cx + Math.cos(a) * size * 1.5, cy + Math.sin(a) * size * 1.5); }
    g.globalAlpha = 0.16; g.stroke(); g.globalAlpha = 1;
  }
  P.bakeFeatures(g, b, L, feature, ['creek', 'road', 'fence', 'works', 'trench', 'redoubt', 'battery', 'ship', 'camp']);
  return { layer: cv, iv, L };
}

function build(b, T, dpr) {
  const { layer: cv, iv, L } = ground(b, T);
  const views = b.events.map(e => e.view ?? b.extent * 0.6).sort((p, r) => p - r), q = Math.max(0.7, (L.pxm * (views[views.length >> 1] ?? b.extent)) / 1100);
  const bySide = new Map();
  for (const u of b.units) { if (!bySide.has(u.side)) bySide.set(u.side, []); bySide.get(u.side).push({ u, runs: tracks(u) }); }
  const pecked = (c, side, k, fresh) => { const s = q * k; c.setLineDash([3 * s, 3 * s]); c.lineWidth = 1 * s; c.strokeStyle = b.sides[side].color; c.globalAlpha = fresh ? 0.85 : 0.4; };
  return {
    layer: cv, iv, tracks: P.plate(cv, L, bySide, 900, pecked), rose: rose(dpr),
    smoke: { sprites: [1, 2, 3, 4].map(s => P.puffSprite(64, s, '246,243,236', '160,165,170')), alpha: 0.75, grow: 1.7, life: 1.6 },
    flash: P.glowSprite(24, [[0, 'rgba(255,255,235,1)'], [0.25, 'rgba(255,214,120,0.95)'], [0.6, 'rgba(230,120,40,0.35)'], [1, 'rgba(200,80,20,0)']]),
  };
}

// A sixteen-point rose in navy ink with a fleur-de-lis north, as the chart engravers cut them.
export function rose(dpr) {
  return P.sprite(Math.round(150 * dpr), g => {
    g.scale(dpr, dpr); const c = 75, R = 58; g.strokeStyle = INK; g.fillStyle = INK; g.lineWidth = 1;
    g.beginPath(); g.arc(c, c, R, 0, 7); g.stroke(); g.beginPath(); g.arc(c, c, R - 4, 0, 7); g.stroke();
    for (let i = 0; i < 32; i++) { const a = (i / 32) * 6.283; g.beginPath(); g.moveTo(c + Math.cos(a) * (R - 4), c + Math.sin(a) * (R - 4)); g.lineTo(c + Math.cos(a) * (R - (i % 4 ? 8 : 12)), c + Math.sin(a) * (R - (i % 4 ? 8 : 12))); g.stroke(); }
    const point = (a, len, w, solid) => {
      const tip = [c + Math.cos(a) * len, c + Math.sin(a) * len], l = [c + Math.cos(a - Math.PI / 2) * w, c + Math.sin(a - Math.PI / 2) * w], r = [c + Math.cos(a + Math.PI / 2) * w, c + Math.sin(a + Math.PI / 2) * w];
      g.beginPath(); g.moveTo(c, c); g.lineTo(...l); g.lineTo(...tip); g.closePath(); if (solid) g.fill(); else g.stroke();
      g.beginPath(); g.moveTo(c, c); g.lineTo(...r); g.lineTo(...tip); g.closePath(); if (solid) g.stroke(); else g.fill();
    };
    for (let i = 0; i < 8; i++) point(Math.PI / 8 + (i * Math.PI) / 4, R * 0.42, 3, i % 2 === 0);
    for (let i = 0; i < 4; i++) point(Math.PI / 4 + (i * Math.PI) / 2, R * 0.62, 5, true);
    for (let i = 0; i < 4; i++) point(-Math.PI / 2 + (i * Math.PI) / 2, R - 12, 7, true);
    g.beginPath(); g.moveTo(c, 2); g.bezierCurveTo(c - 7, 6, c - 7, 13, c, 13); g.bezierCurveTo(c + 7, 13, c + 7, 6, c, 2); g.fill();
    g.beginPath(); g.arc(c, c, 3, 0, 7); g.fillStyle = PAPER; g.fill(); g.stroke();
  });
}

const strips = (ctx, l, t, r, b, V, c) => { ctx.fillStyle = c; ctx.fillRect(0, 0, V.W, Math.max(0, t)); ctx.fillRect(0, b, V.W, Math.max(0, V.H - b)); ctx.fillRect(0, t, Math.max(0, l), b - t); ctx.fillRect(r, t, Math.max(0, V.W - r), b - t); };

function over(ctx, V) {
  const yd = 0.9144 * V.z, len = [50, 100, 200, 250, 500, 1000, 2000, 5000].findLast(n => n * yd <= 170) ?? 50, w = len * yd;
  const corner = P.freeCorner(V, 190, 230);
  if (!corner) return;
  const x0 = corner[0] - 10 - Math.max(w, 150) / 2 - w / 2, y0 = corner[1] - 26;
  for (let i = 0; i < 10; i++) { ctx.fillStyle = i % 2 ? PAPER : INK; ctx.fillRect(x0 + (i * w) / 10, y0, w / 10, 4); }
  ctx.strokeStyle = INK; ctx.lineWidth = 1; ctx.strokeRect(x0, y0, w, 4);
  const t = (s, x, y, f) => P.haloText(ctx, s, x, y, f, INK, 'rgba(238,233,216,0.85)', 3.5);
  t('0', x0, y0 + 15, `italic 12px ${CASLON}`); t(String(len), x0 + w, y0 + 15, `italic 12px ${CASLON}`); t('Scale of Yards', x0 + w / 2, y0 - 11, `italic 15px ${CASLON}`);
  ctx.drawImage(V.sheet.rose, x0 + w / 2 - 75, y0 - 186, 150, 150);
}

// A unit as a solid block in its side's colour under a navy rule, with a pennant on its front.
function unit(ctx, U) {
  const { w, h, side } = U;
  ctx.save(); ctx.translate(U.x, U.y); ctx.rotate(U.a);
  ctx.globalAlpha = U.rout ? 0.5 : 1;
  ctx.fillStyle = U.gone ? '#a4a39c' : U.mil ? side.light ?? side.color : side.color; ctx.fillRect(-w / 2, -2, w, h + 3);
  ctx.lineWidth = 1.1; ctx.strokeStyle = INK; ctx.strokeRect(-w / 2, -2, w, h + 3);
  ctx.fillStyle = INK; ctx.fillRect(-w / 2, -3.5, w, 2.5);
  if (!U.gone) { const l = U.go ? 12 : 8; ctx.beginPath(); ctx.moveTo(0, -3.5); ctx.lineTo(0, -3.5 - l); ctx.stroke(); ctx.beginPath(); ctx.moveTo(0, -3.5 - l); ctx.lineTo(7, -1.5 - l); ctx.lineTo(0, 0.5 - l); ctx.closePath(); ctx.fill(); }
  if (U.art) for (const x of P.gunXs(U)) { ctx.fillRect(x - 1.6, -12, 3.2, 12); ctx.beginPath(); ctx.arc(x, 1, 3.6, 0, 7); ctx.fill(); }
  ctx.restore();
  P.menDots(ctx, U, U.gone ? '#e8e6de' : '#f6f2e6');
}

const period = h => (h < 5 || h >= 21 ? 'at night' : h < 12 ? 'in the morning' : h < 17 ? 'in the afternoon' : 'in the evening');

export default {
  id: 'war-of-1812',
  fonts: 'https://fonts.googleapis.com/css2?family=Cardo:ital,wght@0,400;0,700;1,400&display=swap',
  faces: [`italic 11px ${CASLON}`, `15px ${CASLON}`, `700 15px ${CASLON}`],
  kicker: 'A Chart of the',
  paper: PAPER,
  night: [86, 104, 122],
  ring: ['rgba(238,233,216,0.95)', '#b3331f'],
  build,
  feature,
  preview(b) { const ids = Object.keys(b.sides); ids.forEach((id, i) => Object.assign(b.sides[id], i === ids.length - 1 ? { color: '#b3331f', light: '#d87a68', dark: '#5a150c' } : { color: '#27497f', light: '#6f8fc4', dark: '#12254a' })); },
  surround(ctx, r, V) { // the sheet, its graduated border, and the blue back beyond
    if (r.l <= 0 && r.t <= 0 && r.r >= V.W && r.b >= V.H) return;
    strips(ctx, r.l, r.t, r.r, r.b, V, PAPER); strips(ctx, r.l - 30, r.t - 30, r.r + 30, r.b + 30, V, BACK);
    ctx.strokeStyle = INK; ctx.lineWidth = 1; ctx.strokeRect(r.l - 4, r.t - 4, r.r - r.l + 8, r.b - r.t + 8); ctx.strokeRect(r.l - 12, r.t - 12, r.r - r.l + 24, r.b - r.t + 24);
    for (let x = r.l - 4, i = 0; x < r.r + 4; x += 24, i++) { ctx.fillStyle = i % 2 ? INK : PAPER; const w = Math.min(24, r.r + 4 - x); ctx.fillRect(x, r.t - 12, w, 8); ctx.fillRect(x, r.b + 4, w, 8); }
    for (let y = r.t - 4, i = 0; y < r.b + 4; y += 24, i++) { ctx.fillStyle = i % 2 ? INK : PAPER; const h = Math.min(24, r.b + 4 - y); ctx.fillRect(r.l - 12, y, 8, h); ctx.fillRect(r.r + 4, y, 8, h); }
  },
  placeName(ctx, f, x, y) {
    const font = `${f.rot ? 'italic ' : ''}15px ${CASLON}`;
    P.haloText(ctx, f.name, x, y, font, INK, 'rgba(238,233,216,0.8)', 3.5, (-(f.rot ?? 0) * Math.PI) / 180);
    ctx.font = font; return ctx.measureText(f.name).width;
  },
  unit,
  label: {
    measure: (ctx, l) => { ctx.font = `700 ${l.size}px ${CASLON}`; return [ctx.measureText(l.text).width + 8, l.size + 4]; },
    draw: (ctx, l) => P.haloText(ctx, l.text, l.x, l.y, `700 ${l.size}px ${CASLON}`, INK, 'rgba(238,233,216,0.92)', 4.5),
  },
  under: (ctx, V) => V.sheet.tracks(ctx, V), // the chart pecks where every unit has been
  fallen: { color: s => s.dark ?? INK, mark(ctx, x, y, d) { const k = d * 0.55; ctx.moveTo(x - k, y - k); ctx.lineTo(x + k, y + k); ctx.moveTo(x + k, y - k); ctx.lineTo(x - k, y + k); } },
  over,
  ambient(el) {
    el.innerHTML = '<div class="paper"></div><div class="binnacle"></div>';
    el.firstChild.style.backgroundImage = `${P.grainURL(256, 13, [40, 48, 60], r => r * 22)}, var(--vignette)`;
  },
  clock(t) {
    const { h, m, day, month } = clockParts(t);
    return [`${h % 12 || 12}:${String(m).padStart(2, '0')}`, day == null ? period(h) : `${day} ${MONTHS[month]}, ${period(h).replace(/^in the /, '')}`];
  },
  hours(t) { // the scale of hours under the scrubber
    const { h, day, month } = clockParts(t);
    if (h === 0 && day != null) return `${day} ${MONTHS[month]}`;
    return h === 12 ? 'noon' : h === 0 ? 'midnight' : `${h % 12} o’clock`;
  },
  legend: {
    text: {
      infantry: b => `Infantry, a block in its side’s colour under a pennant. Each pale dot is ${b.menPerDot} men; the rows are ranks.`,
      fallen: b => `Where men fell: a small cross for every ${b.menPerDot} men a unit lost, in that side’s colour.`,
      contours: () => 'Hills as the chart shows them: short hachures where the ground rises. The yellow wash is the coast; the figures in the water are soundings in fathoms.',
      woods: () => 'Woods, marked with the chart’s tree sign.',
    },
    swatch: {
      woods: g => { g.fillStyle = 'rgba(120,140,110,0.25)'; g.fillRect(2, 3, 60, 22); g.strokeStyle = INK; g.lineWidth = 0.7; g.beginPath(); for (const [x, y] of [[10, 10], [22, 16], [34, 8], [46, 15], [56, 10]]) { g.moveTo(x + 2.2, y); g.arc(x, y, 2.2, 0, 7); g.moveTo(x, y + 2.2); g.lineTo(x, y + 5); } g.stroke(); },
      contours: g => { g.fillStyle = COAST; g.fillRect(0, 2, 30, 24); g.fillStyle = '#ece6d4'; g.fillRect(30, 2, 34, 24); g.strokeStyle = INK; g.lineWidth = 0.8; g.beginPath(); for (let x = 34; x < 62; x += 3.2) { g.moveTo(x, 9); g.lineTo(x + 1, 18); } g.stroke(); },
      water: g => { g.fillStyle = SEA; g.fillRect(0, 12, 64, 16); [15, 18, 21.5].forEach((y, i) => P.stroke(g, [[0, y], [64, y]], INK, 0.6, 0.5 - i * 0.12)); P.stroke(g, [[0, 12], [64, 12]], INK, 1.4); g.fillStyle = INK; g.font = `italic 10px ${CASLON}`; g.textAlign = 'center'; g.fillText('4', 20, 27); g.fillText('6', 44, 27); },
      field: g => { const p = [[8, 3], [62, 3], [62, 26], [8, 26]]; g.fillStyle = 'rgba(236,222,180,0.5)'; P.polyPath(g, p); g.fill(); P.stroke(g, [...p, p[0]], INK, 0.7, 0.7, [5, 3]); },
    },
    extra: () => [[(g, s) => { g.setLineDash([3, 3]); g.lineWidth = 1; g.strokeStyle = s.color; g.globalAlpha = 0.85; g.beginPath(); g.moveTo(4, 22); g.bezierCurveTo(20, 22, 30, 8, 46, 10); g.stroke(); g.setLineDash([]); g.globalAlpha = 1; g.fillStyle = s.color; g.fillRect(46, 4, 14, 10); g.strokeStyle = INK; g.strokeRect(46, 4, 14, 10); },
      'The pecked line is where each unit has been since the battle began.']],
  },
};
