// The Second World War: a reconnaissance photo mosaic laid on a lamp-lit operations table. The ground is a sortie's
// overlapping prints, each a touch askew and differently exposed in its captioned border. Units are painted counters with
// stencilled names behind chinagraph frontages, yellow for one side and red for the other; hollow chinagraph arrows show
// each unit's advance, a 1 km grid is numbered at the edge, and every fifth round is a tracer. The lamp sways in #fx.
import { mulberry32, hash, unitAt, eventAt, clockParts, MONTHS } from '../sim.js';
import * as P from './paint.js';

const STENCIL = '"Stardos Stencil", Impact, sans-serif', TELE = '"Courier Prime", "Courier New", monospace', NUM = 'Oswald, "Arial Narrow", sans-serif';
const TABLE = '#141310', CHALK = '#ecebe2', YELLOW = '#f2d24b', RED = '#ff6a4d';
const ROMAN = 'I II III IV V VI VII VIII IX X XI XII'.split(' ');
const pad2 = n => String(n).padStart(2, '0');

// The battle on the table now: each side's look, the counters painted so far, the grid's origin, the dark at the last
// frame (the night falls after under() and before the units, so they read it a frame late).
let cur = null;

// Grease pencil drags and skips on a glossy print: the colour with a scatter of thin spots, as a repeating pattern, for the
// arrows' broad strokes.
function waxOf(hex, seed) {
  const c = P.canvas(48, 48), g = c.getContext('2d'), img = g.createImageData(48, 48), rnd = mulberry32(seed), [r, gg, b] = P.hex(hex);
  for (let i = 0; i < 48 * 48; i++) { const v = rnd(); img.data.set([r, gg, b, v < 0.1 ? 80 : v < 0.28 ? 195 : 248], i * 4); }
  g.putImageData(img, 0, 0);
  return g.createPattern(c, 'repeat');
}
const lum = hex => { const [r, g, b] = P.hex(hex); return (0.299 * r + 0.587 * g + 0.114 * b) / 255; };
// Each side's look: its chinagraph (`wax` in battle.json, else red for the last side listed and yellow for the rest), its
// tracer, and its counters painted in the side's colour, the lighter shade for militia.
function looks(b) {
  const ids = Object.keys(b.sides), out = new Map();
  ids.forEach((id, i) => {
    const s = b.sides[id], enemy = i === ids.length - 1 && ids.length > 1, wax = s.wax ?? (enemy ? RED : YELLOW);
    const paint = c => ({ top: c, edge: `rgb(${P.mix(P.hex(c), [0, 0, 0], 0.35).map(Math.round)})`, text: lum(c) > 0.4 ? '#121212' : '#efe6c4' });
    out.set(s, { id, wax, pattern: waxOf(wax, 7 + i), tracer: s.tracer ?? (enemy ? [150, 255, 150] : [255, 120, 70]), paint: paint(s.color), light: paint(s.light ?? s.color) });
  });
  return out;
}

// Tree crowns seen from above, lit from the north-west, each throwing its shadow south-east.
let crownSprites = null;
const crowns = () => (crownSprites ??= [3.4, 4.2, 5, 5.8].map((r, i) => P.sprite(Math.ceil(r * 3 + 7), (s, n) => {
  const c = n / 2 - 1.5, rnd = mulberry32(60 + i);
  s.fillStyle = 'rgba(10,12,8,0.55)'; s.beginPath(); s.ellipse(c + r * 0.7, c + r * 0.7, r * 1.05, r * 0.9, 0.7, 0, 7); s.fill();
  const gr = s.createRadialGradient(c - r * 0.35, c - r * 0.35, 0, c, c, r); gr.addColorStop(0, '#a9ad98'); gr.addColorStop(0.55, '#5f6452'); gr.addColorStop(1, '#2f3328');
  s.fillStyle = gr; s.beginPath();
  for (let k = 0; k < 5; k++) { const a = k * 1.26 + rnd(), x = c + Math.cos(a) * r * 0.3, y = c + Math.sin(a) * r * 0.3; s.moveTo(x + r * 0.72, y); s.arc(x, y, r * 0.72, 0, 7); }
  s.fill();
})));
// Crowns every `step` px along a line, `off` px to either side of it.
function treeRow(g, pts, k, step, offs, seed) {
  const st = crowns(), rnd = mulberry32(seed);
  let acc = 0;
  for (let i = 1; i < pts.length; i++) {
    const [x0, y0] = pts[i - 1], [x1, y1] = pts[i], seg = Math.hypot(x1 - x0, y1 - y0), nx = -(y1 - y0) / (seg || 1), ny = (x1 - x0) / (seg || 1);
    for (; acc < seg; acc += step * k * (0.8 + rnd() * 0.4)) {
      const f = acc / seg, x = x0 + (x1 - x0) * f, y = y0 + (y1 - y0) * f;
      for (const o of offs) { const s = st[(rnd() * st.length) | 0], w = s.width * k, j = (rnd() - 0.5) * 3 * k; g.drawImage(s, x + nx * (o * k + j) - w / 2, y + ny * (o * k + j) - w / 2, w, w); }
    }
    acc -= seg;
  }
}

const feature = (g, type, pts, k, closed) => {
  switch (type) {
    case 'road': P.stroke(g, pts, '#d6d4c2', 7 * k, 0.25); P.stroke(g, pts, '#dddbc9', 3.6 * k, 0.9); P.stroke(g, pts, '#8d8c7c', 0.7 * k, 0.6, [12 * k, 7 * k]); break;
    case 'creek': treeRow(g, pts, k, 4, [-7, 7], pts.length); P.stroke(g, pts, '#1e221b', 2.6 * k, 0.95); P.stroke(g, pts, '#9aa196', 0.6 * k, 0.5, [3 * k, 9 * k]); break;
    case 'fence': P.stroke(g, pts, '#2a2d24', 1.6 * k, 0.5); treeRow(g, pts, k, 5, [0], pts.length + 1); break; // a hedgerow grown along it
    case 'works': P.stroke(g, P.offset(pts, 2.2 * k), '#14150f', 2.4 * k, 0.75); P.stroke(g, pts, '#cdc9b2', 3.6 * k, 0.95); break; // a pale earth bank and its shadow
    case 'trench': P.stroke(g, pts, '#c4c0a8', 4.6 * k, 0.75); P.stroke(g, pts, '#14150f', 2 * k, 0.95); break; // spoil thrown up either side of a dark cut
    case 'water': P.polyPath(g, pts); g.fillStyle = '#2a2f29'; g.fill(); P.stroke(g, [...pts, pts[0]], 'rgba(205,208,192,0.55)', 1.2 * k); break;
    default: if (closed) {
      g.save();
      if (type === 'camp') { // tent lines: rows of small pale roofs
        P.polyPath(g, pts); g.fillStyle = 'rgba(30,32,26,0.25)'; g.fill();
        g.setLineDash([2.4 * k, 2.6 * k]); P.rule(g, pts, 0, 4.5 * k, '#e6e4d6', 1.8 * k, 0.85);
      } else if (type === 'ship') {
        P.polyPath(g, pts); g.fillStyle = '#23241f'; g.fill(); P.stroke(g, [...pts, pts[0]], '#c9c8b8', 0.9 * k, 0.8);
      } else { // redoubt or battery: a pale earthwork ringed by its dark ditch
        P.stroke(g, [...pts, pts[0]], '#12130e', 4 * k, 0.85); P.polyPath(g, pts); g.fillStyle = '#bdb9a2'; g.fill();
        P.rule(g, pts, Math.PI / 4, 3 * k, '#5d5c4e', 0.6 * k, 0.4);
      }
      g.restore();
    }
  }
};

