// Drawing helpers the skins share: the elevation model, contours, line work, trees, water, sprites. DOM canvas only.
import { hash, mulberry32 } from '../sim.js';

export const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
export const canvas = (w, h) => { const c = document.createElement('canvas'); c.width = Math.max(1, Math.round(w)); c.height = Math.max(1, Math.round(h)); return c; };
export const sprite = (size, fn) => { const c = canvas(size, size); fn(c.getContext('2d'), size); return c; };
export const hex = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
export const mix = (a, b, f) => a.map((v, i) => v + (b[i] - v) * f);
export function rampOf(stops) { // [[f, '#hex'], ...] to f => [r, g, b]
  const S = stops.map(([f, h]) => [f, hex(h)]);
  return f => { for (let i = 1; i < S.length; i++) if (f <= S[i][0]) return mix(S[i - 1][1], S[i][1], (f - S[i - 1][0]) / (S[i][0] - S[i - 1][0] || 1)); return S[S.length - 1][1]; };
}

function inPoly(x, y, poly) {
  let inside = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

// ---------- the ground ----------

// Elevation with gaps filled, slope, and a hillshade lit from the north-west, all per DEM cell; `sample` reads any of
// them bilinearly at world metres.
export function makeDem(b, T) {
  const { cols, rows, spacing } = T, E = b.extent, ex = b.terrainExaggeration ?? 2;
  let zmin = Infinity, zmax = -Infinity;
  for (const v of T.z) if (v) { if (v < zmin) zmin = v; if (v > zmax) zmax = v; }
  const Z = Float32Array.from(T.z, v => v || zmin);
  const at = (r, c) => Z[clamp(r, 0, rows - 1) * cols + clamp(c, 0, cols - 1)];
  const n = rows * cols, shade = new Float32Array(n), GX = new Float32Array(n), GY = new Float32Array(n);
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const gx = (at(r, c + 1) - at(r, c - 1)) / (2 * spacing), gy = (at(r - 1, c) - at(r + 1, c)) / (2 * spacing), i = r * cols + c;
    GX[i] = gx; GY[i] = gy;
    const ax = gx * ex, ay = gy * ex;
    shade[i] = Math.max(0, (0.5 * ax - 0.5 * ay + 0.707) / Math.hypot(ax, ay, 1));
  }
  const sample = (A, x, y) => {
    const fc = clamp((x + E / 2) / spacing - 0.5, 0, cols - 1.001), fr = clamp((E / 2 - y) / spacing - 0.5, 0, rows - 1.001);
    const c = Math.floor(fc), r = Math.floor(fr), u = fc - c, v = fr - r, i = r * cols + c;
    return (A[i] * (1 - u) + A[i + 1] * u) * (1 - v) + (A[i + cols] * (1 - u) + A[i + cols + 1] * u) * v;
  };
  return { Z, cols, rows, spacing, zmin, zmax, shade, GX, GY, sample, E, ex, water: b.water };
}

// The layer: an offscreen canvas covering the whole extent, `size` px square, with world and DEM-grid projections.
export function layerSpace(b, dem) {
  const size = Math.min(3072, Math.max(1024, Math.round(b.extent))), E = b.extent, pxm = size / E, sc = dem.spacing * pxm;
  return { size, pxm, sc, x: wx => (wx + E / 2) * pxm, y: wy => (E / 2 - wy) * pxm, gx: c => (c + 0.5) * sc, gy: r => (r + 0.5) * sc,
    wx: px => px / pxm - E / 2, wy: py => E / 2 - py / pxm, pts: P => P.map(([x, y]) => [(x + E / 2) * pxm, (E / 2 - y) * pxm]) };
}

