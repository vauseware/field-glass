import { SPEEDS, STATE_TEXT, normalizeBattle, unitAt, shape, dots, eventAt, advance, defaultSpeed, fmtTime, parseTime, hash, mulberry32, mod } from './sim.js';

const $ = s => document.querySelector(s);
const canvas = $('#map'), ctx = canvas.getContext('2d');
const ui = { play: $('#play'), speed: $('#speed'), scrub: $('#scrub'), clock: $('#clock'), follow: $('#follow'), battle: $('#battle'),
  title: $('#title'), sub: $('#sub'), legend: $('#legend'), caption: $('#caption'), capTitle: $('#cap-title'), capText: $('#cap-text'),
  hover: $('#hover'), sources: $('#sources'), srcBtn: $('#src-btn'), srcList: $('#src-list'), lapse: $('#lapse'),
  marks: $('#marks'), splash: $('#splash'), splashList: $('#splash-list'), plan: $('#plan'), home: $('#home'), legendBtn: $('#legend-btn'), legendDlg: $('#legend-dlg'), legendList: $('#legend-list') };

let B = null, T = null, layer = null;
let t = 0, playing = false, speed = 10, curEvent = null, shownEvent = null;
let cam = { x: 0, y: 0, zoom: 0.5 }, follow = true, lapse = true, lapsing = false;
let W = 0, H = 0, DPR = 1, last = performance.now();
const smoke = [], flashes = [], placed = []; // placed: label boxes drawn this frame, so labels avoid each other
let mouse = null;

// ---------- loading ----------

async function loadBattle(id) {
  const [raw, terrain] = await Promise.all([
    fetch(`battles/${id}/battle.json`).then(r => r.json()),
    fetch(`battles/${id}/terrain.json`).then(r => r.json()),
  ]);
  const b = normalizeBattle(raw);
  layer = buildLayer(b, terrain);
  B = b; T = terrain;
  smoke.length = 0; curEvent = shownEvent = null;
  setPlaying(false);
  speed = SPEEDS.includes(b.speed) ? b.speed : 10;
  const dur = b.endT - b.startT;
  ui.speed.innerHTML = '';
  for (const s of SPEEDS) if (s <= 120 || dur / s >= 120) ui.speed.add(new Option(`${s}×`, s)); // the big speeds only when the battle lasts
  ui.speed.value = speed;
  ui.scrub.min = b.startT; ui.scrub.max = b.endT;
  buildMarks(b); buildLegend(b);
  ui.title.textContent = b.name;
  ui.sub.textContent = `${b.place} · ${b.dateText ?? b.date}`;
  ui.legend.innerHTML = Object.values(b.sides).map(s => `<span><i style="background:${s.color}"></i>${s.name}</span>`).join('');
  ui.srcList.innerHTML = (b.sources ?? []).map(s => `<li>${s}</li>`).join('');
  const v = b.view ?? { x: 0, y: 0, width: b.extent };
  cam = { x: v.x, y: v.y, zoom: Math.min(W, H) / v.width };
  follow = true; ui.follow.checked = true; lapse = true; ui.lapse.checked = true;
  clampCam();
  const [, , at, play, warp, legend] = location.hash.match(/^#([^@,]*)(?:@([^,]+))?(,play)?(,warp)?(,legend)?$/) ?? [];
  seek(at ? parseTime(at) : b.startT);
  if (play) setPlaying(true);
  if (legend) ui.legendDlg.showModal(); // screenshots
  document.body.classList.toggle('nofade', !!warp); // screenshots: skip the caption fade
  if (warp) for (let i = 0; i < 300; i++) step(1 / 60); // five seconds of frames for screenshots
  location.hash = id;
}

function rgb(hex) { return [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16)); }

