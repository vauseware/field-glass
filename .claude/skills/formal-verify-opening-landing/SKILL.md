---
name: formal-verify-opening-landing
description: Formally check that Field Glass's opening shot lands on the frame the first playing Follow step will use (ADR-0009). Under /poteto-mode, run this when Prove It Works or a Feature/Bug-fix touches the opening/Follow/lapse path. Use when a change touches startOpening, updateCamera, step, advance, activity, actionBox, lapse defaults, battle start times/chapters, or when claiming the opening no longer jumps after the title.
---

# Formal verify: opening lands where play Follows

## Under poteto

Poteto does not replace this check with a journey. If the change can move the opening target or first-play `lapsing`, `/poteto-mode` should run `node tools/formal/opening-landing.mjs` as part of verify (alongside **verify-field-glass** journeys when the UI also changed). Findings stay findings until product code is fixed on purpose.

## Property

The opening shot's camera target is the frame Follow will already be settled on for the first chapter, including the lookahead of the first playing frame. The clock stays frozen until the ease finishes. If this breaks, the title sequence eases onto one frame and Follow then jumps to another.

Harm in one sentence: the viewer watches a four-second ease onto the first chapter, then the map slews when play takes over.

## Tool and why

A Node property check over every battle in `battles/index.json`, DOM-free, using `actionBox` / `activity` / `defaultSpeed` from `sim.js`. No TLA+, no browser. The failure is a deterministic mismatch of two lookaheads at `t = startT`; geometry needs numbers, not a model checker. One command, no extra install.

## Coverage

| What | Where |
| --- | --- |
| Opening sample (ahead while `lapsing` is still false) | `app.js` `startOpening` + `updateCamera` before `setPlaying(true)` |
| First-play lookahead (`advance` sets `lapsing`) | `app.js` `step`; `sim.js` `advance`, `activity` |
| Frame stand-in | `sim.js` `actionBox` at battle start |
| Promise | `docs/adr/0009-opening-shot.md` ("lands on the frame play uses") |

**Out of scope:** panel clear-rect fit and zoom math in `updateCamera`, reduced-motion beats, seek/skip/`endOpening`, dawn wash, battles opened mid-way.

**Sync commit:** `7564b2f704bda92e77e8a98b17f621659025cca3` — last confirmed that this check describes the covered code. Move this forward only after you re-read those sites and confirm the opening-side and play-side formulas in `tools/formal/opening-landing.mjs` still match.

## When to run

A change touches any coverage row, or you are about to claim the opening no longer jumps. Also run after editing the check itself.

## Command

From the repo root:

```bash
node tools/formal/opening-landing.mjs
```

Exit `0` only when every battle's opening box and first-play box match within 1 m. Exit `1` prints each finding in battle terms (quiet vs busy start, both aheads, both boxes).

Findings are real. Do not soften the property, shrink the battle set, or widen `EPS` to make a red check green. Do not change product code unless the user asks; report the counterexample.

## Reading a failure

1. `FAIL` naming a battle means at that battle's start the opening samples one Follow ahead and the first playing step uses another.
2. `first play sets lapsing=true` means Time-lapse will hurry on the first clock step, so Follow's ahead jumps from `speed * 4` to `lapse * 4` (often hours).
3. `opening samples ahead=… → null` and `first play uses ahead=… → … m centred …` means the ease has nowhere to go, then Follow snaps to the first chapter.
4. A modelling error looks different: both boxes equal in the log but the live page still jumps (then the stand-in missed panel fit — out of scope here), or the check's opening-side formula no longer matches `startOpening` (update the check, then re-run).

When you intentionally fix the bug, make `startOpening` sample with the same ahead the first playing `updateCamera` will use (predict `lapsing` the way `advance` does). Then change the `openingAhead` line in `tools/formal/opening-landing.mjs` to that same formula so the check stays a real comparison, not a stale mirror. Re-run until exit `0`. Advance the sync commit only after that.

## Broken-variant proof

The check must be able to fail. To confirm after editing the check: temporarily force `lapsing` true in `sim.js` `advance` (e.g. `const lapsing = !!lapse && b.lapse > speed`), run the command, and expect more `FAIL`s than the baseline — at least `sidi-bou-zid`, which is busy at the start under the real rule but whose `actionBox` changes when ahead jumps to `lapse * 4`. Revert the scratch edit and confirm the log matches the known baseline (passing, or only the reported findings).

## Baseline at sync commit

At `7564b2f`, the check fails on quiet starts where the two aheads disagree: `trenton-princeton`, `monmouth`, `yorktown`, `fort-fisher`, `cantigny`. Busy starts such as `cowpens` and `sidi-bou-zid` pass. Treat those five as open findings until product code is fixed on purpose.

## After drift

If covered files changed after the sync commit and nobody re-ran this check, use `/maintain-formal-verification-skill` (or `/pstack:maintain-formal-verification-skill`) to bring the verification back in line.
