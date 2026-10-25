# Builds battles/chippawa/battle.json and fits terrain.json to 1814. Run from the repo root: python3 battles/chippawa/make.py
# Local metres from 43.0545N 79.0360W (x east, y north). The 3.5 km square holds the plain between Street's Creek and
# the Chippawa (Welland) River, the woods on its west, Scott's and Ripley's camps south of the creek, the King's Bridge,
# the tête-de-pont and Riall's works at Chippawa. Every place is kept in latitude and longitude, or in the research
# note's local metres where the note derives it (N below), and converted once. Anchors are OpenStreetMap points and the
# Niagara Parks markers. The King's Bridge, the tête-de-pont, Street's and Ussher's houses, Ussher's lane and the 1814
# wood line are placed from Lossing, Scott and the park's panels, within 100 to 250 m, and labelled "about here".
# Strengths are Drummond's for the British; the American battalions are Scott's 1,377 split by Gardner's casualty return.
import json, math, re
HERE = "battles/chippawa/"
LAT0, LON0 = 43.0545, -79.0360
KX, KY = 111320 * math.cos(math.radians(LAT0)), 111320  # tools/fetch_terrain.py's metres per degree
def M(lat, lon): return (round((lon - LON0) * KX), round((lat - LAT0) * KY))
R_NOTE = 6371009 * math.pi / 180  # the note's equirectangular metres per degree
def N(x, y): return (LAT0 + y / R_NOTE, LON0 + x / (R_NOTE * math.cos(math.radians(LAT0))))  # a place the note gives in its metres
def NL(*pts): return [M(*N(x, y)) for x, y in pts]

# ---- plane geometry ----
def unit(v): L = math.hypot(*v); return (v[0] / L, v[1] / L)
def heading(a, b): return round(math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) % 360)
def seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]; t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)))
    return math.dist(p, (a[0] + t * dx, a[1] + t * dy))
def inside(p, poly):
    c, (x, y) = False, p
    for (xa, ya), (xb, yb) in zip(poly, poly[-1:] + poly[:-1]):
        if (ya > y) != (yb > y) and x < xa + (xb - xa) * (y - ya) / (yb - ya): c = not c
    return c
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
    return out if s0 <= s1 else out[::-1]
def rect(c, h, w, d):  # a rectangle w across heading h and d deep, centred on c
    s, co = math.sin(math.radians(h)), math.cos(math.radians(h))
    return [[round(c[0] + a * co + b * s), round(c[1] - a * s + b * co)] for a, b in [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)]]
def quad(x0, y0, x1, y1): return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
def label_on(p, q, off=0):  # a label rotated along the line p-q at p, `off` metres to its left
    t = unit((q[0] - p[0], q[1] - p[1])); return dict(at=[round(p[0] - t[1] * off), round(p[1] + t[0] * off)], rot=round(math.degrees(math.atan2(t[1], t[0]))))

# ---- places ----
PLACES = {
    # OpenStreetMap and the markers' positions
    'monument': (43.05213, -79.02473), 'creek_mouth': (43.05182, -79.02254), 'slater': (43.05611, -79.02719),
    'kingsbridge_park': (43.06364, -79.04955), 'cummington': (43.05923, -79.05096),
    # from the note's text, within 100 to 250 m
    'kings_bridge': N(-950, 850), 'tete_de_pont': N(-800, 800), 'street': N(1050, -460), 'ussher': N(1000, -250),
}
P = {k: M(*v) for k, v in PLACES.items()}

# ---- lines ----
# Street's Creek on OpenStreetMap's ways, from the south edge round the bend and up the reach behind the shore to its
# mouth. It is too narrow for the 30 m survey, so the DEM does not show it.
CREEK = NL((-624, -1750), (-348, -1460), (56, -1278), (500, -1200), (960, -1118), (1065, -871), (1152, -652), (1115, -331), (1094, -298))
# The river road: the Niagara Parkway from the creek bridge to the Chippawa, then the 1814 leg to the King's Bridge and
# over it into Riall's works. South of the creek it runs along the shore to Fort Erie; the note gives no trace there, so
# it is kept 100 to 150 m inside the DEM's waterline.
ROAD_S = [(1400, -1750), (1360, -1500), (1320, -1200), (1290, -950), (1250, -700), (1200, -520)]
ROAD_N = NL((1121, -391), (1082, -367), (898, -49), (771, 140), (655, 361), (528, 528), (399, 613), (176, 665), (-151, 688), (-551, 759), (-870, 857), (-950, 850))
BRIDGE_N = (P['kings_bridge'][0] - 10, P['kings_bridge'][1] + 120)  # the north bank, across the 1814 channel
BRIDGES = [(ROAD_N[-1], BRIDGE_N)]  # dry over water
LANE = NL((1040, -240), (200, -240))  # Ussher's farm lane, west from the river road just north of the creek

# The plain inside the 1814 wood line (Lossing's three-quarter mile from the river at the creek, narrowing to Scott's
# third at the north) up to the strip of trees that hid Riall's march, y 530 to 590; the road's margin beyond the strip.
PLAIN = NL((-300, -1300), (-300, 300), (-169, 530), (450, 530), (750, 530), (1350, -300), (1250, -900), (960, -1150), (56, -1300))
ROADSIDE = NL((-1000, 800), (-1000, 900), (-550, 810), (-150, 740), (500, 700), (500, 590), (-110, 590), (-550, 700), (-950, 770))
CAMPS = [(-100, -1320), (1000, -1170), (1550, -1100), (1550, -1750), (-100, -1750)]

