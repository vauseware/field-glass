# Start screen

The start screen shows one war at a time. A bar along the foot rules the years 1770 to 1950 with a button per war, giving its name, years and battle count. Each war has its own card and map behind it: a sepia battle plan for the Revolution, a survey sheet for the Civil War, and a recon mosaic for the Second World War. A war with no battles shows an "in preparation" card with buttons to the other wars. Choosing a battle opens it and starts it playing.

## Sub-features

- `ss-default` opens the American Revolution from a bare URL.
- `ss-war` switches card, backdrop and URL hash when a timeline button is chosen, without adding history entries.
- `ss-empty` shows the in-preparation card for a war with no battles, with buttons to the other wars.
- `ss-open` opens a battle from its row and starts it playing, after the opening shot, without reloading the page.
- `ss-home` takes All battles back to the war the battle belongs to, and Back returns to the battle.
- `ss-link` opens a war directly from `#revolution`, `#civil-war` or `#ww2`.

## How to get to it (user POV)

- Open the site with no hash.
- Open a war link: `#revolution`, `#civil-war`, `#ww2`.
- Press `☰ All battles` (`#home`) in a battle's top panel.
- Press the browser's Back button from a battle opened from the list.

## Driving it with fg.sh

Preconditions:

- The baseline from `README.md` holds.

- **Whole journey.** Run `bash .claude/skills/verify-field-glass/fg.sh drive <dir> .claude/skills/verify-field-glass/journeys/start-screen.cjs`. Every line is `PASS`, and `<dir>/start-screen-1-bare.png` through `-5-all-battles.png` show each step.
- **Default war.** Load the bare URL. `#splash` is visible with class `war-revolution`, `.tl-war[data-war="revolution"]` has `aria-pressed="true"`, and the `.row` count equals the Revolution battles in `battles/index.json`.
- **Switch war.** Click `.tl-war[data-war="ww2"]`. The hash is `#ww2`, `#splash` has class `war-ww2`, `.tag` names the Second World War, and `history.length` is unchanged.
- **Empty war.** Click `.tl-war[data-war="civil-war"]`. While no Civil War battle exists, `.empty` is present with `.go button[data-war]` links and there are no `.row`s.
- **Open battle.** Click `.row[data-id="sidi-bou-zid"]`. `#splash` hides, the hash starts `#sidi-bou-zid`, `body` has `theme-ww2`, and `#play`'s `aria-label` is `Pause`.
- **All battles.** From `#sidi-bou-zid`, click `#home`. The page reloads on `#ww2` showing the WW2 card. Press Back and the battle returns.

## Gotchas

- Backdrops are drawn after the card, and WW2 and Civil War take a moment the first time. Wait for network idle before a screenshot, or the backdrop may be blank.
- The Revolution backdrop picks a random battle. Add `?plan=<battle id>` before the hash (for example `?plan=cowpens#revolution`) for a repeatable screenshot.
- All battles is a real page load. Wait for the `load` event, not a hash change.
- Once the first Civil War battle lands, `ss-empty` no longer applies to it. The journey's Civil War check accepts either a list or the empty card.
