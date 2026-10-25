# Builds battles/cantigny/battle.json. Run from the repo root: python3 battles/cantigny/make.py
# Local metres from 49.6660N 2.4990E (x east, y north). The 6 km square holds Cantigny church (-540,-235), the
# jump-off line 800 m west of it, the objective, Villers-Tournelle (-2597,-1260), the Bois St Eloi, des Glands, de
# Cantigny and de Fontaine on the American side, and the Framicourt, Lalval and Voyeux woods the counter-attacks came
# out of. The guns of both sides are off the map. Anchors are OpenStreetMap points; the woods are OpenStreetMap's,
# matched by position to the 1918 names on the First Division G-2's order-of-battle map, the Bois St Eloi moved 300 m
# west to where that map has it. Points in the field orders are on the French Lambert grid, read here against the
# church (grid 122.2, 331.6), good to about 150 m. Clock times are French summer time, GMT+1, as the sources wrote them.
import json, math, re, datetime as dt
HERE = "battles/cantigny/"
LAT0, LON0 = 49.6660, 2.4990
KX, KY = 111320 * math.cos(math.radians(LAT0)), 111320  # tools/fetch_terrain.py's metres per degree
def M(lat, lon): return (round((lon - LON0) * KX), round((lat - LAT0) * KY))
HALF_EXTENT = 3000

# ---- terrain: open chalk plateau, no water; the page reads a zero as a gap in the survey ----
T = json.load(open(HERE + "terrain.json"))
COLS, SP = T["cols"], T["spacing"]; HALF = COLS * SP / 2
assert HALF == HALF_EXTENT, "terrain.json is not the battle's extent"
Z = [round(max(v, 0.1), 2) for v in T["z"]]
if Z != T["z"]: T["z"] = Z; json.dump(T, open(HERE + "terrain.json", "w"), separators=(",", ":"))
def z(x, y):
    c, r = int((x + HALF) / SP), int((HALF - y) / SP)
    return T["z"][r * COLS + c] if 0 <= c < COLS and 0 <= r < COLS else None
def on_land(p): return z(*p) is not None and z(*p) > 0

# ---- places ----
PLACES = {  # OpenStreetMap
    'church': (49.66389, 2.49149), 'cemetery': (49.66700, 2.49250), 'monument': (49.66322, 2.49096),
    'villers': (49.65467, 2.46292), 'fontaine': (49.65647, 2.51685), 'framicourt': (49.67020, 2.52488), 'la_folie': (49.68057, 2.50118),
    'st_aignan': (49.68047, 2.48192), 'le_plessier': (49.67741, 2.46170), 'grivesnes': (49.68784, 2.46861), 'courtemanche': (49.66091, 2.53931),
}
P = {k: M(*v) for k, v in PLACES.items()}
CHURCH = P['church']
def G(ref):  # a point the field orders give in hectometres on the Lambert grid, "12.14" = x 121.2 km, y 331.4 km
    a, b = ref.split('.'); return (round(CHURCH[0] + (120 + int(a) / 10 - 122.2) * 1000), round(CHURCH[1] + (330 + int(b) / 10 - 331.6) * 1000))
# placed from the 1918 maps against the church, labelled "about here"
CHATEAU = (CHURCH[0] + 140, CHURCH[1] - 145)  # Machard's château, 200 m south-east of the church; within 80 m
FONTAINE_CH = (800, -1100)                     # the château of Fontaine, "500 m west of Fontaine"; within 200 m
HILL_104 = (700, -100)                         # within 300 m
SUISSE, CARRE = (-700, -1400), (-600, -1700)   # the Bois Suisse and Bois Carré, gone today

# ---- lines ----
JUMP_OFF = [(-1250, 815), (-1100, 5), (-1350, -185), (-1350, -405), (-1270, -595), (-1170, -805), (-1020, -1125), (-930, -1265), (-110, -1265), (400, -1265)]
OBJECTIVE = [G("19.25"), G("21.21"), G("24.19"), G("26.13"), G("25.09"), (-250, -1265)]
GERMAN_LINE = [(-700, 900), (-750, 0), (-500, -900), (300, -1050), FONTAINE_CH]
def mid(a, b): return (round((a[0] + b[0]) / 2), round((a[1] + b[1]) / 2))
J1, J2, J3 = (-1080, -950), (-1330, -250), (-1190, 470)                  # each battalion's place on the jump-off line
O1, O2, O3 = (-215, -900), mid(G("24.19"), G("26.13")), mid(G("19.25"), G("21.21"))  # and on the objective

