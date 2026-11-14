# Contributing to Field Glass

Thanks for helping. Field Glass replays historical battles from the written record, so accuracy comes first:
nothing is simulated that would change the outcome ([ADR-0001](docs/adr/0001-replay-not-simulation.md)).

## Before you start

- Open an issue first for anything larger than a small fix, so we can agree on the approach.
- Read the [README](README.md) for the data format and how the app fits together, and the
  [ADRs](docs/adr/) for why it works the way it does.
- The app is for laptops and desktops. Phones are out of scope ([ADR-0012](docs/adr/0012-phones-out-of-scope.md)).
- No framework, bundler or build step for the page: vanilla JS and Canvas 2D.
- A new battle is data under `battles/<id>/`, written by its `make.py`. Don't add engine features for one battle.

## Run it

You need Python 3 to serve the page and Node to run the checks.

```
npm run serve      # python3 -m http.server 8000
```

Then open http://localhost:8000/#cowpens. `file://` won't work; the page fetches its battle files.

## Check it

```
npm run check
```

This validates every battle, self-checks `sim.js` and rewrites `battles/index.json` with each battle's running
time. Commit `battles/index.json` if it changes. A PR must pass it.

For a change you can see, open the affected battles in a browser and check them at the default settings (Follow
and Time-lapse on). Add a desktop screenshot to the PR. The README lists URL flags that help: `#cowpens@07:45`
opens a battle at a time, `,warp` pre-runs a few seconds of frames, `,legend` opens the legend.

## Add or change a battle

Follow **Add a battle** in the README. Every fact needs a source in the battle's `sources`. Terrain and map data
carry licences of their own: keep their credit lines, and see [THIRD_PARTY.md](THIRD_PARTY.md). Don't add sound,
images or data unless their licence allows it, and list each one in THIRD_PARTY.md in the same PR.

## Pull requests

- One topic per PR. Branch from `main`, named `<type>/<short-desc>` (`feat/`, `fix/`, `docs/`, `chore/`).
- Use [Conventional Commits](https://www.conventionalcommits.org) style messages: `fix(app): ...`.
- Write an ADR in `docs/adr/` for any decision the code can't explain on its own.
- Sign off every commit (see below).

## Developer Certificate of Origin

Field Glass uses the [Developer Certificate of Origin](https://developercertificate.org) (DCO) instead of a CLA.
You keep the copyright in your work and license it under the project's [MIT licence](LICENSE). By signing off a
commit you certify the DCO below for that commit.

Sign off with `git commit -s`, which adds a line with your name and email:

```
Signed-off-by: Your Name <you@example.com>
```

Use your real name, or the name you are known by. The email must match the commit author. To sign off commits you
already made on a branch, run `git rebase --signoff main` and push the branch again.

```
Developer Certificate of Origin
Version 1.1

Copyright (C) 2004, 2006 The Linux Foundation and its contributors.

Everyone is permitted to copy and distribute verbatim copies of this
license document, but changing it is not allowed.


Developer's Certificate of Origin 1.1

By making a contribution to this project, I certify that:

(a) The contribution was created in whole or in part by me and I
    have the right to submit it under the open source license
    indicated in the file; or

(b) The contribution is based upon previous work that, to the best
    of my knowledge, is covered under an appropriate open source
    license and I have the right under that license to submit that
    work with modifications, whether created in whole or in part
    by me, under the same open source license (unless I am
    permitted to submit under a different license), as indicated
    in the file; or

(c) The contribution was provided directly to me by some other
    person who certified (a), (b) or (c) and I have not modified
    it.

(d) I understand and agree that this project and the contribution
    are public and that a record of the contribution (including all
    personal information I submit with it, including my sign-off) is
    maintained indefinitely and may be redistributed consistent with
    this project or the open source license(s) involved.
```

## Conduct and security

Everyone taking part follows the [Code of Conduct](CODE_OF_CONDUCT.md). Report security problems privately, as
[SECURITY.md](SECURITY.md) describes, not in a public issue.
