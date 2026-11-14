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

Each `refs*/manifest.json` is the list the page loads. A clip on disk but missing from its manifest
does not appear.

## Saved picks

The page saves ticks and blind-test results in the browser's localStorage under `synthAudition.v2`,
and the observer switch under `synthAudition.observer`. localStorage belongs to one browser and one
address: picks made on the artifact URL do not show on `localhost:8000`, and the reverse. To move
them, use "Save picks" under the summary: it downloads `synth-audition-picks-<date>.json`, the saved
object as is. "Load picks" reads such a file on the other address. By default it merges: each sound
in the file replaces that sound's picks and score, and other sounds stay. Tick "Replace instead of
merge" to clear every pick first. On claude.ai the page saves through the artifact's `downloads`
capability, so the viewer confirms each save. "Copy pools" still copies the summary as text, for a
dated `pools-*.txt` file here.

Two maps near the top of the script keep old saves working, on page load and on Load picks.
`RENAMED` points an old file name at its trimmed `-t` version. `DROPPED` removes clips taken out of the
pools. When you rename or remove a clip that someone may have ticked, add it to one of these maps. Never change the storage key.

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
