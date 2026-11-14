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
- **Licences.** Dave's own recordings need none and are marked `own`. For downloads: CC0 first. CC BY
  3.0 or 4.0 when nothing CC0 fits, with the credit shown in the Sources dialog. Never NC
  (non-commercial), ND (no derivatives: every clip is trimmed and levelled), Sampling+, or "all rights
  reserved". An archive.org item counts only when its page states one of these licences or public
  domain. An upload with no licence is out. The BBC Sound Effects archive is non-commercial, so it is out.
- **Sources.** Dave's own recordings and Logic Pro sessions first. Then freesound.org through its API,
  which needs an API key kept out of the repo, archive.org through its advanced search API, and National
  Park Service recordings (living-history musket and cannon firings, the nature sound gallery), which are
  US government work. Others only if they meet the same licence rule and give a stable URL.
- **Logic content.** A part Dave plays on a Logic instrument is his. An Apple Loop or stock sample
  shipped unchanged as its own file is not allowed by Logic's licence, so none goes in the library.

## Where each sound comes from

Dave chose this split on 2026-11-13. Synthesis in the page sounds real only for far-off sound, and the
viewer zooms in. So files carry the sound itself, and code varies it and places it at a distance
(see Playback).

| Cue | Source | How |
|---|---|---|
| `field` wind and far rumble | Synthesized in the page | Filtered noise with a slow LFO. No file. |
| `field` birds | Download | One shared loop, mixed under the wind. |
| `bugle` in WW1 (the whistle) | Synthesized in the page | Two close sine tones with a pea warble. |
| `volley`, `scatter`, `gun`, `heavy`, `mg` | Download | Black-powder and live-fire recordings. |
| `hooves`, `engine`, `air`, `transport` | Download | Horses, tanks and warbirds can't be faked. |
| `wheels` | Download, plus Dave | Wagons downloaded. Chain and harness as foley. |
| `march`, `advance`, `fallback` | Dave, in Logic | His boots on gravel and grass, 20 to 40 passes layered. Kit rattle from a canteen, belt and tin cup. |
| `cheer`, the rebel yell, shouted orders | Dave, in Logic | His voice layered 30 to 50 times, pitch and formant shifted, low-passed until no word can be made out. |
| `drum`, fife, `bugle` calls | Dave, in Logic | Played. Every call and tune is public domain. |

A synthesized cue goes on the audition page beside a recording of the same thing. Dave keeps it only if
he can't tell which is which. If it fails, the cue becomes a file.

## The library

Sound belongs to a war's weapons, not to one battle, so the library is shared by era and each battle
draws on it:

| Era | Battles | What it needs |
|---|---|---|
| `common` | every war | `march`, `advance`, `fallback`, `cheer`, the bird bed of `field`, `hooves` at the walk, trot and gallop, horse-drawn `wheels` |
| `flintlock` | Revolution, War of 1812 | smoothbore musket volleys, skirmish pops, field guns, ship and battery guns, fife and drum, bugle and horn calls |
| `percussion` | Civil War | rifle-musket volleys, skirmish, rifled and smoothbore guns, naval guns (Fort Fisher), drums, bugle calls, the rebel yell |
| `great-war` | First World War | bolt-action rifles, machine guns, field guns and shell bursts |
| `ww2` | Second World War | rifles, machine guns, tank guns and engines, artillery, aircraft and bombs, transport aircraft, trucks and half-tracks |

Sounds that don't change between wars live once, in `common`. A cue resolves to the era's takes when
the era has any, and to `common` otherwise, so an era can override a shared cue (trucks for `wheels`
in `ww2`). That is about 36 sounds and 100 files in all, against 59 sounds with no sharing.

Files live in `sounds/<era>/<cue>-<n>.m4a`, beside `sounds/<era>/manifest.json`, with `common` as one
more folder of the same shape. Each cue has 2 to 4
takes. The page varies each play (see Playback), so repeats don't sound looped. Synthesized cues have
no files and no manifest entry.

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

`licence` is one of `own`, `CC0-1.0`, `CC-BY-3.0`, `CC-BY-4.0` or `PD`. `trim` and `gainDb` record what
the tool did, so a reviewer can redo it from the source. An `own` entry has `"source": "own"` and Dave
as `author`. Its WAV master and Logic project stay with Dave, outside the repo.

## The Sound agent

A new role in `.claude/skills/battle-pipeline/SKILL.md`, after Build. It runs once the research has said
the battle fits and the build PR is open. The first battle builds `common`. The first battle of an era
builds that era's library. Later battles add only the cues and extras they lack.

