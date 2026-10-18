// The start screen: one screen per war, chosen on a timeline of the years along its foot. Each war draws its own
// backdrop in the dress of its maps; a war with no battles yet shows an in-preparation card. See
// docs/adr/0005-start-screen-per-war-timeline.md. WARS stays importable in node: tools/check.mjs checks every battle's war.
import { normalizeBattle, unitAt, shape, hash, mulberry32, MONTHS } from './sim.js';
import * as P from './themes/paint.js';
import ww2, { counter, looks, arrowPath } from './themes/ww2.js';

// In date order. `war` is the index.json "war" string; ids match the skins in themes.js where a war has one.
// draw(cv, o): o = { id: the battle to draw, fx, fy: where the fight sits as a share of width and height, refW: the
// width the scale is judged by, bottom: px kept clear at the foot, cartouche: bool }.
export const WARS = [
  { id: 'revolution', name: 'American Revolution', years: '1775–1783', from: 1775, to: 1783, war: 'American Revolutionary War', draw: drawPlan },
  { id: 'civil-war', name: 'Civil War', years: '1861–1865', from: 1861, to: 1865, war: 'Civil War', draw: drawSurvey,
    note: 'Specimen sheet: the ground behind this card is Guilford Courthouse, drawn in the survey style.' },
  { id: 'ww2', name: 'Second World War', years: '1939–1945', from: 1939, to: 1945, war: 'World War II', draw: drawTable },
];

const load = id => Promise.all([fetch(`battles/${id}/battle.json`).then(r => r.json()), fetch(`battles/${id}/terrain.json`).then(r => r.json())])
  .then(([raw, T]) => ({ b: normalizeBattle(raw), T }));
const faces = fs => Promise.all(fs.map(f => document.fonts.load(f).catch(() => {})));
// The chapter with the most units in action on the weaker side: a moment when one side has broken reads as a one-sided plan.
const busiest = b => {
  const busy = ev => Math.min(...Object.keys(b.sides).map(sd => b.units.filter(u => { const p = unitAt(u, ev.t); return u.side === sd && p && u.type !== 'artillery' && ['firing', 'charge', 'skirmish'].includes(p.state); }).length));
  return b.events.reduce((best, e) => (e.at && busy(e) > busy(best) ? e : best), b.events.find(e => e.at) ?? b.events[0]);
};