// Shaded relief with contour lines, drawn once per battle into an offscreen canvas covering the whole extent.
function buildLayer(b, T) {
  const { cols, rows, spacing } = T, size = Math.min(3072, Math.max(1024, Math.round(b.extent))), ex = b.terrainExaggeration ?? 2;
  let zmin = Infinity, zmax = -Infinity;
  for (const v of T.z) if (v) { if (v < zmin) zmin = v; if (v > zmax) zmax = v; }
  const Z = T.z.map(v => v || zmin);
  const at = (r, c) => Z[Math.min(rows - 1, Math.max(0, r)) * cols + Math.min(cols - 1, Math.max(0, c))];
  const small = document.createElement('canvas'); small.width = cols; small.height = rows;
  const sg = small.getContext('2d'), img = sg.createImageData(cols, rows);
  const lo = rgb(b.palette?.ground ?? '#a8ad7a'), hi = rgb(b.palette?.high ?? '#d2cb9e'), water = rgb(b.palette?.water ?? '#7f9fc0');
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const gx = ((at(r, c + 1) - at(r, c - 1)) / (2 * spacing)) * ex, gy = ((at(r - 1, c) - at(r + 1, c)) / (2 * spacing)) * ex;
    const shade = Math.max(0, (0.5 * gx - 0.5 * gy + 0.707) / Math.hypot(gx, gy, 1)); // light from the north-west
    const f = (Z[r * cols + c] - zmin) / (zmax - zmin || 1), k = 0.55 + 0.6 * shade, i = (r * cols + c) * 4;
    const wet = b.water != null && Z[r * cols + c] <= b.water; // river or sea: the DEM flattens it to one level
    for (let ch = 0; ch < 3; ch++) img.data[i + ch] = wet ? water[ch] : (lo[ch] + (hi[ch] - lo[ch]) * f) * k;
    img.data[i + 3] = 255;
  }
  sg.putImageData(img, 0, 0);
  const cv = document.createElement('canvas'); cv.width = cv.height = size;
  const g = cv.getContext('2d');
  g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high';
  g.drawImage(small, 0, 0, size, size);
  const sc = size / cols, iv = b.contourInterval ?? 5;
  g.strokeStyle = 'rgba(80,60,30,0.3)'; g.lineWidth = Math.max(1, size / 1500); g.beginPath();
  for (let lv = Math.ceil(zmin / iv) * iv; lv <= zmax; lv += iv)
    contours(Z, cols, rows, lv, (x0, y0, x1, y1) => { g.moveTo((x0 + 0.5) * sc, (y0 + 0.5) * sc); g.lineTo((x1 + 0.5) * sc, (y1 + 0.5) * sc); });
  g.stroke();
  const pxm = size / b.extent, toPx = ([x, y]) => [(x + b.extent / 2) * pxm, (b.extent / 2 - y) * pxm];
  // Fields: cleared, lighter ground. They are also kept free of trees below.
  g.fillStyle = b.palette?.field ?? 'rgba(232,220,170,0.45)';
  for (const poly of b.fields ?? []) { g.beginPath(); poly.map(toPx).forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); g.closePath(); g.fill(); }
  // Trees are static, so they live in the layer: a tree is ~2 m across, which is about one layer pixel.
  const rnd = mulberry32(hash(b.id + 'trees')), n = Math.min(60000, Math.round((b.trees?.density ?? 0) * b.extent * b.extent));
  g.fillStyle = b.palette?.tree ?? 'rgba(60,85,40,0.5)';
  const clear = [...(b.trees?.clear ?? []), ...(b.fields ?? [])]; // polygons in world metres with no trees
  for (let i = 0; i < n; i++) {
    const x = rnd() * size, y = rnd() * size, r = (1.5 + rnd() * 1.5) * pxm;
    if (clear.some(poly => inPoly(x / pxm - b.extent / 2, b.extent / 2 - y / pxm, poly))) continue;
    if (b.water != null && Z[Math.floor(y / sc) * cols + Math.floor(x / sc)] <= b.water) continue;
    g.beginPath(); g.arc(x, y, r, 0, 6.2832); g.fill();
  }
  return cv;
}

