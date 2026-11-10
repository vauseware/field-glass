// The First World War: a 1:10,000 trench map, as the Ordnance Survey and the AEF printed them. Cream paper, brown
// contours, woods as ring-on-stalk tree signs, and a squared grid of 1000-yard squares numbered 1 to 36 inside lettered
// 6000-yard squares. Trenches and works in red, stepped into fire bays and traverses, with wire as crosses before them.
// A unit is a block in its side's colour under an ink rule; its track is dashed behind it. At night a star shell
// lights the field. See docs/adr/0008-first-world-war-skin.md.
import { tracks, clockParts, MONTHS } from '../sim.js';
import * as P from './paint.js';

export const INK = '#1f1d1a', PAPER = '#f2eee2', RED = '#c3162b';
const BROWN = '#8a5a30', GREEN = '#5f7f3c', WATER = '#b9d0dd', BLUE = '#2f6f9f';
const ROMAN = '"Crimson Pro", Georgia, serif', SANS = '"Archivo Narrow", "Arial Narrow", sans-serif';
const YD = 0.9144, SQUARE = 1000 * YD, LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWX';

// A trench trace: the line stepped from side to side, so its runs are the fire bays and its steps the traverses.
const bays = (pts, step, d) => {
  const q = P.densify(pts, step), n = P.normals(q), out = [];
  q.forEach((p, i) => { const s = (i % 2 ? 1 : -1) * d; out.push([p[0] + n[i][0] * s, p[1] + n[i][1] * s], [p[0] - n[i][0] * s, p[1] - n[i][1] * s]); });
  return out;
};
const wire = (g, pts, k) => {
  const q = P.densify(pts, 9 * k), n = P.normals(q), r = 2 * k;
  g.save(); g.strokeStyle = INK; g.lineWidth = 0.7 * k; g.globalAlpha = 0.7; g.beginPath();
  q.forEach((p, i) => { const x = p[0] + n[i][0] * 9 * k, y = p[1] + n[i][1] * 9 * k; g.moveTo(x - r, y - r); g.lineTo(x + r, y + r); g.moveTo(x + r, y - r); g.lineTo(x - r, y + r); });
  g.stroke(); g.restore();
};
// Every works and trench is red: features carry no side, so the map cannot tell whose line it is.
export const feature = (g, type, pts, k, closed) => {
  switch (type) {
    case 'road': P.stroke(g, pts, INK, 5 * k, 0.85); P.stroke(g, pts, '#e8b866', 3.4 * k); break;
    case 'creek': P.stroke(g, pts, BLUE, 1.6 * k, 0.9); break;
    case 'fence': P.stroke(g, pts, INK, 0.6 * k, 0.5, [2 * k, 2 * k]); break;
    case 'works': case 'trench': P.stroke(g, bays(pts, 7 * k, 3.4 * k), RED, 2.2 * k, 0.95); wire(g, pts, k); break;
    case 'water': P.polyPath(g, pts); g.fillStyle = WATER; g.fill(); P.stroke(g, [...pts, pts[0]], BLUE, 1.2 * k); break;
    default: if (closed) { // redoubt, battery, ship, camp
      const ship = type === 'ship';
      P.polyPath(g, pts); g.fillStyle = ship ? INK : type === 'camp' ? 'rgba(31,29,26,0.06)' : 'rgba(195,22,43,0.15)'; g.fill();
      g.save(); if (type === 'camp') g.setLineDash([3 * k, 2 * k]); P.stroke(g, [...pts, pts[0]], ship || type === 'camp' ? INK : RED, 1.4 * k); g.restore();
    }
  }
};

// The squared grid: 1000-yard squares numbered 1 to 36 within lettered 6000-yard squares, from the sheet's top left.
function grid(g, b, L, size) {
  const E = b.extent, x0 = -E / 2, n = Math.ceil(E / SQUARE) + 1, cols = Math.ceil(n / 6);
  g.save(); g.strokeStyle = INK; g.fillStyle = INK; g.textAlign = 'center'; g.textBaseline = 'middle';
  for (let i = 0; i <= n; i++) {
    const big = i % 6 === 0; g.lineWidth = big ? 1.6 : 0.6; g.globalAlpha = big ? 0.8 : 0.5;
    g.beginPath(); g.moveTo(L.x(x0 + i * SQUARE), 0); g.lineTo(L.x(x0 + i * SQUARE), size); g.moveTo(0, L.y(E / 2 - i * SQUARE)); g.lineTo(size, L.y(E / 2 - i * SQUARE)); g.stroke();
  }
  g.globalAlpha = 0.75; const fs = Math.max(11, L.pxm * 60);
  for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) {
    g.font = `${fs}px ${SANS}`; g.fillText(String((r % 6) * 6 + (c % 6) + 1), L.x(x0 + (c + 0.5) * SQUARE), L.y(E / 2 - (r + 0.5) * SQUARE));
    if (r % 6 === 0 && c % 6 === 0) { g.font = `700 ${fs * 3}px ${SANS}`; g.fillText(LETTERS[((r / 6) * cols + c / 6) % 24], L.x(x0 + c * SQUARE + SQUARE * 0.7), L.y(E / 2 - r * SQUARE - SQUARE * 0.7)); }
  }
  g.restore();
}

