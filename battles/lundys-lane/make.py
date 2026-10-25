# Builds battles/lundys-lane/battle.json and fits terrain.json to 1814. Run from the repo root: python3 battles/lundys-lane/make.py
# Local metres from 43.0730N 79.0740W (x east, y north). The 6 km square holds the hill at Lundy's Lane with its church
# and graveyard, the lane west toward DeCew's Falls, the Portage road from the King's Bridge over the Chippawa past
# Bridgewater mills, the Falls and Table Rock to the junction and on north toward Queenston, and the Niagara from the
# Chippawa's mouth over the Falls into the gorge. Every place is kept in latitude and longitude, or in the research
# note's local metres where the note derives it (N below), and converted once. Anchors are OpenStreetMap points and the
# Ontario plaque. Mrs. Wilson's tavern, the hollow, the log fence, Skinner's lane, Jesup's track and the woods are placed
# from Cruikshank's description and labelled "about here". The King's Bridge and the river road south of it are
# Chippawa's (battles/chippawa/make.py), converted from that note's frame.
# Strengths are Graves's brigade totals as Wikipedia gives them, split by the research note; Porter's is his own figure.
import json, math, re, datetime as dt
HERE = "battles/lundys-lane/"
LAT0, LON0 = 43.0730, -79.0740
KX, KY = 111320 * math.cos(math.radians(LAT0)), 111320  # tools/fetch_terrain.py's metres per degree
def M(lat, lon): return (round((lon - LON0) * KX), round((lat - LAT0) * KY))
def N(x, y): return (LAT0 + y / KY, LON0 + x / KX)  # a place the note gives in its metres, which are M's
CH_LAT0, CH_LON0, R_CH = 43.0545, -79.0360, 6371009 * math.pi / 180  # the Chippawa note's frame
def NC(x, y): return (CH_LAT0 + y / R_CH, CH_LON0 + x / (R_CH * math.cos(math.radians(CH_LAT0))))

# ---- plane geometry ----
def unit(v): L = math.hypot(*v); return (v[0] / L, v[1] / L)
def heading(a, b): return round(math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) % 360)
def seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]; t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)))
    return math.dist(p, (a[0] + t * dx, a[1] + t * dy))
def point(pts, s):  # the point s metres along a polyline
    for a, b in zip(pts, pts[1:]):
        L = math.dist(a, b)
        if s <= L or b is pts[-1]: t = unit((b[0] - a[0], b[1] - a[1])); return (a[0] + t[0] * s, a[1] + t[1] * s)
        s -= L
def proj(pts, p):  # how far along a polyline its nearest point to p is
    best, run = None, 0
    for a, b in zip(pts, pts[1:]):
        L = math.dist(a, b); f = max(0, min(1, ((p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1])) / (L * L)))
        d = math.dist(p, (a[0] + f * (b[0] - a[0]), a[1] + f * (b[1] - a[1])))
        if best is None or d < best[0]: best = (d, run + f * L)
        run += L
    return best[1]
def stretch(pts, a, b):  # the part of a polyline between the points on it nearest a and b, in that order
    s0, s1 = proj(pts, a), proj(pts, b); lo, hi = min(s0, s1), max(s0, s1); out, run = [point(pts, lo)], 0
    for p, q in zip(pts, pts[1:]):
        run += math.dist(p, q)
        if lo < run < hi: out.append(q)
    out.append(point(pts, hi))
    out = [(round(x), round(y)) for x, y in out]
    return out if s0 <= s1 else out[::-1]
def quad(x0, y0, x1, y1): return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
def label_on(p, q, off=0):  # a label rotated along the line p-q at p, `off` metres to its left
    t = unit((q[0] - p[0], q[1] - p[1])); return dict(at=[round(p[0] - t[1] * off), round(p[1] + t[0] * off)], rot=round(math.degrees(math.atan2(t[1], t[0]))))