// The ground as one print of the sortie: monochrome relief, fields bright with plough lines, woods dark with crowns,
// hedgerows, creeks, roads and works, and film grain.
function ground(b, dem, L) {
  const size = L.size, base = P.canvas(size, size), g = base.getContext('2d');
  g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high';
  g.drawImage(P.reliefCanvas(dem, (f, sh) => { const v = 70 + 120 * sh + 25 * f; return [v * 0.97, v, v * 0.9]; }, { shadeOnly: true }), 0, 0, size, size);
  g.globalCompositeOperation = 'overlay'; g.globalAlpha = 0.55; g.drawImage(P.noiseCanvas(600, 600, { cell: 40, seed: 4, octaves: 5, persist: 0.6 }), 0, 0, size, size);
  g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1;
  const patchy = P.noiseCanvas(300, 300, { cell: 12, seed: 8, octaves: 3 });
  for (const poly of b.fields ?? []) {
    const p = L.pts(poly);
    g.fillStyle = 'rgba(196,196,176,0.78)'; P.polyPath(g, p); g.fill();
    P.rule(g, p, P.furrow(p), 2.6, '#3e4036', 0.9, 0.22);
    g.save(); P.polyPath(g, p); g.clip(); g.globalCompositeOperation = 'overlay'; g.globalAlpha = 0.6; g.drawImage(patchy, 0, 0, size, size); g.restore();
  }
  P.water(g, b, dem, L, { fill: '#2a2f29', line: 'rgba(205,208,192,0.55)', lw: 1.2, liningColor: '#c8cbbd', liningWidth: 0.6, lining: [[3.5, 0.22], [8, 0.1]] });
  g.globalCompositeOperation = 'multiply'; g.drawImage(P.woodsSheet(b, L, { lo: 0.3, hi: 0.36, color: [92, 98, 82], alpha: 0.9, edge: 6 }), 0, 0); g.globalCompositeOperation = 'source-over';
  P.stampTrees(g, crowns(), P.treePoints(b, dem, L, { scale: 1.6, lo: 0.3, hi: 0.36 }));
  P.bakeFeatures(g, b, L, feature, ['creek', 'fence']);
  P.bakeFeatures(g, b, L, feature, ['road', 'works', 'trench', 'redoubt', 'battery', 'ship', 'camp']);
  for (const f of b.features ?? []) if (f.at && !f.type && /farm|house|court|church|meeting|mill|tavern|store|hall/i.test(f.name ?? '')) { // the roofs the name stands for
    const k = Math.max(0.3, L.pxm), x = L.x(f.at[0]), y = L.y(f.at[1]) + 14 * k; // about 12 m by 9, never under a few pixels
    g.fillStyle = 'rgba(0,0,0,0.6)'; g.fillRect(x - 3 * k, y - 2 * k, 12 * k, 9 * k); g.fillStyle = '#e6e3d4'; g.fillRect(x - 6 * k, y - 5 * k, 12 * k, 9 * k);
  }
  const half = Math.round(size / 2);
  g.globalCompositeOperation = 'overlay'; g.globalAlpha = 0.35; g.drawImage(P.grainCanvas(half, half, 12), 0, 0, size, size);
  g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1;
  return base;
}

// The mosaic: four rows of four overlapping prints, each a touch rotated, misregistered and differently exposed, with a
// white border captioned along its foot with the place, the battle's date and the print's number. The captions stay generic
// (no sortie, squadron or camera) so nothing on them reads as an archival record.
function mosaic(base, b, size) {
  const cv = P.canvas(size, size), m = cv.getContext('2d'), id = hash(b.id), rnd = mulberry32(id);
  const pw = size * 0.32, ph = size * 0.3, cap = Math.max(16, size * 0.01), [y, mo, d] = (b.date ?? '1944-06-06').split('-');
  const place = (b.place ?? b.name).split(',')[0].toUpperCase(), date = `${+d}.${ROMAN[+mo - 1]}.${y.slice(2)}`;
  m.fillStyle = TABLE; m.fillRect(0, 0, size, size);
  m.font = `700 ${(cap * 0.68).toFixed(1)}px ${TELE}`; m.textBaseline = 'middle';
  let frame = 1;
  for (let r = 0; r < 4; r++) for (let c = 0; c < 4; c++) {
    const cx = size * (c * 0.2467 + 0.1267) + (rnd() - 0.5) * size * 0.017, cy = size * (r * 0.24 + 0.133) + (rnd() - 0.5) * size * 0.017, a = (rnd() - 0.5) * 0.035;
    m.save(); m.translate(cx, cy); m.rotate(a);
    m.fillStyle = 'rgba(0,0,0,0.2)'; m.fillRect(-pw / 2 + 4, -ph / 2 + 6, pw, ph); m.fillRect(-pw / 2 + 9, -ph / 2 + 12, pw, ph); // its shadow on the print below
    m.save(); m.beginPath(); m.rect(-pw / 2, -ph / 2, pw, ph); m.clip(); m.rotate(-a);
    m.drawImage(base, -cx + (rnd() - 0.5) * 6, -cy + (rnd() - 0.5) * 6);
    const ex = rnd(); m.fillStyle = ex > 0.5 ? `rgba(255,252,240,${((ex - 0.5) * 0.18).toFixed(3)})` : `rgba(10,12,6,${((0.5 - ex) * 0.3).toFixed(3)})`; m.fillRect(-cx, -cy, size, size);
    const hot = m.createRadialGradient(0, 0, 0, 0, 0, pw * 0.75); hot.addColorStop(0, 'rgba(255,255,255,0.05)'); hot.addColorStop(1, 'rgba(0,0,0,0.22)'); m.fillStyle = hot; m.fillRect(-pw, -ph, 2 * pw, 2 * ph);
    m.restore();
    m.strokeStyle = CHALK; m.lineWidth = 7; m.strokeRect(-pw / 2, -ph / 2, pw, ph);
    m.fillStyle = CHALK; m.fillRect(-pw / 2, ph / 2 - cap, pw, cap);
    m.fillStyle = '#1b1b18'; m.fillText(`${place}   ${date}   PRINT ${frame++} OF 16`, -pw / 2 + 12, ph / 2 - cap / 2);
    m.restore();
  }
  return cv;
}