// The map's ground: paper, a faint relief, field boundaries, contours, woods and their tree signs, water, the features
// and the grid. The start screen draws its First World War backdrop from this (splash.js).
export function ground(b, T) {
  const dem = P.makeDem(b, T), L = P.layerSpace(b, dem), cv = P.canvas(L.size, L.size), g = cv.getContext('2d'), size = L.size;
  g.fillStyle = PAPER; g.fillRect(0, 0, size, size);
  g.globalCompositeOperation = 'multiply'; g.globalAlpha = 0.35;
  g.drawImage(P.reliefCanvas(dem, () => [255, 250, 238], { k0: 0.82, k1: 0.2 }), 0, 0, size, size);
  g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1;
  for (const poly of b.fields ?? []) { const p = L.pts(poly); P.stroke(g, [...p, p[0]], INK, 0.6, 0.45); }
  const iv = P.interval(dem, b.contourInterval ?? 2.5);
  for (const { lv, pts } of P.contourLines(dem, iv)) { const major = Math.round(lv / iv) % 4 === 0; P.stroke(g, P.densify(pts.map(([c, r]) => [L.gx(c), L.gy(r)]), 6), BROWN, major ? 1.1 : 0.6, major ? 0.75 : 0.5); }
  g.drawImage(P.woodsSheet(b, L, { lo: 0.3, hi: 0.5, color: [120, 150, 90], alpha: 0.18 }), 0, 0);
  g.strokeStyle = GREEN; g.lineWidth = 0.8; g.beginPath(); // the tree sign: a small ring on a stalk
  for (const [x, y] of P.treePoints(b, dem, L, { scale: 0.5, lo: 0.3, hi: 0.5 })) { g.moveTo(x + 2.4, y); g.arc(x, y, 2.4, 0, 7); g.moveTo(x, y + 2.4); g.lineTo(x, y + 4.6); }
  g.stroke();
  P.water(g, b, dem, L, { fill: WATER, line: BLUE, lw: 1.2 });
  P.bakeFeatures(g, b, L, feature, ['creek', 'road', 'fence', 'works', 'trench', 'redoubt', 'battery', 'ship', 'camp']);
  grid(g, b, L, size);
  return { layer: cv, iv, L };
}

function build(b, T) {
  const { layer: cv, iv, L } = ground(b, T);
  const views = b.events.map(e => e.view ?? b.extent * 0.6).sort((p, r) => p - r), q = Math.max(0.7, (L.pxm * (views[views.length >> 1] ?? b.extent)) / 1100);
  const bySide = new Map();
  for (const u of b.units) { if (!bySide.has(u.side)) bySide.set(u.side, []); bySide.get(u.side).push({ u, runs: tracks(u) }); }
  const dashed = (c, side, k, fresh) => { const s = q * k; c.setLineDash([5 * s, 3 * s]); c.lineWidth = 1.1 * s; c.strokeStyle = b.sides[side].color; c.globalAlpha = fresh ? 0.85 : 0.35; };
  return {
    layer: cv, iv, tracks: P.plate(cv, L, bySide, 900, dashed),
    smoke: { sprites: [1, 2, 3, 4].map(s => P.puffSprite(64, s + 30, '238,236,228', '150,146,138')), alpha: 0.85, grow: 2, life: 1.8 },
    flash: P.glowSprite(24, [[0, 'rgba(255,255,235,1)'], [0.25, 'rgba(255,214,120,0.95)'], [0.6, 'rgba(230,120,40,0.35)'], [1, 'rgba(200,80,20,0)']]),
  };
}

// The scale bar in yards on a patch of paper, so it reads over the grid figures and the night, in a free corner.
function over(ctx, V) {
  const yd = YD * V.z, len = [100, 200, 500, 1000, 2000, 5000].findLast(n => n * yd <= 200) ?? 100, w = len * yd, c = P.freeCorner(V, 240, 90);
  if (!c) return;
  const x0 = c[0] - 20 - w, y0 = c[1] - 30;
  ctx.fillStyle = 'rgba(242,238,226,0.9)'; ctx.fillRect(x0 - 16, y0 - 44, w + 32, 74);
  for (let i = 0; i < 10; i++) { ctx.fillStyle = i % 2 ? PAPER : INK; ctx.fillRect(x0 + (i * w) / 10, y0 - 4, w / 10, 4); }
  ctx.strokeStyle = INK; ctx.lineWidth = 1; ctx.strokeRect(x0, y0 - 4, w, 4);
  ctx.fillStyle = INK; ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic'; ctx.font = `13px ${SANS}`; ctx.letterSpacing = '2px';
  ctx.fillText('SCALE 1:10,000', x0 + w / 2, y0 - 28); ctx.letterSpacing = '0px'; ctx.font = `italic 13px ${ROMAN}`; ctx.fillText(`${len} Yards`, x0 + w / 2, y0 + 16);
}

