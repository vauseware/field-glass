// The American Revolution: a plan of the battle engraved and hand-coloured on laid paper, as Faden or Des Barres
// published them. The plate engraves each unit's path as the battle plays; at night a candle lights the table.
import { tracks, mulberry32, clockParts, MONTHS } from '../sim.js';
import * as P from './paint.js';

const INK = '#2a1a0c', PAPER = '#f3e7cb';
const FELL = '"IM Fell English", Georgia, serif';

const feature = (g, type, pts, k, closed) => {
  switch (type) {
    case 'road': P.stroke(g, pts, '#3a2714', 9.5 * k, 0.85); P.stroke(g, pts, '#e9dab0', 7 * k); P.stroke(g, pts, '#b49a66', k, 0.5, [5 * k, 7 * k]); break;
    case 'creek': {
      const n = P.normals(pts);
      P.stroke(g, pts, '#7d9db4', 18 * k, 0.22); P.stroke(g, pts, '#6b8faa', 8 * k, 0.35);
      for (const d of [-6, -9.5, 6, 9.5]) P.stroke(g, P.offset(pts, d * k, n), '#3c5d78', 0.6 * k, 0.45);
      P.stroke(g, pts, '#2c4660', 2.2 * k, 0.9); break;
    }
    case 'fence': P.wormFence(g, pts, 2.6 * k, 7 * k, '#2e1d0d', 1.05 * k); break;
    case 'works': P.stroke(g, pts, INK, 7 * k, 0.9); P.stroke(g, pts, '#d8bd85', 3.5 * k); P.stroke(g, pts, INK, 0.7 * k, 0.6, [2 * k, 2 * k]); break;
    case 'trench': P.stroke(g, pts, INK, 5 * k, 0.85); P.stroke(g, pts, '#c4a574', 2.2 * k); break;
    case 'water': P.polyPath(g, pts); g.fillStyle = '#9fb4bd'; g.fill(); P.stroke(g, [...pts, pts[0]], '#2c4660', 1.4 * k); break;
    default: if (closed) { // redoubt, battery, ship, camp: an inked outline, hatched for earth and timber
      const fill = { ship: '#5a4030', camp: 'rgba(250,240,215,0.55)' }[type] ?? '#d8bd85';
      P.polyPath(g, pts); g.fillStyle = fill; g.fill();
      if (type !== 'camp') P.rule(g, pts, Math.PI / 4, 3 * k, INK, 0.6 * k, 0.45);
      g.save(); if (type === 'camp') g.setLineDash([3 * k, 2 * k]); P.polyPath(g, pts); g.strokeStyle = INK; g.lineWidth = 1.6 * k; g.stroke(); g.restore();
    }
  }
};

// Little engraved canopies with a cast shadow, lit from the north-west.
const treeStamps = () => [4.2, 4.9, 5.6, 6.3].map((r, i) => P.sprite(Math.ceil(r * 4 + 6), (s, n) => {
  const c = n / 2, rnd = mulberry32(40 + i);
  s.fillStyle = 'rgba(60,44,22,0.18)'; s.beginPath(); s.ellipse(c + r * 0.6, c + r * 0.6, r, r * 0.75, 0.6, 0, 7); s.fill();
  const lobes = [...Array(6)].map((_, k) => [c + Math.cos(k * 1.05 + rnd()) * r * 0.42, c + Math.sin(k * 1.05 + rnd()) * r * 0.42, r * (0.48 + rnd() * 0.15)]);
  const path = () => { s.beginPath(); for (const [x, y, rr] of lobes) { s.moveTo(x + rr, y); s.arc(x, y, rr, 0, 7); } };
  path(); s.fillStyle = '#a3a46c'; s.fill();
  s.save(); s.clip(); s.fillStyle = 'rgba(70,72,30,0.45)'; s.beginPath(); s.arc(c + r * 0.6, c + r * 0.6, r * 0.95, 0, 7); s.fill(); s.restore();
  path(); s.strokeStyle = 'rgba(45,32,14,0.75)'; s.lineWidth = 0.6; s.stroke();
}));

