# ADR-0003: WWII battles get terrain, unit and effect features shared across the war

**Status:** accepted, 2026-10-17

## Context

Sidi Bou Zid (14–17 February 1943, the opening of the Kasserine Pass battles) is the first WWII
battle. The research for it (issue #4) found four gaps:

- `tools/fetch_terrain.py` reads USGS 3DEP, which covers only the US.
- WWII fighting turns on tanks, and dots for men cannot show a tank company.
- Dive bombers destroyed the 2nd Battalion, 17th Field Artillery. Aircraft are not formations on the
  ground, so units are the wrong model for them.
- Every `firing` unit draws black-powder smoke.

The rule so far has been that new battles are data, with no engine features for one battle. These
gaps are not one battle's: the Bulge, D-Day and Market Garden need the same things, and all but D-Day
lie outside the US.

## Decision

Engine features that serve a whole war are allowed. Features for one battle still are not.

- **Terrain.** Outside the US, terrain comes from the Copernicus GLO-30 DSM:
  `fetch_terrain.py --copernicus`. The files are public cloud-optimised GeoTIFFs on AWS, with no
  account needed. The script reads only the header and the tiles it samples, by HTTP range request,
  and decodes them with the standard library. GLO-30 is 30 m and a surface model, so modern towns
  and orchards add a few metres. Its licence requires credit; the app does not show terrain sources,
  so each battle's `sources` must carry the credit.
- **Armour.** `armor` is a unit type in `sim.js` with a vehicle count, like `guns` for artillery,
  and casualties counted in vehicles. It is drawn in the theme's unit hook (ADR-0002), not in a new
  branch in `app.js`.
- **Aircraft.** An air strike is a cosmetic feature with a place and `from`/`until` times. Like
  smoke, it never moves a unit or changes the outcome.
- **Smoke.** Black-powder smoke is part of a war's fire recipe in its theme, and a battle can
  override it.

ADR-0001 speaks of regiment-sized formations. In WWII the formation is the company or battery (US)
and the battalion (German). The engine does not care; the unit size is a data choice made per
battle, aiming for a few hundred formations at most.

## Consequences

- WWII battles need engine work before their data can be built. Later wars may need the same, and
  the test is the same: does more than one battle need the feature?
- Terrain fetches outside the US depend on the AWS Open Data copy of GLO-30 staying public.
- Tank types (Sherman, Mark IV, Tiger) look alike unless the label names them.