# ---- places ----
PLACES = {
    # OpenStreetMap and the Ontario plaque
    'graveyard': (43.08863, -79.09532), 'church': (43.08910, -79.09623), 'plaque': (43.08920, -79.09582),
    'junction': (43.08950, -79.09273), 'lane_drummond': (43.08931, -79.09804), 'lane_dorchester': (43.08914, -79.11076),
    'museum': (43.08934, -79.09136), 'horseshoe': (43.07832, -79.07447), 'horseshoe_w': (43.07714, -79.07588),
    'american_falls': (43.08577, -79.07014), 'mills': (43.07116, -79.07283), 'cummington': (43.05923, -79.05096),
    'kingsbridge_park': (43.06364, -79.04955), 'table_rock': (43.07900, -79.07850),
    # from the note's text, within 60 to 250 m
    'guns': N(-1740, 1770), 'wilson': N(-650, 760), 'hollow': N(-1400, 1400), 'kings_bridge': NC(-950, 850),
}
P = {k: M(*v) for k, v in PLACES.items()}

# ---- terrain: the 1814 ground ----
# The Copernicus surface model reads today's city as hills: the Fallsview hotels and the casino stand 15 to 35 m over
# the plain, and the cemetery's trees, the church and the monument sit on the knoll. Each land cell is set to the
# highest of the lowest values within 80 m of it (an opening, which removes anything narrower than 170 m and keeps the
# broad ground) and then averaged over 70 m. That leaves the knoll about 212 m at the graveyard, falling 13 m in 300 m to
# the north and 10 m in 400 m to the south, 4 to 7 m over the lane to the west: the shape Cruikshank gives it. The water
# is left as fetched. The fit runs once on the fetched grid and marks it `fitted`; to change it, fetch again.
WATER = 170.5  # the Niagara above the Falls reads 158 to 170 m, the gorge 96 to 100; the plain 175 and up
T = json.load(open(HERE + "terrain.json"))
COLS, SP = T["cols"], T["spacing"]; HALF = COLS * SP / 2
if not T.get("fitted"):
    def filt(a, R, f):  # f over a square 2R+1 cells across, of the cells that are not None; separable
        tmp, out = list(a), list(a)
        for r in range(COLS):
            row = a[r * COLS:(r + 1) * COLS]
            for c in range(COLS):
                v = [x for x in row[max(0, c - R):c + R + 1] if x is not None]; tmp[r * COLS + c] = f(v) if v else None
        for c in range(COLS):
            col = tmp[c::COLS]
            for r in range(COLS):
                v = [x for x in col[max(0, r - R):r + R + 1] if x is not None]; out[r * COLS + c] = f(v) if v else None
        return out
    land = [v if v > WATER else None for v in T["z"]]
    opened = filt(filt(land, 8, min), 8, max)
    opened = [None if l is None else (o if o is not None else l) for l, o in zip(land, opened)]
    smooth = filt(opened, 3, lambda v: sum(v) / len(v))
    T["z"] = [v if l is None else max(0.1, round(s, 2)) for v, l, s in zip(T["z"], land, smooth)]
    T["fitted"] = "land opened over 170 m and averaged over 70 m (battles/lundys-lane/make.py)"
    json.dump(T, open(HERE + "terrain.json", "w"), separators=(",", ":"))
def z(p):
    c, r = int((p[0] + HALF) / SP), int((HALF - p[1]) / SP)
    return T["z"][r * COLS + c] if 0 <= c < COLS and 0 <= r < COLS else 999

# ---- lines ----
J = P['junction']
BR_S = M(*NC(-950, 850)); BR_N = (BR_S[0] - 10, BR_S[1] + 120)  # the King's Bridge, as Chippawa draws it
BRIDGES = [(BR_S, BR_N)]  # dry over water
def wet(p): return z(p) <= WATER and not any(seg_dist(p, a, b) < 15 for a, b in BRIDGES)
def ashore(p): return not any(wet((p[0] + dx, p[1] + dy)) for dx, dy in ((0, 0), (15, 0), (-15, 0), (0, 15), (0, -15)))
def dry(p, reach=80):  # the nearest ground 15 m clear of the water within reach: the road keeps to the top of the bank
    if ashore(p): return p
    return min(((p[0] + dx, p[1] + dy) for dx in range(-reach, reach + 1, 10) for dy in range(-reach, reach + 1, 10) if ashore((p[0] + dx, p[1] + dy))), key=lambda q: math.dist(p, q))
