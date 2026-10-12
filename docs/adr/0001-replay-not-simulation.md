# ADR-0001: Battles are historical replays, not simulations

**Status:** accepted, 2026-10-12

## Context

The app exists so a military historian can watch battles unfold on a cheap laptop with
integrated graphics. Accuracy is the first requirement. A true simulation, with morale, fire and
movement models, produces a different outcome on every run and needs tens of thousands of agents
to look right, which that hardware cannot draw at a steady frame rate.

## Decision

Each battle is a data folder of regiment-sized units with keyframed timelines taken from troop
movement maps and orders of battle. The engine interpolates position, facing and strength between
keys. Fire, smoke, muzzle flashes and casualty markers are cosmetic: they are driven by the
recorded state and never feed back into movement or outcome.

Units are formations, never individual soldiers. A few hundred formations cover Gettysburg; a few
thousand dots cover any battle on Canvas 2D without a GPU.

## Consequences

- Adding a battle is research and data entry, not engine work.
- Positions between recorded snapshots are reconstruction. Every battle lists its sources, and the
  caption text says what is known and what is inferred.
- A "what if" mode is out of scope. If it is ever wanted, it is a different engine.
