# Builds battles/new-orleans/battle.json and fits terrain.json to 1815. Run from the repo root: python3 battles/new-orleans/make.py
# Local metres from 29.9400N 89.9780W (x east, y north). The 9 km square holds Line Jackson on the Rodriguez Canal
# (-1731,-70 to -889,1277), the Chalmette, Bienvenu and de la Ronde ground the British crossed on 8 January, the night
# battle of 23 December at Lacoste's and Villeré's, and the west bank from Morgan's line down to Thornton's landing.
# New Orleans is six miles upriver, off the west edge; the head of Villeré's canal and Bayou Bienvenu, where the British
# came ashore, are off the north edge. Anchors are OpenStreetMap points and the de la Ronde ruins' historical marker.
# The batteries are placed by Latour's distances along the canal from the 1815 bank; Villeré's and Macarty's houses,
# the redoubt, Morgan's line, Patterson's battery and Thornton's landing from the sources' prose, within 200 to 600 m,
# and labelled "about here". Strengths are Latour's for Jackson's line and Pringle's 8 January figures for the British,
# as tabulated in Wikipedia's orders of battle.
import json, math, re, datetime as dt
HERE = "battles/new-orleans/"
LAT0, LON0 = 29.94, -89.978
KX, KY = 111320 * math.cos(math.radians(LAT0)), 111320  # tools/fetch_terrain.py's metres per degree
def M(lat, lon): return (round((lon - LON0) * KX), round((lat - LAT0) * KY))

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
def left(pts, i):  # the unit normal to the left of a polyline's direction at vertex i
    a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]; t = unit((b[0] - a[0], b[1] - a[1])); return (-t[1], t[0])
def offset(pts, d): return [(round(p[0] + left(pts, i)[0] * d), round(p[1] + left(pts, i)[1] * d)) for i, p in enumerate(pts)]
def length(pts): return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
def point(pts, s):  # the point s metres along a polyline, and its direction there
    for a, b in zip(pts, pts[1:]):
        L = math.dist(a, b)
        if s <= L or b is pts[-1]:
            t = unit((b[0] - a[0], b[1] - a[1])); return (a[0] + t[0] * s, a[1] + t[1] * s), t
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
    s0, s1 = proj(pts, a), proj(pts, b); lo, hi = min(s0, s1), max(s0, s1); out, run = [point(pts, lo)[0]], 0
    for p, q in zip(pts, pts[1:]):
        run += math.dist(p, q)
        if lo < run < hi: out.append(q)
    out.append(point(pts, hi)[0])
    return out if s0 <= s1 else out[::-1]
def ray_hit(p, d, pts):  # where the ray p + t·d first meets a polyline
    best = None
    for a, b in zip(pts, pts[1:]):
        ex, ey = b[0] - a[0], b[1] - a[1]; den = d[0] * ey - d[1] * ex
        if abs(den) < 1e-9: continue
        t = ((a[0] - p[0]) * ey - (a[1] - p[1]) * ex) / den; u = ((a[0] - p[0]) * d[1] - (a[1] - p[1]) * d[0]) / den
        if t > 0 and 0 <= u <= 1 and (best is None or t < best): best = t
    return None if best is None else (p[0] + d[0] * best, p[1] + d[1] * best)
def rect(c, h, w, d):  # a rectangle w across heading h and d deep, centred on c
    s, co = math.sin(math.radians(h)), math.cos(math.radians(h))
    return [[round(c[0] + a * co + b * s), round(c[1] - a * s + b * co)] for a, b in [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)]]
def hull(c, L, W, h):  # a ship's outline, bow toward heading h
    s, co = math.sin(math.radians(h)), math.cos(math.radians(h))
    return [[round(c[0] + b * s + a * co), round(c[1] + b * co - a * s)] for a, b in [(-W / 2, -L / 2), (-W / 2, L / 2 - 8), (0, L / 2), (W / 2, L / 2 - 8), (W / 2, -L / 2)]]
def label_on(p, q, off=0):  # a label rotated along the line p-q at p, `off` metres to its left
    t = unit((q[0] - p[0], q[1] - p[1])); return dict(at=[round(p[0] - t[1] * off), round(p[1] + t[0] * off)], rot=round(math.degrees(math.atan2(t[1], t[0]))))