// WGS84 to UTM metres, [easting, northing], for numbering the kilometre grid. The grid is drawn square to the map, so it
// leans off true UTM by the grid convergence (under a degree on these sheets).
function utm(lat, lon) {
  const a = 6378137, f = 1 / 298.257223563, e2 = f * (2 - f), ep2 = e2 / (1 - e2), k0 = 0.9996, rad = Math.PI / 180;
  const lon0 = (Math.floor((lon + 180) / 6) * 6 - 177) * rad, p = lat * rad, s = Math.sin(p), c = Math.cos(p), tn = Math.tan(p);
  const N = a / Math.sqrt(1 - e2 * s * s), T = tn * tn, C = ep2 * c * c, A = c * (lon * rad - lon0);
  const M = a * ((1 - e2 / 4 - (3 * e2 ** 2) / 64 - (5 * e2 ** 3) / 256) * p - ((3 * e2) / 8 + (3 * e2 ** 2) / 32 + (45 * e2 ** 3) / 1024) * Math.sin(2 * p) +
    ((15 * e2 ** 2) / 256 + (45 * e2 ** 3) / 1024) * Math.sin(4 * p) - ((35 * e2 ** 3) / 3072) * Math.sin(6 * p));
  const E = k0 * N * (A + ((1 - T + C) * A ** 3) / 6 + ((5 - 18 * T + T * T + 72 * C - 58 * ep2) * A ** 5) / 120) + 500000;
  const Nn = k0 * (M + N * tn * ((A * A) / 2 + ((5 - T + 9 * C + 4 * C * C) * A ** 4) / 24 + ((61 - 58 * T + T * T + 600 * C - 330 * ep2) * A ** 6) / 720));
  return [E, lat < 0 ? Nn + 1e7 : Nn];
}

function build(b, T, dpr) {
  const dem = P.makeDem(b, T), L = P.layerSpace(b, dem);
  const [E0, N0] = b.origin ? utm(b.origin.lat, b.origin.lon) : [b.extent / 2, b.extent / 2];
  const sheet = {
    layer: mosaic(ground(b, dem, L), b, L.size), iv: P.interval(dem, 5), dpr, looks: looks(b), counters: new Map(), E0, N0, gridX: [], gridY: [], tails: null,
    units: [...b.units].sort((p, q) => q.strength - p.strength), // the biggest unit claims an arrow where two converge
    // Smokeless powder: dust and a little smoke, a quarter of what the same fire makes in black powder (`rate`).
    smoke: { sprites: [1, 2, 3, 4].map(s => P.puffSprite(64, s + 50, '150,150,140', '70,70,64', 0.8)), alpha: 0.55, grow: 2, life: 1.2, rate: 0.25 },
    flash: P.glowSprite(32, [[0, 'rgba(255,255,240,1)'], [0.2, 'rgba(255,220,140,0.9)'], [0.5, 'rgba(255,140,40,0.35)'], [1, 'rgba(255,100,20,0)']]),
  };
  cur = { sheet, dark: 0 };
  return sheet;
}

// ---------- the overlay ----------

// The kilometre grid on the prints, under everything else; over() numbers it at the edge of the clear part of the window.
function grid(ctx, V) {
  const S = V.sheet, h = V.B.extent / 2, ox = V.sx(0), oy = V.sy(0);
  const x0 = Math.max(-h, -ox / V.z), x1 = Math.min(h, (V.W - ox) / V.z), y0 = Math.max(-h, (oy - V.H) / V.z), y1 = Math.min(h, oy / V.z);
  const top = Math.max(0, V.sy(h)), bot = Math.min(V.H, V.sy(-h)), lft = Math.max(0, V.sx(-h)), rgt = Math.min(V.W, V.sx(h));
  S.gridX.length = S.gridY.length = 0;
  ctx.beginPath();
  for (let e = Math.ceil((S.E0 + x0) / 1000) * 1000; e <= S.E0 + x1; e += 1000) { const x = V.sx(e - S.E0); ctx.moveTo(x, top); ctx.lineTo(x, bot); S.gridX.push([x, pad2(Math.floor(e / 1000) % 100)]); }
  for (let n = Math.ceil((S.N0 + y0) / 1000) * 1000; n <= S.N0 + y1; n += 1000) { const y = V.sy(n - S.N0); ctx.moveTo(lft, y); ctx.lineTo(rgt, y); S.gridY.push([y, pad2(Math.floor(n / 1000) % 100)]); }
  ctx.save(); ctx.setLineDash([7, 5]); ctx.lineWidth = 1; ctx.strokeStyle = 'rgba(240,238,226,0.5)'; ctx.stroke(); ctx.restore(); // dashed, unlike the prints' solid borders
}