def densify(pts, step=20): return [point(pts, s) for s in range(0, int(sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))), step)] + [pts[-1]]
def on_land(pts): return [pts[0]] + [dry((round(x), round(y))) for x, y in densify(pts)[1:-1]] + [pts[-1]]
# The Portage (Queenston) road on today's Portage Road and Main Street, from the King's Bridge to the junction with the
# lane, then north toward Queenston. South of the bridge it is Chippawa's river road toward Street's Creek and the camp.
RIVER_RD = on_land([(3000, -1378)] + [M(*NC(x, y)) for x, y in ((-151, 688), (-551, 759), (-870, 857))] + [BR_S])
PORTAGE = on_land([BR_N] + [M(*v) for v in ((43.0625, -79.0530), (43.06158, -79.05766), (43.06331, -79.06393), (43.06530, -79.06959),
    (43.06657, -79.07321), (43.07060, -79.07834), (43.07290, -79.08021), (43.07464, -79.08120), (43.07713, -79.08143),
    (43.08001, -79.08227), (43.08484, -79.08939), (43.08627, -79.09133))] + [J, M(*N(-1500, 2300)), M(*N(-1413, 3000))])
ROAD = RIVER_RD + PORTAGE  # from the east edge to the north edge, over the bridge
LANE = [J, P['lane_drummond'], P['lane_dorchester'], M(*N(-3000, 1797))]
FERRY = [J, P['museum'], M(*N(-450, 1840))]
JESUP = [M(*N(*p)) for p in ((-1250, 1350), (-900, 1500), (-900, 1900), (-1480, 2050))]
SKINNER = [M(*N(-2100, 1810)), M(*N(-2100, 1300))]
FENCE = [(P['guns'][0] - 80, P['guns'][1] - 20), (P['guns'][0] + 80, P['guns'][1] - 20)]  # "within twenty yards" of the guns

# ---- ground ----
# Fields south of the lane from the Portage road west to Skinner's and east to the thickets, the orchard on the slope
# below the graveyard, and the grain north of the lane; the woods beyond, the belt Scott's brigade came through across
# the road, and the thickets east of it to the bank. The road south of the belt keeps a cleared margin for its farms.
FIELD_S = [(-2200, 1250), (-900, 1250), (-900, 1800), (-2200, 1800)]
FIELD_N = [(-2200, 1850), (-1300, 1850), (-1300, 2150), (-2200, 2150)]
ORCHARD = [(-1950, 1450), (-1450, 1450), (-1450, 1720), (-1950, 1720)]
LANE_SIDE = [(-3000, 1770), (-1300, 1770), (-1300, 1870), (-3000, 1870)]
def corridor(pts, w):  # a polygon w metres either side of a polyline
    L, R = [], []
    for i, p in enumerate(pts):
        a, b = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]; t = unit((b[0] - a[0], b[1] - a[1]))
        L.append((round(p[0] - t[1] * w), round(p[1] + t[0] * w))); R.append((round(p[0] + t[1] * w), round(p[1] - t[0] * w)))
    return L + R[::-1]
