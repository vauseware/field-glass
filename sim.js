// Battle replay logic with no DOM dependencies. Shared by app.js and tools/check.mjs.

export const SPEEDS = [1, 2, 5, 10, 20, 30, 60, 120, 300, 600, 1800, 3600, 7200];
export const STATES = ['hidden', 'column', 'line', 'skirmish', 'firing', 'charge', 'retreat', 'rout', 'surrender'];
export const TYPES = ['infantry', 'light_infantry', 'militia', 'riflemen', 'cavalry', 'artillery', 'armor'];
export const STATE_TEXT = { column: 'in column', line: 'in line', skirmish: 'skirmishing', firing: 'firing', charge: 'charging', retreat: 'withdrawing', rout: 'routed', surrender: 'surrendered' };

// "HH:MM[:SS]" is seconds into the day. "YYYY-MM-DD HH:MM[:SS]" (a T also separates) is seconds since 1970,
// negative before it, so a battle that runs for weeks uses the same arithmetic. Numbers pass through.
export function parseTime(v) {
  if (typeof v === 'number') return v;
  const [date, clock] = String(v).includes('-') ? String(v).split(/[ T]/) : [null, String(v)];
  const [h, m = 0, s = 0] = clock.split(':').map(Number);
  let day = 0;
  if (date) { const [y, mo, d] = date.split('-').map(Number); day = Date.UTC(y, mo - 1, d) / 1000; }
  return day + h * 3600 + m * 60 + s;
}

export const mod = (a, n) => ((a % n) + n) % n;
export const MONTHS = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split(' ');
// Hour, minute, and for a dated time its day and month index, for the skins' clocks.
export function clockParts(t) {
  const h = mod(Math.floor(t / 3600), 24), m = mod(Math.floor(t / 60), 60);
  if (Math.abs(t) < 366 * 86400) return { h, m, day: null, month: null };
  const d = new Date(t * 1000);
  return { h, m, day: d.getUTCDate(), month: d.getUTCMonth() };
}
export function fmtTime(t) {
  const { h, m, day, month } = clockParts(t), clock = `${h % 12 || 12}:${String(m).padStart(2, '0')} ${h < 12 ? 'AM' : 'PM'}`;
  return day == null ? clock : `${day} ${MONTHS[month]}, ${clock}`;
}

export function hash(s) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619);
  return h >>> 0;
}

export function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), a | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const lerp = (a, b, f) => a + (b - a) * f;
export function lerpAngle(a, b, f) {
  const d = ((b - a + 540) % 360) - 180;
  return (a + d * f + 360) % 360;
}
const angleGap = (a, b) => Math.abs(mod(b - a + 180, 360) - 180);

const fireLevel = s => (s === 'firing' ? 1 : s === 'skirmish' ? 0.3 : 0);

// Parse times, sort keys, carry missing key fields forward, precompute casualty markers.
export function normalizeBattle(b) {
  b.startT = parseTime(b.start);
  b.endT = parseTime(b.end);
  b.sunriseT = b.sunrise == null ? null : parseTime(b.sunrise);
  b.sunsetT = b.sunset == null ? null : parseTime(b.sunset);
  b.lapse ??= Math.min(7200, (b.speed ?? 10) * 6); // clock rate for quiet stretches when time-lapse is on
  b.menPerDot ??= 10;
  for (const f of [...(b.features ?? []), ...(b.tints ?? [])]) { if (f.from != null) f.from = parseTime(f.from); if (f.until != null) f.until = parseTime(f.until); }
  for (const u of b.units) {
    let x = 0, y = 0, h = 0, strength = u.strength, state = 'line';
    u.keys = (u.keys ?? []).map(k => ({ ...k, t: parseTime(k.t) })).sort((p, q) => p.t - q.t);
    for (const k of u.keys) {
      x = k.x ?? x; y = k.y ?? y; h = k.h ?? h; strength = k.strength ?? strength; state = k.state ?? state;
      Object.assign(k, { x, y, h, strength, state, fire: k.fire ?? fireLevel(state) });
    }
    // A key's facing is reached as late as possible, just before that key: a line keeps firing at the enemy until it turns
    // to go. A unit marching off along its new facing turns first, then marches.
    for (let i = 0; i + 1 < u.keys.length; i++) {
      const a = u.keys[i], c = u.keys[i + 1], m = (Math.atan2(c.x - a.x, c.y - a.y) * 180) / Math.PI;
      a.turnFirst = (a.x !== c.x || a.y !== c.y) && angleGap(c.h, m) < angleGap(a.h, m);
    }
  }
  b.events = (b.events ?? []).map(e => ({ ...e, t: parseTime(e.t) })).sort((p, q) => p.t - q.t);
  planAir(b);
  b.fallen = fallenMarkers(b);
  b.active = activeSpans(b);
  return b;
}