// Hollow chinagraph arrows: each sizeable unit's advance since the chapter before this one, drawn to just behind it.
// Arrows whose heads would meet are one thrust, drawn once; shafts are capped so a long march stays an arrow.
function arrows(ctx, V) {
  const S = V.sheet, ev = eventAt(V.B, V.t), i = V.B.events.indexOf(ev);
  if (i < 1) return;
  const t0 = V.B.events[i - 1].t;
  if (S.tails?.t0 !== t0) S.tails = { t0, at: new Map(V.B.units.map(u => [u, unitAt(u, t0)])) };
  const tips = [], paths = new Map();
  for (const u of S.units) {
    const p = u.pose, q = S.tails.at.get(u);
    if (!p || !q || p.state === 'surrender' || Math.hypot(p.x - q.x, p.y - q.y) < 120) continue;
    const rad = (p.h * Math.PI) / 180, x1 = V.sx(p.x) - Math.sin(rad) * 34, y1 = V.sy(p.y) + Math.cos(rad) * 34; // 34 px behind its front
    let x0 = V.sx(q.x), y0 = V.sy(q.y);
    const len = Math.hypot(x1 - x0, y1 - y0);
    if (len < 40 || tips.some(([x, y]) => Math.hypot(x - x1, y - y1) < 140)) continue;
    tips.push([x1, y1]);
    if (len > 240) { x0 = x1 - ((x1 - x0) * 240) / len; y0 = y1 - ((y1 - y0) * 240) / len; }
    const side = V.B.sides[u.side], path = paths.get(side) ?? paths.set(side, new Path2D()).get(side);
    arrowPath(path, x0, y0, x1, y1);
  }
  ctx.save(); ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  for (const [side, path] of paths) {
    ctx.translate(1, 1.5); ctx.lineWidth = 3.4; ctx.strokeStyle = 'rgba(0,0,0,0.4)'; ctx.stroke(path); ctx.translate(-1, -1.5);
    ctx.lineWidth = 2.6; ctx.strokeStyle = S.looks.get(side).pattern; ctx.globalAlpha = 0.9; ctx.stroke(path); ctx.globalAlpha = 1;
  }
  ctx.restore();
}
function arrowPath(c, x0, y0, x1, y1) {
  const L = Math.hypot(x1 - x0, y1 - y0), ux = (x1 - x0) / L, uy = (y1 - y0) / L, nx = -uy, ny = ux, bw = 8, hw = 17, hl = 22;
  const bx = x1 - ux * hl, by = y1 - uy * hl, mx = (x0 + bx) / 2, my = (y0 + by) / 2;
  c.moveTo(x0 + nx * 3, y0 + ny * 3);
  c.quadraticCurveTo(mx + nx * (bw + 4), my + ny * (bw + 4), bx + nx * bw, by + ny * bw);
  c.lineTo(bx + nx * hw, by + ny * hw); c.lineTo(x1, y1); c.lineTo(bx - nx * hw, by - ny * hw); c.lineTo(bx - nx * bw, by - ny * bw);
  c.quadraticCurveTo(mx - nx * (bw - 4), my - ny * (bw - 4), x0 - nx * 3, y0 - ny * 3);
}

// The grid's numbers, the last two figures of each kilometre, in the window's margins as a sheet numbers its grid at the
// edge: eastings top and bottom, northings left and right, each left off where a panel covers it.
function over(ctx, V) {
  const S = V.sheet, bot = V.safe.bar - 12, free = (x, y) => !V.avoid.some(p => x > p.l - 6 && x < p.r + 6 && y > p.t - 10 && y < p.b + 10);
  const t = (text, x, y, align) => free(x, y) && P.haloText(ctx, text, x, y, `600 14px ${NUM}`, '#f1efe2', 'rgba(14,14,10,0.8)', 3.5, 0, align);
  for (const [x, n] of S.gridX) if (x > 16 && x < V.W - 16) { t(n, x + 4, 12, 'left'); t(n, x + 4, bot, 'left'); }
  for (const [y, n] of S.gridY) if (y > 24 && y < bot - 16) { t(n, 8, y - 9, 'left'); t(n, V.W - 8, y - 9, 'right'); }
}

// ---------- units ----------

// A tank seen from above, nose toward -y: hull on its tracks, turret, gun. `s` is its length in px.
function tankTop(ctx, s) {
  const w = s * 0.58;
  ctx.fillRect(-w / 2, -s / 2, w, s);
  ctx.beginPath(); ctx.arc(0, s * 0.06, s * 0.21, 0, 7); ctx.fill();
  ctx.fillRect(-s * 0.045, -s * 0.78, s * 0.09, s * 0.8);
}
// A tank from the side, facing right, standing on (x, y): tracks, hull, turret, gun. `s` is its length in px.
function tankSide(g, x, y, s) {
  g.beginPath(); g.roundRect(x, y - s * 0.22, s, s * 0.22, s * 0.11); g.fill();
  g.fillRect(x + s * 0.08, y - s * 0.36, s * 0.84, s * 0.16);
  g.fillRect(x + s * 0.3, y - s * 0.52, s * 0.36, s * 0.17);
  g.fillRect(x + s * 0.62, y - s * 0.47, s * 0.48, s * 0.06);
}
// Armor's vehicles where the app laid them out (U.dots, one per tank): each a tank, drawn larger than its real 6 m so
// it reads as one, set back behind the bracket and turned the way the unit faces.
function tanks(ctx, U, color) {
  if (!U.dots) return;
  const s = P.clamp(6.5 * U.z, 16, 24), D = U.dots;
  ctx.fillStyle = color;
  for (let i = 0; i < D.length; i += 2) { ctx.save(); ctx.translate(D[i], D[i + 1]); ctx.rotate(U.a); ctx.translate(0, s * 0.9); tankTop(ctx, s); ctx.restore(); }
}

// The unit as the table shows it: its men as dark specks on the print (pale at night), or its tanks, and a chinagraph
// bracket along its front, hooked back at the ends, with an arrow the way it faces. Guns sit in pits. The counter is its label.
function unit(ctx, U) {
  const look = cur.sheet.looks.get(U.side), night = cur.dark > 0.5, w = U.w / 2, hook = Math.min(U.h + 3, 10), L = U.go ? 20 : 13;
  (U.type === 'armor' ? tanks : P.menDots)(ctx, U, night ? 'rgba(214,218,200,0.75)' : 'rgba(18,20,14,0.85)');
  const shape = () => {
    ctx.beginPath(); ctx.moveTo(-w, -2 + hook); ctx.lineTo(-w, -2); ctx.lineTo(w, -2); ctx.lineTo(w, -2 + hook);
    ctx.moveTo(0, -5); ctx.lineTo(0, -2 - L); ctx.moveTo(-4.5, 3.5 - L); ctx.lineTo(0, -2 - L); ctx.lineTo(4.5, 3.5 - L);
  };
  ctx.save(); ctx.globalAlpha = U.rout ? 0.5 : 1; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  if (U.mil) ctx.setLineDash([6, 4]); // militia and riflemen: a broken bracket
  ctx.translate(U.x + 1, U.y + 1.5); ctx.rotate(U.a); // the pencil's shadow on the print, down and right whatever the facing
  if (U.art) for (const x of P.gunXs(U)) { ctx.fillStyle = 'rgba(12,12,9,0.8)'; ctx.beginPath(); ctx.arc(x, 4, 4.5, 0, 7); ctx.fill(); }
  shape(); ctx.lineWidth = 3.6; ctx.strokeStyle = 'rgba(0,0,0,0.45)'; ctx.stroke();
  ctx.rotate(-U.a); ctx.translate(-1, -1.5); ctx.rotate(U.a);
  if (U.art) for (const x of P.gunXs(U)) { // a gun in its pit, the spoil thrown up round it
    ctx.strokeStyle = 'rgba(225,222,205,0.75)'; ctx.lineWidth = 1.3; ctx.beginPath(); ctx.arc(x, 4, 5.5, 0, 7); ctx.stroke();
    ctx.strokeStyle = '#11120d'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(x, 4); ctx.lineTo(x, -6); ctx.stroke();
  }
  shape(); ctx.lineWidth = 2.6; ctx.strokeStyle = U.gone ? '#a4a49a' : look.wax; ctx.stroke(); // solid: the skips barely show this thin, and cost a fifth of a ms in software
  ctx.restore();
}