# ---- the river ----
# Both banks are traced from the 3DEP DEM's hydro-flattened river surface (0.1 to 0.3 m west of x 2100, 3.0 to 3.2 m
# east of it, a later survey), every 225 m, and run on past the map's edges. The river is 690 m across at the line.
NBANK = [(-4650, 1594), (-4489, 1530), (-4264, 1440), (-4039, 1350), (-3814, 1170), (-3589, 1080), (-3364, 1012), (-3139, 878), (-2914, 765), (-2689, 630),
         (-2464, 495), (-2239, 360), (-2014, 202), (-1789, 45), (-1564, -68), (-1339, -202), (-1114, -360), (-889, -472), (-664, -585), (-439, -698), (-214, -788),
         (11, -922), (236, -990), (461, -1080), (686, -1148), (911, -1192), (1136, -1238), (1361, -1282), (1586, -1305), (1811, -1372), (2261, -1418), (2486, -1350),
         (2711, -1350), (2936, -1282), (3161, -1282), (3386, -1328), (3611, -1372), (3836, -1395), (4061, -1418), (4286, -1440), (4650, -1476)]
SBANK = [(-4650, 859), (-4489, 810), (-4264, 742), (-4039, 630), (-3814, 518), (-3589, 382), (-3364, 248), (-3139, 90), (-2914, -45), (-2689, -180), (-2464, -315),
         (-2239, -428), (-2014, -562), (-1789, -720), (-1564, -878), (-1339, -990), (-1114, -1102), (-889, -1215), (-664, -1328), (-439, -1418), (-214, -1508),
         (11, -1598), (236, -1688), (461, -1755), (686, -1822), (911, -1868), (1136, -1890), (1361, -1912), (1586, -1912), (1811, -1890), (2261, -1958), (2486, -1958),
         (2711, -1958), (2936, -1935), (3161, -1912), (3386, -1935), (3611, -1958), (3836, -2002), (4061, -2025), (4286, -2070), (4650, -2143)]
