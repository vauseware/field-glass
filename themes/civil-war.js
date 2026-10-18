// The Civil War: a topographical engineer's survey, as Hotchkiss drew the Valley and Bachelder the field at Gettysburg.
// Brown contours in feet with every fifth figured, scalloped wood edges, red-ochre roads, Prussian-blue streams, houses as
// black squares. Regiments are blocks in their side's colour ruled into companies, each under a small flag; a battery is
// a row of guns; crosses mark the fallen. At night a lantern lights the sheet.
import { mulberry32, clockParts, MONTHS } from '../sim.js';
import * as P from './paint.js';

export const INK = '#1d2230', SHEET = '#f1ece0';
const SEPIA = '#7a4a26', OCHRE = '#d9925f', PRUSSIAN = '#2f5d9a';
const OLD = '"Old Standard TT", Georgia, serif', CAPS = '"Playfair Display SC", Georgia, serif';
const FT = 0.3048, STAFF = 11; // metres in a foot; a flag's staff in px

const feature = (g, type, pts, k, closed) => {
  switch (type) {
    case 'road': P.stroke(g, pts, INK, 7.5 * k); P.stroke(g, pts, OCHRE, 5.2 * k); break;
    case 'creek': { // widening downstream, from the first point
      g.save(); g.strokeStyle = PRUSSIAN; g.lineCap = 'round';
      for (let i = 1; i < pts.length; i++) { g.lineWidth = (1 + (i / pts.length) * 2.6) * k; g.beginPath(); g.moveTo(...pts[i - 1]); g.lineTo(...pts[i]); g.stroke(); }
      g.restore(); break;
    }
    case 'fence': P.wormFence(g, pts, 1.8 * k, 6 * k, INK, 0.8 * k); break;
    case 'works': case 'trench': { // the parapet, hachured on the side the earth was thrown
      const d = P.densify(pts, 3 * k), n = P.normals(d);
      g.save(); g.beginPath();
      for (let i = 0; i < d.length; i += 2) { const [x, y] = d[i]; g.moveTo(x, y); g.lineTo(x + n[i][0] * 4.5 * k, y + n[i][1] * 4.5 * k); }
      g.strokeStyle = SEPIA; g.lineWidth = 0.9 * k; g.stroke(); g.restore();
      P.stroke(g, pts, INK, (type === 'works' ? 2.2 : 1.5) * k); break;
    }
    case 'water': P.polyPath(g, pts); g.fillStyle = '#c9d6e0'; g.fill(); P.stroke(g, [...pts, pts[0]], PRUSSIAN, 1.2 * k); break;
    default: if (closed) { // redoubt, battery, ship, camp
      g.save(); P.polyPath(g, pts);
      if (type === 'ship') { g.fillStyle = INK; g.fill(); }
      else if (type === 'camp') { g.fillStyle = 'rgba(241,236,224,0.6)'; g.fill(); g.setLineDash([3 * k, 2 * k]); g.strokeStyle = INK; g.lineWidth = 1 * k; g.stroke(); }
      else { g.fillStyle = '#e2cfa4'; g.fill(); P.rule(g, pts, Math.PI / 4, 3 * k, SEPIA, 0.7 * k, 0.6); P.polyPath(g, pts); g.strokeStyle = INK; g.lineWidth = 1.5 * k; g.stroke(); }
      g.restore();
    }
  }
};

