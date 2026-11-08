// Self-check for sim.js plus validation of every battle in battles/index.json. Run: npm run check
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import assert from 'node:assert/strict';
import { normalizeBattle, validate, unitAt, lerpAngle, dots, parseTime, fmtTime, activity, playTime, actionBox, tracks, shape, dropAt } from '../sim.js';
import { WARS } from '../splash.js';

const u = { id: 'x', side: 'a', type: 'infantry', strength: 100, keys: [
  { t: '07:00', x: 0, y: 0, h: 350 },
  { t: '07:10', x: 100, y: 0, h: 10, strength: 50, state: 'firing' },
  { t: '07:20', state: 'hidden' },
] };
const b = normalizeBattle({ start: '07:00', end: '08:00', menPerDot: 10, units: [u] });
const mid = unitAt(u, parseTime('07:05'));
assert.equal(unitAt(u, parseTime('06:59')), null, 'hidden before first key');
assert.deepEqual([mid.x, mid.h, mid.strength, mid.state], [50, 10, 75, 'line'], 'midpoint interpolation; the turn is done');
assert.equal(unitAt(u, parseTime('07:00:25')).h, 0, 'half way through the 50 s turn, through north');
assert.equal(unitAt(u, parseTime('07:10')).state, 'firing');
assert.equal(unitAt(u, parseTime('07:15')).fire, 1);
assert.equal(unitAt(u, parseTime('07:21')), null, 'hidden after hidden key');
assert.equal(dots(u, unitAt(u, parseTime('07:00')), 10).length, 20, 'ten dots');
assert.equal(b.fallen.length, 5, 'one marker per 10 men lost');
assert.deepEqual(tracks(u), [[parseTime('07:00'), 0, 0, parseTime('07:10'), 100, 0, parseTime('07:20'), 100, 0]], 'track ends where the unit was last seen');
assert.deepEqual(tracks({ keys: [{ t: 1, x: 0, y: 0, state: 'hidden' }, { t: 2, x: 5, y: 0, state: 'line' }, { t: 3, x: 9, y: 0, state: 'hidden' }, { t: 4, x: 1, y: 1, state: 'hidden' }, { t: 5, x: 2, y: 2, state: 'line' }] }),
  [[2, 5, 0, 3, 9, 0], [5, 2, 2]], 'a hidden spell splits the track');