ROADSIDE_S = corridor(stretch(ROAD, (3000, -1378), M(*N(-780, 880))), 70)
ROADSIDE_N = corridor(stretch(ROAD, J, (-1413, 3000)), 60)
FIELDS = [FIELD_S, FIELD_N]
features = [
    dict(type="road", name="the Portage road", pts=ROAD, **label_on(M(*N(-604, 460)), M(*N(-673, 780)), 45)),
    dict(type="road", name="the Queenston road", pts=stretch(ROAD, J, (-1413, 3000)), **label_on((-1480, 2500), (-1440, 2800), 45)),
    dict(type="road", name="Lundy's Lane", pts=LANE, **label_on((-2300, 1806), LANE[1], 30)),
    dict(type="road", name="the ferry road", pts=FERRY, **label_on((-900, 1829), FERRY[2], 30)),
    dict(type="road", name="Skinner's lane (about here)", pts=SKINNER, **label_on(SKINNER[1], SKINNER[0], 30)),
    dict(type="road", name="Jesup's track (about here)", pts=JESUP, **label_on(JESUP[1], JESUP[2], -35)),
    dict(type="fence", name="log fence (about here)", pts=FENCE, at=[FENCE[1][0] + 80, FENCE[1][1] - 20]),
    dict(name="the church", at=[P['church'][0] - 60, P['church'][1] + 40]),
    dict(name="the graveyard", at=[P['graveyard'][0] + 20, P['graveyard'][1] - 60]),
    dict(name="the orchard", at=[-1700, 1500]),
    dict(name="the hollow (about here)", at=list(P['hollow'])),
    dict(name="Mrs. Wilson's tavern (about here)", at=[P['wilson'][0] + 60, P['wilson'][1] - 40]),
    dict(name="Table Rock", at=[P['table_rock'][0] - 200, P['table_rock'][1] - 20]),  # the brink reads as water
    dict(name="Horseshoe Falls", at=[P['horseshoe_w'][0] + 150, P['horseshoe_w'][1]]),
    dict(name="American Falls", at=[P['american_falls'][0] + 120, P['american_falls'][1]]),
    dict(name="Bridgewater mills", at=[P['mills'][0] - 250, P['mills'][1] - 120]),
    dict(name="Chippawa", at=[P['cummington'][0] + 60, P['cummington'][1] - 60]),
    dict(name="King's Bridge (about here)", at=[P['kings_bridge'][0] + 20, P['kings_bridge'][1] - 90]),
    dict(name="to Queenston, 10 km", at=[-1300, 2900]),
    dict(name="to DeCew's Falls and Twelve Mile Creek", at=[-2650, 1890]),
    dict(name="to Brown's camp", at=[2700, -1500]),
    dict(name="the woods", at=[-950, 1080]), dict(name="the thickets", at=[-650, 1600]),
    dict(name="Niagara River", **label_on((1500, -300), (2500, -700))),
    dict(name="Niagara gorge", **label_on((420, 2000), (780, 2600))),
    dict(name="Chippawa River", **label_on((900, -2350), (1400, -1900))),
]
WATER_NAMES = ("Niagara River", "Niagara gorge", "Chippawa River", "Horseshoe Falls", "American Falls")
for f in features:
    if "at" in f and f.get("name") not in WATER_NAMES: assert not wet(f["at"]), (f["name"], f["at"], "a label in the water")
for f in features:
    if f.get("type") == "road":
        for a, b in zip(f["pts"], f["pts"][1:]):
            for s in (i / 10 for i in range(11)): q = (a[0] + s * (b[0] - a[0]), a[1] + s * (b[1] - a[1])); assert not wet(q), (f["name"], q, "a road in the water")

