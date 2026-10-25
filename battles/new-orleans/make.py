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
def regroup(id, t, n):  # a change of strength that is not a loss: hidden for a minute, so no casualty markers are left
    s = carried(id, "state"); keys(id, [K(t, last(id), state="hidden"), K(plus(t, 1), last(id), state=s, strength=n)])
PACE = 4  # km/h, a column of foot on the road
def walk(t0, pts, state="column", kmh=PACE):  # keys along a path at a marching pace
    pts = [p for i, p in enumerate(pts) if i == 0 or math.dist(p, pts[i - 1]) > 5]
    t, out = sec(t0), []
    for i, p in enumerate(pts):
        if i: t += math.dist(pts[i - 1], p) / (kmh / 3.6)
        out.append(K(fmt(t), p, h=heading(p, pts[i + 1]) if i + 1 < len(pts) else heading(pts[i - 1], p), **(dict(state=state) if i == 0 else {})))
    return out
def move(id, t0, pts, h=None, state="line", moving="column", kmh=PACE):  # from where it stands along pts; returns the arrival time
    if sec(t0) - sec(KEYS[id][-1]["t"]) > 120: at(id, plus(t0, -1))  # stand until the minute before, then turn and go
    ks = walk(t0, [last(id)] + pts, moving, kmh)
    if len(ks) > 1: ks[-1]["state"] = state
    else: ks[0]["state"] = state
    if h is not None: ks[-1]["h"] = h
    keys(id, ks); return ks[-1]["t"]
def lose(id, t0, t1, n): at(id, t0); at(id, t1, strength=carried(id, "strength") - n)
def share(total, ids):  # a day's loss shared among units in proportion to their strength, largest remainders first
    w = {i: carried(i, "strength") for i in ids}; raw = {i: total * w[i] / sum(w.values()) for i in ids}; n = {i: math.floor(raw[i]) for i in ids}
    for i in sorted(ids, key=lambda i: raw[i] - n[i], reverse=True)[:total - sum(n.values())]: n[i] += 1
    return n
LINE_AT = dict(beale=(8, 25), us7=(85, 28), plauche=(175, 28), lacoste=(230, 28), daquin=(290, 28), us44=(378, 28), marines=(520, 28), carroll=(680, 30),
               adair=(680, 110), coffee=(1150, 25), harrison=(420, 320), hinds=(250, 480), **{f"bat{i + 1}": (d, 6) for i, d in enumerate(BATT_D)})
POST = {k: line(*v) for k, v in LINE_AT.items()}
BATTERIES = [f"bat{i}" for i in range(1, 9)]
ON_LINE = ["beale", "us7", "plauche", "lacoste", "daquin", "us44", "marines", "carroll", "adair", "coffee"]

# ---- 23 December: the landing and the night battle ----
# Keane's advance comes down Villeré's canal from the swamp and takes the house about half past eleven, then camps on
# the river road. Jackson comes down the river road from the city; Coffee's mounted men reach de la Ronde's at
# nightfall, the main column the British camp about seven. The Carolina opens at half past seven, the land attack
# goes in half an hour later, and both sides draw off about half past nine.
CAMP23 = {"r85": (2300, -1150), "r95": (2050, -900), "r4": (2750, -1150), "r93": (2950, -1000)}
for id, p0, n in (("r85", (3460, 900), 0), ("r95", (3470, 1150), 1), ("r4", (3480, 1400), 2)):
    appear(id, START, p0, "column", h=190)
    move(id, START, [(3420 - 60 * n, -350 - 60 * n)], h=270, kmh=3)
    at(id, D(23, "11:40"), state="column"); move(id, D(23, "11:41"), [CAMP23[id]], h=270)
appear("carolina", D(23, "17:20"), CENTRE[1], "column")
move("carolina", D(23, "17:20"), [p for p in CENTRE[2:] if p[0] < 2100] + [CAROLINA], h=90, kmh=4)
keys("carolina", [K(D(23, "19:30"), CAROLINA, state="firing"), K(D(23, "21:00"), CAROLINA, state="line")])
# Coffee, with Beale's rifles, up the de la Ronde avenue to the house at nightfall, then round against the British right
for id, t, dx in (("coffee", "16:00", 0), ("beale", "16:06", 80)):
    appear(id, D(23, t), ENTRY_E, "column")
    move(id, D(23, t), road(ENTRY_E, on_road(DLR[0])) + [(DLR[0] + dx, DLR[1])], h=60, kmh=5.8)
    move(id, D(23, "18:50"), [(1500 + dx, 50)], h=150)
    move(id, D(23, "20:00"), [(2100 + dx, -450)], h=150, state="firing", moving="charge")