WOODS_LL = {  # OpenStreetMap ways (ODbL), simplified to 12 m
    'st_eloi': [(49.66212, 2.48125), (49.663, 2.47978), (49.66405, 2.47855), (49.66481, 2.47598), (49.6652, 2.4732), (49.6655, 2.47258), (49.66882, 2.47093), (49.6691, 2.47107), (49.66947, 2.47248), (49.66877, 2.47342), (49.66882, 2.47366), (49.66816, 2.4739), (49.66628, 2.47762), (49.66598, 2.47744), (49.66613, 2.47381), (49.66546, 2.47301), (49.66499, 2.47774), (49.66552, 2.47813), (49.66536, 2.47861), (49.66486, 2.47835), (49.66486, 2.4778), (49.66448, 2.47763), (49.66307, 2.48164), (49.66261, 2.48139), (49.66244, 2.48176)],  # way 235282875
    'glands': [(49.6641, 2.47072), (49.66387, 2.47244), (49.6626, 2.47463), (49.66153, 2.47507), (49.66087, 2.47159), (49.66075, 2.46978), (49.66248, 2.46926), (49.66257, 2.46971), (49.66338, 2.46921), (49.66389, 2.47084)],  # way 235282691
    'cantigny_fontaine': [(49.65126, 2.48883), (49.65159, 2.49036), (49.65333, 2.49393), (49.65418, 2.49628), (49.6553, 2.49745), (49.65581, 2.49869), (49.65633, 2.50209), (49.65647, 2.50536), (49.65682, 2.50819), (49.65739, 2.51085), (49.65671, 2.51047), (49.65616, 2.5086), (49.65584, 2.50964), (49.65588, 2.50906), (49.65465, 2.50945), (49.6544, 2.5089), (49.65304, 2.50873), (49.65258, 2.50757), (49.65198, 2.50528), (49.65505, 2.50418), (49.6506, 2.49092), (49.65091, 2.49066), (49.64997, 2.48722), (49.64983, 2.48532), (49.64879, 2.48602), (49.64871, 2.4857), (49.64736, 2.48629), (49.64723, 2.48518), (49.64774, 2.48458), (49.64825, 2.48448), (49.64951, 2.4834), (49.64938, 2.48291), (49.64983, 2.48093), (49.65029, 2.48128), (49.65038, 2.48576), (49.65092, 2.48803), (49.65182, 2.48779), (49.65206, 2.48851), (49.65163, 2.48888), (49.65216, 2.49021), (49.65237, 2.49049), (49.65243, 2.49012), (49.65266, 2.49013), (49.65254, 2.49081), (49.65322, 2.49038), (49.6545, 2.49446), (49.65593, 2.4961), (49.65641, 2.49725), (49.65618, 2.49778), (49.65636, 2.49847), (49.65678, 2.49847), (49.65696, 2.49899), (49.6566, 2.49982), (49.65588, 2.49754), (49.6544, 2.49536), (49.65148, 2.48885), (49.65138, 2.48865)],  # way 42071277
    'framicourt': [(49.66986, 2.51049), (49.66934, 2.51363), (49.66933, 2.51623), (49.66987, 2.51707), (49.67099, 2.52037), (49.67052, 2.52079), (49.66997, 2.51956), (49.67016, 2.51937), (49.66962, 2.51811), (49.66706, 2.51597), (49.66645, 2.51467), (49.66603, 2.51503), (49.6657, 2.51346), (49.66621, 2.51293), (49.66643, 2.51164), (49.66695, 2.5115), (49.66691, 2.51063), (49.66628, 2.50909), (49.66674, 2.50772), (49.6666, 2.50669), (49.66669, 2.50553), (49.66781, 2.50322), (49.67028, 2.506)],  # way 67559963
    'lalval': [(49.67809, 2.50329), (49.67801, 2.50426), (49.67842, 2.50429), (49.67847, 2.50525), (49.6797, 2.50542), (49.68131, 2.50752), (49.68132, 2.50847), (49.68107, 2.50955), (49.67923, 2.51054), (49.67943, 2.51206), (49.67813, 2.51274), (49.6779, 2.5211), (49.67331, 2.5198), (49.6732, 2.51924), (49.6742, 2.51905), (49.67297, 2.51453), (49.67261, 2.51481), (49.67221, 2.51302), (49.6728, 2.5122), (49.67343, 2.50893), (49.67467, 2.5093), (49.67536, 2.50523), (49.67613, 2.50425), (49.67448, 2.50508), (49.67379, 2.50665), (49.67406, 2.50695), (49.67364, 2.50823), (49.67273, 2.50742), (49.6717, 2.50945), (49.67152, 2.50956), (49.67155, 2.50931), (49.67472, 2.50337), (49.67483, 2.50298), (49.67472, 2.5024), (49.67688, 2.50215), (49.67735, 2.50229)],  # way 42198284
    'voyeux': [(49.6571, 2.52169), (49.65803, 2.52269), (49.6588, 2.5273), (49.65909, 2.52834), (49.65985, 2.52978), (49.65948, 2.52979), (49.65881, 2.52875), (49.65825, 2.52719), (49.65805, 2.52792), (49.65794, 2.52771), (49.65809, 2.52681), (49.65801, 2.52477), (49.657, 2.5249), (49.65704, 2.52742), (49.65298, 2.52329), (49.65233, 2.52316), (49.65149, 2.52247), (49.65095, 2.52383), (49.64908, 2.52266), (49.65072, 2.52079), (49.65166, 2.51884), (49.65319, 2.51686), (49.65354, 2.51602), (49.65377, 2.51622), (49.65519, 2.51991), (49.6567, 2.52165)],  # way 42054179
    'la_folie': [(49.67791, 2.50176), (49.67736, 2.50163), (49.67646, 2.50049), (49.67687, 2.49969), (49.67763, 2.49715), (49.6784, 2.49789), (49.67914, 2.49584), (49.67875, 2.49468), (49.67926, 2.49444), (49.67969, 2.49466), (49.68024, 2.49521), (49.6796, 2.49757), (49.67937, 2.49927), (49.67954, 2.49947), (49.67853, 2.5015), (49.67843, 2.50128)],  # way 538068046
    'grivesnes_park': [(49.68018, 2.44665), (49.67862, 2.44534), (49.67706, 2.4435), (49.67595, 2.44172), (49.67398, 2.4393), (49.67374, 2.43958), (49.68013, 2.44753), (49.68041, 2.44891), (49.68163, 2.45081), (49.68061, 2.45187), (49.68126, 2.45436), (49.68353, 2.45277), (49.68844, 2.46097), (49.68846, 2.46038), (49.68679, 2.4569), (49.68626, 2.4548), (49.68482, 2.45321), (49.682, 2.44871)],  # way 235281607
}
ROADS_LL = {
    'villers_rd': [(49.65358, 2.46435), (49.65335, 2.46659), (49.65348, 2.47016), (49.65922, 2.47985), (49.661, 2.48326), (49.66132, 2.48574), (49.66299, 2.49012), (49.66284, 2.49168), (49.66191, 2.49462)],  # ways 357814718, 357814726, 166205642, 295655965
    'plessier_rd': [(49.67696, 2.46196), (49.67659, 2.46296), (49.67657, 2.46639), (49.67514, 2.46671), (49.67407, 2.46816), (49.67301, 2.4708), (49.67152, 2.47302), (49.66866, 2.4785), (49.66652, 2.48325), (49.66565, 2.48658), (49.66421, 2.48941), (49.66395, 2.49082)],  # ways 60370413, 1303506054
    'grivesnes_rd': [(49.6856, 2.47072), (49.68195, 2.47568), (49.68147, 2.47753), (49.68127, 2.48157), (49.68097, 2.4826), (49.68043, 2.48346), (49.6767, 2.48595), (49.67411, 2.48695), (49.671, 2.48889), (49.66961, 2.49008), (49.66691, 2.49161), (49.66625, 2.49173), (49.66541, 2.49105)],  # ways 296430428, 1303506748
    'fontaine_rd': [(49.66541, 2.49105), (49.66395, 2.49082), (49.66339, 2.49139), (49.66235, 2.49406), (49.66168, 2.49508), (49.66122, 2.49883), (49.66018, 2.49999), (49.65727, 2.50472), (49.65638, 2.50561), (49.65591, 2.50952), (49.65507, 2.51142), (49.65474, 2.51308)],  # ways 349889975, 349889976
    'framicourt_rd': [(49.6616, 2.49546), (49.66209, 2.49809), (49.6629, 2.50004), (49.66763, 2.52287), (49.66906, 2.52601)],  # ways 349909082, 166205639
    'cemetery': [(49.6672, 2.49241), (49.66703, 2.49165), (49.66674, 2.4918), (49.66691, 2.49256)],  # ways 295655939
}
def fix(name, poly):  # the Bois St Eloi stood 300 m west of today's wood
    return [(x - 300, y) for x, y in poly] if name == 'st_eloi' else poly
WOODS = {k: fix(k, [M(*p) for p in v]) for k, v in WOODS_LL.items()}
ROADS = {k: [M(*p) for p in v] for k, v in ROADS_LL.items()}
def inside(x, y, poly):
    c = False
    for i in range(len(poly)):
        (xa, ya), (xb, yb) = poly[i], poly[i - 1]
        if (ya > y) != (yb > y) and x < xa + (xb - xa) * (y - ya) / (yb - ya): c = not c
    return c
def centre(poly): return (round(sum(p[0] for p in poly) / len(poly)), round(sum(p[1] for p in poly) / len(poly)))

