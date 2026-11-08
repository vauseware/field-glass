# ADR-0013: Gliders fly their approach at the transports' pace

**Status:** accepted, 2026-11-08

## Context

ADR-0011 made everything in a drop except the transports pure in battle time, gliders included. Each glider flew a
1,500 m final approach in 90 battle seconds. At Arnhem's 60x glider chapters that took 1.5 real seconds, so a glider
crossed the map at about 1,000 m a real second. The Dakotas fly on the real-time clock at 228 to 344 m a real second.
The gliders went three to four times as fast as the aircraft that towed them. They were also drawn at their size on
the map, about 9 px against a Dakota's 34, so they read as tiny aeroplanes.

## Decision

- **A glider's approach takes the real seconds the transports take to fly it.** `dropAt(f, t, clock, rate)` takes
  the playback rate (battle seconds a real second) and stretches the approach to `1,500 m / transport pace x rate`
  battle seconds. The glider still touches down at its battle time, so the landing, roll-out, men and rally stay
  pure in `t`. The frame now depends on the rate, which a screenshot link fixes through the chapter's speed.
- **The approach is capped at 900 battle seconds** (`GLIDER_APPROACH_MAX_S`), so a glider drop's air hook starts a
  fixed time before its first touchdown. Up to 120x on Arnhem's zones the cap never binds. Past it, gliders fly
  faster than the transports but never pop in mid-air.
- **A glider aloft is drawn at a Dakota's size** (31 px, as a Horsa on tow is) and shrinks to its size on the map as
  it comes down. Drawn at full size on the ground, a zone's 150 gliders bury the zone and its units.

## Consequences

- Parachute canopies stay pure in battle time. They drift about 210 m as they fall, so at 60x they move about 140 m
  a real second, slower than the transports.
- Time-lapse slows 900 battle seconds before a glider drop's first touchdown instead of 90.