// A unit as the map's overprint shows it: a block in its side's colour, the front rank in ink, its men as pale dots.
function unit(ctx, U) {
  const { w, h, side } = U;
  ctx.save(); ctx.translate(U.x, U.y); ctx.rotate(U.a); ctx.globalAlpha = U.rout ? 0.5 : 1;
  ctx.fillStyle = U.gone ? '#a8a69e' : U.mil ? side.light ?? side.color : side.color; ctx.fillRect(-w / 2, -2, w, h + 3);
  ctx.lineWidth = 1; ctx.strokeStyle = INK; ctx.strokeRect(-w / 2, -2, w, h + 3); ctx.fillStyle = INK; ctx.fillRect(-w / 2, -3.5, w, 2.5);
  if (U.go && !U.gone) { ctx.beginPath(); ctx.moveTo(-5, -3.5); ctx.lineTo(0, -12); ctx.lineTo(5, -3.5); ctx.fill(); }
  if (U.art) for (const x of P.gunXs(U)) { ctx.fillRect(x - 1.6, -12, 3.2, 12); ctx.beginPath(); ctx.arc(x, 1, 3.4, 0, 7); ctx.fill(); }
  ctx.restore(); P.menDots(ctx, U, U.gone ? '#ece9e0' : '#f5f2ea');
}

const trees = g => { g.strokeStyle = GREEN; g.lineWidth = 0.8; g.beginPath(); for (const [x, y] of [[10, 10], [22, 17], [34, 9], [46, 16], [56, 10]]) { g.moveTo(x + 2.4, y); g.arc(x, y, 2.4, 0, 7); g.moveTo(x, y + 2.4); g.lineTo(x, y + 4.6); } g.stroke(); };
const ampm = h => (h < 12 ? 'a.m.' : 'p.m.');