# The line meets the 1815 bank at A, 200 ft beyond the park's river edge by the National Register nomination; the river
# has taken that strip since, with Batteries 1 to 3 and the redoubt. Along the canal U runs inland and V downstream,
# toward the British.
A, U = (-1731, -70), (0.530, 0.848)
V = (U[1], -U[0])
HUS, HBR = heading((0, 0), V), heading(V, (0, 0))  # facing the British, 122; facing the line, 302
O_LINE = min(seg_dist(A, a, b) for a, b in zip(NBANK, NBANK[1:]))  # A's distance beyond today's water's edge, about 80 m
def lost(x): return O_LINE * max(0, min(1, (x + 2500) / 400, (-700 - x) / 400))  # the full strip from x -2100 to -1100
BANK = [(round(p[0] - left(NBANK, i)[0] * lost(p[0])), round(p[1] - left(NBANK, i)[1] * lost(p[0]))) for i, p in enumerate(NBANK)]
assert min(seg_dist(A, a, b) for a, b in zip(BANK, BANK[1:])) < 8, "the 1815 bank misses the end of the canal"
RIVER = BANK + SBANK[::-1]
LOST = [p for p in BANK if lost(p[0])] + [p for p in NBANK if lost(p[0])][::-1]
CENTRE = [((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) for a, b in zip(NBANK, SBANK)]
def wet(p): return inside(p, RIVER)

# ---- the swamp and the plain ----
# The cypress swamp's edge is 850 m from the bank at the line, where Battery 8 stands at the first trees, and nearly
# two miles back at Villeré's by Latour's march; above the line it is kept 850 m from the bank. Across the river the
# wood begins at the back of Morgan's canal, 2,000 yards from the bank.
def line(d, back=0): return (A[0] + d * U[0] - back * V[0], A[1] + d * U[1] - back * V[1])  # d m up the canal, `back` behind it
def front(d, f): return (A[0] + d * U[0] + f * V[0], A[1] + d * U[1] + f * V[1])          # d m up the canal, f m in front of it
WOOD_D = 850
SWAMP_EDGE = [(-5000, 2750)] + [p for p in offset(NBANK, WOOD_D) if p[0] < -2000] + [line(WOOD_D), (4100, 2500), (5600, 3020)]
SWAMP = SWAMP_EDGE + [(4650, 4650), (-4650, 4650)]
PLAIN = BANK + SWAMP_EDGE[::-1]
WEST_EDGE = [(-5600, -400)] + offset(SBANK, -1830) + [(5600, -4300)]
WEST_PLAIN = SBANK + WEST_EDGE[::-1]

# ---- terrain: the 1815 river and ground ----
# Inside the traced river the DEM goes to -2 m and the water level is -1. On land the drained suburbs, the modern
# levee, the refinery's fill and the canal banks are held between 0.1 and 3.2 m, the height of the natural bank, and the
# swamp to 1 m; the strip the river took is raised to 2.5 m. Each step is idempotent, so the script can be rerun.
T = json.load(open(HERE + "terrain.json"))
COLS, SP = T["cols"], T["spacing"]; HALF = COLS * SP / 2
def cells(poly):  # the DEM cells whose centres lie inside a polygon, by scanline
    out = set()
    for r in range(COLS):
        y = HALF - (r + 0.5) * SP
        xs = sorted(xa + (xb - xa) * (y - ya) / (yb - ya) for (xa, ya), (xb, yb) in zip(poly, poly[1:] + poly[:1]) if (ya > y) != (yb > y))
        for x0, x1 in zip(xs[::2], xs[1::2]):
            out.update(range(r * COLS + max(0, math.ceil((x0 + HALF) / SP - 0.5)), r * COLS + min(COLS - 1, math.floor((x1 + HALF) / SP - 0.5)) + 1))
    return out
WATER = -1.0
river, strip, swamp = cells(RIVER), cells(LOST), cells(SWAMP)
Z = []
for i, v in enumerate(T["z"]):
    if i in river: Z.append(-2.0); continue
    v = min(max(v, 0.1), 3.2)  # never 0: the page reads a zero as a gap in the survey
    if i in strip: v = max(v, 2.5)
    if i in swamp: v = min(v, 1.0)
    Z.append(round(v, 2))
if Z != T["z"]: T["z"] = Z; json.dump(T, open(HERE + "terrain.json", "w"), separators=(",", ":"))

# ---- places ----
PLACES = {  # OpenStreetMap, and the historical marker in the median of St. Bernard Highway at the de la Ronde ruins
    'monument': (29.94245, -89.99414), 'cemetery_river': (29.93752, -89.98968), 'cemetery_rear': (29.94466, -89.98674),
    'jourdan': (29.93233, -89.99757), 'delaronde': (29.93770, -89.96805),
}
P = {k: M(*v) for k, v in PLACES.items()}
DLR = P['delaronde']
VILLERE = (3400, -450)                   # "about 1-1/2 miles east of the De La Ronde Oaks", under the refinery; within 600 m
MOUTH = (3420, -1260)                    # where Villeré's canal, cut through on 6 January, meets the river
LANDING = (4300, -2150)                  # Thornton's landing, "about a thousand yards" below the canal's mouth
MACARTY = line(103, 180)                 # Jackson's headquarters, 180 m behind Battery 2; within 200 m
REDOUBT = (A[0] + 45 * V[0] + 18 * U[0], A[1] + 45 * V[1] + 18 * U[1])  # on the bank in front of the line's right
BATT_D = [21, 103, 149, 167, 341, 374, 548, 603]  # Latour's distances from the bank, metres
R0 = (-1790, -728)                       # Morgan's line meets the river, by the Jourdan plaque, 200 m in
def mline(s, f=0): return (R0[0] - s * U[0] + f * V[0], R0[1] - s * U[1] + f * V[1])  # s m back from the river along Raguet's canal
PATTERSON = (-2010, -640)                # "behind the levee in front of Jourdan's plantation", behind Morgan's line; within 400 m
PICKET = (-380, -1540)                   # Arnaud's picket, "about a mile below Morgan's line"; within 500 m
ROAD_E, ROAD_W, LEVEE = offset(BANK, 50), offset(SBANK, -50), offset(BANK, 20)
def road(a, b, R=ROAD_E): return stretch(R, a, b)
def on_road(x, R=ROAD_E): return point(R, proj(R, (x, next(p[1] for p in R if p[0] >= x))))[0]
ENTRY_E, ENTRY_W = on_road(-4470), on_road(-4470, ROAD_W)
LOUISIANA_AT = (lambda p: (p[0] - 0.53 * 130, p[1] - 0.85 * 130))(on_road(-1000, BANK))
CAROLINA = (2350, -1520)                 # the Carolina's station off the British camp, 130 m out
BR_BATT = {"brL": front(100, 560), "brC": front(400, 560), "brR": front(700, 560)}  # 1 January, 600 yards out

# ---- fields: cane on the plain, in strips running back from the river every 600 m, one boundary on the canal ----
def strips(bank, edge, side, step=600, near=70, far=40, gap=14, at=None):
    s, total = (proj(bank, at) % step if at else 0), length(bank); rays = []
    while s < total:
        p, t = point(bank, s); n = (-t[1] * side, t[0] * side)
        if at and math.dist(p, at) < 30: n = U
        rays.append((p, n)); s += step
    out = []
    for (p, n), (q, m) in zip(rays, rays[1:]):
        t = unit((q[0] - p[0], q[1] - p[1]))
        a, b = (p[0] + n[0] * near + t[0] * gap, p[1] + n[1] * near + t[1] * gap), (q[0] + m[0] * near - t[0] * gap, q[1] + m[1] * near - t[1] * gap)
        a2, b2 = ray_hit(a, n, edge), ray_hit(b, m, edge)
        if not (a2 and b2): continue
        out.append([[round(c) for c in v] for v in (a, b, (b2[0] - m[0] * far, b2[1] - m[1] * far), (a2[0] - n[0] * far, a2[1] - n[1] * far))])
    return out
FIELDS = strips(BANK, SWAMP_EDGE, 1, at=A) + strips(SBANK, WEST_EDGE, -1)

# ---- the clock: 23 December 1814 to 8 January 1815, local mean time ----
UTC = dt.timezone.utc
T0 = dt.datetime(1814, 12, 23, tzinfo=UTC)
def D(day, hm): return f"{'1814-12' if day >= 20 else '1815-01'}-{day:02d} {hm}"
def sec(t): return (dt.datetime.strptime(t, "%Y-%m-%d %H:%M:%S" if t.count(":") == 2 else "%Y-%m-%d %H:%M").replace(tzinfo=UTC) - T0).total_seconds()
def fmt(s): s = round(s); return (T0 + dt.timedelta(seconds=s)).strftime("%Y-%m-%d %H:%M" + (":%S" if s % 60 else ""))
def plus(t, mins): return fmt(sec(t) + mins * 60)
START, END = D(23, "11:00"), D(8, "16:30")

# ---- ground ----
WORKS = D(24, "08:00")  # the works are drawn whole from the morning after the night battle; they grew until 8 January
features = [
    dict(type="trench", name="Rodriguez Canal", pts=[line(0), line(1588)], **label_on(line(980), line(1100), -45)),
    dict(type="works", name="Line Jackson: the mud rampart", pts=[line(0, 10), line(WOOD_D, 10)], **label_on(line(420), line(600), 70), **{"from": WORKS}),
    dict(type="works", name="a double row of logs in the wood", pts=[line(WOOD_D, 10), line(1588, 10)], **label_on(line(1330), line(1450), 60), **{"from": WORKS}),
    *[dict(type="battery", poly=rect(line(d, 6), HUS, 24, 14), **{"from": WORKS}) for d in BATT_D],
    dict(type="redoubt", name="redoubt (about here)", poly=rect(REDOUBT, HUS, 26, 20), at=[round(REDOUBT[0] + 75), round(REDOUBT[1] - 20)], **{"from": WORKS}),
    dict(type="works", name="the levee (about here)", pts=LEVEE, **label_on((-3100, 905), (-2900, 790), 22)),
    dict(type="road", name="the river road", pts=ROAD_E, **label_on((-3600, 1210), (-3400, 1130), 40)),
    dict(type="road", pts=ROAD_W),
    dict(type="creek", name="Raguet's old canal", pts=[R0, mline(1830)], **label_on(mline(1100), mline(1300), 40)),
    dict(type="trench", name="Morgan's line (about here)", pts=[R0, mline(183)], at=[round(mline(200)[0] - 160), round(mline(200)[1] + 20)]),
    dict(type="battery", name="Patterson's battery (about here)", poly=rect(PATTERSON, heading(PATTERSON, front(300, 500)), 40, 16), at=[PATTERSON[0] - 330, PATTERSON[1] - 40], **{"from": D(29, "18:00")}),
    *[dict(type="battery", poly=rect(p, HBR, 50 if id != "brL" else 24, 14), **{"from": D(1, "02:00"), "until": D(1, "22:00")}) for id, p in BR_BATT.items()],
    dict(type="battery", poly=rect(front(400, 731), HBR, 50, 14), **{"from": D(8, "03:00")}),
    dict(type="ship", poly=hull(CAROLINA, 60, 13, 90), **{"from": D(23, "19:00"), "until": D(27, "08:30")}),
    dict(type="smoke", at=list(CAROLINA), rate=10, spread=50, **{"from": D(27, "07:20"), "until": D(27, "11:00")}),
    dict(type="ship", poly=hull(LOUISIANA_AT, 60, 13, 120), **{"from": D(28, "06:00"), "until": D(28, "18:00")}),
    dict(name="Mississippi River", **label_on((-2300, -120), (-2000, -310))),
    dict(name="Mississippi River", **label_on((2600, -1680), (2900, -1680))),
    dict(name="cypress swamp", at=[-2600, 2300]), dict(name="cypress swamp", at=[1200, 2300]), dict(name="the wood", at=[-3200, -3300]),
    dict(name="Macarty house, Jackson's headquarters (about here)", at=[round(MACARTY[0] - 270), round(MACARTY[1] + 310)]),
    dict(name="Chalmette plantation", at=list(map(round, front(650, 300)))),
    dict(name="de la Ronde house (ruins)", at=[DLR[0], DLR[1] + 80]),
    dict(name="Lacoste's", at=[2150, -800]),
    dict(name="Villeré house, British headquarters (about here)", at=[VILLERE[0] - 150, VILLERE[1] - 110]),
    dict(name="Chalmette Monument (1840 to 1908)", at=[P['monument'][0] - 400, P['monument'][1] + 400]),
    dict(name="National Cemetery (1864)", at=[round((P['cemetery_river'][0] + P['cemetery_rear'][0]) / 2) + 150, round((P['cemetery_river'][1] + P['cemetery_rear'][1]) / 2)]),
    dict(name="Jourdan's plantation", at=[P['jourdan'][0] - 300, P['jourdan'][1] - 220]),
    dict(name="Thornton's landing (about here)", at=[LANDING[0] - 380, LANDING[1] - 120], **{"from": D(8, "05:30")}),
    dict(name="to New Orleans, six miles", **label_on((-4300, 1730), (-4100, 1650), 60)),
    dict(name="to the head of Villeré's canal and Bayou Bienvenu", at=[3450, 4330]),
]
for f in features:
    if "at" in f and f.get("name") and f.get("type") != "smoke" and "Mississippi" not in f["name"]: assert not wet(f["at"]), (f["name"], "a label in the river")

# ---- order of battle: (id, side, short, name, commander, type, strength, extra) ----
OOB = [
    # Jackson's army; the strengths are Latour's for 23 December where he gives them, and for the line on 8 January
    ("us7", "american", "7th U.S.", "7th U.S. Infantry", "Maj. Henry Peire", "infantry", 465, {}),
    ("us44", "american", "44th U.S.", "44th U.S. Infantry; Col. Ross commands the right of the line", "Lt. Baker", "infantry", 331, {}),
    ("marines", "american", "Marines", "U.S. Marines", "Lt. Bellevue", "infantry", 50, {}),
    ("plauche", "american", "Plauché", "Battalion of Orleans, the uniformed volunteer companies of New Orleans", "Maj. Jean Baptiste Plauché", "infantry", 289, {}),
    ("daquin", "american", "Daquin", "Daquin's battalion of free men of colour, from Saint-Domingue", "Maj. Louis Daquin", "infantry", 150, {}),
    ("lacoste", "american", "Lacoste", "Lacoste's battalion of free men of colour", "Maj. Pierre Lacoste", "infantry", 280, {}),
    ("beale", "american", "Beale's rifles", "New Orleans volunteer riflemen", "Capt. Thomas Beale", "riflemen", 30, dict(loose=True)),
    ("coffee", "american", "Coffee", "Coffee's Tennessee mounted gunmen, dismounted, with Jugeant's Choctaws: 732 fighting men on 23 December, about 500 on the line in the wood on 8 January", "Brig. Gen. John Coffee", "riflemen", 732, dict(ranks=1)),
    ("carroll", "american", "Carroll", "Carroll's West Tennessee militia, three regiments", "Maj. Gen. William Carroll", "militia", 1100, {}),
    ("adair", "american", "Adair", "Adair's Kentucky militia (Slaughter's and Mitchusson's regiments), the second line behind Carroll", "Brig. Gen. John Adair", "militia", 526, {}),
    ("harrison", "american", "Harrison", "Harrison's Kentucky battalion, in reserve", "Maj. Reuben Harrison", "militia", 305, {}),
    ("hinds", "american", "Hinds", "Hinds's Mississippi dragoons, with Ogden's and Chauveau's horse, in reserve", "Maj. Thomas Hinds", "cavalry", 230, {}),
    ("ross", "american", "Ross", "A company of the 7th in the unfinished redoubt, with guns of the 44th", "Lt. Ross", "infantry", 60, {}),
    ("bat1", "american", "Battery 1", "Battery No. 1: two brass 12-pounders and a 6-inch howitzer", "Capt. Humphreys", "artillery", 36, dict(guns=3)),
    ("bat2", "american", "Battery 2", "Battery No. 2: one 24-pounder, served by sailors from the Carolina", "Lt. Norris", "artillery", 12, dict(guns=1)),
    ("bat3", "american", "Battery 3", "Battery No. 3: two 24-pounders, served by Baratarians", "Capts. Dominique You and Beluche", "artillery", 24, dict(guns=2)),
    ("bat4", "american", "Battery 4", "Battery No. 4: one 32-pounder, a naval gun", "Lt. Crawley", "artillery", 12, dict(guns=1)),
    ("bat5", "american", "Battery 5", "Battery No. 5: two 6-pounders", "Col. Perry and Lt. Kerr", "artillery", 24, dict(guns=2)),
    ("bat6", "american", "Battery 6", "Battery No. 6: one brass 12-pounder", "Gen. Garrigues Flaujeac", "artillery", 12, dict(guns=1)),
    ("bat7", "american", "Battery 7", "Spotts's guns: two 6-pounders on 23 December; on the line, Battery No. 7, an 18-pounder culverin and a 6-pounder", "Lts. Spotts and Chauveau", "artillery", 24, dict(guns=2)),
    ("bat8", "american", "Battery 8", "Battery No. 8: a small brass carronade by Latour's list, a 12-pounder by his account of Pakenham's death", "a corporal of artillery", "artillery", 12, dict(guns=1)),
    ("carolina", "american", "Carolina", "The schooner Carolina: three 9-pounders and twelve 12-pounder carronades", "Capt. Henly, with Patterson aboard", "artillery", 100, dict(guns=5)),
    ("louisiana", "american", "Louisiana", "The Louisiana, which fired 'upwards of eight hundred shot' on 28 December", "", "artillery", 60, dict(guns=4)),
    ("patterson", "american", "Patterson", "Patterson's marine battery on the west bank: two 12-pounders landed on 29 December, then a 24-pounder, four more 12-pounders and two more 24-pounders, with a hot-shot furnace", "Patterson", "artillery", 30, dict(guns=9)),
    ("morgan", "american", "Morgan", "Louisiana militia on Morgan's line, the 2nd militia brigade", "Brig. Gen. David B. Morgan", "militia", 540, {}),
    ("morgan_guns", "american", "Morgan's guns", "One 12-pounder and two 6-pounders, the only cannon on Morgan's line", "", "artillery", 30, dict(guns=3)),
    ("arnaud", "american", "Arnaud's picket", "Arnaud's advanced picket of 100 men, fifteen of them without arms", "Maj. Paul Arnaud", "militia", 100, {}),
    ("davis", "american", "Davis", "Davis's Kentucky detachment: about 500 set out, about 250 armed men reached Morgan's line", "Davis", "militia", 250, {}),
    # Pakenham's army: Keane's advance on 23 December, split evenly from its 1,680, then the 25 December headcounts and
    # Pringle's other ranks for 8 January
    ("r85", "british", "85th", "85th Foot, the head of the advance on 23 December and of Thornton's crossing on 8 January", "Col. William Thornton", "light_infantry", 560, {}),
    ("r95", "british", "95th", "95th Foot (rifles)", "Maj. Gen. John Keane (brigade)", "riflemen", 560, {}),
    ("r4", "british", "4th", "4th Foot", "Maj. Gen. Samuel Gibbs (brigade), mortally wounded", "infantry", 560, dict(ranks=12)),
    ("r21", "british", "21st", "21st Fusiliers", "Maj. Gen. Samuel Gibbs (brigade), mortally wounded", "infantry", 873, dict(ranks=12)),
    ("r93", "british", "93rd", "93rd Highlanders", "Maj. Gen. John Keane (brigade), wounded", "infantry", 850, dict(ranks=12)),
    ("r44", "british", "44th", "44th Foot, which was to carry the fascines and ladders", "Maj. Gen. Samuel Gibbs (brigade), mortally wounded", "infantry", 552, dict(ranks=12)),
    ("wi1", "british", "1st W.I.", "1st West India Regiment", "Maj. Gen. John Keane (brigade), wounded", "infantry", 755, {}),
    ("wi5", "british", "5th W.I.", "5th West India Regiment", "Maj. Gen. Samuel Gibbs (brigade), mortally wounded", "infantry", 570, {}),
    ("r7", "british", "7th", "7th Fusiliers, in Lambert's reserve", "Maj. Gen. John Lambert", "infantry", 750, {}),
    ("r43", "british", "43rd", "43rd Light Infantry, in Lambert's reserve", "Maj. Gen. John Lambert", "light_infantry", 820, {}),
    ("ld14", "british", "14th L.D.", "14th Light Dragoons, dismounted, in reserve", "Maj. Gen. John Lambert", "infantry", 295, {}),
    ("rennie", "british", "Rennie", "Light companies of the 4th and 21st, along the river", "Lt. Col. Rennie (killed)", "light_infantry", 150, {}),
    ("seamen", "british", "Seamen", "Seamen of the fleet, with Thornton", "Capt. Rowland Money RN (killed)", "infantry", 200, {}),
    ("rmar", "british", "Royal Marines", "Royal Marines, with Thornton", "Maj. Adair RM", "infantry", 100, {}),
    ("brL", "british", "Left battery", "The left battery of 1 January: two 12-pounders", "Lt. Col. Alexander Dickson", "artillery", 68, dict(guns=2)),
    ("brC", "british", "Centre battery", "The centre battery of 1 January: eight 18-pounders and 24-pounder carronades; on the night of 7 January a battery about 800 yards from the line", "Lt. Col. Alexander Dickson", "artillery", 271, dict(guns=8)),
    ("brR", "british", "Right battery", "The right battery of 1 January: 'eight pieces of cannon and cannonades'", "Lt. Col. Alexander Dickson", "artillery", 271, dict(guns=8)),
]
BASE = {row[0]: row for row in OOB}
SHIPS = {"carolina", "louisiana"}

units, events = [], []

battle = dict(
    id="new-orleans", name="Battle of New Orleans", date="1814-12-23", dateText="23 December 1814 to 8 January 1815", place="Chalmette, below New Orleans, Louisiana",
    origin=dict(lat=LAT0, lon=LON0), extent=9000, start=START, end=END, sunrise="06:57", sunset="17:17", speed=60, lapse=7200, menPerDot=10,
    water=WATER, terrainExaggeration=3, contourInterval=1, trees=dict(density=0.0012, clear=[PLAIN, WEST_PLAIN]), fields=FIELDS,
    wind=dict(x=0.4, y=0.2), view=dict(x=0, y=0, width=9000),
    sides=dict(american=dict(name="Americans (Jackson)", color="#27497f", light="#6f8fc4", dark="#12254a"),
               british=dict(name="British (Pakenham, then Lambert)", color="#b3331f", light="#d87a68", dark="#5a150c")),
    features=features, units=units, events=events,
    tints=[dict(color="rgba(232,234,236,0.5)", **{"from": D(8, "05:30"), "until": D(8, "07:00")}), dict(color="rgba(232,234,236,0.3)", **{"from": D(1, "06:00"), "until": D(1, "09:30")})],
    outcome={"result": "American victory: the assault on Line Jackson beaten off; the west bank taken and given up", "losses": [
        ["american", "8 January, both banks: 71 by Butler's return of 16 January (13 killed, 39 wounded, 19 missing); on this bank 11 killed and 23 wounded. The whole campaign: 333 (55 killed, 185 wounded, 93 missing)."],
        ["british", "8 January: 2,037 by Remini (291 killed, 1,262 wounded, 484 missing); four returns give 386 killed, 1,516 wounded and 552 missing; Latour says at least 3,000. Pakenham and Gibbs killed, Keane wounded. The campaign: 2,459 by the official returns."]],
        "note": "The peace had been signed at Ghent on 24 December 1814, the day after the night battle. The sources' clock times are the diarists' watches, good to about a quarter of an hour."},
    sources=[
        "Arsène Lacarrière Latour, <a href='https://archive.org/details/historicalmemoi00latogoog' target='_blank'><i>Historical Memoir of the War in West Florida and Louisiana in 1814-15</i></a> (Philadelphia, 1816), with its appendix of Jackson's, Patterson's, Keane's and Lambert's reports and Butler's return: the line, its length and its eight batteries by their distances from the bank, the strengths on the line, the night battle's times, Morgan's line and Patterson's battery. Latour was Jackson's chief engineer. Read in the Internet Archive's text, not his atlas.",
        "J. Fred Roush, <a href='https://npshistory.com/handbooks/historical/29/' target='_blank'><i>Chalmette National Historical Park</i></a>, National Park Service Historical Handbook 29 (1954, revised 1958): the night battle, the mud rampart, 28 December, 1 January, 8 January, the river's loss of the bank and the guide to the nearby sites.",
        "Wikipedia, <a href='https://en.wikipedia.org/wiki/Battle_of_New_Orleans' target='_blank'>Battle of New Orleans</a>, <a href='https://en.wikipedia.org/wiki/Battle_of_New_Orleans_order_of_battle:_American' target='_blank'>order of battle: American</a> and <a href='https://en.wikipedia.org/wiki/Battle_of_New_Orleans_order_of_battle:_British' target='_blank'>order of battle: British</a> (read 23 October 2026): the British strengths for 8 January from the WO 17 monthly returns and Pringle, the regimental losses, the rocket at 6:20, Remini's totals and the American aggregates. Remini, Reilly, Owsley and Dickson's journal are quoted only through it.",
        "Places: OpenStreetMap contributors (ODbL) for the Chalmette Monument, the surviving trace of the Rodriguez Canal, the National Cemetery and the Jourdan plantation plaque; the de la Ronde ruins from the Historical Marker Database's position for the Chalmette Plantations marker in the median of St. Bernard Highway, opposite the ruins. The National Register nomination for Chalmette Battlefield (seen only in search excerpts) gives the 200 feet of bank the river has taken.",
        "Terrain: USGS 3DEP elevation at 10 m, sampled to 22.5 m. The river is traced from the survey's flattened water surface, and the bank at the line moved out to 200 feet beyond the park's river edge, over about 1.6 km. The modern levee, the refinery's fill and the canal banks are flattened to the height of the natural bank, the drained suburbs raised to sea level and the swamp held below 1 m, so the ground reads as it did in 1815. Sunrise and sunset for 8 January from the NOAA solar formulae, local mean time; the map uses them for every day, so dusk on 23 December falls eleven minutes late.",
        "What is reconstructed: the 1815 bank, the levee and the river road, which are placed 20 and 50 m inside it; the swamp's edge, from Latour's distances; the cane fields' boundaries; Villeré's and Macarty's houses, the redoubt, Morgan's line, Patterson's battery, Arnaud's picket and Thornton's landing, labelled 'about here'; the night battle's ground and the camp, from the plantation names; the British columns on 28 December, drawn as the brigades of 8 January; Rennie's party, about 150 by guess, taken from the 4th and 21st; Spotts's two guns of 23 December drawn as Battery 7, which he commanded; and every loss within a day, shared among the units engaged in proportion to their strength. The works are drawn whole from 24 December. Carroll's, Lacoste's and Hinds's men stand on the line from 24 December and Morgan's from 1 January, since the sources read do not say when each took post. The Louisiana's station, crew and guns are not in them either. Jones's light companies on the swamp flank, the 95th's and 7th's companies with Keane and the rocket troop are not drawn.",
    ],
)
json.dump(battle, open(HERE + "battle.json", "w"), indent=1)
print(len(units), "units,", len(events), "events,", len(features), "features,", len(FIELDS), "fields")
