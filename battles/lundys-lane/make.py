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
        assert sec(b["t"]) >= sec(a["t"]), (id, a["t"], b["t"], "a key before the last one: the unit is still on its way")
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
    pts = [last(id)] + pts; pts = [p for i, p in enumerate(pts) if i == 0 or math.dist(p, pts[i - 1]) > 5]; d = [0]
    if len(pts) == 1: return at(id, t1, state=state, **({"h": h} if h is not None else {}))  # already there
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

AMERICANS = [row[0] for row in OOB if row[1] == "american"]
for id in AMERICANS + ["royals", "r103", "k8", "r104", "hamilton", "r89", "royalsdet", "lc41", "ra24"]: appear(id, START, EAST if BASE[id][1] == "american" else NORTH, 0, "hidden")
def to_hill(id):  # down the Queenston road to the junction, then along the lane for the right of the line
    p, _ = HILL[id]; pts = road(last(id), J)
    return pts + ([P['lane_drummond'], (p[0], 1800)] if p[0] < -1950 else []) + [p]

# ---- the morning: Pearson's light brigade down the Queenston road; by seven it holds the high ground at the lane.
# The dragoons are out ahead at Bridgewater, and toward the Chippawa camp. At eight they fall back on the lane and
# leave a picket at Mrs. Wilson's tavern ----
for n, id in enumerate(("glengarry", "incmil", "k8lc", "tomkins", "parry", "norton")):
    go(id, plus(A("06:10"), 3 * n), plus(A("06:45"), 3 * n), to_hill(id), HILL[id][1])
WILSON = rd(760)
move("ld19", A("08:00"), road(last("ld19"), J) + [HILL["ld19"][0]], HILL["ld19"][1], kmh=8)
move("pld", A("08:00"), road(last("pld"), WILSON), 150, kmh=8)

# ---- four o'clock: Scott's brigade from the camp over the King's Bridge up the Portage road for Queenston, Harris's
# dragoons ahead. At five they drive in the picket at Mrs. Wilson's. The column halts short of the wood while Scott
# reports the enemy in force (the halt is inferred), and Riall orders the light brigade back ----
COL = dict(harris=("16:00", -720), towson=("16:03", -640), r9=("16:05", -560), r11=("16:09", -440), r25=("16:12", -340))
for id, (t, y) in COL.items():
    appear(id, A(t), EAST, 270, "column"); move(id, A(t), road(EAST, rd(y)) if id != "harris" else road(EAST, rd(870)), state="column", kmh=4.5 if id != "harris" else 5)
move("pld", A("17:02"), road(WILSON, J) + [(-1450, 2200)], 180, kmh=10)
for id in ("glengarry", "incmil", "k8lc", "parry", "norton", "tomkins"):  # a few hundred metres up the road and the lane
    p = HILL[id][0]; go(id, A("17:15"), A("17:40"), [(p[0], p[1] + 380)], 180, "retreat", "retreat")
    at(id, A("17:41"), state="line")

# ---- towards six: Drummond meets Morrison's column on the Queenston road and brings it on. He countermands the retreat
# and forms the line: the guns on the summit, the 89th, the Royals detachment and the 41st light company in the rear of
# the hill, the Glengarry on the right, the Incorporated Militia and the King's on the left of the road ----
BEHIND = dict(r89=(-1600, 1910), royalsdet=(-1780, 1905), lc41=(-1960, 1915), ra24=(-1700, 1748))
for n, id in enumerate(("ra24", "r89", "royalsdet", "lc41")):
    t = plus(A("17:40"), 3 * n); appear(id, t, NORTH, 180, "column")
    move(id, t, road(NORTH, J) + [BEHIND[id]], 180, kmh=5)
for id in ("glengarry", "incmil", "k8lc", "parry", "norton", "tomkins"):
    go(id, A("17:55"), A("18:15"), [HILL[id][0]], HILL[id][1])
at("tomkins", A("18:45"), state="firing"); at("ra24", A("18:45"), state="firing")