1. **Decide the cues.** Read battle.json for the unit types and states that occur and the features that
   fire. List the cues the era library has, and the ones this battle needs that it lacks. Split the
   missing ones by the source table: the agent searches for the downloads and gives Dave a list of the
   ones he makes.
2. **Search.** For each missing download cue, query freesound (`license:"Creative Commons 0"` first, then
   Attribution) and archive.org. Rank by duration (1 to 10 s), rating and downloads. Read every
   candidate's title, tags and description, and drop any that names a banned sound: scream, agony,
   pain, wounded, dying, death, moan, groan, cry, gore, injured, or a modern noise.
3. **Fetch and prepare.** `tools/fetch_sound.py` downloads the original, or takes a local WAV from
   Dave, trims to the event, makes it mono, levels it to -18 LUFS (`ffmpeg loudnorm`), fades the ends
   and writes AAC at 96 kbit/s as `.m4a`. It records `trim` and `gainDb` in the manifest. Dave bounces
   from Logic at 48 kHz, 24-bit, mono, with no limiter.
4. **Check what it can't hear.** The agent cannot listen. It uses `ffmpeg` to reject clipping, long
   silence and a loudness far off target.
5. **Dave listens.** The agent publishes an audition page with each new take, its cue, source and
   licence, and Dave marks each one keep or drop. His own takes and the synthesized cues go on the same
   page. Nothing enters the library without this pass. It is the
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
  blends into one sound. Desktop only: phones are out of scope (ADR-0012).
- **Variation and distance.** Each one-shot plays at a random rate within 5% of natural and a random
  gain within 2 dB, and never the same take twice running. A far source passes through a lowpass
  filter that closes with distance and sends more to one shared `ConvolverNode` reverb.
- **Synthesized cues.** The wind and far rumble of `field` and the WW1 whistle are built from Web Audio
  nodes, with no files.
- **Loops.** AAC pads the ends of a file, so a looped `.m4a` can click. Each loop plays as two
  overlapping sources that crossfade, not with `loop = true`.
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
- **Loading.** The `common` files and the battle's era files load on the first Play, so the start
  screen and first frame cost nothing new. About 5 MB for the two together.
- **Credits.** The Sources dialog lists every CC BY sound the battle can play, with title, author and
  link.

## Verification

- `npm run check` validates every manifest: the files exist, every licence is on the allowed list, every
  file cue a battle can trigger has at least 2 takes in its era or in `common`, and no file is over 10 s or 200 KB.
- A journey, `journeys/sound.cjs`, records which cues fire and how loud, through a hook available only
  under `navigator.webdriver`. It checks: silence while paused and during the opening; `volley` and `gun`
  during Cowpens's main line; `march` and `drum` as Tarleton's column comes on before dawn;
  `hooves` during Washington's charge; `wheels` when a battery limbers up and moves; `fallback` during a
  rout; `transport` during an Arnhem lift; `air` during Sidi Bou Zid's dive bombers; no movement cue
  while every unit in view stands; a source at the left edge pans left; a far source has a lower filter
  cutoff than a near one; two plays of one cue differ in rate; the synthesized `field` bed sounds with
  no file loaded; nothing while scrubbing; nothing
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

Dave chose on 2026-11-13:

5. Files carry each sound and code varies and places it. Only wind, far rumble and the whistle are
   synthesized, and only if they pass the audition. Dave makes the feet, kit, voices, drums, fifes and
   bugles in Logic. The rest is downloaded.

6. Sounds that don't change between wars are shared in `common`.

## Open: music

Not decided. No AI-generated music. If music comes in, it plays in the opening shot and in quiet
time-lapse stretches and fades out when fighting starts, because it would clash in tempo and key with
the `drum` loop. It shares the control and `AudioContext`, and loads on the first Play.

| Option | Fits | Catch |
|---|---|---|
| Dave arranges period tunes in Logic, one theme per war | Every era | His time. WW2 popular songs are still in copyright, so that era uses marches published before 1931 or an original score. |
| US military band recordings (Old Guard Fife and Drum Corps, the Marine Band's Sousa set) | `flintlock`, `percussion`, `great-war` | Check each recording's terms. |
| Commercial recordings published before 1926 (Library of Congress National Jukebox, archive.org 78s) | `great-war` | Nothing for WW2. |
| CC BY composers (Kevin MacLeod, Scott Buckley) | Any era, as plain underscore | Not period. Credit in Sources. |

Dave decides: whether music is in, and which option.

## Out of scope

- Narration, which issue #88 covers. It will share this spec's control and `AudioContext`, and battle
  sound ducks while the narrator speaks.