assert.equal(lerpAngle(350, 10, 0.5), 0, 'heading wraps through north');
assert.equal(parseTime('1781-10-14T20:00') - parseTime('1781-10-13 20:00'), 86400, 'dated times');
assert.equal(fmtTime(parseTime('1781-10-14 20:05')), '14 Oct, 8:05 PM', 'dated clock');
assert.deepEqual(activity(b, parseTime('07:05')), [true, parseTime('07:20')], 'moving then firing is one active span');
assert.deepEqual(activity(b, parseTime('06:50')), [false, parseTime('06:58:30')], 'quiet until 90 s before the move');
assert.deepEqual(activity(b, parseTime('07:30')), [false, Infinity], 'quiet after the last key');
const cb = normalizeBattle({ start: '07:00', end: '08:00', extent: 2000, menPerDot: 10, units: [
  { id: 'm', type: 'infantry', strength: 100, keys: [{ t: '07:00', x: 300, y: 0, state: 'column' }, { t: '07:10', x: 600, y: 0 }] },
  { id: 'idle', type: 'infantry', strength: 100, keys: [{ t: '07:00', x: -900, y: 0 }, { t: '08:00', x: -900, y: 0 }] },
  { id: 'stand', type: 'infantry', strength: 100, keys: [{ t: '07:00', x: -900, y: 500, h: 120, state: 'firing' }, { t: '07:13', h: 290, state: 'retreat' }] },
], events: [{ t: '07:00', at: [0, 0], view: 400 }, { t: '07:10', at: [600, 0], view: 400 }] });
const stand = cb.units[2];
assert.equal(unitAt(stand, parseTime('07:12')).h, 120, 'a standing line keeps facing the enemy until it turns to go');
assert.equal(unitAt(stand, parseTime('07:12:35')).h, 205, 'and turns in the last 50 s before the key');
const box = (t, ahead) => actionBox(cb, parseTime(t), ahead, 0);
assert.equal(box('07:01', 0).x0, -200, 'chapter focus framed; idle unit left out');
assert.ok(box('07:01', 0).x1 >= 330 && box('07:01', 120).x1 >= 390, 'marching unit framed now and where it will be');
const [pre, at] = [actionBox(cb, parseTime('07:10') - 0.01, 60, 0), box('07:10', 60)];
assert.ok(['x0', 'y0', 'x1', 'y1'].every(k => Math.abs(pre[k] - at[k]) < 1), 'no jump at the chapter boundary');
const tanks = { id: 't', side: 'a', type: 'armor', strength: 17, keys: [{ t: '07:00', x: 0, y: 0, state: 'column' }, { t: '07:10', state: 'line' }, { t: '07:20', strength: 12 }] };
const tb = normalizeBattle({ start: '07:00', end: '08:00', menPerDot: 20, units: [tanks] });
assert.equal(dots(tanks, unitAt(tanks, parseTime('07:10')), 20).length, 34, 'armor: a dot per tank whatever menPerDot is');
assert.deepEqual([shape(tanks, unitAt(tanks, parseTime('07:00')), 20).F, shape(tanks, unitAt(tanks, parseTime('07:10')), 20).F], [4, 850], 'armor: one tank wide in column, 50 m a tank in line');
assert.equal(tb.fallen.length, 5, 'armor: a marker per tank lost');
assert.deepEqual(validate(normalizeBattle({ id: 'v', name: 'v', date: 'd', place: 'p', origin: {}, extent: 1000, start: '07:00', end: '08:00', sides: {}, units: [],
  features: [{ type: 'airstrike', name: 'Stukas', at: [0, 0], from: '07:10' }] })), ['airstrike Stukas needs at, from and until'], 'an air strike needs its times');
assert.deepEqual(normalizeBattle({ start: '07:00', end: '08:00', units: [], features: [{ type: 'airstrike', at: [0, 0], from: '07:10', until: '07:20' }] }).features[0].air,
  [parseTime('07:10'), parseTime('07:20')], 'the air hook flies an air strike from its from to its until');

const T = parseTime, ZONE_RADIUS = 400, para = (keys = [{ t: '13:00', x: 0, y: 0, state: 'hidden' }, { t: '14:00', x: 200, y: 0, h: 90, strength: 80, state: 'line' }]) =>
  ({ id: 'para', side: 'a', type: 'infantry', strength: 100, keys });
const dropBattle = (drop = {}, units = [para()], more = []) => normalizeBattle({ id: 'd', name: 'd', date: '1944-09-17', place: 'p', origin: {}, extent: 4000,
  start: '13:00', end: '15:00', menPerDot: 10, wind: { x: 1, y: 0 }, sides: { a: {} }, units,
  features: [{ type: 'drop', kind: 'para', name: 'test', zone: [[0, -ZONE_RADIUS], [ZONE_RADIUS, 0], [0, ZONE_RADIUS], [-ZONE_RADIUS, 0]], h: 90, from: '13:30', until: '13:40', craft: 10, units: ['para'], ...drop }, ...more] });