// Revolution: a period battle plan. One battle's own contours, roads and creeks in sepia ink, its regiments as washed
// blocks at the hottest moment of the fight, and dashed arrows for where they had come from.
async function drawPlan(cv, o) {
  const [{ b, T }] = await Promise.all([load(o.id), faces(['italic 20px "IM Fell English"'])]);
  const g = cv.getContext('2d'), CW = cv.width, CH = cv.height, rnd = mulberry32(hash(b.id + 'plan'));
  // Paper: a warm gradient, darker at the edges, flecked, foxed and folded in four.
  const pg = g.createRadialGradient(CW / 2, CH / 2, CH * 0.2, CW / 2, CH / 2, Math.max(CW, CH) * 0.75);
  pg.addColorStop(0, '#efe2c2'); pg.addColorStop(0.7, '#dcc79a'); pg.addColorStop(1, '#a98455');
  g.fillStyle = pg; g.fillRect(0, 0, CW, CH);
  for (let i = 0; i < (CW * CH) / 160; i++) { g.fillStyle = `rgba(90,60,25,${(rnd() * 0.12).toFixed(3)})`; g.fillRect(rnd() * CW, rnd() * CH, 1 + rnd() * 1.5, 1 + rnd() * 1.5); }
  for (let i = 0; i < 14; i++) {
    const x = rnd() * CW, y = rnd() * CH, r = 20 + rnd() * 90, f = g.createRadialGradient(x, y, 0, x, y, r);
    f.addColorStop(0, 'rgba(140,90,40,0.16)'); f.addColorStop(1, 'rgba(140,90,40,0)'); g.fillStyle = f; g.fillRect(x - r, y - r, 2 * r, 2 * r);
  }
  const ev = busiest(b), at = ev.at ?? [0, 0], k = o.refW / Math.max(1200, (ev.view ?? b.extent / 2) * 1.4);
  const X = x => CW * o.fx + (x - at[0]) * k, Y = y => CH * o.fy - (y - at[1]) * k, J = () => (rnd() - 0.5) * 1.2; // hand-drawn wobble
  const ink = a => `rgba(62,38,18,${a})`, half = (T.cols * T.spacing) / 2, sp = T.spacing;
  let zmin = Infinity, zmax = -Infinity;
  for (const v of T.z) if (v) { zmin = Math.min(zmin, v); zmax = Math.max(zmax, v); }
  const Z = T.z.map(v => v || zmin);
  if (b.water != null) { // a one-pixel-per-cell mask, scaled up smooth, so the shore has no stair steps or seams
    const m = document.createElement('canvas'); m.width = T.cols; m.height = T.rows;
    const mg = m.getContext('2d'), img = mg.createImageData(T.cols, T.rows);
    for (let i = 0; i < Z.length; i++) if (Z[i] <= b.water) img.data.set([95, 110, 110, 70], i * 4);
    mg.putImageData(img, 0, 0); g.imageSmoothingEnabled = true; g.drawImage(m, X(-half), Y(half), 2 * half * k, 2 * half * k);
  }
  for (const f of b.features ?? []) if (f.type === 'water') { g.beginPath(); f.poly.forEach(([x, y], i) => (i ? g.lineTo(X(x), Y(y)) : g.moveTo(X(x), Y(y)))); g.fillStyle = 'rgba(95,110,110,0.22)'; g.fill(); }
  const iv = Math.max(b.contourInterval ?? 5, Math.ceil((zmax - zmin) / 45)); // no more than about 45 contours
  for (let lv = Math.ceil(zmin / iv) * iv, n = 0; lv <= zmax; lv += iv, n++) {
    g.beginPath(); g.strokeStyle = ink(n % 5 ? 0.22 : 0.4); g.lineWidth = n % 5 ? 0.8 : 1.3;
    P.contours(Z, T.cols, T.rows, lv, (x0, y0, x1, y1) => { g.moveTo(X((x0 + 0.5) * sp - half) + J(), Y(half - (y0 + 0.5) * sp) + J()); g.lineTo(X((x1 + 0.5) * sp - half) + J(), Y(half - (y1 + 0.5) * sp) + J()); });
    g.stroke();
  }
  const line = (pts, w, a, dash = [], color = ink(a)) => { g.beginPath(); g.setLineDash(dash); pts.forEach(([x, y], i) => (i ? g.lineTo(X(x) + J(), Y(y) + J()) : g.moveTo(X(x), Y(y)))); g.lineWidth = w; g.strokeStyle = color; g.stroke(); g.setLineDash([]); };
  for (const f of b.features ?? []) {
    if (f.pts && f.type === 'road') { line(f.pts, 3.4, 0.55); line(f.pts, 1.4, 0, [], '#e6d5ae'); } // a cased road
    else if (f.pts && f.type === 'creek') line(f.pts, 1.6, 0.5, [7, 3]);
    else if (f.pts && (f.type === 'works' || f.type === 'trench' || f.type === 'fence')) line(f.pts, 2.4, 0.75);
    if (f.poly && f.type !== 'water' && f.type !== 'camp' && (f.from == null || f.from <= ev.t) && (f.until == null || f.until > ev.t)) {
      g.beginPath(); f.poly.forEach(([x, y], i) => (i ? g.lineTo(X(x), Y(y)) : g.moveTo(X(x), Y(y)))); g.closePath(); g.fillStyle = ink(0.25); g.fill(); g.lineWidth = 1.5; g.strokeStyle = ink(0.8); g.stroke();
    }
  }
  // Where each regiment had come from since the chapter before last, as a dashed ink arrow.
  const i0 = b.events.indexOf(ev), t0 = b.events[Math.max(0, i0 - 2)].t;
  for (const u of b.units) {
    const pts = [];
    for (let i = 0; i <= 24; i++) { const p = unitAt(u, t0 + ((ev.t - t0) * i) / 24); if (p) pts.push([p.x, p.y]); }
    if (pts.length < 2 || Math.hypot(pts.at(-1)[0] - pts[0][0], pts.at(-1)[1] - pts[0][1]) * k < 30) continue;
    line(pts, 1.4, 0.7, [8, 5]);
    const [ax, ay] = pts.at(-1), [bx, by] = pts.at(-3) ?? pts[0], ang = Math.atan2(Y(ay) - Y(by), X(ax) - X(bx));
    g.beginPath(); g.moveTo(X(ax), Y(ay)); g.lineTo(X(ax) - 11 * Math.cos(ang - 0.4), Y(ay) - 11 * Math.sin(ang - 0.4)); g.lineTo(X(ax) - 11 * Math.cos(ang + 0.4), Y(ay) - 11 * Math.sin(ang + 0.4)); g.closePath(); g.fillStyle = ink(0.75); g.fill();
  }
  // The regiments, washed in their side's colour and hatched, as Faden and Des Barres drew them.
  const named = [];
  for (const u of b.units) {
    const p = unitAt(u, ev.t);
    if (!p || p.state === 'rout' || p.state === 'surrender') continue; // a plan shows formed bodies only
    const { ranks, F, rankD } = shape(u, p, b.menPerDot), w = Math.max(10, F * k), h = Math.max(5, ranks * rankD * k);
    g.save(); g.translate(X(p.x), Y(p.y)); g.rotate((p.h * Math.PI) / 180);
    g.globalAlpha = 0.6; g.fillStyle = B_SIDE(u.side); g.fillRect(-w / 2, 0, w, h); g.globalAlpha = 1;
    g.beginPath(); g.rect(-w / 2, 0, w, h); g.clip(); g.strokeStyle = ink(0.35); g.lineWidth = 0.8;
    for (let x = -w / 2 - h; x < w / 2; x += 4) { g.moveTo(x, h); g.lineTo(x + h, 0); }
    g.stroke(); g.restore();
    g.save(); g.translate(X(p.x), Y(p.y)); g.rotate((p.h * Math.PI) / 180); g.lineWidth = 1.2; g.strokeStyle = ink(0.85); g.strokeRect(-w / 2, 0, w, h); g.restore();
    if (u.type !== 'artillery') named.push([p.strength, u.short ?? u.name, X(p.x), Y(p.y) - 10]);
  }
  g.font = 'italic 17px "IM Fell English", Georgia, serif'; g.textAlign = 'center'; g.fillStyle = ink(0.85);
  const boxes = []; // biggest units first; a label that would overlap one already written is left off
  for (const [, n, x, y] of named.sort((a, c) => c[0] - a[0])) {
    const w = g.measureText(n).width / 2 + 4, r = [x - w, y - 16, x + w, y + 4];
    if (boxes.length >= 10 || boxes.some(q => r[0] < q[2] && r[2] > q[0] && r[1] < q[3] && r[3] > q[1])) continue;
    boxes.push(r); g.fillText(n, x, y);
  }
  if (o.cartouche) { // compass rose and the cartouche
    const cx = CW - 120, cy = 130, fb = CH - o.bottom;
    g.strokeStyle = ink(0.7); g.fillStyle = ink(0.7); g.lineWidth = 1;
    for (let i = 0; i < 8; i++) {
      const a = (i * Math.PI) / 4, L = i % 2 ? 34 : 64;
      g.beginPath(); g.moveTo(cx, cy); g.lineTo(cx + Math.sin(a - 0.12) * 12, cy - Math.cos(a - 0.12) * 12); g.lineTo(cx + Math.sin(a) * L, cy - Math.cos(a) * L); g.closePath(); i % 2 ? g.stroke() : g.fill();
    }
    g.beginPath(); g.arc(cx, cy, 44, 0, 6.283); g.stroke();
    g.font = '22px "IM Fell English", Georgia, serif'; g.fillText('N', cx, cy - 72);
    g.textAlign = 'right'; g.font = 'italic 24px "IM Fell English", Georgia, serif'; g.fillText(`Plan of ${/^(Battle|Siege)/.test(b.name) ? 'the ' : ''}${b.name}`, CW - 60, fb - 82);
    g.font = 'italic 19px "IM Fell English", Georgia, serif'; g.fillText(`${b.dateText ?? b.date}: ${ev.title}`, CW - 60, fb - 54);
  }
  g.strokeStyle = 'rgba(80,50,20,0.12)'; g.lineWidth = 2; g.beginPath(); g.moveTo(CW / 2, 0); g.lineTo(CW / 2, CH); g.moveTo(0, CH / 2); g.lineTo(CW, CH / 2); g.stroke(); // folds
}
const B_SIDE = side => (side === 'british' ? '#b0382c' : side === 'french' ? '#d8cfb0' : '#3d5a99'); // period washes: red, buff, blue

