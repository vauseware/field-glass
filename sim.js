// Battle replay logic with no DOM dependencies. Shared by app.js and tools/check.mjs.

export const SPEEDS = [1, 2, 5, 10, 20, 30, 60, 120, 300, 600, 1800, 3600, 7200];
export const STATES = ['hidden', 'column', 'line', 'skirmish', 'firing', 'charge', 'retreat', 'rout', 'surrender'];
export const TYPES = ['infantry', 'light_infantry', 'militia', 'riflemen', 'cavalry', 'artillery'];
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
const MONTHS = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split(' ');
export function fmtTime(t) {
  const h = mod(Math.floor(t / 3600), 24), m = mod(Math.floor(t / 60), 60);
  const clock = `${h % 12 || 12}:${String(m).padStart(2, '0')} ${h < 12 ? 'AM' : 'PM'}`;
  if (Math.abs(t) < 366 * 86400) return clock;
  const d = new Date(t * 1000);
  return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]}, ${clock}`;
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
  }
  b.events = (b.events ?? []).map(e => ({ ...e, t: parseTime(e.t) })).sort((p, q) => p.t - q.t);
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

// Pose of a unit at battle time t, or null while hidden. State is a step function of the previous key.
export function unitAt(u, t) {
  const k = u.keys;
  if (!k.length || t < k[0].t) return null;
  let i = k.length - 1;
  while (i > 0 && k[i].t > t) i--;
  const a = k[i], c = k[i + 1];
  if (a.state === 'hidden') return null;
  if (!c || c.t <= a.t) return { x: a.x, y: a.y, h: a.h, strength: a.strength, state: a.state, fire: a.fire };
  const f = (t - a.t) / (c.t - a.t);
  return { x: lerp(a.x, c.x, f), y: lerp(a.y, c.y, f), h: lerpAngle(a.h, c.h, f), strength: lerp(a.strength, c.strength, f), state: a.state, fire: a.fire };
}

// Formation footprint: dot count, ranks, frontage (m), rank depth (m). Files are ~0.7 m for foot, 1 m for horse.
export function shape(u, pose, mpd) {
  const men = Math.max(0, pose.strength), nd = Math.max(1, Math.ceil(men / mpd)), s = pose.state;
  if (u.type === 'artillery') return { nd, ranks: 2, F: (u.guns ?? 1) * 14, rankD: 4 };
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
  const jit = u.loose && pose.state !== 'column' ? 3 : { rout: 8, skirmish: 2, charge: 1, retreat: 0.8 }[pose.state] ?? 0.3;
  const rnd = mulberry32(hash(u.id));
  for (let i = 0; i < nd; i++) {
    const uu = ((i % perFile) - (perFile - 1) / 2) * sp + (rnd() - 0.5) * 2 * jit;
    const vv = -Math.floor(i / perFile) * rankD + (rnd() - 0.5) * 2 * jit;
    out.push(pose.x + uu * dy + vv * dx, pose.y - uu * dx + vv * dy);
  }
  return out;
}

// Casualty markers for the whole battle, sorted by time: one per menPerDot men lost between keys.
export function fallenMarkers(b) {
  const out = [], mpd = b.menPerDot;
  for (const u of b.units) {
    const rnd = mulberry32(hash(u.id) ^ 0x9e3779b9);
    for (let i = 0; i + 1 < u.keys.length; i++) {
      const a = u.keys[i], c = u.keys[i + 1];
      const n = Math.floor(a.strength / mpd) - Math.floor(c.strength / mpd);
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
  return out.sort((p, q) => p.t - q.t);
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