function build(b, T, dpr) {
  const dem = P.makeDem(b, T), L = P.layerSpace(b, dem), cv = P.canvas(L.size, L.size), g = cv.getContext('2d'), size = L.size;
  g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high';
  g.drawImage(P.reliefCanvas(dem, P.rampOf([[0, '#b0aa7e'], [0.45, '#cfc499'], [1, '#ebdfb6']]), { k0: 0.66, k1: 0.46 }), 0, 0, size, size);
  g.globalCompositeOperation = 'overlay'; g.globalAlpha = 0.32; // watercolour mottling, mean-neutral
  g.drawImage(P.noiseCanvas(750, 750, { cell: 48, seed: 11, octaves: 5, persist: 0.55 }), 0, 0, size, size);
  g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1;
  for (const poly of b.fields ?? []) { // paler, ruled with furrows
    const p = L.pts(poly);
    g.fillStyle = 'rgba(240,226,180,0.55)'; P.polyPath(g, p); g.fill();
    P.rule(g, p, P.furrow(p), 4.2, '#7b6238', 0.6, 0.35);
  }
  const iv = P.interval(dem, b.contourInterval ?? 3), hiv = Math.max(0.6, (dem.zmax - dem.zmin) / 50);
  for (const { lv, pts } of P.contourLines(dem, iv)) { // faint contours, every fifth a touch heavier
    const major = Math.round(lv / iv) % 5 === 0;
    P.stroke(g, P.densify(pts.map(([c, r]) => [L.gx(c), L.gy(r)]), 6), '#6a4c2a', major ? 1.3 : 0.8, major ? 0.42 : 0.26);
  }
  P.hachures(g, dem, L, P.contourLines(dem, hiv), hiv, { step: 3.4, maxLen: 11, minSlope: 0.075, color: '#3a2714', wMin: 0.45, wMax: 1.4, aMin: 0.18, aMax: 0.62 });
  // Water over the relief, so the drowned ground and the shoreline the modern survey has filled show no contours.
  P.water(g, b, dem, L, { fill: '#9fb4bd', line: '#2c4660', lw: 1.6, liningColor: '#3c5d78', lining: [[4, 0.5], [7.5, 0.4], [11.5, 0.3], [16.5, 0.22], [23, 0.14]] });
  g.drawImage(P.woodsSheet(b, L, { lo: 0.3, hi: 0.52, color: [96, 112, 52], alpha: 0.3 }), 0, 0);
  const stamps = treeStamps();
  P.stampTrees(g, stamps, P.treePoints(b, dem, L, { scale: 1.1, lo: 0.3, hi: 0.52 }));
  P.bakeFeatures(g, b, L, feature, ['creek', 'road', 'fence', 'works', 'trench', 'redoubt', 'battery', 'ship', 'camp']);
  // Layer px per screen px at the chapters' usual framing (the camera's working zoom), never under a layer px.
  const views = b.events.map(e => e.view ?? b.extent * 0.6).sort((p, r) => p - r), q = Math.max(0.7, (L.pxm * (views[views.length >> 1] ?? b.extent)) / 1100);
  const bySide = new Map();
  for (const u of b.units) { if (!bySide.has(u.side)) bySide.set(u.side, []); bySide.get(u.side).push({ u, runs: tracks(u) }); }
  // Dots, not dashes: zero-length dashes with round caps. The last quarter hour of a track is darker than its history.
  const dotted = (c, side, k, fresh) => { const s = q * k; c.setLineDash([0, 3.4 * s]); c.lineWidth = 1.25 * s; c.lineCap = 'round'; c.strokeStyle = b.sides[side].color; c.globalAlpha = fresh ? 0.8 : 0.38; };
  return {
    layer: cv, iv, tracks: P.plate(cv, L, bySide, 900, dotted), rose: rose(dpr), stamps,
    smoke: { sprites: [1, 2, 3, 4].map(s => P.puffSprite(64, s, '247,242,226', '170,160,140')), alpha: 0.8, grow: 1.7, life: 1.6 },
    flash: P.glowSprite(24, [[0, 'rgba(255,255,235,1)'], [0.25, 'rgba(255,214,120,0.95)'], [0.6, 'rgba(230,120,40,0.35)'], [1, 'rgba(200,80,20,0)']]),
  };
}

