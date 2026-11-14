# Battle sound audition

A single page for choosing battle sounds by ear. It plays each synth cue next to real recordings,
runs a blind test, and lets you tick which takes join each cue's pool. An "Observer distance" switch
adds a 1.4 kHz lowpass and reverb, so every take is heard as the observer hears it: distant and
muffled, never incoming. The rules it serves are in `docs/specs/battle-sound.md`.

This folder is a research tool. `tools/build.sh` does not copy it into `dist/`, so it never deploys
with Field Glass.

The page is also published at https://claude.ai/artifact/Kqb6bgTnHbCAgHESw8b7ZU. Republish to that
URL after a change, so saved picks and the link stay the same.

## Run it

```bash
cd /Users/claw/dev/gh/vauseware/field-glass/tools/sound-audition && python3 -m http.server 8000
```

Open http://localhost:8000/. From another machine over SSH, forward the port first
(`ssh -L 8000:localhost:8000 <mini>`), then open the same address there.

The page must be served over HTTP; it fetches `refs*/manifest.json` and the clips, which `file://`
blocks.

## What is here

| Path | What |
|---|---|
| `index.html` | The page: synth recipes (`CUES`), World War rows (`WWROWS`), pool picks, blind test, observer switch. |
| `refs/` | First pass: freesound recordings for the shared cues (wind, rumble, cannon, volley, and so on). |
| `refs2/` | Second pass: real WW1 and WW2 equipment by nation and weapon family (rows `A*`, `US*`, `UK*`, `DE*`, `W*`). |
| `refs3/` | Third pass: thin and empty World War rows, distant recordings first. Its README lists every search per row, and the rows that still have nothing. |
| `fetch_refs.py`, `fetch_refs2.py`, `fetch_refs3.py` | The scripts that searched for and fetched each pass. |
| `pools-2026-11-13.txt` | Dave's picks per cue, copied from the page's summary on 2026-11-13. |
| `export_pools.py` | Writes the picks into `sounds/<era>/` with each era's `manifest.json`. See below. |

Each `refs*/manifest.json` is the list the page loads. A clip on disk but missing from its manifest
does not appear.

## Saved picks

The page saves ticks and blind-test results in the browser's localStorage under `synthAudition.v2`,
and the observer switch under `synthAudition.observer`. localStorage belongs to one browser and one
address: picks made on the artifact URL do not show on `localhost:8000`, and the reverse. Use "Copy
pools" under the summary to move them, or keep them in a dated `pools-*.txt` file here.

Two maps near the top of the script keep old saves working. `RENAMED` points an old file name at its
trimmed `-t` version. `DROPPED` removes clips taken out of the pools. When you rename or remove a clip
that someone may have ticked, add it to one of these maps. Never change the storage key.

## Export the picks to the library

`export_pools.py` turns a pools file into Field Glass's sound library, in the shape
`docs/specs/battle-sound.md` sets: `sounds/<era>/<cue>-<n>.m4a` beside `sounds/<era>/manifest.json`.

```bash
cd /Users/claw/dev/gh/vauseware/field-glass/tools/sound-audition && python3 -I export_pools.py pools-2026-11-13.txt --dry-run
```

Drop `--dry-run` to write the files. To export the page's summary instead of a dated file, save it
to a file and pass `- < summary.txt`. It needs `ffmpeg` and `ffprobe`.

What it does:

- Reads the pool ids and cues from `CUES` and `WWROWS` in `index.html`, and applies `RENAMED` and
  `DROPPED` to the picked names, so old picks still resolve.
- Places each pick by its row. A World War row names its era and kit (`ww2 · us`; `both wars` means
  `great-war` and `ww2`; `fr, us` means one entry per kit). The first-pass rows in `refs/` name
  neither, so `REFS_ERAS` in the script places them. Dave accepted that mapping on 2026-11-14:
  `wind` and `hooves` go to `common`; `cannon`, `volley`, `scatter` and the `shell` and `rumble`
  synths go to `flintlock` and `percussion`; the `whistle` goes to `great-war` `bugle`; the `shell`
  and `rumble` recordings go to both World Wars; `transport` and `stuka` go to `ww2` as labelled
  stand-ins. `REFS_WW` gives those World War entries their equipment and stand-in flag.