// A unit's counter: a painted block, darker along its foot for its thickness, with the side's chinagraph colour down its
// left edge and its name stencilled on it, its shadow baked in; an armor counter carries a tank before the name. Painted
// once per size and kept.
function counter(text, look, fs, mil, gone, dpr, tank = false) {
  const m = P.canvas(1, 1).getContext('2d'); m.font = `700 ${fs}px ${STENCIL}`;
  const ts = tank ? Math.round(fs * 1.3) : 0, tw = tank ? ts + 6 : 0;
  const w = Math.round(m.measureText(text).width + 19) + tw, h = fs + 10, pad = 8, paint = gone ? { top: '#8e8e86', edge: '#5c5c56', text: '#1a1a18' } : mil ? look.light : look.paint;
  const c = P.canvas((w + pad * 2 + 6) * dpr, (h + pad * 2 + 8) * dpr), g = c.getContext('2d');
  g.scale(dpr, dpr);
  g.filter = 'blur(2.5px)'; g.fillStyle = 'rgba(0,0,0,0.6)'; g.fillRect(pad + 3, pad + 5, w, h); g.filter = 'none';
  g.fillStyle = paint.edge; g.fillRect(pad, pad + 2, w, h);
  g.fillStyle = paint.top; g.fillRect(pad, pad, w, h - 2);
  g.fillStyle = 'rgba(255,255,255,0.22)'; g.fillRect(pad, pad, w, 1.5);
  g.fillStyle = gone ? '#6e6e68' : look.wax; g.fillRect(pad, pad, 5, h - 2);
  g.font = m.font; g.fillStyle = paint.text; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(text, pad + 3 + tw + (w - tw) / 2, pad + h / 2);
  if (tank) tankSide(g, pad + 10, pad + h / 2 + ts * 0.26, ts);
  return { c, w, h, pad, dpr };
}
const fontSize = l => Math.round(P.clamp(l.size - 1, 13, 15));
function counterFor(l) {
  const S = cur.sheet, mil = l.U.mil, gone = l.U.gone, fs = fontSize(l), key = `${l.u.id}|${fs}|${mil}|${gone}`;
  return S.counters.get(key) ?? S.counters.set(key, counter(l.text.toUpperCase(), S.looks.get(l.U.side), fs, mil, gone, S.dpr, l.U.type === 'armor')).get(key);
}
const label = {
  place(l) { const U = l.U, d = Math.min(U.h, 30) + 16; l.x = U.x - Math.sin(U.a) * d; l.y = U.y + Math.cos(U.a) * d; }, // behind the unit's rear
  measure: (ctx, l) => { const k = counterFor(l); return [k.w + 6, k.h + 6]; },
  draw(ctx, l) { // laid by hand: each counter a few degrees off true
    const k = counterFor(l), a = ((Math.abs(hash(l.u.id)) % 100) / 100 - 0.5) * 0.12;
    ctx.save(); ctx.translate(l.x, l.y); ctx.rotate(a); if (l.U.rout) ctx.globalAlpha = 0.6;
    ctx.drawImage(k.c, -k.w / 2 - k.pad, -k.h / 2 - k.pad, k.c.width / k.dpr, k.c.height / k.dpr);
    ctx.restore();
  },
};

// Tracer: every fifth round leaves bright dashes flying out along the line of fire, added light in its side's colour.
function fire(ctx, V, pops, n) {
  ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.lineCap = 'round';
  for (const [side, look] of V.sheet.looks) {
    ctx.beginPath();
    let any = false;
    for (let i = 0; i < n; i++) {
      const q = pops[i];
      if (q.k >= 0.2 || q.art || V.B.sides[q.side] !== side) continue;
      const len = Math.min(420, (60 + q.k * 5 * 260) * V.z), head = (q.age / q.life) * len + 8, x = V.sx(q.x), y = V.sy(q.y);
      for (let d = 0; d < 3; d++) { const a = head - d * 31, c = Math.max(4, a - 9); if (a <= 4) break; ctx.moveTo(x + q.dx * c, y - q.dy * c); ctx.lineTo(x + q.dx * a, y - q.dy * a); any = true; }
    }
    if (!any) continue;
    const [r, g, b] = look.tracer;
    ctx.lineWidth = 5; ctx.strokeStyle = `rgba(${r},${g},${b},0.35)`; ctx.stroke();
    ctx.lineWidth = 1.6; ctx.strokeStyle = `rgb(${Math.min(255, r + 120)},${Math.min(255, g + 120)},${Math.min(255, b + 120)})`; ctx.stroke();
  }
  ctx.restore();
}

// ---------- air ----------