// A compass rose engraved in the plate's corner: 32 rhumb ticks, the cardinal points in ink, north in red.
function rose(dpr) {
  return P.sprite(Math.round(150 * dpr), g => {
    g.scale(dpr, dpr); const c = 75, R = 56;
    g.strokeStyle = INK; g.lineWidth = 1;
    g.beginPath(); g.arc(c, c, R, 0, 7); g.stroke(); g.beginPath(); g.arc(c, c, R - 5, 0, 7); g.stroke();
    for (let i = 0; i < 64; i++) { const a = (i / 64) * 6.283, r0 = R - (i % 8 ? 3 : 5); g.beginPath(); g.moveTo(c + Math.cos(a) * r0, c + Math.sin(a) * r0); g.lineTo(c + Math.cos(a) * R, c + Math.sin(a) * R); g.stroke(); }
    const point = (a, len, w, dark) => {
      const tip = [c + Math.cos(a) * len, c + Math.sin(a) * len], l = [c + Math.cos(a - Math.PI / 2) * w, c + Math.sin(a - Math.PI / 2) * w], r = [c + Math.cos(a + Math.PI / 2) * w, c + Math.sin(a + Math.PI / 2) * w];
      g.beginPath(); g.moveTo(c, c); g.lineTo(...l); g.lineTo(...tip); g.closePath(); g.fillStyle = dark; g.fill(); g.stroke();
      g.beginPath(); g.moveTo(c, c); g.lineTo(...r); g.lineTo(...tip); g.closePath(); g.fillStyle = PAPER; g.fill(); g.stroke();
    };
    for (let i = 0; i < 4; i++) point(-Math.PI / 4 + (i * Math.PI) / 2, R * 0.55, 5, '#6b4a2a');
    for (let i = 0; i < 4; i++) point(-Math.PI / 2 + (i * Math.PI) / 2, R - 6, 8, i === 0 ? '#8a2617' : INK);
    g.beginPath(); g.arc(c, c, 3, 0, 7); g.fillStyle = PAPER; g.fill(); g.stroke();
    g.font = `20px ${FELL}`; g.textAlign = 'center'; g.fillStyle = '#8a2617'; g.fillText('N', c, 13);
  });
}

// The rose and a scale of yards in the bottom right corner above the bar, or the clear part of the window's corner, or
// nowhere: never under a panel, a chapter name or a unit.
function over(ctx, V) {
  if (V.W <= 640) return;
  const yd = 0.9144 * V.z, len = [50, 100, 200, 250, 500, 1000, 2000, 5000].findLast(n => n * yd <= 170) ?? 50, w = len * yd;
  const fits = (r, b) => r - 190 >= 0 && b - 230 >= 0 && !V.avoid.some(p => p.t < b - 4 && p.b > b - 230 && p.l < r && p.r > r - 190) &&
    !V.B.units.some(u => u.pose && u.screen && Math.abs(u.screen.x - (r - 95)) < 95 + u.screen.w / 2 && Math.abs(u.screen.y - (b - 115)) < 115 + u.screen.w / 2);
  const corner = [[V.W - 24, V.safe.bar - 14], [V.safe.r - 10, V.safe.b]].find(([r, b]) => fits(r, b));
  if (!corner) return;
  const x0 = corner[0] - 10 - Math.max(w, 150) / 2 - w / 2, y0 = corner[1] - 26;
  for (let i = 0; i < 4; i++) { ctx.fillStyle = i % 2 ? PAPER : INK; ctx.fillRect(x0 + (i * w) / 4, y0, w / 4, 5); }
  ctx.strokeStyle = INK; ctx.lineWidth = 1; ctx.strokeRect(x0, y0, w, 5);
  const t = (s, x, y, f) => P.haloText(ctx, s, x, y, f, INK, 'rgba(243,231,203,0.85)', 3.5);
  t('0', x0, y0 + 15, `italic 12px ${FELL}`); t(String(len), x0 + w, y0 + 15, `italic 12px ${FELL}`); t('Scale of Yards', x0 + w / 2, y0 - 11, `italic 15px ${FELL}`);
  ctx.drawImage(V.sheet.rose, x0 + w / 2 - 75, y0 - 186, 150, 150);
}