// Marching squares over cell centres. Corner bits: top-left 8, top-right 4, bottom-right 2, bottom-left 1.
export function contours(Z, cols, rows, lv, seg) {
  const f = (p, q) => (lv - p) / (q - p);
  for (let r = 0; r < rows - 1; r++) for (let c = 0; c < cols - 1; c++) {
    const a = Z[r * cols + c], b = Z[r * cols + c + 1], d = Z[(r + 1) * cols + c + 1], e = Z[(r + 1) * cols + c];
    const idx = (a >= lv ? 8 : 0) | (b >= lv ? 4 : 0) | (d >= lv ? 2 : 0) | (e >= lv ? 1 : 0);
    if (!idx || idx === 15) continue;
    const top = [c + f(a, b), r], right = [c + 1, r + f(b, d)], bot = [c + f(e, d), r + 1], left = [c, r + f(a, e)];
    const L = { 1: [left, bot], 2: [bot, right], 3: [left, right], 4: [top, right], 5: [top, right, left, bot], 6: [top, bot], 7: [top, left], 8: [top, left],
      9: [top, bot], 10: [top, left, right, bot], 11: [top, right], 12: [left, right], 13: [bot, right], 14: [left, bot] }[idx];
    for (let i = 0; i < L.length; i += 2) seg(L[i][0], L[i][1], L[i + 1][0], L[i + 1][1]);
  }
}

// Contour polylines {lv, pts} in grid coordinates (col, row of cell centres), segments chained end to end so they can
// be smoothed, labelled and hung with hachures.
export function contourLines(dem, iv, levels = null) {
  const { Z, cols, rows, zmin, zmax } = dem, out = [];
  const lvs = levels ?? []; if (!levels) for (let lv = Math.ceil(zmin / iv) * iv; lv <= zmax; lv += iv) lvs.push(lv);
  for (const lv of lvs) {
    const segs = [];
    contours(Z, cols, rows, lv, (x0, y0, x1, y1) => segs.push([[x0, y0], [x1, y1]]));
    for (const pts of chain(segs)) out.push({ lv, pts });
  }
  return out;
}
function chain(segs) {
  const key = p => `${Math.round(p[0] * 1e4)},${Math.round(p[1] * 1e4)}`, ends = new Map(), used = new Uint8Array(segs.length);
  segs.forEach((s, i) => { for (const p of s) { const k = key(p); (ends.get(k) ?? ends.set(k, []).get(k)).push(i); } });
  const next = p => { for (const i of ends.get(key(p)) ?? []) if (!used[i]) return i; return -1; };
  const lines = [];
  for (let i = 0; i < segs.length; i++) {
    if (used[i]) continue;
    used[i] = 1;
    const line = [segs[i][0], segs[i][1]];
    for (let dir = 0; dir < 2; dir++) for (;;) {
      const tail = dir ? line[0] : line[line.length - 1], j = next(tail);
      if (j < 0) break;
      used[j] = 1;
      const s = segs[j], other = key(s[0]) === key(tail) ? s[1] : s[0];
      if (dir) line.unshift(other); else line.push(other);
    }
    lines.push(line);
  }
  return lines;
}
// A contour interval no finer than `iv` that keeps the sheet to about `most` lines.
export const interval = (dem, iv, most = 45) => { let k = iv; while ((dem.zmax - dem.zmin) / k > most) k *= 2; return k; };

// Relief colour from a ramp over elevation, lit by the hillshade, one pixel per DEM cell: scale it up smooth.
export function reliefCanvas(dem, ramp, { k0 = 0.55, k1 = 0.6, shadeOnly = false } = {}) {
  const { cols, rows, Z, zmin, zmax, shade } = dem, c = canvas(cols, rows), g = c.getContext('2d'), img = g.createImageData(cols, rows);
  for (let i = 0; i < cols * rows; i++) {
    const f = (Z[i] - zmin) / (zmax - zmin || 1), k = shadeOnly ? 1 : k0 + k1 * shade[i], col = ramp(f, shade[i]);
    for (let ch = 0; ch < 3; ch++) img.data[i * 4 + ch] = col[ch] * k;
    img.data[i * 4 + 3] = 255;
  }
  g.putImageData(img, 0, 0);
  return c;
}

