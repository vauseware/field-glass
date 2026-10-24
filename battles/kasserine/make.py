# Builds battles/kasserine/battle.json. Run from the repo root: python3 battles/kasserine/make.py
# Local metres from 35.3750N 8.6400E (x east, y north), the Bahiret Foussana basin between Kasserine Pass and Thala. The 52 km
# square holds Kasserine (17845,-22954), the pass narrows (9984,-13358), Djebel Semmama and Djebel Chambi, the Thala road to
# Thala (2805,21908), the Tébessa road across the basin to Djebel el Hamra (-18145,-5210), Bou Chebka pass (-9984,-13915) and
# Haïdra (-17636,21106). Every place is kept in latitude and longitude below and converted once. Towns, the two roads and the
# Oued el Hatab come from OpenStreetMap; the summits from the Copernicus DEM. The named hills (1191, 974, 712, 704, Zebbeus, Point
# 732, the Thala ridges, the Hamra passes) are DEM knolls fitted to Howe's prose, good to a kilometre or two; see the research notes.
import json, math, datetime as dt
HERE = "battles/kasserine/"
LAT0, LON0 = 35.375, 8.640
KX, KY = 111320 * math.cos(math.radians(LAT0)), 111320  # tools/fetch_terrain.py's metres per degree
def M(lat, lon): return (round((lon - LON0) * KX), round((lat - LAT0) * KY))