// A side's colour as a colourist's wash on this paper: a fifth of the way to sepia.
const washes = new Map();
const wash = c => washes.get(c) ?? washes.set(c, `rgb(${P.mix(P.hex(c), [90, 74, 58], 0.2).map(Math.round).join(',')})`).get(c);

function unit(ctx, U) {
  const { w, h, side } = U;
  ctx.save(); ctx.translate(U.x, U.y); ctx.rotate(U.a);
  ctx.fillStyle = 'rgba(30,18,6,0.25)'; ctx.fillRect(-w / 2 + 2, 0, w, h + 3); // cast shadow
  ctx.globalAlpha = U.rout ? 0.55 : 0.92;
  ctx.fillStyle = U.gone ? '#9a9688' : wash(U.mil ? side.light ?? side.color : side.color); ctx.fillRect(-w / 2, -2, w, h + 3);
  ctx.globalAlpha = 1; ctx.lineWidth = 1.3; ctx.strokeStyle = INK; ctx.strokeRect(-w / 2, -2, w, h + 3);
  if (!U.gone) { // the facing, an inked point on the front rank; bolder on the march
    const L = U.go ? 10 : 7, hw = U.go ? 6 : 4.5;
    ctx.globalAlpha = U.rout ? 0.55 : 1;
    ctx.beginPath(); ctx.moveTo(-hw, -2.5); ctx.lineTo(0, -2.5 - L); ctx.lineTo(hw, -2.5); ctx.closePath();
    ctx.lineWidth = 1.6; ctx.strokeStyle = 'rgba(243,231,203,0.9)'; ctx.stroke(); ctx.fillStyle = INK; ctx.fill();
    ctx.globalAlpha = 1;
  }
  if (U.art) { ctx.fillStyle = INK; for (const x of P.gunXs(U)) { ctx.fillRect(x - 2, -12, 4, 12); ctx.beginPath(); ctx.arc(x, 1, 4, 0, 7); ctx.fill(); } }
  ctx.restore();
  P.menDots(ctx, U, U.gone ? '#e8e4d8' : '#f7efda');
}

const period = h => (h < 5 || h >= 21 ? 'at night' : h < 12 ? 'in the morning' : h < 17 ? 'in the afternoon' : 'in the evening');