# ---- fields: all the open ground, in farm-sized parcels that each take their own furrows (after First Manassas) ----
def hashf(i, j, s=0): return ((i * 73856093 ^ j * 19349663 ^ s * 83492791) & 0xffff) / 0xffff
CELL, PARCEL, NP = 50, 800, 4
SEEDS = {(i, j): (i * PARCEL + (hashf(i, j, 1) - 0.5) * PARCEL * 0.8, j * PARCEL + (hashf(i, j, 2) - 0.5) * PARCEL * 0.8) for i in range(-NP, NP + 1) for j in range(-NP, NP + 1)}
def parcel(x, y): return min(SEEDS, key=lambda k: math.hypot(SEEDS[k][0] - x, SEEDS[k][1] - y))
N = 2 * HALF_EXTENT // CELL
cells = {}
for j in range(N):
    for i in range(N):
        x, y = -HALF_EXTENT + (i + 0.5) * CELL, -HALF_EXTENT + (j + 0.5) * CELL
        if not any(inside(x, y, w) for w in WOODS.values()): cells.setdefault(parcel(x, y), set()).add((i, j))
def area(r): return sum(r[i][0] * r[(i + 1) % len(r)][1] - r[(i + 1) % len(r)][0] * r[i][1] for i in range(len(r))) / 2
def dp(pts, tol):
    if len(pts) < 3: return pts
    (x0, y0), (x1, y1) = pts[0], pts[-1]; Ln = math.hypot(x1 - x0, y1 - y0) or 1
    dist = [abs((x1 - x0) * (y0 - y) - (x0 - x) * (y1 - y0)) / Ln for x, y in pts]
    k = max(range(len(pts)), key=dist.__getitem__)
    return [pts[0], pts[-1]] if dist[k] <= tol else dp(pts[:k + 1], tol)[:-1] + dp(pts[k:], tol)
def rings(S):  # boundary edges with the open cell on the left, linked into loops: outer rings run anticlockwise, holes clockwise
    E = {}
    for i, j in S:
        for (di, dj), e0, e1 in (((0, -1), (i, j), (i + 1, j)), ((1, 0), (i + 1, j), (i + 1, j + 1)), ((0, 1), (i + 1, j + 1), (i, j + 1)), ((-1, 0), (i, j + 1), (i, j))):
            if (i + di, j + dj) not in S: E.setdefault(e0, []).append(e1)
    out = []
    while E:
        s = next(iter(E)); ring = [s]; p = s
        while True:
            q = E[p].pop()
            if not E[p]: del E[p]
            if q == s: break
            ring.append(q); p = q
        r = [(-HALF_EXTENT + u * CELL, -HALF_EXTENT + v * CELL) for u, v in ring]
        k = max(range(len(r)), key=lambda n: math.hypot(r[n][0] - r[0][0], r[n][1] - r[0][1]))
        out.append(dp(r[:k + 1], 30)[:-1] + dp(r[k:] + [r[0]], 30)[:-1])
    return out
FIELDS = []
for key in sorted(cells):
    rs = rings(cells[key]); outer = [r for r in rs if area(r) > 20000]
    for o in outer:
        for hole in (r for r in rs if area(r) < -10000 and inside(*r[0], o)):  # bridged in, so even-odd and non-zero fills both leave it out
            k = min(range(len(o)), key=lambda n: math.hypot(o[n][0] - hole[0][0], o[n][1] - hole[0][1]))
            o[:] = o[:k + 1] + hole + [hole[0]] + o[k:]
        FIELDS.append([(round(x), round(y)) for x, y in o])

# ---- the clock: 28 to 31 May 1918, French summer time ----
UTC = dt.timezone.utc
T0 = dt.datetime(1918, 5, 28, tzinfo=UTC)
def D(day, hm): return f"1918-05-{day:02d} {hm}"
def sec(t): return (dt.datetime.strptime(t, "%Y-%m-%d %H:%M:%S" if t.count(":") == 2 else "%Y-%m-%d %H:%M").replace(tzinfo=UTC) - T0).total_seconds()
def fmt(s): s = round(s); return (T0 + dt.timedelta(seconds=s)).strftime("%Y-%m-%d %H:%M" + (":%S" if s % 60 else ""))
def plus(t, mins): return fmt(sec(t) + mins * 60)
START, END = D(28, "04:30"), D(31, "01:00")
OBJ_DUG = D(28, "08:00")  # the second wave consolidated the objective with trenches and wire

# ---- ground ----
def label(name, p, dy=0, dx=0, **kw): return dict(name=name, at=[p[0] + dx, p[1] + dy], **kw)
NAMES = {'st_eloi': ("Bois St Eloi", 0, 250), 'glands': ("Bois des Glands de Villers", -60, -150), 'framicourt': ("Bois de Framicourt", 0, 260),
         'lalval': ("Bois de Lalval", 150, 330), 'voyeux': ("Bois de Voyeux", 0, -250)}
features = [
    dict(type="road", name="road to Villers-Tournelle", pts=ROADS['villers_rd'], at=[-1600, -1000], rot=-37),
    dict(type="road", name="road to Le Plessier", pts=ROADS['plessier_rd'], at=[-1900, 720], rot=-36),
    dict(type="road", name="road to Grivesnes", pts=ROADS['grivesnes_rd'], at=[-1250, 1250], rot=-53),
    dict(type="road", name="road to Fontaine", pts=ROADS['fontaine_rd'], at=[480, -820], rot=-34),
    dict(type="road", name="road to Framicourt", pts=ROADS['framicourt_rd'], at=[1050, 80], rot=21),
    dict(type="trench", name="the jump-off line, dug by the 18th Infantry and the engineers", pts=JUMP_OFF),
    dict(type="trench", name="German front line (about here)", pts=GERMAN_LINE),
    dict(type="trench", name="the objective, dug in after the attack", pts=OBJECTIVE, **{"from": OBJ_DUG}),
    label("Cantigny", CHURCH, dx=-230, dy=160), label("cemetery", P['cemetery'], dx=150), label("the château (about here)", CHATEAU, dy=-90),
    label("Villers-Tournelle", P['villers'], dy=-160), label("Fontaine-sous-Montdidier", P['fontaine'], dx=120, dy=150), label("Framicourt", P['framicourt'], dy=110),
    label("Courtemanche", P['courtemanche'], dx=-200, dy=-120), label("Le Plessier", P['le_plessier'], dy=110), label("St Aignan chapel", P['st_aignan'], dy=-100),
    label("La Folie farm", P['la_folie'], dy=110), label("Grivesnes", P['grivesnes'], dy=110), label("Hill 104 (about here)", HILL_104),
    label("château of Fontaine (about here)", FONTAINE_CH, dy=-130), label("Bois de Cantigny", (-850, -1650)), label("Bois de Fontaine", (300, -1500)),
    label("Bois Suisse (about here)", SUISSE, dx=-150), label("Bois Carré (about here)", CARRE, dy=-150),
    *[label(n, centre(WOODS[k]), dx=dx, dy=dy) for k, (n, dx, dy) in NAMES.items()],
]
# The barrage: the preparation on the village from 5.45, then the 75s' rolling barrage ahead of each battalion from H hour,
# 100 m every two minutes, standing 200 m beyond the objective until a quarter to eight. From noon the German guns.
H = D(28, "06:45")
features += [dict(type="smoke", at=[CHURCH[0], CHURCH[1]], rate=30, spread=700, **{"from": D(28, "05:45"), "until": H}),
             dict(type="smoke", at=[CHURCH[0], CHURCH[1] + 100], rate=3, spread=900, **{"from": D(28, "12:00"), "until": D(30, "12:00")})]