// Second World War: the recon mosaic on the operations table, under the lamp, with the skin's counters and arrows.
const sheets = new Map(); // the mosaic is the skin's whole layer: built once per battle
async function drawTable(cv, o) {
  const [{ b, T }] = await Promise.all([load(o.id), faces(['700 13px "Courier Prime"', '700 15px "Courier Prime"', '700 13px "Stardos Stencil"'])]);
  const S = sheets.get(b.id) ?? sheets.set(b.id, ww2.build(b, T, 1)).get(b.id), L = looks(b);
  const g = cv.getContext('2d'), CW = cv.width, CH = cv.height;
  g.fillStyle = '#141310'; g.fillRect(0, 0, CW, CH);
  const ev = b.events.find(e => e.title === 'The pincers meet') ?? busiest(b);
  const at = ev.at ?? [0, 0], k = o.refW / Math.max(3000, (ev.view ?? 15000) * 1.25), E = b.extent;
  const X = x => CW * o.fx + (x - at[0]) * k, Y = y => CH * o.fy - (y - at[1]) * k;
  g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high';
  g.drawImage(S.layer, X(-E / 2), Y(E / 2), E * k, E * k);
  // Place names in the interpreter's white ink, where they fit.
  const boxes = [];
  for (const f of b.features) if (f.name && f.at && !f.type) {
    const x = X(f.at[0]), y = Y(f.at[1]);
    g.font = '700 13px "Courier Prime"'; g.letterSpacing = '1px'; const w = g.measureText(f.name.toUpperCase()).width / 2 + 10, r = [x - w, y - 10, x + w, y + 10]; g.letterSpacing = '0px';
    if (r[0] < 8 || r[2] > CW - 8 || y < 20 || y > CH - 20 || f.rot) continue;
    if (boxes.some(q => r[0] < q[2] && r[2] > q[0] && r[1] < q[3] && r[3] > q[1])) continue;
    boxes.push(r); ww2.placeName(g, f, x, y);
  }
  // Hollow chinagraph arrows: each sizeable unit's advance since the chapter before.
  const i0 = b.events.indexOf(ev), t0 = b.events[Math.max(0, i0 - 1)].t, paths = new Map();
  const units = [...b.units].sort((p, q) => q.strength - p.strength), tips = [];
  for (const u of units) {
    const p = unitAt(u, ev.t), q = unitAt(u, t0);
    if (!p || !q || p.state === 'surrender') continue;
    const rad = (p.h * Math.PI) / 180, x1 = X(p.x) - Math.sin(rad) * 30, y1 = Y(p.y) + Math.cos(rad) * 30;
    let x0 = X(q.x), y0 = Y(q.y); const len = Math.hypot(x1 - x0, y1 - y0);
    if (len < 50 || tips.some(([x, y]) => Math.hypot(x - x1, y - y1) < 120)) continue;
    tips.push([x1, y1]);
    if (len > 260) { x0 = x1 - ((x1 - x0) * 260) / len; y0 = y1 - ((y1 - y0) * 260) / len; }
    const look = L.get(b.sides[u.side]), path = paths.get(look) ?? paths.set(look, new Path2D()).get(look);
    arrowPath(path, x0, y0, x1, y1);
  }
  g.save(); g.lineJoin = 'round'; g.lineCap = 'round';
  for (const [look, path] of paths) {
    g.translate(1, 1.5); g.lineWidth = 3.4; g.strokeStyle = 'rgba(0,0,0,0.4)'; g.stroke(path); g.translate(-1, -1.5);
    g.lineWidth = 2.6; g.strokeStyle = look.pattern; g.globalAlpha = 0.9; g.stroke(path); g.globalAlpha = 1;
  }
  g.restore();
  // Units: men or tanks as dark specks, a chinagraph bracket along the front with an arrow the way it faces.
  const named = [];
  for (const u of b.units) {
    const p = unitAt(u, ev.t);
    if (!p) continue;
    const look = L.get(b.sides[u.side]), { nd, ranks, F, rankD } = shape(u, p, b.menPerDot), w = Math.max(16, F * k), h = Math.max(4, ranks * rankD * k);
    const x = X(p.x), y = Y(p.y);
    if (x < -50 || x > CW + 50 || y < -50 || y > CH + 50) continue;
    g.save(); g.translate(x, y); g.rotate((p.h * Math.PI) / 180);
    g.fillStyle = 'rgba(18,20,14,0.85)';
    const n = Math.min(nd, u.type === 'armor' ? 14 : 24), rr = mulberry32(hash(u.id));
    for (let i = 0; i < n; i++) { const s = u.type === 'armor' ? 3.2 : 1.6; g.fillRect(-w / 2 + rr() * w - s / 2, 2 + rr() * h, s, s * (u.type === 'armor' ? 1.4 : 1)); }
    const hook = Math.min(h + 3, 9), Lh = 14, br = () => { g.beginPath(); g.moveTo(-w / 2, -2 + hook); g.lineTo(-w / 2, -2); g.lineTo(w / 2, -2); g.lineTo(w / 2, -2 + hook); g.moveTo(0, -5); g.lineTo(0, -2 - Lh); g.moveTo(-4.5, 3.5 - Lh); g.lineTo(0, -2 - Lh); g.lineTo(4.5, 3.5 - Lh); };
    g.lineCap = 'round'; g.lineJoin = 'round';
    g.translate(1, 1.5); br(); g.lineWidth = 3.6; g.strokeStyle = 'rgba(0,0,0,0.45)'; g.stroke(); g.translate(-1, -1.5);
    br(); g.lineWidth = 2.6; g.strokeStyle = look.wax; g.stroke();
    g.restore();
    named.push({ u, p, look, x, y });
  }
  const drawn = [];
  for (const { u, look, x, y } of named.sort((a, c) => c.p.strength - a.p.strength)) {
    if (drawn.length >= 9) break;
    const c = counter((u.short ?? u.name).toUpperCase(), look, 13, false, false, 1, u.type === 'armor');
    const cx = x - c.w / 2, cy = y - 30 - c.h, r = [cx - 4, cy - 4, cx + c.w + 4, cy + c.h + 4];
    if (r[0] < 0 || r[2] > CW || r[1] < 0 || [...drawn, ...boxes].some(q => r[0] < q[2] && r[2] > q[0] && r[1] < q[3] && r[3] > q[1])) continue;
    drawn.push(r); g.drawImage(c.c, cx - c.pad, cy - c.pad);
  }
  // The lamp: a warm pool on the fight, falling off into the dark room.
  const R = Math.hypot(CW, CH), lx = CW * o.fx, ly = CH * o.fy;
  const lamp = g.createRadialGradient(lx, ly, Math.min(CW, CH) * 0.12, lx, ly, R * 0.62);
  lamp.addColorStop(0, 'rgba(0,0,0,0)'); lamp.addColorStop(0.55, 'rgba(8,7,4,0.35)'); lamp.addColorStop(1, 'rgba(8,7,4,0.8)');
  g.fillStyle = lamp; g.fillRect(0, 0, CW, CH);
  g.globalCompositeOperation = 'soft-light';
  const warm = g.createRadialGradient(lx, ly, 0, lx, ly, R * 0.4); warm.addColorStop(0, 'rgba(255,196,110,0.55)'); warm.addColorStop(1, 'rgba(255,196,110,0)');
  g.fillStyle = warm; g.fillRect(0, 0, CW, CH); g.globalCompositeOperation = 'source-over';
  if (o.cartouche) { // a teleprinter strip pinned to the table, in the skin's words for the hour
    const d = new Date(Math.abs(ev.t) < 366 * 86400 ? Date.parse(b.date) + ev.t * 1000 : ev.t * 1000); // an undated time is the battle's first day
    const text = `${b.name}  ${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}  ${ww2.when(ev, b)[0].split('\n')[1]}  ${ev.title} STOP`.toUpperCase();
    g.font = '700 15px "Courier Prime"'; const w = g.measureText(text).width + 36, x = CW - 40 - w, y = CH - o.bottom - 74;
    g.save(); g.translate(x, y); g.rotate(-0.012);
    g.fillStyle = 'rgba(0,0,0,0.5)'; g.fillRect(4, 6, w, 40); g.fillStyle = '#f2e6b4'; g.fillRect(0, 0, w, 40);
    g.fillStyle = '#1f1c14'; g.textBaseline = 'middle'; g.fillText(text, 18, 21); g.restore();
  }
}