// The survey's ground: paper, relief shading, woods with scalloped edges and tree marks, fields, contours in feet with
// the index contours figured, water, the features and the houses. `s` is layer px per screen px with the whole map
// across a 1440 px window, the farthest the follow camera pulls back. The figures are drawn that much larger, so they stay
// legible there; the other marks only by its square root, so they do not crowd the regiments as the camera closes in; and
// the contours thin out by it. The start screen draws its Civil War backdrop from this at s = 1 (splash.js).
export function ground(b, T, s = null) {
  const dem = P.makeDem(b, T), L = P.layerSpace(b, dem), size = L.size, cv = P.canvas(size, size), g = cv.getContext('2d');
  s ??= P.clamp(size / 1440, 1, 2);
  const k = Math.sqrt(s);
  g.fillStyle = SHEET; g.fillRect(0, 0, size, size);
  g.globalCompositeOperation = 'multiply'; g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high';
  g.drawImage(P.reliefCanvas(dem, (f, sh) => { const v = 0.78 + 0.3 * sh + 0.06 * f; return [Math.min(255, 255 * v), Math.min(255, 250 * v), Math.min(255, 240 * v)]; }, { shadeOnly: true }), 0, 0, size, size);
  g.globalCompositeOperation = 'source-over';
  const woods = P.woodsSheet(b, L, { lo: 0.31, hi: 0.33, color: [150, 178, 120], alpha: 0.55, edge: 14 * k });
  g.drawImage(woods, 0, 0);
  { // scalloped wood edges and scattered tree marks, sampled from a coarse copy of the woods
    const m = P.canvas(size / 6, size / 6), mg = m.getContext('2d'); mg.drawImage(woods, 0, 0, m.width, m.height);
    const id = mg.getImageData(0, 0, m.width, m.height).data, Mw = m.width;
    const inside = (x, y) => { const i = (Math.floor(y / 6) * Mw + Math.floor(x / 6)) * 4 + 3; return id[i] > 70; };
    const rnd = mulberry32(17), st = 7 * k, r = 4 * k, e = 8 * k;
    g.strokeStyle = '#3f5a2c'; g.lineWidth = 0.9 * k; g.globalAlpha = 0.85; g.beginPath();
    for (let y = st; y < size - st; y += st) for (let x = st; x < size - st; x += st) {
      if (!inside(x, y)) continue;
      if (!inside(x + e, y) || !inside(x - e, y) || !inside(x, y + e) || !inside(x, y - e)) { g.moveTo(x + r, y); g.arc(x, y, r, 0, Math.PI * 2); }
    }
    g.stroke(); g.globalAlpha = 1;
    g.lineWidth = 0.8 * k; g.beginPath();
    for (let i = 0; i < 26000 / s; i++) {
      const x = rnd() * size, y = rnd() * size;
      if (!inside(x, y) || !inside(x + 10 * k, y) || !inside(x - 10 * k, y)) continue;
      g.moveTo(x + 2.6 * k, y); g.arc(x, y, 2.6 * k, 0, 7); g.moveTo(x + 0.8 * k, y + 4.2 * k); g.arc(x, y + 4.2 * k, 0.8 * k, 0, 7);
    }
    g.stroke();
  }
  for (const poly of b.fields ?? []) {
    const p = L.pts(poly);
    g.fillStyle = 'rgba(236,222,180,0.55)'; P.polyPath(g, p); g.fill();
    g.strokeStyle = INK; g.lineWidth = 0.9 * k; g.setLineDash([6 * k, 2 * k, k, 2 * k]); P.polyPath(g, p); g.stroke(); g.setLineDash([]);
  }
  // Five feet apart, doubled until the sheet holds about 45 lines; every fifth an index contour, figured in feet.
  const iv = P.interval(dem, 5 * FT, 45 / s), ivft = Math.round(iv / FT), labels = [];
  for (const { lv, pts } of P.contourLines(dem, iv)) {
    const feet = Math.round(lv / FT), index = Math.round(feet / ivft) % 5 === 0, q = P.densify(pts.map(([c, r]) => [L.gx(c), L.gy(r)]), 5 * s);
    P.stroke(g, q, SEPIA, (index ? 1.25 : 0.6) * k, index ? 0.8 : 0.5);
    if (index && q.length > 120) for (let i = 60; i < q.length - 30; i += 260) labels.push([q[i], q[i + 4], feet]);
  }
  g.font = `italic ${11 * s}px ${OLD}`; g.textAlign = 'center'; g.textBaseline = 'middle';
  for (const [a, c, feet] of labels) {
    let ang = Math.atan2(c[1] - a[1], c[0] - a[0]); if (ang > Math.PI / 2) ang -= Math.PI; if (ang < -Math.PI / 2) ang += Math.PI;
    g.save(); g.translate(a[0], a[1]); g.rotate(ang); g.scale(s, s); g.fillStyle = 'rgba(241,236,224,0.92)'; g.fillRect(-11, -6, 22, 12); g.scale(1 / s, 1 / s);
    g.fillStyle = SEPIA; g.fillText(String(feet), 0, 0.5 * s); g.restore();
  }
  P.water(g, b, dem, L, { fill: '#c9d6e0', line: PRUSSIAN, lw: 1.4 * k, liningColor: PRUSSIAN, liningWidth: 0.6 * k, lining: [[3.5, 0.45], [7, 0.32], [11, 0.2], [16, 0.12]].map(([d, a]) => [d * k, a]) });
  for (const types of [['creek'], ['fence'], ['road'], ['works', 'trench', 'redoubt', 'battery', 'ship', 'camp']]) P.bakeFeatures(g, b, L, feature, types, k);
  g.fillStyle = INK;
  for (const f of b.features ?? []) if (f.at && !f.type && /farm|house|court|church|meeting|mill|tavern|store|hall/i.test(f.name ?? '')) { // the house the name stands for
    g.fillRect(L.x(f.at[0]) - 4 * k, L.y(f.at[1]) + 10 * s, 8 * k, 6 * k);
  }
  return { layer: cv, iv, ivft };
}