// Hachures: rows of short downhill strokes hung from fine contours, heavier on steep and shadowed ground.
export function hachures(g, dem, L, lines, hiv, { step = 5, maxLen = 14, minSlope = 0.012, color = '#3d2a18', wMin = 0.45, wMax = 1.7, aMin = 0.25, aMax = 0.85, buckets = 5 } = {}) {
  const ex = dem.ex, paths = Array.from({ length: buckets }, () => []), rnd = mulberry32(99);
  for (const { pts } of lines) {
    const P = pts.map(([c, r]) => [L.gx(c), L.gy(r)]);
    let acc = rnd() * step;
    for (let i = 1; i < P.length; i++) {
      const [x0, y0] = P[i - 1], [x1, y1] = P[i], seg = Math.hypot(x1 - x0, y1 - y0);
      while (acc < seg) {
        const f = acc / seg, x = x0 + (x1 - x0) * f, y = y0 + (y1 - y0) * f, wx = L.wx(x), wy = L.wy(y);
        const gx = dem.sample(dem.GX, wx, wy), gy = dem.sample(dem.GY, wx, wy), s = Math.hypot(gx, gy) * ex;
        if (s > minSlope && !(dem.water != null && dem.sample(dem.Z, wx, wy) <= dem.water)) {
          const sh = dem.sample(dem.shade, wx, wy), k = clamp((s - minSlope) / 0.12, 0, 1) * clamp(1.35 - sh * 0.7, 0.4, 1.2);
          const len = Math.min(maxLen, (hiv / (s / ex)) * L.pxm * 0.95), dx = -gx / (s / ex), dy = gy / (s / ex); // downhill, layer y down
          paths[Math.min(buckets - 1, Math.floor(k * buckets))].push(x, y, x + dx * len, y + dy * len);
        }
        acc += step * (0.85 + rnd() * 0.3);
      }
      acc -= seg;
    }
  }
  g.save(); g.lineCap = 'round'; g.strokeStyle = color;
  paths.forEach((p, b) => {
    const f = (b + 0.5) / buckets; g.lineWidth = wMin + (wMax - wMin) * f; g.globalAlpha = aMin + (aMax - aMin) * f;
    g.beginPath(); for (let i = 0; i < p.length; i += 4) { g.moveTo(p[i], p[i + 1]); g.lineTo(p[i + 2], p[i + 3]); } g.stroke();
  });
  g.restore();
}

// Smooth value-noise fBm over the unit square: f(u, v) in [0, 1].
function fbm(seed, base = 6, octaves = 4, persist = 0.5) {
  const rnd = mulberry32(seed), sm = t => t * t * (3 - 2 * t);
  const oct = [...Array(octaves)].map((_, o) => { const n = base * 2 ** o, a = new Float32Array((n + 1) * (n + 1)); for (let i = 0; i < a.length; i++) a[i] = rnd(); return { n, a, amp: persist ** o }; });
  const tot = oct.reduce((s, o) => s + o.amp, 0);
  return (u, v) => {
    let s = 0;
    for (const { n, a, amp } of oct) {
      const fx = clamp(u, 0, 0.9999) * n, fy = clamp(v, 0, 0.9999) * n, ix = fx | 0, iy = fy | 0, x = sm(fx - ix), y = sm(fy - iy), W = n + 1, i = iy * W + ix;
      s += ((a[i] * (1 - x) + a[i + 1] * x) * (1 - y) + (a[i + W] * (1 - x) + a[i + W + 1] * x) * y) * amp;
    }
    return s / tot;
  };
}

// Where the woods are: the battle's tree density, clumped into woods and glades by noise between `lo` and `hi`, kept off
// cleared polygons, fields and water. A tree is [x, y, random] in layer px.
export function treePoints(b, dem, L, { scale = 1, lo = 0.3, hi = 0.5, seed = 5 } = {}) {
  const rnd = mulberry32(hash(b.id + 'trees')), n = Math.min(90000, Math.round((b.trees?.density ?? 0) * b.extent * b.extent * scale));
  const clear = [...(b.trees?.clear ?? []), ...(b.fields ?? [])], out = [], N = fbm(seed, 5, 4, 0.55);
  for (let i = 0; i < n; i++) {
    const x = rnd() * L.size, y = rnd() * L.size, wx = L.wx(x), wy = L.wy(y);
    if (rnd() > clamp((N(x / L.size, y / L.size) - lo) / (hi - lo), 0, 1)) continue;
    if (dem.water != null && dem.sample(dem.Z, wx, wy) <= dem.water) continue;
    if (clear.some(poly => inPoly(wx, wy, poly))) continue;
    out.push([x, y, rnd()]);
  }
  return out;
}