JACKSON = [("marines", "17:15", on_road(2050), on_road(1300), on_road(1200)), ("bat7", "17:18", on_road(1980), on_road(1220), on_road(1150)),
           ("us7", "17:21", (2000, -1200), on_road(1120), (1100, -1050)), ("us44", "17:26", (1950, -1060), on_road(1020), (1000, -1000)),
           ("plauche", "17:31", (1900, -900), (1150, -950), (1050, -850)), ("daquin", "17:36", (1850, -760), (1100, -800), (1000, -700))]
for id, t, fight, wait, rally in JACKSON:
    appear(id, D(23, t), ENTRY_E, "column")
    move(id, D(23, t), road(ENTRY_E, on_road(wait[0])) + [wait], h=90, kmh=4.5)
    move(id, D(23, "20:00"), [fight], h=80, state="firing")
# the British stand to; the 21st comes up from the canal against Coffee, the 93rd later in the night
keys("r85", [K(D(23, "20:00"), CAMP23["r85"], state="firing", h=260)]); keys("r4", [K(D(23, "20:00"), CAMP23["r4"], state="column")])
move("r4", D(23, "20:00"), [(2300, -950)], h=250, state="firing")
keys("r95", [K(D(23, "20:00"), CAMP23["r95"], state="firing", h=320)])
appear("r21", D(23, "20:15"), VILLERE, "column"); move("r21", D(23, "20:15"), [(2350, -600)], h=300, state="firing")
appear("r93", D(23, "22:30"), VILLERE, "column"); move("r93", D(23, "22:30"), [CAMP23["r93"]], h=270)
# the losses: 213 American (24 killed, 115 wounded, 74 missing) and 277 British, shared by strength
for id, n in share(213, ["coffee", "beale", "us7", "us44", "marines", "plauche", "daquin", "bat7"]).items(): lose(id, D(23, "20:15"), D(23, "20:49" if id in ("coffee", "beale") else "21:30"), n)
for id, dx in (("coffee", 0), ("beale", 80)): move(id, D(23, "20:50"), [(1450 + dx, -200)], h=150, state="firing", moving="retreat")
for id, n in share(277, ["r85", "r95", "r4", "r21"]).items(): lose(id, D(23, "20:45"), D(23, "21:30"), n)
for id in ("r85", "r95", "r4", "r21"): at(id, D(23, "21:31"), state="line")
for id, t, fight, wait, rally in JACKSON: move(id, D(23, "21:31"), [rally], h=90, moving="retreat")
for id, dx in (("coffee", 0), ("beale", 80)): move(id, D(23, "21:31"), [(DLR[0] + dx, DLR[1] - 100)], h=90, moving="retreat")
# 24 December, four in the morning: back two miles to the Rodriguez Canal
for n, id in enumerate(["marines", "bat7", "us7", "us44", "plauche", "daquin", "coffee", "beale"]):
    move(id, D(24, f"04:{n * 2:02d}"), ([on_road(-800)] if id in ("marines", "bat7", "us7", "us44") else []) + [POST[id]], h=HUS)
for id, n in (("us7", 430), ("us44", 240), ("coffee", 500), ("plauche", 289), ("daquin", 150), ("beale", 30), ("marines", 50), ("bat7", 24)): regroup(id, D(24, "06:00"), n)

# ---- 24 December to 7 January: the line, the camp, the two probes ----
for id, t in (("carroll", "08:00"), ("lacoste", "08:10"), ("hinds", "08:16")):
    appear(id, D(24, t), ENTRY_E, "column"); move(id, D(24, t), road(ENTRY_E, on_road(-2300)) + [POST[id]], h=HUS, kmh=6 if id == "hinds" else PACE)
for id in BATTERIES:
    if id != "bat7": appear(id, D(24, "10:00"), POST[id], h=HUS)
# the British move up to de la Ronde's and Bienvenu's by the river; the rest of the army joins them on the 25th
CAMP_A = {"r85": (-150, -520), "r95": (200, -650), "r4": (550, -800), "r21": (900, -900), "r93": (1250, -980), "wi5": (350, -420), "r44": (750, -600), "wi1": (1150, -700), "ld14": (1550, -900)}
CAMP_B = {k: (x, y + 700) for k, (x, y) in CAMP_A.items()}
for n, id in enumerate(["r85", "r95", "r4", "r21", "r93"]): move(id, D(24, f"08:{n * 4:02d}"), [CAMP_A[id]], h=HBR)
for n, id in enumerate(["wi5", "r44", "wi1", "ld14"]):
    appear(id, D(25, f"12:{n * 5:02d}"), VILLERE, "column"); move(id, D(25, f"12:{n * 5:02d}"), [CAMP_A[id]], h=HBR)