for J, O in ((J1, O1), (J2, O2), (J3, O3)):
    L = math.dist(J, O); u = ((O[0] - J[0]) / L, (O[1] - J[1]) / L); d, t = 150, H
    while d < L + 200:
        features.append(dict(type="smoke", at=[round(J[0] + d * u[0]), round(J[1] + d * u[1])], rate=14, spread=450, **{"from": t, "until": plus(t, 2)}))
        d, t = d + 100, plus(t, 2)
    features.append(dict(type="smoke", at=[round(O[0] + 200 * u[0]), round(O[1] + 200 * u[1])], rate=10, spread=450, **{"from": t, "until": D(28, "07:45")}))
for f in features:
    if "at" in f: assert on_land(f["at"]) and max(map(abs, f["at"])) < HALF_EXTENT - 100, (f.get("name"), f["at"], "a label off the map")

# ---- order of battle: (id, side, short, name, commander, type, strength, extra) ----
A1 = dict(ranks=1)  # the American battalions advanced in lines, a battalion about 600 m across
OOB = [
    ("r28_1", "american", "1/28th", "1st Battalion, 28th Infantry, the right: two companies in the front line from the Bois Suisse to the Bois Carré, one on the west edge of the Bois de Cantigny, one in reserve in the Bois des Glands", "Maj. George F. Rozelle Jr.", "infantry", 900, A1),
    ("r28_2", "american", "2/28th", "2nd Battalion, 28th Infantry, the centre, with the tanks: its right half through the village, its left straight on to the objective", "Lt. Col. Robert J. Maxey (mortally wounded), then Maj. Clarence R. Huebner", "infantry", 900, A1),
    ("r28_3", "american", "3/28th", "3rd Battalion, 28th Infantry, the left, toward St Aignan in touch with the French 152nd Division", "Lt. Col. Jesse M. Cullison (probably)", "infantry", 900, A1),
    ("r18co_a", "american", "18th Inf. coy", "A company of the 18th Infantry in reserve north of Villers-Tournelle, released only by the brigade", "", "infantry", 250, {}),
    ("r18co_b", "american", "18th Inf. coy", "A company of the 18th Infantry in reserve in the west of the Bois de Cantigny, released only by the brigade", "", "infantry", 250, {}),
    ("eng", "american", "Co. D, 1st Eng.", "Company D, 1st Engineers, which went in with the infantry", "", "infantry", 150, {}),
    ("r26_1", "american", "1/26th", "1st Battalion, 26th Infantry, holding the sector south of the 28th", "Maj. Theodore Roosevelt Jr.", "infantry", 900, A1),
    ("r18_a", "american", "18th Inf.", "A battalion of the 18th Infantry, at the south-west corner of the Bois des Glands from the night of the 28th", "", "infantry", 750, {}),
    ("r18_b", "american", "18th Inf.", "A battalion of the 18th Infantry, at Villers-Tournelle from the night of the 28th", "", "infantry", 750, {}),
    ("r16_1", "american", "16th Inf.", "A battalion of the 16th Infantry, which relieved the 28th on the night of the 30th", "", "infantry", 1000, A1),
    ("r16_2", "american", "16th Inf.", "A battalion of the 16th Infantry, which relieved the 28th on the night of the 30th", "", "infantry", 1000, A1),
    ("r16_3", "american", "16th Inf.", "A battalion of the 16th Infantry, which relieved the 28th on the night of the 30th", "", "infantry", 1000, A1),
    ("tank1", "french", "1st battery", "1st battery, French 5th Tank Battalion: four Schneider tanks", "Capt. Noscereau", "armor", 4, {}),
    ("tank2", "french", "2nd battery", "2nd battery, French 5th Tank Battalion: four Schneider tanks, which crossed the gardens north-east of the village", "Capt. Noscereau", "armor", 4, {}),
    ("tank3", "french", "3rd battery", "3rd battery, French 5th Tank Battalion: four Schneider tanks, at their objective north of Cantigny about seven", "Capt. Noscereau", "armor", 4, {}),
    ("g271_1", "german", "I/271 R.I.R.", "1st Battalion, 271st Reserve Infantry (1st to 3rd companies), the garrison of Cantigny", "", "infantry", 375, dict(loose=True)),
    ("g271_4", "german", "4th Coy, 271", "4th Company, 271st Reserve Infantry, in the Bois de Framicourt", "", "infantry", 125, {}),
    ("g271_3", "german", "III/271 R.I.R.", "3rd Battalion, 271st Reserve Infantry (9th, 11th and 12th companies), north-west of the village on the road to St Aignan", "", "infantry", 400, dict(loose=True)),
    ("g272_1", "german", "272 R.I.R.", "A battalion of the 272nd Reserve Infantry, holding the northern outskirts and the ground north of the village", "", "infantry", 500, dict(loose=True)),
    ("g272_2", "german", "II/272 R.I.R.", "2nd Battalion, 272nd Reserve Infantry, in support in the Bois de Lalval", "", "infantry", 500, {}),
    ("g271_r", "german", "271 R.I.R.", "A battalion of the 271st Reserve Infantry at rest in the ravine south of Framicourt, with its rolling kitchen", "", "infantry", 500, {}),
    ("g83", "german", "83 R.I.R.", "A company of the 83rd Reserve Infantry, 25th Reserve Division, at Fontaine", "", "infantry", 125, {}),
    ("g118", "german", "118 R.I.R.", "Part of a battalion of the 118th Reserve Infantry, 25th Reserve Division, in support in the Bois de Voyeux", "", "infantry", 250, {}),
    ("g25r", "german", "three companies", "Three companies seen going into the Bois de Voyeux at 2.57 p.m. on the 28th", "", "infantry", 375, {}),
]
BASE = {row[0]: row for row in OOB}

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
def heading(a, b): return round(math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) % 360)
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
    ks[-1]["state"] = state
    if h is not None: ks[-1]["h"] = h
    keys(id, ks); return ks[-1]["t"]
def lose(id, t0, t1, n): at(id, t0); at(id, t1, strength=carried(id, "strength") - n)