// Print one of the stamps, picked by the tree's random, centred on each tree.
export function stampTrees(g, stamps, trees) {
  for (const [x, y, k] of trees) { const st = stamps[Math.floor(k * stamps.length)]; g.drawImage(st, x - st.width / 2, y - st.height / 2); }
}

// The woods as a soft sheet from the same noise, fields and clearings cut out. Layer-sized.
export function woodsSheet(b, L, { lo, hi, seed = 5, color, alpha = 0.3, res = 500, edge = 0 }) {
  const N = fbm(seed, 5, 4, 0.55), c = canvas(res, res), g = c.getContext('2d'), img = g.createImageData(res, res);
  if (b.trees?.density) for (let y = 0; y < res; y++) for (let x = 0; x < res; x++) {
    const p = clamp((N(x / res, y / res) - lo) / (hi - lo), 0, 1), i = (y * res + x) * 4;
    img.data[i] = color[0]; img.data[i + 1] = color[1]; img.data[i + 2] = color[2]; img.data[i + 3] = p * alpha * 255;
  }
  g.putImageData(img, 0, 0);
  const out = canvas(L.size, L.size), o = out.getContext('2d');
  o.imageSmoothingEnabled = true; o.imageSmoothingQuality = 'high'; o.drawImage(c, 0, 0, L.size, L.size);
  o.globalCompositeOperation = 'destination-out';
  for (const poly of [...(b.trees?.clear ?? []), ...(b.fields ?? [])]) { polyPath(o, L.pts(poly)); o.fill(); if (edge) { o.lineWidth = edge; o.stroke(); } }
  return out;
}

// Water from the DEM (at or below `b.water`) and `water` polygons: a fill, a shore line and water-lining inside it.
// The DEM mask carries alpha 0.5 exactly where the shore contour runs, so the fill and the line agree.
export function water(g, b, dem, L, { fill, line, lw = 1.4, lining = [], liningColor = line, liningWidth = 0.6 }) {
  const polys = (b.features ?? []).filter(f => f.type === 'water' && f.poly && f.from == null && f.until == null).map(f => L.pts(f.poly));
  if (dem.water == null && !polys.length) return;
  const mask = canvas(L.size, L.size), m = mask.getContext('2d'), shores = [];
  if (dem.water != null) {
    const { cols, rows, Z } = dem, small = canvas(cols, rows), s = small.getContext('2d'), img = s.createImageData(cols, rows);
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
      const i = r * cols + c; let d = 1e-3;
      for (const j of [i - 1, i + 1, i - cols, i + cols]) if (j >= 0 && j < Z.length) d = Math.max(d, Math.abs(Z[j] - Z[i]));
      img.data[i * 4 + 3] = clamp(0.5 + (dem.water - Z[i]) / (2 * d), 0, 1) * 255;
    }
    s.putImageData(img, 0, 0);
    m.imageSmoothingEnabled = true; m.imageSmoothingQuality = 'high'; m.drawImage(small, 0, 0, L.size, L.size);
    for (const { pts } of contourLines(dem, 0, [dem.water])) shores.push(densify(pts.map(([c, r]) => [L.gx(c), L.gy(r)]), 4));
  }
  m.fillStyle = '#000';
  for (const p of polys) { polyPath(m, p); m.fill(); shores.push(densify([...p, p[0]], 4)); }
  const lines = canvas(L.size, L.size), q = lines.getContext('2d');
  q.fillStyle = fill; q.fillRect(0, 0, L.size, L.size);
  for (const s of shores) { const n = normals(s); for (const [d, a] of lining) for (const k of [-1, 1]) stroke(q, offset(s, k * d, n), liningColor, liningWidth, a); }
  q.globalCompositeOperation = 'destination-in'; q.drawImage(mask, 0, 0);
  g.drawImage(lines, 0, 0);
  for (const s of shores) stroke(g, s, line, lw, 1);
}

// ---------- line work ----------