# ---- between six and seven: Scott clears the wood. The 9th, 11th and 22nd deploy in the fields on the left of the
# road, the 25th on the right; Towson unlimbers on the highway ----
DEPLOY = dict(r9=((-1680, 1330), 15), r11=((-1420, 1320), 5), towson=(rd(1330), 315), r25=((-1140, 1370), 345), harris=(rd(1080), 330))
for n, id in enumerate(("harris", "towson", "r9", "r11", "r25")):
    p, h = DEPLOY[id]; t = plus(A("18:20"), 2 * n)
    move(id, t, road(last(id), rd(min(p[1], 1250))) + [p], h, "line", kmh=5)
for id in ("r9", "r11", "towson"): at(id, A("19:00"), state="firing")
for id in ("glengarry", "incmil", "k8lc"): at(id, A("19:00"), state="firing")

# ---- the attack on the hill: the 11th and 22nd straight at it, the 9th round the left. A shell blows up one of
# Towson's ammunition wagons ----
go("r11", A("19:15"), A("19:30"), [(-1440, 1540)], 345, "firing", "line")
go("r9", A("19:15"), A("19:35"), [(-1900, 1520)], 20, "firing", "line")
lose("towson", A("19:17"), 12)
for id, n in (("r9", 90), ("r11", 45), ("glengarry", 20), ("incmil", 25), ("k8lc", 5)): lose(id, A("19:40"), n)

# ---- Jesup's 25th through the thickets to the interval by the bank, into the Incorporated Militia's flank and onto
# the Queenston road behind the British left. Riall is taken on the road; Lisle's dragoons run to Muddy Run ----
move("r25", A("19:30"), [JESUP[1], (-900, 1720)], 270, "firing", kmh=3)
lose("r25", A("20:00"), 30); lose("incmil", A("20:00"), 50); lose("k8lc", A("20:00"), 10)
for id, p in (("incmil", (-1480, 2140)), ("k8lc", (-1380, 2160))): go(id, A("20:01"), A("20:15"), [p], 180, "line", "retreat")
go("r25", A("20:05"), A("20:20"), [(-1000, 1950), (-1420, 2050)], 270, "firing", "line")
move("ld19", A("20:08"), road(last("ld19"), NORTH), kmh=12, moving="rout", state="rout"); hide("ld19", plus(KEYS["ld19"][-1]["t"], 1))
go("pld", A("20:08"), A("20:20"), [(-1720, 2230)], 140, "line", "retreat"); lose("pld", A("20:21"), 3)
go("r89", A("20:12"), A("20:20"), [(-1570, 1960)], 95, "firing", "line")  # its left thrown back to face the road
lose("r25", A("20:30"), 40); lose("r89", A("20:30"), 20); lose("incmil", A("20:30"), 50)
go("r25", A("20:35"), A("20:55"), [(-1000, 1950), (-1000, 1720)], 270, "line", "column")
go("r89", A("20:45"), A("20:50"), [BEHIND["r89"]], 180)

# ---- half past eight: the 11th and 22nd go to pieces; the 9th alone keeps its formation ----
lose("r9", A("20:25"), 110); lose("r11", A("20:25"), 65)
go("r11", A("20:31"), A("20:48"), [(-1350, 1220)], 200, "line", "rout"); at("r11", A("20:55"), h=345)
for id in ("r9", "towson", "glengarry", "k8lc"): at(id, A("20:35"), state="line")
lose("towson", A("20:36"), 8); lose("glengarry", A("20:36"), 15)

# ---- nine o'clock: Ripley's and Porter's brigades and Hindman's guns come up the road, Brown last with the reserve;
# Colonel Scott's column comes in along the lane from the west and forms a second line in rear of Lundy's Lane ----
HOLLOW = dict(r23=(-1290, 1460), r21=(-1420, 1420), r1=(-1560, 1390), ritchie=rd(1300), porter=(-1720, 1340))
for n, id in enumerate(("r23", "r1", "r21", "ritchie", "porter")):
    t = plus(A("19:00"), 4 * n); appear(id, t, EAST, 270, "column")
    go(id, t, plus(A("20:58"), 3 * n), road(EAST, rd(1250)) + [HOLLOW[id]], 330, "column")
