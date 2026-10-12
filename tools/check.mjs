// Self-check for sim.js plus validation of every battle in battles/index.json. Run: npm run check
import { readFileSync, existsSync } from 'node:fs';
import assert from 'node:assert/strict';
import { normalizeBattle, validate, unitAt, lerpAngle, dots, parseTime } from '../sim.js';

const u = { id: 'x', side: 'a', type: 'infantry', strength: 100, keys: [
  { t: '07:00', x: 0, y: 0, h: 350 },
  { t: '07:10', x: 100, y: 0, h: 10, strength: 50, state: 'firing' },
  { t: '07:20', state: 'hidden' },
] };
const b = normalizeBattle({ start: '07:00', end: '08:00', menPerDot: 10, units: [u] });
const mid = unitAt(u, parseTime('07:05'));
assert.equal(unitAt(u, parseTime('06:59')), null, 'hidden before first key');
assert.deepEqual([mid.x, mid.h, mid.strength, mid.state], [50, 0, 75, 'line'], 'midpoint interpolation');
assert.equal(unitAt(u, parseTime('07:10')).state, 'firing');
assert.equal(unitAt(u, parseTime('07:15')).fire, 1);
assert.equal(unitAt(u, parseTime('07:21')), null, 'hidden after hidden key');
assert.equal(dots(u, unitAt(u, parseTime('07:00')), 10).length, 20, 'ten dots');
assert.equal(b.fallen.length, 5, 'one marker per 10 men lost');
assert.equal(lerpAngle(350, 10, 0.5), 0, 'heading wraps through north');
console.log('sim.js: ok');

let bad = 0;
for (const { id } of JSON.parse(readFileSync('battles/index.json', 'utf8'))) {
  const dir = `battles/${id}`;
  const battle = normalizeBattle(JSON.parse(readFileSync(`${dir}/battle.json`, 'utf8')));
  const terrain = existsSync(`${dir}/terrain.json`) ? JSON.parse(readFileSync(`${dir}/terrain.json`, 'utf8')) : null;
  const problems = validate(battle, terrain);
  if (!terrain) problems.push('no terrain.json (run tools/fetch_terrain.py)');
  console.log(`${id}: ${battle.units.length} units, ${battle.events.length} events, ${battle.fallen.length} casualty markers${problems.length ? '' : ', ok'}`);
  for (const p of problems) console.log('  ! ' + p);
  bad += problems.length;
}
process.exit(bad ? 1 : 0);