// Catmull-Rom densify: points every ~step px along a smooth curve through pts.
export function densify(pts, step = 3) {
  if (pts.length < 2) return pts;
  const P = [pts[0], ...pts, pts[pts.length - 1]], out = [];
  for (let i = 1; i < P.length - 2; i++) {
    const [p0, p1, p2, p3] = [P[i - 1], P[i], P[i + 1], P[i + 2]];
    const n = Math.max(1, Math.ceil(Math.hypot(p2[0] - p1[0], p2[1] - p1[1]) / step));
    for (let j = 0; j < n; j++) {
      const t = j / n, t2 = t * t, t3 = t2 * t, f = (a, b, c, d) => 0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3);
      out.push([f(p0[0], p1[0], p2[0], p3[0]), f(p0[1], p1[1], p2[1], p3[1])]);
    }
  }
  out.push(pts[pts.length - 1]);
  return out;
}
export const normals = pts => pts.map((p, i) => {
  const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)], dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1;
  return [-dy / l, dx / l];
});
export const offset = (pts, d, nrm = normals(pts)) => pts.map((p, i) => [p[0] + nrm[i][0] * d, p[1] + nrm[i][1] * d]);
function linePath(g, pts) { g.beginPath(); pts.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); }
export function polyPath(g, pts) { linePath(g, pts); g.closePath(); }
export function stroke(g, pts, style, width, alpha = 1, dash = null) {
  g.save(); g.globalAlpha *= alpha; g.strokeStyle = style; g.lineWidth = width; g.lineCap = 'round'; g.lineJoin = 'round';
  if (dash) g.setLineDash(dash);
  linePath(g, pts); g.stroke(); g.restore();
}
// Zig-zag worm fence: rails laid alternately left and right of the line.
export function wormFence(g, pts, amp = 2.6, period = 8, style = '#3b2614', width = 1) {
  const d = densify(pts, 1), n = normals(d);
  g.save(); g.strokeStyle = style; g.lineWidth = width; g.lineJoin = 'miter'; g.beginPath();
  let acc = 0, k = 0;
  for (let i = 0; i < d.length; i++) {
    if (i) acc += Math.hypot(d[i][0] - d[i - 1][0], d[i][1] - d[i - 1][1]);
    if (i === 0 || acc >= period / 2) { acc = 0; const s = k++ % 2 ? amp : -amp, x = d[i][0] + n[i][0] * s, y = d[i][1] + n[i][1] * s; i ? g.lineTo(x, y) : g.moveTo(x, y); }
  }
  g.stroke(); g.restore();
}
// Parallel ruling clipped to a polygon: furrows, hatching.
export function rule(g, poly, angle, gap, style, width, alpha = 1) {
  const xs = poly.map(p => p[0]), ys = poly.map(p => p[1]);
  const cx = (Math.min(...xs) + Math.max(...xs)) / 2, cy = (Math.min(...ys) + Math.max(...ys)) / 2, R = Math.hypot(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys));
  g.save(); polyPath(g, poly); g.clip(); g.translate(cx, cy); g.rotate(angle);
  g.globalAlpha *= alpha; g.strokeStyle = style; g.lineWidth = width; g.beginPath();
  for (let y = -R; y <= R; y += gap) { g.moveTo(-R, y); g.lineTo(R, y); }
  g.stroke(); g.restore();
}
// The furrow angle of a field: along its first edge.
export const furrow = p => Math.atan2(p[1][1] - p[0][1], p[1][0] - p[0][0]);

// Static features baked into the layer through the skin's own `feature` drawing; ones that come and go are drawn per frame.
export const isStatic = f => f.from == null && f.until == null;
export function bakeFeatures(g, b, L, feature, types) {
  for (const f of b.features ?? []) {
    if (!isStatic(f) || !types.includes(f.type)) continue;
    if (f.pts) feature(g, f.type, densify(L.pts(f.pts), 2), 1, false);
    else if (f.poly) feature(g, f.type, L.pts(f.poly), 1, true);
  }
}

// ---------- sprites and sheets ----------