// Civil War, before its first battle: Guilford Courthouse drawn as a topographical engineer's survey, ground only.
const INK = '#1d2230', SHEET = '#f1ece0', SEPIA = '#7a4a26';
let survey = null; // the layer, built once
function surveyLayer(b, T) {
  const dem = P.makeDem(b, T), L = P.layerSpace(b, dem), size = L.size, cv = P.canvas(size, size), g = cv.getContext('2d');
  g.fillStyle = SHEET; g.fillRect(0, 0, size, size);
  g.globalCompositeOperation = 'multiply'; g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high';
  g.drawImage(P.reliefCanvas(dem, (f, sh) => { const v = 0.78 + 0.3 * sh + 0.06 * f; return [Math.min(255, 255 * v), Math.min(255, 250 * v), Math.min(255, 240 * v)]; }, { shadeOnly: true }), 0, 0, size, size);
  g.globalCompositeOperation = 'source-over';
  const woods = P.woodsSheet(b, L, { lo: 0.31, hi: 0.33, color: [150, 178, 120], alpha: 0.55, edge: 14 });
  g.drawImage(woods, 0, 0);
  { // scalloped wood edges and scattered tree marks, sampled from a coarse copy of the woods
    const m = P.canvas(size / 6, size / 6), mg = m.getContext('2d'); mg.drawImage(woods, 0, 0, m.width, m.height);
    const id = mg.getImageData(0, 0, m.width, m.height).data, Mw = m.width;
    const inside = (x, y) => { const i = (Math.floor(y / 6) * Mw + Math.floor(x / 6)) * 4 + 3; return id[i] > 70; };
    const rnd = mulberry32(17);
    g.strokeStyle = '#3f5a2c'; g.lineWidth = 0.9; g.globalAlpha = 0.85; g.beginPath();
    for (let y = 6; y < size - 6; y += 7) for (let x = 6; x < size - 6; x += 7) {
      if (!inside(x, y)) continue;
      if (!inside(x + 8, y) || !inside(x - 8, y) || !inside(x, y + 8) || !inside(x, y - 8)) { g.moveTo(x + 4, y); g.arc(x, y, 4, 0, Math.PI * 2); }
    }
    g.stroke(); g.globalAlpha = 1;
    g.lineWidth = 0.8; g.beginPath();
    for (let i = 0; i < 26000; i++) { const x = rnd() * size, y = rnd() * size; if (!inside(x, y) || !inside(x + 10, y) || !inside(x - 10, y)) continue; g.moveTo(x + 2.6, y); g.arc(x, y, 2.6, 0, 7); g.moveTo(x + 0.8, y + 4.2); g.arc(x, y + 4.2, 0.8, 0, 7); }
    g.stroke();
  }
  for (const poly of b.fields ?? []) {
    const p = poly.map(([x, y]) => [L.x(x), L.y(y)]);
    g.fillStyle = 'rgba(236,222,180,0.55)'; P.polyPath(g, p); g.fill();
    g.strokeStyle = INK; g.lineWidth = 0.9; g.setLineDash([6, 2, 1, 2]); P.polyPath(g, p); g.stroke(); g.setLineDash([]);
  }
  const ft = 0.3048, labels = [];
  for (const { lv, pts } of P.contourLines(dem, 5 * ft)) {
    const feet = Math.round(lv / ft), index = feet % 25 === 0, q = P.densify(pts.map(([c, r]) => [L.gx(c), L.gy(r)]), 5);
    P.stroke(g, q, SEPIA, index ? 1.25 : 0.6, index ? 0.8 : 0.5);
    if (index && q.length > 120) for (let i = 60; i < q.length - 30; i += 260) labels.push([q[i], q[i + 4], feet]);
  }
  g.font = 'italic 11px "Old Standard TT"'; g.textAlign = 'center'; g.textBaseline = 'middle';
  for (const [a, c, feet] of labels) {
    let ang = Math.atan2(c[1] - a[1], c[0] - a[0]); if (ang > Math.PI / 2) ang -= Math.PI; if (ang < -Math.PI / 2) ang += Math.PI;
    g.save(); g.translate(a[0], a[1]); g.rotate(ang); g.fillStyle = 'rgba(241,236,224,0.92)'; g.fillRect(-11, -6, 22, 12); g.fillStyle = SEPIA; g.fillText(String(feet), 0, 0.5); g.restore();
  }
  for (const f of b.features.filter(f => f.type === 'creek')) {
    const q = P.densify(f.pts.map(([x, y]) => [L.x(x), L.y(y)]), 2);
    for (let i = 1; i < q.length; i++) { const kk = i / q.length; g.strokeStyle = '#2f5d9a'; g.lineWidth = 1 + kk * 2.6; g.lineCap = 'round'; g.beginPath(); g.moveTo(...q[i - 1]); g.lineTo(...q[i]); g.stroke(); }
  }
  for (const f of b.features.filter(f => f.type === 'road')) {
    const q = P.densify(f.pts.map(([x, y]) => [L.x(x), L.y(y)]), 2);
    P.stroke(g, q, INK, 7.5, 1); P.stroke(g, q, '#d9925f', 5.2, 1);
  }
  for (const f of b.features.filter(f => f.type === 'fence')) {
    const q = P.densify(f.pts.map(([x, y]) => [L.x(x), L.y(y)]), 2);
    P.stroke(g, q, INK, 0.9, 1); const n = P.normals(q);
    g.beginPath(); for (let i = 0; i < q.length; i += 3) { const [x, y] = q[i]; g.moveTo(x - n[i][0] * 2.2, y - n[i][1] * 2.2); g.lineTo(x + n[i][0] * 2.2, y + n[i][1] * 2.2); } g.lineWidth = 0.7; g.stroke();
  }
  return cv;
}
async function drawSurvey(cv, o) {
  const [{ b, T }] = await Promise.all([load('guilford'), faces(['italic 11px "Old Standard TT"', 'italic 12px "Old Standard TT"', '700 14px "Playfair Display SC"', '13px "Playfair Display SC"'])]);
  const layer = (survey ??= surveyLayer(b, T)), g = cv.getContext('2d'), CW = cv.width, CH = cv.height;
  const at = [-250, -60], k = o.refW / 1440, E = b.extent; // the fields round the courthouse
  const X = x => CW * o.fx + (x - at[0]) * k, Y = y => CH * o.fy - (y - at[1]) * k;
  g.fillStyle = SHEET; g.fillRect(0, 0, CW, CH);
  g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high';
  g.drawImage(layer, X(-E / 2), Y(E / 2), E * k, E * k);
  // linen grain and a vignette, multiplied, as on the battle screen
  g.globalCompositeOperation = 'multiply';
  g.globalAlpha = 0.35; g.drawImage(P.grainCanvas(CW, CH, 4, 225, 255), 0, 0); g.globalAlpha = 1;
  const vg = g.createRadialGradient(CW / 2, CH / 2, Math.min(CW, CH) * 0.4, CW / 2, CH / 2, Math.hypot(CW, CH) * 0.6);
  vg.addColorStop(0, 'rgba(255,255,255,1)'); vg.addColorStop(1, 'rgba(160,150,135,1)');
  g.fillStyle = vg; g.fillRect(0, 0, CW, CH); g.globalCompositeOperation = 'source-over';
  if (o.cartouche) { // a meridian arrow and a scale of feet, the engineer's furniture
    const fb = CH - o.bottom, sx = CW - 380, sy = fb - 60, ftpx = 0.3048 * k;
    g.strokeStyle = INK; g.fillStyle = INK; g.lineWidth = 1.2;
    const mx = CW - 80, my = 70; g.beginPath(); g.moveTo(mx, my + 90); g.lineTo(mx, my); g.stroke();
    g.beginPath(); g.moveTo(mx, my - 6); g.lineTo(mx - 7, my + 16); g.lineTo(mx, my + 10); g.closePath(); g.fill();
    g.beginPath(); g.moveTo(mx, my - 6); g.lineTo(mx + 7, my + 16); g.lineTo(mx, my + 10); g.closePath(); g.stroke();
    g.font = '700 14px "Playfair Display SC"'; g.textAlign = 'center'; g.fillText('N', mx, my - 18);
    g.fillStyle = 'rgba(241,236,224,0.88)'; g.fillRect(sx - 24, sy - 38, 2 * 24 + 1000 * ftpx, 78);
    g.fillStyle = INK; g.font = '13px "Playfair Display SC"'; g.letterSpacing = '2px'; g.fillText('Scale of Feet', sx + 500 * ftpx, sy - 20); g.letterSpacing = '0px';
    for (let i = 0; i < 5; i++) { g.fillStyle = i % 2 ? SHEET : INK; g.fillRect(sx + i * 200 * ftpx, sy - 6, 200 * ftpx, 6); }
    g.strokeRect(sx, sy - 6, 1000 * ftpx, 6);
    g.font = 'italic 12px "Old Standard TT"'; g.fillStyle = INK;
    for (let i = 0; i <= 5; i++) g.fillText(String(i * 200), sx + i * 200 * ftpx, sy + 14);
    g.fillText('Contours at intervals of five feet.', sx + 500 * ftpx, sy + 32);
  }
}

