import { SPEEDS, STATE_TEXT, normalizeBattle, unitAt, shape, dots, eventAt, actionBox, advance, defaultSpeed, fmtTime, parseTime, hash, mulberry32, mod } from './sim.js';
import { themeFor } from './themes.js';
import { contours, isStatic, canvas as newCanvas } from './themes/paint.js';

const $ = s => document.querySelector(s);
const canvas = $('#map'), ctx = canvas.getContext('2d');
const ui = { play: $('#play'), speed: $('#speed'), scrub: $('#scrub'), clock: $('#clock'), follow: $('#follow'), bar: $('#bar'),
  top: $('#top'), topFold: $('#top-fold'), title: $('#title'), sub: $('#sub'), legend: $('#legend'), caption: $('#caption'), capTitle: $('#cap-title'), capText: $('#cap-text'), capWhen: $('#cap-when'), capFold: $('#cap-fold'),
  hover: $('#hover'), sources: $('#sources'), srcBtn: $('#src-btn'), srcList: $('#src-list'), lapse: $('#lapse'),
  marks: $('#marks'), splash: $('#splash'), splashList: $('#splash-list'), plan: $('#plan'), home: $('#home'), legendBtn: $('#legend-btn'), legendDlg: $('#legend-dlg'), legendList: $('#legend-list'),
  outcome: $('#outcome'), outResult: $('#out-result'), outBody: $('#out-body'),
  card: $('#card'), cardSwatch: $('#card-swatch'), cardName: $('#card-name'), cardCmd: $('#card-cmd'), cardKind: $('#card-kind'), cardLive: $('#card-live'), cardClose: $('#card-close'),
  fx: $('#fx'), fonts: $('#theme-fonts'), kicker: $('#kicker'), hours: $('#hours'), loading: $('#loading') };

let B = null, skin = null, sheet = null, buildMs = 0; // the battle, its skin (themes.js), what the skin built for it and how long that took
let t = 0, playing = false, speed = 10, curEvent = null, shownEvent = null;
let cam = { x: 0, y: 0, zoom: 0.5 }, follow = true, lapse = true, lapsing = false;
let W = 0, H = 0, DPR = 1, last = performance.now();
const smoke = [], pops = [], placed = []; // placed: label boxes drawn this frame, so labels avoid each other
let popN = 0; // live muzzle flashes are pops[0..popN); the objects past it are kept for reuse
let mouse = null, selected = null, cardAt = null, cardLive = '', cardSwap = 0; // cardAt: the card's eased screen position

// ---------- loading ----------