# 27 December: a British battery burns the Carolina with hot shot
at("carolina", D(27, "07:00"), state="retreat"); at("carolina", D(27, "08:30"), state="hidden")
# 28 December: the reconnaissance in force, in two columns by the river and the swamp, skirmishers between
appear("louisiana", D(28, "06:00"), LOUISIANA_AT, h=120)
keys("louisiana", [K(D(28, "09:00"), LOUISIANA_AT, state="firing"), K(D(28, "11:30"), LOUISIANA_AT, state="line"), K(D(28, "18:00"), LOUISIANA_AT, state="hidden")])
RIVER_COL = {"r93": front(60, 760), "r85": front(90, 900), "wi1": front(110, 1050)}
SWAMP_COL = {"r21": front(780, 700), "r4": front(760, 830), "r44": front(740, 960), "wi5": front(720, 1090)}
for n, (id, p) in enumerate([*RIVER_COL.items(), *SWAMP_COL.items(), ("r95", front(420, 620))]):
    move(id, D(28, f"08:{30 + n * 2:02d}"), [p], h=HBR, state="firing", kmh=3)
for id in [*BATTERIES]: keys(id, [K(D(28, "09:20"), POST[id], state="firing"), K(D(28, "11:30"), POST[id], state="line")])
lose("carroll", D(28, "09:40"), D(28, "10:40"), 15)  # Hutchinson's detachment, driven in on the swamp flank
for id, n in share(56, list(RIVER_COL)).items(): lose(id, D(28, "09:50"), D(28, "10:30"), n)
for n, id in enumerate([*RIVER_COL, "r95", *SWAMP_COL]):
    move(id, D(28, f"{10 if id in RIVER_COL else 11}:{30 + n:02d}"), [CAMP_A[id]], h=HBR, moving="retreat" if id in RIVER_COL else "column")
# 29 December: Patterson's first guns ashore on the west bank; Morgan's militia drawn from 1 January
appear("patterson", D(29, "18:00"), PATTERSON, h=heading(PATTERSON, front(300, 500)))
appear("morgan", D(1, "00:00"), mline(110, -25), h=HUS); appear("morgan_guns", D(1, "00:00"), mline(50, -12), h=HUS)
# 1 January: batteries built overnight 600 yards out; the duel from breakfast to one; a probe on the swamp flank; the
# infantry formed for an assault that Pakenham calls off at three
for id, p in BR_BATT.items(): appear(id, D(1, "02:00"), p, h=HBR)
ASSAULT1 = {"r85": front(150, 900), "r93": front(250, 900), "wi1": front(200, 1050), "r21": front(650, 900), "r4": front(750, 900), "r44": front(600, 1050), "wi5": front(700, 1050), "r95": front(500, 950)}
for n, (id, p) in enumerate(ASSAULT1.items()): move(id, D(1, f"06:{30 + n * 2:02d}"), [p], h=HBR, kmh=3)
for id in [*BR_BATT, *BATTERIES, "patterson"]: at(id, D(1, "08:00"), state="firing")
for id, n in [*share(34, BATTERIES).items(), *share(78, list(BR_BATT)).items()]: lose(id, D(1, "08:10"), D(1, "12:50"), n)
for id in [*BR_BATT, *BATTERIES, "patterson"]: at(id, D(1, "13:00"), state="line")
move("r95", D(1, "09:00"), [front(1050, 300)], h=HBR, state="firing")
keys("coffee", [K(D(1, "09:20"), POST["coffee"], state="firing"), K(D(1, "11:00"), POST["coffee"], state="line")])
move("r95", D(1, "11:00"), [ASSAULT1["r95"]], h=HBR, moving="retreat")
for n, id in enumerate(ASSAULT1): move(id, D(1, f"15:{n * 2:02d}"), [CAMP_A[id]], h=HBR)
for id in BR_BATT: at(id, D(1, "22:00"), state="hidden")
# after the duel the camp moves back from the river to the back grounds of de la Ronde's and Bienvenu's
for n, id in enumerate(CAMP_A): move(id, D(2, f"10:{n * 3:02d}"), [CAMP_B[id]], h=HBR)
# 4 January: the Kentuckians; 6 January: Lambert with the 7th and 43rd
for id, t in (("adair", "12:00"), ("harrison", "12:10")):
    appear(id, D(4, t), ENTRY_E, "column"); move(id, D(4, t), road(ENTRY_E, on_road(-2300)) + [POST[id]], h=HUS)