// An aircraft seen from above, nose toward -y, `s` px across the wings: the inverted gull wing, fuselage and tailplane of
// a Ju 87. `grow` thickens every stroke, for a pale outline drawn under it.
function plane(ctx, s, grow = 0) {
  const k = s / 2, line = (w, ...p) => { ctx.lineWidth = w * s + grow; ctx.beginPath(); for (let i = 0; i < p.length; i += 2) (i ? ctx.lineTo : ctx.moveTo).call(ctx, p[i] * k, p[i + 1] * k); ctx.stroke(); };
  line(0.15, -1, -0.12, -0.38, 0.06, 0, -0.14, 0.38, 0.06, 1, -0.12);
  line(0.12, 0, -0.78, 0, 0.82);
  line(0.08, -0.3, 0.74, 0.3, 0.74);
}
const DAKOTA = [[0.12, -1, 0.04, -0.3, -0.1, 0.3, -0.1, 1, 0.04], [0.12, 0, -0.6, 0, 0.75], [0.08, -0.32, 0.68, 0.32, 0.68], [0.09, -0.28, -0.3, -0.28, -0.08], [0.09, 0.28, -0.3, 0.28, -0.08]];
const HORSA = [[0.15, -1, -0.12, 1, -0.12], [0.13, 0, -0.62, 0, 0.74], [0.09, -0.3, 0.66, 0.3, 0.66]];
const PASS = [{ stroke: 'rgba(0,0,0,0.28)', grow: 0, throwX: 22, throwY: 30 }, { stroke: 'rgba(236,235,226,0.55)', grow: 2.5, throwX: 0, throwY: 0 }, { stroke: '#262925', grow: 0, throwX: 0, throwY: 0 }];
const XYH = 3, XYH_ALT = 4, HORSA_PX = 31;
function fleet(ctx, V, sh, buf, n, st, s, pass, i0 = 0) {
  const k = s / 2;
  ctx.strokeStyle = pass.stroke;
  for (let j = 0; j < sh.length; j++) {
    const p = sh[j];
    ctx.lineWidth = p[0] * s + pass.grow; ctx.beginPath();
    for (let i = i0; i < i0 + n; i++) {
      const o = i * st, up = st === XYH_ALT ? 0.06 + buf[o + 3] : 1, a = (buf[o + 2] * Math.PI) / 180, c = Math.cos(a), sn = Math.sin(a);
      const x = V.sx(buf[o]) + pass.throwX * up, y = V.sy(buf[o + 1]) + pass.throwY * up;
      for (let q = 1; q < p.length; q += 2) { const u = p[q] * k, v = p[q + 1] * k; (q > 1 ? ctx.lineTo : ctx.moveTo).call(ctx, x + u * c - v * sn, y + u * sn + v * c); }
    }
    ctx.stroke();
  }
}
let WING = new Float32Array(0), TOW = new Float32Array(0);
let LANDED = new Float32Array(0);
function drop(ctx, V, D) {
  const night = V.dark > 0.5, sx = V.sx, sy = V.sy, rc = Math.max(3, 5 * V.z), first = night ? 1 : 0;
  ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  if (D.nChute) {
    const w = V.B.wind, wl = Math.hypot(w?.x ?? 0, w?.y ?? 0), l = Math.max(4, 7 * V.z), dx = wl ? (w.x / wl) * l : l, dy = wl ? (-w.y / wl) * l : 0;
    ctx.beginPath();
    for (let i = 0; i < D.nChute; i++) { const x = sx(D.chutes[2 * i]), y = sy(D.chutes[2 * i + 1]); ctx.moveTo(x, y); ctx.lineTo(x + dx, y + dy); }
    ctx.lineWidth = Math.max(2, 3 * V.z); ctx.strokeStyle = 'rgba(236,235,226,0.55)'; ctx.stroke();
  }
  if (D.nGlider) { // a glider aloft is drawn at a Dakota's size and shrinks to its size on the map as it comes down
    const g = D.gliders, sg = P.clamp(27 * V.z, 9, 30);
    if (LANDED.length < g.length) LANDED = new Float32Array(g.length);
    let nl = 0;
    for (let i = 0; i < D.nGlider; i++) if (!g[4 * i + 3]) { for (let q = 0; q < 4; q++) LANDED[4 * nl + q] = g[4 * i + q]; nl++; }
    for (let p = first; p < 3; p++) {
      fleet(ctx, V, HORSA, LANDED, nl, XYH_ALT, sg, PASS[p]);
      for (let i = 0; i < D.nGlider; i++) if (g[4 * i + 3]) fleet(ctx, V, HORSA, g, 1, XYH_ALT, sg + (HORSA_PX - sg) * g[4 * i + 3], PASS[p], i);
    }
  }
  if (D.nMen) {
    const d = Math.max(2.2, 1.8 * V.z); ctx.fillStyle = night ? 'rgba(214,218,200,0.75)' : 'rgba(18,20,14,0.85)';
    for (let i = 0; i < D.nMen; i++) ctx.fillRect(sx(D.men[2 * i]) - d / 2, sy(D.men[2 * i + 1]) - d / 2, d, d);
  }
  for (let p = first; p < 2 && D.nCanopy; p++) {
    const ox = p ? 0 : 14, oy = p ? 0 : 18;
    ctx.beginPath();
    for (let i = 0; i < D.nCanopy; i++) { const o = 3 * i, a = D.canopies[o + 2], r = rc * (1 + 0.6 * a), x = sx(D.canopies[o]) + ox * a, y = sy(D.canopies[o + 1]) + oy * a; ctx.moveTo(x + r, y); ctx.arc(x, y, r, 0, 7); }
    if (!p) { ctx.fillStyle = 'rgba(0,0,0,0.25)'; ctx.fill(); continue; }
    ctx.fillStyle = 'rgba(240,238,228,0.95)'; ctx.fill(); ctx.lineWidth = 0.8; ctx.strokeStyle = '#262925'; ctx.stroke();
  }
  if (D.nCraft) {
    const k = 1 / V.z, glider = D.kind === 'glider';
    if (WING.length < 9 * D.nCraft) { WING = new Float32Array(9 * D.nCraft); TOW = new Float32Array(9 * D.nCraft); }
    let n = 0;
    for (let i = 0; i < D.nCraft; i++) {
      const o = 3 * i, a = (D.craft[o + 2] * Math.PI) / 180, ux = Math.sin(a), uy = Math.cos(a);
      for (let w = -1; w <= 1; w++) {
        const back = Math.abs(w) * 30 * k, out = w * 38 * k, q = 3 * n++;
        WING[q] = D.craft[o] - ux * back + uy * out; WING[q + 1] = D.craft[o + 1] - uy * back - ux * out; WING[q + 2] = TOW[q + 2] = D.craft[o + 2];
        TOW[q] = WING[q] - ux * 46 * k; TOW[q + 1] = WING[q + 1] - uy * 46 * k;
      }
    }
    if (glider) {
      ctx.beginPath();
      for (let q = 0; q < 3 * n; q += 3) { ctx.moveTo(sx(WING[q]), sy(WING[q + 1])); ctx.lineTo(sx(TOW[q]), sy(TOW[q + 1])); }
      ctx.lineWidth = 0.8; ctx.strokeStyle = '#262925'; ctx.stroke();
      for (let p = first; p < 3; p++) fleet(ctx, V, HORSA, TOW, n, XYH, HORSA_PX, PASS[p]);
    }
    for (let p = first; p < 3; p++) fleet(ctx, V, DAKOTA, WING, n, XYH, 34, PASS[p]);
  }
  ctx.restore();
}