# ---- terrain: the 1814 ground ----
# The Copernicus surface model reads today's woods, houses and street trees as hills up to 25 m high: the park woodland
# on the plain, the suburbs in the old forest, the creek's tree line, Navy Island's canopy. Any land cell above 179 m is
# set to 176, the plain's own level, and the land is then averaged over 70 m, which keeps the shore and the slope down
# to the Chippawa and drops the buildings. The woods are drawn as trees. The fit runs once on the fetched grid and marks
# it `fitted`; to change it, fetch the grid again with the note's command.
WATER = 170.5  # the Niagara and the Chippawa read 169 to 170 m; the plain 174 to 178
T = json.load(open(HERE + "terrain.json"))
COLS, SP = T["cols"], T["spacing"]; HALF = COLS * SP / 2
if not T.get("fitted"):
    Z0 = [176.0 if v > 179 else v for v in T["z"]]; R = 3  # cells each way: 70 m
    Z = list(Z0)
    for r in range(COLS):
        for c in range(COLS):
            if Z0[r * COLS + c] <= WATER: continue
            near = [Z0[rr * COLS + cc] for rr in range(max(0, r - R), min(COLS, r + R + 1)) for cc in range(max(0, c - R), min(COLS, c + R + 1)) if Z0[rr * COLS + cc] > WATER]
            Z[r * COLS + c] = round(sum(near) / len(near), 2)
    T["z"], T["fitted"] = Z, "land above 179 m set to 176, then averaged over 70 m (battles/chippawa/make.py)"
    json.dump(T, open(HERE + "terrain.json", "w"), separators=(",", ":"))
def z(p):
    c, r = int((p[0] + HALF) / SP), int((HALF - p[1]) / SP)
    return T["z"][r * COLS + c] if 0 <= c < COLS and 0 <= r < COLS else 999
def wet(p): return z(p) <= WATER and not any(seg_dist(p, a, b) < 15 for a, b in BRIDGES)
def ashore(p): return not any(wet((p[0] + dx, p[1] + dy)) for dx, dy in ((0, 0), (15, 0), (-15, 0), (0, 15), (0, -15)))
def dry(p, reach=60):  # the nearest ground 15 m clear of the water within reach: the Parkway hugs a shore the 30 m survey blurs
    if ashore(p): return p
    return min(((p[0] + dx, p[1] + dy) for dx in range(-reach, reach + 1, 10) for dy in range(-reach, reach + 1, 10) if ashore((p[0] + dx, p[1] + dy))), key=lambda q: math.dist(p, q))
def densify(pts, step=20): return [point(pts, s) for s in range(0, int(sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))), step)] + [pts[-1]]
ROAD_N = [ROAD_N[0]] + [dry((round(x), round(y))) for x, y in densify(ROAD_N)[1:-1]] + [ROAD_N[-1]]
ROAD = ROAD_S + ROAD_N + [BRIDGE_N, (-1000, 1040)]

# ---- ground ----
FIELDS = [quad(150, -1000, 850, -420), quad(450, -120, 850, 380), quad(-200, -1000, 100, -500), quad(-200, -100, 300, 350)]
features = [
    dict(type="creek", name="Street's Creek", **label_on((300, -1240), (700, -1170), -40), pts=CREEK),
    dict(type="road", name="the river road", pts=ROAD, **label_on((1290, -950), (1250, -700), 45)),
    dict(type="road", pts=[M(*N(1050, -360)), M(*N(1160, -400))]),  # the bridge over Street's Creek
    dict(type="road", name="Ussher's lane (about here)", pts=LANE, **label_on(LANE[1], LANE[0], 30)),
    dict(type="works", name="Fort Chippawa and Riall's works (about here)", pts=[(-1130, 975), (-880, 990), (-850, 1080)], at=[-1250, 930]),
    dict(type="redoubt", name="tête-de-pont (about here)", poly=rect(P['tete_de_pont'], 160, 60, 40), at=[P['tete_de_pont'][0] + 150, P['tete_de_pont'][1] - 40]),
    dict(type="camp", poly=quad(-1150, 1000, -900, 1100)),
    dict(type="camp", name="Scott's camp", poly=quad(500, -1600, 1050, -1350), at=[775, -1640]),
    dict(type="camp", name="Ripley's camp", poly=quad(0, -1700, 450, -1450), at=[225, -1730]),
    dict(name="King's Bridge (about here)", at=[P['kings_bridge'][0] - 60, P['kings_bridge'][1] - 60]),
    dict(name="Chippawa", at=[P['cummington'][0], P['cummington'][1] - 60]),
    dict(name="Street's house (about here)", at=[P['street'][0] - 60, P['street'][1] - 50]),
    dict(name="Ussher's (about here)", at=[P['ussher'][0] - 90, P['ussher'][1] - 40]),
    dict(name="the plain", at=[300, -650]),
    dict(name="the woods", at=[-900, -400]), dict(name="the woods", at=[-1000, 300]),
    dict(name="Battlefield monument (2001)", at=[P['monument'][0] - 150, P['monument'][1] - 110]),
    dict(name="Navy Island", at=[1650, 400]),
    dict(name="Niagara River", **label_on((1300, -700), (1500, -100))),
    dict(name="Chippawa (Welland) River", **label_on((-1700, 50), (-1450, 380))),
    dict(name="to Fort Erie", at=[1250, -1700]),
]
for f in features:
    if "at" in f and f.get("name") and "River" not in f["name"]: assert not wet(f["at"]), (f["name"], "a label in the water")