function build(b, T) {
  return {
    ...ground(b, T),
    smoke: { sprites: [1, 2, 3, 4].map(s => P.puffSprite(64, s + 20, '246,244,238', '160,158,150')), alpha: 0.8, grow: 1.7, life: 1.6 },
    flash: P.glowSprite(24, [[0, 'rgba(255,255,235,1)'], [0.25, 'rgba(255,214,120,0.95)'], [0.6, 'rgba(230,120,40,0.35)'], [1, 'rgba(200,80,20,0)']]),
  };
}

// A meridian arrow and a scale of feet on a slip of paper, in the bottom right corner above the bar or the clear part of
// the window's corner: never under a panel, a chapter name or a unit.
function over(ctx, V) {
  if (V.W <= 640) return;
  const c = P.freeCorner(V, 250, 150);
  if (!c) return;
  const ft = FT * V.z, len = [100, 200, 500, 1000, 2000, 5000, 10000].findLast(n => n * ft <= 180) ?? 100, w = len * ft, x0 = c[0] - 60 - w, y0 = c[1] - 44;
  ctx.fillStyle = 'rgba(241,236,224,0.88)'; ctx.fillRect(x0 - 22, y0 - 36, w + 44, 74);
  ctx.fillStyle = INK; ctx.font = `13px ${CAPS}`; ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
  ctx.letterSpacing = '2px'; ctx.fillText('Scale of Feet', x0 + w / 2, y0 - 18); ctx.letterSpacing = '0px';
  for (let i = 0; i < 5; i++) { ctx.fillStyle = i % 2 ? SHEET : INK; ctx.fillRect(x0 + (i * w) / 5, y0 - 6, w / 5, 6); }
  ctx.strokeStyle = INK; ctx.lineWidth = 1; ctx.strokeRect(x0, y0 - 6, w, 6);
  ctx.fillStyle = INK; ctx.font = `italic 12px ${OLD}`; ctx.fillText('0', x0, y0 + 14); ctx.fillText(String(len), x0 + w, y0 + 14);
  const mx = c[0] - 22, my = c[1] - 120; // the meridian: a half-feathered arrow pointing north
  ctx.lineWidth = 1.2; ctx.beginPath(); ctx.moveTo(mx, my + 90); ctx.lineTo(mx, my); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(mx, my - 6); ctx.lineTo(mx - 7, my + 16); ctx.lineTo(mx, my + 10); ctx.closePath(); ctx.fill();
  ctx.beginPath(); ctx.moveTo(mx, my - 6); ctx.lineTo(mx + 7, my + 16); ctx.lineTo(mx, my + 10); ctx.closePath(); ctx.stroke();
  P.haloText(ctx, 'N', mx, my - 16, `700 14px ${CAPS}`, INK, 'rgba(241,236,224,0.88)', 3.5);
}

