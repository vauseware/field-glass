// Formal property: the opening shot lands on the frame the first playing Follow step uses.
// ADR-0009: "The opening lands on the frame play uses, so the camera does not jump when Follow takes over."
//
// Opening side mirrors app.js startOpening + updateCamera while playing is still false:
//   lapsing stays false (step never calls advance), so ahead = speed * 4.
// Play side mirrors the first step after setPlaying(true):
//   advance sets lapsing; updateCamera uses (lapsing ? B.lapse : speed) * 4.
//
// Scope: actionBox at battle start (DOM-free stand-in for the Follow aim). Not the full camera
// fit into the panel clear-rect, not reduced-motion beats, not seek/skip of the opening.
//
// Run from repo root: node tools/formal/opening-landing.mjs
// Exit 0 only when every battle's boxes match within 1 m. Findings are failures, not soft warnings.

import { readFileSync } from 'node:fs';
import { normalizeBattle, actionBox, advance, defaultSpeed } from '../../sim.js';

const EPS = 1; // metres; actionBox is in world metres
const index = JSON.parse(readFileSync('battles/index.json', 'utf8'));
const findings = [];

function boxKey(bx) {
  if (!bx) return null;
  return { x0: bx.x0, y0: bx.y0, x1: bx.x1, y1: bx.y1 };
}

function sameBox(a, c) {
  if (!a && !c) return true;
  if (!a || !c) return false;
  return ['x0', 'y0', 'x1', 'y1'].every(k => Math.abs(a[k] - c[k]) < EPS);
}

function describe(bx) {
  if (!bx) return 'null (nothing to frame)';
  const w = (bx.x1 - bx.x0).toFixed(0), h = (bx.y1 - bx.y0).toFixed(0);
  const cx = ((bx.x0 + bx.x1) / 2).toFixed(0), cy = ((bx.y0 + bx.y1) / 2).toFixed(0);
  return `${w}×${h} m centred (${cx}, ${cy})`;
}

for (const entry of index) {
  const b = normalizeBattle(JSON.parse(readFileSync(`battles/${entry.id}/battle.json`, 'utf8')));
  const t = b.startT;
  const speed = defaultSpeed(b);
  const lapseOn = true; // opening and first Play leave Time-lapse on

  // Opening sample (app.js: startOpening runs updateCamera before setPlaying(true)).
  const openingAhead = speed * 4;
  const openingBox = actionBox(b, t, openingAhead);

  // First playing Follow lookahead (app.js: step → advance → updateCamera).
  // dt matches the frame cap in app.js frame(); only the returned lapsing flag matters here.
  const [, lapsing] = advance(b, t, 0.1, speed, lapseOn);
  const playAhead = (lapsing ? b.lapse : speed) * 4;
  const playBox = actionBox(b, t, playAhead);

  if (sameBox(openingBox, playBox)) {
    console.log(`${entry.id}: ok (lapsing=${lapsing}, ahead=${openingAhead})`);
    continue;
  }

  const finding = {
    id: entry.id,
    lapsing,
    openingAhead,
    playAhead,
    openingBox: boxKey(openingBox),
    playBox: boxKey(playBox),
  };
  findings.push(finding);
  console.log(`${entry.id}: FAIL`);
  console.log(`  first play sets lapsing=${lapsing}`);
  console.log(`  opening samples ahead=${openingAhead} s → ${describe(openingBox)}`);
  console.log(`  first play uses ahead=${playAhead} s → ${describe(playBox)}`);
  console.log(`  harm: title ease settles on the opening box, then Follow jumps to the play box`);
}

if (findings.length) {
  console.log(`\n${findings.length} battle(s) break ADR-0009 opening-landing.`);
  console.log('Do not weaken this check. Fix startOpening to sample with the first-play ahead, then update the openingAhead line in this file to match.');
  process.exit(1);
}
console.log('\nopening-landing: ok');