# ---- order of battle: (id, side, short, name, commander, type, strength, extra) ----
OOB = [
    # Brown's Left Division: Scott's brigade, the artillery, Ripley's brigade and Porter's volunteers and warriors
    ("r9", "american", "9th and 22nd", "1st battalion, 9th US Infantry, with a detachment of the 22nd", "Maj. Henry Leavenworth", "infantry", 577, {}),
    ("r11", "american", "11th", "2nd battalion, 11th US Infantry", "Col. John Campbell, then Maj. John McNeil", "infantry", 400, {}),
    ("r25", "american", "25th", "3rd battalion, 25th US Infantry", "Maj. Thomas Jesup", "infantry", 400, {}),
    ("towson", "american", "Towson", "Towson's company, US Artillery: three guns", "Capt. Nathan Towson", "artillery", 90, dict(guns=3)),
    ("ritchie", "american", "Ritchie", "Ritchie's company, US Artillery", "Capt. John Ritchie", "artillery", 75, dict(guns=3)),
    ("hall", "american", "Hall", "Hall's 12-pounder of Biddle's company", "Lt. Hall", "artillery", 25, dict(guns=1)),
    ("harris", "american", "Harris", "Harris's troop, US Light Dragoons", "Capt. Samuel Harris", "cavalry", 70, {}),
    ("r21", "american", "21st", "21st US Infantry, with the 19th's detachment (Ripley's brigade)", "Brig. Gen. Eleazer Ripley; Maj. Vose", "infantry", 680, {}),
    ("r23", "american", "23rd", "23rd US Infantry (Ripley's brigade)", "Maj. Daniel McFarland", "infantry", 400, {}),
    ("fenton", "american", "Pennsylvanians", "Fenton's 5th Pennsylvania Volunteers (Porter's brigade)", "Lt. Col. James Fenton; Brig. Gen. Peter B. Porter", "militia", 300, dict(loose=True)),
    ("sixnations", "american", "Six Nations", "Six Nations and allied warriors (Porter's brigade)", "Capt. Pollard; Red Jacket", "riflemen", 400, dict(loose=True)),
    # Riall's Right Division
    ("royals", "british", "Royal Scots", "1st battalion, 1st (Royal Scots) Foot", "Lt. Col. John Gordon", "infantry", 500, {}),
    ("r100", "british", "100th", "100th (Prince Regent's) Foot", "Lt. Col. the Marquis of Tweeddale", "infantry", 460, {}),
    ("r8", "british", "8th (King's)", "1st battalion, 8th (King's) Foot", "Maj. Thomas Evans", "infantry", 400, {}),
    ("lights", "british", "Light companies", "Light companies of the Royal Scots and the 100th", "Lt. Col. Thomas Pearson", "light_infantry", 150, dict(loose=True)),
    ("lincoln", "british", "2nd Lincoln", "2nd Lincoln Militia", "Lt. Col. Thomas Dickson", "militia", 200, dict(loose=True)),
    ("norton", "british", "Grand River", "Grand River Six Nations", "Capt. John Norton", "riflemen", 200, dict(loose=True)),
    ("western", "british", "Western Indians", "Western Indians", "Capt. Colvin", "riflemen", 100, dict(loose=True)),
    ("ra24", "british", "Royal Artillery", "Royal Artillery: two light 24-pounders and a 5.5-inch howitzer", "Capt. James Mackonochie", "artillery", 40, dict(guns=3)),
    ("ra6", "british", "6-pounders", "Royal Artillery: three 6-pounders", "Capt. James Mackonochie", "artillery", 30, dict(guns=3)),
    ("ld19", "british", "19th Dragoons", "19th Light Dragoons", "Maj. Robert Lisle", "cavalry", 70, {}),
]
BASE = {row[0]: row for row in OOB}

# ---- the clock: 5 July 1814, local mean time ----
def sec(t): h, m, *s = map(int, t.split(':')); return h * 3600 + m * 60 + (s[0] if s else 0)
def fmt(s): s = int(round(s)); return f"{s // 3600:02d}:{s % 3600 // 60:02d}" + (f":{s % 60:02d}" if s % 60 else "")
def plus(t, mins): return fmt(sec(t) + mins * 60)
START, END = "05:00", "19:45"

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
def appear(id, t, p, state="line", **kw): keys(id, [K(t, p, state=state, **kw)])