# ---- order of battle: (id, side, short, name, commander, type, strength, extra) ----
OOB = [
    # Brown's Left Division: Scott's 1st Brigade, Ripley's 2nd, Porter's volunteers and the artillery
    ("r9", "american", "9th and 22nd", "9th and 22nd US Infantry (Scott's brigade)", "Col. Hugh Brady; Maj. Henry Leavenworth", "infantry", 450, {}),
    ("r11", "american", "11th", "11th US Infantry (Scott's brigade)", "Maj. John McNeil", "infantry", 315, {}),
    ("r25", "american", "25th", "25th US Infantry (Scott's brigade)", "Maj. Thomas Jesup", "infantry", 315, {}),
    ("towson", "american", "Towson", "Towson's company, US Artillery: two 6-pounders and a 5.5-inch howitzer", "Capt. Nathan Towson", "artillery", 90, dict(guns=3)),
    ("harris", "american", "Harris", "Harris's troop, US Light Dragoons", "Capt. Samuel Harris", "cavalry", 70, {}),
    ("r1", "american", "1st", "1st US Infantry (Ripley's brigade)", "Lt. Col. Robert Nicholas", "infantry", 150, {}),
    ("r21", "american", "21st", "21st US Infantry (Ripley's brigade)", "Col. James Miller", "infantry", 432, {}),
    ("r23", "american", "23rd", "23rd US Infantry (Ripley's brigade)", "Maj. Daniel McFarland; Brig. Gen. Eleazer Ripley", "infantry", 300, {}),
    ("ritchie", "american", "Ritchie and Biddle", "Ritchie's and Biddle's companies, US Artillery", "Maj. Jacob Hindman; Capts. John Ritchie and Thomas Biddle", "artillery", 110, dict(guns=6)),
    ("porter", "american", "Porter", "Porter's brigade: New York and Pennsylvania volunteers and Canadian Volunteers", "Brig. Gen. Peter B. Porter", "militia", 300, {}),
    # Drummond's Right Division. Pearson's light brigade, on the hill from the morning
    ("glengarry", "british", "Glengarry", "Glengarry Light Infantry", "Lt. Col. Francis Battersby", "light_infantry", 376, {}),
    ("incmil", "british", "Incorporated Militia", "Incorporated Militia of Upper Canada", "Lt. Col. William Robinson", "militia", 336, {}),
    ("k8lc", "british", "King's light coy", "Detachment of the 8th (King's) Foot", "Capt. Campbell", "light_infantry", 80, {}),
    ("ld19", "british", "19th Dragoons", "19th Light Dragoons, Lisle's troop", "Maj. Robert Lisle", "cavalry", 50, {}),
    ("pld", "british", "Provincial Dragoons", "Provincial Light Dragoons", "Capt. William Hamilton Merritt", "cavalry", 30, {}),
    ("parry", "british", "1st Militia Bde", "1st Militia Brigade: 1st, 2nd, 4th and 5th Lincoln and 2nd York", "Lt. Col. Love Parry", "militia", 300, dict(loose=True)),
    ("norton", "british", "Mohawks", "Mohawk warriors", "John Norton", "riflemen", 50, dict(loose=True)),
    ("tomkins", "british", "Royal Artillery", "Royal Artillery: two 6-pounders and a 5.5-inch howitzer, with Congreve rockets", "Lt. Tomkins; Capt. James Mackonochie", "artillery", 35, dict(guns=3)),
    # Drummond's column from Queenston, Morrison's force
    ("ra24", "british", "24-pounders", "Royal Artillery: two brass 24-pounders", "Capt. James Mackonochie", "artillery", 25, dict(guns=2)),
    ("r89", "british", "89th", "2nd battalion, 89th Foot", "Lt. Col. Joseph Morrison", "infantry", 425, {}),
    ("royalsdet", "british", "Royal Scots det.", "Detachment, 1st (Royal Scots) Foot", "Capt. Brereton", "infantry", 171, {}),
    ("lc41", "british", "41st light coy", "Light company, 41st Foot", "Capt. Glew", "light_infantry", 80, {}),
    # Colonel Hercules Scott's column from Twelve Mile Creek
    ("r103", "british", "103rd", "103rd Foot, seven companies", "Col. Hercules Scott", "infantry", 635, {}),
    ("k8", "british", "King's", "8th (King's) Foot, headquarters wing", "Maj. Thomas Evans", "infantry", 300, {}),
    ("r104", "british", "104th flank coys", "Flank companies, 104th Foot", "", "infantry", 100, {}),
    ("royals", "british", "Royal Scots", "1st (Royal Scots) Foot, headquarters wing", "Lt. Col. John Gordon", "infantry", 400, {}),
    ("hamilton", "british", "2nd Militia Bde", "2nd Militia Brigade", "Lt. Col. Hamilton", "militia", 250, {}),
]
BASE = {row[0]: row for row in OOB}

# ---- the clock: 25 and 26 July 1814, local mean time ----
UTC = dt.timezone.utc
T0 = dt.datetime(1814, 7, 25, tzinfo=UTC)
def A(hm): return f"1814-07-25 {hm}"
def B(hm): return f"1814-07-26 {hm}"
def sec(t): return (dt.datetime.strptime(t, "%Y-%m-%d %H:%M:%S" if t.count(":") == 2 else "%Y-%m-%d %H:%M").replace(tzinfo=UTC) - T0).total_seconds()
def fmt(s): s = round(s); return (T0 + dt.timedelta(seconds=s)).strftime("%Y-%m-%d %H:%M" + (":%S" if s % 60 else ""))
def plus(t, mins): return fmt(sec(t) + mins * 60)
START, END = A("06:00"), B("12:00")