const db = dropBattle(), df = db.features[0], pu = db.units[0];
const ground = (t, clock) => { const D = dropAt(df, T(t), clock); return [...D.canopies.slice(0, D.nCanopy * 3), ...D.chutes.slice(0, D.nChute * 2), ...D.men.slice(0, D.nMen * 2)]; };
const toDots = (D, dd) => D.men.slice(0, D.nMen * 2).reduce((s, v, i) => s + Math.abs(v - dd[i]), 0);
const formedDots = dots(pu, unitAt(pu, T('14:00')), 10);
assert.deepEqual(validate(db), [], 'a well-formed drop');
assert.equal(dropAt(df, T('13:28'), 0), null, 'nothing before the first canopy');
assert.ok(dropAt(df, T('13:35'), 0).nCanopy > 0 && dropAt(df, T('13:35'), 0).nCraft > 0, 'canopies and transports over the zone mid-drop');
assert.deepEqual(ground('13:38', 3), ground('13:38', 7), 'canopies, chutes and men are pure in battle time');
assert.notDeepEqual([...dropAt(df, T('13:38'), 3).craft], [...dropAt(df, T('13:38'), 7).craft], 'only the transports fly on the clock');
const down = dropAt(df, T('13:50'), 0);
assert.ok(down.nChute === 10 && [...down.chutes.slice(0, 20)].every((v, i, a) => i % 2 || Math.abs(v) + Math.abs(a[i + 1]) <= ZONE_RADIUS), 'all ten dots of men come down inside the zone');
assert.equal(down.nMen, 8, 'eight dots of men walk in: 80 of the 100 formed, two dots were lost on the drop');
assert.ok(toDots(dropAt(df, T('13:42'), 0), formedDots) > toDots(dropAt(df, T('13:52'), 0), formedDots), 'the men close on their places in the unit');
assert.ok(toDots(dropAt(df, T('14:00') - 0.01, 0), formedDots) < 8 * 2, 'each man is at his own dot as the unit forms');
const rallied = dropAt(df, T('14:00'), 0, 60);
assert.ok(!rallied?.nMen && !rallied?.nChute && !rallied?.nCanopy && unitAt(pu, T('14:00') - 0.01) === null && unitAt(pu, T('14:00')), 'the unit takes over from its men at the rally key');
assert.ok(db.fallen.length === 2 && db.fallen.every(m => Math.abs(m.x) + Math.abs(m.y) <= ZONE_RADIUS && m.t >= T('13:30') && m.t <= T('13:40')), 'a fallen marker where and when each lost dot came down');
assert.deepEqual(df.air, [T('13:30') - 90, T('14:00')], 'the air hook draws from the first canopy until the unit has formed and the transports have flown out');
assert.equal(activity(db, T('13:50'))[0], true, 'the rally is active: time-lapse waits for it');
const offMap = (x, y) => Math.max(Math.abs(x), Math.abs(y)) > db.extent / 2;
for (let c = 0, prev = null; c < 60; c += 0.05) {
  const D = dropAt(df, T('13:35'), c, 60), cur = [...D.craft.slice(0, D.nCraft * 3)];
  for (let v = 0; prev && v < D.nCraft; v++) {
    const [x0, y0, x1, y1] = [prev[3 * v], prev[3 * v + 1], cur[3 * v], cur[3 * v + 1]];
    assert.ok(Math.hypot(x1 - x0, y1 - y0) < 100 || (offMap(x0, y0) && offMap(x1, y1)), `a transport leaves the map before it starts its next pass, not at (${x0.toFixed(0)}, ${y0.toFixed(0)})`);
  }
  prev = cur;
}
assert.ok(dropAt(df, T('13:40') + 30, 0, 60).nCraft > 0, 'transports already on their pass fly on after the last man is down');
assert.equal(dropAt(df, T('13:59'), 0, 60).nCraft, 0, 'and no transport starts a new pass');
const gf = dropBattle({ kind: 'glider', craft: 4 }).features[0], count = (t, k) => dropAt(gf, T(t), 0, 60)[k];
assert.ok(count('13:35', 'nGlider') > 0 && count('13:50', 'nGlider') === 4 && count('13:50', 'nMen') === 8 && count('13:50', 'nCanopy') === 0, 'gliders come down and their men get out');
assert.equal(dropAt(gf, T('13:59'), 0, 60).nGlider, 4, 'the gliders stand until the unit has formed');
const flying = D => [[...D.craft.slice(0, D.nCraft * 3)].filter((_, i) => i % 3 < 2), [...D.gliders.slice(0, D.nGlider * 4)].filter((_, i, a) => i % 4 < 2 && a[i - (i % 4) + 3] > 0)];
const drift = (a, b) => { const d = []; for (let i = 0; i < a.length; i += 2) { let m = Infinity; for (let j = 0; j < b.length; j += 2) m = Math.min(m, Math.hypot(a[i] - b[j], a[i + 1] - b[j + 1])); d.push(m); } return d.sort((p, q) => p - q)[d.length >> 1]; };
for (const rate of [10, 60]) {
  let t = T('13:30');
  while (t < T('13:40') && !flying(dropAt(gf, t, 0, rate))[1].length) t += 5;
  const dt = 0.05, [ca, ga] = flying(dropAt(gf, t, 0, rate)), [cb, gb] = flying(dropAt(gf, t + rate * dt, dt, rate)), pace = drift(ga, gb) / drift(ca, cb);
  assert.ok(ga.length && pace > 0.75 && pace < 1.25, `a landing glider crosses the map at the transports' pace at ${rate}x, not ${pace.toFixed(2)} times it`);
}
const problems = (drop, units, more) => validate(dropBattle(drop, units, more));
assert.deepEqual(problems({ units: ['para', 'nobody'] }), ['drop test: no unit nobody'], 'a drop names units that exist');
assert.deepEqual(problems({}, [para()], [{ type: 'drop', kind: 'para', name: 'again', zone: [[0, 0], [100, 0], [0, 100]], h: 0, from: '13:30', until: '13:40', craft: 1, units: ['para'] }]),
  ['drop again: para is already in drop test'], 'a unit is in one drop');