# Where each unit stands at five in the morning: Scott's brigade in its camp behind the creek, Ripley's beside it, the
# British behind their works at Chippawa, and the militia and warriors who sniped at the pickets along the creek.
# Porter's brigade is still on the road from Buffalo.
DAWN = dict(
    r9=((900, -1450), 0), r11=((760, -1450), 0), r25=((620, -1450), 0), towson=((1000, -1400), 0), harris=((850, -1560), 0),
    r21=((300, -1560), 0), r23=((130, -1600), 0), ritchie=((400, -1660), 0), hall=((330, -1660), 0),
    royals=((-1450, 1150), 150), r100=((-1420, 1000), 150), r8=((-1150, 1060), 150), lights=((-1600, 1300), 150),
    norton=((-1650, 1450), 150), ra24=((-960, 1010), 160), ra6=((-1080, 960), 160), ld19=((-1350, 1220), 150),
    lincoln=((300, -1040), 180), western=((700, -1000), 200),
)
for id, (p, h) in DAWN.items(): appear(id, START, p, h=h)
appear("fenton", "12:00", ROAD_S[0], "column", h=0); appear("sixnations", "12:04", ROAD_S[0], "column", h=0)

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
def road(a, b): return stretch(ROAD, a, b)
KB, CB = ROAD_N[-1], ROAD_N[0]  # the King's Bridge's south end; the bridge over Street's Creek
CAMP_RD = (1320, -1200)          # where the camps' track meets the river road
def to_bridge(p): return [CAMP_RD] + road(CAMP_RD, CB)                             # from the camps up the road to the creek bridge
def from_bridge(p): return road(CB, CAMP_RD) + [p]                                 # and back down to a place in camp
WORKS = dict(lincoln=(-1250, 1150), western=(-1550, 1350))  # the militia and warriors' dawn posts were by the creek
def home(id): return road(last(id), KB) + [BRIDGE_N, WORKS.get(id, DAWN[id][0])]  # up the river road, over the King's Bridge, into the works
def out_of_works(id): return [BRIDGE_N, KB] + road(KB, (-151, 688))                # out of the works and east along the river road

# ---- dawn: the Lincoln militia and the Western Indians snipe at the pickets from the bushes north of the creek ----
for id in ("lincoln", "western"): at(id, START, state="firing"); at(id, "05:40", state="line")
# ---- noon: they attack Treat's picket on the American left, then go back through the woods toward Chippawa ----
move("lincoln", "11:50", [(-100, -1090)], 200, "firing"); at("lincoln", "12:12", state="line")
move("lincoln", "12:15", [(-400, -400), (-500, 450)], 180); move("western", "12:15", [(300, -500), (-200, 200), (-700, 470)], 180)
# ---- Porter's brigade comes up the road from Buffalo and camps in the rear ----
move("fenton", "12:00", [(1380, -1700), (750, -1680)], 0); move("sixnations", "12:04", [(1390, -1720), (1000, -1705)], 0)

# ---- half past three: Riall over the King's Bridge in three columns, the King's in advance; the line forms south of
# the strip of trees by a quarter past four. The light troops go into the woods on the right, Norton far out beyond them.
for id, t, spot, h in (("r8", "15:28", (320, 500), 180), ("ra6", "15:34", (80, 440), 180), ("royals", "15:36", (200, 440), 180),
                       ("r100", "15:44", (440, 440), 180), ("ra24", "15:50", (600, 430), 160), ("ld19", "15:54", (540, 490), 180)):
    move(id, t, out_of_works(id) + [(min(spot[0], 300), 620), spot], h)
move("lights", "15:30", [BRIDGE_N, KB, (-600, 620), (-850, -560)], 180, moving="line", kmh=2.5)
go("lincoln", "15:50", "16:30", [(-350, -580)], 180, moving="line"); go("western", "15:50", "16:28", [(-600, -620)], 180, moving="line")
go("norton", "15:50", "17:15", out_of_works("norton")[:2] + [(-900, 600), (-1150, 0), (-1000, -800), (-750, -1450)], 60, moving="line")

# ---- four o'clock: Porter takes the volunteers and warriors from the rear of the camp into the woods ----
go("fenton", "16:00", "16:15", [(-150, -1560), (-450, -1250)]); go("fenton", "16:15", "16:30", [(-450, -720)], 0, "firing", "line")
go("sixnations", "16:00", "16:20", [(-150, -1640), (-850, -1250)]); go("sixnations", "16:20", "16:30", [(-850, -720)], 0, "firing", "line")
# ---- half past four: the woods fight. The Western Indians break at the first volleys; the 2nd Lincoln stands about
# fifteen minutes and is driven; Porter drives them three-quarters of a mile, to the edge of the woods opposite Chippawa ----
for id in ("lincoln", "lights"): at(id, "16:30", state="firing")
at("western", "16:30", state="firing"); lose("western", "16:32", 16); go("western", "16:33", "16:47", [(-700, 480)], 180, moving="rout")
lose("lincoln", "16:34", 14); go("lincoln", "16:35", "16:49", [(-100, 500)], 180, moving="retreat"); lose("lincoln", "16:50", 14)
go("lights", "16:35", "16:50", [(-480, 480)], 180, moving="retreat")
go("fenton", "16:31", "16:45", [(-250, 300)], 0, "firing", "firing"); go("sixnations", "16:31", "16:45", [(-700, 250)], 0, "firing", "firing")
# ---- a quarter to five: Porter meets the whole British line in order of battle, and his men break ----
for id in ("royals", "ra6"): at(id, "16:44", state="firing"); at(id, "16:50", state="line")
lose("fenton", "16:47", 5); lose("sixnations", "16:47", 13)
go("fenton", "16:48", "17:12", [(-200, -1300), (100, -1500)], 0, moving="rout"); go("sixnations", "16:48", "17:15", [(-350, -1600)], 0, moving="rout")
move("harris", "16:50", [(0, -1480)], 0)  # Harris's dragoons stop the fugitives behind the creek