// A regiment as Bachelder drew one: a block in its side's colour ruled into companies, the front rank heavier, and its
// flag on a staff from the centre of the front (a swallow-tailed guidon for cavalry). A battery is its guns in a row.
function unit(ctx, U) {
  const { w, h, side } = U, col = U.gone ? '#9a978c' : U.mil ? side.light ?? side.color : side.color;
  ctx.save(); ctx.translate(U.x, U.y); ctx.rotate(U.a);
  ctx.globalAlpha = U.rout ? 0.5 : 1;
  ctx.fillStyle = col; ctx.fillRect(-w / 2, -2, w, h + 3);
  const n = U.art ? 0 : Math.max(2, Math.min(10, Math.round(w / 6))); // ten companies, fewer where they would run together
  ctx.beginPath(); for (let i = 1; i < n; i++) { const x = -w / 2 + (w * i) / n; ctx.moveTo(x, -2); ctx.lineTo(x, h + 1); }
  ctx.lineWidth = 1; ctx.strokeStyle = 'rgba(241,236,224,0.6)'; ctx.stroke();
  ctx.strokeStyle = INK; ctx.strokeRect(-w / 2, -2, w, h + 3);
  ctx.fillStyle = INK; ctx.fillRect(-w / 2, -3.5, w, 2.5);
  if (U.go && !U.gone) { ctx.beginPath(); ctx.moveTo(-5, -3.5); ctx.lineTo(0, -12); ctx.lineTo(5, -3.5); ctx.fill(); } // on the march: a point the way it goes
  if (U.art) for (const x of P.gunXs(U)) { // a gun from above: barrel forward, wheels, trail
    ctx.fillRect(x - 1.6, -13, 3.2, 12); ctx.fillRect(x - 5.5, -4, 2.2, 6); ctx.fillRect(x + 3.3, -4, 2.2, 6); ctx.fillRect(x - 0.8, 0, 1.6, 7);
  }
  ctx.restore();
  P.menDots(ctx, U, U.gone ? '#e8e4d8' : '#f6f1e4');
  if (U.art || U.gone) return;
  const fx = U.x + 2 * Math.sin(U.a), fy = U.y - 2 * Math.cos(U.a) - STAFF;
  ctx.save(); ctx.globalAlpha = U.rout ? 0.5 : 1; ctx.strokeStyle = INK; ctx.lineWidth = 1.3;
  ctx.beginPath(); ctx.moveTo(fx, fy + STAFF); ctx.lineTo(fx, fy - 1); ctx.stroke();
  ctx.beginPath();
  if (U.cav) { ctx.moveTo(fx, fy); ctx.lineTo(fx + 12, fy); ctx.lineTo(fx + 8, fy + 3.5); ctx.lineTo(fx + 12, fy + 7); ctx.lineTo(fx, fy + 7); }
  else ctx.rect(fx, fy, 12, 7.5);
  ctx.fillStyle = col; ctx.fill(); ctx.lineWidth = 1; ctx.stroke();
  ctx.restore();
}

const ampm = h => (h < 12 ? 'a.m.' : 'p.m.');

