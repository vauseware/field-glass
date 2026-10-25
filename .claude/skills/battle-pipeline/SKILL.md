---
name: battle-pipeline
description: Research a Field Glass battle into its GitHub issue, build it from that issue into a PR, and review the PR. The contract the battle-loop workflow's agents follow. Use when researching, building or reviewing a battle from a queued issue.
---

# Battle pipeline

One GitHub issue per battle. The issue carries the battle from queued to built:

| label | meaning | set by |
|---|---|---|
| `research` | queued; the body names the battle, its date and a suggested id | Dave or the coordinator |
| `researched` | the note and the verdict are posted; the battle fits | the researcher |
| `question` | it does not fit as asked, or needs engine work; Dave decides | the researcher or the builder |
| `building` | a builder has it | the builder |

The builder's PR says `Closes #<issue>`, so the issue closes when Dave merges. Each issue also carries its war's label (`revolutionary-war`, `war-of-1812`, `civil-war`, `ww1`, `ww2`). The order of work is the checklist in the pinned "Battle queue" issue.

`note.py` (beside this file) moves a note between a local file and the issue: `post <issue> <file>` and `pull <issue> <file>`. Always use it. Never paste a note by hand.

Fences for every role: never edit this skill, `.claude/workflows/`, another battle's folder, or the engine (`app.js`, `sim.js`, `splash.js`, `themes.js`, `themes/`, `index.html`, `tools/`). If a battle needs engine work, stop, say what is needed, and set `question`. Never merge, tag or deploy. Never spawn subagents.

## Research

You get one issue. Read it, then README "Add a battle" and the battle.json field table, `docs/adr/0001-replay-not-simulation.md`, and one finished note as a model if any exists in `docs/plans/research/` (`new-orleans-research.md` is the newest).

1. Read the sources. Prefer primary accounts, official records, troop-movement maps and park service histories. Tag every fact with its source (`[LAT]`, `[OR]`, `[NPS]`), and every placement you derive with `[DERIVED]`, `[CALC]` or `[INF]` and its method.
2. Write `docs/plans/research/<id>-research.md` (gitignored; never commit it) with these sections:
   1. **Geography.** Proposed `origin` and `extent` with what the frame holds and leaves out; the exact `tools/fetch_terrain.py` command (3DEP in the US, `--copernicus` elsewhere); a table of anchors in lat/lon and local metres with source and error; how the ground has changed (shoreline, fill, woods, roads); the features to draw (roads, creeks, works, trenches, woods, fields, buildings).
   2. **Order of battle.** Every unit at regiment, battalion or brigade size, per side, with commander, strength and type (infantry, cavalry, artillery with guns, armor with vehicles), and variant strengths.
   3. **Timeline.** Each unit's movements with clock times, each marked **recorded** (a time in a source, quoted) or **inferred** (your placement, with the reasoning). State the clock convention (local mean time before standard time).
   4. **Casualties.** Per side and per unit where known, with variant figures.
   5. **Sun and weather.** Sunrise and sunset computed for the place and date, moon if a night action matters, fog, rain, snow.
   6. **Fit for Field Glass.** Whether it is worth watching: what moves on the map, how often and how far, and where formations meet. A battle that is mostly bombardment, siege digging or ships at sea is dull to watch; propose a narrower frame or days where the armies manoeuvre, or give the verdict **does not fit**. Then what the DEM will show and what `make.py` must draw; proposed chapters with times; `menPerDot`; the skin (by date: 1812 to 1815 War of 1812, 1861 to 1865 Civil War, 1914 to 1918 First World War, 1939 to 1945 Second World War, else Revolution); any engine gap.
   7. **Gaps and uncertainties.** What you could not settle, and which source would settle it.
   8. **Sources.** Each with its tag, full citation and URL, and how you read it.
3. `python3 .claude/skills/battle-pipeline/note.py post <issue> docs/plans/research/<id>-research.md`.
4. Comment the verdict, headed `<!-- verdict -->`: **fits**, **fits with engine work**, or **does not fit**; why it is worth watching; origin and extent; time span; unit count; `menPerDot`; chapters; engine gaps; the five best sources.
5. Swap `research` for `researched` if it fits, else for `question`.

## Build

You get one researched issue and a git worktree. Read README in full, `docs/adr/` titles, `battles/monmouth/make.py` (the template: copy its `walk()` marching-pace helper and its closing asserts) and the newest battle's `make.py` for multi-day clocks, ships and water. Read `.claude/skills/verify-field-glass/SKILL.md`.

1. `git fetch origin && git checkout -b feat/<id> origin/main`. Add `building` to the issue.
2. `python3 .claude/skills/battle-pipeline/note.py pull <issue> docs/plans/research/<id>-research.md`. The note is the only source of facts. A caption states nothing the note does not give.
3. Fetch the terrain with the note's command. Commit it alone ("<Name>: terrain from <source>, <extent> at <spacing>").
4. Write `battles/<id>/make.py` that writes `battle.json`. Keep every place in lat/lon and convert once. Label any place the note gives at ±200 m or worse "about here". Its asserts must hold:
   - every leg starts where the unit stands, and no moving leg runs over three hours;
   - no unit moves faster than its type's top pace;
   - every key and every label is on land, unless it is a ship;
   - each caption's `when` hour matches its frame's time, and an untimed chapter sits within 15 minutes of the hour.
   The page draws elevation exactly 0 as missing data, so floor dry ground at 0.1 m. Commit ground and order of battle, then movements, then chapters, each a commit whose `make.py` runs on its own.
5. Add the battle to `battles/index.json` (`id`, `name`, `date`, `war`) and run `npm run check`; it sorts the list by date and writes the running time. Do not touch the README.
6. Verify with `fg.sh` in a new folder under your scratchpad: shoot every chapter at 1536x830 (`#<id>@<time>,play,warp`; shoot a quiet chapter paused, since time-lapse runs past it), one frame at 390x844, and the start screen on the battle's war. Run `journeys/playback.cjs <id>` and `journeys/laptop.cjs <id>`. Look at every PNG. Fix units in water, labels on labels, a chapter framed on nothing, formations wider than their men, night that does not darken the ground.
7. Push. Open the PR with `gh pr create`, ready, titled "<Name>: <what the replay covers>", body: Why, What changed, Scope, Verification, then where you departed from the note and why, and open gaps. It says `Closes #<issue>`. Add a desktop and a phone shot with `bash ~/bin/pr-shot.sh <pr> <png>...`. Stop the `fg.sh` server.

## Review

You get one PR and its issue. Read only; change nothing. Pull the note to your scratchpad with `note.py pull`.

Check, each against the note: every number and name in every caption; each unit's strength and side; each anchor's position against the note's table; chapter times against recorded times; that `make.py`'s asserts are present and pass (`python3 battles/<id>/make.py` in a scratch checkout of the PR); that the PR's screenshots show what the captions say. Report each finding with the caption or line, what the note says, and severity: **wrong** (contradicts the note), **unsupported** (not in the note), **nit**. Post the findings as one PR comment headed `<!-- review -->`.

## Fix

You get the PR, its branch and the review's findings. Fix every **wrong** and **unsupported** finding, or dismiss it with a reason in a PR comment. Rerun `make.py`, `npm run check` and the shots the fix touches. Push to the same branch.