function inPoly(x, y, poly) {
  let inside = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

// Marching squares over cell centres. Corner bits: top-left 8, top-right 4, bottom-right 2, bottom-left 1.
function contours(Z, cols, rows, lv, seg) {
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

// ---------- camera ----------

const w2sx = x => (x - cam.x) * cam.zoom + W / 2;
const w2sy = y => (cam.y - y) * cam.zoom + H / 2;
const minZoom = () => Math.max(W, H) / B.extent; // the map always covers the viewport

function clampCam() {
  cam.zoom = Math.min(12, Math.max(minZoom(), cam.zoom));
  const h = B.extent / 2, rx = Math.max(0, h - W / 2 / cam.zoom), ry = Math.max(0, h - H / 2 / cam.zoom);
  cam.x = Math.max(-rx, Math.min(rx, cam.x));
  cam.y = Math.max(-ry, Math.min(ry, cam.y));
}
function zoomAt(sx, sy, f) {
  const nz = Math.min(12, Math.max(minZoom(), cam.zoom * f));
  const wx = cam.x + (sx - W / 2) / cam.zoom, wy = cam.y - (sy - H / 2) / cam.zoom;
  cam.zoom = nz; cam.x = wx - (sx - W / 2) / nz; cam.y = wy + (sy - H / 2) / nz;
  clampCam();
}
function userMoved() { if (follow) { follow = false; ui.follow.checked = false; } }

function updateCamera(dt) {
  if (!follow || !curEvent?.at) return;
  const k = 1 - Math.exp(-dt * 1.2);
  const tz = Math.min(12, Math.max(minZoom(), Math.min(W, H) / (curEvent.view ?? B.extent * 0.6)));
  cam.x += (curEvent.at[0] - cam.x) * k;
  cam.y += (curEvent.at[1] - cam.y) * k;
  cam.zoom *= Math.exp(Math.log(tz / cam.zoom) * k);
  clampCam();
}

const ptrs = new Map();
let pinch = 0;
canvas.addEventListener('pointerdown', e => { ptrs.set(e.pointerId, [e.clientX, e.clientY]); canvas.setPointerCapture(e.pointerId); });
canvas.addEventListener('pointermove', e => {
  mouse = [e.clientX, e.clientY];
  if (!ptrs.has(e.pointerId)) return;
  const prev = ptrs.get(e.pointerId);
  ptrs.set(e.pointerId, [e.clientX, e.clientY]);
  if (ptrs.size === 1) {
    cam.x -= (e.clientX - prev[0]) / cam.zoom; cam.y += (e.clientY - prev[1]) / cam.zoom;
    clampCam(); userMoved();
  } else if (ptrs.size === 2) {
    const [a, b] = [...ptrs.values()], d = Math.hypot(a[0] - b[0], a[1] - b[1]);
    if (pinch) zoomAt((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, d / pinch);
    pinch = d; userMoved();
  }
});
const up = e => { ptrs.delete(e.pointerId); pinch = 0; };
canvas.addEventListener('pointerup', up);
canvas.addEventListener('pointercancel', up);
canvas.addEventListener('pointerleave', () => { mouse = null; });
canvas.addEventListener('wheel', e => { e.preventDefault(); zoomAt(e.clientX, e.clientY, Math.exp(-e.deltaY * 0.0012)); userMoved(); }, { passive: false });

// ---------- drawing ----------

const smokeSprite = (() => {
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const g = c.getContext('2d'), r = g.createRadialGradient(32, 32, 2, 32, 32, 32);
  r.addColorStop(0, 'rgba(238,236,226,0.9)'); r.addColorStop(0.5, 'rgba(228,226,216,0.4)'); r.addColorStop(1, 'rgba(220,220,210,0)');
  g.fillStyle = r; g.fillRect(0, 0, 64, 64);
  return c;
})();

function label(text, x, y, rot, color, size, italic, bold) {
  ctx.save(); ctx.translate(x, y);
  if (rot) ctx.rotate((-rot * Math.PI) / 180);
  ctx.font = `${italic ? 'italic ' : ''}${bold ? '600 ' : ''}${size}px system-ui, sans-serif`;
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.lineWidth = 4; ctx.strokeStyle = 'rgba(245,240,225,0.9)'; ctx.strokeText(text, 0, 0);
  ctx.fillStyle = color; ctx.fillText(text, 0, 0);
  ctx.restore();
}

// Advance the clock, camera, unit poses and smoke by dt real seconds. Drawing reads the results.
function step(dt) {
  if (playing) {
    [t, lapsing] = advance(B, t, dt, speed, lapse);
    if (t >= B.endT) setPlaying(false);
  }
  const ev = eventAt(B, t);
  if (ev !== curEvent) { // a chapter may set its own pace while the story is being followed
    curEvent = ev;
    if (follow) { speed = ev?.speed ?? defaultSpeed(B); ui.speed.value = speed; }
  }
  updateCamera(dt);
  flashes.length = 0;
  for (const u of B.units) {
    const p = (u.pose = unitAt(u, t));
    if (playing && p && p.fire > 0 && p.state !== 'surrender') { const { F, nd } = shape(u, p, B.menPerDot); emit(u, p, F, nd, dt); }
  }
  if (playing) for (const f of B.features ?? []) { // burning town or ship: a standing pall of smoke while the feature is active
    if (f.type !== 'smoke' || (f.from != null && t < f.from) || (f.until != null && t >= f.until)) continue;
    const wind = B.wind ?? { x: 0.8, y: 0.3 }, sp = f.spread ?? 60;
    let n = Math.floor(f.rate * dt + Math.random());
    while (n-- > 0 && smoke.length < 2500) smoke.push({ x: f.at[0] + (Math.random() - 0.5) * sp, y: f.at[1] + (Math.random() - 0.5) * sp,
      vx: wind.x * 2 + Math.random() - 0.5, vy: wind.y * 2 + Math.random() - 0.5, age: 0, life: 8 + Math.random() * 4, r0: 8, r1: 50 });
  }
  if (!playing) return;
  let w = 0;
  for (const s of smoke) {
    s.age += dt;
    if (s.age >= s.life) continue;
    s.x += s.vx * dt; s.y += s.vy * dt;
    smoke[w++] = s;
  }
  smoke.length = w;
}

function draw() {
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  ctx.fillStyle = '#0d0f14'; ctx.fillRect(0, 0, W, H);
  const half = B.extent / 2;
  ctx.imageSmoothingEnabled = true;
  ctx.drawImage(layer, w2sx(-half), w2sy(half), B.extent * cam.zoom, B.extent * cam.zoom);
  drawFeatures(); drawFallen(); drawUnits(); drawFlashes(); drawSmoke(); drawNight();
}

const FEATURE_STYLE = { road: ['rgba(90,70,40,0.6)', 6, '#dccb9f', 4], creek: ['rgba(40,70,120,0.5)', 4, '#7aa8dc', 2.2], fence: ['rgba(70,50,30,0.6)', 2],
  works: ['rgba(50,35,15,0.9)', 7, 'rgba(210,180,120,0.95)', 3.5], trench: ['rgba(50,35,15,0.85)', 5, 'rgba(175,145,95,0.9)', 2.2] };
const POLY_FILL = { redoubt: 'rgba(210,180,120,0.85)', battery: 'rgba(210,180,120,0.85)', ship: 'rgba(70,50,35,0.95)', camp: 'rgba(255,255,255,0.25)' };
function drawFeatures() {
  const z = cam.zoom;
  placed.length = 0;
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  for (const f of B.features ?? []) {
    if ((f.from != null && t < f.from) || (f.until != null && t >= f.until)) continue; // siegeworks dug, ships burnt
    if (f.poly) {
      ctx.beginPath();
      f.poly.forEach(([x, y], i) => (i ? ctx.lineTo(w2sx(x), w2sy(y)) : ctx.moveTo(w2sx(x), w2sy(y))));
      ctx.closePath();
      if (f.type === 'water') { ctx.fillStyle = B.palette?.water ?? '#7f9fc0'; ctx.fill(); continue; } // a shoreline the modern ground no longer shows
      ctx.fillStyle = POLY_FILL[f.type] ?? POLY_FILL.redoubt; ctx.fill();
      ctx.strokeStyle = 'rgba(50,35,15,0.9)'; ctx.lineWidth = Math.max(1.5, 2 * z); ctx.stroke();
    }
    if (f.pts) {
      ctx.beginPath();
      f.pts.forEach(([x, y], i) => (i ? ctx.lineTo(w2sx(x), w2sy(y)) : ctx.moveTo(w2sx(x), w2sy(y))));
      const [c1, w1, c2, w2] = FEATURE_STYLE[f.type] ?? ['#000', 1];
      ctx.strokeStyle = c1; ctx.lineWidth = Math.max(w1, w1 * z * 0.8); ctx.stroke();
      if (c2) { ctx.strokeStyle = c2; ctx.lineWidth = Math.max(w2, w2 * z * 0.8); ctx.stroke(); }
    }
    if (f.name && f.at) {
      const x = w2sx(f.at[0]), y = w2sy(f.at[1]);
      label(f.name, x, y, f.rot ?? 0, 'rgba(60,45,25,0.9)', 14, true);
      if (!f.rot) { const w = ctx.measureText(f.name).width + 6; placed.push([x - w / 2, y - 9, x + w / 2, y + 9]); }
    }
  }
}

function drawFallen() {
  const d = Math.max(2.5, 1.6 * cam.zoom);
  ctx.globalAlpha = 0.6;
  for (const [side, s] of Object.entries(B.sides)) {
    ctx.fillStyle = s.dark ?? '#3a2a20';
    for (const f of B.fallen) {
      if (f.t > t) break;
      if (f.side === side) ctx.fillRect(w2sx(f.x) - d / 2, w2sy(f.y) - d / 2, d, d);
    }
  }
  ctx.globalAlpha = 1;
}

function drawUnits() {
  const z = cam.zoom, mpd = B.menPerDot, labels = [];
  for (const u of B.units) {
    const p = u.pose;
    if (!p) continue;
    const sx = w2sx(p.x), sy = w2sy(p.y);
    u.screen = [sx, sy];
    const { ranks, F, rankD } = shape(u, p, mpd), D = ranks * rankD, ext = Math.max(F, D) * z + 40;
    if (sx < -ext || sy < -ext || sx > W + ext || sy > H + ext) continue;
    const side = B.sides[u.side], gone = p.state === 'surrender', militia = u.type === 'militia' || u.type === 'riflemen';
    // Solid body with a dark outline so a unit reads at any zoom; it never shrinks below a few pixels.
    const wPx = Math.max(16, F * z), hPx = Math.max(7, D * z);
    ctx.save(); ctx.translate(sx, sy); ctx.rotate((p.h * Math.PI) / 180);
    ctx.globalAlpha = p.state === 'rout' ? 0.5 : 0.85;
    ctx.fillStyle = gone ? '#9a9a92' : militia ? side.light ?? side.color : side.color;
    ctx.fillRect(-wPx / 2, -2, wPx, hPx + 3);
    ctx.globalAlpha = 1; ctx.lineWidth = 1.5; ctx.strokeStyle = gone ? '#55554f' : side.dark ?? '#000';
    ctx.strokeRect(-wPx / 2, -2, wPx, hPx + 3);
    ctx.restore();
    if (F * z >= 24) {
      const pts = dots(u, p, mpd), d = Math.max(2.5, 2 * z), cav = u.type === 'cavalry';
      ctx.fillStyle = gone ? '#e8e8e2' : 'rgba(255,255,255,0.92)';
      for (let i = 0; i < pts.length; i += 2) {
        const x = w2sx(pts[i]), y = w2sy(pts[i + 1]);
        if (cav) ctx.fillRect(x - d / 2, y - d, d, d * 2); else ctx.fillRect(x - d / 2, y - d / 2, d, d);
      }
    }
    if (u.type === 'artillery') drawGuns(u, p, z);
    // Every unit offers a label just above its topmost corner (a marching column is narrow but long); the overlap pass below thins them.
    const s = Math.sin((p.h * Math.PI) / 180), c = Math.cos((p.h * Math.PI) / 180);
    const top = -Math.abs((wPx / 2) * s) + Math.min(-2 * c, (hPx + 1) * c);
    labels.push({ text: u.short ?? u.name, x: sx, y: sy + top - 11, size: Math.min(17, 12 + z * 3), men: p.strength });
  }
  // Bigger units get their label first; a label that would overlap one already placed is dropped this frame.
  for (const l of labels.sort((a, b) => b.men - a.men)) {
    ctx.font = `${l.size}px system-ui, sans-serif`;
    const w = ctx.measureText(l.text).width + 6, h = l.size + 4, r = [l.x - w / 2, l.y - h / 2, l.x + w / 2, l.y + h / 2];
    if (placed.some(q => r[0] < q[2] && r[2] > q[0] && r[1] < q[3] && r[3] > q[1])) continue;
    placed.push(r);
    label(l.text, l.x, l.y, 0, '#141414', l.size, false, true);
  }
}

function drawGuns(u, p, z) {
  const n = u.guns ?? 1, rad = (p.h * Math.PI) / 180, dx = Math.sin(rad), dy = Math.cos(rad), s = Math.max(6, 3.5 * z);
  ctx.fillStyle = '#141414';
  for (let i = 0; i < n; i++) {
    const uu = (i - (n - 1) / 2) * 14;
    ctx.save(); ctx.translate(w2sx(p.x + uu * dy + 2 * dx), w2sy(p.y - uu * dx + 2 * dy)); ctx.rotate(rad);
    ctx.fillRect(-s / 2, -s / 2, s, s * 1.4);
    ctx.restore();
  }
}

function emit(u, p, F, nd, dt) {
  const art = u.type === 'artillery', wind = B.wind ?? { x: 0.8, y: 0.3 };
  const rate = p.fire * (art ? (u.guns ?? 1) * 0.5 : nd * 0.35);
  let n = Math.floor(rate * dt + Math.random());
  const rad = (p.h * Math.PI) / 180, dx = Math.sin(rad), dy = Math.cos(rad);
  while (n-- > 0) {
    const uu = (Math.random() - 0.5) * F, x = p.x + uu * dy + 2 * dx, y = p.y - uu * dx + 2 * dy;
    if (smoke.length < 2500) smoke.push({ x, y, vx: wind.x + dx * 1.2 + Math.random() - 0.5, vy: wind.y + dy * 1.2 + Math.random() - 0.5,
      age: 0, life: art ? 4.5 : 2.4 + Math.random() * 1.6, r0: art ? 4 : 2, r1: art ? 22 : 11 });
    flashes.push(x, y);
  }
}

function drawFlashes() {
  const d = Math.max(2, 1.5 * cam.zoom);
  ctx.fillStyle = '#fff1a8';
  for (let i = 0; i < flashes.length; i += 2) ctx.fillRect(w2sx(flashes[i]) - d / 2, w2sy(flashes[i + 1]) - d / 2, d, d);
  flashes.length = 0;
}

function drawSmoke() {
  const z = cam.zoom;
  for (const s of smoke) {
    const f = s.age / s.life, r = (s.r0 + (s.r1 - s.r0) * f) * z;
    if (r < 0.8) continue;
    ctx.globalAlpha = 0.7 * (1 - f);
    ctx.drawImage(smokeSprite, w2sx(s.x) - r, w2sy(s.y) - r, 2 * r, 2 * r);
  }
  ctx.globalAlpha = 1;
}

// Blue dusk over the map from about 45 minutes before sunrise, and after sunset when the battle gives one.
function drawNight() {
  if (B.sunriseT == null) return;
  const tod = mod(t, 86400), ramp = x => Math.min(1, Math.max(0, x));
  let dark = ramp((B.sunriseT - tod) / 2800);
  if (B.sunsetT != null) dark = Math.max(dark, ramp((tod - B.sunsetT) / 2800));
  if (dark > 0) { ctx.fillStyle = `rgba(15,25,70,${(0.35 * dark).toFixed(3)})`; ctx.fillRect(0, 0, W, H); }
  for (const f of B.tints ?? []) { // weather: a timed wash over the map, fading in and out over ten minutes
    const a = Math.min(1, (t - f.from) / 600, (f.until - t) / 600);
    if (a <= 0) continue;
    ctx.globalAlpha = a; ctx.fillStyle = f.color; ctx.fillRect(0, 0, W, H); ctx.globalAlpha = 1;
  }
}

// ---------- chapter marks and legend ----------

// One tick per chapter above the scrubber. Each label slants up over the map from the top edge of the bar,
// joined to its tick by a leader line, so neighbours can be spread sideways without losing their place in time.
let marks = [], leads = [];
function buildMarks(b) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  ui.marks.replaceChildren(svg);
  leads = []; marks = b.events.map(ev => {
    const el = document.createElement('button');
    el.textContent = ev.title; el.title = `${ev.title} · ${fmtTime(ev.t)}`;
    el.onclick = () => { follow = true; ui.follow.checked = true; seek(ev.t); };
    ui.marks.append(el);
    leads.push(svg.appendChild(document.createElementNS('http://www.w3.org/2000/svg', 'path')));
    return el;
  });
  layoutMarks();
}
function layoutMarks() {
  const tw = ui.marks.clientWidth, dur = B.endT - B.startT, gap = 27; // a 20 px pill at 50° clears its neighbour at 27 px (27·sin 50° > 20)
  const px = B.events.map(ev => ((ev.t - B.startT) / dur) * tw);
  const k = Math.max(1, Math.ceil((marks.length * gap) / Math.max(1, tw))); // too many for the width: label every k-th
  const idx = [...marks.keys()].filter(i => i % k === 0), ax = idx.map(i => px[i]);
  for (let j = 1; j < ax.length; j++) ax[j] = Math.max(ax[j], ax[j - 1] + gap); // push crowded labels right…
  ax[ax.length - 1] = Math.min(ax[ax.length - 1], tw);
  for (let j = ax.length - 2; j >= 0; j--) ax[j] = Math.min(ax[j], ax[j + 1] - gap); // …then back from the end
  marks.forEach((el, i) => { el.hidden = true; leads[i].setAttribute('d', `M${px[i]} 23V15`); });
  idx.forEach((i, j) => {
    marks[i].hidden = false; marks[i].style.left = `${ax[j]}px`;
    leads[i].setAttribute('d', `M${px[i]} 23V15L${ax[j]} 0`);
  });
}

const SVG = (inner, w = 64, h = 28) => `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" aria-hidden="true">${inner}</svg>`;
// A unit block as the map draws it: solid body, dark outline, one white dot per menPerDot men.
function blockSvg(fill, stroke, { w = 56, h = 12, files = 9, ranks = 2, cav = false, alpha = 0.85, dot = 'rgba(255,255,255,0.92)', extra = '' } = {}) {
  const x0 = (64 - w) / 2, y0 = (28 - h) / 2;
  let d = '';
  for (let r = 0; r < ranks; r++) for (let f = 0; f < files; f++)
    d += `<rect x="${(x0 + (w / files) * (f + 0.5) - 1.5).toFixed(1)}" y="${(y0 + (h / ranks) * (r + 0.5) - (cav ? 3 : 1.5)).toFixed(1)}" width="3" height="${cav ? 6 : 3}" fill="${dot}"/>`;
  return SVG(`<rect x="${x0}" y="${y0}" width="${w}" height="${h}" fill="${fill}" stroke="${stroke}" stroke-width="1.5" opacity="${alpha}"/>${d}${extra}`);
}
const lineSvg = (c1, w1, c2, w2) => SVG(`<path d="M4 14 L60 14" stroke="${c1}" stroke-width="${w1}" stroke-linecap="round"/>${c2 ? `<path d="M4 14 L60 14" stroke="${c2}" stroke-width="${w2}" stroke-linecap="round"/>` : ''}`);
const polySvg = (pts, fill, bg) => SVG(`${bg}<polygon points="${pts}" fill="${fill}" stroke="rgba(50,35,15,0.9)" stroke-width="2"/>`);

// Only the symbols this battle uses.
function buildLegend(b) {
  const sides = Object.values(b.sides), s0 = sides[0], mpd = b.menPerDot, iv = b.contourInterval ?? 5;
  const types = new Set(b.units.map(u => u.type)), states = new Set(b.units.flatMap(u => u.keys.map(k => k.state)));
  const feats = new Set((b.features ?? []).map(f => f.type));
  const bg = `<rect width="64" height="28" fill="${b.palette?.ground ?? '#a8ad7a'}"/>`;
  const scatter = (pts, mark) => SVG(`${bg}${pts.map(([x, y], i) => mark(x, y, i)).join('')}`);
  const rows = [
    ...sides.map(s => [SVG(`<rect x="4" y="4" width="56" height="20" rx="3" fill="${s.color}"/>`), s.name]),
    [blockSvg(s0.color, s0.dark), `Infantry. Each white dot is ${mpd} men; the rows are ranks.`],
    (types.has('militia') || types.has('riflemen')) && [blockSvg(s0.light ?? s0.color, s0.dark), 'Militia and riflemen, in the lighter shade.'],
    states.has('column') && [blockSvg(s0.color, s0.dark, { w: 12, h: 26, files: 3, ranks: 6 }), 'A column on the march: narrow and long.'],
    types.has('cavalry') && [blockSvg(s0.color, s0.dark, { h: 16, cav: true }), 'Cavalry: taller dots, a mounted man each.'],
    types.has('artillery') && [blockSvg(s0.color, s0.dark, { w: 42, h: 8, files: 6, ranks: 1, extra: [18, 32, 46].map(x => `<rect x="${x - 2.5}" y="7" width="5" height="7" fill="#141414"/>`).join('') }), 'Artillery. Each dark square is a gun.'],
    (states.has('skirmish') || b.units.some(u => u.loose)) && [blockSvg(s0.color, s0.dark, { h: 7, files: 7, ranks: 1 }), 'Skirmishers and open order: one thin, spread-out rank.'],
    states.has('rout') && [blockSvg(s0.color, s0.dark, { alpha: 0.5 }), 'Broken and running: faded.'],
    states.has('surrender') && [blockSvg('#9a9a92', '#55554f', { dot: '#e8e8e2' }), 'Surrendered: grey.'],
    [scatter([[8, 6], [20, 18], [31, 9], [44, 20], [55, 7], [15, 22], [38, 5], [50, 15], [26, 14]], (x, y, i) => `<rect x="${x}" y="${y}" width="3" height="3" fill="${sides[i % sides.length].dark ?? '#3a2a20'}" opacity="0.6"/>`),
      `Where men fell: a dark mark for every ${mpd} men a unit lost, in that side's colour.`],
    [SVG(`<rect x="22" y="18" width="20" height="6" fill="${s0.color}" stroke="${s0.dark}"/><circle cx="30" cy="12" r="5" fill="#d8d4c8" opacity="0.5"/><circle cx="40" cy="9" r="7" fill="#d8d4c8" opacity="0.4"/><circle cx="50" cy="6" r="8" fill="#d8d4c8" opacity="0.3"/><rect x="26" y="15" width="3" height="3" fill="#fff1a8"/>`),
      'Powder smoke drifts downwind from units firing.'],
    (feats.has('redoubt') || feats.has('battery')) && [polySvg('14,22 14,8 26,4 38,4 50,8 50,22', POLY_FILL.redoubt, bg), 'Redoubt or battery: an earthwork fort.'],
    feats.has('works') && [lineSvg(...FEATURE_STYLE.works), 'Fortified line of earthworks.'],
    feats.has('trench') && [lineSvg(...FEATURE_STYLE.trench), 'Siege trench: the parallels and the approaches between them.'],
    feats.has('camp') && [polySvg('6,6 58,6 58,22 6,22', POLY_FILL.camp, bg), 'Camp.'],
    feats.has('ship') && [polySvg('6,10 54,10 60,16 50,22 10,22', POLY_FILL.ship, bg), 'Ship.'],
    feats.has('road') && [lineSvg(...FEATURE_STYLE.road), 'Road.'],
    feats.has('creek') && [lineSvg(...FEATURE_STYLE.creek), 'Creek or stream.'],
    feats.has('fence') && [lineSvg(...FEATURE_STYLE.fence), 'Fence.'],
    (b.water != null || feats.has('water')) && [SVG(`<rect width="64" height="28" fill="${b.palette?.water ?? '#7f9fc0'}"/>`), 'Water.'],
    b.fields?.length && [SVG(`${bg}<rect x="10" y="4" width="54" height="24" fill="${b.palette?.field ?? 'rgba(232,220,170,0.45)'}"/>`), 'Open field or cleared ground.'],
    b.trees?.density && [scatter([[8, 8], [20, 20], [30, 7], [44, 18], [56, 9], [14, 24], [38, 24], [52, 24], [26, 15]], (x, y) => `<circle cx="${x}" cy="${y}" r="3" fill="${b.palette?.tree ?? 'rgba(60,85,40,0.5)'}"/>`), 'Woods.'],
    [SVG(`${bg}<path d="M0 22 Q16 12 32 16 T64 6 M0 10 Q20 2 40 8 T64 0" fill="none" stroke="rgba(80,60,30,0.5)"/>`), `Contour lines every ${iv} m (${Math.round(iv * 3.28)} ft) of height; shading shows the slopes.`],
  ];
  ui.legendList.innerHTML = rows.filter(Boolean).map(([sw, text]) => `<div>${sw}</div><div>${text}</div>`).join('');
}

// ---------- hud and controls ----------

function updateHud() {
  ui.clock.textContent = (playing && lapsing ? '⏩ ' : '') + fmtTime(t);
  ui.scrub.value = t;
  if (curEvent !== shownEvent) {
    shownEvent = curEvent;
    ui.capTitle.textContent = curEvent?.title ?? '';
    ui.capText.textContent = curEvent?.text ?? '';
    ui.caption.classList.toggle('show', !!curEvent);
    marks.forEach((m, i) => { m.classList.toggle('on', B.events[i] === curEvent); leads[i].classList.toggle('on', B.events[i] === curEvent); });
  }
  let best = null, bd = 28;
  if (mouse) for (const u of B.units) {
    if (!u.pose) continue;
    const d = Math.hypot(u.screen[0] - mouse[0], u.screen[1] - mouse[1]);
    if (d < bd) { bd = d; best = u; }
  }
  ui.hover.hidden = !best;
  if (best) { // tooltip beside the cursor, flipped to the left near the right edge
    ui.hover.style.left = mouse[0] + 360 > W ? `${mouse[0] - 360}px` : `${mouse[0] + 20}px`;
    ui.hover.style.top = `${Math.min(mouse[1] + 20, H - 160)}px`;
  }
  if (best) ui.hover.innerHTML = `<b>${best.name}</b><br>${best.commander ? best.commander + '<br>' : ''}${B.sides[best.side].name} · ${best.type.replace('_', ' ')}<br>${Math.round(best.pose.strength)} men · ${STATE_TEXT[best.pose.state] ?? ''}`;
}

const nudge = () => Math.max(30, (B.endT - B.startT) / 240); // arrow keys: 30 s, or 1/240 of a long battle
function setPlaying(v) { playing = v; ui.play.textContent = v ? '❚❚' : '▶'; ui.play.setAttribute('aria-label', v ? 'Pause' : 'Play'); }
function seek(v) { t = Math.max(B.startT, Math.min(B.endT, v)); smoke.length = 0; }

ui.play.onclick = () => { if (!playing && t >= B.endT) seek(B.startT); setPlaying(!playing); };
ui.speed.onchange = () => { speed = +ui.speed.value; };
ui.scrub.oninput = () => seek(+ui.scrub.value);
ui.follow.onchange = () => { follow = ui.follow.checked; };
ui.lapse.onchange = () => { lapse = ui.lapse.checked; };
ui.battle.onchange = () => loadBattle(ui.battle.value);
ui.srcBtn.onclick = () => ui.sources.showModal();
ui.legendBtn.onclick = () => ui.legendDlg.showModal();
addEventListener('keydown', e => {
  if (['INPUT', 'SELECT', 'BUTTON'].includes(e.target.tagName)) return;
  if (e.code === 'Space') { e.preventDefault(); ui.play.click(); }
  else if (e.key === 'ArrowRight') seek(t + nudge());
  else if (e.key === 'ArrowLeft') seek(t - nudge());
  else if (e.key === 'f') { follow = !follow; ui.follow.checked = follow; }
  else if (e.key === 't') { lapse = !lapse; ui.lapse.checked = lapse; }
});

function resize() {
  DPR = Math.min(2, devicePixelRatio || 1);
  W = innerWidth; H = innerHeight;
  canvas.width = W * DPR; canvas.height = H * DPR;
  canvas.style.width = W + 'px'; canvas.style.height = H + 'px';
}
addEventListener('resize', () => { resize(); if (B) clampCam(); });
new ResizeObserver(() => B && layoutMarks()).observe(ui.marks); // the track also narrows when the clock text widens
resize();

function frame(now) {
  const dt = Math.min(0.1, (now - last) / 1000);
  last = now;
  if (B) { step(dt); draw(); updateHud(); }
  requestAnimationFrame(frame);
}

for (const s of SPEEDS) ui.speed.add(new Option(`${s}×`, s));
const list = (await (await fetch('battles/index.json')).json()).sort((a, b) => a.date.localeCompare(b.date));
const groups = new Map(); // one optgroup per war, in order of each war's first battle
for (const b of list) {
  if (!groups.has(b.war)) { const g = document.createElement('optgroup'); g.label = b.war; groups.set(b.war, g); ui.battle.add(g); }
  groups.get(b.war).append(new Option(b.name, b.id));
}
// ---------- start screen ----------

// A period battle plan as the backdrop: one battle's own contours, roads and creeks in sepia ink, its regiments as
// washed blocks at the hottest moment of the fight, and dashed arrows for where they had come from.
async function drawPlan(cv, entry) {
  const [raw, T] = await Promise.all([fetch(`battles/${entry.id}/battle.json`).then(r => r.json()), fetch(`battles/${entry.id}/terrain.json`).then(r => r.json())]);
  const b = normalizeBattle(raw), g = cv.getContext('2d'), CW = cv.width, CH = cv.height, rnd = mulberry32(hash(b.id + 'plan'));
  try { await document.fonts.load('italic 20px "IM Fell English"'); } catch {}
  // Paper: a warm gradient, darker at the edges, flecked, foxed and folded in four.
  const pg = g.createRadialGradient(CW / 2, CH / 2, CH * 0.2, CW / 2, CH / 2, CW * 0.75);
  pg.addColorStop(0, '#efe2c2'); pg.addColorStop(0.7, '#dcc79a'); pg.addColorStop(1, '#a98455');
  g.fillStyle = pg; g.fillRect(0, 0, CW, CH);
  for (let i = 0; i < 9000; i++) { g.fillStyle = `rgba(90,60,25,${(rnd() * 0.12).toFixed(3)})`; g.fillRect(rnd() * CW, rnd() * CH, 1 + rnd() * 1.5, 1 + rnd() * 1.5); }
  for (let i = 0; i < 14; i++) {
    const x = rnd() * CW, y = rnd() * CH, r = 20 + rnd() * 90, f = g.createRadialGradient(x, y, 0, x, y, r);
    f.addColorStop(0, 'rgba(140,90,40,0.16)'); f.addColorStop(1, 'rgba(140,90,40,0)'); g.fillStyle = f; g.fillRect(x - r, y - r, 2 * r, 2 * r);
  }
  // Focus on the chapter with the most units in action.
  const busy = ev => b.units.filter(u => { const p = unitAt(u, ev.t); return p && u.type !== 'artillery' && ['firing', 'charge', 'skirmish'].includes(p.state); }).length;
  const ev = b.events.reduce((best, e) => (e.at && busy(e) > busy(best) ? e : best), b.events.find(e => e.at) ?? b.events[0]);
  const at = ev.at ?? [0, 0], k = CW / Math.max(1200, (ev.view ?? b.extent / 2) * 1.4);
  const X = x => CW * 0.66 + (x - at[0]) * k, // the fight sits right of the card on a wide screen
    Y = y => CH / 2 - (y - at[1]) * k, J = () => (rnd() - 0.5) * 1.2; // hand-drawn wobble
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
    contours(Z, T.cols, T.rows, lv, (x0, y0, x1, y1) => { g.moveTo(X((x0 + 0.5) * sp - half) + J(), Y(half - (y0 + 0.5) * sp) + J()); g.lineTo(X((x1 + 0.5) * sp - half) + J(), Y(half - (y1 + 0.5) * sp) + J()); });
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
    g.globalAlpha = 0.6; g.fillStyle = B_SIDE(b, u.side); g.fillRect(-w / 2, 0, w, h); g.globalAlpha = 1;
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
  // Compass rose and the cartouche.
  const cx = CW - 120, cy = 130;
  g.strokeStyle = ink(0.7); g.fillStyle = ink(0.7); g.lineWidth = 1;
  for (let i = 0; i < 8; i++) {
    const a = (i * Math.PI) / 4, L = i % 2 ? 34 : 64;
    g.beginPath(); g.moveTo(cx, cy); g.lineTo(cx + Math.sin(a - 0.12) * 12, cy - Math.cos(a - 0.12) * 12); g.lineTo(cx + Math.sin(a) * L, cy - Math.cos(a) * L); g.closePath(); i % 2 ? g.stroke() : g.fill();
  }
  g.beginPath(); g.arc(cx, cy, 44, 0, 6.283); g.stroke();
  g.font = '22px "IM Fell English", Georgia, serif'; g.fillText('N', cx, cy - 72);
  g.font = 'italic 24px "IM Fell English", Georgia, serif'; g.textAlign = 'left';
  g.textAlign = 'right'; g.fillText(`Plan of ${/^(Battle|Siege)/.test(b.name) ? 'the ' : ''}${b.name}`, CW - 60, CH - 82); g.font = 'italic 19px "IM Fell English", Georgia, serif'; g.fillText(`${b.dateText ?? b.date}: ${ev.title}`, CW - 60, CH - 54);
  g.strokeStyle = 'rgba(80,50,20,0.12)'; g.lineWidth = 2; g.beginPath(); g.moveTo(CW / 2, 0); g.lineTo(CW / 2, CH); g.moveTo(0, CH / 2); g.lineTo(CW, CH / 2); g.stroke(); // folds
}
const B_SIDE = (b, side) => (side === 'british' ? '#b0382c' : side === 'french' ? '#d8cfb0' : '#3d5a99'); // period washes: red, buff, blue

function showSplash(list) {
  const fmt = s => (s < 90 ? `${s} s` : `${Math.round(s / 60)} min`);
  const wars = new Map();
  for (const b of list) { if (!wars.has(b.war)) wars.set(b.war, []); wars.get(b.war).push(b); }
  ui.splashList.innerHTML = [...wars].map(([war, bs]) => `<h2>${war}</h2>` + bs.map(b =>
    `<button data-id="${b.id}"><span>${b.name}</span><i></i><span class="rt">${b.runtime ? fmt(b.runtime) : ''}</span></button>`).join('')).join('');
  ui.splash.hidden = false;
  const pick = list.find(b => b.id === new URLSearchParams(location.search).get('plan')) ?? list[Math.floor(Math.random() * list.length)]; // ?plan=id for screenshots
  drawPlan(ui.plan, pick).catch(() => {}); // the backdrop is decoration; the list works without it
  ui.splashList.onclick = async e => {
    const id = e.target.closest('button')?.dataset.id;
    if (!id) return;
    ui.splash.hidden = true; ui.battle.value = id; location.hash = id;
    await loadBattle(id); setPlaying(true);
  };
}

const want = location.hash.slice(1).split(/[@,]/)[0];
if (list.some(b => b.id === want)) { ui.battle.value = want; await loadBattle(want); }
else showSplash(list);
ui.home.onclick = () => { setPlaying(false); showSplash(list); };
requestAnimationFrame(frame);
