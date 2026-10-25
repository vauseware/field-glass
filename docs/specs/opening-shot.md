# The opening shot

**Status:** draft. Issue #63.

## Why

A battle opens today on the first chapter's frame with the panels already up. Dave wants it to open like a
television programme: the whole field, the title, then the camera closing in.

## What the viewer sees

When a battle starts from its beginning, the page shows the whole map filling the window with every unit in
its starting place, and nothing else: no panels, no bar, no chapter labels. The battle's name and date fade in
over the field, hold, and fade out. The camera then eases in, over four seconds, to the frame "Follow the
action" would give the first chapter. The panels, bar and labels fade back as the camera settles, and the
battle plays. The clock does not move until the camera has landed.

Dave picked this from three rendered prototypes (A, slow reveal). B overlapped the zoom with the title's
exit and felt rushed on a 52 km map; C added a slow push-in under the title and two more seconds that gave
nothing once the title had gone.

## The beats

Measured on the page's clock, not battle time, so the opening lasts the same at every speed.

| beat | from | for | what |
|---|---|---|---|
| field | 0.0 s | 1.0 s | the whole map, still |
| title in | 1.0 s | 1.2 s | the title fades up |
| title | 2.2 s | 2.0 s | held |
| title out | 4.2 s | 1.0 s | the title fades away |
| ease in | 5.2 s | 4.0 s | the camera closes in, smoothstep |
| page in | 8.0 s | 1.2 s | panels, bar and labels fade back, over the ease's last 1.2 s |
| play | 9.2 s | | the clock starts |

- **The wide frame.** The map centred and fitted to the window's shorter side (`Math.min(W, H) / extent`),
  as the page frames a battle with no `view` today. It is the whole field, not the clear rect, since no
  panel is up.
- **The target.** Wherever `updateCamera` would settle for the first chapter, computed once at the start
  (run the follow ease to convergence against the start-time action box), so the opening lands exactly on
  the frame play would use and the camera does not move again when follow takes over.
- **The ease.** Smoothstep (`u * u * (3 - 2 * u)`) over position, and over the log of the zoom so the
  zoom reads as a constant rate. One continuous move, no steps.
- **The title.** The battle's name over its date, centred, slightly above the middle (46% down). The same
  dress family as the chapter titles (`docs/specs/chapter-titles.md`): the skin's display face at about
  64 px over a 24 px italic date, on a soft band of the skin's paper. It scales from 1.03 to 1.00 over its
  life, a drift the eye feels more than sees. Each skin dresses it under `body.theme-<id> #opening`.
- **Night.** A battle that opens before sunrise (Cowpens, Sidi Bou Zid) draws its night wash from the
  start, and the prototype's first frame on Cowpens was nearly black. The opening holds the wash at a
  dawn level (`dark` capped at 0.35) until the ease begins, then lets it reach its true value over the ease,
  so the field reads under the title and the battle still opens in the dark.

## When it runs

| start | opening |
|---|---|
| a battle chosen on the start screen | runs |
| Play pressed with the clock at the battle's start | runs |
| a bare `#cowpens` link | runs, on the first Play |
| a link to a later time (`#cowpens@07:45`) | does not run |
| Play after a seek, or a replay after the end | does not run |
| `,warp` and other screenshot links | does not run |
| `prefers-reduced-motion: reduce` | the beats run with no ease: field 1 s, title 3 s, cut to the target |

It runs once per load. Any click, key, scroll or drag during it ends it: the camera cuts to the target, the
page comes back, and the input is then handled as normal. Space, Play and the scrubber included.

## Data shape

- One `opening` object in `app.js`, or `null`: `{ e, wide, target }`, the elapsed seconds and the two
  camera frames. While it is set, `step()` advances `e` instead of the clock and sets `cam` from it;
  `updateCamera` does not run.
- One `#opening` element in `index.html` beside `#caption`, hidden when idle. Its opacity and transform are
  set from `e` each frame, so there is no CSS timeline to keep in step with the camera.
- The page's own panels hide through one class on `<body>`, `opening`, that sets their opacity and
  `pointer-events`; their fade back is the class's removal with a CSS transition of 1.2 s.
- A `,title` style flag is not needed: `,opening` on a screenshot link runs the opening and holds at the
  title beat for the shot.

## Performance

The opening adds no canvas work: the map draws as it does at any zoom, and the title is a DOM element. The
whole-field frame at Sidi Bou Zid (52 km) is the page's most zoomed-out draw; it is what the start screen
draws already, so no new cost. Check the ease stays at full frame rate in `tools/bench.sh` at the laptop
size before shipping; a stutter would spoil the move.

## Verification

A journey `.claude/skills/verify-field-glass/journeys/opening.cjs`:

1. From the start screen, choose Cowpens: the panels are hidden, `cam.zoom` equals the wide frame, the
   clock reads the start time and does not advance for 9 s.
2. At 3 s the title's opacity is above 0.95 and its text is the battle's name; at 5.5 s it is 0.
3. At 9.2 s `cam` equals the follow target within a pixel, the panels are visible, and the clock advances.
4. `#cowpens@07:45` opens with no opening; Play after a seek starts no opening.
5. A click at 2 s ends the opening: the next frame has `cam` at the target and the panels visible.
6. Under reduced motion the camera never takes an intermediate value.
7. The first frame on Cowpens is not black: mean luminance of the map area above a floor.
8. `laptop.cjs` passes at both laptop sizes.

Shots for the PR: the field, the title and the landing on one Revolution battle and Sidi Bou Zid at
1536x830, and the title on a phone. A clip from the journey's frames for the PR body.

## Out of scope

- Sound.
- An opening for a battle opened mid-way.
- A closing shot at the battle's end.