# 04:30 on 28 May: the 28th on the jump-off line, the Germans in and about the village; the rest come up later
for id, p, h, kw in [("r28_1", J1, 63, {}), ("r28_2", J2, 90, {}), ("r28_3", J3, 70, {}), ("r18co_a", (-2500, -900), 90, {}), ("r18co_b", (-1150, -1450), 60, {}),
                     ("eng", (-1480, -300), 90, {}), ("r26_1", (150, -1300), 20, {}),
                     ("g271_1", (-430, -300), 270, {}), ("g271_4", (650, 250), 250, {}), ("g271_3", (-720, 520), 265, {}), ("g272_1", (-350, 780), 250, {}),
                     ("g272_2", (700, 1050), 230, {}), ("g271_r", (1750, 180), 250, {}), ("g83", (1285, -1060), 270, {}), ("g118", (1850, -1000), 280, {})]:
    appear(id, START, p, h=h, **kw)
for id, p in [("r18_a", (-2990, -650)), ("r18_b", (-2990, -1350)), ("r16_1", (-2990, -1330)), ("r16_2", (-2990, -1330)), ("r16_3", (-2990, -1330)),
              ("tank1", (-2300, -1100)), ("tank2", (-2300, -1150)), ("tank3", (-2300, -1200)), ("g25r", (2850, -600))]:
    appear(id, START, p, state="hidden", h=90)

def run(id, t0, legs, **kw0):  # from where it stands at t0 through timed legs: (time, place, fields)
    if sec(t0) - sec(KEYS[id][-1]["t"]) > 120: at(id, plus(t0, -1))
    keys(id, [K(t0, last(id), **kw0)] + [K(t, p, **kw) for t, p, kw in legs])
def timed(id, t0, t1, pts, h, **kw0):  # from where it stands at t0 along pts, arriving at t1, times spread by distance
    pts = [last(id)] + pts; d = [0]
    for a, b in zip(pts, pts[1:]): d.append(d[-1] + math.dist(a, b))
    run(id, t0, [(fmt(sec(t0) + (sec(t1) - sec(t0)) * d[i] / d[-1]), p, dict(h=heading(pts[i - 1], p))) for i, p in enumerate(pts) if i][:-1] + [(t1, pts[-1], dict(h=h))], h=heading(pts[0], pts[1]), **kw0)
def hide(id, t): at(id, t, state="hidden")
def fire(id, t0, t1, state="line"): at(id, t0, state="firing"); at(id, t1, state=state)
VILLERS_RD = ROADS['villers_rd']
def by_road(a, b):  # along the Villers-Tournelle road from the vertex nearest a to the one nearest b
    i, j = (min(range(len(VILLERS_RD)), key=lambda n: math.dist(VILLERS_RD[n], p)) for p in (a, b))
    return VILLERS_RD[i:j + 1] if i <= j else VILLERS_RD[j:i + 1][::-1]
WEST = (-2990, -1330)  # where the road to Coullemelle and the rear leaves the map

# ---- 28 May: the attack ----
# The engineers lose two officers and 30 men before H hour; they follow the centre battalion into the village.
move("eng", D(28, "06:55"), [(-1330, -260), (-870, -250), (-520, -260)], h=90)
# The three battalions go over at H hour behind the barrage; the centre is in the village at 6.56, all on the objective at 7.20.
run("r28_3", H, [(D(28, "06:58"), (-790, 470), dict(state="firing")), (D(28, "07:10"), O3, {}), (D(28, "07:20"), O3, dict(state="line", h=63))], state="charge", h=70)
run("r28_2", H, [(D(28, "06:56"), (-870, -240), dict(state="firing")), (D(28, "07:15"), (-420, -225), {}), (D(28, "07:20"), O2, dict(state="line", h=72))], state="charge", h=90)
run("r28_1", H, [(D(28, "07:05"), (-520, -920), dict(state="firing", h=90)), (D(28, "07:20"), O1, dict(state="line", h=100))], state="charge", h=75)
# The tanks: out of their waiting positions at 5.50, at their point of departure behind the Bois Suisse at 6.30, moving
# east at 6.42 with the centre battalion and round north of the village, their third battery at its objective about seven.
DEP = {"tank1": (-1250, -1000), "tank2": (-1200, -1080), "tank3": (-1150, -1160)}
GOAL = {"tank1": (-560, 330), "tank2": (-330, 150), "tank3": (-650, 480)}
for id in DEP:
    appear(id, D(28, "05:50"), last(id), state="column", h=100)
    run(id, D(28, "05:50"), [(D(28, "06:30"), DEP[id], dict(state="line", h=70))], state="column")
    timed(id, D(28, "06:42"), D(28, "07:00"), [(-850, 100), GOAL[id]], h=60, state="line")
for id, back in (("tank3", (-2350, -1150)), ("tank1", (-2350, -1200)), ("tank2", (-2350, -1250))):
    move(id, D(28, "07:40"), [(-850, 100), (-1300, -500), back], h=270, state="column", moving="column", kmh=6)
    hide(id, D(28, "08:30"))
