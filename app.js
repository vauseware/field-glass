import { SPEEDS, STATE_TEXT, MONTHS, normalizeBattle, unitAt, shape, dots, dropAt, eventAt, actionBox, advance, defaultSpeed, fmtTime, parseTime, mod, clockParts,
  captionPage, paginate, timeOfDay, nearest } from './sim.js';
import { themeFor } from './themes.js';
import { WARS, showSplash } from './splash.js';
import { isStatic, canvas as newCanvas } from './themes/paint.js';

const $ = s => document.querySelector(s);
const canvas = $('#map'), ctx = canvas.getContext('2d');
const ui = { play: $('#play'), speed: $('#speed'), scrub: $('#scrub'), clock: $('#clock'), follow: $('#follow'), bar: $('#bar'),
  top: $('#top'), title: $('#title'), sub: $('#sub'), legend: $('#legend'), caption: $('#caption'), capTitle: $('#cap-title'), capText: $('#cap-text'), capWhen: $('#cap-when'),
  hover: $('#hover'), sources: $('#sources'), srcBtn: $('#src-btn'), srcList: $('#src-list'), lapse: $('#lapse'),
  marks: $('#marks'), splash: $('#splash'), home: $('#home'), legendBtn: $('#legend-btn'), legendDlg: $('#legend-dlg'), legendList: $('#legend-list'),
  outcome: $('#outcome'), outResult: $('#out-result'), outBody: $('#out-body'),
  card: $('#card'), cardSwatch: $('#card-swatch'), cardName: $('#card-name'), cardCmd: $('#card-cmd'), cardKind: $('#card-kind'), cardLive: $('#card-live'), cardClose: $('#card-close'),
  fx: $('#fx'), fonts: $('#theme-fonts'), kicker: $('#kicker'), hours: $('#hours'), loading: $('#loading'),
  opening: $('#opening'), opName: $('#op-name'), opDate: $('#op-date'), chTitle: $('#chapter-title'),
  clockBox: $('#clock-box'), speedBox: $('#clock-box .speed'), chaptersBtn: $('#chapters-btn'), topClose: $('#top-close'), chCount: $('#ch-count'), chList: $('#chapter-list'),
  capPips: $('#cap-pips'), track: $('#track'), tickTip: $('#tick-tip'), settingsBtn: $('#settings-btn'), settings: $('#settings'), titles: $('#titles'), captions: $('#captions') };

let B = null, skin = null, sheet = null, buildMs = 0; // the battle, its skin (themes.js), what the skin built for it and how long that took
let t = 0, playing = false, speed = 10, curEvent = null, shownEvent = null;
let cam = { x: 0, y: 0, zoom: 0.5 }, lapsing = false;
let quiet = false; // the scrubber or an arrow key moved the clock since the last frame: a chapter it lands in gets no title
let W = 0, H = 0, DPR = 1, last = performance.now();
let airClock = 0; // real seconds of play, which fly the aircraft of an air strike
const smoke = [], pops = [], placed = []; // placed: label boxes drawn this frame, so labels avoid each other
let popN = 0; // live muzzle flashes are pops[0..popN); the objects past it are kept for reuse
let mouse = null, selected = null, cardAt = null, cardLive = '', cardSwap = 0; // cardAt: the card's eased screen position
let opening = null, openingDue = false; // the opening shot while it runs, { e, wide, target, beats, hold }; due: the next Play runs it

// ---------- loading ----------