for id, t, p in (("r7", "12:00", (1550, 100)), ("r43", "12:06", (1850, -50))):
    appear(id, D(6, t), VILLERE, "column"); move(id, D(6, t), [p], h=HBR); CAMP_B[id] = p
# 7 January: the strengths of 8 January, Pringle's other ranks; Rennie's light companies come out of the 4th and 21st
for id, n in (("r85", 298), ("r4", 672), ("r21", 725), ("r93", 775), ("r44", 427), ("wi1", 755), ("wi5", 570)): regroup(id, D(7, "18:00"), n)
move("r85", D(7, "19:00"), [MOUTH], h=200)
for id in ("seamen", "rmar"): appear(id, D(7, "22:00"), (MOUTH[0] + (60 if id == "seamen" else 120), MOUTH[1] + 40), h=200)
appear("arnaud", D(7, "18:00"), PICKET, h=heading(PICKET, (500, -1700)))
appear("ross", D(7, "18:00"), REDOUBT, h=HUS)

# ---- 8 January ----
# The boats take the night to reach the river and the crossing is hours late; the first 500 are over by half past five,
# a thousand yards below the mouth. Davis's Kentuckians reach Morgan's line at four.
for id in ("r85", "seamen", "rmar"): at(id, D(8, "03:00"), state="hidden")
appear("davis", D(8, "03:00"), ENTRY_W, "column"); move("davis", D(8, "03:00"), road(ENTRY_W, on_road(R0[0] - 60, ROAD_W), ROAD_W) + [mline(450, -20)], h=HUS)
appear("r85", D(8, "05:30"), LANDING, "column", h=290); appear("seamen", D(8, "05:30"), (LANDING[0] + 80, LANDING[1] - 30), "column", h=290)
appear("rmar", D(8, "06:00"), (LANDING[0] + 40, LANDING[1] - 80), "column", h=290)
# Pakenham's columns form in the dark, Gibbs's toward Battery 7 and Keane's by the river, Lambert's reserve behind
FORM = {"r21": front(560, 560), "r4": front(520, 650), "wi5": front(480, 760), "r44": front(380, 920), "r93": front(150, 600), "wi1": front(120, 760),
        "rennie": front(30, 520), "r95": front(450, 450), "r7": front(250, 950), "r43": front(600, 950), "ld14": front(420, 1060)}