# The garrison is killed or captured, 275 dead counted in the village; the troops north of it fall back on the woods.
fire("g271_1", D(28, "06:50"), D(28, "07:15"), state="firing")
at("g271_1", D(28, "07:15"), strength=100, state="surrender"); hide("g271_1", D(28, "07:55"))
at("g271_3", D(28, "06:50"), state="firing"); at("g271_3", D(28, "07:00"), strength=300, state="retreat")
move("g271_3", D(28, "07:01"), [(-200, 700), (350, 880)], h=240, moving="retreat", kmh=3)
at("g272_1", D(28, "06:55"), state="firing"); at("g272_1", D(28, "07:05"), strength=380, state="retreat")
move("g272_1", D(28, "07:06"), [(0, 1350)], h=220, moving="retreat", kmh=3)
# A feeble counter-attack by a small force out of the Bois de Fontaine at 7.30; then the company holds the château.
run("g83", D(28, "07:20"), [(D(28, "07:30"), (500, -1080), dict(state="firing", h=250)), (D(28, "07:40"), (500, -1080), dict(state="retreat", strength=100))], state="charge", h=260)
move("g83", D(28, "07:41"), [FONTAINE_CH], h=260, moving="retreat", kmh=3)
fire("r26_1", D(28, "07:28"), D(28, "07:40"))
# 11.34: a counter-attack forming in the valley between the Framicourt and Lalval woods is shelled and goes back.
move("g271_r", D(28, "11:10"), [(1300, 450), (850, 560)], h=230)
lose("g271_r", D(28, "11:34"), D(28, "11:50"), 40)
move("g271_r", D(28, "11:55"), [(1000, 250)], h=240)
# Courtemanche: Germans massing in the open fields in the early afternoon; three companies into the Bois de Voyeux at 2.57.
appear("g25r", D(28, "13:30"), last("g25r"), h=250)
run("g25r", D(28, "14:30"), [(D(28, "14:57"), (1800, -1250), dict(state="line", h=270))], state="column", h=250)
# 5 p.m.: from the western tip of the Bois de Framicourt, caught by the barrage at 5.10; repulsed by 5.50.
move("g271_r", D(28, "16:40"), [(380, 250)], h=240)
run("g271_r", D(28, "17:00"), [(D(28, "17:10"), (50, 80), dict(state="rout", strength=410))], state="charge", h=245)
move("g271_r", D(28, "17:11"), [(450, 250)], h=245, moving="rout", kmh=3)
move("g271_r", D(28, "17:50"), [(900, 200)], h=245)
fire("r28_2", D(28, "17:00"), D(28, "17:15")); fire("r28_3", D(28, "17:02"), D(28, "17:15"))
# 6.40 p.m.: a rolling barrage, then waves from the southern and western edges of the wood. The first is killed to a man
# by rifle and machine-gun fire, the second crushed by the guns; much of it falls on the 26th's battalion.
move("g271_4", D(28, "18:25"), [(700, -20)], h=220)
run("g271_4", D(28, "18:40"), [(D(28, "18:55"), (100, -550), dict(state="firing", h=225)), (D(28, "19:00"), (100, -550), dict(strength=0))], state="charge", h=225)
hide("g271_4", D(28, "19:01"))
move("g271_r", D(28, "18:30"), [(900, -30)], h=225)
run("g271_r", D(28, "18:45"), [(D(28, "19:00"), (400, -500), dict(state="rout", h=225)), (D(28, "19:07"), (450, -440), dict(strength=280))], state="charge", h=225)
move("g271_r", D(28, "19:08"), [(900, 150)], h=225, moving="rout", kmh=3)
fire("r28_1", D(28, "18:40"), D(28, "19:10")); fire("r26_1", D(28, "18:40"), D(28, "19:10")); fire("r28_2", D(28, "18:45"), D(28, "19:05"))
# 7.36: about 200 lying down in front of the Bois de Voyeux.
move("g25r", D(28, "19:20"), [(1150, -1050)], h=270)
move("g25r", D(28, "20:45"), [(1800, -1250)], h=270)
# 8.30 p.m.: advancing from Framicourt in great numbers; barrage; by 9.10 Framicourt and the ravine south of it are full of Germans.
move("g271_r", D(28, "20:20"), [(400, 200)], h=240)
run("g271_r", D(28, "20:32"), [(D(28, "20:40"), (150, 70), dict(state="rout", strength=250))], state="charge", h=245)
move("g271_r", D(28, "20:41"), [(900, 150), (1700, 150)], h=245, moving="rout", kmh=3)
fire("r28_2", D(28, "20:32"), D(28, "20:45"))
# The night of the 28th: two companies of the 18th and the engineers into the line, two battalions of the 18th behind it.
move("r18co_a", D(28, "22:30"), [(-1600, -600), (-900, -300), (-420, 0)], h=72, state="line")
move("r18co_b", D(28, "22:30"), [(-350, -1050)], h=95, state="line")
move("eng", D(28, "22:30"), [(-400, -650)], h=90, state="line")
appear("r18_a", D(28, "22:00"), last("r18_a"), state="column", h=90); move("r18_a", D(28, "22:01"), [(-2140, -580)], h=80)
appear("r18_b", D(28, "22:00"), last("r18_b"), state="column", h=90); move("r18_b", D(28, "22:01"), [(-2450, -1300)], h=80)

# ---- 29 May: holding ----
# Two small counter-attacks at six and seven, broken up by artillery and rifle fire.
for t0, t1, n in (("05:45", "06:00", 330), ("06:45", "06:55", 290)):
    move("g272_1", D(29, t0), [(-100, 1050)], h=225)
    run("g272_1", D(29, t1), [(plus(D(29, t1), 8), (-500, 700), dict(state="firing")), (plus(D(29, t1), 12), (-500, 700), dict(state="retreat", strength=n))], state="charge", h=225)
    move("g272_1", plus(D(29, t1), 13), [(-100, 1050)], h=225, moving="retreat", kmh=3)
    fire("r28_3", plus(D(29, t1), 2), plus(D(29, t1), 14))
move("g272_1", D(29, "07:30"), [(0, 1350)], h=225)
# 5.45 p.m.: a strong and determined assault against the left. The advanced elements on the extreme left draw back to the
# old line; hand-to-hand fighting at 7.43; the 2nd Battalion falls back under the shells at 8.11 and is sent back in.
move("g272_2", D(29, "17:20"), [(250, 720)], h=250)
move("g271_3", D(29, "17:25"), [(150, 800)], h=255)
run("g272_2", D(29, "17:45"), [(D(29, "18:00"), (-560, 600), dict(state="firing", h=255))], state="charge", h=255)
run("g271_3", D(29, "17:50"), [(D(29, "18:05"), (-600, 780), dict(state="firing", h=250))], state="charge", h=250)
run("r28_3", D(29, "17:45"), [(D(29, "18:05"), (-1000, 520), dict(state="firing", h=70))], state="retreat", h=250)
run("g272_2", D(29, "19:38"), [(D(29, "19:45"), (-800, 560), dict(state="firing")), (D(29, "19:55"), (-800, 560), {}), (D(29, "20:05"), (-560, 600), {})], state="charge")
at("g272_2", D(29, "20:50"), strength=340, state="retreat"); at("g271_3", D(29, "20:50"), strength=220, state="retreat")
move("g272_2", D(29, "20:51"), [(650, 1000)], h=60, moving="retreat", kmh=3)
move("g271_3", D(29, "20:51"), [(350, 880)], h=60, moving="retreat", kmh=3)
move("r28_3", D(29, "21:00"), [O3], h=63, moving="line")
run("r28_2", D(29, "20:11"), [(D(29, "20:25"), (-560, -250), dict(state="line", h=72))], state="retreat", h=270)
move("r28_2", D(29, "20:55"), [O2], h=72, moving="line")
# 8.21 p.m.: a large body of Germans near the château in the Bois de Fontaine, Roosevelt reports.
move("g118", D(29, "19:50"), [(950, -1000)], h=260)
fire("r26_1", D(29, "20:20"), D(29, "20:40"))
move("g118", D(29, "21:10"), [(1850, -1000)], h=80)

# ---- 30 May: the last attack, two waves out of the Bois de Lalval, swept back before they reach the line ----
move("g272_2", D(30, "05:10"), [(300, 750)], h=240)
move("g271_3", D(30, "05:15"), [(400, 900)], h=240)
run("g272_2", D(30, "05:30"), [(D(30, "05:43"), (-350, 620), dict(state="rout", strength=230))], state="charge", h=250)
run("g271_3", D(30, "05:35"), [(D(30, "05:47"), (-200, 780), dict(state="rout", strength=150))], state="charge", h=250)
move("g272_2", D(30, "05:44"), [(650, 1000)], h=60, moving="rout", kmh=3)
move("g271_3", D(30, "05:48"), [(350, 880)], h=60, moving="rout", kmh=3)
fire("r28_3", D(30, "05:32"), D(30, "05:50")); fire("r28_2", D(30, "05:34"), D(30, "05:48"))