assert.deepEqual(problems({}, [para([{ t: '13:00', x: 0, y: 0, state: 'line' }, { t: '14:00', x: 200, y: 0 }])]), ['drop test: para is on the map when the drop starts'], 'hidden when the drop starts');
assert.deepEqual(problems({}, [para([{ t: '13:00', x: 0, y: 0, state: 'hidden' }])]), ['drop test: para never forms up'], 'forms up after the drop');
assert.deepEqual(problems({}, [para([{ t: '13:00', x: 0, y: 0, state: 'hidden' }, { t: '13:35', x: 200, y: 0, state: 'line' }, { t: '13:45', state: 'hidden' }, { t: '14:00', state: 'line' }])]),
  ['drop test: para forms up at 1:35 PM, before the last of the drop is down at 1:40 PM'], 'not on the map until the last of the drop is down');
assert.deepEqual(problems({ zone: [[0, 0], [100, 0]] }), ['drop test needs a zone of three or more corners'], 'a zone is a polygon');
assert.deepEqual(problems({ zone: [[0, 0], [2500, 0], [0, 100]] }), ['drop test: zone corner off map (2500, 0)'], 'a zone on the map');
assert.deepEqual(problems({ kind: 'balloon', until: '13:20', craft: 0 }), ['drop test: kind must be para or glider', 'drop test needs from before until', 'drop test needs craft'], 'a kind, its times and its aircraft');
console.log('sim.js: ok');

let bad = 0;
const index = JSON.parse(readFileSync('battles/index.json', 'utf8'));
for (const entry of index) {
  const { id } = entry;
  const dir = `battles/${id}`;
  const battle = normalizeBattle(JSON.parse(readFileSync(`${dir}/battle.json`, 'utf8')));
  const terrain = existsSync(`${dir}/terrain.json`) ? JSON.parse(readFileSync(`${dir}/terrain.json`, 'utf8')) : null;
  const problems = validate(battle, terrain);
  if (!terrain) problems.push('no terrain.json (run tools/fetch_terrain.py)');
  if (!WARS.some(w => w.war === entry.war)) problems.push(`war "${entry.war}" has no entry in WARS (splash.js), so the start screen would not list it`);
  console.log(`${id}: ${battle.units.length} units, ${battle.events.length} events, ${battle.fallen.length} casualty markers${problems.length ? '' : ', ok'}`);
  for (const p of problems) console.log('  ! ' + p);
  bad += problems.length;
  entry.runtime = playTime(battle); // shown on the start screen; kept here so the page need not load every battle
}
index.sort((a, c) => a.date.localeCompare(c.date)); // date order, so battles built in parallel insert at different lines
writeFileSync('battles/index.json', JSON.stringify(index, null, 1) + '\n');
console.log('runtimes (s): ' + index.map(e => `${e.id} ${e.runtime}`).join(', '));
process.exit(bad ? 1 : 0);
