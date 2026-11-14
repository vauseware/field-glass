# Third-party material and trademarks

[LICENSE](LICENSE) (MIT) covers Field Glass's code and its own text and images: the battle narratives and
captions, the docs and ADRs, and the screenshots. It does not cover the material below. Each item keeps its own
licence, and you must follow that licence when you copy or change it.

Each battle's `sources` in `battles/<id>/battle.json` gives the full credit line, and the app shows it in the
**Sources** dialog. Keep those lines when you fork or redistribute a battle.

## Terrain

| Data | Used in | Licence | Credit |
| --- | --- | --- | --- |
| [USGS 3DEP](https://www.usgs.gov/3d-elevation-program) elevation, 10 m | `terrain.json` for antietam, bunker-hill, cowpens, first-manassas, fort-fisher, gettysburg, guilford, kings-mountain, monmouth, new-orleans, saratoga, second-manassas, trenton-princeton, waxhaws, yorktown | Public domain (US federal government work) | "USGS 3DEP" requested, not required |
| [Copernicus GLO-30 DSM](https://registry.opendata.aws/copernicus-dem/), 30 m, via AWS Open Data | `terrain.json` for arnhem, bastogne, belleau-wood, cantigny, chippawa, kasserine, lundys-lane, omaha-beach, sidi-bou-zid, somme | Copernicus DEM licence (ESA): free use, credit required | "Produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved" (the `source` field in each `terrain.json`) |

`tools/fetch_terrain.py` writes the credit into `terrain.json`. A battle that uses Copernicus terrain must repeat
it in its `sources`.

## Map data

| Data | Used in | Licence | Credit |
| --- | --- | --- | --- |
| [OpenStreetMap](https://www.openstreetmap.org/copyright) positions of monuments, roads, churches, bridges and other landmarks | `battle.json` for every battle except bunker-hill, cowpens and trenton-princeton | [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) | "© OpenStreetMap contributors" |
| National Library of Scotland, [British First World War Trench Maps](https://maps.nls.uk/ww1/trenches/), sheets 57D.SE and 62D.NE (1916) | front lines in `battles/somme/battle.json` | CC BY, as NLS publishes them | "National Library of Scotland" |
| National Park Service maps, markers and tour stops | positions in many US battles | Public domain where the work is by the US government | As each battle's `sources` gives it |

Field Glass takes a few dozen OSM positions per battle and redraws them, which we read as an insubstantial
extract under the ODbL. If you build a larger database from OSM, the ODbL share-alike terms apply to it.

## Cited sources

Each battle also cites books, official histories, Wikipedia and the Historical Marker Database for facts: times,
strengths, orders of battle and marker positions. Field Glass states those facts in its own words and does not
intend to reproduce their text. Wikipedia text is CC BY-SA 4.0; if you find any copied into a caption, open an
issue.

## Fonts

The page loads these fonts from [Google Fonts](https://fonts.google.com) at runtime. None are stored in this
repo. All are under the [SIL Open Font License 1.1](https://openfontlicense.org).

Archivo Narrow, Cardo, Courier Prime, Crimson Pro, IM Fell DW Pica, IM Fell English, IM Fell English SC,
Old Standard TT, Oswald, Playfair Display SC, Stardos Stencil.

## Sound

The repo holds no sound files yet. [docs/specs/battle-sound.md](docs/specs/battle-sound.md) allows only CC0,
public domain, CC BY and CC BY-SA clips, from freesound, Wikimedia Commons and the USC collection on archive.org.
Each clip added must get a row here before it merges:

| File | Title | Author | Source URL | Licence | Changes |
| --- | --- | --- | --- | --- | --- |

A clip under CC BY-SA stays CC BY-SA after editing, and so does any mix built from it. Keep such mixes in their own
files, not inside MIT code.

## Trademarks

These are not licensed under MIT or any other licence in this repo. You may use the names to say truthfully what a
fork is based on, but not to brand a fork or imply endorsement.

| Mark | Owner | Files |
| --- | --- | --- |
| Field Glass name and its field-glass icon | Dave Vause | `favicon.svg`, `apple-touch-icon.png` |
| Vauseware and Vause Consulting names and logos | Vause Consulting | None in this repo |

A fork that ships publicly should replace `favicon.svg` and `apple-touch-icon.png` and use another name.