# ---- the night of the 30th: the 16th Infantry relieves the 28th ----
for new, old, t0, via in (("r16_3", "r28_3", "21:45", [(-1300, -500), (-1150, 100)]), ("r16_2", "r28_2", "21:55", []), ("r16_1", "r28_1", "22:05", [(-900, -1000)])):
    post, h = last(old), next(k["h"] for k in reversed(KEYS[old]) if "h" in k)
    road = by_road(WEST, via[0] if via else post)
    appear(new, D(30, t0), WEST, state="column", h=90)
    arrive = move(new, plus(D(30, t0), 1), road + via + [post], h=h)
    back = move(old, plus(arrive, 10), [*reversed(via), *by_road(via[0] if via else post, WEST), WEST], h=270)
    hide(old, plus(back, 1))

# ---- American losses: the First Division's 1,067 for 28 to 30 May, shared among the units engaged by inference: a few in
# the assault, the engineers' 32 before it, the rest under the shelling from noon on the 28th and in the counter-attacks ----
LOSS = {
    "r28_1": [(H, D(28, "07:20"), 10), (D(28, "12:00"), D(28, "21:30"), 120), (D(28, "21:30"), D(29, "05:00"), 30), (D(29, "12:00"), D(29, "21:30"), 100), (D(30, "05:30"), D(30, "06:00"), 10)],
    "r28_2": [(H, D(28, "07:20"), 10), (D(28, "12:00"), D(28, "21:30"), 110), (D(28, "21:30"), D(29, "05:00"), 30), (D(29, "12:00"), D(29, "21:30"), 70)],
    "r28_3": [(H, D(28, "07:20"), 5), (D(28, "12:00"), D(28, "21:30"), 90), (D(28, "21:30"), D(29, "05:00"), 30), (D(29, "12:00"), D(29, "21:30"), 75), (D(30, "05:30"), D(30, "06:00"), 10)],
    "r26_1": [(D(28, "18:40"), D(28, "19:10"), 70), (D(28, "19:10"), D(28, "21:30"), 20), (D(28, "21:30"), D(29, "05:00"), 20), (D(29, "12:00"), D(29, "21:30"), 50)],
    "eng": [(D(28, "05:45"), D(28, "06:40"), 32), (D(28, "23:00"), D(29, "05:00"), 10)],
    "r18co_a": [(D(29, "00:00"), D(29, "05:00"), 15), (D(29, "12:00"), D(29, "21:30"), 25)],
    "r18co_b": [(D(29, "00:00"), D(29, "05:00"), 20), (D(29, "12:00"), D(29, "21:30"), 25)],
    "r18_a": [(D(29, "12:00"), D(29, "21:30"), 40)], "r18_b": [(D(29, "12:00"), D(29, "21:30"), 40)],
}
assert sum(n for v in LOSS.values() for *_, n in v) == 1067, "the division's 1,067"
def pose(id, t):  # where a unit is at time t between its keys
    ks = KEYS[id]; a = max((k for k in ks if sec(k["t"]) <= sec(t)), key=lambda k: sec(k["t"])); b = next((k for k in ks if sec(k["t"]) > sec(t)), None)
    if b is None: return (a["x"], a["y"])
    f = (sec(t) - sec(a["t"])) / (sec(b["t"]) - sec(a["t"])); return (a["x"] + f * (b["x"] - a["x"]), a["y"] + f * (b["y"] - a["y"]))
def curve(pts, base):  # strength at a time, falling linearly through each span of losses
    def f(s):
        if s <= pts[0][0]: return base
        for (s0, v0), (s1, v1) in zip(pts, pts[1:]):
            if s0 <= s <= s1: return v1 if s1 == s0 else round(v0 + (s - s0) / (s1 - s0) * (v1 - v0))
        return pts[-1][1]
    return f
for id, spans in LOSS.items():
    cur, pts = BASE[id][6], []
    for t0, t1, n in spans: pts += [(sec(t0), cur), (sec(t1), cur - n)]; cur -= n
    s_at = curve(pts, BASE[id][6])
    have = {k["t"] for k in KEYS[id]}
    for s, _ in pts:
        t = fmt(s)
        if t not in have: KEYS[id].append(K(t, pose(id, t))); have.add(t)
    KEYS[id].sort(key=lambda k: sec(k["t"]))
    for k in KEYS[id]: k["strength"] = s_at(sec(k["t"]))

assert set(KEYS) == set(BASE), set(KEYS) ^ set(BASE)
for id in KEYS:
    if carried(id, "state") != "hidden" and sec(KEYS[id][-1]["t"]) < sec(END): at(id, END)

# ---- assemble and check ----
units = []
TOP = {"infantry": 6, "armor": 8}  # km/h, the fastest any leg may go; a Schneider made about 8 on good going
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
    for k in ks: assert on_land((k["x"], k["y"])), (id, k["t"], "off the map")
    units.append(dict(id=id, side=side, name=name, short=short, commander=commander, type=type, strength=strength, keys=ks, **extra))