LINE2 = dict(r103=(-1880, 2030), k8=(-2070, 2010), r104=(-1970, 2100), royals=(-2260, 1990), hamilton=(-2180, 2130))
for n, id in enumerate(("r103", "k8", "r104", "royals", "hamilton")):
    t = plus(A("20:44"), 4 * n); appear(id, t, WEST, 90, "column")
    move(id, t, [(-2450, 1802), (LINE2[id][0], 1950), LINE2[id]], 180, kmh=4.5)
for id, p in (("glengarry", (-2460, 1960)), ("parry", (-2660, 1950)), ("norton", (-2860, 1890))): go(id, A("21:10"), A("21:25"), [p], 180, "line", "retreat")

# ---- Miller's 21st up through the dark from the hollow to the log fence; one volley, then the battery. The 1st gives
# way, the 23rd lost heavily, Porter on their left, the 25th in the thickets on the right ----
go("r21", A("21:15"), A("21:27"), [(FENCE[0][0] + 80, FENCE[0][1] - 10)], 320, "firing", "line")
go("r21", A("21:28"), A("21:30"), [(-1745, 1830)], 0, "firing", "charge")
for id, n in (("tomkins", 12), ("ra24", 10)): at(id, A("21:30"), state="surrender", strength=carried(id, "strength") - n)
lose("r21", A("21:31"), 25)
go("r23", A("21:18"), A("21:33"), [(-1590, 1800)], 0, "firing", "line")
go("r1", A("21:18"), A("21:33"), [(-1950, 1770)], 355, "firing", "line")
lose("r1", A("21:35"), 20); go("r1", A("21:36"), A("21:45"), [(-1920, 1560)], 180, "line", "retreat"); at("r1", A("21:47"), h=355)
go("r1", A("21:50"), A("21:58"), [(-1960, 1770)], 355, "line", "line")
go("porter", A("21:20"), A("21:40"), [(-2180, 1730)], 345, "firing", "line")
go("ritchie", A("21:35"), A("21:50"), [(-1660, 1700)], 0, "line", "column")
for id, p in (("r89", (-1560, 2010)), ("royalsdet", (-1720, 2040)), ("lc41", (-1720, 2120))): go(id, A("21:31"), A("21:40"), [p], 180, "line", "retreat")
lose("r23", A("21:40"), 45); lose("r89", A("21:40"), 40); lose("royalsdet", A("21:40"), 15)
for id, p in (("r9", (-1840, 1590)), ("r11", (-1600, 1620)), ("towson", (-1480, 1650))): go(id, A("21:40"), A("21:55"), [p], 0, "line", "column")

# ---- about ten, by moonlight: the first counterattack, in the darkness straight at the centre; the lines twenty
# yards apart; repelled ----
FRONT = ("r103", "r89", "k8", "royalsdet", "royals")
REFORM = dict(LINE2, r89=(-1560, 2010), royalsdet=(-1720, 2040))
for id in FRONT: go(id, A("22:00"), A("22:06"), [(last(id)[0], 1895 if id != "royals" else 1880)], 180, "firing", "charge")
for id in ("r21", "r23", "r1", "porter", "ritchie"): at(id, A("22:00"), state="firing")
for id, n in (("r103", 25), ("r89", 60), ("k8", 30), ("royalsdet", 20), ("royals", 35), ("r21", 25), ("r23", 30), ("r1", 13), ("porter", 25), ("ritchie", 10)): lose(id, A("22:12"), n)
for id in FRONT: go(id, A("22:14"), A("22:24"), [REFORM[id]], 180, "line", "retreat")

# ---- after half past ten: the second attack. Scott leads about 250 men past the guns; the 89th is repulsed at
# about twenty paces, Ripley's men fire into Scott's column from behind, and it breaks. Scott and Brown are wounded ----
for id in FRONT: go(id, A("22:45"), A("22:51"), [(last(id)[0], 1935)], 180, "firing", "charge")
go("r9", A("22:44"), A("22:52"), [(-1680, 1880)], 10, "charge", "charge"); go("r11", A("22:44"), A("22:52"), [(-1580, 1880)], 10, "charge", "charge")
for id, n in (("r9", 40), ("r11", 20), ("r89", 70), ("r103", 20), ("k8", 25), ("royals", 40), ("r21", 25), ("r23", 14), ("porter", 15), ("ritchie", 8)): lose(id, A("22:56"), n)
go("r9", A("22:57"), A("23:10"), [(-1850, 1580)], 180, "line", "rout"); go("r11", A("22:57"), A("23:10"), [(-1600, 1600)], 180, "line", "rout")
go("r89", A("22:57"), A("23:07"), [REFORM["r89"]], 180, "line", "retreat")
go("r103", A("22:57"), A("23:05"), [(-1830, 2160)], 180, "line", "rout"); go("r103", A("23:15"), A("23:25"), [LINE2["r103"]], 180)
for id in ("k8", "royalsdet", "royals"): go(id, A("22:57"), A("23:07"), [REFORM[id]], 180, "line", "retreat")
for id in ("r21", "r23", "r1", "porter"): at(id, A("23:10"), state="line")