export default {
  id: 'ww1',
  fonts: 'https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,400;0,600;1,400&family=Archivo+Narrow:wght@400;700&display=swap',
  faces: [`13px ${SANS}`, `700 33px ${SANS}`, `italic 13px ${ROMAN}`, `15px ${ROMAN}`, `italic 15px ${ROMAN}`, `600 15px ${ROMAN}`],
  kicker: 'Trench Map',
  paper: PAPER,
  night: [80, 84, 96],
  ring: ['rgba(242,238,226,0.95)', RED],
  build,
  feature,
  preview(b) { const ids = Object.keys(b.sides); ids.forEach((id, i) => Object.assign(b.sides[id], i === ids.length - 1 ? { color: '#c3162b', light: '#e0707c', dark: '#5e0a14' } : { color: '#2a55a0', light: '#7090c8', dark: '#132a52' })); },
  surround(ctx, r, V) { // the sheet's margin and its neatline
    if (r.l <= 0 && r.t <= 0 && r.r >= V.W && r.b >= V.H) return;
    ctx.fillStyle = PAPER; ctx.fillRect(0, 0, V.W, r.t); ctx.fillRect(0, r.b, V.W, V.H - r.b); ctx.fillRect(0, r.t, r.l, r.b - r.t); ctx.fillRect(r.r, r.t, V.W - r.r, r.b - r.t);
    ctx.strokeStyle = INK; ctx.lineWidth = 1.5; ctx.strokeRect(r.l - 3, r.t - 3, r.r - r.l + 6, r.b - r.t + 6);
  },
  placeName(ctx, f, x, y) {
    const font = `${f.rot ? 'italic ' : ''}15px ${ROMAN}`;
    P.haloText(ctx, f.name, x, y, font, INK, 'rgba(242,238,226,0.85)', 3.5, (-(f.rot ?? 0) * Math.PI) / 180);
    ctx.font = font; return ctx.measureText(f.name).width;
  },
  unit,
  label: {
    measure: (ctx, l) => { ctx.font = `600 ${l.size}px ${ROMAN}`; return [ctx.measureText(l.text).width + 8, l.size + 4]; },
    draw: (ctx, l) => P.haloText(ctx, l.text, l.x, l.y, `600 ${l.size}px ${ROMAN}`, INK, 'rgba(242,238,226,0.92)', 4.5),
  },
  under: (ctx, V) => V.sheet.tracks(ctx, V), // the map dashes where every unit has been
  fallen: { color: s => s.dark ?? INK, mark(ctx, x, y, d) { const k = d * 0.6; ctx.moveTo(x, y - k); ctx.lineTo(x, y + k); ctx.moveTo(x - k * 0.65, y - k * 0.3); ctx.lineTo(x + k * 0.65, y - k * 0.3); } },
  over,
  ambient(el) {
    el.innerHTML = '<div class="paper"></div><div class="flare"></div>';
    el.firstChild.style.backgroundImage = `${P.grainURL(256, 19, [40, 36, 28], r => r * 18)}, var(--vignette)`;
  },
  clock(t) { // as the war diaries wrote the time: 2.15 p.m.
    const { h, m, day, month } = clockParts(t);
    return [`${P.dial(h, m)}${h % 12 || 12}.${String(m).padStart(2, '0')}`, day == null ? ampm(h) : `${day} ${MONTHS[month]}, ${ampm(h)}`];
  },
  time(t) { const { h, m } = clockParts(t); return `${h % 12 || 12}.${String(m).padStart(2, '0')} ${ampm(h)}`; },
  hours(t) { // the scale of hours under the scrubber
    const { h, day, month } = clockParts(t);
    if (h === 0 && day != null) return `${day} ${MONTHS[month]}`;
    return h === 12 ? 'noon' : h === 0 ? 'midnight' : `${h % 12} ${ampm(h)}`;
  },
  legend: {
    text: {
      infantry: b => `Infantry, a block in its side’s colour under an ink rule. Each pale dot is ${b.menPerDot} men; the rows are ranks.`,
      facing: () => 'The ink rule is the front rank, the way the unit faces. On the march a point shows the way it goes.',
      fallen: b => `Where men fell: a small upright cross for every ${b.menPerDot} men a unit lost, in that side’s colour.`,
      works: () => 'Trenches and works in red, stepped into fire bays and traverses. The crosses before them are wire.',
      trench: () => 'Siege trench, drawn as the works are: red fire bays and traverses, wire before them.',
      contours: (b, sheet) => `Brown contours every ${sheet.iv} m (${Math.round(sheet.iv * 3.28)} ft), every fourth heavier.`,
      woods: () => 'Woods, marked with the trench map’s tree sign.',
    },
    swatch: {
      woods: g => { g.fillStyle = 'rgba(120,150,90,0.18)'; g.fillRect(2, 3, 60, 22); trees(g); },
      contours: g => { [[[0, 22], [20, 17], [44, 19], [64, 11]], [[0, 14], [22, 9], [42, 11], [64, 4]]].forEach((p, i) => P.stroke(g, p, BROWN, i ? 0.6 : 1.1, i ? 0.6 : 0.8)); },
      water: g => { g.fillStyle = WATER; g.fillRect(0, 12, 64, 16); P.stroke(g, [[0, 12], [64, 12]], BLUE, 1.2); },
      field: g => { const p = [[8, 3], [62, 3], [62, 26], [8, 26]]; P.stroke(g, [...p, p[0]], INK, 0.8, 0.6); },
    },
    extra: () => [
      [(g, s) => { g.setLineDash([5, 3]); g.lineWidth = 1.1; g.strokeStyle = s.color; g.globalAlpha = 0.85; g.beginPath(); g.moveTo(4, 22); g.bezierCurveTo(20, 22, 30, 8, 46, 10); g.stroke(); g.setLineDash([]); g.globalAlpha = 1; g.fillStyle = s.color; g.fillRect(46, 4, 14, 10); g.strokeStyle = INK; g.strokeRect(46, 4, 14, 10); },
        'The dashed line is where each unit has been since the battle began.'],
      [g => {
        g.strokeStyle = INK; g.lineWidth = 0.6; g.globalAlpha = 0.6; g.beginPath(); for (const x of [21, 42]) { g.moveTo(x, 0); g.lineTo(x, 28); } g.moveTo(0, 14); g.lineTo(64, 14); g.stroke();
        g.lineWidth = 1.6; g.globalAlpha = 0.9; g.beginPath(); g.moveTo(0.8, 0); g.lineTo(0.8, 28); g.moveTo(0, 0.8); g.lineTo(64, 0.8); g.stroke(); g.globalAlpha = 1;
        g.fillStyle = INK; g.textAlign = 'center'; g.textBaseline = 'middle'; g.font = `10px ${SANS}`; [['1', 10, 8], ['2', 31, 8], ['3', 53, 8], ['7', 10, 21], ['8', 31, 21], ['9', 53, 21]].forEach(([s, x, y]) => g.fillText(s, x, y));
      }, 'The squared grid: squares of 1,000 yards, numbered 1 to 36 within each lettered square of 6,000 yards, for giving map references.'],
    ],
  },
};