export default {
  id: 'revolution',
  fonts: 'https://fonts.googleapis.com/css2?family=IM+Fell+English:ital@0;1&family=IM+Fell+English+SC&family=IM+Fell+DW+Pica:ital@0;1&display=swap',
  faces: [`17px ${FELL}`, `italic 15px ${FELL}`],
  kicker: 'A Plan of the',
  paper: '#ece0c0',
  night: [88, 70, 54],
  ring: ['rgba(255,248,225,0.95)', '#8a2617'],
  build,
  feature,
  surround(ctx, r, V) { // the sheet's margin, and a double neatline ruled round the plate
    if (r.l <= 0 && r.t <= 0 && r.r >= V.W && r.b >= V.H) return;
    ctx.fillStyle = '#ebdfc0';
    ctx.fillRect(0, 0, V.W, r.t); ctx.fillRect(0, r.b, V.W, V.H - r.b); ctx.fillRect(0, r.t, r.l, r.b - r.t); ctx.fillRect(r.r, r.t, V.W - r.r, r.b - r.t);
    ctx.strokeStyle = INK; ctx.lineWidth = 2; ctx.strokeRect(r.l - 5, r.t - 5, r.r - r.l + 10, r.b - r.t + 10);
    ctx.lineWidth = 0.8; ctx.strokeRect(r.l - 10, r.t - 10, r.r - r.l + 20, r.b - r.t + 20);
  },
  placeName(ctx, f, x, y) {
    P.haloText(ctx, f.name, x, y, `italic 15px ${FELL}`, '#4a3418', 'rgba(240,228,196,0.75)', 3.5, (-(f.rot ?? 0) * Math.PI) / 180);
    ctx.font = `italic 15px ${FELL}`; return ctx.measureText(f.name).width;
  },
  under: (ctx, V) => V.sheet.tracks(ctx, V), // the plate engraves where every unit has been
  fallen: { color: s => s.dark ?? INK, mark(ctx, x, y, d) { const k = d * 0.55; ctx.moveTo(x - k, y - k); ctx.lineTo(x + k, y + k); ctx.moveTo(x + k, y - k); ctx.lineTo(x - k, y + k); } },
  unit,
  label: {
    measure: (ctx, l) => { ctx.font = `${l.size}px ${FELL}`; return [ctx.measureText(l.text).width + 8, l.size + 4]; },
    draw: (ctx, l) => P.haloText(ctx, l.text, l.x, l.y, `${l.size}px ${FELL}`, '#1a1008', 'rgba(246,238,216,0.92)', 4.5),
  },
  over,
  ambient(el) {
    el.innerHTML = '<div class="clouds"></div><div class="paper"></div><div class="candle"></div>';
    el.firstChild.append(P.cloudSheet(320, 200, 21, [38, 28, 14], 0.2));
    el.children[1].style.backgroundImage = `${P.grainURL(256, 5, [92, 64, 32], r => r * 34)}, var(--vignette)`;
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
      infantry: b => `Infantry, washed in its side’s colour. Each pale dot is ${b.menPerDot} men; the rows are ranks.`,
      fallen: b => `Where men fell: a small cross for every ${b.menPerDot} men a unit lost, in that side’s colour.`,
      contours: (b, sheet) => `Hachures shade the slopes, heavier where steeper; faint contours every ${sheet.iv} m (${Math.round(sheet.iv * 3.28)} ft).`,
    },
    swatch: {
      woods: (g, sheet) => { const r = mulberry32(3); for (let i = 0; i < 9; i++) { const st = sheet.stamps[i % 4]; g.drawImage(st, 6 + r() * 52 - st.width / 2, 5 + r() * 18 - st.height / 2); } },
      contours: g => { P.stroke(g, [[0, 20], [20, 15], [44, 17], [64, 9]], '#6a4c2a', 0.8, 0.5); g.strokeStyle = '#3a2714'; g.globalAlpha = 0.6; g.lineWidth = 0.8; g.beginPath(); for (let x = 2; x < 62; x += 3.4) { g.moveTo(x, 12 - x / 16); g.lineTo(x + 1, 21 - x / 16); } g.stroke(); g.globalAlpha = 1; },
      water: g => { g.fillStyle = '#9fb4bd'; g.fillRect(0, 12, 64, 16); [16, 19.5, 23.5].forEach((y, i) => P.stroke(g, [[0, y], [64, y]], '#3c5d78', 0.6, 0.5 - i * 0.1)); P.stroke(g, [[0, 12], [64, 12]], '#2c4660', 1.6); },
      field: g => { const p = [[8, 3], [62, 3], [62, 26], [8, 26]]; g.fillStyle = 'rgba(240,226,180,0.8)'; P.polyPath(g, p); g.fill(); P.rule(g, p, 0, 4.2, '#7b6238', 0.6, 0.5); },
    },
    extra: () => [[(g, s) => { g.setLineDash([1.5, 3.2]); g.lineWidth = 1.2; g.lineCap = 'round'; g.strokeStyle = s.color; g.globalAlpha = 0.8; g.beginPath(); g.moveTo(4, 22); g.bezierCurveTo(20, 22, 30, 8, 46, 10); g.stroke(); g.setLineDash([]); g.globalAlpha = 1; g.fillStyle = s.color; g.fillRect(46, 4, 14, 10); g.strokeStyle = INK; g.strokeRect(46, 4, 14, 10); },
      'The dotted track engraves where each unit has been since the battle began.']],
  },
};