const BUSY = new Set(['skirmish', 'firing', 'charge', 'retreat', 'rout']);
// Stretches of battle time when something moves, fights, or appears, merged, with `lead` seconds in front
// so the time-lapse slows down before it happens. Artillery firing alone does not count: a siege
// bombardment runs for days.
function activeSpans(b, lead = 90) {
  const raw = [];
  for (const u of b.units) {
    const k = u.keys, busy = s => BUSY.has(s) && u.type !== 'artillery';
    for (let i = 0; i + 1 < k.length; i++) {
      const a = k[i], c = k[i + 1];
      if (a.state === 'hidden') { if (c.state !== 'hidden') raw.push([c.t, c.t + 60]); continue; }
      if (a.x !== c.x || a.y !== c.y || a.h !== c.h || busy(a.state)) raw.push([a.t, c.t]);
    }
    if (k.length && busy(k[k.length - 1].state)) raw.push([k[k.length - 1].t, b.endT]);
  }
  for (const f of [...(b.features ?? []), ...(b.tints ?? [])]) { if (f.from != null) raw.push([f.from, f.from + 300]); if (f.until != null) raw.push([f.until, f.until + 300]); }
  for (const f of b.features ?? []) { const P = PLANS.get(f); if (P?.men) raw.push([P.t0, P.end]); }
  raw.sort((p, q) => p[0] - q[0]);
  const out = [];
  for (const [s, e] of raw) {
    const st = s - lead, last = out[out.length - 1];
    if (last && st <= last[1]) last[1] = Math.max(last[1], e); else out.push([st, e]);
  }
  return out;
}

// [busy, until]: whether t is inside an active span, and when that answer changes (Infinity after the last).
export function activity(b, t) {
  for (const [s, e] of b.active) { if (t < s) return [false, s]; if (t < e) return [true, e]; }
  return [false, Infinity];
}

// One playback step: dt real seconds at this speed, hurrying through quiet stretches when time-lapse is on but never
// past the start of the next action. Returns [new battle time, lapsing].
export function advance(b, t, dt, speed, lapse) {
  const [busy, until] = activity(b, t), lapsing = lapse && !busy && b.lapse > speed;
  let n = t + dt * (lapsing ? b.lapse : speed);
  if (lapsing && n > until) n = until;
  return [Math.min(n, b.endT), lapsing];
}
export const defaultSpeed = b => (SPEEDS.includes(b.speed) ? b.speed : 10);

// Real seconds to play the whole battle as it opens: default speed, chapter speeds, Follow and Time-lapse on.
export function playTime(b, dt = 1 / 30) {
  let t = b.startT, cur, speed = defaultSpeed(b), secs = 0;
  while (t < b.endT) {
    const ev = eventAt(b, t);
    if (ev !== cur) { cur = ev; speed = ev?.speed ?? defaultSpeed(b); }
    [t] = advance(b, t, dt, speed, true);
    secs += dt;
  }
  return Math.round(secs);
}

// ---------- the caption strip ----------

// Which page of a chapter's story shows at battle time t. The chapter's playing time, counted as playTime counts it
// (1/30 s steps of advance() at the chapter's speed, Time-lapse on), is shared among its pages by `weights`, their
// character counts. 0 at the chapter's start, the last page just before the next chapter, never falling as t rises.
// The viewer's own speed and switches do not change it: the page depends on the battle time alone.
export function captionPage(b, ev, t, weights) {
  const starts = pageStarts(b, ev, weights);
  let i = 0;
  while (i < starts.length && t >= starts[i]) i++;
  return i;
}

// The battle times at which pages 1..n-1 begin, worked out once per chapter and weights. The step grid starts at the
// chapter's start, so a chapter's pages do not depend on the chapters before it.
const STARTS = new WeakMap(); // ev -> { weights, key, starts }
export function pageStarts(b, ev, weights) {
  let m = STARTS.get(ev);
  if (m?.weights !== weights) { // a new array with the same counts reuses the work
    const key = weights.join(',');
    STARTS.set(ev, (m = { weights, key, starts: m?.key === key ? m.starts : startsOf(b, ev, weights) }));
  }
  return m.starts;
}
function startsOf(b, ev, weights, dt = 1 / 30) {
  const next = b.events[b.events.indexOf(ev) + 1], end = Math.min(b.endT, next?.t ?? b.endT), speed = ev.speed ?? defaultSpeed(b);
  if (weights.length < 2 || !(end > ev.t)) return [];
  const xs = [ev.t]; // the battle time after each step
  while (xs[xs.length - 1] < end) xs.push(advance(b, xs[xs.length - 1], dt, speed, true)[0]);
  const n = xs.length - 1, steps = n - 1 + (end - xs[n - 1]) / (xs[n] - xs[n - 1]); // the chapter's length in steps, to `end`
  const total = weights.reduce((a, w) => a + w, 0), out = [];
  let acc = 0;
  for (let k = 0; k + 1 < weights.length; k++) {
    acc += weights[k];
    const r = (steps * acc) / total, s = Math.floor(r); // 0 < r < steps, so the start lies before `end`
    out.push(xs[s] + (xs[s + 1] - xs[s]) * (r - s));
  }
  return out;
}