- Prepares each take: trims silence below -50 dB off both ends, cuts it to 10 s (30 s for `air`
  and `transport`), sums to mono, levels it to -18 LUFS, fades the ends over 50 ms, and writes
  AAC at 96 kbit/s, 48 kHz. `trim`, `gainDb` and `seconds` go in the manifest entry.
- Levels with a plain gain, measured by `loudnorm`, never a limiter. When -18 LUFS would push the
  true peak over -1 dBTP, the gain stops there and the run prints `peak-capped` with the loudness
  reached. Those takes need a hand trim or Dave's ear.
- Writes a synth member as `{ "cue": "gun", "synth": "cannon" }`, named by its recipe id on the
  page. It refuses a synth in `great-war` or `ww2`, except the `wind`, which lands in `common`.
- Skips undecided pools and lists them.
- Checks each World War kit for its own `volley`, `mg` and `gun` takes, the rule `npm run check`
  will enforce.
- Prints a battle.json `"sound": { "kit": … }` block for each World War battle. It maps only side
  names that need no judgment (`american`, `us`, `british`, `german`, `french`); it lists the others
  for Dave. It does not edit battle.json.

It builds the library from scratch and stops if an era's `manifest.json` already exists. Move the
old folder aside first. `tools/build.sh` does not copy `sounds/` yet; the playback build will.

## Licences and credits

Only CC0, public domain, CC BY and CC BY-SA recordings are used. CC BY and CC BY-SA need credit
wherever the sound ships.

The licence and credit for each clip are recorded in two places in its folder:

- `manifest.json`, one entry per clip. `refs/`: `licence`, `licence_url`, `username` (author),
  `name` (original title), `url` (source page). `refs2/` and `refs3/`: `licence`, `author`, `title`,
  `page` (source page).
- `README.md`, the same entries as a table with licence links, and notes on recording date, place and
  equipment.

`refs3/sources.json` holds the raw source records from the third pass.

Sources: freesound.org (HQ MP3 previews), Wikimedia Commons, and the USC Cinema / Sunset Editorial
sound-effects collection on archive.org (CC0). An author shown as `None` is the USC library, which
names no recordist.

## Add clips

Start a new pass rather than re-running an old one. A script's `fetch` rewrites its folder's
`manifest.json` and `README.md` from its `PICKS` list, which would undo the hand trims (`-t` files)
and cuts (`1b`, `2a` files) made since.

1. Copy the latest script to the next number, for example `fetch_refs4.py`. Point `REFS` at `refs4`
   and `CANDIDATES` at `candidates4.json`, and edit `ROWS` (the searches) for the rows you need.
2. Put the freesound API key in `~/.config/freesound/api_key`. The scripts read it from there and send
   it only to freesound.org. Never put the key in this folder.
3. Run `python3 -I fetch_refs4.py search`, then `show <row>` and `info <source> <id>` to read the
   candidates. Reject anything that describes incoming fire.
4. Add the chosen clips to `PICKS` and run `python3 -I fetch_refs4.py fetch`, then `verify`. Fetch
   needs `ffmpeg` to convert originals to MP3.
5. In `index.html`, add `getRows('refs4')` to the `Promise.all` list. A new row also needs a `WWROWS`
   entry.
6. Commit the MP3s, `manifest.json` and `README.md`. `orig/` and `candidates*.json` are gitignored;
   the scripts can download them again.

To trim a clip, write the trimmed copy as `<name>-t.mp3`, change the manifest entry to the new name,
and add the old name to `RENAMED`.

## Not committed

Untrimmed originals (`refs2/orig/`, `refs3/orig/`), the search caches (`candidates*.json`) and the
run's decision log stay out of git. A copy of the whole working folder from 2026-11-13 is on the mini
at `~/Backups/field-glass-sound-audition-2026-11-14`.