// Seeded value noise rendered by upscaling small random canvases: smooth fBm for paper, mottling, photo grain.
export function noiseCanvas(w, h, { cell = 8, seed = 1, octaves = 4, persist = 0.5 } = {}) {
  const out = canvas(w, h), g = out.getContext('2d'), rnd = mulberry32(seed);
  g.fillStyle = '#808080'; g.fillRect(0, 0, w, h);
  let amp = 1, total = 0;
  for (let o = 0; o < octaves; o++) total += Math.pow(persist, o);
  for (let o = 0; o < octaves; o++) {
    const cw = Math.max(2, Math.ceil(w / cell) + 2), ch = Math.max(2, Math.ceil(h / cell) + 2), small = canvas(cw, ch), sg = small.getContext('2d'), img = sg.createImageData(cw, ch);
    for (let i = 0; i < cw * ch; i++) { const v = rnd() * 255; img.data[i * 4] = img.data[i * 4 + 1] = img.data[i * 4 + 2] = v; img.data[i * 4 + 3] = 255; }
    sg.putImageData(img, 0, 0);
    g.globalAlpha = amp / total; g.imageSmoothingEnabled = cell > 1; g.imageSmoothingQuality = 'high';
    g.drawImage(small, 0, 0, cw * cell, ch * cell);
    amp *= persist; cell = Math.max(1, cell / 2);
  }
  g.globalAlpha = 1;
  return out;
}
// Film grain: an independent grey level per pixel between lo and hi, opaque. Scale it up for coarser grain.
export function grainCanvas(w, h, seed, lo = 0, hi = 255) {
  const c = canvas(w, h), g = c.getContext('2d'), img = g.createImageData(w, h), rnd = mulberry32(seed);
  for (let i = 0; i < w * h; i++) { const v = lo + rnd() * (hi - lo); img.data[i * 4] = img.data[i * 4 + 1] = img.data[i * 4 + 2] = v; img.data[i * 4 + 3] = 255; }
  g.putImageData(img, 0, 0);
  return c;
}
// Soft cloud shadows: thresholded fBm as alpha in one colour. Small; CSS scales it over the window.
export function cloudSheet(w, h, seed, color, maxA = 0.16, lo = 0.52, hi = 0.72) {
  const c = canvas(w, h), g = c.getContext('2d'), N = fbm(seed, 4, 3, 0.5), img = g.createImageData(w, h);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const al = clamp((N(x / w, y / h) - lo) / (hi - lo), 0, 1), i = (y * w + x) * 4;
    img.data[i] = color[0]; img.data[i + 1] = color[1]; img.data[i + 2] = color[2]; img.data[i + 3] = al * al * (3 - 2 * al) * maxA * 255;
  }
  g.putImageData(img, 0, 0);
  return c;
}
// Billowy smoke puff: overlapping soft blobs, the underside darker.
export function puffSprite(size, seed, light, shadow, maxA = 0.9) {
  const c = canvas(size, size), g = c.getContext('2d'), rnd = mulberry32(seed), R = size / 2;
  const blob = (x, y, r, col, a) => { const gr = g.createRadialGradient(x, y, 0, x, y, r); gr.addColorStop(0, `rgba(${col},${a})`); gr.addColorStop(0.6, `rgba(${col},${a * 0.5})`); gr.addColorStop(1, `rgba(${col},0)`); g.fillStyle = gr; g.fillRect(0, 0, size, size); };
  for (let i = 0; i < 6; i++) { const a = rnd() * 6.28, d = rnd() * R * 0.35; blob(R + Math.cos(a) * d + R * 0.08, R + Math.sin(a) * d + R * 0.1, R * (0.45 + rnd() * 0.3), shadow, maxA * 0.35); }
  for (let i = 0; i < 7; i++) { const a = rnd() * 6.28, d = rnd() * R * 0.38; blob(R + Math.cos(a) * d - R * 0.05, R + Math.sin(a) * d - R * 0.06, R * (0.4 + rnd() * 0.3), light, maxA * 0.45); }
  return c;
}
export function glowSprite(size, stops) {
  return sprite(size, g => { const gr = g.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2); for (const [o, col] of stops) gr.addColorStop(o, col); g.fillStyle = gr; g.fillRect(0, 0, size, size); });
}
// A tile of fine grain as a CSS url(), for the paper layers the compositor lays over the map.
export function grainURL(size, seed, rgb, alphaOf) {
  const c = canvas(size, size), g = c.getContext('2d'), img = g.createImageData(size, size), rnd = mulberry32(seed);
  for (let i = 0; i < size * size; i++) { img.data.set(rgb, i * 4); img.data[i * 4 + 3] = alphaOf(rnd()); }
  g.putImageData(img, 0, 0);
  return `url(${c.toDataURL()})`;
}