# ---- movement ----
KEYS = {}
def K(t, p, **kw): return dict(t=t, x=round(p[0]), y=round(p[1]), **kw)
def carried(id, f): return next((k[f] for k in reversed(KEYS.get(id, [])) if f in k), {"state": "line", "strength": BASE[id][6]}.get(f))
def keys(id, ks):  # every leg starts where the unit stands, unless it is coming out of hiding
    have = KEYS.setdefault(id, [])
    if have and ks:
        a, b = have[-1], ks[0]
        assert carried(id, "state") == "hidden" or (a["x"], a["y"]) == (b["x"], b["y"]), (id, a["t"], b["t"], "a leg must start where the unit stands")
        if a["t"] == b["t"]: a.update({k: v for k, v in b.items() if k != "t"}); ks = ks[1:]
    have += ks
def last(id): k = KEYS[id][-1]; return (k["x"], k["y"])
def at(id, t, **kw): keys(id, [K(t, last(id), **kw)])  # a change in place
def appear(id, t, p, h, state="line", **kw): keys(id, [K(t, p, h=h, state=state, **kw)])

PACE = 4  # km/h, a column of foot on the road
def walk(t0, pts, state="column", kmh=PACE):  # keys along a path at a marching pace
    pts = [p for i, p in enumerate(pts) if i == 0 or math.dist(p, pts[i - 1]) > 5]
    t, out = sec(t0), []
    for i, p in enumerate(pts):
        if i: t += math.dist(pts[i - 1], p) / (kmh / 3.6)
        out.append(K(fmt(t), p, h=heading(p, pts[i + 1]) if i + 1 < len(pts) else heading(pts[i - 1], p), **(dict(state=state) if i == 0 else {})))
    return out
def hold_until(id, t0):  # stand until the minute before t0, then turn and go
    if sec(t0) - sec(KEYS[id][-1]["t"]) > 120: at(id, plus(t0, -1))
def move(id, t0, pts, h=None, state="line", moving="column", kmh=PACE):  # from where it stands along pts at a pace; returns the arrival time
    hold_until(id, t0)
    ks = walk(t0, [last(id)] + pts, moving, kmh); ks[-1]["state"] = state
    if h is not None: ks[-1]["h"] = h
    keys(id, ks); return ks[-1]["t"]
def go(id, t0, t1, pts, h=None, state="line", moving="column"):  # from where it stands along pts, arriving at t1
    hold_until(id, t0)
    pts = [last(id)] + [p for p in pts if math.dist(p, last(id)) > 5]; d = [0]
    for a, b in zip(pts, pts[1:]): d.append(d[-1] + math.dist(a, b))
    ks = [K(fmt(sec(t0) + (sec(t1) - sec(t0)) * d[i] / d[-1]), p, h=heading(p, pts[i + 1]) if i + 1 < len(pts) else heading(pts[i - 1], p)) for i, p in enumerate(pts)]
    ks[0]["state"] = moving; ks[-1]["state"] = state
    if h is not None: ks[-1]["h"] = h
    keys(id, ks)
def lose(id, t, n): at(id, t, strength=carried(id, "strength") - n)
def hide(id, t): at(id, t, state="hidden")
def road(a, b): return stretch(ROAD, a, b)
def rd(y): return min((p for p in densify(ROAD, 10)), key=lambda p: abs(p[1] - y) + (0 if p[1] > -1300 else 1e9))  # the road where it crosses y
EAST, NORTH, WEST = ROAD[0], ROAD[-1], LANE[-1]  # where the roads leave the map: to Brown's camp, to Queenston, to DeCew's