# ---- Brown sends Scott forward. Towson first, then the brigade up the river road and over the creek bridge under the
# British guns; it forms line to the left and front along Ussher's lane, the 25th detached into the woods on the left ----
USSHER = M(*N(1000, -250)); LANE_E, LANE_W = LANE
move("towson", "16:42", to_bridge(None) + [(980, -190)], 330, "firing", kmh=5.9)
move("r9", "16:43", to_bridge(None) + [USSHER, (800, -240), (700, -200)], 345, kmh=5.5)
move("r11", "16:45", to_bridge(None) + [USSHER, (500, -240), (420, -200)], 15, kmh=5.5)
move("r25", "16:44", to_bridge(None) + [USSHER, LANE_W, (-200, -130)], 50, "firing", kmh=5.9)
move("ritchie", "16:52", to_bridge(None) + [USSHER, (515, -240), (515, -160)], 0, "firing", kmh=4.5)
move("hall", "16:53", to_bridge(None) + [USSHER, (560, -240), (560, -160)], 0, "firing", kmh=4.5)
# the 21st round the woods against the British right rear, wading the creek; it comes out of the woods too late
go("r21", "16:50", "18:00", [(-250, -1560), (-350, -1300), (-500, -500), (-500, 200), (-380, 380)], 45)

# ---- the British line comes on, halting to fire; its guns on the river road open on the bridge ----
move("ra24", "16:48", [(771, 140)], 160, "firing")
for id, mid, spot in (("royals", (310, 150), (400, -60)), ("r100", (550, 150), (650, -60)), ("ra6", (190, 150), (280, -60))):
    go(id, "16:52", "17:05", [mid], 180, "firing", "line"); go(id, "17:08", "17:15", [spot], 180, "firing", "line")
go("r8", "16:55", "17:10", [(300, 200)], 180); go("r8", "17:10", "17:22", [(160, -10)], 225, "firing")
go("ra24", "17:08", "17:12", [(865, 0)], 160, "firing"); go("ld19", "17:20", "17:30", [(780, 150)], 180)
go("lincoln", "16:52", "17:12", [(-150, 80)], 200); go("lights", "16:52", "17:12", [(-330, 20)], 180)
for id in ("lincoln", "lights"): at(id, "17:22", state="firing")
# ---- the firefight, about twenty-five minutes at seventy paces: the 11th's left wing and the 9th's right thrown
# forward into an obtuse angle, Towson on the extreme right; he blows up a 24-pounder's limber ----
for id, y in (("r9", -150), ("r11", -150)): go(id, "17:12", "17:15", [(last(id)[0], y)], carried(id, "h"), "firing", "line")
lose("r9", "17:22", 55); lose("r11", "17:22", 38); lose("royals", "17:22", 80); lose("r100", "17:22", 80)
lose("towson", "17:25", 10); lose("ra24", "17:25", 3); lose("r25", "17:30", 76); lose("r8", "17:32", 27)
# Riall orders the Royals and the 100th to charge, and withdraws them under a most destructive fire
for id in ("royals", "r100"): go(id, "17:25", "17:30", [(last(id)[0], last(id)[1] - 25)], 180, "charge", "charge")
lose("royals", "17:31", 103); lose("r100", "17:31", 123); lose("r9", "17:31", 54); lose("r11", "17:31", 37); lose("ritchie", "17:32", 8); lose("ra6", "17:32", 2)
go("r11", "17:33", "17:37", [(430, -90)], 15, "charge", "charge")
# ---- the British fall back a quarter of a mile; at the slope down to the Chippawa they break and run for the bridge.
# The 8th and the 6-pounders cover; the 19th Dragoons save the disabled 24-pounder ----
go("royals", "17:32", "17:45", [(230, 450)], 180, "retreat", "retreat"); go("r100", "17:33", "17:46", [(470, 460)], 180, "retreat", "retreat")
go("ra24", "17:33", "17:45", road((865, 0), (655, 361)), 180, "retreat", "retreat"); go("ld19", "17:32", "17:45", [(600, 420)], 180)
go("ra6", "17:36", "17:48", [(150, 400)], 180, "firing", "retreat"); go("r8", "17:36", "17:50", [(60, 420)], 180, "line", "retreat")
for id in ("lincoln", "lights"): go(id, "17:36", "17:50", [(-300, 560)] if id == "lincoln" else [(-480, 560)], 180, "retreat", "retreat")
for id, t in (("royals", "17:46"), ("r100", "17:48"), ("ra24", "17:47"), ("ld19", "17:52"), ("lincoln", "17:52"), ("lights", "17:54"), ("western", "17:50")):
    move(id, t, home(id), 150, "line", "rout" if id in ("royals", "r100", "lincoln", "lights", "western") else "column", kmh=5.5 if id != "ld19" else 8)
