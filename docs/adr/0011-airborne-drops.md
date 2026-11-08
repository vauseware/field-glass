# ADR-0011: Airborne drops are a cosmetic feature; the unit's keys own its rally

**Status:** accepted, 2026-11-07

## Context

Arnhem's lifts decided the battle, but its paratroop and glider units popped into being fully formed on a text
label at their drop time (issue #84). A viewer should see the transports cross the zone, canopies or gliders come
down, the men scattered across the ground, and the men walking in to form their unit. Three questions were open:
whether the scatter is the unit's own dots or a separate effect, whether gliders and parachutes are one type or
two, and how to draw a drop that missed its zone.

Air strikes already set the pattern (ADR-0003): cosmetic, never moving a unit or changing the outcome, drawn only
by a skin's `air` hook. D-Day (#6) needs drops too, so the feature serves more than one battle, which is
ADR-0003's test.

## Decision

- **One `drop` feature type with `kind: para | glider`.** Rally, validation, time-lapse, the hook and the legend
  are the same code for both; `kind` changes only how men come down (canopies along each aircraft's stick, or out
  of a glider where it stopped) and what the skin draws.
- **The unit's keys own the rally.** A dropped unit stays `hidden` until its first visible key at or after the
  drop's `until`. That key is where and when it has formed; the drop stores no rally time. `sim.js` validates the
  rule and `make.py` checks it at build time. A unit is in one drop at most. Losses on the drop are a loss at the
  rally key: the hidden key keeps the strength that went in, and each lost dot becomes a fallen marker where that
  man came down.
- **The drop is cosmetic and private to `sim.js`.** `normalizeBattle` plans each drop once: every man's landing,
  seeded, and his walk to his own dot in the formed unit, so the unit appears where its men already stand. The plan
  lives in a module `WeakMap`. The one public read is `dropAt(f, t, clock)`, a reused frame of typed buffers in
  world metres, so nothing is allocated per frame and the skin projects as it does for an air strike. Canopies,
  gliders and men are pure in battle time, so scrubbing and screenshot links work; only the transports fly on the
  real-time clock. Units, `unitAt`, `dots`, `actionBox` and `drawUnits` are unchanged.
- **`zone` is a polygon of where the men came down,** which for a drop that missed is not the zone it was meant
  for. On target it is the zone outline the battle already holds, so it costs no new data. Men land inside it, which
  keeps the Poles out of the Rhine at DZ-K.
- **`f.air = [t0, t1)`** on drops and air strikes alike: from the first canopy or glider's approach until the last
  unit has formed. `app.js` gates every `air` call and hides every air feature's name on it, and time-lapse holds
  over the whole span. A skin without `air` computes nothing and draws nothing: there the unit appears at its rally
  key, as it appeared at its drop time before.

**Rejected: the scatter as the unit's pose.** The other design gave `unitAt` a rally branch, `dots` a blend between
landing and formation, and changed `actionBox`, the `drawUnits` zoom gate, the unit card and the WWII bracket. It
touched every hot path and every skin, and in skins without `air` the men would still scatter, against the issue's
"does nothing there". Chapters already set the camera, so its gain in framing was small.

## Consequences

- A battle times each dropped unit's appearance from its rally, not its drop. Where sources give no rally time or
  run-in heading, the battle's `make.py` marks its choice `[INF]` or `[DERIVED]`.
- Gliders and chutes leave the ground when the drop's last unit has formed, not when the real ones were cleared.
- A unit split across several drops, as in Normandy, needs a share per drop. Validation rejects it today.
- Men on the ground draw over unit labels, since the `air` hook runs after them; during a drop few labelled units
  stand on the zone.
- At a zoom where a formed unit draws no dots (a column below 24 px wide), its men's specks give way to its bracket
  and counter at the rally key, in the same place.