# Where each unit stands on the hill once the light brigade has taken it, facing south down the Portage road: the guns
# among the graves on the summit, the Glengarrys on the right in the orchards, Parry's militia and Norton's warriors
# beyond them, the Incorporated Militia and the King's light company on the left of the road, the 19th behind the left.
HILL = dict(
    tomkins=((P['guns'][0] - 40, P['guns'][1] + 5), 175), glengarry=((-2050, 1640), 180), parry=((-2450, 1700), 180),
    norton=((-2780, 1640), 180), incmil=((-1330, 1700), 200), k8lc=((-1215, 1645), 200), ld19=((-1490, 2250), 180),
)
for n, id in enumerate(("glengarry", "incmil", "k8lc", "tomkins", "parry", "norton")): appear(id, START, (NORTH[0], NORTH[1] - 60 * n), 180, "column")
appear("ld19", START, rd(-20), 200, "line"); appear("pld", START, rd(-800), 140, "line")

assert set(KEYS) <= set(BASE), set(KEYS) - set(BASE)
for id in KEYS:
    if carried(id, "state") != "hidden" and sec(KEYS[id][-1]["t"]) < sec(END): at(id, END)

# ---- assemble and check ----
units = []
TOP = {"infantry": 6, "light_infantry": 6, "militia": 6, "riflemen": 6, "artillery": 6, "cavalry": 15}  # km/h, the fastest any leg may go
for id, side, short, name, commander, type, strength, extra in OOB:
    if id not in KEYS: continue
    ks, state, h = KEYS[id], None, None
    for a, b in zip(ks, ks[1:]):
        state, h = a.get("state", state), a.get("h", h)
        assert sec(b["t"]) > sec(a["t"]), (id, a["t"], b["t"])
        if state == "hidden": continue
        moved = (a["x"], a["y"]) != (b["x"], b["y"])
        assert moved or b.get("h", h) == h or "strength" in b or sec(b["t"]) - sec(a["t"]) <= 600, (id, a["t"], b["t"], "a slow turn in place holds the time-lapse")
        assert not (moved and sec(b["t"]) - sec(a["t"]) > 3 * 3600), (id, a["t"], b["t"], "a march leg over three hours")
        kmh = math.dist((a["x"], a["y"]), (b["x"], b["y"])) / (sec(b["t"]) - sec(a["t"])) * 3.6
        assert kmh <= TOP[type], (id, a["t"], b["t"], f"{kmh:.1f} km/h")
        for f in (i / 20 for i in range(1, 20)):
            q = (a["x"] + f * (b["x"] - a["x"]), a["y"] + f * (b["y"] - a["y"]))
            assert not wet(q), (id, a["t"], b["t"], q, "a leg through the water")
    state = None
    for k in ks:
        state = k.get("state", state)
        assert state == "hidden" or not wet((k["x"], k["y"])), (id, k["t"], (k["x"], k["y"]), "afloat")
    units.append(dict(id=id, side=side, name=name, short=short, commander=commander, type=type, strength=strength, keys=ks, **extra))
events = []

battle = dict(
    id="lundys-lane", name="Battle of Lundy's Lane", date="1814-07-25", dateText="25 July 1814", place="Lundy's Lane, by the Falls of Niagara, Upper Canada (Ontario)",
    origin=dict(lat=LAT0, lon=LON0), extent=6000, start=START, end=END, sunrise="04:43", sunset="19:30", speed=30, lapse=1800, menPerDot=5,
    water=WATER, terrainExaggeration=2, contourInterval=2,
    trees=dict(density=0.003, clear=[FIELD_S, FIELD_N, ORCHARD, LANE_SIDE, ROADSIDE_S, ROADSIDE_N]), fields=FIELDS,
    wind=dict(x=0.3, y=0.4), view=dict(x=0, y=0, width=6000),
    sides=dict(american=dict(name="Americans (Brown, Scott)", color="#27497f", light="#6f8fc4", dark="#12254a"),
               british=dict(name="British, Canadians and allies (Drummond, Riall)", color="#b3331f", light="#d87a68", dark="#5a150c")),
    features=features, units=units, events=events,
    sources=["Terrain: " + T["source"] + ". Resampled to 10 m. Today's city, the Fallsview hotels and the cemetery's trees are smoothed away."],
)
json.dump(battle, open(HERE + "battle.json", "w"), indent=1)
print(len(units), "units,", len(events), "events,", len(features), "features,", sum(u["strength"] for u in units if u["side"] == "american"), "Americans,", sum(u["strength"] for u in units if u["side"] == "british"), "British")
