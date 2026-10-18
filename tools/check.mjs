// Self-check for sim.js plus validation of every battle in battles/index.json. Run: npm run check
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import assert from 'node:assert/strict';
import { normalizeBattle, validate, unitAt, lerpAngle, dots, parseTime, fmtTime, activity, playTime, actionBox, tracks, shape } from '../sim.js';

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
  console.log(`${id}: ${battle.units.length} units, ${battle.events.length} events, ${battle.fallen.length} casualty markers${problems.length ? '' : ', ok'}`);
  for (const p of problems) console.log('  ! ' + p);
  bad += problems.length;
  entry.runtime = playTime(battle); // shown on the start screen; kept here so the page need not load every battle
}
writeFileSync('battles/index.json', JSON.stringify(index, null, 1) + '\n');
console.log('runtimes (s): ' + index.map(e => `${e.id} ${e.runtime}`).join(', '));
process.exit(bad ? 1 : 0);
