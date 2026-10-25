# Opening shot

A battle started from its beginning opens on the whole map with every unit in its starting place and no panels, bar or chapter labels. The battle's name over its date fades in, holds and fades out. The camera then eases in over four seconds to the frame Follow the action gives the first chapter, the panels fade back as it settles, and only then does the clock start. A battle that opens before sunrise keeps its night wash at a dawn level until the ease begins.

## Sub-features

- `os-start` runs the opening when a battle is chosen on the start screen, and on the first Play of a bare link such as `#cowpens`.
- `os-not` skips it for a link with a time or a flag (`#cowpens@07:45`, `,play`, `,warp`), for Play after a seek, and for a replay after the end. It runs once per load.
- `os-skip` ends it on any click, key, scroll or drag: the camera cuts to the landing, the page comes back, and the input then does what it does.
- `os-still` under `prefers-reduced-motion: reduce` holds the field 1 s and the title 3 s, then cuts to the landing with no ease.
- `os-dawn` caps the night wash at 0.35 until the ease begins, then lets it reach its true value by the landing.
- `os-dress` dresses the title per skin under `body.theme-<id> #opening`.
- `os-link` holds the opening at its title for a screenshot: `#cowpens,opening`.

## How to get to it (user POV)

- Choose a battle on the start screen.
- Open `#cowpens` and press Play or Space.

## Driving it with fg.sh

Preconditions:

- The baseline from `README.md` holds.

- **Whole journey.** Run `bash .claude/skills/verify-field-glass/fg.sh drive <dir> .claude/skills/verify-field-glass/journeys/opening.cjs [ids] [clip]`. Every line is `PASS`. `<dir>/opening-<id>-field.png`, `-title.png` and `-landing.png` show the three beats at 1536x830, and `opening-<first id>-title-phone.png` the title at 390x844. With `clip`, `<dir>/clip/f000.jpg` to `f150.jpg` are 15 fps frames of the first battle's opening; `ffmpeg -framerate 15 -i <dir>/clip/f%03d.jpg -pix_fmt yuv420p out.mp4` makes the clip.
- **Title still.** Run `fg.sh shot <dir> '#sidi-bou-zid,opening' sbz-title 1536 830`. The map fills the window's height with no panels, and "SIDI BOU ZID" sits over "14 TO 17 FEBRUARY 1943" on a dark band.
- **State.** Under puppeteer, `navigator.webdriver` is true and the page exposes `window.fg`: `fg.state()` returns `{ cam, t, playing, follow, opening }`, where `opening` is `{ e, wide, target }` or `null`, and `fg.hold(e)` holds a running opening at `e` seconds.

## Gotchas

- This mini has Reduce motion on (`defaults read com.apple.universalaccess reduceMotion` prints 1), so headless Chrome reports `prefers-reduced-motion: reduce` and runs the still opening unless a journey calls `page.emulateMediaFeatures` with `no-preference`.
- `requestAnimationFrame` runs in real time under puppeteer, so the opening moves on between two screenshots. Read `fg.state()` in the same `evaluate` as what you check against it, or hold it with `fg.hold(e)`.
- `fg.hold` stops the opening's clock, not the panels' 1.2 s CSS fade. To hold that too, pause `document.getAnimations()` and set their `currentTime`, as the journey's clip does.
- The first Play on a bare link now runs the opening, so a check that Play moves the clock waits for `#opening` to hide first.
