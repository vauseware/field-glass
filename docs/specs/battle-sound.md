# Battle sound: a sound library per era, and the agent that gathers it

**Status:** draft

## Why

The replay is silent. Smoke and muzzle flashes show where the fighting is, but a viewer watching one part
of the field misses a volley at the other end. A low bed of musketry, guns and hooves says the fight has
started, grown or died down, the way a documentary's sound does. Field Glass is watched, not played, so
the sound is a mood track driven by the replay, not one sound per shot.

The aim on desktop is immersion: the viewer should hear an army move as well as fight. Columns tramp
up a road, guns rattle into position, horses come on, and a line going forward through a field sounds
different from one falling back. Movement fills the long stretches between the fighting, which are most
of a battle.

## Rules for every sound

- **What we want.** Cannon and field guns, musket volleys and scattered skirmish fire, rifles, machine
  guns, shell bursts, tanks and aircraft for the wars that had them, horses at the walk, trot and gallop,
  drums and fifes on the march, bugle calls, men cheering, shouting orders and yelling in a charge. For
  movement: boots on road and in grass, the rattle of kit and canteens, gun limbers, caissons and wagons,
  harness and teams, trucks and half-tracks, and transport aircraft overhead.
- **What we never take.** Nothing with agony, pain, screaming, the wounded, dying, crying or gore, and no
  distressed animals. No modern sounds in the clip: traffic, an aircraft over a re-enactment, a PA, or
  talk between shots. No speech a viewer can make out, since it would be in the wrong voice.
- **Licences.** CC0 first. CC BY 3.0 or 4.0 when nothing CC0 fits, with the credit shown in the Sources
  dialog. Never NC (non-commercial), ND (no derivatives: every clip is trimmed and levelled), Sampling+,
  or "all rights reserved". An archive.org item counts only when its page states one of these licences
  or public domain. An upload with no licence is out.
- **Sources.** freesound.org through its API, which needs an API key kept out of the repo, and
  archive.org through its advanced search API. Others only if they meet the same licence rule and give a
  stable URL.

## The library

Sound belongs to a war's weapons, not to one battle, so the library is shared by era and each battle
draws on it:

| Era | Battles | What it needs |
|---|---|---|
| `flintlock` | Revolution, War of 1812 | smoothbore musket volleys, skirmish pops, field guns, cavalry, fife and drum; marching feet, gun teams and limbers, bugle and horn calls |
| `percussion` | Civil War | rifle-musket volleys, skirmish, rifled and smoothbore guns, naval guns (Fort Fisher), cavalry, drums, the rebel yell and cheering; marching feet, limbers and caissons, bugle calls |
| `great-war` | First World War | bolt-action rifles, machine guns, field guns and shell bursts, whistles; boots and kit, horse-drawn guns and wagons |
| `ww2` | Second World War | rifles, machine guns, tank guns and engines, artillery, aircraft and bombs; boots and kit, trucks and half-tracks, transport aircraft |

Files live in `sounds/<era>/<cue>-<n>.m4a`, beside `sounds/<era>/manifest.json`. Each cue has 3 to 6
takes, so repeats don't sound looped.

### Cues

A cue is what the replay can ask for. The replay already knows each unit's `type` (infantry,
light_infantry, riflemen, militia, cavalry, artillery, armor), its `state` (column, line, skirmish,
firing, charge, retreat, rout, surrender) and its `fire` level (`sim.js` `fireLevel`), plus features
such as `ship`, `battery` and `airstrike`. The cues map onto those, so nothing new is authored per unit:

| Cue | Plays when | Kind |
|---|---|---|
| `volley` | infantry-type units firing | one-shot, rate set by how much fire is in view |
| `scatter` | units skirmishing, or `fire` below 0.5 | one-shot, sparse |
| `gun` | artillery firing; armour firing in WW2 | one-shot |
| `heavy` | a `ship` or `battery` feature firing; WW1 and WW2 shell bursts | one-shot |
| `mg` | WW1 and WW2 infantry firing, mixed with `volley` | one-shot |
| `hooves` | cavalry moving or charging; the gait (walk, trot, gallop) follows the unit's ground speed | loop, faded by distance |
| `engine` | armour moving | loop |
| `air` | an `airstrike` feature active | loop, with `heavy` for the bombs |
| `transport` | a `drop` feature's transports over the zone (`f.air`, ADR-0011) | loop, the drone rising and passing |
| `cheer` | a unit enters `charge` | one-shot, once per charge |
| `bugle` | a cavalry unit enters `charge` (flintlock and percussion); in WW1, the whistle as infantry leave their trench | one-shot, once per charge or attack |
| `march` | infantry-type units in `column` on the move, every era: boots on the road, kit | loop, its volume set by the men moving in view |
| `drum` | flintlock and percussion infantry moving in `column` or `line` | loop, with `march` |
| `advance` | infantry-type units moving in `line` or `skirmish`: feet in grass, kit, an order shouted now and then | loop, quieter than `march` |
| `wheels` | artillery moving: limbers, caissons and teams; trucks and tows in WW2 | loop |
| `fallback` | units in `retreat` or `rout`: hurried feet and hooves, no voices in distress | loop, faster than `march` |
| `field` | always while playing: wind, birds, a distant rumble | loop, a very quiet bed |

**Moving** means a unit's position changed since the last frame by more than a walking pace at the
current battle time, read from the same keyframes the map draws, so no unit needs new data. A unit
standing in `column` or `line` makes no movement sound. The movement loops play at their natural pace,
like the fire cues; only their volume follows how many men move in view.