async function loadBattle(id) {
  const [raw, terrain] = await Promise.all([
    fetch(`battles/${id}/battle.json`).then(r => r.json()),
    fetch(`battles/${id}/terrain.json`).then(r => r.json()),
  ]);
  const b = normalizeBattle(raw), theme = themeFor(b, new URLSearchParams(location.search).get('theme'));
  if (theme !== themeFor(b)) theme.preview?.(b); // ?theme= tries a skin on another war's battle: the skin may recolour the sides
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
  ui.speedBox.dataset.lapse = `» ${b.lapse}×`;
  sizeClock();
  buildChapters(b); buildLegend(b); layoutTrack();
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
  ui.follow.checked = ui.lapse.checked = true;
  clampCam();
  const [link, , at, play, pickId, warp, shotTitle, legend, outcome, shotOpening, bench] = location.hash.match(/^#([^@,]*)(?:@([^,]+))?(,play)?(?:,select=([^,]+))?(,warp)?(,title)?(,legend)?(,outcome)?(,opening)?(,bench)?$/) ?? [];
  seek(at ? parseTime(at) : b.startT);
  openingDue = link === `#${id}`; // a bare link opens on the first Play; any time or flag goes straight to the battle
  setPlaying(!!play); setDrawer(!play || !!outcome);
  if (legend) ui.legendDlg.showModal(); // screenshots
  if (outcome) ui.outcome.open = true;
  if (pickId) select(b.units.find(u => u.id === pickId) ?? null); // screenshots: the card open on this unit
  document.body.classList.toggle('nofade', !!warp); // screenshots: skip the caption and card fades, and the chapter title unless ,title holds it
  if (warp) { // five seconds of frames for screenshots, framed around the caption, with the card beside its unit
    await document.fonts.ready; rects = null; capWeights = null; // the Fell faces resize the panels
    step(0); updateHud();
    for (let i = 0; i < 300; i++) step(1 / 60);
    draw(); updateHud();
    if (shotTitle) { showTitle(curEvent); ui.chTitle.classList.add('held'); }
  }
  if (shotOpening) { // screenshots: the opening held at its title
    await document.fonts.ready; rects = null; capWeights = null;
    startOpening(); opening.e = opening.hold = 3.2; step(0); draw();
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
// giving one candidate. Measured only when a panel or the window changes. `clear` is the candidate in use; the camera moves it to whichever shows the action
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
  const m = 10, panels = [...document.querySelectorAll('[data-clear]')].filter(el => el !== ui.caption || captionShows()).map(el => el.getBoundingClientRect());
  V.avoid = panels.map(p => ({ l: p.left, t: p.top, r: p.right, b: p.bottom })); // for the skin's map furniture
  const out = [], bar = ui.bar.getBoundingClientRect().top;
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
// A panel that changes size moves the clear rect and the chapter title; a caption strip that changes width re-pages.
let capWidth = 0;
const panelSizes = new ResizeObserver(es => {
  rects = null;
  for (const e of es) if (e.target === ui.caption && e.contentRect.width !== capWidth) { capWidth = e.contentRect.width; capWeights = null; }
  if (B) placeTitle();
});
for (const el of document.querySelectorAll('[data-clear]')) panelSizes.observe(el);
document.fonts.addEventListener('loadingdone', () => { rects = null; capWeights = null; }); // a face that arrives late rewraps the story

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
function userMoved() { ui.follow.checked = false; }

// Ease toward the action box fitted into the clear rect. It looks four real seconds ahead at the current clock rate.
function updateCamera(dt) {
  if (!ui.follow.checked) return;
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
  if (opening) return stepOpening(dt);
  if (playing) {
    [t, lapsing] = advance(B, t, dt, speed, ui.lapse.checked);
    if (t >= B.endT) setPlaying(false);
    let w = 0; // flashes age in real time; spent ones swap to the back of the pool
    for (let i = 0; i < popN; i++) { const q = pops[i]; q.age += dt; if (q.age < q.life) { pops[i] = pops[w]; pops[w++] = q; } }
    popN = w;
  }
  const ev = eventAt(B, t);
  if (ev !== curEvent) { // a chapter may set its own pace while the story is being followed
    curEvent = ev;
    if (ui.follow.checked) { speed = ev?.speed ?? defaultSpeed(B); ui.speed.value = speed; }
  }
  updateCamera(dt);
  for (const u of B.units) {
    const p = (u.pose = unitAt(u, t));
    if (playing && p && p.fire > 0 && p.state !== 'surrender') { const { F, nd } = shape(u, p, B.menPerDot); emit(u, p, F, nd, dt); }
  }
  if (playing) airClock += dt;
  if (playing) for (const f of B.features ?? []) if (f.type === 'airstrike' && t >= f.from && t < f.until) bombs(f, dt);
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

// ---------- the opening shot ----------

// The whole field, the battle's name over its date, then the camera closing in on the first chapter's frame; the clock
// waits until it lands (docs/adr/0009-opening-shot.md). Beats in real seconds: the title fades in at `titleIn` and out at
// `titleOut`, the camera eases from `ease` for `easeFor`, the panels fade back from `pageIn` and the clock starts at `end`.
// Under reduced motion the title holds still and the camera cuts.
const BEATS = {
  motion: { titleIn: 1, titleInFor: 1.2, titleOut: 4.2, titleOutFor: 1, drift: 0.03, ease: 5.2, easeFor: 4, pageIn: 8, end: 9.2 },
  still: { titleIn: 1, titleInFor: 0.4, titleOut: 3.6, titleOutFor: 0.4, drift: 0, ease: 4, easeFor: 0, pageIn: 4, end: 4 },
};
const ramp = x => Math.min(1, Math.max(0, x)), smooth = x => { const u = ramp(x); return u * u * (3 - 2 * u); };
const easeAt = ({ e, beats: b }) => (b.easeFor ? smooth((e - b.ease) / b.easeFor) : +(e >= b.ease));

// The target is where Follow settles for the first chapter, worked out now against the panels play will show.
function startOpening() {
  setDrawer(false); // first, so the landing is worked out against the closed drawer and the strip as play shows it
  openingDue = false;
  step(0); updateHud(0);
  for (let i = 0; i < 400; i++) updateCamera(0.1);
  opening = { e: 0, wide: { x: 0, y: 0, zoom: Math.min(W, H) / B.extent }, target: { ...cam }, beats: BEATS[matchMedia('(prefers-reduced-motion: reduce)').matches ? 'still' : 'motion'] };
  ui.opName.textContent = B.name; ui.opDate.textContent = B.dateText ?? B.date;
  ui.opening.hidden = false; document.body.classList.add('opening'); showTitle(null);
  setPlaying(true);
  stepOpening(0);
}
function stepOpening(dt) {
  const o = opening, b = o.beats;
  o.e = Math.min(o.hold ?? Infinity, o.e + dt);
  if (o.e >= b.end) return endOpening();
  const u = easeAt(o), mix = (p, q) => p + (q - p) * u;
  cam = { x: mix(o.wide.x, o.target.x), y: mix(o.wide.y, o.target.y), zoom: Math.exp(mix(Math.log(o.wide.zoom), Math.log(o.target.zoom))) };
  const a = Math.min(ramp((o.e - b.titleIn) / b.titleInFor), 1 - ramp((o.e - b.titleOut) / b.titleOutFor));
  ui.opening.style.opacity = a.toFixed(3);
  ui.opening.style.transform = `translate(-50%, -50%) scale(${(1 + b.drift * (1 - ramp((o.e - b.titleIn) / (b.titleOut + b.titleOutFor - b.titleIn)))).toFixed(4)})`;
  document.body.classList.toggle('opening', o.e < b.pageIn);
}
// Any input ends it at once: the camera cuts to its target, the page comes back, and the input then does what it does.
function endOpening() {
  cam = { ...opening.target }; opening = null;
  ui.opening.hidden = true; document.body.classList.remove('opening');
  showTitle(curEvent);
}
for (const type of ['pointerdown', 'keydown', 'wheel']) addEventListener(type, () => { if (opening) endOpening(); }, { capture: true });

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
  drawNight(); // the ground darkens; the regiments stay readable above it
  const labels = drawUnits();
  drawSmoke(); drawLabels(labels);
  for (const f of B.features ?? []) if (skin.air && f.air && t >= f.air[0] && t < f.air[1]) skin.air(ctx, V, f, airClock, f.type === 'drop' ? dropAt(f, t, airClock, lapsing ? B.lapse : speed) : null);
  skin.over?.(ctx, V);
  drawPops();
}

// Features that come and go (siegeworks dug, ships burnt) and every place name; the rest are baked into the layer.
function drawFeatures() {
  const k = Math.max(0.7, (cam.zoom * B.extent) / sheet.layer.width);
  placed.length = 0;
  for (const f of B.features ?? []) {
    if ((f.from != null && t < f.from) || (f.until != null && t >= f.until)) continue;
    const pts = f.pts ?? f.poly;
    if (pts && !isStatic(f)) skin.feature(ctx, f.type, pts.map(([x, y]) => [w2sx(x), w2sy(y)]), k, !!f.poly);
    if (f.name && f.at && !f.air) {
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
      type: u.type, gone: p.state === 'surrender', rout: p.state === 'rout', go: p.moving || p.state === 'column', mil: u.type === 'militia' || u.type === 'riflemen',
      cav: u.type === 'cavalry', art: u.type === 'artillery', guns: u.guns ?? 1 };
    skin.unit(ctx, U);
    // Every unit offers a label just above its topmost corner (a marching column is narrow but long); a skin may move it.
    const s = Math.sin(U.a), c = Math.cos(U.a), top = -Math.abs((wPx / 2) * s) + Math.min(-2 * c, (hPx + 1) * c);
    const l = { u, U, text: u.short ?? u.name, x: sx, y: sy + top - 11, size: Math.min(17, 12 + z * 3), men: p.strength };
    skin.label.place?.(l);
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

// A firing unit's flashes and smoke. A tank fires its gun now and then, flashing like a field piece; the skin's smoke
// `rate` and the battle's `smoke` thin the smoke (smokeless powder) but never the flashes.
function emit(u, p, F, nd, dt) {
  const art = u.type === 'artillery' || u.type === 'armor', wind = B.wind ?? { x: 0.8, y: 0.3 }, life = sheet.smoke.life;
  const rate = p.fire * (u.type === 'artillery' ? (u.guns ?? 1) * 0.5 : nd * (art ? 0.12 : 0.35)), thin = (sheet.smoke.rate ?? 1) * (B.smoke ?? 1);
  let n = Math.floor(rate * dt + Math.random());
  const rad = (p.h * Math.PI) / 180, dx = Math.sin(rad), dy = Math.cos(rad);
  while (n-- > 0) {
    const uu = (Math.random() - 0.5) * F, x = p.x + uu * dy + 2 * dx, y = p.y - uu * dx + 2 * dy;
    if (smoke.length < 2500 && Math.random() < thin) smoke.push({ x, y, vx: wind.x + dx * 1.2 + Math.random() - 0.5, vy: wind.y + dy * 1.2 + Math.random() - 0.5,
      age: 0, life: (art ? 4.5 : 2.4 + Math.random() * 1.6) * life, r0: art ? 4 : 2, r1: art ? 22 : 11, k: Math.random() });
    if (popN < 400) { // a musket pops for a tenth of a second or so; a gun's flash is bigger and lasts longer
      const q = (pops[popN++] ??= {});
      q.x = x; q.y = y; q.age = 0; q.side = u.side; q.dx = dx; q.dy = dy; q.art = art; q.k = Math.random(); // dx, dy: the line of fire, north up
      q.life = art ? 0.18 + Math.random() * 0.1 : 0.08 + Math.random() * 0.12;
      q.r = art ? 11 + Math.random() * 7 : 3.5 + Math.random() * 3; // glow radius in pixels; the white core is a fifth of it
    }
  }
}

// An air strike's bombs: two or three a second of play burst within `spread` of the target, each a big flash and a
// column of dust. The skin flies the aircraft (air).
function bombs(f, dt) {
  const wind = B.wind ?? { x: 0.8, y: 0.3 }, sp = f.spread ?? 150;
  let n = Math.floor(2.5 * dt + Math.random());
  while (n-- > 0) {
    const a = Math.random() * 2 * Math.PI, d = sp * Math.sqrt(Math.random()), x = f.at[0] + Math.cos(a) * d, y = f.at[1] + Math.sin(a) * d;
    for (let i = 0; i < 4 && smoke.length < 2500; i++) smoke.push({ x: x + (Math.random() - 0.5) * 20, y: y + (Math.random() - 0.5) * 20, vx: wind.x * 2 + Math.random() - 0.5,
      vy: wind.y * 2 + Math.random() - 0.5, age: 0, life: (5 + Math.random() * 3) * sheet.smoke.life, r0: 12, r1: 60, k: Math.random() });
    if (popN < 400) {
      const q = (pops[popN++] ??= {});
      Object.assign(q, { x, y, age: 0, side: null, dx: 0, dy: 1, art: true, k: Math.random(), life: 0.3 + Math.random() * 0.15, r: 24 + Math.random() * 10 });
    }
  }
}

function drawPops() {
  if (!playing || !popN) return;
  const s = Math.min(2, Math.max(0.8, Math.sqrt(cam.zoom))); // a little bigger close up, never lost far out
  skin.fire?.(ctx, V, pops, popN); // what else the skin's fire draws, such as tracer
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
    const tod = mod(t, 86400);
    dark = ramp((B.sunriseT - tod) / 2800);
    if (B.sunsetT != null) dark = Math.max(dark, ramp((tod - B.sunsetT) / 2800));
  }
  if (opening && dark > 0.35) dark = 0.35 + (dark - 0.35) * easeAt(opening); // dawn under the title, so the field reads; true dark by the landing
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

// ---------- the timeline and legend ----------

// A tick a chapter above the groove (CSS places them by --f) and a row a chapter in the drawer's list, under day headings
// when the battle runs over more than one day. A row's click jumps there and turns Follow back on; the drawer stays open.
let tickXs = []; // each tick's screen x, for the tip; measured when the track changes size
const frac = t => Math.min(1, Math.max(0, (t - B.startT) / (B.endT - B.startT)));
const dayOf = t => { const { day, month } = clockParts(t); return day == null ? '' : `${day} ${MONTHS[month]}`; };
function buildChapters(b) {
  const time = skin.time ?? timeOfDay, multi = new Set(b.events.map(ev => dayOf(ev.t))).size > 1, rows = [];
  let day = null;
  for (const ev of b.events) {
    if (multi && dayOf(ev.t) !== day) rows.push(Object.assign(document.createElement('h3'), { className: 'day', textContent: (day = dayOf(ev.t)) }));
    const row = document.createElement('div'), go = document.createElement('button'), when = document.createElement('span'), story = document.createElement('p');
    row.className = 'ch'; when.className = 'time'; when.textContent = time(ev.t); story.textContent = ev.text;
    go.append(when, ev.title); go.onclick = () => { ui.follow.checked = true; seek(ev.t); };
    row.append(go, story); rows.push(row);
  }
  ui.chList.replaceChildren(...rows); ui.chList.scrollTop = 0;
  ui.marks.replaceChildren(...b.events.map(ev => { const i = document.createElement('i'); i.style.setProperty('--f', frac(ev.t).toFixed(5)); return i; }));
  markOn();
}
// The current chapter's tick, row and count; the list scrolls to the row when the drawer is open.
function markOn() {
  const i = B.events.indexOf(curEvent), n = B.events.length;
  [...ui.marks.children].forEach((m, j) => m.classList.toggle('on', j === i));
  ui.chList.querySelectorAll('.ch').forEach((r, j) => r.classList.toggle('on', j === i));
  ui.chCount.innerHTML = i < 0 ? `${n} chapters` : `Chapters <em>${i + 1} of ${n}</em>`;
  if (ui.top.classList.contains('open')) showRow();
}
function showRow() {
  const r = ui.chList.querySelector('.ch.on'), L = ui.chList, head = L.querySelector('.day')?.offsetHeight ?? 0;
  if (!r) return;
  if (r.offsetTop - head < L.scrollTop) L.scrollTop = r.offsetTop - head;
  else if (r.offsetTop + r.offsetHeight > L.scrollTop + L.clientHeight) L.scrollTop = Math.min(r.offsetTop - head, r.offsetTop + r.offsetHeight - L.clientHeight);
}
function layoutTrack() {
  const r = ui.scrub.getBoundingClientRect(), th = parseFloat(getComputedStyle(ui.track).getPropertyValue('--thumb'));
  tickXs = B.events.map(ev => r.left + th / 2 + frac(ev.t) * (r.width - th));
  layoutHours(r.width - th, B.endT - B.startT, th);
  placeTitle();
}
// The pointer over the scrubber names the nearest chapter within 12 px. Hover only: a click seeks as it always has.
ui.scrub.addEventListener('pointermove', e => {
  const i = nearest(tickXs, e.clientX, 12), tip = ui.tickTip;
  if (i < 0) { tip.hidden = true; return; }
  if (!tip.hidden && tip.dataset.i === String(i)) return;
  const ev = B.events[i], day = new Set(B.events.map(e => dayOf(e.t))).size > 1 ? `${dayOf(ev.t)}, ` : '';
  const when = document.createElement('small'); when.textContent = day + (skin.time ?? timeOfDay)(ev.t);
  tip.replaceChildren(ev.title, when); tip.dataset.i = i; tip.hidden = false;
  tip.style.left = `${tickXs[i]}px`; tip.style.setProperty('--f', frac(ev.t).toFixed(4));
});
ui.scrub.addEventListener('pointerleave', () => { ui.tickTip.hidden = true; });

// The chapter title: the name fading in just above the caption strip, or the bar when no strip shows, on the page's clock
// (index.html). Centred in the map less 48 px each side, narrowed past a panel that reaches down level with it, such as the
// open drawer. Showing one restarts its animation; null clears it.
function placeTitle() {
  const el = ui.chTitle, box = e => e.getBoundingClientRect();
  const bottom = box(captionShows() ? ui.caption : ui.bar).top - 14, top = bottom - el.offsetHeight;
  let l = 48, r = W - 48;
  for (const p of [ui.top, ui.clockBox, ui.settings].map(box)) {
    if (!p.width || p.bottom <= top || p.top >= bottom) continue;
    if (p.left + p.right < W) l = Math.max(l, p.right + 24); else r = Math.min(r, p.left - 24);
  }
  Object.assign(el.style, { bottom: `${H - bottom}px`, left: `${(l + r) / 2}px`, maxWidth: `${Math.max(0, r - l)}px` });
}
function showTitle(ev) {
  const el = ui.chTitle;
  el.classList.remove('run', 'held');
  if (!ev) return;
  el.firstChild.textContent = ev.title; placeTitle();
  void el.offsetWidth; // a reflow between, so the animation starts again
  el.classList.add('run');
}

// The scale of hours under the scrubber, for a skin that rules one: alternate inked and blank segments of a round number
// of hours (or days) at least 40 px wide, named every 70 px or so. --seg and --seg0 size and place the segments.
function layoutHours(tw, dur, th) {
  ui.hours.replaceChildren();
  if (!skin.hours) return;
  const unit = [900, 1800, 3600, 7200, 10800, 21600, 43200, 86400, 172800, 604800].find(u => (tw * u) / dur >= 40) ?? 604800;
  const seg = (tw * unit) / dur, first = Math.ceil(B.startT / unit) * unit;
  let named = unit * Math.ceil(70 / seg); // a name every 70 px or so, on the hour
  if (named < 3600) named = 3600; else if (named < 86400) named = Math.ceil(named / 3600) * 3600;
  ui.scrub.style.setProperty('--seg', `${seg.toFixed(2)}px`);
  ui.scrub.style.setProperty('--seg0', `${(th / 2 + ((first - B.startT) / dur) * tw).toFixed(2)}px`);
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
  armor: () => 'Armor: a mark for each vehicle.',
  airstrike: () => 'Air attack: bombs bursting round the target.',
  drop: b => `Airborne landing: aircraft over the zone, a canopy for every ${b.menPerDot} men or a glider each, and the men making for their unit.`,
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
      type, gone: state === 'surrender', rout: state === 'rout', go: state === 'column', mil, cav: type === 'cavalry', art: type === 'artillery', guns: 3 });
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
    types.has('armor') && [unitSwatch(s0, { w: 52, h: 6, y: 15, files: 4, ranks: 1, type: 'armor' }), say('armor')],
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
      skin.unit(g, { u: { id: 'legend', type: 'infantry' }, p: { state: 'firing', h: 0, strength: 60 }, side: s0, x: 22, y: 20, a: 0, w: 24, h: 4, z: 1, dots: null, type: 'infantry', guns: 1 });
      sheet.smoke.sprites.forEach((sp, i) => { g.globalAlpha = sheet.smoke.alpha * (0.9 - i * 0.15); g.drawImage(sp, 22 + i * 9, 1 + (3 - i) * 2, 14 + i * 5, 14 + i * 5); });
      g.globalAlpha = 1; g.drawImage(sheet.flash, 14, 9, 14, 14);
    }), say('fire')],
    ...(L.extra?.(b, sheet) ?? []).map(([draw, text]) => [swatch(g => draw(g, s0, sheet)), text]),
    ...['redoubt', 'works', 'trench', 'camp', 'ship', 'road', 'creek', 'fence'].filter(k => feats.has(k)).map(k =>
      [swatch(g => skin.feature(g, k, FEATURE_SWATCH[k], 0.8, ['redoubt', 'camp', 'ship'].includes(k))), say(k)]),
    (b.water != null || feats.has('water')) && [swatch(g => L.swatch.water(g, sheet)), say('water')],
    feats.has('airstrike') && L.swatch.airstrike && [swatch(g => L.swatch.airstrike(g, sheet)), say('airstrike')],
    feats.has('drop') && L.swatch.drop && [swatch(g => L.swatch.drop(g, sheet)), say('drop')],
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
  showClock(t); ui.clockBox.classList.toggle('lapsing', playing && lapsing);
  ui.scrub.value = t; ui.scrub.style.setProperty('--p', `${frac(t) * 100}%`);
  const turned = curEvent !== shownEvent;
  if (turned) {
    shownEvent = curEvent;
    ui.capTitle.textContent = curEvent?.title ?? '';
    ui.capWhen.textContent = !curEvent ? '' : skin.when?.(curEvent, B) ?? chapterWhen(curEvent); // a skin may word the time its own way
    ui.caption.classList.toggle('show', !!curEvent); rects = null; capWeights = null;
    markOn();
  }
  if (!capWeights) pageCaption(curEvent);
  if (curEvent) turnPage(captionPage(B, curEvent, t, capWeights));
  if (turned && !quiet && !opening) showTitle(curEvent);
  quiet = false;
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

const NOUN = { armor: 'vehicles' }; // what a unit's strength counts, by type: men unless named here
const liveText = u => (u.pose ? `${Math.round(u.pose.strength)} ${NOUN[u.type] ?? 'men'} · ${STATE_TEXT[u.pose.state] ?? ''}` : '');
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
function placeCard(dt) {
  const u = selected, s = u?.screen;
  if (!u) return;
  if (!u.pose) return select(null); // gone from the field
  if (!s) return;
  if (!ui.card.classList.contains('swap')) { const live = liveText(u); if (live !== cardLive) ui.cardLive.textContent = cardLive = live; }
  const [cw, ch] = cardSize, S = safeRect(), g = 14, c = Math.cos(s.a), n = Math.sin(s.a), mid = s.h / 2;
  let target;
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
// The story cut into pages of whole sentences, as many as fit three lines of the strip, measured on the real element so
// the skin's face, case and suffix count. Run when the chapter or the strip's width changes, never per frame. The strip
// is held at its tallest page, so a page turn never moves the clear rect.
let capWeights = null; // the pages' character counts; null re-pages on the next frame
const captionShows = () => ui.caption.classList.contains('show') && ui.captions.checked;
function pageCaption(ev) {
  const probe = document.createElement('p');
  ui.capText.style.minHeight = ''; ui.capText.replaceChildren(probe); // the probe is the last child, as the last page is
  const max = 3 * parseFloat(getComputedStyle(probe).lineHeight) + 1, h = s => { probe.textContent = s; return probe.offsetHeight; };
  const pages = ev ? paginate(ev.text, s => h(s) <= max) : [], tall = Math.max(0, ...pages.map(h));
  ui.capText.replaceChildren(...pages.map((s, i) => Object.assign(document.createElement('p'), { textContent: s, hidden: i > 0 })));
  ui.capText.style.minHeight = `${tall}px`;
  ui.capPips.replaceChildren(...pages.map((_, i) => Object.assign(document.createElement('i'), { className: i ? '' : 'on' })));
  capWeights = pages.map(s => s.length); rects = null;
}
function turnPage(i) {
  const p = ui.capText.children[i];
  if (!p?.hidden) return;
  for (const q of ui.capText.children) q.hidden = q !== p;
  [...ui.capPips.children].forEach((d, j) => d.classList.toggle('on', j === i));
}

// The drawer: the chip's Chapters opens it, Close and Esc close it, and so does Play when play starts. Instant, so a
// measure straight after sees the final layout.
function setDrawer(v) {
  ui.top.classList.toggle('open', v); ui.chaptersBtn.setAttribute('aria-expanded', v);
  rects = null; capWeights = null;
  if (!B) return;
  placeTitle();
  if (v) showRow(); else if (ui.top.contains(document.activeElement)) ui.chaptersBtn.focus();
}
ui.chaptersBtn.onclick = () => { setDrawer(true); ui.topClose.focus(); };
ui.topClose.onclick = () => setDrawer(false);
function setSettings(v) { ui.settings.hidden = !v; ui.settingsBtn.setAttribute('aria-expanded', v); placeTitle(); }
ui.settingsBtn.onclick = () => setSettings(ui.settings.hidden);
addEventListener('pointerdown', e => { if (!ui.settings.hidden && !ui.settings.contains(e.target) && !ui.settingsBtn.contains(e.target)) setSettings(false); }, { capture: true });
ui.captions.addEventListener('change', () => { rects = null; placeTitle(); });

// The settings the browser keeps for every battle. An element's markup value is its default, replaced at boot by a stored
// one. Storage may be blocked, so every read and write is inside try. Elements sharing a key with data-field store one
// JSON object of them all, so the stored object is always whole.
function bindPrefs() {
  const byKey = Map.groupBy(document.querySelectorAll('[data-pref]'), el => el.dataset.pref);
  for (const [key, els] of byKey) {
    let raw = null;
    try { raw = localStorage.getItem(key); } catch {}
    const fields = !!els[0].dataset.field, fill = el => el.style.setProperty('--p', `${el.value}%`);
    let stored = null;
    if (fields) try { stored = JSON.parse(raw); } catch {}
    for (const el of els) {
      if (!fields) { if (raw === 'on' || raw === 'off') el.checked = raw === 'on'; }
      else { const n = stored?.[el.dataset.field]; if (Number.isInteger(n) && n >= 0 && n <= 100) el.value = n; fill(el); }
      el.addEventListener(fields ? 'input' : 'change', () => {
        if (fields) fill(el);
        const v = fields ? JSON.stringify(Object.fromEntries(els.map(e => [e.dataset.field, +e.value]))) : el.checked ? 'on' : 'off';
        try { localStorage.setItem(key, v); } catch {}
      });
    }
  }
}
bindPrefs();

const nudge = () => Math.max(30, (B.endT - B.startT) / 240); // arrow keys: 30 s, or 1/240 of a long battle
function setPlaying(v) { playing = v; ui.play.textContent = v ? '❚❚' : '▶'; ui.play.setAttribute('aria-label', v ? 'Pause' : 'Play'); }
function seek(v) { t = Math.max(B.startT, Math.min(B.endT, v)); smoke.length = 0; popN = 0; openingDue = false; }

ui.play.onclick = () => {
  if (!playing) setDrawer(false);
  if (!playing && openingDue) return startOpening();
  if (!playing && t >= B.endT) seek(B.startT);
  setPlaying(!playing);
};
ui.speed.onchange = () => { speed = +ui.speed.value; };
ui.scrub.oninput = () => { quiet = true; seek(+ui.scrub.value); };
ui.srcBtn.onclick = () => ui.sources.showModal();
ui.legendBtn.onclick = () => ui.legendDlg.showModal();
addEventListener('keydown', e => {
  if (e.key === 'Escape' && !document.querySelector('dialog[open]')) { // one layer a press, innermost first; a dialog closes itself
    if (!ui.settings.hidden) return setSettings(false);
    if (ui.top.classList.contains('open')) return setDrawer(false);
    if (selected) return select(null);
  }
  if (['INPUT', 'SELECT', 'BUTTON'].includes(e.target.tagName)) return;
  if (e.code === 'Space') { e.preventDefault(); ui.play.click(); }
  else if (e.key === 'ArrowRight') { quiet = true; seek(t + nudge()); }
  else if (e.key === 'ArrowLeft') { quiet = true; seek(t - nudge()); }
  else if (e.key === 'f') ui.follow.click();
  else if (e.key === 't') ui.lapse.click();
  else if (e.key === 'c') ui.titles.click();
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
addEventListener('resize', () => { resize(); if (opening) endOpening(); if (B) { clampCam(); sizeClock(); } if (selected) fillCard(selected); });
new ResizeObserver(() => B && layoutTrack()).observe(ui.track);
resize();

function frame(now) {
  const dt = Math.min(0.1, (now - last) / 1000);
  last = now;
  if (B) { step(dt); draw(); updateHud(dt); }
  requestAnimationFrame(frame);
}

for (const s of SPEEDS) ui.speed.add(new Option(`${s}×`, s));
const list = (await (await fetch('battles/index.json')).json()).sort((a, b) => a.date.localeCompare(b.date));
const named = () => location.hash.slice(1).split(/[@,]/)[0]; // a battle, a war (#ww2) or nothing (the Revolution)
if (list.some(b => b.id === named())) await loadBattle(named());
else showSplash(list, WARS.some(w => w.id === named()) ? named() : WARS[0].id, async id => {
  ui.splash.hidden = true;
  await loadBattle(id); startOpening(); // loadBattle puts the battle in the hash
});
// The battles and the war lists are hashes of one page, so All battles, Back and Forward change only the hash: load what it names.
addEventListener('hashchange', () => { if (named() !== B?.id) location.reload(); });
ui.home.onclick = () => { location.hash = WARS.find(w => w.war === list.find(e => e.id === B.id).war).id; };
requestAnimationFrame(frame);
if (navigator.webdriver) window.fg = { // journeys only: read the camera and clock, and hold the opening at a moment for a frame
  state: () => ({ cam: { ...cam }, t, playing, follow: ui.follow.checked, opening: opening && { e: opening.e, wide: opening.wide, target: opening.target } }),
  hold: e => { if (opening) opening.hold = opening.e = e; },
};