// A story cut into sentences. A full stop, ! or ? ends one only before a capital, a digit or an opening quote, and never
// after a single capital ("S. D. Lee"), a dotted initialism ("U.S.", "p.m.") or a rank or title ("Brig. Gen."); an
// ellipsis never ends one. A missed break only makes a page longer, so the rules err that way.
const ABBR = new Set(['Gen', 'Brig', 'Maj', 'Lt', 'Col', 'Capt', 'Sgt', 'Cpl', 'Pvt', 'Adm', 'Cdr', 'Gov', 'Pres', 'Sen', 'Hon', 'Rev', 'Dr',
  'Mr', 'Mrs', 'Messrs', 'St', 'Ft', 'Mt', 'No', 'Co', 'Jr', 'Sr', 'Bn', 'Regt', 'Div', 'Bde', 'Bty', 'vs', 'c']);
export function sentences(text) {
  const out = [], re = /([.!?]+)(['’”")\]]*)\s+(?=['‘“"(]?[A-Z0-9])/g;
  let from = 0, m;
  while ((m = re.exec(text))) {
    const word = text.slice(from, m.index).match(/(\S*)$/)[1].replace(/^[^A-Za-z0-9]+/, '');
    if (m[1].length > 1 || (m[1] === '.' && (/^[A-Z]$/.test(word) || /^(?:[A-Za-z]\.)+[A-Za-z]$/.test(word) || ABBR.has(word)))) continue;
    out.push(text.slice(from, m.index + m[0].trimEnd().length)); from = re.lastIndex;
  }
  if (from < text.length) out.push(text.slice(from).trim());
  return out.filter(Boolean);
}

// Whole sentences per page, as many as `fits` allows. A sentence that does not fit alone breaks after its semicolons;
// a clause that still does not fit keeps a page to itself (the strip grows, nothing is clipped). A page under `min`
// characters then joins a neighbour when the pair fits, or takes the last sentence of the page before.
export function paginate(text, fits, min = 25) {
  const units = sentences(text).flatMap(s => (fits(s) ? [s] : s.split(/(?<=;)\s+/))), say = p => p.join(' '), pages = [];
  for (const u of units) { const p = pages.at(-1); if (p && fits(say([...p, u]))) p.push(u); else pages.push([u]); }
  for (let j = 0; j < pages.length && pages.length > 1; j++) {
    const p = pages[j], prev = pages[j - 1], next = pages[j + 1];
    if (say(p).length >= min) continue;
    if (prev && fits(say([...prev, ...p]))) { prev.push(...p); pages.splice(j--, 1); }
    else if (next && fits(say([...p, ...next]))) { next.unshift(...p); pages.splice(j--, 1); }
    else if (prev?.length > 1 && say(prev.slice(0, -1)).length >= min && fits(say([prev.at(-1), ...p]))) p.unshift(prev.pop());
  }
  return pages.map(say);
}

// The time of day for the chapter list and the tick tip when a skin has no `time` hook: "6:30 AM", "8 AM".
export function timeOfDay(t) {
  const { h, m } = clockParts(t);
  return `${h % 12 || 12}${m ? `:${String(m).padStart(2, '0')}` : ''} ${h < 12 ? 'AM' : 'PM'}`;
}

// The index of the x in xs nearest to x, or -1 when none lies within `within`.
export function nearest(xs, x, within) {
  let best = -1, d = within;
  xs.forEach((v, i) => { if (Math.abs(v - x) <= d) { best = i; d = Math.abs(v - x); } });
  return best;
}

const TURN = 50; // battle seconds a formation takes to wheel to a new facing, at the start or end of a segment (see turnFirst)
// Pose of a unit at battle time t, or null while hidden. State is a step function of the previous key.
export function unitAt(u, t) {
  const k = u.keys;
  if (!k.length || t < k[0].t) return null;
  let i = k.length - 1;
  while (i > 0 && k[i].t > t) i--;
  const a = k[i], c = k[i + 1];
  if (a.state === 'hidden') return null;
  if (!c || c.t <= a.t) return { x: a.x, y: a.y, h: a.h, strength: a.strength, state: a.state, fire: a.fire, moving: false };
  const f = (t - a.t) / (c.t - a.t), span = Math.min(c.t - a.t, TURN);
  const g = Math.min(1, Math.max(0, (a.turnFirst ? t - a.t : t - c.t + span) / span));
  return { x: lerp(a.x, c.x, f), y: lerp(a.y, c.y, f), h: lerpAngle(a.h, c.h, g * g * (3 - 2 * g)), strength: lerp(a.strength, c.strength, f), state: a.state, fire: a.fire,
    moving: a.x !== c.x || a.y !== c.y };
}

const grow = (bx, x0, y0, x1, y1) => (bx ? { x0: Math.min(bx.x0, x0), y0: Math.min(bx.y0, y0), x1: Math.max(bx.x1, x1), y1: Math.max(bx.y1, y1) } : { x0, y0, x1, y1 });
const focusBox = (b, ev) => { const r = (ev.view ?? b.extent * 0.6) / 2; return { x0: ev.at[0] - r, y0: ev.at[1] - r, x1: ev.at[0] + r, y1: ev.at[1] + r }; };
// World box {x0,y0,x1,y1} for the camera at t: the chapter's focus, sliding toward the next chapter's over the last `ahead`
// seconds before it, joined by every nearby unit that moves or fights now or within `ahead` seconds, so marching columns
// stay in frame and the camera is already looking where they are going. Nearby is within half a focus width of the focus:
// the fight on another part of the field is another chapter's story. Null when there is nothing to frame.
export function actionBox(b, t, ahead, pad = 30) {
  const ev = eventAt(b, t), nx = b.events.find(e => e.t > t && e.at);
  let fb = ev?.at ? focusBox(b, ev) : null;
  if (nx && nx.t - t < ahead) {
    const f = 1 - (nx.t - t) / ahead, nb = focusBox(b, nx);
    fb = fb ? { x0: lerp(fb.x0, nb.x0, f), y0: lerp(fb.y0, nb.y0, f), x1: lerp(fb.x1, nb.x1, f), y1: lerp(fb.y1, nb.y1, f) } : nb;
  }
  const reach = fb ? Math.max(fb.x1 - fb.x0, fb.y1 - fb.y0) / 2 : Infinity;
  let bx = fb;
  for (const u of b.units) for (let i = 0; i <= 4; i++) {
    const p = unitAt(u, t + (ahead * i) / 4);
    if (!p || !(p.moving || BUSY.has(p.state))) continue;
    if (fb && Math.max(fb.x0 - p.x, p.x - fb.x1, fb.y0 - p.y, p.y - fb.y1) > reach) continue;
    const { F, ranks, rankD } = shape(u, p, b.menPerDot), r = Math.max(F / 2, ranks * rankD);
    bx = grow(bx, p.x - r, p.y - r, p.x + r, p.y + r);
  }
  return bx && { x0: bx.x0 - pad, y0: bx.y0 - pad, x1: bx.x1 + pad, y1: bx.y1 + pad };
}

// An armor unit's strength counts vehicles, not men: a dot for each vehicle and a casualty marker for each one lost.
export const perDot = (u, mpd) => (u.type === 'armor' ? 1 : mpd);

// Formation footprint: dot count, ranks, frontage (m), rank depth (m). Files are ~0.7 m for foot, 1 m for horse;
// tanks keep about 50 m apart in line and 30 m nose to tail on a road.
export function shape(u, pose, mpd) {
  mpd = perDot(u, mpd);
  const men = Math.max(0, pose.strength), nd = Math.max(1, Math.ceil(men / mpd)), s = pose.state;
  if (u.type === 'artillery') return { nd, ranks: 2, F: (u.guns ?? 1) * 14, rankD: 4 };
  if (u.type === 'armor') {
    if (s === 'column') return { nd, ranks: nd, F: 4, rankD: 30 };
    if (s === 'rout') return { nd, ranks: Math.ceil(nd / 3), F: nd * 40, rankD: 40 };
    return { nd, ranks: 1, F: Math.max(10, nd * 50), rankD: 30 };
  }
  if (s === 'column') return { nd, ranks: Math.ceil(nd / 4), F: 8, rankD: Math.max(1.5, mpd * 0.5) };
  if (s === 'rout') return { nd, ranks: Math.ceil(nd / 6), F: Math.max(10, men * 0.25), rankD: 6 };
  if (s === 'skirmish') return { nd, ranks: 1, F: Math.max(10, men * 2.5), rankD: 3 };
  if (u.loose) return { nd, ranks: 1, F: Math.max(10, men * 1.5), rankD: 3 }; // open order, as backwoods riflemen fought
  const cav = u.type === 'cavalry', r = u.ranks ?? 2;
  return { nd, ranks: r, F: Math.max(4, (men / r) * (cav ? 1.0 : 0.7)), rankD: cav ? 3 : 2 };
}

// Dot positions [x0,y0,x1,y1,...] in world metres. Pose is the centre of the front rank; jitter is stable per unit.
export function dots(u, pose, mpd, out = []) {
  const { nd, ranks, F, rankD } = shape(u, pose, mpd);
  const perFile = Math.ceil(nd / ranks), sp = F / perFile;
  const rad = (pose.h * Math.PI) / 180, dx = Math.sin(rad), dy = Math.cos(rad);
  const open = pose.state !== 'column' && (u.loose ? 3 : u.type === 'armor' ? 6 : 0);
  const jit = open || ({ rout: 8, skirmish: 2, charge: 1, retreat: 0.8 }[pose.state] ?? 0.3);
  const rnd = mulberry32(hash(u.id));
  for (let i = 0; i < nd; i++) {
    const uu = ((i % perFile) - (perFile - 1) / 2) * sp + (rnd() - 0.5) * 2 * jit;
    const vv = -Math.floor(i / perFile) * rankD + (rnd() - 0.5) * 2 * jit;
    out.push(pose.x + uu * dy + vv * dx, pose.y - uu * dx + vv * dy);
  }
  return out;
}

// Casualty markers for the whole battle, sorted by time: one per menPerDot men (or per vehicle) lost between keys.
export function fallenMarkers(b) {
  const out = [], mpd = b.menPerDot;
  for (const u of b.units) {
    const rnd = mulberry32(hash(u.id) ^ 0x9e3779b9);
    for (let i = 0; i + 1 < u.keys.length; i++) {
      const a = u.keys[i], c = u.keys[i + 1];
      const m = perDot(u, mpd), n = Math.floor(a.strength / m) - Math.floor(c.strength / m);
      for (let j = 0; j < n; j++) {
        const t = a.t + rnd() * Math.max(1, c.t - a.t);
        const p = unitAt(u, t);
        if (!p) continue;
        const { F } = shape(u, p, mpd);
        const rad = (p.h * Math.PI) / 180, dx = Math.sin(rad), dy = Math.cos(rad);
        const uu = (rnd() - 0.5) * F, vv = 3 - rnd() * 8;
        out.push({ t, x: p.x + uu * dy + vv * dx, y: p.y - uu * dx + vv * dy, side: u.side });
      }
    }
  }
  out.push(...dropFallen(b));
  return out.sort((p, q) => p.t - q.t);
}

function dropFallen(b) {
  const out = [];
  for (const f of b.features ?? []) {
    const P = PLANS.get(f), m = P?.men;
    if (m) for (const g of P.groups) for (let i = g.i0; i < g.i1; i++) {
      const o = i * MAN.stride;
      if (m[o + MAN.lost]) out.push({ t: m[o + MAN.downAt], x: m[o + MAN.landX], y: m[o + MAN.landY], side: g.side });
    }
  }
  return out;
}

// A drop is cosmetic: its units' keys alone say where and when each one has formed (docs/adr/0011-airborne-drops.md).
const CANOPY_FALL_S = 90;
const GLIDER_APPROACH_M = 1500, GLIDER_APPROACH_MAX_S = 900;
const GLIDER_ROLL_M = 80, GLIDER_ROLL_S = 15;
const GLIDER_STOP_TO_EXIT_S = 30;
const GATHER_MIN_S = 90, GATHER_MAX_S = 240;
const WALK_M_PER_S = 1.2;
const DRIFT_DOWNWIND_M = 150, THROW_ALONG_TRACK_M = 60;
const STICK_LENGTH_M = 600;
const STREAM = { mPerRealS: 300, spacingM: 800, pastEdgeM: 600, reachM: 5000 };
const MAN = Object.freeze({ landX: 0, landY: 1, releaseX: 2, releaseY: 3, placeX: 4, placeY: 5, downAt: 6, setOffAt: 7, arriveAt: 8, formedAt: 9, lost: 10, stride: 11 });
const GLIDER = Object.freeze({ approachX: 0, approachY: 1, touchX: 2, touchY: 3, stopX: 4, stopY: 5, touchAt: 6, heading: 7, stride: 8 });
const PLANS = new WeakMap();

const inZone = (z, x, y) => {
  let c = false;
  for (let i = 0, j = z.length - 1; i < z.length; j = i++) { const [xi, yi] = z[i], [xj, yj] = z[j]; if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c; }
  return c;
};
const smooth01 = x => x * x * (3 - 2 * x);
const arrival = (setOffAt, formedAt, walkM, r) =>
  Math.max(setOffAt + 1, Math.min(formedAt, setOffAt + Math.max(walkM / WALK_M_PER_S, (formedAt - setOffAt) * (0.4 + 0.6 * r))));

function planAir(b) {
  const byId = new Map(b.units.map(u => [u.id, u])), taken = new Map(), half = b.extent / 2;
  for (const f of b.features ?? []) {
    if (f.type === 'airstrike') f.air = [f.from, f.until];
    if (f.type !== 'drop') continue;
    const name = f.name ?? '', P = { problems: [] }, z = f.zone, para = f.kind === 'para', bad = s => P.problems.push(`drop ${name}${s}`);
    PLANS.set(f, P);
    if (!(z?.length >= 3)) bad(' needs a zone of three or more corners');
    else if (b.extent != null) for (const [x, y] of z) if (Math.abs(x) > half || Math.abs(y) > half) bad(`: zone corner off map (${x}, ${y})`);
    if (!para && f.kind !== 'glider') bad(': kind must be para or glider');
    if (!(f.from < f.until)) bad(' needs from before until');
    if (!(f.craft >= 1)) bad(' needs craft');
    if (P.problems.length) continue;

    const groups = [];
    for (const id of f.units ?? []) {
      const u = byId.get(id);
      if (!u) { bad(`: no unit ${id}`); continue; }
      if (taken.has(id)) { bad(`: ${id} is already in drop ${taken.get(id)}`); continue; }
      taken.set(id, name);
      const k = u.keys, at = k.findLastIndex(q => q.t <= f.from), ri = k.findIndex(q => q.t > f.from && q.state !== 'hidden');
      if (at >= 0 && k[at].state !== 'hidden') { bad(`: ${id} is on the map when the drop starts`); continue; }
      if (ri < 0) { bad(`: ${id} never forms up`); continue; }
      if (k[ri].t < f.until) { bad(`: ${id} forms up at ${fmtTime(k[ri].t)}, before the last of the drop is down at ${fmtTime(f.until)}`); continue; }
      const pose = unitAt(u, k[ri].t), m = perDot(u, b.menPerDot), dot = dots(u, pose, b.menPerDot);
      const lost = Math.max(0, Math.floor((ri ? k[ri - 1].strength : u.strength) / m) - Math.floor(pose.strength / m));
      groups.push({ side: u.side, tu: k[ri].t, dot, lost, n: dot.length / 2 + lost, i0: 0, i1: 0 });
    }

    const h = ((f.h ?? 0) * Math.PI) / 180, alongX = Math.sin(h), alongY = Math.cos(h), acrossX = alongY, acrossY = -alongX;
    const ox = z.reduce((s, p) => s + p[0], 0) / z.length, oy = z.reduce((s, p) => s + p[1], 0) / z.length;
    let aLo = Infinity, aHi = -Infinity, cLo = Infinity, cHi = -Infinity, x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    for (const [x, y] of z) {
      const a = (x - ox) * alongX + (y - oy) * alongY, c = (x - ox) * acrossX + (y - oy) * acrossY;
      aLo = Math.min(aLo, a); aHi = Math.max(aHi, a); cLo = Math.min(cLo, c); cHi = Math.max(cHi, c);
      x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y);
    }
    const rnd = mulberry32(hash(`${name}|${f.from}`)), wl = Math.hypot(b.wind?.x ?? 0, b.wind?.y ?? 0), wx = wl && b.wind.x / wl, wy = wl && b.wind.y / wl;
    const pointInZone = propose => {
      for (let i = 0; i < 64; i++) { const p = i < 32 ? propose() : [x0 + rnd() * (x1 - x0), y0 + rnd() * (y1 - y0)]; if (inZone(z, p[0], p[1])) return p; }
      return [ox, oy];
    };
    const edge = s => { let d = Infinity; for (const [o, u] of [[ox, alongX * s], [oy, alongY * s]]) if (u) d = Math.min(d, ((u > 0 ? half : -half) - o) / u); return Math.min(d + STREAM.pastEdgeM, STREAM.reachM); };
    const back = edge(-1), track = back + edge(1), vics = Math.ceil(track / STREAM.spacingM);
    const nl = Math.max(1, Math.min(f.craft, Math.round((cHi - cLo) / 120))), lanes = Float64Array.from({ length: nl }, (_, i) => 0.8 * (cLo + ((cHi - cLo) * (i + 0.5)) / nl));
    const K = para ? 0 : f.craft, gl = new Float64Array(K * GLIDER.stride);
    for (let g = 0; g < K; g++) {
      const tk = f.from + ((g + rnd()) / K) * (f.until - f.from), [lx, ly] = pointInZone(() => [x0 + rnd() * (x1 - x0), y0 + rnd() * (y1 - y0)]);
      const gh = h + (rnd() - 0.5) * 0.7, gx = Math.sin(gh), gy = Math.cos(gh), side = (rnd() - 0.5) * 200, o = g * GLIDER.stride;
      gl[o + GLIDER.approachX] = lx - gx * GLIDER_APPROACH_M + acrossX * side; gl[o + GLIDER.approachY] = ly - gy * GLIDER_APPROACH_M + acrossY * side;
      gl[o + GLIDER.touchX] = lx; gl[o + GLIDER.touchY] = ly;
      gl[o + GLIDER.stopX] = lx + gx * GLIDER_ROLL_M; gl[o + GLIDER.stopY] = ly + gy * GLIDER_ROLL_M;
      gl[o + GLIDER.touchAt] = tk; gl[o + GLIDER.heading] = (gh * 180) / Math.PI;
    }
    const len = Math.min(STICK_LENGTH_M, aHi - aLo), sticks = Float64Array.from({ length: para ? f.craft : 0 }, () => aLo + rnd() * (aHi - aLo - len));
    const N = groups.reduce((s, g) => s + g.n, 0), men = new Float64Array(N * MAN.stride);
    let s = 0;
    for (const g of groups) {
      g.i0 = s;
      for (let j = 0, d = 0; j < g.n; j++, s++) {
        const slot = (s + rnd()) / N, lost = Math.floor(((j + 1) * g.lost) / g.n) > Math.floor((j * g.lost) / g.n);
        let lx, ly, rx, ry, tl;
        if (para) {
          const k = slot * f.craft, st = Math.floor(k), lane = lanes[st % nl] + (rnd() - 0.5) * 50, a0 = sticks[st] + (k - st) * len + (rnd() - 0.5) * 40;
          let tries = 0;
          [lx, ly] = pointInZone(() => { const a = tries++ ? aLo + rnd() * (aHi - aLo) : a0; return [ox + alongX * a + acrossX * lane, oy + alongY * a + acrossY * lane]; });
          tl = f.from + slot * (f.until - f.from);
          rx = lx - wx * DRIFT_DOWNWIND_M - alongX * THROW_ALONG_TRACK_M; ry = ly - wy * DRIFT_DOWNWIND_M - alongY * THROW_ALONG_TRACK_M;
        } else {
          const o = Math.floor(slot * K) * GLIDER.stride;
          lx = rx = gl[o + GLIDER.stopX] + (rnd() - 0.5) * 30; ly = ry = gl[o + GLIDER.stopY] + (rnd() - 0.5) * 30;
          tl = gl[o + GLIDER.touchAt] + GLIDER_ROLL_S + GLIDER_STOP_TO_EXIT_S + rnd() * 60;
        }
        const dx = lost ? lx : g.dot[2 * d], dy = lost ? ly : g.dot[2 * d + 1];
        if (!lost) d++;
        const tg = Math.max(tl, Math.min(tl + GATHER_MIN_S + rnd() * (GATHER_MAX_S - GATHER_MIN_S), (tl + g.tu) / 2));
        const ta = arrival(tg, g.tu, Math.hypot(dx - lx, dy - ly), rnd()), o = s * MAN.stride;
        men[o + MAN.landX] = lx; men[o + MAN.landY] = ly; men[o + MAN.releaseX] = rx; men[o + MAN.releaseY] = ry;
        men[o + MAN.placeX] = dx; men[o + MAN.placeY] = dy;
        men[o + MAN.downAt] = tl; men[o + MAN.setOffAt] = tg; men[o + MAN.arriveAt] = ta; men[o + MAN.formedAt] = g.tu; men[o + MAN.lost] = +lost;
      }
      g.i1 = s;
    }
    // Transports still on their pass when the last man is down fly it out, at the speed the chapter then plays.
    const formed = Math.max(f.until, ...groups.map(g => g.tu)), end = Math.max(formed, f.until + (track / STREAM.mPerRealS) * (eventAt(b, f.until)?.speed ?? defaultSpeed(b)));
    Object.assign(P, { para, until: f.until, t0: f.from - (para ? CANOPY_FALL_S : GLIDER_APPROACH_MAX_S), formed, end, ox, oy, alongX, alongY, acrossX, acrossY, h: f.h ?? 0,
      back, track, vics, lanes, nl, gl, k: K, men, groups,
      out: { kind: f.kind, craft: new Float32Array(vics * 3), nCraft: 0, canopies: new Float32Array(N * 3), nCanopy: 0, chutes: new Float32Array(N * 2), nChute: 0,
        gliders: new Float32Array(K * 4), nGlider: 0, men: new Float32Array(N * 2), nMen: 0 } });
    f.air = [P.t0, end];
  }
}

/**
 * Drop `f` at battle time t, in world metres, or null outside f.air. Everything on or over the ground is pure in t; only
 * the transports fly on `clock` (real seconds of play), as an air strike's aircraft do. A glider flies its final approach at
 * the transports' pace on screen, so at `rate` battle seconds a real second it takes that many more battle seconds, up to
 * GLIDER_APPROACH_MAX_S. Writes into the plan's own frame and returns it: read it before the next call for the same drop.
 * @typedef {{ kind: 'para'|'glider',
 *   craft: Float32Array, nCraft: number,       // [x, y, h] the lead aircraft of each vic, until the last are out of sight
 *   canopies: Float32Array, nCanopy: number,   // [x, y, alt] a canopy in the air for each dot's men, alt 1 at release, 0 down
 *   chutes: Float32Array, nChute: number,      // [x, y] a canopy on the ground where its men came down
 *   gliders: Float32Array, nGlider: number,    // [x, y, h, alt] a glider on its final approach (alt > 0), rolling out or standing
 *   men: Float32Array, nMen: number }} DropFrame // [x, y] a dot's men on the ground, from where they came down to their place
 * @returns {DropFrame | null}
 */
export function dropAt(f, t, clock, rate) {
  const P = PLANS.get(f);
  if (!P?.out || t < P.t0 || t >= P.end) return null;
  const D = P.out, m = P.men, gl = P.gl, pace = STREAM.mPerRealS, since = t > P.until ? (t - P.until) / rate : 0;
  D.nCraft = D.nCanopy = D.nChute = D.nGlider = D.nMen = 0;
  for (let v = 0; v < P.vics; v++) {
    const s = (clock * pace + (v * P.track) / P.vics) % P.track;
    if (since && s / pace <= since) continue;
    const d = s - P.back, c = P.lanes[Math.floor(((v + 0.5) / P.vics) * P.nl)], w = D.nCraft++ * 3;
    D.craft[w] = P.ox + P.alongX * d + P.acrossX * c; D.craft[w + 1] = P.oy + P.alongY * d + P.acrossY * c; D.craft[w + 2] = P.h;
  }
  if (t >= P.formed) return D;
  const glide = Math.min(GLIDER_APPROACH_MAX_S, (GLIDER_APPROACH_M / pace) * rate);
  for (let g = 0; g < P.k; g++) {
    const o = g * GLIDER.stride, tk = gl[o + GLIDER.touchAt];
    if (t < tk - glide) continue;
    const alt = t < tk ? (tk - t) / glide : 0, e = t < tk ? 0 : Math.min(1, (t - tk) / GLIDER_ROLL_S), w = D.nGlider++ * 4;
    const tx = gl[o + GLIDER.touchX], ty = gl[o + GLIDER.touchY];
    D.gliders[w] = alt ? tx + (gl[o + GLIDER.approachX] - tx) * alt : tx + (gl[o + GLIDER.stopX] - tx) * e;
    D.gliders[w + 1] = alt ? ty + (gl[o + GLIDER.approachY] - ty) * alt : ty + (gl[o + GLIDER.stopY] - ty) * e;
    D.gliders[w + 2] = gl[o + GLIDER.heading]; D.gliders[w + 3] = alt;
  }
  for (let gi = 0; gi < P.groups.length; gi++) {
    const g = P.groups[gi];
    if (!P.para && t >= g.tu) continue;
    for (let i = g.i0; i < g.i1; i++) {
      const o = i * MAN.stride, tl = m[o + MAN.downAt], lx = m[o + MAN.landX], ly = m[o + MAN.landY];
      if (P.para) {
        if (t < tl - CANOPY_FALL_S) continue;
        if (t < tl) {
          const alt = (tl - t) / CANOPY_FALL_S, w = D.nCanopy++ * 3;
          D.canopies[w] = lx + (m[o + MAN.releaseX] - lx) * alt; D.canopies[w + 1] = ly + (m[o + MAN.releaseY] - ly) * alt; D.canopies[w + 2] = alt;
          continue;
        }
        const w = D.nChute++ * 2;
        D.chutes[w] = lx; D.chutes[w + 1] = ly;
      } else if (t < tl) continue;
      if (m[o + MAN.lost] || t >= m[o + MAN.formedAt]) continue;
      const tg = m[o + MAN.setOffAt], ta = m[o + MAN.arriveAt], e = t <= tg ? 0 : t >= ta ? 1 : smooth01((t - tg) / (ta - tg)), w = D.nMen++ * 2;
      D.men[w] = lx + (m[o + MAN.placeX] - lx) * e; D.men[w + 1] = ly + (m[o + MAN.placeY] - ly) * e;
    }
  }
  return D;
}

// Where a unit went, as runs of [t, x, y] vertices: positions are straight lines between keys, so the keys are the
// whole path. A hidden key ends a run where the unit was last seen; the next visible key starts another.
export function tracks(u) {
  const runs = [];
  let run = null;
  u.keys.forEach((k, i) => {
    const prev = u.keys[i - 1], seen = k.state !== 'hidden' || (prev && prev.state !== 'hidden');
    if (!seen) return;
    (run ??= runs[runs.push([]) - 1]).push(k.t, k.x, k.y);
    if (k.state === 'hidden') run = null;
  });
  return runs;
}

export function eventAt(b, t) {
  let e = null;
  for (const ev of b.events) { if (ev.t <= t) e = ev; else break; }
  return e;
}

// Data problems as strings; empty means valid. Call after normalizeBattle.
export function validate(b, terrain) {
  const p = [];
  for (const k of ['id', 'name', 'date', 'place', 'origin', 'extent', 'start', 'end', 'sides', 'units']) if (b[k] == null) p.push(`missing ${k}`);
  if (p.length) return p;
  const half = b.extent / 2, inMap = (x, y) => Math.abs(x) <= half && Math.abs(y) <= half;
  const ids = new Set();
  for (const u of b.units) {
    if (ids.has(u.id)) p.push(`duplicate unit id ${u.id}`);
    ids.add(u.id);
    if (!b.sides[u.side]) p.push(`${u.id}: unknown side ${u.side}`);
    if (!TYPES.includes(u.type)) p.push(`${u.id}: bad type ${u.type}`);
    if (!u.keys.length) p.push(`${u.id}: no keys`);
    for (const k of u.keys) {
      if (!STATES.includes(k.state)) p.push(`${u.id}@${fmtTime(k.t)}: bad state ${k.state}`);
      if (k.t < b.startT || k.t > b.endT) p.push(`${u.id}@${fmtTime(k.t)}: outside battle clock`);
      if (k.state !== 'hidden' && !inMap(k.x, k.y)) p.push(`${u.id}@${fmtTime(k.t)}: off map (${k.x}, ${k.y})`);
    }
  }
  for (const f of [...(b.features ?? []), ...(b.tints ?? [])]) {
    for (const key of ['from', 'until']) {
      if (f[key] != null && (f[key] < b.startT || f[key] > b.endT)) p.push(`feature ${f.name ?? f.type ?? f.color}: ${key} outside battle clock`);
    }
    if (f.type === 'smoke' && !(f.at && f.rate > 0)) p.push(`smoke feature ${f.name ?? ''} needs at and rate`);
    if (f.type === 'airstrike' && !(f.at && f.from != null && f.until != null)) p.push(`airstrike ${f.name ?? ''} needs at, from and until`);
    if (f.type === 'drop') p.push(...(PLANS.get(f)?.problems ?? []));
  }
  for (const e of b.events) {
    if (e.t < b.startT || e.t > b.endT) p.push(`event "${e.title}": outside battle clock`);
    if (e.at && !inMap(e.at[0], e.at[1])) p.push(`event "${e.title}": focus off map`);
  }
  if (terrain) {
    if (terrain.z.length !== terrain.cols * terrain.rows) p.push('terrain: z length does not match cols*rows');
    if (Math.abs(terrain.cols * terrain.spacing - b.extent) > 1) p.push(`terrain: covers ${terrain.cols * terrain.spacing} m but battle extent is ${b.extent} m`);
  }
  return p;
}