move("ra6", "17:56", road((150, 400), KB)[:-1] + [P['tete_de_pont']], 200, "firing")  # into the tête-de-pont, whose guns fire on the pursuit
move("r8", "18:00", home("r8"), 150)  # the last over
move("ra6", "18:25", [KB, BRIDGE_N, DAWN["ra6"][0]], 160)
go("norton", "17:45", "19:00", [(-1000, -800), (-1150, 0), (-900, 600), KB, BRIDGE_N, DAWN["norton"][0]], 150, moving="line")
# ---- the pursuit to within half gunshot of the batteries; Hall's 12-pounder is dismounted in sight of the Chippawa ----
go("r9", "17:36", "18:00", [(330, 430)], 315); go("r11", "17:38", "18:00", [(40, 440)], 315); go("r25", "17:36", "18:00", [(-180, 520)], 300)
go("hall", "17:40", "17:56", [(130, 400)], 300, "firing"); lose("hall", "17:58", 2); at("hall", "18:00", state="line"); at("ritchie", "17:40", state="line")
at("towson", "17:38", state="line")

# ---- about half past six the troops are ordered back; at sunset they reach their camp behind Street's Creek ----
for id, t in (("r9", "18:38"), ("r11", "18:42"), ("r25", "18:46"), ("hall", "18:50"), ("ritchie", "18:52"), ("towson", "18:54")):
    move(id, t, ([] if id in ("ritchie", "towson") else [LANE_W]) + [LANE_E, CB] + from_bridge(DAWN[id][0]), 0)
go("r21", "18:40", "19:40", [(-500, -500), (-350, -1300), (-250, -1560), DAWN["r21"][0]], 0)
for id, p in (("fenton", (750, -1680)), ("sixnations", (1000, -1705)), ("harris", DAWN["harris"][0])): move(id, "18:45", [p], 0)

assert set(KEYS) == set(BASE), set(KEYS) ^ set(BASE)
for id in KEYS:
    if carried(id, "state") != "hidden" and sec(KEYS[id][-1]["t"]) < sec(END): at(id, END)

# ---- assemble and check ----
units = []
TOP = {"infantry": 6, "light_infantry": 6, "militia": 6, "riflemen": 6, "artillery": 6, "cavalry": 15}  # km/h, the fastest any leg may go
for id, side, short, name, commander, type, strength, extra in OOB:
    ks, state = KEYS[id], None
    for a, b in zip(ks, ks[1:]):
        state = a.get("state", state)
        assert sec(b["t"]) > sec(a["t"]), (id, a["t"], b["t"])
        if state == "hidden": continue
        moved = (a["x"], a["y"]) != (b["x"], b["y"])
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