// An air strike: a flight of three diving across the target on the strike's heading, round and round while it lasts, each
// with its shadow thrown down and right on the ground below. The app drops the bombs. `clock` is real seconds of play.
function air(ctx, V, f, clock, D) {
  if (D) return drop(ctx, V, D);
  const h = ((f.h ?? 0) * Math.PI) / 180, dx = Math.sin(h), dy = -Math.cos(h), R = Math.max(280, (f.spread ?? 150) * 8 * V.z);
  const cx = V.sx(f.at[0]), cy = V.sy(f.at[1]);
  ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  for (let i = 0; i < 3; i++) {
    const d = (((clock / 7 + i * 0.03) % 1) * 2 - 1) * R, o = i - 1, back = Math.abs(o) * 30; // the wingmen echeloned behind the leader
    const x = cx + dx * (d - back) - dy * o * 38, y = cy + dy * (d - back) + dx * o * 38;
    for (const [ox, oy, col, grow] of [[22, 30, 'rgba(0,0,0,0.28)', 0], [0, 0, 'rgba(236,235,226,0.55)', 2.5], [0, 0, '#262925', 0]]) {
      ctx.save(); ctx.translate(x + ox, y + oy); ctx.rotate(h); ctx.strokeStyle = col; plane(ctx, 30, grow); ctx.restore();
    }
  }
  ctx.restore();
}

// ---------- the bar ----------

// The sector clock: red, yellow and blue five-minute sectors round the dial, with its hands at the battle's time.
const DIAL = '<svg class="dial" viewBox="-50 -50 100 100" aria-hidden="true"><circle r="48" fill="#ece6d2" stroke="#111" stroke-width="2"/>' +
  [...Array(12)].map((_, i) => {
    const a0 = ((i * 30 - 90) * Math.PI) / 180, a1 = (((i + 1) * 30 - 90) * Math.PI) / 180, p = (a, r) => `${(Math.cos(a) * r).toFixed(2)} ${(Math.sin(a) * r).toFixed(2)}`;
    return `<path d="M0 0L${p(a0, 46)}A46 46 0 0 1 ${p(a1, 46)}Z" fill="${['#c8372a', '#e4b532', '#2d5fa8'][i % 3]}" opacity="0.85"/>`;
  }).join('') + '<circle r="30" fill="#ece6d2"/>' +
  [...Array(12)].map((_, i) => `<line y1="-24" y2="-30" stroke="#111" stroke-width="2" transform="rotate(${i * 30})"/>`).join('');
const dial = (h, m) => `${DIAL}<line y2="-17" stroke="#111" stroke-width="4" stroke-linecap="round" transform="rotate(${((h % 12) + m / 60) * 30})"/>` +
  `<line y2="-40" stroke="#111" stroke-width="2.5" stroke-linecap="round" transform="rotate(${m * 6})"/><circle r="3" fill="#111"/></svg>`;

const mon = i => MONTHS[i].toUpperCase();