D = lambda d, hm: f"1943-02-{d:02d} {hm}"
def sec(s): return dt.datetime.strptime(s, "%Y-%m-%d %H:%M").timestamp()
def fmt(ts): return dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
def K(t, p, **kw): return dict(t=t, x=p[0], y=p[1], **kw)
def hd(p, q): return round(math.degrees(math.atan2(q[0] - p[0], q[1] - p[1])) % 360)
def off(p, dx, dy): return (p[0] + dx, p[1] + dy)
def march(t0, t1, pts, **kw):  # keys along a path, times spread by distance; heading follows the path
    d = [0]
    for i in range(1, len(pts)): d.append(d[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    out = []
    for i, p in enumerate(pts):
        j = min(i + 1, len(pts) - 1); q = pts[j] if j != i else pts[i - 1]
        h = hd(p, q) if j != i else out[-1]["h"]
        out.append(K(fmt(sec(t0) + (sec(t1) - sec(t0)) * d[i] / d[-1]), p, h=h, **({"state": "column"} if i == 0 else {}), **(kw if i == 0 else {})))
    return out

# ---- terrain ----
T = json.load(open(HERE + "terrain.json"))
COLS, SP = T["cols"], T["spacing"]; HALF = COLS * SP / 2
def z(x, y):
    c, r = int((x + HALF) / SP), int((HALF - y) / SP)
    return T["z"][r * COLS + c] if 0 <= c < COLS and 0 <= r < COLS else 999

# ---- geography: places ----
PLACES = {
    # OpenStreetMap and the DEM summits
    'kasserine': (35.1688, 8.8366), 'chambi': (35.2069, 8.6813), 'semmama': (35.3309, 8.7848), 'foussana': (35.3497, 8.6256),
    'thala': (35.5718, 8.6709), 'haidra': (35.5646, 8.4457), 'fork': (35.2416, 8.7470), 'thala_rd_hatab': (35.2539, 8.7465),
    'bend': (35.3415, 8.7156),
    # DEM knolls fitted to Howe's descriptions; about a kilometre, the Hamra passes and Bou Chebka two
    'narrows': (35.255, 8.750), 'tebessa_rd_hatab': (35.2541, 8.7226), 'zebbeus': (35.2483, 8.7176), 'hill712': (35.2554, 8.7562),
    'hill704': (35.290, 8.730), 'hill974': (35.3255, 8.7308), 'hill1191': (35.277, 8.768), 'point732': (35.2986, 8.6042),
    'hamra': (35.3282, 8.4401), 'hamra_centre': (35.3405, 8.41), 'hamra_north': (35.372, 8.4625), 'bou_chebka': (35.25, 8.53),
    'ridge1': (35.4617, 8.7137), 'ridge_leic': (35.545, 8.685), 'irwin155': (35.572, 8.655), 'irwin105': (35.548, 8.672),
    # from the narrative, within a few kilometres
    'rommel_cp': (35.20, 8.80), 'dak_bivouac': (35.17, 8.75), 'se_entrance': (35.215, 8.790),
}
P = {k: M(*v) for k, v in PLACES.items()}

# ---- geography: lines (OpenStreetMap; the Tébessa road west of 8.515 E and the Haïdra track are drawn from the narrative) ----
THALA_RD = [(35.1745, 8.7943), (35.2416, 8.7470), (35.2539, 8.7465), (35.2586, 8.7482), (35.2657, 8.7452), (35.2787, 8.7392), (35.2929, 8.7375),
            (35.3059, 8.7302), (35.3200, 8.7211), (35.3415, 8.7156), (35.4617, 8.7137), (35.5718, 8.6709), (35.5890, 8.6638), (35.606, 8.655)]
TEBESSA_RD = [(35.2416, 8.7470), (35.2472, 8.7380), (35.2541, 8.7226), (35.2560, 8.7154), (35.2639, 8.7059), (35.2814, 8.6795), (35.2946, 8.6566),
              (35.3060, 8.6371), (35.3210, 8.6035), (35.3287, 8.5649), (35.3403, 8.5383), (35.3499, 8.5151), (35.372, 8.4625), (35.382, 8.358)]
HAIDRA_TRACK = [(35.5646, 8.4457), (35.47, 8.452), (35.372, 8.4625)]
BOU_CHEBKA_RD = [(35.3060, 8.6371), (35.28, 8.58), (35.25, 8.53), (35.146, 8.37)]
KASSERINE_ROADS = [[(35.1745, 8.7943), (35.1688, 8.8366), (35.18, 8.922)], [(35.1688, 8.8366), (35.142, 8.83)]]  # to Sbeïtla and to Fériana
HATAB = [(35.4202, 8.4795), (35.3542, 8.5873), (35.3174, 8.6512), (35.2697, 8.7279), (35.2539, 8.7465), (35.2392, 8.7579), (35.2289, 8.7951),
         (35.2126, 8.8371), (35.2032, 8.8696), (35.195, 8.922)]
L = lambda pts: [M(*p) for p in pts]

units = []
def unit(id, short, side, name, commander, type, strength, keys, **extra):
    units.append(dict(id=id, side=side, name=name, short=short, commander=commander, type=type, strength=strength, keys=keys, **extra))
al = lambda *a, **k: unit(a[0], a[1], "allied", *a[2:], **k)
ax = lambda *a, **k: unit(a[0], a[1], "axis", *a[2:], **k)

features = [
    dict(type="road", name="Thala road", pts=L(THALA_RD), at=list(off(P['ridge1'], 1800, 2000)), rot=-78),
    dict(type="road", name="Tébessa road", pts=L(TEBESSA_RD), at=list(off(M(35.3287, 8.5649), 0, -900)), rot=-20),
    dict(type="road", name="track from Haïdra", pts=L(HAIDRA_TRACK), at=list(off(M(35.47, 8.452), 1500, 0)), rot=-85),
    dict(type="road", name="to Bou Chebka", pts=L(BOU_CHEBKA_RD), at=list(off(P['bou_chebka'], 0, -1200)), rot=40),
    dict(type="road", pts=L(KASSERINE_ROADS[0])), dict(type="road", pts=L(KASSERINE_ROADS[1])),
    dict(type="creek", name="Oued el Hatab", pts=L(HATAB), at=list(off(M(35.2697, 8.7279), -1800, 900)), rot=-30),
    dict(name="Kasserine", at=list(off(P['kasserine'], 0, 900))), dict(name="Kasserine Pass", at=list(off(P['narrows'], 1200, 600))),
    dict(name="Bordj Chambi", at=list(off(P['fork'], 1300, -500))), dict(name="Djebel Chambi (1544)", at=list(off(P['chambi'], 0, -900))),
    dict(name="Djebel Zebbeus (812)", at=list(off(P['zebbeus'], -500, -800))), dict(name="Hill 712", at=list(off(P['hill712'], 900, 300))),
    dict(name="Hill 704", at=list(off(P['hill704'], -1100, 300))), dict(name="Hill 974", at=list(off(P['hill974'], 1000, 400))),
    dict(name="Hill 1191", at=list(off(P['hill1191'], 1000, -500))), dict(name="Djebel Semmama (1356)", at=list(off(P['semmama'], 0, 900))),
    dict(name="Bahiret Foussana", at=list(off(P['foussana'], 0, 2500))), dict(name="Foussana", at=list(off(P['foussana'], 0, 500))),
    dict(name="Point 732 (about here)", at=list(off(P['point732'], 0, -800))), dict(name="Djebel el Hamra (1112)", at=list(off(P['hamra'], 0, -1200)), rot=-80),
    dict(name="Bou Chebka pass (about here)", at=list(off(P['bou_chebka'], 0, 900))), dict(name="Thala", at=list(off(P['thala'], 0, 900))),
    dict(name="Haïdra", at=list(off(P['haidra'], 0, 900))), dict(name="to Tébessa", at=list(off(M(35.382, 8.358), 2200, 600))),
    dict(name="to Sbeïtla and Sbiba", at=list(off(M(35.18, 8.922), -2600, 600))), dict(name="to Fériana and Thélepte", at=list(off(M(35.142, 8.83), -2800, 700))),
    dict(name="to Le Kef", at=list(off(M(35.606, 8.655), -1800, -500))),
    dict(name="Rommel's CP (about here)", at=list(off(P['rommel_cp'], 0, -700)), **{"from": D(20, "11:00"), "until": D(22, "20:00")}),
]
events = []
PACE, WHEN = {}, {}

# Hold in place through long gaps: without this a unit creeps toward a key hours away and the time-lapse never engages.
# A turn in place takes its last two minutes; a move of more than three hours takes its last fifteen.
def add_holds(units):
    ts = lambda s: dt.datetime.strptime(s.replace("T", " ")[:16], "%Y-%m-%d %H:%M").timestamp()
    for u in units:
        ks, out = u["keys"], []
        for a, c in zip(ks, ks[1:] + [None]):
            out.append(a)
            if c is None or a.get("state") == "hidden": continue
            moved = (a["x"], a["y"]) != (c["x"], c["y"]); turned = "h" in c and c["h"] != next((k["h"] for k in reversed(out) if "h" in k), c["h"])
            gap = ts(c["t"]) - ts(a["t"]); lead = 900 if moved else 120
            if (moved and gap > 3 * 3600) or (turned and not moved and gap > 600):
                out.append(dict(t=dt.datetime.fromtimestamp(ts(c["t"]) - lead).strftime("%Y-%m-%d %H:%M"), x=a["x"], y=a["y"]))
        u["keys"] = out
for u in units: u["keys"] = [{k: v for k, v in key.items() if v is not None} for key in u["keys"]]
add_holds(units)
battle = dict(
    id="kasserine", name="Kasserine Pass", date="1943-02-19", dateText="19 to 23 February 1943", place="Kasserine Pass, Tunisia",
    origin=dict(lat=LAT0, lon=LON0), extent=52000, start=D(19, "06:00"), end=D(23, "07:30"), speed=300, lapse=7200, menPerDot=20,
    sunrise="07:08", sunset="18:12", terrainExaggeration=2, contourInterval=10,
    sides=dict(allied=dict(name="Allies (US II Corps, British 26th Armoured Brigade, French)", color="#1f55c4", light="#4a83e6", dark="#122c66"),
               axis=dict(name="Axis (Kampfgruppe DAK, 10th Panzer Division, Centauro)", color="#b8322a", light="#de5d50", dark="#5c1712")),
    tints=[dict(color="rgba(200,206,214,0.35)", **{"from": D(20, "06:30"), "until": D(21, "17:00")}),  # fog and rain over the battle area, 20-21 Feb
           dict(color="rgba(205,210,218,0.25)", **{"from": D(22, "07:00"), "until": D(22, "17:30")})],  # low cloud and showers, 22 Feb
    features=features, units=units,
    events=[dict(t=t, title=a, text=b, at=list(at), view=v, **({"speed": PACE[a]} if a in PACE else {}), **({"when": WHEN[a]} if a in WHEN else {})) for t, a, b, at, v in events],
    sources=[
        "George F. Howe, <i>Northwest Africa: Seizing the Initiative in the West</i> (US Army Center of Military History, 1957), chapters XXIII and XXIV: the ground, Stark Force and its reinforcements, Gore Force, the German groups, the clock times, the Thala and Djebel el Hamra fighting, the claims and the loss table for 16–24 February.",
        "Rick Atkinson, <i>An Army at Dawn</i> (2002), the Thala chapter: the 26th Armoured Brigade's tank counts, the Leicesters, Irwin's march and the night of 21–22 February.",
        "J. Rickard, 'Battle of the Kasserine Pass, 19–22 February 1943', historyofwar.org (2017): a few clock times Howe lacks, marked as his.",
        "Terrain: " + T["source"] + ". GLO-30 sampled at 100 m over a 52 km square; it is a surface model, so the modern city of Kasserine and the farms of the Foussana basin show. Roads and the Oued el Hatab from OpenStreetMap; the Tébessa road west of the basin, the track from Haïdra and the Bou Chebka road are drawn from the narrative.",
        "Clock: the times as recorded, read as a GMT+1 clock; sunrise 7:08 and sunset 18:12 are computed for 19 February on that assumption. Fog and rain covered the field on 20 and 21 February and low cloud and showers on the 22nd.",
        "What is reconstructed: the named hills (1191, 974, 712, 704, Zebbeus, Point 732, the Thala ridges, the Hamra passes, Bou Chebka pass), fitted to Howe's prose on the Copernicus DEM within a kilometre or two; every Axis tank and infantry count below the figures Howe gives (30 tanks, 20 self-propelled guns and 35 half-tracks for the 10th Panzer at Thala; eleven tanks for Gore; eight for Company I, 13th Armored); the 19th Engineers', 805th and 894th Tank Destroyers' strengths; the routes between recorded places; and the hours of the night movements of 19–20 and 20–21 February, which Howe says cannot be clearly reconstructed.",
    ],
)
json.dump(battle, open(HERE + "battle.json", "w"), indent=1, ensure_ascii=False)
print(len(units), "units (", sum(u["side"] == "allied" for u in units), "Allied,", sum(u["side"] == "axis" for u in units), "Axis ),", len(events), "events,", len(features), "features")
print("DEM at the hills:", {k: z(*P[k]) for k in ('narrows', 'zebbeus', 'hill712', 'hill704', 'hill974', 'hill1191', 'semmama', 'chambi', 'point732', 'hamra', 'bou_chebka', 'ridge1', 'ridge_leic')})