# ---- almost midnight: the last attack, headed by Glew's light company of the 41st, reaches the summit and recovers
# the guns ----
go("lc41", A("23:45"), A("23:52"), [(-1720, 1850)], 180, "firing", "charge")
for id in FRONT: go(id, A("23:45"), A("23:52"), [(last(id)[0], 1900)], 180, "firing", "charge")
for id in ("r21", "r23", "r1", "porter", "ritchie"): at(id, A("23:45"), state="firing")
for id, n in (("lc41", 37), ("r89", 64), ("r103", 15), ("k8", 15), ("royalsdet", 25), ("royals", 37), ("r21", 29), ("r23", 0), ("porter", 26), ("ritchie", 8)):
    if n: lose(id, A("23:52"), n)
for id, p in (("r21", (-1745, 1700)), ("r23", (-1580, 1700)), ("r1", (-1950, 1650)), ("porter", (-2150, 1630)), ("ritchie", (-1650, 1620))):
    go(id, A("23:53"), B("00:02"), [p], carried(id, "h"), "firing", "line")
for id in ("tomkins", "ra24"): at(id, B("00:00"), state="line")
go("lc41", B("00:00"), B("00:05"), [(-1740, 1805)], 180, "line", "charge")

# ---- twelve o'clock: Brown, exhausted by loss of blood, hands over to Ripley, who withdraws to the camp beyond the
# Chippawa under desultory firing. The captured 24-pounders are left on the hill for want of horses ----
HOME = ("r21", "r23", "r1", "porter", "ritchie", "r25", "r9", "r11", "towson", "harris")
for n, id in enumerate(HOME):
    t = move(id, plus(B("00:05"), 3 * n), [rd(1500 - 60 * n)], 150, "column", "retreat" if n < 5 else "column", kmh=4)
    move(id, plus(t, 1), road(last(id), EAST), state="column", kmh=4.5); hide(id, plus(KEYS[id][-1]["t"], 1))
for id in ("r103", "r89", "k8", "royalsdet", "royals"): at(id, B("00:03"), state="line")
for id, p in (("r89", (-1560, 1880)), ("r103", (-1880, 1890)), ("royalsdet", (-1720, 1900)), ("k8", (-2070, 1880)), ("royals", (-2260, 1870)), ("lc41", (-1720, 1830))):
    go(id, B("00:20"), B("00:30"), [p], 180)

# ---- 26 July, nearly nine in the morning: Ripley comes back over the Chippawa with about 1,200 men, finds the hill held
# in force, and retires, destroying the bridge behind him ----
BACK = dict(r21=-30, r23=60, r1=150, r25=230, r9=310, r11=390)
for n, id in enumerate(BACK):
    t = plus(B("07:10"), 4 * n); appear(id, t, EAST, 270, "column")
    move(id, t, road(EAST, rd(BACK[id] + 300)) + [rd(BACK[id] + 450)], state="column", kmh=4.5)
for n, id in enumerate(BACK):  # in line across the fields short of the wood, facing the hill
    go(id, plus(B("08:52"), n), B("09:05"), [(-650 - 110 * n, 620 + 15 * n)], 330)
for n, id in enumerate(BACK):
    t = plus(B("09:30"), 3 * n); move(id, t, road(last(id), EAST), state="column", kmh=4.5); hide(id, plus(KEYS[id][-1]["t"], 1))

assert set(KEYS) == set(BASE), set(KEYS) ^ set(BASE)
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
