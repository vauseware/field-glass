# ADR-0012: Phones are out of scope until a phone layout is planned

**Status:** accepted, 2026-11-08

## Context

Field Glass is a gift for Dave's father, who watches it on a laptop or desktop. The page was built desktop first,
and every feature since has also been fitted to a 390 x 844 phone: the chapter labels hide there (ADR-0010), the
start screen's timeline turns into buttons (ADR-0005, ADR-0007), the story panel docks above the bar, and the
journeys, skills and PRs carry a phone viewport and a phone screenshot. Each new feature pays that cost again.
Battle sound (`docs/specs/battle-sound.md`) and chapter narration (issue #88) aim for immersion on desktop, and a
phone would need its own design for them, not a squeezed copy.

A phone that works well needs its own layout: a different bar, panels and touch controls. That is not on the
roadmap for Christmas 2026.

## Decision

- **Phones are out of scope.** New work is designed, built and tested for desktop and laptop only. Specs, issues
  and ADRs leave phones out rather than settling how a feature behaves on one.
- **No phone tests.** Journeys drop their phone viewports. Battle PRs, skins and UI PRs need desktop screenshots
  only (1536 x 830, and 1280 x 700 where the laptop fit matters), with no phone shot.
- **One exception: the desktop banner** (issue #90). A phone visitor sees a banner suggesting a desktop or laptop,
  with a button to continue anyway. Its journey checks that it shows and hides at 390 x 844, and never shows at
  1536 x 830. Nothing else is checked on a phone.
- **The phone code stays as it is.** The page's existing phone rules (narrow-width CSS, the hidden chapter labels,
  the story panel docked above the bar) are not removed and not maintained. A change may break them; nobody checks.
- **Later.** A phone layout is its own project, with its own spec, after Christmas. It starts by deciding which of
  the current phone rules to keep.

## Consequences

- Features ship faster: no second layout to fit or screenshot.
- A phone viewer may meet broken or cramped pages until the phone layout ships; the banner tells them why.
- The global instruction to add a phone screenshot to UI PRs does not apply to this repo while this ADR stands.
- ADR-0005, ADR-0007 and ADR-0010 still describe how the page behaves on a phone today; they bind no new work there.