export default {
  id: 'civil-war',
  fonts: 'https://fonts.googleapis.com/css2?family=Old+Standard+TT:ital,wght@0,400;0,700;1,400&family=Playfair+Display+SC:wght@400;700;900&display=swap',
  faces: [`italic 11px ${OLD}`, `15px ${OLD}`, `13px ${CAPS}`, `700 14px ${CAPS}`],
  kicker: 'Map of the',
  paper: SHEET,
  night: [92, 100, 130],
  ring: ['rgba(241,236,224,0.95)', '#b07d1a'],
  build,
  feature,
  preview(b) { // a battle of another war on this sheet: Union blue, the last side listed Confederate red, any between a lighter blue
    const ids = Object.keys(b.sides);
    ids.forEach((id, i) => Object.assign(b.sides[id], i === ids.length - 1 ? { color: '#b23a2e', light: '#d77a6c', dark: '#5c1a14' }
      : i === 0 ? { color: '#2c4f96', light: '#6f8fca', dark: '#16294f' } : { color: '#4f86c6', light: '#8fb3dd', dark: '#1f3f66' }));
  },
  surround(ctx, r, V) { // the sheet's margin and its neat line
    if (r.l <= 0 && r.t <= 0 && r.r >= V.W && r.b >= V.H) return;
    ctx.fillStyle = SHEET;
    ctx.fillRect(0, 0, V.W, r.t); ctx.fillRect(0, r.b, V.W, V.H - r.b); ctx.fillRect(0, r.t, r.l, r.b - r.t); ctx.fillRect(r.r, r.t, V.W - r.r, r.b - r.t);
    ctx.strokeStyle = INK; ctx.lineWidth = 0.8; ctx.strokeRect(r.l - 4, r.t - 4, r.r - r.l + 8, r.b - r.t + 8);
    ctx.lineWidth = 2.5; ctx.strokeRect(r.l - 9, r.t - 9, r.r - r.l + 18, r.b - r.t + 18);
  },
  placeName(ctx, f, x, y) { // water lettered in italic along its course, everything else upright
    const font = `${f.rot ? 'italic ' : ''}15px ${OLD}`;
    P.haloText(ctx, f.name, x, y, font, INK, 'rgba(241,236,224,0.8)', 3.5, (-(f.rot ?? 0) * Math.PI) / 180);
    ctx.font = font; return ctx.measureText(f.name).width;
  },
  fallen: { color: s => s.dark ?? INK, mark(ctx, x, y, d) { const k = d * 0.6; ctx.moveTo(x, y - k); ctx.lineTo(x, y + k * 1.3); ctx.moveTo(x - k * 0.65, y - k * 0.25); ctx.lineTo(x + k * 0.65, y - k * 0.25); } },
  unit,
  label: {
    place(l) { if (!l.U.art && !l.U.gone) l.y = Math.min(l.y, l.U.y - 2 * Math.cos(l.U.a) - STAFF - l.size / 2 - 3); }, // above the flag
    measure: (ctx, l) => { ctx.font = `${l.size}px ${OLD}`; return [ctx.measureText(l.text).width + 8, l.size + 4]; },
    draw: (ctx, l) => P.haloText(ctx, l.text, l.x, l.y, `${l.size}px ${OLD}`, INK, 'rgba(241,236,224,0.92)', 4.5),
  },
  over,
  ambient(el) {
    el.innerHTML = '<div class="paper"></div><div class="lantern"></div>';
    el.firstChild.style.backgroundImage = `${P.grainURL(256, 9, [40, 36, 30], r => r * 30)}, var(--vignette)`;
  },
  clock(t) {
    const { h, m, day, month } = clockParts(t);
    return [`${h % 12 || 12}:${String(m).padStart(2, '0')}`, day == null ? ampm(h) : `${day} ${MONTHS[month]}, ${ampm(h)}`];
  },
  hours(t) {
    const { h, day, month } = clockParts(t);
    if (h === 0 && day != null) return `${day} ${MONTHS[month]}`;
    return h === 12 ? 'noon' : h === 0 ? 'midnight' : `${h % 12} ${ampm(h)}`;
  },
  legend: {
    text: {
      infantry: b => `A regiment: a block in its side’s colour ruled into companies, under its flag. Each pale dot is ${b.menPerDot} men.`,
      facing: () => 'The heavy rule is the front rank, the way the regiment faces. On the march a point shows the way it goes.',
      cavalry: () => 'Cavalry, under a swallow-tailed guidon: taller dots, a mounted man each.',
      artillery: () => 'A battery: a mark for each gun, its muzzle to the front.',
      fallen: b => `Where men fell: a small cross for every ${b.menPerDot} men a unit lost, in that side’s colour.`,
      fence: () => 'Rail fence.',
      woods: () => 'Woods, edged in scallops.',
      contours: (b, sheet) => `Contours every ${sheet.ivft} feet of height; every fifth is heavier and figured in feet.`,
    },
    swatch: {
      woods: g => {
        g.fillStyle = 'rgba(150,178,120,0.55)'; g.fillRect(4, 4, 56, 20);
        g.strokeStyle = '#3f5a2c'; g.lineWidth = 0.9; g.beginPath();
        for (let x = 8; x <= 56; x += 7) for (const y of [4, 24]) { g.moveTo(x + 3.5, y); g.arc(x, y, 3.5, 0, 7); }
        for (const [x, y] of [[16, 11], [30, 15], [44, 10], [24, 18]]) { g.moveTo(x + 2.4, y); g.arc(x, y, 2.4, 0, 7); }
        g.stroke();
      },
      contours: g => {
        P.stroke(g, [[0, 21], [20, 17], [44, 19], [64, 12]], SEPIA, 0.6, 0.6); P.stroke(g, [[0, 11], [22, 6], [64, 4]], SEPIA, 1.25, 0.85);
        g.fillStyle = SHEET; g.fillRect(24, 1, 20, 11); g.font = `italic 10px ${OLD}`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillStyle = SEPIA; g.fillText('250', 34, 6.5);
      },
      water: g => { g.fillStyle = '#c9d6e0'; g.fillRect(0, 12, 64, 16); [15.5, 19, 23].forEach((y, i) => P.stroke(g, [[0, y], [64, y]], PRUSSIAN, 0.6, 0.45 - i * 0.12)); P.stroke(g, [[0, 12], [64, 12]], PRUSSIAN, 1.4); },
      field: g => { const p = [[8, 3], [60, 3], [60, 25], [8, 25]]; g.fillStyle = 'rgba(236,222,180,0.9)'; P.polyPath(g, p); g.fill(); g.strokeStyle = INK; g.lineWidth = 0.9; g.setLineDash([6, 2, 1, 2]); P.polyPath(g, p); g.stroke(); g.setLineDash([]); },
    },
  },
};