appear("rennie", D(8, "03:00"), CAMP_B["r4"], "column")
for n, (id, p) in enumerate(FORM.items()): move(id, D(8, f"03:{10 + n * 3:02d}"), [p], h=HBR, state="column", kmh=3)
appear("brC", D(8, "03:00"), front(400, 731), h=HBR)
keys("brC", [K(D(8, "06:20"), front(400, 731), state="firing"), K(D(8, "09:00"), front(400, 731), state="line")])
for id in [*BATTERIES, "patterson"]: at(id, D(8, "06:20"), state="firing")
# the rocket at twenty past six; Rennie on the redoubt, Gibbs on Battery 7, the 93rd across the field; broken in
# about twenty-five minutes, the columns rally four hundred yards out. Losses are the regimental returns.
LOSS = {"r4": 301, "r21": 411, "rennie": 100, "r44": 278, "wi5": 1, "r93": 164, "wi1": 29, "r95": 112, "r7": 102, "r43": 218}
move("rennie", D(8, "06:20"), [(REDOUBT[0] + 10 * V[0], REDOUBT[1] + 10 * V[1])], h=HBR, state="firing", moving="charge", kmh=5)
keys("ross", [K(D(8, "06:22"), REDOUBT, state="firing")]); move("ross", D(8, "06:29"), [line(30, 40)], h=HUS, state="firing", moving="retreat")
lose("rennie", D(8, "06:31"), D(8, "06:38"), 70); move("rennie", D(8, "06:39"), [front(40, 380)], h=HBR, state="line", moving="rout", kmh=5)
lose("rennie", plus(KEYS["rennie"][-1]["t"], 1), D(8, "07:10"), 30)
move("ross", D(8, "06:50"), [REDOUBT], h=HUS, state="firing")
move("r95", D(8, "06:20"), [front(450, 160)], h=HBR, state="firing", moving="charge", kmh=2.5)
for id, d, f in (("r21", 560, 25), ("r4", 520, 70)): move(id, D(8, "06:20"), [front(d, f)], h=HBR, state="charge", moving="charge", kmh=2.2)
move("r44", D(8, "06:20"), [front(540, 300)], h=HBR, moving="column", state="charge", kmh=3.5)
move("r44", D(8, "06:33"), [front(540, 110)], h=HBR, state="firing", moving="charge", kmh=2.5)
move("wi5", D(8, "06:22"), [front(500, 460)], h=HBR, kmh=2.5)
move("r93", D(8, "06:22"), [front(470, 220)], h=HBR, state="firing", moving="charge", kmh=2.5)
move("wi1", D(8, "06:24"), [front(150, 520)], h=HBR, kmh=2.5)
for id in ("r21", "r4", "r44", "r93", "r95", "wi5", "wi1"): lose(id, max(KEYS[id][-1]["t"], D(8, "06:36")), D(8, "06:44"), round(LOSS[id] * 0.7))
for id in ON_LINE: keys(id, [K(D(8, "06:25"), POST[id], state="firing")])
RALLY = {"r21": front(560, 366), "r4": front(520, 420), "r44": front(480, 480), "r93": front(380, 420), "r95": front(450, 400), "wi5": front(480, 600), "wi1": front(150, 600)}
for id, p in RALLY.items(): move(id, D(8, "06:45"), [p], h=HBR, moving="retreat", kmh=5)
for id in RALLY: lose(id, plus(KEYS[id][-1]["t"], 1), D(8, "08:25"), LOSS[id] - round(LOSS[id] * 0.7))
# Lambert sends part of the reserve forward, then halts it; it lies down in the stubble about 650 yards out
for id, d in (("r7", 250), ("r43", 600), ("ld14", 420)): move(id, D(8, "07:00"), [front(d, 594 if id != "ld14" else 700)], h=HBR)
for id in ("r7", "r43"): lose(id, plus(KEYS[id][-1]["t"], 1), D(8, "14:00"), LOSS[id])
for id, n in share(34, ON_LINE).items(): lose(id, D(8, "06:30"), D(8, "08:25"), n)
for id in ON_LINE: at(id, D(8, "08:30"), state="line")
at("ross", D(8, "08:30"), state="line")
for id in RALLY: move(id, D(8, "09:00"), [(RALLY[id][0] + 250 * V[0], RALLY[id][1] + 250 * V[1])], h=HBR)
for id in BATTERIES: at(id, D(8, "14:00"), state="line")
# the west bank: Thornton up the bank, Arnaud's picket turned, then Davis, and Morgan's line breaks; Patterson spikes his
# guns. About ten Lambert orders Gubbins back.
t_pk = move("r85", D(8, "06:00"), road(on_road(LANDING[0], ROAD_W), on_road(PICKET[0] + 250, ROAD_W), ROAD_W), h=290, state="firing", kmh=3.5)
move("seamen", D(8, "06:03"), road(on_road(LANDING[0] + 80, ROAD_W), on_road(PICKET[0] + 380, ROAD_W), ROAD_W), h=290, kmh=3.5)
move("rmar", D(8, "06:10"), road(on_road(LANDING[0] + 40, ROAD_W), on_road(PICKET[0] + 500, ROAD_W), ROAD_W), h=290, kmh=3.5)
keys("arnaud", [K(plus(t_pk, 2), PICKET, state="firing")]); move("arnaud", plus(t_pk, 10), [mline(250, -40)], h=HUS, moving="retreat", kmh=5)
ATTACK_W = {"r85": mline(150, 140), "seamen": mline(40, 170), "rmar": mline(560, 120)}
for id, p in ATTACK_W.items(): move(id, plus(t_pk, 14), [p], h=HBR, state="firing", kmh=3.5)
t_hit = max(KEYS[id][-1]["t"] for id in ATTACK_W)
for id in ("morgan", "morgan_guns", "davis", "arnaud", "patterson"): at(id, plus(t_hit, -10) if id != "patterson" else t_hit, state="firing")
for id, n in share(32, ["morgan", "davis", "arnaud"]).items(): lose(id, plus(t_hit, -5), plus(t_hit, 8), n)
for id, n in (("r85", 44), ("seamen", 20), ("rmar", 18)): lose(id, plus(t_hit, 1), plus(t_hit, 20), n)
FLIGHT = road(on_road(R0[0] - 150, ROAD_W), ENTRY_W, ROAD_W)
move("davis", plus(t_hit, 10), [mline(450, -300)] + FLIGHT, h=300, state="line", moving="rout", kmh=5.5)
for id, dt_ in (("morgan", 20), ("arnaud", 21), ("morgan_guns", 22)): move(id, plus(t_hit, dt_), FLIGHT, h=300, state="line", moving="rout" if id != "morgan_guns" else "retreat", kmh=5 if id != "morgan_guns" else 4)
move("patterson", plus(t_hit, 25), FLIGHT[1:], h=300, state="line", moving="retreat")
for id in ("davis", "morgan", "arnaud", "morgan_guns", "patterson"): at(id, plus(KEYS[id][-1]["t"], 2), state="hidden")
for id, p in (("r85", mline(120, -30)), ("seamen", mline(30, -30)), ("rmar", mline(300, -30))): move(id, plus(t_hit, 25), [p], h=HBR)
for n, id in enumerate(("r85", "seamen", "rmar")): move(id, D(8, f"10:{30 + n * 3}"), road(on_road(last(id)[0], ROAD_W), on_road(LANDING[0] - 100 * n, ROAD_W), ROAD_W), h=110)
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
            assert wet(q) == (id in SHIPS), (id, a["t"], b["t"], q, "a leg through the river" if id not in SHIPS else "a leg over land")
    state = None
    for k in ks:
        state = k.get("state", state)
        assert state == "hidden" or wet((k["x"], k["y"])) == (id in SHIPS), (id, k["t"], (k["x"], k["y"]), "afloat" if id not in SHIPS else "aground")
    units.append(dict(id=id, side=side, name=name, short=short, commander=commander, type=type, strength=strength, keys=ks, **extra))

