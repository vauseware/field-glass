# Screenshot links

A battle link can open a battle at a set moment and state, which is how README images, PR screenshots and data checks are made. The hash is `#<battle>[@<time>][,play][,select=<unit id>][,warp][,title][,legend][,outcome][,opening][,bench]`, with the flags in that order. Once the battle loads, the hash settles to `#<battle>` without a reload.

## Sub-features

- `sl-time` opens at `@HH:MM`, or `@YYYY-MM-DDTHH:MM` for a battle spanning days.
- `sl-play` starts playing with the drawer closed. Without it the drawer opens.
- `sl-select` opens the unit card on one unit.
- `sl-warp` runs 300 frames at load so the camera, smoke and caption have settled for a still frame, and turns off the caption fades. It never shows the chapter title.
- `sl-title`, after `,warp`, holds the chapter title at full opacity, to show its place and its skin's dress.
- `sl-legend` and `sl-outcome` open the Legend dialog, or the drawer with Outcome open.
- `sl-opening` runs the opening shot and holds it at the title: the whole map, no panels, the battle's name over its date.
- `sl-war` opens a war's start screen with `#revolution`, `#civil-war` or `#ww2`, with an optional `?plan=<battle id>` to fix the Revolution backdrop.

## How to get to it (user POV)

- Paste or open a link with the hash. The README's images are made this way.

## Driving it with fg.sh

Preconditions:

- The baseline from `README.md` holds.

- **Still frame.** Run `bash .claude/skills/verify-field-glass/fg.sh shot <dir> '#cowpens@07:30,play,warp' cowpens-0730`. `<dir>/cowpens-0730.png` shows the clock at `7:30`, the caption "The main line", the Pause button, and the units engaged.
- **Unit card.** Run `fg.sh shot <dir> '#cowpens@07:30,play,select=<unit id>,warp' cowpens-card`, using a unit id from `battles/cowpens/battle.json`. `#card` shows that unit's name beside it.
- **Legend.** Run `fg.sh shot <dir> '#sidi-bou-zid@1943-02-14T10:00,warp,legend' sbz-legend`. The Legend dialog is open over the WW2 skin, and the clock behind it reads `1000 HRS 14 FEB`.
- **Chapter title.** Run `fg.sh shot <dir> '#cowpens@07:31,play,warp,title' cowpens-title 1536 830`. "The main line" sits just above the caption strip on its paper band.
- **Settles.** In a journey, load `#cowpens@10:00,play,warp`, set `window.mark = 1`, and wait. `location.hash` becomes `#cowpens` and `window.mark` is still `1`, so the page did not reload.

## Gotchas

- Without `warp`, `shot.sh` captures the first frame: the camera hasn't eased and the captions are half faded, because its virtual time does not run requestAnimationFrame.
- Quote the hash in the shell, or `#` starts a comment.
- Never put a space in a dated time. The browser sends it as `%20`, the time fails to parse, and the battle opens at its end with a black map and no dialog. Use `T`: `@1943-02-14T10:00`.
- A time outside the battle is clamped to its start or end.
- `bench` loads `tools/bench.js` and logs per-frame draw cost. It is for `tools/bench.sh`, not proof of behavior.
