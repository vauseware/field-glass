---
name: war-skin
description: Design and build a Field Glass skin for a war (three rendered options, Dave picks one, then full skin, start-screen entry, ADR). Prefer /poteto-mode on Cursor. Use when a war needs its own look, or a skin needs redesigning.
---

# War skin

## Run under poteto (Cursor)

Drive this skill with **`/poteto-mode`**. Do not spin a Claude agent fleet for the three options.

| Phase | Poteto playbook | pstack skills poteto would pull |
| --- | --- | --- |
| Three options | **Prototype** (or Feature with **Exhaust the Design Space**); bakeoff → **arena** | `how` on `themes.js` / newest skin; three thin skins via `poteto-agent` or arena runners; shoot with **verify-field-glass** / `shoot-skins.cjs` |
| Dave picks | pause (preference only he can make) | show the nine PNGs in chat; recommend one; wait for his choice |
| Build the chosen skin | **Feature** | `architect` if layout/`WARS`/`YEARS` wiring forks; `poteto-agent` for the module + CSS + ADR; verify with **verify-field-glass**; **Opening a PR** |
| After merge babysit | **Babysit** then **Shipping** if asked to land | as poteto names |

## Contract

A skin is one module in `themes/` plus CSS in `index.html`. Its contract is the comment at the top of `themes.js`. Read that, `docs/adr/0002-per-war-skins.md` (the rules: each war wears the dress of its own maps; static drawing is baked into the layer; ambient motion is CSS page layers, never canvas), and the newest skin ADR (`docs/adr/0008-first-world-war-skin.md`).

Dave judges a look only by seeing it rendered. Never ask him to pick from a description.

## 1. Three options

1. Work in a fresh git worktree off `origin/main`. Another agent may own the main checkout.
2. Pick three directions from real map traditions of the war, each a different kind of artifact (a printed sheet, a hand-marked staff map, an artist's view). Each must look unlike every other war's skin: the 1812 pen-and-wash lost for being too close to the Revolution plate, and the WWI situation map for being too close to the WWII table.
3. Write each as `themes/<war>-<option>.js`, register it in `THEMES`, and add a `body.theme-<war>-<option>` CSS block. Speed over polish. Copy the structure of the newest complete skin. If you spread another skin (`...revolution`), override its `legend.swatch` entries too: Revolution's woods swatch reads `sheet.stamps` and crashes any skin without them.
4. `surround` paints only the four margins outside the map rect. Filling the whole window covers the map.
5. Shoot them: `bash .claude/skills/verify-field-glass/fg.sh drive <dir> .claude/skills/war-skin/shoot-skins.cjs <id> <id> <id>`. It previews each on Guilford (hills and woods), Fort Fisher (flat coast, works, ships) and Yorktown at night, at the laptop size, and fails on any page error. A shot stuck on "Loading…" is a page error. Look at every PNG: marks that are faint on Guilford's slopes or vanish on Fort Fisher's flat ground need retuning before Dave sees them.
6. Show the nine shots in chat, captioned in option order (Cursor: attach or Read the PNG paths; Claude Code: SendUserFile). Describe each in a few lines, give the tradeoffs, and recommend one.

## 2. Build the chosen one

Rename it to `themes/<war id>.js` with the id the war uses in `WARS` (`splash.js`), delete the other two and their CSS, and finish it:

- A complete skin with no spread: its own `clock` and `hours` in the period's style, `fallen` marks unlike its other marks, `legend` text and swatches for everything it draws, `preview(b)` recolouring the sides, `night`, `ambient`.
- Export `ground(b, T)` and the colours the start screen needs; `build` uses `ground`.
- Add the war's years to `YEARS` in `themes.js`.
- In `WARS`, give the war a `draw` backdrop built from `ground`, and a `sample` battle until it has one of its own. Add `#splash.war-<id>` CSS for its card and timeline, and its fonts to the start screen's font link. Five wars fit the timeline's two rows; a sixth needs a layout check.
- `docs/adr/00NN-<war>-skin.md`: the three options, why the winner won and why each loser lost, and what is deferred.
- README: the skin paragraph, the `theme` row, the war ids; a screenshot in `docs/screenshots/<id>-<battle>.jpg`.

## 3. Verify and ship

- `npm run check`; `start-screen.cjs`; `shoot-skins.cjs <id>`; the start screen on `#<id>` at 1536x830 and 390x844.
- Then follow `.claude/skills/verify-field-glass/SKILL.md` and open the PR with desktop and phone shots via `bash ~/bin/pr-shot.sh`.
