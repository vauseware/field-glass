# ADR-0009: The opening shot

**Status:** accepted, 2026-10-25

## Context

A battle opened on the first chapter's frame with the panels already up. Dave wanted it to open like a television
programme: the whole field, the title, then the camera closing in (issue #63). Three variants were rendered as
prototypes on Cowpens and Sidi Bou Zid:

- **A, slow reveal.** The whole field, still, for a second; the battle's name over its date fades in, holds and
  fades out; then the camera eases in over four seconds to the first chapter's frame. 9.2 s.
- **B, overlapped.** The same beats, with the zoom starting while the title fades out. Shorter.
- **C, push-in.** A slow push-in under the title, then the ease in. Two seconds longer than A.

## Decision

- **A.** B felt rushed on Sidi Bou Zid's map, 36 km a side, where the move from the whole field to the first
  chapter is the longest of any battle. C's push-in and its extra two seconds added nothing once the title had gone.
- **The beats run on the page's clock**, not battle time, so the opening lasts the same at every speed: field 0 s,
  title in 1.0 s for 1.2 s, held, out 4.2 s for 1 s, ease 5.2 s for 4 s, panels back over its last 1.2 s, clock
  at 9.2 s. Smoothstep over position and over the log of the zoom, so the zoom reads as a constant rate.
- **The wide frame** is the map fitted to the window's shorter side, centred, since no panel is up. **The target**
  is where Follow the action settles for the first chapter, worked out once at the start by running the follow ease
  to convergence against the panels play will show. The opening lands on the frame play uses, so the camera does not
  jump when Follow takes over.
- **A dawn cap on the night wash.** Cowpens and Sidi Bou Zid open before sunrise, and the prototype's first frame on
  Cowpens was nearly black. The wash is held at 0.35 until the ease begins, then eased to its true value with the
  camera, so the field reads under the title and the battle still opens in the dark.
- **When it runs.** Once per load: from the start screen, and on the first Play of a bare link. A link with a time
  or any flag, Play after a seek, and a replay after the end go straight to the battle. Any click, key, scroll or
  drag cuts to the landing, and the input then does what it does. Under reduced motion the field holds 1 s and the
  title 3 s, then the camera cuts.
- **State.** One `opening` object in `app.js`, or `null`, holds the elapsed seconds, the two camera frames and the
  beats; while it is set, `step()` advances it instead of the clock. The title is one DOM element whose opacity and
  scale are set from it each frame. The panels hide through one `opening` class on `<body>`, and fade back with a
  1.2 s CSS transition on `filter`, so they do not fight the caption's and the card's own opacity fades.
- **Journeys read and hold it through `window.fg`**, set only under `navigator.webdriver`. Puppeteer runs frames in
  real time, so the opening moves on between two screenshots; `fg.hold(e)` stops it at a moment, and timing checks
  read the page's own frames.

## Consequences

- The first Play on a bare link now takes 9.2 s to start the clock. A viewer who wants the battle at once presses
  any key or clicks.
- Space during the opening ends it and then pauses, since the opening has already set the battle playing.
- The opening adds no canvas work: on the laptop size the draw costs about 0.4 ms a frame at the wide frame and the
  landing, and the ease holds 60 fps.
- A resize during the opening ends it, rather than refitting both frames mid-move.
- Sound, an opening for a battle opened mid-way, and a closing shot are not built.