export default {
  id: 'ww2',
  fonts: 'https://fonts.googleapis.com/css2?family=Stardos+Stencil:wght@400;700&family=Courier+Prime:wght@400;700&family=Oswald:wght@400;600&display=swap',
  faces: [`700 13px ${STENCIL}`, `700 13px ${TELE}`, `13px ${TELE}`, `600 14px ${NUM}`],
  kicker: 'Operations Room',
  paper: '#85867a',
  night: [61, 66, 86],
  ring: ['rgba(255,214,110,0.45)', '#ffd257'],
  build,
  feature,
  preview(b) { // a battle of another war on this table: olive drab against field grey, the last side listed the enemy
    const ids = Object.keys(b.sides), drab = [['#5f6538', '#7c834c'], ['#7a6f48', '#968a60'], ['#4d5a3c', '#6a7752']];
    ids.forEach((id, i) => Object.assign(b.sides[id], i === ids.length - 1
      ? { color: '#6c7169', light: '#8b9087', dark: '#3a3e38', wax: RED, tracer: [150, 255, 150] }
      : { color: drab[i % 3][0], light: drab[i % 3][1], dark: '#33361f', wax: YELLOW, tracer: [255, 120, 70] }));
  },
  surround(ctx, r, V) { // the bare table round the mosaic
    if (r.l <= 0 && r.t <= 0 && r.r >= V.W && r.b >= V.H) return;
    ctx.fillStyle = TABLE;
    ctx.fillRect(0, 0, V.W, r.t); ctx.fillRect(0, r.b, V.W, V.H - r.b); ctx.fillRect(0, r.t, r.l, r.b - r.t); ctx.fillRect(r.r, r.t, V.W - r.r, r.b - r.t);
  },
  placeName(ctx, f, x, y) { // the interpreter's white ink
    const font = `700 13px ${TELE}`, text = f.name.toUpperCase();
    ctx.letterSpacing = '1px';
    P.haloText(ctx, text, x, y, font, '#f1efe4', 'rgba(16,16,12,0.7)', 3.5, (-(f.rot ?? 0) * Math.PI) / 180);
    ctx.font = font; const w = ctx.measureText(text).width;
    ctx.letterSpacing = '0px';
    return w;
  },
  under(ctx, V) { cur.dark = V.dark; grid(ctx, V); arrows(ctx, V); },
  fallen: { color: s => cur.sheet.looks.get(s).wax, mark(ctx, x, y, d) { const k = d * 0.6; ctx.moveTo(x - k, y); ctx.lineTo(x + k, y); ctx.moveTo(x, y - k); ctx.lineTo(x, y + k); } },
  unit,
  label,
  over,
  fire,
  air,
  ambient(el) { // the lamp: a warm pool over the table falling off into the dark room, swaying a little on its flex (CSS)
    el.innerHTML = '<div class="lamp"></div>';
    el.firstChild.style.backgroundImage = `${P.grainURL(256, 31, [24, 22, 16], r => r * 46)}, var(--lamp)`;
  },
  clock(t) {
    const { h, m, day, month } = clockParts(t);
    return [`${dial(h, m)}${pad2(h)}${pad2(m)}`, day == null ? 'HRS' : `HRS ${day} ${mon(month)}`];
  },
  hours(t) {
    const { h, day, month } = clockParts(t);
    return h === 0 && day != null ? `${day} ${mon(month)}` : `${pad2(h)}00`;
  },
  when(ev, b) { // the teleprinter's header: about the hour, unless the sources record the time
    const exact = ev.when != null, at = exact ? ev.t : Math.round(ev.t / 3600) * 3600, { h, m, day, month } = clockParts(at);
    const [, mo, d] = (b.date ?? '').split('-').map(Number), date = day != null ? `${day} ${mon(month)}` : d ? `${d} ${mon(mo - 1)}` : '';
    return `${exact && !/about/i.test(ev.when) ? '' : 'ABOUT '}${pad2(h)}${pad2(m)} HRS${date ? ` · ${date}` : ''}`;
  },
  time(t) { const { h, m } = clockParts(t); return `${pad2(h)}${pad2(m)}`; },
  legend: {
    text: {
      infantry: b => `Infantry: a chinagraph bracket along its front, in its side’s colour. Each dark speck is ${b.menPerDot} men.`,
      facing: () => 'The arrow from the front shows which way a unit faces.',
      militia: () => 'Militia and riflemen: a broken bracket, and their counters in the lighter shade.',
      column: () => 'A column on the march: a narrow front and a long trail of men.',
      cavalry: () => 'Cavalry: taller specks, a mounted man each.',
      artillery: () => 'Artillery: guns in their pits.',
      armor: () => 'Armor: a tank for each vehicle, and a tank on its counter.',
      airstrike: () => 'Air attack: dive bombers over the target, and their bombs bursting.',
      drop: b => `Airborne landing: Dakotas over the zone, a parachute for every ${b.menPerDot} men or a Horsa glider, and the men making for their unit.`,
      rout: () => 'Broken and running: faded.',
      surrender: () => 'Surrendered: grey.',
      fallen: b => `Where men fell: a small cross for every ${b.menPerDot} men a unit lost, in that side’s chinagraph.`,
      fire: () => 'Muzzle flashes, tracer (one round in five), and dust and smoke drifting downwind.',
      fence: () => 'Hedgerow along a fence line.',
      woods: () => 'Woods: tree crowns and their shadows.',
      field: () => 'Ploughed field.',
      contours: () => 'Relief as the camera saw it: slopes lit from the north-west.',
    },
    swatch: {
      woods: g => { const st = crowns(), r = mulberry32(3); for (let i = 0; i < 16; i++) { const s = st[i % 4]; g.drawImage(s, 4 + r() * 50, r() * 20); } },
      contours: g => { const gr = g.createLinearGradient(8, 4, 56, 24); gr.addColorStop(0, '#c9c9bd'); gr.addColorStop(0.5, '#8a8b80'); gr.addColorStop(1, '#4d4f47'); g.fillStyle = gr; g.beginPath(); g.ellipse(32, 14, 26, 11, -0.2, 0, 7); g.fill(); },
      water: g => { g.fillStyle = '#2a2f29'; g.fillRect(0, 12, 64, 16); P.stroke(g, [[0, 12], [64, 12]], 'rgba(205,208,192,0.7)', 1.2); P.stroke(g, [[0, 15.5], [64, 15.5]], '#c8cbbd', 0.6, 0.25); },
      field: g => { const p = [[8, 3], [62, 3], [62, 26], [8, 26]]; g.fillStyle = 'rgba(196,196,176,0.9)'; P.polyPath(g, p); g.fill(); P.rule(g, p, 0, 2.6, '#3e4036', 0.9, 0.35); },
      airstrike: (g, sheet) => {
        g.drawImage(sheet.flash, 34, 6, 22, 22); g.drawImage(sheet.smoke.sprites[0], 38, 4, 20, 20);
        g.lineCap = 'round'; g.lineJoin = 'round'; g.translate(20, 13); g.rotate(1.2);
        g.strokeStyle = 'rgba(236,235,226,0.55)'; plane(g, 22, 2); g.strokeStyle = '#262925'; plane(g, 22);
      },
      drop: g => {
        g.lineCap = 'round'; g.lineJoin = 'round';
        for (const [x, y, r] of [[40, 8, 4.5], [53, 15, 3.6]]) { g.fillStyle = 'rgba(0,0,0,0.25)'; g.beginPath(); g.arc(x + 5, y + 6, r, 0, 7); g.fill(); g.fillStyle = 'rgba(240,238,228,0.95)'; g.beginPath(); g.arc(x, y, r, 0, 7); g.fill(); g.lineWidth = 0.8; g.strokeStyle = '#262925'; g.stroke(); }
        g.fillStyle = 'rgba(18,20,14,0.85)'; for (const [x, y] of [[36, 23], [44, 25], [50, 22], [58, 24]]) g.fillRect(x - 1.1, y - 1.1, 2.2, 2.2);
        const at = { sx: x => x, sy: y => y }, craft = Float32Array.of(17, 14, 70);
        for (let p = 1; p < 3; p++) fleet(g, at, DAKOTA, craft, 1, XYH, 26, PASS[p]);
      },
    },
    extra: (b, sheet) => [
      [(g, s) => { // the side's shortest name, cut to fit
        const name = b.units.filter(x => b.sides[x.side] === s).map(x => x.short ?? x.name).sort((p, q) => p.length - q.length)[0] ?? 'HQ';
        const k = counter(name.toUpperCase().slice(0, 7), sheet.looks.get(s), 11, false, false, 2); g.drawImage(k.c, 32 - k.w / 2 - k.pad, 14 - k.h / 2 - k.pad, k.c.width / 2, k.c.height / 2);
      },
        'A counter for each unit, painted in its side’s colour and stencilled with its name, behind its front.'],
      [(g, s) => { const p = new Path2D(); arrowPath(p, 6, 20, 58, 9); g.lineJoin = 'round'; g.lineWidth = 2; g.strokeStyle = sheet.looks.get(s).pattern; g.stroke(p); },
        'Axis of advance: where a unit has come from since the chapter before this one.'],
      [g => { g.strokeStyle = 'rgba(236,235,226,0.7)'; g.lineWidth = 1; g.beginPath(); g.moveTo(22.5, 0); g.lineTo(22.5, 28); g.moveTo(0, 14.5); g.lineTo(64, 14.5); g.stroke(); P.haloText(g, '08', 25, 23, `600 10px ${NUM}`, '#f1efe2', 'rgba(14,14,10,0.8)', 2.5, 0, 'left'); },
        'The kilometre grid, numbered at the edge of the map.'],
    ],
  },
};

// The start screen draws its backdrop for this war with the skin's own counters and arrows (splash.js).
export { counter, looks, arrowPath };