async function loadBattle(id) {
  const [raw, terrain] = await Promise.all([
    fetch(`battles/${id}/battle.json`).then(r => r.json()),
    fetch(`battles/${id}/terrain.json`).then(r => r.json()),
  ]);
  const b = normalizeBattle(raw), theme = themeFor(b);
  ui.loading.hidden = false; // the layer takes a moment on a slow machine: parchment rather than a stale map
  await wearSkin(theme);
  await new Promise(r => { requestAnimationFrame(() => setTimeout(r)); setTimeout(r, 100); }); // let it paint; a hidden tab has no frames
  const t0 = performance.now();
  sheet = theme.build(b, terrain, DPR); skin = theme;
  buildMs = performance.now() - t0;
  theme.ambient(ui.fx, sheet); ui.fx.style.setProperty('--dark', 0); fxDark = 0;
  ui.loading.hidden = true;
  B = b;
  smoke.length = 0; curEvent = shownEvent = null; select(null);
  speed = SPEEDS.includes(b.speed) ? b.speed : 10;
  const dur = b.endT - b.startT;
  ui.speed.innerHTML = '';
  for (const s of SPEEDS) if (s <= 120 || dur / s >= 120) ui.speed.add(new Option(`${s}×`, s)); // the big speeds only when the battle lasts
  ui.speed.value = speed;
  ui.scrub.min = b.startT; ui.scrub.max = b.endT;
  sizeClock();
  buildMarks(b); buildLegend(b);
  ui.title.textContent = b.name; ui.kicker.textContent = skin.kicker;
  ui.sub.textContent = `${b.place} · ${b.dateText ?? b.date}`;
  ui.legend.innerHTML = Object.values(b.sides).map(s => `<span><i style="background:${s.color}"></i>${s.name}</span>`).join('');
  const o = b.outcome; // result in the summary; losses side by side once opened
  ui.outcome.hidden = !o; ui.outcome.open = false;
  if (o) {
    ui.outResult.textContent = o.result;
    ui.outBody.innerHTML = o.losses.map(([s, text]) => {
      const ids = [].concat(s);
      return `<p><b>${ids.map(i => `<i style="background:${b.sides[i].color}"></i>`).join('')} ${ids.map(i => b.sides[i].name).join(' and ')}.</b> ${text}</p>`;
    }).join('') + (o.note ? `<p class="note">${o.note}</p>` : '');
  }
  ui.srcList.innerHTML = (b.sources ?? []).map(s => `<li>${s}</li>`).join('');
  const v = b.view ?? { x: 0, y: 0, width: b.extent };
  cam = { x: v.x, y: v.y, zoom: Math.min(W, H) / v.width };
  follow = true; ui.follow.checked = true; lapse = true; ui.lapse.checked = true;
  clampCam();
  const [, , at, play, pickId, warp, legend, outcome, bench] = location.hash.match(/^#([^@,]*)(?:@([^,]+))?(,play)?(?:,select=([^,]+))?(,warp)?(,legend)?(,outcome)?(,bench)?$/) ?? [];
  seek(at ? parseTime(at) : b.startT);
  setPlaying(!!play); foldTop(!!play);
  if (legend) ui.legendDlg.showModal(); // screenshots
  if (outcome) ui.outcome.open = true;
  if (pickId) select(b.units.find(u => u.id === pickId) ?? null); // screenshots: the card open on this unit
  document.body.classList.toggle('nofade', !!warp); // screenshots: skip the caption and card fades
  if (warp) { // five seconds of frames for screenshots, framed around the caption, with the card beside its unit
    await document.fonts.ready; rects = null; // the Fell faces resize the panels
    step(0); updateHud();
    for (let i = 0; i < 300; i++) step(1 / 60);
    draw(); updateHud();
  }
  if (bench) (await import('./tools/bench.js')).bench(skin.id, ctx, draw, buildMs); // per-frame draw cost; tools/bench.sh
  location.hash = id;
}

// Dress the page for a skin: its class on <body> for the chrome, its fonts, loaded before the layer draws with them.
async function wearSkin(theme) {
  document.body.className = document.body.className.replace(/\btheme-\S+/g, '').trim();
  document.body.classList.add(`theme-${theme.id}`);
  if (ui.fonts.getAttribute('href') !== theme.fonts) {
    const loaded = new Promise(r => { ui.fonts.onload = ui.fonts.onerror = r; });
    ui.fonts.href = theme.fonts;
    await loaded;
  }
  await Promise.all(theme.faces.map(f => document.fonts.load(f).catch(() => {})));
}

// ---------- camera ----------

const w2sx = x => (x - cam.x) * cam.zoom + W / 2;
const w2sy = y => (cam.y - y) * cam.zoom + H / 2;

// Screen rects {l,t,r,b} the panels leave clear: each panel is cut away by trimming one side, every combination of trims
// giving one candidate. The chapter labels slanting up from the bar count as one more panel. Measured only when a panel,
// the labels or the window change. `clear` is the candidate in use; the camera moves it to whichever shows the action
// biggest, and a re-measure keeps the nearest new one, so a panel growing a few pixels never swings the view across.
let rects = null, clear = null;
const area = r => (r.r - r.l) * (r.b - r.t), gap = (r, c) => Math.abs(r.l - c.l) + Math.abs(r.t - c.t) + Math.abs(r.r - c.r) + Math.abs(r.b - c.b);
function safeRect() {
  if (!rects) {
    rects = measureSafe();
    clear = rects.reduce((a, r) => (clear ? gap(r, clear) < gap(a, clear) : area(r) > area(a)) ? r : a);
  }
  return clear;
}
function measureSafe() {
  const m = 10, panels = [ui.top, ui.bar, ...(ui.caption.classList.contains('show') ? [ui.caption] : [])].map(el => el.getBoundingClientRect());
  const labels = marks.filter(el => !el.hidden).map(el => el.getBoundingClientRect()).filter(r => r.width);
  V.avoid = [...panels, ...labels].map(p => ({ l: p.left, t: p.top, r: p.right, b: p.bottom })); // for the skin's map furniture
  if (labels.length) panels.push({ left: Math.min(...labels.map(r => r.left)), right: Math.max(...labels.map(r => r.right)), top: Math.min(...labels.map(r => r.top)), bottom: panels[1].top });
  const out = [], bar = panels[1].top;
  const trim = (i, s) => {
    if (s.r - s.l < 80 || s.b - s.t < 80) return;
    if (i === panels.length) return out.push(s);
    const p = panels[i];
    if (p.right <= s.l || p.left >= s.r || p.bottom <= s.t || p.top >= s.b) return trim(i + 1, s);
    trim(i + 1, { ...s, t: p.bottom + m }); trim(i + 1, { ...s, b: p.top - m });
    trim(i + 1, { ...s, l: p.right + m }); trim(i + 1, { ...s, r: p.left - m });
  };
  trim(0, { l: 0, t: 0, r: W, b: H, bar });
  return out.length ? out : [{ l: 0, t: 0, r: W, b: H, bar }];
}
const panelSizes = new ResizeObserver(() => { rects = null; });
for (const el of [ui.top, ui.caption, ui.bar]) panelSizes.observe(el);

const minZoom = () => { const s = safeRect(); return Math.min(s.r - s.l, s.b - s.t) / B.extent; }; // out to the whole map in the clear rect

// The map edge may come in as far as the clear rect's edge, so anything under a panel can be dragged out from under it.
// Zoomed out past that, the map sits centred in the clear rect.
function clampCam() {
  cam.zoom = Math.min(12, Math.max(minZoom(), cam.zoom));
  const h = B.extent / 2, z = cam.zoom, s = safeRect();
  const fit = (v, lo, hi) => (lo > hi ? (lo + hi) / 2 : Math.max(lo, Math.min(hi, v)));
  cam.x = fit(cam.x, -h + (W / 2 - s.l) / z, h - (s.r - W / 2) / z);
  cam.y = fit(cam.y, -h + (s.b - H / 2) / z, h - (H / 2 - s.t) / z);
}
function zoomAt(sx, sy, f) {
  const nz = Math.min(12, Math.max(minZoom(), cam.zoom * f));
  const wx = cam.x + (sx - W / 2) / cam.zoom, wy = cam.y - (sy - H / 2) / cam.zoom;
  cam.zoom = nz; cam.x = wx - (sx - W / 2) / nz; cam.y = wy + (sy - H / 2) / nz;
  clampCam();
}
function userMoved() { if (follow) { follow = false; ui.follow.checked = false; } }

// Ease toward the action box fitted into the clear rect. It looks four real seconds ahead at the current clock rate.
function updateCamera(dt) {
  if (!follow) return;
  const bx = actionBox(B, t, (lapsing ? B.lapse : speed) * 4);
  if (!bx) return;
  const fitZ = r => Math.min((r.r - r.l) / (bx.x1 - bx.x0), (r.b - r.t) / (bx.y1 - bx.y0));
  safeRect();
  const best = rects.reduce((a, r) => (fitZ(r) > fitZ(a) ? r : a));
  if (fitZ(best) > 1.1 * fitZ(clear)) clear = best;
  // Never wider than the map filling the window: a box too big for that crops its outskirts rather than showing bare edges.
  const s = clear, k = 1 - Math.exp(-dt * 1.2), tz = Math.min(12, Math.max(Math.max(W, H) / B.extent, fitZ(s))), h = B.extent / 2;
  // Box centred in the clear rect, then slid, while it still fits there, to where the map fills the whole window.
  // A box too big for the clear rect gives way to the map filling the window; one that fits keeps to the clear rect, edge or not.
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  const aim = (c, lo, hi, vlo, vhi) => { const a = Math.max(lo, vlo), b = Math.min(hi, vhi); return a <= b ? clamp(c, a, b) : lo <= hi ? clamp((vlo + vhi) / 2, lo, hi) : clamp(c, vlo, vhi); };
  const tx = aim((bx.x0 + bx.x1) / 2 - ((s.l + s.r) / 2 - W / 2) / tz, bx.x1 - (s.r - W / 2) / tz, bx.x0 + (W / 2 - s.l) / tz, -h + W / 2 / tz, h - W / 2 / tz);
  const ty = aim((bx.y0 + bx.y1) / 2 + ((s.t + s.b) / 2 - H / 2) / tz, bx.y1 - (H / 2 - s.t) / tz, bx.y0 + (s.b - H / 2) / tz, -h + H / 2 / tz, h - H / 2 / tz);
  cam.x += (tx - cam.x) * k;
  cam.y += (ty - cam.y) * k;
  cam.zoom *= Math.exp(Math.log(tz / cam.zoom) * k);
  clampCam();
}

// The unit whose drawn body is under a screen point, within a few pixels; the smallest wins where bodies overlap.
function pick(mx, my) {
  let best = null, bd = 8, ba = Infinity;
  for (const u of B.units) {
    const s = u.screen;
    if (!u.pose || !s) continue;
    const X = mx - s.x, Y = my - s.y, c = Math.cos(s.a), n = Math.sin(s.a);
    const lx = X * c + Y * n, ly = -X * n + Y * c; // into the body's frame: front edge at y = -2, ranks behind it
    const d = Math.hypot(Math.max(0, Math.abs(lx) - s.w / 2), Math.max(0, -2 - ly, ly - s.h - 1)), area = s.w * s.h;
    if (d < bd || (d === bd && area < ba)) { best = u; bd = d; ba = area; }
  }
  return best ?? B.units.find(u => u.pose && u.tag && mx >= u.tag[0] && mx <= u.tag[2] && my >= u.tag[1] && my <= u.tag[3]) ?? null; // or its name
}

// A press that moves less than 6 px is a click on a unit, not a drag, so it neither pans nor turns Follow off.
const ptrs = new Map();
let pinch = 0;
canvas.addEventListener('pointerdown', e => {
  for (const q of ptrs.values()) q.drag = true;
  ptrs.set(e.pointerId, { x: e.clientX, y: e.clientY, x0: e.clientX, y0: e.clientY, drag: ptrs.size > 0 });
  canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener('pointermove', e => {
  mouse = [e.clientX, e.clientY];
  const q = ptrs.get(e.pointerId);
  if (!q || (!q.drag && Math.hypot(e.clientX - q.x0, e.clientY - q.y0) < 6)) return;
  const px = q.x, py = q.y;
  Object.assign(q, { x: e.clientX, y: e.clientY, drag: true });
  if (ptrs.size === 1) {
    cam.x -= (e.clientX - px) / cam.zoom; cam.y += (e.clientY - py) / cam.zoom;
    clampCam(); userMoved();
  } else if (ptrs.size === 2) {
    const [a, b] = [...ptrs.values()], d = Math.hypot(a.x - b.x, a.y - b.y);
    if (pinch) zoomAt((a.x + b.x) / 2, (a.y + b.y) / 2, d / pinch);
    pinch = d; userMoved();
  }
});
const up = e => {
  const q = ptrs.get(e.pointerId);
  ptrs.delete(e.pointerId); pinch = 0;
  if (e.type === 'pointerup' && q && !q.drag) { const u = pick(e.clientX, e.clientY); if (u) select(u); }
};
canvas.addEventListener('pointerup', up);
canvas.addEventListener('pointercancel', up);
canvas.addEventListener('pointerleave', () => { mouse = null; });
canvas.addEventListener('wheel', e => { e.preventDefault(); zoomAt(e.clientX, e.clientY, Math.exp(-e.deltaY * 0.0012)); userMoved(); }, { passive: false });

// ---------- drawing ----------

// Advance the clock, camera, unit poses and smoke by dt real seconds. Drawing reads the results.
function step(dt) {
  if (playing) {
    [t, lapsing] = advance(B, t, dt, speed, lapse);
    if (t >= B.endT) setPlaying(false);
    let w = 0; // flashes age in real time; spent ones swap to the back of the pool
    for (let i = 0; i < popN; i++) { const q = pops[i]; q.age += dt; if (q.age < q.life) { pops[i] = pops[w]; pops[w++] = q; } }
    popN = w;
  }
  const ev = eventAt(B, t);
  if (ev !== curEvent) { // a chapter may set its own pace while the story is being followed
    curEvent = ev;
    if (follow) { speed = ev?.speed ?? defaultSpeed(B); ui.speed.value = speed; }
  }
  updateCamera(dt);
  for (const u of B.units) {
    const p = (u.pose = unitAt(u, t));
    if (playing && p && p.fire > 0 && p.state !== 'surrender') { const { F, nd } = shape(u, p, B.menPerDot); emit(u, p, F, nd, dt); }
  }
  if (playing) for (const f of B.features ?? []) { // burning town or ship: a standing pall of smoke while the feature is active
    if (f.type !== 'smoke' || (f.from != null && t < f.from) || (f.until != null && t >= f.until)) continue;
    const wind = B.wind ?? { x: 0.8, y: 0.3 }, sp = f.spread ?? 60;
    let n = Math.floor(f.rate * dt + Math.random());
    while (n-- > 0 && smoke.length < 2500) smoke.push({ x: f.at[0] + (Math.random() - 0.5) * sp, y: f.at[1] + (Math.random() - 0.5) * sp,
      vx: wind.x * 2 + Math.random() - 0.5, vy: wind.y * 2 + Math.random() - 0.5, age: 0, life: 8 + Math.random() * 4, r0: 8, r1: 50, k: Math.random() });
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

// The frame, back to front: the layer and what lies beyond it, the skin's underlay, the features that come and go, the
// fallen, the units, smoke, names, the skin's furniture, night and weather, then muzzle flashes, which glow through it all.
const V = { B: null, sheet: null, t: 0, W: 0, H: 0, z: 1, sx: w2sx, sy: w2sy, safe: null, avoid: [], dark: 0 };
function draw() {
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  const half = B.extent / 2, r = { l: w2sx(-half), t: w2sy(half), r: w2sx(half), b: w2sy(-half) };
  Object.assign(V, { B, sheet, t, W, H, z: cam.zoom, safe: safeRect() });
  ctx.imageSmoothingEnabled = true;
  ctx.drawImage(sheet.layer, r.l, r.t, r.r - r.l, r.b - r.t);
  skin.surround(ctx, r, V);
  skin.under?.(ctx, V);
  drawFeatures(); drawFallen();
  const labels = drawUnits();
  drawSmoke(); drawLabels(labels);
  skin.over?.(ctx, V);
  drawNight(); drawPops();
}

// Features that come and go (siegeworks dug, ships burnt) and every place name; the rest are baked into the layer.
function drawFeatures() {
  const k = Math.max(0.7, (cam.zoom * B.extent) / sheet.layer.width);
  placed.length = 0;
  for (const f of B.features ?? []) {
    if ((f.from != null && t < f.from) || (f.until != null && t >= f.until)) continue;
    const pts = f.pts ?? f.poly;
    if (pts && !isStatic(f)) skin.feature(ctx, f.type, pts.map(([x, y]) => [w2sx(x), w2sy(y)]), k, !!f.poly);
    if (f.name && f.at) {
      const x = w2sx(f.at[0]), y = w2sy(f.at[1]);
      if (x < -300 || x > W + 300 || y < -60 || y > H + 60) continue;
      const w = skin.placeName(ctx, f, x, y) + 6;
      if (!f.rot) placed.push([x - w / 2, y - 9, x + w / 2, y + 9]);
    }
  }
}

function drawFallen() {
  const d = Math.max(2.5, Math.min(6, 1.6 * cam.zoom)), { color, mark } = skin.fallen;
  ctx.lineWidth = 1; ctx.globalAlpha = 0.65;
  for (const [side, s] of Object.entries(B.sides)) {
    ctx.beginPath();
    for (const f of B.fallen) {
      if (f.t > t) break;
      if (f.side === side) mark(ctx, w2sx(f.x), w2sy(f.y), d);
    }
    ctx.strokeStyle = color(s); ctx.stroke();
  }
  ctx.globalAlpha = 1;
}

// Each unit as the skin draws it, from the geometry worked out here: U is the body on screen, front edge at y = -2 in its
// own frame and ranks running back to y = h + 1. Returns the labels each unit offers, for drawLabels to thin.
const dotBuf = [];
function drawUnits() {
  const z = cam.zoom, mpd = B.menPerDot, labels = [];
  for (const u of B.units) {
    const p = u.pose;
    u.tag = null;
    if (!p) continue;
    const sx = w2sx(p.x), sy = w2sy(p.y);
    const { ranks, F, rankD } = shape(u, p, mpd), D = ranks * rankD, ext = Math.max(F, D) * z + 40;
    const wPx = Math.max(16, F * z), hPx = Math.max(7, D * z); // never shrinks below a few pixels
    u.screen = { x: sx, y: sy, w: wPx, h: hPx, a: (p.h * Math.PI) / 180 }; // the body as drawn, for pointing and the card
    if (sx < -ext || sy < -ext || sx > W + ext || sy > H + ext) continue;
    if (u === selected) ring(u.screen);
    dotBuf.length = 0;
    if (F * z >= 24) { const pts = dots(u, p, mpd, dotBuf); for (let i = 0; i < pts.length; i += 2) { pts[i] = w2sx(pts[i]); pts[i + 1] = w2sy(pts[i + 1]); } }
    const U = { u, p, side: B.sides[u.side], x: sx, y: sy, a: u.screen.a, w: wPx, h: hPx, z, dots: dotBuf.length ? dotBuf : null,
      gone: p.state === 'surrender', rout: p.state === 'rout', go: p.moving || p.state === 'column', mil: u.type === 'militia' || u.type === 'riflemen',
      cav: u.type === 'cavalry', art: u.type === 'artillery', guns: u.guns ?? 1 };
    skin.unit(ctx, U);
    // Every unit offers a label just above its topmost corner (a marching column is narrow but long).
    const s = Math.sin(U.a), c = Math.cos(U.a), top = -Math.abs((wPx / 2) * s) + Math.min(-2 * c, (hPx + 1) * c);
    const l = { u, U, text: u.short ?? u.name, x: sx, y: sy + top - 11, size: Math.min(17, 12 + z * 3), men: p.strength };
    labels.push(l);
  }
  return labels;
}

// A pulsing ring so the unit on the card is easy to find.
function ring(s) {
  ctx.save(); ctx.translate(s.x, s.y); ctx.rotate(s.a);
  ctx.globalAlpha = 0.75 + 0.25 * Math.sin(performance.now() / 300);
  ctx.lineWidth = 6; ctx.strokeStyle = skin.ring[0]; ctx.strokeRect(-s.w / 2 - 7, -9, s.w + 14, s.h + 17);
  ctx.lineWidth = 2.5; ctx.strokeStyle = skin.ring[1]; ctx.strokeRect(-s.w / 2 - 7, -9, s.w + 14, s.h + 17);
  ctx.restore();
}

// Bigger units get their label first; a label that would overlap one already placed is dropped this frame.
function drawLabels(labels) {
  for (const l of labels.sort((a, b) => b.men - a.men)) {
    const [w, h] = skin.label.measure(ctx, l), r = [l.x - w / 2, l.y - h / 2, l.x + w / 2, l.y + h / 2];
    if (placed.some(q => r[0] < q[2] && r[2] > q[0] && r[1] < q[3] && r[3] > q[1])) continue;
    placed.push(r); l.u.tag = r;
    skin.label.draw(ctx, l);
  }
}

function emit(u, p, F, nd, dt) {
  const art = u.type === 'artillery', wind = B.wind ?? { x: 0.8, y: 0.3 }, life = sheet.smoke.life;
  const rate = p.fire * (art ? (u.guns ?? 1) * 0.5 : nd * 0.35);
  let n = Math.floor(rate * dt + Math.random());
  const rad = (p.h * Math.PI) / 180, dx = Math.sin(rad), dy = Math.cos(rad);
  while (n-- > 0) {
    const uu = (Math.random() - 0.5) * F, x = p.x + uu * dy + 2 * dx, y = p.y - uu * dx + 2 * dy;
    if (smoke.length < 2500) smoke.push({ x, y, vx: wind.x + dx * 1.2 + Math.random() - 0.5, vy: wind.y + dy * 1.2 + Math.random() - 0.5,
      age: 0, life: (art ? 4.5 : 2.4 + Math.random() * 1.6) * life, r0: art ? 4 : 2, r1: art ? 22 : 11, k: Math.random() });
    if (popN < 400) { // a musket pops for a tenth of a second or so; a gun's flash is bigger and lasts longer
      const q = (pops[popN++] ??= {});
      q.x = x; q.y = y; q.age = 0;
      q.life = art ? 0.18 + Math.random() * 0.1 : 0.08 + Math.random() * 0.12;
      q.r = art ? 11 + Math.random() * 7 : 3.5 + Math.random() * 3; // glow radius in pixels; the white core is a fifth of it
    }
  }
}

function drawPops() {
  if (!playing || !popN) return;
  const s = Math.min(2, Math.max(0.8, Math.sqrt(cam.zoom))); // a little bigger close up, never lost far out
  ctx.globalCompositeOperation = V.dark > 0.25 ? 'lighter' : 'source-over'; // added light washes out on paper by day
  for (let i = 0; i < popN; i++) {
    const q = pops[i], f = q.age / q.life, r = q.r * s * (1 - 0.4 * f);
    ctx.globalAlpha = 1 - f * f;
    ctx.drawImage(sheet.flash, w2sx(q.x) - r, w2sy(q.y) - r, 2 * r, 2 * r);
  }
  ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
}

function drawSmoke() {
  const z = cam.zoom, { sprites, alpha, grow } = sheet.smoke, n = sprites.length;
  for (const s of smoke) {
    const f = s.age / s.life, r = (s.r0 + (s.r1 - s.r0) * Math.sqrt(f)) * z * grow;
    if (r < 0.8) continue;
    ctx.globalAlpha = alpha * (1 - f);
    ctx.drawImage(sprites[(s.k * n) | 0], w2sx(s.x) - r, w2sy(s.y) - r, 2 * r, 2 * r);
  }
  ctx.globalAlpha = 1;
}

// Night from about 45 minutes before sunrise, and after sunset when the battle gives one: the skin's dark multiplied
// over the map. The ambient layers hear of it through --dark (clouds thin, a candle or lamp takes over).
let fxDark = 0;
function drawNight() {
  let dark = 0;
  if (B.sunriseT != null) {
    const tod = mod(t, 86400), ramp = x => Math.min(1, Math.max(0, x));
    dark = ramp((B.sunriseT - tod) / 2800);
    if (B.sunsetT != null) dark = Math.max(dark, ramp((tod - B.sunsetT) / 2800));
  }
  V.dark = dark;
  if (Math.abs(dark - fxDark) > 0.02 || (dark === 0) !== (fxDark === 0)) { fxDark = dark; ui.fx.style.setProperty('--dark', dark.toFixed(2)); }
  if (dark > 0) {
    ctx.globalCompositeOperation = 'multiply';
    ctx.fillStyle = `rgb(${skin.night.map(v => Math.round(255 - (255 - v) * dark)).join(',')})`; ctx.fillRect(0, 0, W, H);
    ctx.globalCompositeOperation = 'source-over';
  }
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
    el.textContent = ev.title; el.title = `${ev.title} · ${chapterWhen(ev)}`;
    el.onclick = () => { follow = true; ui.follow.checked = true; seek(ev.t); };
    ui.marks.append(el);
    leads.push(svg.appendChild(document.createElementNS('http://www.w3.org/2000/svg', 'path')));
    return el;
  });
  layoutMarks();
}
function layoutMarks() {
  const tw = ui.marks.clientWidth, dur = B.endT - B.startT, gap = 29; // a 22 px pill at 50° clears its neighbour at 29 px (29·sin 50° > 22)
  rects = null;
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
  layoutHours(ui.scrub.clientWidth - 26, dur); // the thumb's travel; the marks are hidden on a phone
}

// The scale of hours under the scrubber, for a skin that rules one: alternate inked and blank segments of a round number
// of hours (or days) at least 40 px wide, named every 70 px or so. --seg and --seg0 size and place the segments.
function layoutHours(tw, dur) {
  ui.hours.replaceChildren();
  if (!skin.hours) return;
  const unit = [900, 1800, 3600, 7200, 10800, 21600, 43200, 86400, 172800, 604800].find(u => (tw * u) / dur >= 40) ?? 604800;
  const seg = (tw * unit) / dur, first = Math.ceil(B.startT / unit) * unit;
  let named = unit * Math.ceil(70 / seg); // a name every 70 px or so, on the hour
  if (named < 3600) named = 3600; else if (named < 86400) named = Math.ceil(named / 3600) * 3600;
  ui.scrub.style.setProperty('--seg', `${seg.toFixed(2)}px`);
  ui.scrub.style.setProperty('--seg0', `${(13 + ((first - B.startT) / dur) * tw).toFixed(2)}px`);
  for (let tb = first; tb <= B.endT; tb += unit) {
    if (mod(tb, named)) continue;
    const el = document.createElement('span');
    el.textContent = skin.hours(tb); el.style.left = `${((tb - B.startT) / dur) * tw}px`;
    ui.hours.append(el);
  }
}

// Each legend row's words. A skin rewords the rows its drawing changes (legend.text).
const LEGEND_TEXT = {
  infantry: b => `Infantry. Each pale dot is ${b.menPerDot} men; the rows are ranks.`,
  facing: () => 'The point on the front rank shows which way a unit faces.',
  militia: () => 'Militia and riflemen, in the lighter shade.',
  column: () => 'A column on the march: narrow and long.',
  cavalry: () => 'Cavalry: taller dots, a mounted man each.',
  artillery: () => 'Artillery, with its guns.',
  skirmish: () => 'Skirmishers and open order: one thin, spread-out rank.',
  rout: () => 'Broken and running: faded.',
  surrender: () => 'Surrendered: grey.',
  fallen: b => `Where men fell: a mark for every ${b.menPerDot} men a unit lost, in that side’s colour.`,
  fire: () => 'Muzzle flashes, and powder smoke drifting downwind from units firing.',
  redoubt: () => 'Redoubt or battery: an earthwork fort.',
  works: () => 'Fortified line of earthworks.',
  trench: () => 'Siege trench: the parallels and the approaches between them.',
  camp: () => 'Camp.', ship: () => 'Ship.', road: () => 'Road.', creek: () => 'Creek or stream.', fence: () => 'Fence.',
  water: () => 'Water.', field: () => 'Open field or cleared ground.', woods: () => 'Woods.',
  contours: (b, sheet) => `Contour lines every ${sheet.iv} m (${Math.round(sheet.iv * 3.28)} ft) of height.`,
};
const FEATURE_SWATCH = { // where each feature sits in its 64 × 28 swatch
  road: [[4, 16], [30, 13], [60, 15]], creek: [[4, 18], [24, 12], [44, 16], [60, 11]], fence: [[4, 14], [60, 14]], works: [[4, 18], [24, 10], [60, 14]], trench: [[4, 10], [30, 18], [60, 14]],
  redoubt: [[14, 23], [14, 9], [26, 5], [38, 5], [50, 9], [50, 23]], camp: [[6, 6], [58, 6], [58, 22], [6, 22]], ship: [[6, 10], [54, 10], [60, 16], [50, 22], [10, 22]],
};

// A 64 × 28 swatch drawn by the skin on its own ground, at twice the pixels for sharp screens.
function swatch(draw) {
  const c = newCanvas(128, 56), g = c.getContext('2d');
  c.style.width = '64px'; c.style.height = '28px';
  g.scale(2, 2); g.fillStyle = skin.paper; g.fillRect(0, 0, 64, 28);
  draw(g);
  return c;
}
// A unit drawn by the skin exactly as the map draws one, front edge at y - 2, `files` × `ranks` men.
function unitSwatch(side, { w = 50, h = 9, y = 12, files = 9, ranks = 2, type = 'infantry', state = 'line', mil = false } = {}) {
  return swatch(g => {
    const d = [];
    for (let r = 0; r < ranks; r++) for (let f = 0; f < files; f++) d.push(32 - w / 2 + (w / files) * (f + 0.5), y - 2 + ((h + 3) / ranks) * (r + 0.5));
    skin.unit(g, { u: { id: 'legend', type, name: '' }, p: { state, h: 0, strength: 100 }, side, x: 32, y, a: 0, w, h, z: 1, dots: d,
      gone: state === 'surrender', rout: state === 'rout', go: state === 'column', mil, cav: type === 'cavalry', art: type === 'artillery', guns: 3 });
  });
}

// Only the symbols this battle uses, each drawn by the skin.
function buildLegend(b) {
  const sides = Object.values(b.sides), s0 = sides[0], L = skin.legend, say = (k, ...a) => (L.text?.[k] ?? LEGEND_TEXT[k])(b, sheet, ...a);
  const types = new Set(b.units.map(u => u.type)), states = new Set(b.units.flatMap(u => u.keys.map(k => k.state)));
  const feats = new Set((b.features ?? []).map(f => (f.type === 'battery' ? 'redoubt' : f.type)));
  const rows = [
    ...sides.map(s => [swatch(g => { g.fillStyle = s.color; g.beginPath(); g.roundRect(4, 4, 56, 20, 3); g.fill(); }), s.name]),
    [unitSwatch(s0), say('infantry')],
    [unitSwatch(s0, { w: 26, files: 5, y: 15 }), say('facing')],
    (types.has('militia') || types.has('riflemen')) && [unitSwatch(s0, { mil: true }), say('militia')],
    states.has('column') && [unitSwatch(s0, { w: 10, h: 14, y: 12, files: 2, ranks: 5, state: 'column' }), say('column')],
    types.has('cavalry') && [unitSwatch(s0, { h: 11, type: 'cavalry', files: 8 }), say('cavalry')],
    types.has('artillery') && [unitSwatch(s0, { w: 42, h: 5, y: 16, files: 6, ranks: 1, type: 'artillery' }), say('artillery')],
    (states.has('skirmish') || b.units.some(u => u.loose)) && [unitSwatch(s0, { h: 4, files: 7, ranks: 1 }), say('skirmish')],
    states.has('rout') && [unitSwatch(s0, { state: 'rout' }), say('rout')],
    states.has('surrender') && [unitSwatch(s0, { state: 'surrender' }), say('surrender')],
    [swatch(g => {
      const pts = [[8, 6], [20, 18], [31, 9], [44, 20], [55, 7], [15, 22], [38, 5], [50, 15], [26, 14]];
      g.lineWidth = 1; g.globalAlpha = 0.75;
      sides.forEach((s, i) => { g.beginPath(); pts.forEach(([x, y], j) => j % sides.length === i && skin.fallen.mark(g, x, y, 4)); g.strokeStyle = skin.fallen.color(s); g.stroke(); });
      g.globalAlpha = 1;
    }), say('fallen')],
    [swatch(g => {
      skin.unit(g, { u: { id: 'legend', type: 'infantry' }, p: { state: 'firing', h: 0, strength: 60 }, side: s0, x: 22, y: 20, a: 0, w: 24, h: 4, z: 1, dots: null, guns: 1 });
      sheet.smoke.sprites.forEach((sp, i) => { g.globalAlpha = sheet.smoke.alpha * (0.9 - i * 0.15); g.drawImage(sp, 22 + i * 9, 1 + (3 - i) * 2, 14 + i * 5, 14 + i * 5); });
      g.globalAlpha = 1; g.drawImage(sheet.flash, 14, 9, 14, 14);
    }), say('fire')],
    ...(L.extra?.(b, sheet) ?? []).map(([draw, text]) => [swatch(g => draw(g, s0, sheet)), text]),
    ...['redoubt', 'works', 'trench', 'camp', 'ship', 'road', 'creek', 'fence'].filter(k => feats.has(k)).map(k =>
      [swatch(g => skin.feature(g, k, FEATURE_SWATCH[k], 0.8, ['redoubt', 'camp', 'ship'].includes(k))), say(k)]),
    (b.water != null || feats.has('water')) && [swatch(g => L.swatch.water(g, sheet)), say('water')],
    b.fields?.length && [swatch(g => L.swatch.field(g, sheet)), say('field')],
    b.trees?.density && [swatch(g => L.swatch.woods(g, sheet)), say('woods')],
    [swatch(g => L.swatch.contours(g, sheet)), say('contours')],
  ];
  ui.legendList.replaceChildren(...rows.filter(Boolean).flatMap(([sw, text]) => {
    const a = document.createElement('div'), t = document.createElement('div');
    a.append(sw); t.textContent = text;
    return [a, t];
  }));
}

// ---------- hud and controls ----------

let clockShown = '';
function showClock(at) {
  const [main, small] = skin.clock(at), s = small ? `${main}<small>${small}</small>` : main;
  if (s !== clockShown) ui.clock.innerHTML = clockShown = s;
}
function updateHud(dt) {
  showClock(t); ui.clock.classList.toggle('lapsing', playing && lapsing);
  ui.scrub.value = t; ui.scrub.style.setProperty('--p', `${((t - B.startT) / (B.endT - B.startT)) * 100}%`);
  if (curEvent !== shownEvent) {
    shownEvent = curEvent;
    ui.capTitle.textContent = curEvent?.title ?? '';
    ui.capText.textContent = curEvent?.text ?? '';
    ui.capWhen.textContent = curEvent ? chapterWhen(curEvent) : '';
    ui.caption.classList.toggle('show', !!curEvent); rects = null;
    foldCaption(false); // every new chapter opens with its story showing
    marks.forEach((m, i) => { m.classList.toggle('on', B.events[i] === curEvent); leads[i].classList.toggle('on', B.events[i] === curEvent); });
  }
  const under = mouse && !ptrs.size ? pick(mouse[0], mouse[1]) : null, best = under !== selected && under;
  if (canvas.style.cursor !== (under ? 'pointer' : '')) canvas.style.cursor = under ? 'pointer' : '';
  ui.hover.hidden = !best;
  if (best) { // tooltip beside the cursor, flipped to the left near the right edge
    ui.hover.style.left = mouse[0] + 360 > W ? `${mouse[0] - 360}px` : `${mouse[0] + 20}px`;
    ui.hover.style.top = `${Math.min(mouse[1] + 20, H - 160)}px`;
  }
  if (best) ui.hover.innerHTML = `<b>${best.name}</b><br>${best.commander ? best.commander + '<br>' : ''}${B.sides[best.side].name} · ${best.type.replace('_', ' ')}<br>${liveText(best)}`;
  placeCard(dt);
}

// ---------- unit card ----------

const liveText = u => (u.pose ? `${Math.round(u.pose.strength)} men · ${STATE_TEXT[u.pose.state] ?? ''}` : '');
let cardSize = [0, 0], cardSide = 0;
function fillCard(u) {
  const side = B.sides[u.side];
  ui.cardSwatch.style.background = u.type === 'militia' || u.type === 'riflemen' ? side.light ?? side.color : side.color;
  ui.cardName.textContent = u.name;
  ui.cardCmd.textContent = u.commander ?? ''; ui.cardCmd.hidden = !u.commander;
  ui.cardKind.textContent = `${side.name} · ${u.type.replace('_', ' ')}`;
  ui.cardLive.textContent = cardLive = liveText(u);
  cardSize = [ui.card.offsetWidth, ui.card.offsetHeight];
}
// Click a unit to open its card, or hand the card on to another unit: the old details fade and slide out, the new ones in,
// while the card glides across to its new unit.
function select(u) {
  if (u === selected) return;
  const was = selected;
  selected = u; clearTimeout(cardSwap);
  ui.card.classList.toggle('show', !!u);
  if (!u) return;
  if (!was) { ui.card.classList.remove('swap'); fillCard(u); cardAt = null; return; }
  ui.card.classList.add('swap');
  cardSwap = setTimeout(() => { if (selected) fillCard(selected); ui.card.classList.remove('swap'); }, 110);
}
ui.cardClose.onclick = () => select(null);

// The card rides beside its unit on whichever side covers the unit least, inside the clear rect, easing after it.
// On a phone it docks above the bar instead.
function placeCard(dt) {
  const u = selected, s = u?.screen;
  if (!u) return;
  if (!u.pose) return select(null); // gone from the field
  if (!s) return;
  if (!ui.card.classList.contains('swap')) { const live = liveText(u); if (live !== cardLive) ui.cardLive.textContent = cardLive = live; }
  const [cw, ch] = cardSize, S = safeRect(), g = 14, c = Math.cos(s.a), n = Math.sin(s.a), mid = s.h / 2;
  let target;
  if (W <= 640) target = [(W - cw) / 2, S.bar - ch - 12];
  else {
    const cx = s.x - n * mid, cy = s.y + c * mid; // centre of the body, whose ranks run back from the front edge
    const ex = Math.abs((s.w / 2) * c) + Math.abs(mid * n) + 10, ey = Math.abs((s.w / 2) * n) + Math.abs(mid * c) + 10;
    const fit = (v, lo, hi) => Math.max(Math.min(lo, hi), Math.min(Math.max(lo, hi), v));
    const xl = [S.l, S.r - cw], yl = [S.t, S.b - ch];
    if (xl[1] < xl[0]) xl.splice(0, 2, 8, W - cw - 8);
    if (yl[1] < yl[0]) yl.splice(0, 2, 8, H - ch - 8);
    let best = Infinity, side = cardSide;
    [[cx + ex + g, cy - ch / 2], [cx - ex - g - cw, cy - ch / 2], [cx - cw / 2, cy - ey - g - ch], [cx - cw / 2, cy + ey + g]].forEach(([x, y], i) => {
      const px = fit(x, ...xl), py = fit(y, ...yl);
      const cover = Math.max(0, Math.min(px + cw, cx + ex) - Math.max(px, cx - ex)) * Math.max(0, Math.min(py + ch, cy + ey) - Math.max(py, cy - ey));
      const score = cover + Math.hypot(px - x, py - y) + i * 5 - (i === cardSide ? 60 : 0); // stick to the current side unless another is clearly better
      if (score < best) { best = score; target = [px, py]; side = i; }
    });
    cardSide = side;
  }
  const k = cardAt && dt ? 1 - Math.exp(-dt * 8) : 1;
  cardAt = cardAt ? [cardAt[0] + (target[0] - cardAt[0]) * k, cardAt[1] + (target[1] - cardAt[1]) * k] : target;
  ui.card.style.transform = `translate(${cardAt[0].toFixed(1)}px, ${cardAt[1].toFixed(1)}px)`;
}

// "About 3 PM", or "26 Dec, about noon": times between recorded moments are estimates, so the story gives the nearest hour.
// A chapter whose time the sources record carries it as `when` ("8:00 AM", "about 3:30 PM").
function chapterWhen(ev) {
  const h = Math.round(ev.t / 3600), hh = mod(h, 24), d = fmtTime(ev.when ? ev.t : h * 3600);
  const when = ev.when ?? `about ${hh === 0 ? 'midnight' : hh === 12 ? 'noon' : `${hh % 12} ${hh < 12 ? 'AM' : 'PM'}`}`;
  return d.includes(', ') ? `${d.split(', ')[0]}, ${when}` : when[0].toUpperCase() + when.slice(1);
}
function fold(panel, btn, what, v) {
  panel.classList.toggle('folded', v);
  btn.textContent = v ? 'Show' : 'Hide';
  btn.setAttribute('aria-expanded', String(!v));
  btn.title = btn.ariaLabel = `${v ? 'Show' : 'Hide'} ${what}`;
}
const foldCaption = v => fold(ui.caption, ui.capFold, 'the story', v);
const foldTop = v => fold(ui.top, ui.topFold, 'the battle details', v); // folded to the title row while playing, so it hides fewer men
ui.capFold.onclick = () => foldCaption(!ui.caption.classList.contains('folded'));
ui.topFold.onclick = () => foldTop(!ui.top.classList.contains('folded'));

const nudge = () => Math.max(30, (B.endT - B.startT) / 240); // arrow keys: 30 s, or 1/240 of a long battle
function setPlaying(v) { playing = v; ui.play.textContent = v ? '❚❚' : '▶'; ui.play.setAttribute('aria-label', v ? 'Pause' : 'Play'); }
function seek(v) { t = Math.max(B.startT, Math.min(B.endT, v)); smoke.length = 0; popN = 0; }

ui.play.onclick = () => { if (!playing && t >= B.endT) seek(B.startT); setPlaying(!playing); };
ui.speed.onchange = () => { speed = +ui.speed.value; };
ui.scrub.oninput = () => seek(+ui.scrub.value);
ui.follow.onchange = () => { follow = ui.follow.checked; };
ui.lapse.onchange = () => { lapse = ui.lapse.checked; };
ui.srcBtn.onclick = () => ui.sources.showModal();
ui.legendBtn.onclick = () => ui.legendDlg.showModal();
addEventListener('keydown', e => {
  if (e.key === 'Escape' && selected && !document.querySelector('dialog[open]')) return select(null);
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
  canvas.width = W * DPR; canvas.height = H * DPR; rects = null;
  canvas.style.width = W + 'px'; canvas.style.height = H + 'px';
}
// Old-style figures differ in width, so the clock is held at the width of the widest time it can show; otherwise every tick nudges the scrubber.
function sizeClock() {
  let w = 0; ui.clock.style.width = '';
  for (let d = B.startT; d < B.endT + 86400; d += 86400) for (const h of [0, 10, 12, 15, 20, 22]) { // each day of the battle, round the clock
    showClock(d - mod(d, 86400) + h * 3600 + 3480);
    w = Math.max(w, ui.clock.offsetWidth);
  }
  ui.clock.style.width = `${w + 4}px`;
}
addEventListener('resize', () => { resize(); if (B) { clampCam(); sizeClock(); } if (selected) fillCard(selected); });
new ResizeObserver(() => B && layoutMarks()).observe(ui.marks); // the track also narrows when the clock text widens
resize();

function frame(now) {
  const dt = Math.min(0.1, (now - last) / 1000);
  last = now;
  if (B) { step(dt); draw(); updateHud(dt); }
  requestAnimationFrame(frame);
}

for (const s of SPEEDS) ui.speed.add(new Option(`${s}×`, s));
const list = (await (await fetch('battles/index.json')).json()).sort((a, b) => a.date.localeCompare(b.date));
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
    ui.splash.hidden = true; location.hash = id;
    await loadBattle(id); setPlaying(true); foldTop(true);
  };
}

const want = location.hash.slice(1).split(/[@,]/)[0];
if (list.some(b => b.id === want)) await loadBattle(want);
else showSplash(list);
ui.home.onclick = () => { setPlaying(false); showSplash(list); };
requestAnimationFrame(frame);