# ---- chapters: (time, title, text, camera centre, metres across, playback speed, when) ----
# `when` holds a clock time the sources record, or a phrase; without one the card gives the nearest hour.
CHAPTERS = [
    (START, "Chippawa, July 1814", "Brown's division crossed the Niagara on 3 July and took Fort Erie at five that afternoon, with 137 prisoners. On the 4th Scott's brigade marched north in a running fight of some sixteen miles, found the bridge over the Chippawa taken up and Riall behind a strong tête-de-pont, and fell back a little more than a mile to camp behind Street's Creek. Brown came up at eleven that night with the reserve. At dawn on the 5th Canadian militia and warriors are sniping at the pickets from the bushes north of the creek.", [500, -1250], 1800, 300, "at dawn"),
    ("12:00", "Noon", "By noon the British attack one of the pickets, forty men under Treat, as it returns to camp on the American left. About noon Porter arrives from Buffalo with three hundred Pennsylvania volunteers and about four hundred Indians. Scott's brigade eats its late Fourth of July dinner.", [700, -1400], 1600, 300, "about noon"),
    ("15:30", "Riall marches", "Riall marches out to give battle, at three by Merritt's journal and four by his own report, over the King's Bridge in three columns with the King's Regiment in advance; it reached him only this morning, about 400 strong by Drummond. Brown sees a cloud of dust rise toward Chippawa. Riall puts his regulars at about fifteen hundred, and the militia and Indians at not above three hundred.", [-350, 750], 2200, 60, "around 3:30 PM"),
    ("16:15", "Into the woods", "At four, by Brown's plan, Porter leads the Pennsylvania volunteers and the Indians from the rear of the camp into the woods on the left. The British light companies and the 2nd Lincoln go into the same woods from the north, with Norton's Grand River warriors thrown out far on their right.", [-450, -950], 1300, 60, "4 o'clock"),
    ("16:30", "The woods fight", "About half past four Porter's advance meets the British light parties in the woods and drives them. The Western Indians break at the first volleys. The 2nd Lincoln stands for fifteen minutes, against at least 800 men by Merritt's count; it loses 43 men today, the heaviest loss of any Canadian militia unit in one action of the war. The Pennsylvanians drive them three-quarters of a mile.", [-400, -50], 1800, 20, "about half-past four"),
    ("16:45", "Porter routed", "Near Chippawa Porter's men come within a few yards of the whole British line drawn up in order of battle, and they flee in every direction. From the cloud of dust and the heavy firing, Brown orders Scott forward and sends Gardner to bring up Ripley. Harris's dragoons stop the fugitives behind the creek.", [-250, 200], 1300, 20, None),
    ("17:00", "Over the bridge", "Riall comes out in order of battle about five, by Brown's report. Scott's brigade reaches the bridge over Street's Creek and is met by fire from nine field guns, by Scott's count. Towson's three guns open before the infantry is formed and take post by the river on the right. The battalions cross and form line to the left and front along Ussher's farm lane, while the 25th goes into the woods on the left. Seeing grey jackets, Riall takes them for 'a body of Buffalo militia'.", [900, -550], 900, 20, "about five o'clock"),
    ("17:15", "Why, these are regulars!", "The Americans advance about 50 metres from the lane. Both lines halt to fire more than once, and close to within sixty or seventy paces by Scott's memoir, 75 metres by the park's panels. Scott throws the 11th's left wing and the 9th's right forward into an obtuse angle, with Towson on the extreme right, while the 25th in the woods checks the British right. The musketry lasts about 25 minutes.", [450, -100], 900, 10, None),
    ("17:30", "The charge", "Towson silences the most effective British battery by blowing up an ammunition wagon, then turns canister on the infantry, now nearly in contact. Riall orders the Royal Scots and the 100th to charge, under a most destructive fire, and withdraws them; the King's moves up on the right.", [450, -30], 900, 10, "after about twenty-five minutes"),
    ("17:45", "The break", "The whole British line falls back. Where the ground slopes down toward the Chippawa, a quarter of a mile on, it breaks and runs for its works. The 8th and the 6-pounders cover the retreat, and the 19th Light Dragoons save a 24-pounder whose limber was blown up. The Americans pursue to within half gunshot of the batteries, and Hall's 12-pounder is dismounted in sight of the Chippawa.", [-150, 550], 1800, 20, "before six o'clock"),
    ("18:00", "The thunder-gust", "Over the river the British take up the planks of the bridge, and a building near it is set alight. A thunder-gust and then gentle rain sweep up the river, filling the air with blinding dust. Ripley's 21st comes out of the woods too late. Brown considers forcing the works; the lateness of the hour decides him against it.", [-450, 650], 2000, 60, None),
    ("18:30", "Ordered back", "Around half past six the troops are ordered back to camp. Merritt writes that the men had to lie out all night, every house being filled with the wounded; out of fourteen officers the 100th has only three unhurt.", [100, 250], 1200, 60, "around 6:30 PM"),
    ("19:00", "Back behind the creek", "The army marches back over the creek bridge and reaches its camp at sunset. Gardner's return gives the American loss as 328: 60 killed, 249 wounded and 19 missing. The Montreal return gives the British 515: 148 killed, 321 wounded and 46 missing, of whom the Royal Scots lost 213 and the 100th 204. On the evening of the 7th Riall withdraws to Fort George. On 25 July the armies meet again at Lundy's Lane, 4 km north.", [900, -1100], 1300, 60, "toward sunset"),
]
events = [dict(t=t, title=a, text=b, at=at_, view=v, speed=s, **({"when": w} if w else {})) for t, a, b, at_, v, s, w in CHAPTERS]
for e in events:  # without `when` the card speaks the nearest hour (app.js chapterWhen), so it must be near the frame's clock
    s = sec(e["t"]) % 86400; hh = [n % 12 or 12 for n in (int(s // 3600), int(s // 3600) + 1)]; num = re.search(r"\d+", e.get("when", ""))
    assert not num or int(num[0]) in hh, (e["t"], e["when"], "the card's hour is not the frame's")
    assert e["speed"] in (1, 2, 5, 10, 20, 30, 60, 120, 300, 600, 1800, 3600, 7200), (e["t"], e["speed"], "not on the speed menu (sim.js SPEEDS)")
    assert "when" in e or abs(s - math.floor(s / 3600 + 0.5) * 3600) <= 15 * 60, (e["t"], e["title"], "give it a when")

battle = dict(
    id="chippawa", name="Battle of Chippawa", date="1814-07-05", dateText="5 July 1814", place="Chippawa, on the Niagara River, Upper Canada (Ontario)",
    origin=dict(lat=LAT0, lon=LON0), extent=3500, start=START, end=END, sunrise="04:26", sunset="19:42", speed=30, lapse=1800, menPerDot=5,
    water=WATER, terrainExaggeration=3, contourInterval=1, trees=dict(density=0.003, clear=[PLAIN, ROADSIDE, CAMPS]), fields=FIELDS,
    tints=[dict(color="rgba(96,102,110,0.3)", **{"from": "17:50", "until": "18:30"})],  # the thunder-gust and rain
    wind=dict(x=0.5, y=0.4), view=dict(x=0, y=0, width=3500),
    sides=dict(american=dict(name="Americans (Brown, Scott)", color="#27497f", light="#6f8fc4", dark="#12254a"),
               british=dict(name="British, Canadians and allies (Riall)", color="#b3331f", light="#d87a68", dark="#5a150c")),
    features=features, units=units, events=events,
    outcome={"result": "American victory: Riall's line beaten on the plain and driven back over the Chippawa", "losses": [
        ["american", "328 by Gardner's return: 60 killed, 249 wounded and 19 missing. Scott's three battalions lost 260 of them and the artillery 20; Porter's Pennsylvanians 12 and the warriors 23. The 19th's 7 and the 23rd's 1 are not drawn; nor are the missing."],
        ["british", "515 by the Montreal return of 13 July: 148 killed, 321 wounded and 46 missing. The Royal Scots lost 213 and the 100th 204; the 2nd Lincoln 43, the heaviest loss of any Canadian militia unit in one action of the war. Later counts give 108 dead. The missing are not drawn."]],
        "note": "Brown's first report counted four hundred British killed and wounded left on the field; Drummond wrote of about 500, a third of the men. The clock times are officers' watches, good to about a quarter of an hour."},
    sources=[
        "E. A. Cruikshank, ed., <a href='https://archive.org/details/cihm_05281' target='_blank'><i>The Documentary History of the Campaign upon the Niagara Frontier in 1814</i></a>, Part I (Lundy's Lane Historical Society, 1896), pp. 31-52: Riall's report of 6 July and his abstract of casualties; Drummond's letters of 9 and 10 July with the regimental strengths; Brown's reports of 6 and 7 July; Scott's and Hindman's reports; Gardner's return of the American loss; the Montreal General Order of 13 July; and eyewitness letters from the Ontario Messenger, a captain of Fenton's Pennsylvanians and a US artillery officer.",
        "William Hamilton Merritt's journal, in William Wood, ed., <a href='https://archive.org/details/selectbritishdoc0003will' target='_blank'><i>Select British Documents of the Canadian War of 1812</i></a>, vol. III (Champlain Society, 1926-28), pp. 613-616: Riall's march at three, the King's arriving that morning, the Western Indians and the 2nd Lincoln in the woods.",
        "Winfield Scott, <a href='https://archive.org/details/memoirsoflieutge01scotrich' target='_blank'><i>Memoirs of Lieut.-General Scott</i></a>, vol. I (1864), ch. X: the bridge, the nine guns, 'Buffalo militia', the obtuse angle and the final charge at sixty or seventy paces. Written fifty years after.",
        "Benson J. Lossing, <a href='https://archive.org/details/pictorialfieldbo00lossuoft' target='_blank'><i>The Pictorial Field-Book of the War of 1812</i></a> (1868), pp. 805-812: the plain three-quarters of a mile wide, Street's and Ussher's houses, the tête-de-pont, Porter's force and the thunder-gust.",
        "Niagara Parks Commission, the six interpretive panels and the monument at Chippawa Battlefield Park (2001), after Donald Graves, <i>Red Coats and Grey Jackets</i> (1994), as transcribed at the <a href='https://www.hmdb.org/m.asp?m=49399' target='_blank'>Historical Marker Database</a>: the dawn sniping, Ussher's lane, the 50 m advance and the 75 m range.",
        "Wikipedia, <a href='https://en.wikipedia.org/wiki/Battle_of_Chippawa' target='_blank'>Battle of Chippawa</a> (read 24 October 2026), for Graves's brigade strengths of 3 July and Hendry's revised British losses; The Canadian Encyclopedia; warhistory.org.",
        "Terrain: " + T["source"] + ". Resampled to 10 m. The surface model's modern woodland over the 1814 plain and the camps is flattened to the plain's level. The Chippawa's mouth is today's widened hydro channel, not the 1814 river. Places from OpenStreetMap contributors (ODbL): Street's Creek, the Niagara Parkway, the battlefield park and monument, Kingsbridge Park on the site of Fort Chippawa.",
        "What is reconstructed: the King's Bridge and the tête-de-pont from Lossing and the modern street plan, within 250 m; Street's and Ussher's houses and Ussher's lane from Lossing's sketches and the park's panels, within 100 m; the 1814 wood line from Lossing's three-quarter mile and Scott's 'third narrower'; the camps; the river road south of the creek. American battalion strengths are Scott's 1,377 split by each battalion's casualties; Graves's returns would settle them. Clock times between the recorded ones are placed from the sources' durations.",
    ],
)
json.dump(battle, open(HERE + "battle.json", "w"), indent=1)
print(len(units), "units,", len(events), "events,", len(features), "features,", sum(u["strength"] for u in units if u["side"] == "american"), "Americans,", sum(u["strength"] for u in units if u["side"] == "british"), "British")
# Which units each chapter's frame holds at its moment, so a caption never names a unit the camera leaves out.
def where(u, t):
    ks = [k for k in u["keys"] if sec(k["t"]) <= sec(t)]
    if not ks: return None
    state = next((k["state"] for k in reversed(ks) if "state" in k), "line")
    if state == "hidden": return None
    k = ks[-1]; nxt = [k2 for k2 in u["keys"] if sec(k2["t"]) > sec(t)]
    if nxt and (k["x"], k["y"]) != (nxt[0]["x"], nxt[0]["y"]):
        f = (sec(t) - sec(k["t"])) / (sec(nxt[0]["t"]) - sec(k["t"])); return (k["x"] + f * (nxt[0]["x"] - k["x"]), k["y"] + f * (nxt[0]["y"] - k["y"]))
    return (k["x"], k["y"])
for e in events:
    r = e["view"] / 2; inside_ = [u["id"] for u in units if (p := where(u, e["t"])) and abs(p[0] - e["at"][0]) <= r and abs(p[1] - e["at"][1]) <= r]
    print(f"{e['t']} {e['title']}: {' '.join(inside_)}")