# ---- chapters: (time, title, text, camera centre, metres across, playback speed, when) ----
# `when` holds a clock time the sources record, or a phrase; without one the card gives the nearest hour.
CHAPTERS = [
    (START, "New Orleans, December 1814", "The first British division reached the far end of Villeré's canal, in the swamp beyond the north edge of this map, by four this morning. From there the way to the river is about a mile of wood and then nearly two miles of cane fields, by Latour's count. The ground is a strip of sugar plantations between the Mississippi and a cypress swamp. At the Rodriguez Canal it is somewhat more than half a mile deep. New Orleans is six miles upriver, beyond the west edge.", [0, 0], 9000, 300, None),
    (D(23, "11:30"), "Villeré's plantation", "At about half past eleven the British advance surrounds Villeré's house, within nine miles of the city. It is about 1,680 men. The house is the British headquarters from now until 19 January. It is gone: an oil refinery covers the site, and this map places it within about 600 m.", [3000, -500], 3200, 120, "about half past 11"),
    (D(23, "13:30"), "Jackson hears", "Latour, Jackson's engineer, sees the British position at half past one, and Jackson has the news within twenty-five minutes; the park handbook says about one o'clock. By half past two his artillery and the 7th Infantry are formed on the river road.", [2500, -800], 3600, 300, "half past 1"),
    (D(23, "17:00"), "Jackson marches", "Jackson marches at five, by his report of 27 December, and Plauché's battalion comes up about then. Coffee's mounted Tennesseans reach de la Ronde's plantation at nightfall. Latour counts about 1,800 effective men once the horse-holders are left behind; Jackson's own figure is about 1,500. The schooner Carolina, with Patterson aboard, is on its way down the river.", [-1200, -100], 7400, 120, "5 PM"),
    (D(23, "19:30"), "The Carolina", "At about half past seven the Carolina opens on the British camp from the river: three 9-pounders and twelve 12-pounder carronades, with more than 100 men aboard. Patterson wrote of 'about forty minutes of most incessant fire'. Jackson reached the camp about seven.", [2000, -1150], 2600, 60, "about half past 7"),
    (D(23, "20:00"), "The night attack", "About half an hour later Jackson attacks by land. The marines go in along the levee with the 7th and 44th behind them, and Plauché's and Daquin's battalions come up from the rear. Coffee swings through de la Ronde's against the British right. In the dark, the fog and the smoke the fighting breaks into confused clashes, and the 21st, newly arrived, drives Coffee's men back.", [1800, -750], 2400, 60, None),
    (D(23, "21:30"), "The British fall back", "The Carolina stops firing about nine. Latour has the British falling back about half past nine and the fighting over by ten; Keane's despatch says half past twelve, which Latour rejects. The 21st and 93rd reach the camp during the night. Americans lost 24 killed, 115 wounded and 74 missing; the British 46 killed, 167 wounded and 64 missing, which their own report makes 305 and Latour about 400.", [1600, -750], 3000, 120, "about half past 9"),
    (D(24, "04:00"), "Back to the Rodriguez Canal", "At four in the morning Jackson draws back about two miles to the Rodriguez Canal, a disused millrace on the boundary between the Macarty and Chalmette plantations, 10 to 20 feet wide and 4 to 8 feet deep. It runs from the river back into the swamp. On the 24th his men cut the levee to flood the ground in front; the river falls and the flooding fails.", [-500, -200], 4800, 120, "4 AM"),
    (D(24, "09:00"), "Line Jackson", "Behind the canal the men build a wall of mud, driving fence rails into the soil and piling earth against them; the ground is too wet for trenches. Latour gives it as much as twenty feet thick at the top though hardly five feet high, and in the wood a double row of logs with two feet of earth between. He measures 815 toises, about a mile, somewhat more than half of it from the river to the wood. It is drawn here as it stood by 8 January, with its eight batteries; it grew over the fortnight. Jackson's headquarters are in the Macarty house, behind the right.", [-1350, 450], 2300, 120, None),
    (D(27, "07:00"), "The Carolina burned", "At seven on the morning of the 27th a British battery opens on the Carolina with hot shot, and burns her.", [2100, -1300], 2400, 60, "7 AM"),
    (D(28, "08:30"), "The reconnaissance in force", "On the 28th, as soon as the mist clears, the British come on in two columns, one by the river and one by the swamp, with skirmishers between. The Louisiana, which fires upwards of eight hundred shot today, and the batteries on the line break the river column. On the swamp flank Hutchinson's Tennessee detachment is driven in. Pakenham calls the attack off. The Americans lose 7 killed and 8 or 10 wounded; the British 16 killed, 38 wounded and 2 missing by one count, 9 killed and 8 wounded by another, and two to three hundred by Latour's guess.", [-900, 200], 3200, 60, "as soon as the mist cleared"),
    (D(1, "08:00"), "The artillery duel", "Overnight the British have built batteries about 600 yards from the line: two 12-pounders on the left, eight 18-pounders and 24-pounder carronades in the centre, and eight more pieces on the right. They open in fog, during breakfast by one account, and their first target is the Macarty house. Across the river Patterson has had guns ashore behind the levee since 29 December.", [-1350, 100], 2700, 120, "during breakfast"),
    (D(1, "13:00"), "The duel ends", "By noon the British fire has slackened and by one it has stopped, by the park handbook; Latour has it going on until about three. On the line the 32-pounder of Battery 4, a 24-pounder and a 12-pounder are disabled and two caissons blown up; all three guns are firing again by the 8th. Cotton bales tried in the works catch fire. A British probe on the swamp flank is driven off by Coffee. At three Pakenham calls off the assault. The Americans lose 11 killed and 23 wounded, the British 32 killed, 44 wounded and 2 missing. Once Patterson's battery opens across the river, the British camp moves back from the bank.", [-900, 250], 3400, 120, "1 PM"),
    (D(6, "12:00"), "Reinforcements", "On 4 January some 2,250 Kentucky militia reach Jackson, only 550 of them armed. On the 6th the British finish the cut from Villeré's canal to the river, and Lambert arrives with the 7th and 43rd; about 8,000 British troops have landed. Across the river Morgan's Louisiana militia hold a line on Raguet's old canal, about 200 yards of it dug, with one 12-pounder and two 6-pounders. The canal runs some 2,000 yards back to the wood.", [0, -400], 7600, 300, None),
    (D(8, "01:00"), "The night of the 7th", "Through the night Thornton's boats are dragged along the canal to the river. A dam fails, and the crossing loses four or five hours by Lambert's account, about eight by Thornton's. At one in the morning Patterson learns that the British have launched barges.", [2800, -1500], 4000, 120, "1 AM"),
    (D(8, "05:30"), "Over the river", "Only by half past five are Thornton's first 500 men over, landing about a thousand yards below the point intended; in all about a third of the planned force crosses, 298 of the 85th with seamen and marines. Davis's Kentuckians reached Morgan's line at four after a five-mile march: about 500 set out and about 250 armed men arrived. Morgan has about 640 by the order of battle; Latour says no more than 800, against Thornton's 1,500.", [1200, -1900], 6800, 60, "half past 5"),
    (D(8, "06:00"), "Dawn", "Dawn, Latour writes, 'discovered to us the enemy occupying two-thirds of the space between the wood and the Mississippi'. Jackson has about 3,200 men on the parapet out of about 4,000; the returns give 4,698 on this bank and 546 across the river. Gibbs's brigade is to attack toward Battery 7, Keane's by the river, with Lambert's in reserve. The sun will not be up until about seven, and there is fog.", [-1150, 250], 2300, 30, None),
    (D(8, "06:20"), "The rocket", "At twenty past six a signal rocket goes up; Latour saw 'a Congreve rocket' go off 'from the skirt of the wood, in the direction of the river'. The British guns open on the Macarty house. The 44th, which was to carry the fascines and ladders, has gone to the wrong place, and they are fetched after the column is already moving. The fascines are nine or ten inches thick and four feet long, the ladders ten to twelve feet.", [-1150, 300], 1900, 20, "6:20 AM"),
    (D(8, "06:30"), "The redoubt", "By the river Rennie's light companies of the 4th and 21st come along the bank and take the unfinished redoubt in front of the line, held by a company of the 7th under Lieutenant Ross. The line fires into it, and they are shot down there; Rennie is killed.", [-1620, -40], 900, 20, "about half past 6"),
    (D(8, "06:35"), "Gibbs's column", "Gibbs's column comes on toward Battery 7, about sixty men in front. The fog lifts as it nears the line; Lambert says the columns could be seen 'at more than two hundred yards'. Carroll's Tennesseans and Adair's Kentuckians fire over the mud wall. Keane's 93rd Highlanders cross the field at a slant to join the attack, and lose 164 men by the returns.", [-1250, 450], 1300, 20, "soon after half past 6"),
    (D(8, "06:45"), "Pakenham", "Pakenham is hit in the knee and then 'fatally in the body', and falls 'in the arms of major M'Dougall'. Gibbs is mortally wounded and Keane carried off wounded soon after. Latour says the grape that killed Pakenham came from Battery 8's twelve-pounder, though his own list gives that battery a small brass carronade; the park handbook calls it 'the Mysterious Gun'. The attack has broken after about twenty-five minutes, and the columns fall back to rally about four hundred yards out.", [-1150, 350], 1800, 30, "about a quarter to 7"),
    (D(8, "07:00"), "Lambert", "Lambert, now in command, sends part of the reserve forward, then halts it. The 7th and 43rd lie down in the stubble about 650 yards from the line, where the edition of Dickson's journal counts 182 casualties; the regimental returns give the 7th 102 and the 43rd 218 for the day.", [-1000, 150], 2600, 60, None),
    (D(8, "08:00"), "The west bank", "Across the river Thornton has come up the bank; no clock time for it is recorded. He turns Arnaud's picket of 100, then Davis's Kentuckians, and Morgan's line breaks. Patterson's battery, its fire masked by the militia, spikes its guns and the crews withdraw. Thornton is wounded and Gubbins takes command. Humbert, sent across with 400 reinforcements, is rebuffed by Morgan.", [-1300, -1500], 3600, 60, None),
    (D(8, "08:30"), "Half past eight", "By half past eight the musketry has stopped, by Latour; the British guns stop at nine. Remini puts the British loss at 2,037: 291 killed, 1,262 wounded and 484 missing. By the regimental returns the 21st lost 461, 236 of them missing, the 4th 351 and the 44th 278. On this bank the Americans lost 11 killed and 23 wounded.", [-1150, 300], 2600, 60, "half past 8"),
    (D(8, "10:00"), "Gubbins recalled", "About ten Lambert learns of the success across the river by a rocket from Gubbins. Dickson advises that about two thousand men would be needed to hold the battery, and Lambert orders Gubbins back.", [-300, -1100], 6400, 120, "about 10"),
    (D(8, "14:00"), "Ceasefire", "The American batteries stop firing at two in the afternoon. The British army stays where it is until night, then goes back to its camp.", [-1100, 250], 3200, 120, "2 PM"),
    (D(8, "15:00"), "The truce", "A truce is agreed for burying the dead; Jackson wrote on the 9th that 'upwards of three hundred' had already been handed over for burial. The British leave Villeré's by 19 January, leaving behind, by a letter of Lambert's, 80 men wounded too badly to be taken home, and the last are back aboard the fleet on the 27th. Butler's return of 16 January gives the American loss on 8 January as 71: 13 killed, 39 wounded and 19 missing.", [-900, 150], 4200, 120, None),
    (D(8, "16:00"), "Ghent", "The treaty that ended the war had been signed at Ghent on 24 December, the day after the night battle. Over the whole campaign Butler counted 333 Americans killed, wounded and missing; the British official returns give 2,459.", [0, -300], 9000, 300, None),
]
events = [dict(t=t, title=a, text=b, at=at_, view=v, speed=s, **({"when": w} if w else {})) for t, a, b, at_, v, s, w in CHAPTERS]
for e in events:  # without `when` the card speaks the nearest hour (app.js chapterWhen), so it must be near the frame's clock
    s = sec(e["t"]) % 86400; hh = [n % 12 or 12 for n in (int(s // 3600), int(s // 3600) + 1)]; num = re.search(r"\d+", e.get("when", ""))
    assert not num or int(num[0]) in hh, (e["t"], e["when"], "the card's hour is not the frame's")
    assert "when" in e or abs(s - math.floor(s / 3600 + 0.5) * 3600) <= 15 * 60, (e["t"], e["title"], "give it a when")

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