// ---------- the screen ----------

const Y0 = 1770, Y1 = 1950; // the timeline's span, ruled every ten years
const fmt = s => (s < 90 ? `${s} s` : `${Math.round(s / 60)} min`);
const FOOT = 'Each battle plays from first shot to last in the time shown. Pause, scrub or change the speed at any time.';

// list: battles/index.json, in date order. war: the id to open on. open(id): play that battle.
export function showSplash(list, war, open) {
  const el = document.querySelector('#splash'), cv = el.querySelector('#plan'), card = el.querySelector('.card'), axis = el.querySelector('.tl-axis');
  const battles = w => list.filter(e => e.war === w.war), plan = new URLSearchParams(location.search).get('plan');
  const pick = new Map(WARS.map(w => { const bs = battles(w); return [w, (bs.find(e => e.id === plan) ?? bs[Math.floor(Math.random() * bs.length)])?.id]; })); // ?plan=<id> for screenshots
  const drawn = new Map(); // backdrops are slow to build, so each is drawn once per war and size, then copied
  const count = w => { const n = battles(w).length; return n ? `${n} battle${n > 1 ? 's' : ''}` : 'in preparation'; };
  const pc = y => ((y - Y0) / (Y1 - Y0)) * 100;
  axis.innerHTML = '<div class="tl-rule"></div>' + [1800, 1850, 1900].map(y => `<span class="tl-yr" style="left:${pc(y)}%">${y}</span>`).join('')
    + WARS.map(w => `<span class="tl-span" style="left:${pc(w.from)}%;width:${pc(w.to) - pc(w.from)}%"></span>`).join('')
    + WARS.map(w => `<button class="tl-war" data-war="${w.id}" style="left:clamp(0px, calc(${pc((w.from + w.to) / 2)}% - 130px), calc(100% - 260px))"><b>${w.name}</b><small>${w.years}, ${count(w)}</small></button>`).join('');

  async function backdrop() {
    const w = WARS.find(x => x.id === war), W = innerWidth, H = innerHeight, wide = W > 800, bar = wide ? 140 : 0, key = `${war} ${W}x${H}`;
    if (cv.dataset.key === key) return;
    cv.dataset.key = key; cv.width = W; cv.height = H;
    if (!drawn.has(key)) drawn.set(key, (async () => {
      const c = document.createElement('canvas'); c.width = W; c.height = H;
      await w.draw(c, { id: pick.get(w), fx: wide ? Math.min(0.75, (680 + (W - 680) / 2) / W) : 0.5, fy: wide ? (H - bar) / 2 / H : 0.74, refW: wide ? W : 900, bottom: bar, cartouche: wide });
      return c;
    })());
    const c = await drawn.get(key).catch(() => null); // the backdrop is decoration; the list works without it
    if (c && cv.dataset.key === key) cv.getContext('2d').drawImage(c, 0, 0); // still the war and size on show
  }
  function render() {
    const w = WARS.find(x => x.id === war), bs = battles(w);
    el.className = `war-${war}`;
    card.innerHTML = `<div class="label"><h1>Field Glass</h1></div><p class="tag">Battles of the ${w.name}, replayed from the record</p>` + (bs.length
      ? `<nav class="list" aria-label="Battles">${bs.map(b => `<button class="row" data-id="${b.id}"><span>${b.name}</span><i></i><span class="rt">${b.runtime ? fmt(b.runtime) : ''}</span></button>`).join('')}</nav><p class="foot">${FOOT}</p>`
      : `<div class="rule2"></div><div class="empty"><p class="lead">The first battles are in preparation.</p><p>They will be listed here, each with its running time, when they are ready.</p>
        <div class="go">${WARS.filter(o => battles(o).length).map(o => `<button data-war="${o.id}">See the battles of the ${o.name}</button>`).join('')}</div></div><p class="foot">${w.note ?? ''}</p>`);
    for (const b of axis.querySelectorAll('.tl-war')) b.setAttribute('aria-pressed', b.dataset.war === war);
    backdrop();
  }
  el.onclick = e => {
    const b = e.target.closest('button');
    if (b?.dataset.war) { war = b.dataset.war; history.replaceState(null, '', `#${war}`); render(); }
    else if (b?.dataset.id) open(b.dataset.id);
  };
  let rt; addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(() => el.hidden || backdrop(), 150); });
  el.hidden = false;
  render();
}