# ---- chapters: (time, title, text, camera centre, metres across, playback speed, when) ----
# Times are the artillery brigade's journal and the division history's; where they differ by two hours on the 29th and
# 30th the caption gives the history's and the fighting runs to the journal's.
CHAPTERS = [
    (D(28, "04:45"), "The guns register", "The First Division holds the line before Cantigny under the French. By half past three the 28th Infantry, Colonel Hanson Ely, is in place on a jump-off line dug 800 m west of the village, with two companies of the 18th Infantry, three machine-gun companies and a company of engineers: 3,564 men. In the village and north of it are the 271st and 272nd Reserve Infantry of the German 82nd Reserve Division. At 4.45 the batteries begin firing for adjustment, a few shots each. 'Day quite clear. More so than usual.'", [-500, 0], 4500, 60, "4.45 a.m."),
    (D(28, "05:45"), "Fire for destruction", "At 5.45 every gun turns on its target: 386 guns and trench mortars, 200,000 rounds. The 220, 240 and 280 mm howitzers and the heavy trench mortars turn Cantigny 'into a volcano', and by 5.49 the observers cannot see it for smoke. The twelve French Schneider tanks leave their waiting positions at 5.50. Five German batteries that reply between 6.13 and 6.35 are smothered.", [-800, -300], 3000, 60, "5.45 a.m."),
    (D(28, "06:45"), "H hour", "The 75s lift into a rolling barrage that moves forward 100 m every two minutes, and the infantry rise and go forward in three lines behind it. The 3rd Battalion on the left makes for the ground toward St Aignan, the 2nd goes for the village with the tanks, the 1st on the right for the ravines south of it. Lieutenant Colonel Maxey, leading the 2nd, is mortally wounded in the first wave and Major Huebner takes over. 'Very little enemy fire.'", [-850, -250], 2200, 20, "6.45 a.m."),
    (D(28, "06:56"), "Into the village", "'Our men have entered CANTIGNY,' the artillery's journal has at 6.56, and 'there is no enemy fire.' The right half of the 2nd Battalion goes through the houses. French flame-throwers, three teams split among three companies, work the cellars, which are dug in the soft stone. The garrison, a battalion of the 271st, is killed or captured; 275 German dead are counted in the village. Prisoners begin coming in at seven, and say the attack was a complete surprise.", [-600, -200], 1600, 20, "6.56 a.m."),
    (D(28, "07:20"), "On the objective", "'The entire objective was reached at 7:20 A.M. on schedule time.' The new line runs from the head of the ravine north of the village to the corner of the orchard, east of the houses, and back to the old line at the Bois de Cantigny. The tanks' third battery reached its objective about seven, so the infantry could dig in north of the village. A feeble counter-attack by a small force comes out of the Bois de Fontaine at 7.30. By 7.45 the men are digging in, and the second wave makes the line a trench with wire.", [-450, -250], 2400, 30, "7.20 a.m."),
    (D(28, "08:03"), "The tanks go home", "At 8.03 nine tanks are seen going back to Villers-Tournelle. The infantry report 'no American dead in CANTIGNY, but many dead Boche, and that the Tanks were a great help'. By 8.26 there are 140 prisoners and two officers, who say three companies are in reserve in the Bois de Framicourt; the guns turn on it. Machine guns fire on the men digging in from the direction of Fontaine.", [-1100, -350], 3200, 60, "8.03 a.m."),
    (D(28, "12:00"), "The German guns", "About noon the French begin to withdraw their counter-battery artillery for the Chemin des Dames. 'By noon, the artillery and machine gun fire upon the salient became intense and continued for forty-eight hours.' At 11.34 a counter-attack forming in the valley between the Framicourt and Lalval woods was fired on. Through the afternoon Germans are seen gathering about Courtemanche, and three companies go into the Bois de Voyeux at 2.57.", [600, -300], 4800, 300, "About noon"),
    (D(28, "17:00"), "The first counter-attack", "About five a counter-attack comes on from the north-east, out of the western tip of the Bois de Framicourt. At 5.10 it is caught by the barrage and goes to pieces. 'Counter Attack repulsed,' the artillery's journal has at 5.50.", [100, 100], 2200, 30, "5.10 p.m."),
    (D(28, "18:40"), "From the Bois de Framicourt", "A rolling barrage, then several waves of infantry from the southern and western edges of the Bois de Framicourt. 'The first wave broke under the infantry and machine gun fire and the succeeding ones were crushed by the artillery.' Much of it falls on Major Theodore Roosevelt Jr.'s battalion of the 26th Infantry, on the right, which suffers heavily. Observers report the infantry falling back; it is not. 'Several times they moved around on account of shell fire.'", [150, -550], 2400, 30, "6.40 p.m."),
    (D(28, "21:15"), "At all costs", "At 8.30 the enemy is reported advancing on Cantigny from Framicourt in great numbers, and the barrage comes down again; by 9.10 Framicourt and the ravine south of it are 'full of Boche'. Ely reports 'Our men still in position. Our losses heavy.' The air is in German hands. Bullard tells him 'this line must be held at all costs.' In the night two companies of the 18th Infantry and the engineers go into the line, and two battalions of the 18th come up behind it.", [-300, -300], 4000, 300, "9.15 p.m."),
    (D(29, "06:00"), "The morning attacks", "The infantry ran out of rockets before dawn and expected an attack. Two small counter-attacks, at six and at seven, are broken up by artillery and rifle fire. The hospitals report 600 men wounded in the whole division up to six. The German guns keep up their fire all day.", [-450, 850], 2200, 60, "6 a.m."),
    (D(29, "17:45"), "The left gives a little", "Tanks were reported coming out of the Framicourt wood in the afternoon, and the infantry claimed two hit by the heavy guns. At 5.45 'a strong and determined assault was made against the left of the line'. On the extreme left the advanced elements of the 28th draw back to the old line near St Aignan. At 7.43 the artillery's Colonel Holbrook sees hand-to-hand fighting.", [-700, 600], 2200, 120, "5.45 p.m."),
    (D(29, "20:11"), "Driven out by the shells", "At 8.11 the 2nd Battalion is reported falling back and asks the heavy guns to fire in front of it; at 8.21 Roosevelt reports a large body of Germans near the château in the Bois de Fontaine. An aeroplane sees no counter-attack and light German fire on the village, and Holbrook thinks shellfire drove the infantry out of the line. Bullard orders Ely to send the battalion back in. By ten past nine things are quieter.", [-400, -200], 2800, 60, "8.11 p.m."),
    (D(30, "05:30"), "The last attack", "Now 'the enemy made his final effort'. Behind a rolling barrage of 210, 150 and 77 mm guns, two well-formed waves, probably a battalion, come on determinedly from the Bois de Lalval and are swept back before they reach the line. Wise counts it the seventh effort. The artillery's journal puts an attack at about 3.30, its first wave through the barrage, its second destroyed by it.", [-250, 750], 2200, 30, "5.30 a.m."),
    (D(30, "22:00"), "The relief", "In the night the 16th Infantry comes up and relieves the 28th; the relief is completed the next night. The division's records count 1,067 casualties for the three days: 199 killed, 652 wounded, 16 missing and 200 gassed. Five German officers and 225 men were taken. Pershing wrote on the 28th that the attack 'marks a distinct step forward in American participation in the war'.", [-1300, -500], 4500, 300, None),
]
events = [dict(t=t, title=a, text=b, at=at_, view=v, speed=s, **({"when": w} if w else {})) for t, a, b, at_, v, s, w in CHAPTERS]
for e in events:  # without `when` the card speaks the nearest hour (app.js chapterWhen), so it must be near the frame's clock
    s = sec(e["t"]) % 86400; hh = [n % 12 or 12 for n in (int(s // 3600), int(s // 3600) + 1)]; num = re.search(r"\d+", e.get("when", ""))
    assert not num or int(num[0]) in hh, (e["t"], e["when"], "the card's hour is not the frame's")
    assert "when" in e or abs(s - math.floor(s / 3600 + 0.5) * 3600) <= 15 * 60, (e["t"], e["title"], "give it a when")

battle = dict(
    id="cantigny", name="Battle of Cantigny", date="1918-05-28", dateText="28 to 31 May 1918", place="Cantigny, Picardy, France",
    origin=dict(lat=LAT0, lon=LON0), extent=2 * HALF_EXTENT, start=START, end=END, sunrise="04:51", sunset="20:46", speed=60, lapse=3600, menPerDot=5,
    terrainExaggeration=3, contourInterval=5, trees=dict(density=0.006), fields=FIELDS, wind=dict(x=0.6, y=0.2), view=dict(x=0, y=0, width=6000),
    sides=dict(american=dict(name="Americans (First Division, Bullard)", color="#2a55a0", light="#7090c8", dark="#15305e"),
               french=dict(name="French tanks", color="#6d8fb5", light="#a9c0dc", dark="#36506e"),
               german=dict(name="Germans (82nd Reserve Division, von Lorne de St. Ange)", color="#4a4a42", light="#8c8c80", dark="#22221e")),
    features=features, units=units, events=events,
    sources=["Terrain: " + T["source"] + ", 30 m, sampled to 15 m."],
)
json.dump(battle, open(HERE + "battle.json", "w"), indent=1)
print(len(units), "units,", len(events), "events,", len(features), "features,", len(FIELDS), "fields")