// ---------- units ----------

// The men of a unit as the app laid them out (U.dots, screen px): squares, or tall marks for horsemen.
export function menDots(ctx, U, color) {
  if (!U.dots) return;
  const d = Math.max(2.2, 1.8 * U.z), P = U.dots;
  ctx.fillStyle = color;
  for (let i = 0; i < P.length; i += 2) U.cav ? ctx.fillRect(P[i] - d / 2, P[i + 1] - d, d, d * 2) : ctx.fillRect(P[i] - d / 2, P[i + 1] - d / 2, d, d);
}
// Each gun's place along the front, in the unit's own frame (x across, y back from the front edge).
export const gunXs = U => Array.from({ length: U.guns }, (_, i) => (i - (U.guns - 1) / 2) * 14 * U.z);
// Where every unit has been, engraved into the layer itself. Dashed strokes cost about a dash each, so redrawing a whole
// battle's tracks every frame would cost milliseconds. Instead each frame draws only the recent legs, those that ended in
// the last `recent` seconds of battle time, darker; about every second and a half the legs that have grown older are cut
// into the plate, fainter. Going back in time restores the clean plate and engraves again. Tracks are [{ u, runs }] per
// side (sim.tracks). style(g, side, scale, fresh) sets the stroke; scale is screen px per layer px, so both halves match.
export function plate(layer, L, bySide, recent, style) {
  const base = canvas(layer.width, layer.height), g = layer.getContext('2d');
  base.getContext('2d').drawImage(layer, 0, 0);
  let cut = -Infinity, at = 0;
  const engrave = (t0, t1) => {
    for (const [side, list] of bySide) {
      g.beginPath();
      for (const { runs } of list) for (const run of runs) for (let i = 3; i < run.length; i += 3) {
        if (run[i] <= t0 || run[i] > t1) continue;
        g.moveTo(L.x(run[i - 2]), L.y(run[i - 1])); g.lineTo(L.x(run[i + 1]), L.y(run[i + 2]));
      }
      g.save(); style(g, side, 1, false); g.stroke(); g.restore();
    }
  };
  return (ctx, V) => {
    const old = V.t - recent;
    if (old < cut) { g.save(); g.globalCompositeOperation = 'copy'; g.drawImage(base, 0, 0); g.restore(); cut = -Infinity; }
    if (cut === -Infinity || (old > cut && performance.now() - at > 1500)) { engrave(cut, old); cut = old; at = performance.now(); }
    const k = V.z / L.pxm;
    for (const [side, list] of bySide) {
      ctx.beginPath();
      for (const { u, runs } of list) for (const run of runs) {
        if (run[0] > V.t) break;
        let i = 0;
        while (i + 3 < run.length && run[i + 3] <= cut) i += 3;
        if (i + 3 >= run.length && run[i] <= cut) continue; // the run ended and is engraved
        ctx.moveTo(V.sx(run[i + 1]), V.sy(run[i + 2]));
        for (i += 3; i < run.length && run[i] <= V.t; i += 3) ctx.lineTo(V.sx(run[i + 1]), V.sy(run[i + 2]));
        if (i < run.length && u.pose) ctx.lineTo(V.sx(u.pose.x), V.sy(u.pose.y));
      }
      ctx.save(); style(ctx, side, k, true); ctx.stroke(); ctx.restore();
    }
  };
}

// Text with a halo, the map-label staple.
export function haloText(g, text, x, y, font, fill, halo, hw = 4, rot = 0, align = 'center') {
  g.save(); g.translate(x, y); if (rot) g.rotate(rot);
  g.font = font; g.textAlign = align; g.textBaseline = 'middle';
  if (halo) { g.lineJoin = 'round'; g.lineWidth = hw; g.strokeStyle = halo; g.strokeText(text, 0, 0); }
  g.fillStyle = fill; g.fillText(text, 0, 0); g.restore();
}