A battle that needs a sound its era lacks, such as bagpipes for the 71st at Cowpens, adds it to the
era's library with a `battles` list in its manifest entry. Its battle.json names it in an optional
`sound.extra` list. There is no per-battle sound folder.

### Manifest entry

```json
{ "file": "volley-2.m4a", "cue": "volley", "seconds": 3.4,
  "source": "https://freesound.org/s/123456/", "title": "Musket volley, reenactment", "author": "name",
  "licence": "CC0-1.0", "trim": [1.20, 4.60], "gainDb": -3.1, "battles": null }
```

`licence` is one of `CC0-1.0`, `CC-BY-3.0`, `CC-BY-4.0` or `PD`. `trim` and `gainDb` record what the
tool did, so a reviewer can redo it from the source.

## The Sound agent

A new role in `.claude/skills/battle-pipeline/SKILL.md`, after Build. It runs once the research has said
the battle fits and the build PR is open. The first battle of an era builds that era's library. Later
battles add only the cues and extras they lack.

1. **Decide the cues.** Read battle.json for the unit types and states that occur and the features that
   fire. List the cues the era library has, and the ones this battle needs that it lacks.
2. **Search.** For each missing cue, query freesound (`license:"Creative Commons 0"` first, then
   Attribution) and archive.org. Rank by duration (1 to 10 s), rating and downloads. Read every
   candidate's title, tags and description, and drop any that names a banned sound: scream, agony,
   pain, wounded, dying, death, moan, groan, cry, gore, injured, or a modern noise.
3. **Fetch and prepare.** `tools/fetch_sound.py` downloads the original, trims to the event, makes it
   mono, levels it to -18 LUFS (`ffmpeg loudnorm`), fades the ends and writes AAC at 96 kbit/s as
   `.m4a`. It records `trim` and `gainDb` in the manifest.
4. **Check what it can't hear.** The agent cannot listen. It uses `ffmpeg` to reject clipping, long
   silence and a loudness far off target.
5. **Dave listens.** The agent publishes an audition page with each new take, its cue, source and
   licence, and Dave marks each one keep or drop. Nothing enters the library without this pass. It is the
   only human step, Dave alone signs it off, and it enforces the "no agony" rule the agent cannot check by ear.
6. **Commit** the kept files, manifest entries and credits to the build PR.

## Playback in the page

- **Web Audio.** One `AudioContext`, created on the first Play click, since browsers allow sound only
  after a gesture. Each frame the page sums what is in view: fire by unit type, cavalry and armour
  moving, charges begun, active features. That mix sets each cue's rate and volume. Units off screen
  count at a quarter, so a fight just out of frame is heard faintly.
- **Place on desktop.** Each source pans left or right by where its units sit across the screen (a
  `StereoPannerNode` per active cue), and its volume falls with distance from the centre of the view.
  Zoomed in, the near column's boots and the battery in front of it stand out; zoomed out, the field
  blends into one sound. A phone plays the same cues in mono.
- **Real time, not battle time.** At 10× to 300× a unit fires many times a second of replay, so each
  sound plays at its natural pace and only the density follows the fighting. At most 8 one-shots sound
  at once.
- **Quiet when nothing happens.** Paused: silent. Time-lapse over a quiet stretch: only the `field` bed.
  Scrubbing or arrow keys: silent until play resumes. The opening shot: the `field` bed fading up, and
  battle sound only once it ends.
- **The control.** A speaker button in the bar mutes and unmutes; the `m` key does the same. Pointing at
  the button, or tabbing to it, slides out a short volume slider beside it, the way video players do, so
  the bar at 1280x700 gains one icon and no fixed width. Sound starts on at 60% volume. The state is
  stored as `{ on, volume }` in `localStorage` key `fieldglass.sound` inside `try`. Dragging the slider
  to zero mutes; raising it unmutes.
- **Loading.** An era's files load on the first Play, so the start screen and first frame cost nothing
  new. About 5 MB per era with the movement cues.
- **Credits.** The Sources dialog lists every CC BY sound the battle can play, with title, author and
  link.

## Verification

- `npm run check` validates every manifest: the files exist, every licence is on the allowed list, every
  cue a battle can trigger has at least 3 takes, and no file is over 10 s or 200 KB.
- A journey, `journeys/sound.cjs`, records which cues fire and how loud, through a hook available only
  under `navigator.webdriver`. It checks: silence while paused and during the opening; `volley` and `gun`
  during Cowpens's main line; `march` and `drum` as Tarleton's column comes on before dawn;
  `hooves` during Washington's charge; `wheels` when a battery limbers up and moves; `fallback` during a
  rout; `transport` during an Arnhem lift; `air` during Sidi Bou Zid's dive bombers; no movement cue
  while every unit in view stands; a source at the left edge pans left; nothing while scrubbing; nothing
  after `m`; the slider scales the master gain and its value survives a reload.
- `laptop.cjs` still passes with the speaker button and its slider open, and the bar does not wrap at
  1280x700.

## Decided

Dave answered on 2026-10-25:

1. Sound is on by default once he presses Play.
2. There is a volume slider as well as mute.
3. Dave alone signs off the audition page.

Dave added on 2026-11-08:

4. The goal is immersive on desktop: sound covers marches and every kind of unit movement, not only
   fighting, and sources sit in stereo by where they are on screen.

## Out of scope

- Music.
- Narration, which issue #88 covers. It will share this spec's control and `AudioContext`, and battle
  sound ducks while the narrator speaks.
