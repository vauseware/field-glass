# Builds battles/omaha-beach/battle.json and the 1944 tidal flat in terrain.json. Run from the repo root:
# python3 battles/omaha-beach/make.py
# Local metres from 49.3680N 0.8760W (x east, y north). The 10 km square holds the whole of Omaha Beach, Charlie to Fox
# Red, its five draws and the strongpoints WN 60 to WN 74, Vierville, St-Laurent and Colleville, and Formigny to the south.
# Pointe du Hoc is 3 km beyond the west edge. Anchors are the research note's OpenStreetMap points; places it gives at
# ±200 m or worse are labelled "about here". Clock times are GMT+2, the Allies' "B" zone and German summer time alike.
import json, math, random, re
HERE = "battles/omaha-beach/"
LAT0, LON0 = 49.3680, -0.8760
KX, KY = 111320 * math.cos(math.radians(LAT0)), 111320  # tools/fetch_terrain.py's metres per degree
def M(lat, lon): return (round((lon - LON0) * KX), round((lat - LAT0) * KY))
def N(x, y): return (round(x * 111194.9 / 111320), round(y * 111194.9 / 111320))  # the note's local metres (R = 6,371,009 m) to these
HALF_EXTENT = 5000

# ---- terrain: the tidal flat the surface model does not have ----
# Copernicus GLO-30 sets the sea to 0 and drops from the upper beach to it within a cell or two, so its coast is the
# 1944 high-water line and the whole foreshore reads as sea. The note's flat: every sea cell within 274 m (300 yards)
# of the shore becomes a straight 1:50 ramp from 5.49 m at the high-water line to 0.1 m at the low-water mark, under a
# water level of 0.05. Land keeps its height. The surface model's own heights of the changed cells are kept in
# terrain.json under "dsm", so a rerun starts again from them.
FLAT = 274  # m, high-water line to low-water mark
WATER = 0.05
T = json.load(open(HERE + "terrain.json"))
COLS, SP = T["cols"], T["spacing"]; HALF = COLS * SP / 2
assert abs(HALF - HALF_EXTENT) < 1, "terrain.json is not the battle's extent"
for i, v in T.pop("dsm", []): T["z"][i] = v
DSM = list(T["z"])
LAND = [v > 0.5 for v in DSM]
def edt(src):  # metres from each cell centre to the nearest source cell's centre (Felzenszwalb and Huttenlocher)
    INF = 1e12
    def one(f):
        n = len(f); v, z, d = [0] * n, [0.0] * (n + 1), [0.0] * n; k = 0; z[0], z[1] = -INF, INF
        for q in range(1, n):
            while True:
                s = ((f[q] + q * q) - (f[v[k]] + v[k] * v[k])) / (2 * q - 2 * v[k])
                if s <= z[k]: k -= 1
                else: break
            k += 1; v[k] = q; z[k] = s; z[k + 1] = INF
        k = 0
        for q in range(n):
            while z[k + 1] < q: k += 1
            d[q] = (q - v[k]) ** 2 + f[v[k]]
        return d
    g = [0.0 if s else INF for s in src]
    for r in range(COLS): g[r * COLS:(r + 1) * COLS] = one(g[r * COLS:(r + 1) * COLS])
    for c in range(COLS):
        col = one(g[c::COLS])
        for r in range(COLS): g[r * COLS + c] = col[r]
    return [math.sqrt(v) * SP for v in g]
# S: metres seaward of the high-water line, which runs midway between the last land cell and the first sea cell;
# negative inland
S = [-(b - SP / 2) if LAND[i] else a - SP / 2 for i, (a, b) in enumerate(zip(edt(LAND), edt([not v for v in LAND])))]
changed = []
for i, s in enumerate(S):
    if not LAND[i] and s <= FLAT:
        changed.append([i, DSM[i]]); T["z"][i] = round(0.1 + 5.39 * (1 - s / FLAT), 2)
T["dsm"] = changed
json.dump(T, open(HERE + "terrain.json", "w"), separators=(",", ":"))
def z(x, y):
    c, r = int((x + HALF) / SP), int((HALF - y) / SP)
    return T["z"][r * COLS + c] if 0 <= c < COLS and 0 <= r < COLS else None
def seaward(p):  # metres from p out past the high-water line, read bilinearly; negative inland
    fc, fr = (p[0] + HALF) / SP - 0.5, (HALF - p[1]) / SP - 0.5
    c, r = max(0, min(COLS - 2, int(fc))), max(0, min(COLS - 2, int(fr))); u, v = fc - c, fr - r
    a = lambda rr, cc: S[rr * COLS + cc]
    return (a(r, c) * (1 - u) + a(r, c + 1) * u) * (1 - v) + (a(r + 1, c) * (1 - u) + a(r + 1, c + 1) * u) * v
def contour(w, x0=-HALF, x1=HALF):  # the line `w` metres seaward of the high-water line, west to east, a point a column, smoothed
    out = []
    for c in range(COLS):
        r = next(r for r in range(COLS) if S[r * COLS + c] <= w)
        a, b = S[(r - 1) * COLS + c], S[r * COLS + c]; f = (a - w) / (a - b)
        out.append((c * SP - HALF + SP / 2, HALF - (r - 1 + f) * SP - SP / 2))
    sm = [out[0]] + [(p[0], (q[1] + 2 * p[1] + s[1]) / 4) for q, p, s in zip(out, out[1:], out[2:])] + [out[-1]]
    return [(round(x), round(y)) for x, y in sm if x0 <= x <= x1]
def normal(p):  # the unit vector from p out to sea
    gx, gy = seaward((p[0] + 30, p[1])) - seaward((p[0] - 30, p[1])), seaward((p[0], p[1] + 30)) - seaward((p[0], p[1] - 30))
    n = math.hypot(gx, gy) or 1; return (gx / n, gy / n)
def to_line(p, w):  # from p straight in or out across the beach to where it is w metres seaward of the high-water line
    q = p
    for _ in range(200):
        d = seaward(q) - w
        if abs(d) < 2: break
        nx, ny = normal(q); step = max(-25, min(25, d)); q = (q[0] - nx * step, q[1] - ny * step)
    return (round(q[0]), round(q[1]))

# ---- the clock and the tide, 6 June 1944 ----
START, END = "05:30", "23:59"
def sec(t): h, m, *s = map(int, t.split(':')); return h * 3600 + m * 60 + (s[0] if s else 0)
def fmt(s): s = int(round(s)); return f"{s // 3600:02d}:{s % 3600 // 60:02d}" + (f":{s % 60:02d}" if s % 60 else "")
def plus(t, mins): return fmt(sec(t) + mins * 60)
# The note's reconstruction (§5.2), feet above the morning low water. Low water 05:25 and high water 11:00 [OBH];
# 2.4 ft from 06:30 to 07:00 [S&T]; 8 ft from 07:00 to 08:00 [OBH]; an 18 ft range; the afternoon low at 17:50 and the
# evening flood repeat the morning's shape [INF].
TIDE = [("05:30", 0.0), ("06:00", 0.5), ("06:20", 1.1), ("06:30", 1.5), ("06:40", 2.1), ("06:50", 2.9), ("07:00", 3.9),
        ("07:10", 5.1), ("07:20", 6.5), ("07:30", 8.0), ("07:40", 9.5), ("07:50", 10.9), ("08:00", 11.9), ("08:20", 13.4),
        ("08:40", 14.6), ("09:00", 15.6), ("09:30", 16.7), ("10:00", 17.5), ("10:30", 18.0), ("11:00", 18.0), ("12:20", 16.9),
        ("13:20", 14.8), ("14:20", 11.6), ("15:20", 7.7), ("16:20", 3.8), ("17:20", 0.7), ("17:50", 0.0), ("18:50", 1.3),
        ("19:50", 7.2), ("20:50", 13.8), ("21:50", 16.6), ("22:50", 17.9), ("23:20", 18.0)]
RANGE = 18.0
def pchip(pts):  # a monotone cubic through (x, y) points (Fritsch and Carlson)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]; n = len(xs)
    d = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) for i in range(n - 1)]
    m = [0.0] * n
    for i in range(1, n - 1):
        if d[i - 1] * d[i] > 0:
            w1, w2 = 2 * (xs[i + 1] - xs[i]) + (xs[i] - xs[i - 1]), (xs[i + 1] - xs[i]) + 2 * (xs[i] - xs[i - 1])
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    def f(x):
        if x <= xs[0]: return ys[0]
        if x >= xs[-1]: return ys[-1]
        i = next(k for k in range(n - 1) if x < xs[k + 1]); h = xs[i + 1] - xs[i]; s = (x - xs[i]) / h
        return (2 * s ** 3 - 3 * s ** 2 + 1) * ys[i] + (s ** 3 - 2 * s ** 2 + s) * h * m[i] + (-2 * s ** 3 + 3 * s ** 2) * ys[i + 1] + (s ** 3 - s ** 2) * h * m[i + 1]
    return f
tide_ft = pchip([(sec(t), v) for t, v in TIDE])
def waterline(t): return FLAT * (1 - tide_ft(sec(t) if isinstance(t, str) else t) / RANGE)  # metres seaward of the HW line
assert abs(waterline("07:00") - 215) < 3 and abs(waterline("08:00") - 93) < 3 and waterline("10:45") < 1, "the tide is not the note's"
# One water polygon a step, from the waterline out to the map's north edge. A step ends once the waterline has moved
# 20 m, or after 30 minutes, so the flood of 06:30 to 08:00 steps every five minutes and the high stand every 30.
TIDE_STEPS, t0 = [], sec(START)
while t0 < sec(END):
    t1 = t0 + 300
    while t1 < sec(END) and t1 - t0 < 1800 and abs(waterline(t1 + 300) - waterline(t0)) < 20: t1 += 300
    t1 = min(t1, sec(END)); TIDE_STEPS.append((fmt(t0), fmt(t1), waterline((t0 + t1) / 2))); t0 = t1
def sea(w):  # the sea beyond the line w metres out, closed along the map's edges
    line = contour(w); H = HALF_EXTENT
    return [(-H, line[0][1])] + line + [(H, line[-1][1]), (H, H), (-H, H)]
WADE = 40  # m: a man may stand this far into the water, wading ashore or sheltering behind an obstacle
def dry(p, t, wade=0): return seaward(p) < waterline(t) + wade  # above the water at t, or within `wade` of its edge

# ---- places (WGS84), from the note's anchor table ----
PLACES = {
    'wn72': (49.37917, -0.90286), 'wn73': (49.38059, -0.90589), 'wn74': (49.39351, -0.93734), 'percee': (49.39373, -0.93291),
    'vierville_ch': (49.37256, -0.90483), 'vierville': (49.37455, -0.90410), 'chateau_v': (49.37409, -0.90690), 'vaumicel': (49.36837, -0.90952),
    'hamel': (49.37280, -0.89941), 'moulins': (49.36862, -0.87448), 'signal': (49.37072, -0.87970), 'stl_ch': (49.35961, -0.87764),
    'stlaurent': (49.36038, -0.87893), 'ruquet': (49.36500, -0.86336), 'wn65': (49.36448, -0.86368), 'ncdu': (49.36510, -0.86310),
    'cemetery': (49.35878, -0.85640), 'wn62': (49.36041, -0.84769), 'div1': (49.35918, -0.84816), 'wn61': (49.35938, -0.83890),
    'wn60': (49.35644, -0.83120), 'colleville_ch': (49.34869, -0.84781), 'colleville': (49.34876, -0.85209), 'cabourg': (49.35091, -0.83652),
    'hameau': (49.34958, -0.81740), 'bray': (49.34751, -0.85756), 'louvieres': (49.36378, -0.91870), 'vacqueville': (49.35995, -0.90324),
    'gruchy': (49.38076, -0.92611), 'formigny': (49.33568, -0.89894), 'surrain': (49.32773, -0.86371),
    # placed from Maps V and VI or a description, ±200 to 300 m [DERIVED in the note]
    'wn71': (49.37686, -0.90117), 'wn70': (49.37382, -0.89268), 'wn66': (49.36866, -0.87597), 'wn68': (49.36753, -0.87392),
    'wn67': (49.36408, -0.87346), 'wn64': (49.36266, -0.85882),
}
P = {k: M(*v) for k, v in PLACES.items()}
P['wn69'], P['wn63'] = P['stlaurent'], P['colleville_ch']  # in the villages, ±300 m [the note]
# The sector boundaries on the shore, west to east, at D-1 and between the draws [the note's §1.3, ±100 m]
SECTORS = ['Charlie', 'Dog Green', 'Dog White', 'Dog Red', 'Easy Green', 'Easy Red', 'Fox Green', 'Fox Red']
BOUNDS = [M(*ll) for ll in [(49.37901, -0.90283), (49.37415, -0.88958), (49.37083, -0.88023), (49.36894, -0.87399), (49.36706, -0.86680),
                            (49.36167, -0.84823), (49.35898, -0.83445)]]
# The touchdown points (§3.5): each company's landing at its column on Maps V and VI, at the waterline at its time, ±150 m
TOUCH = {
    'rgr2c': (49.38356, -0.90522), 'a116': (49.37912, -0.89620), 'f116': (49.37096, -0.87229), 'g116': (49.37108, -0.87252),
    'g116e': (49.36934, -0.86667), 'e116w': (49.36505, -0.85153), 'e16': (49.36450, -0.84969), 'f16w': (49.36381, -0.84688),
    'fox_green': (49.36220, -0.83792), 'l16': (49.36035, -0.82966), 'd116': (49.38740, -0.91256), 'b116': (49.37997, -0.89933),
    'rgr2ab': (49.37627, -0.89142), 'c116': (49.37376, -0.88281), 'rgr5': (49.37259, -0.88186), 'h116': (49.37165, -0.87638),
    'ik116': (49.36909, -0.86843), 'l116': (49.36846, -0.86616), 'm116': (49.36748, -0.86343), 'ab16': (49.36512, -0.85513),
    'g16': (49.36455, -0.85101), 'c16': (49.36352, -0.85044), 'h16': (49.36324, -0.84828), 'km16': (49.36209, -0.83993), 'i16': (49.36066, -0.83845),
}
TD = {k: M(*v) for k, v in TOUCH.items()}
# Midnight on Map IX, by the note's fit (±400 m), in the note's local metres
MAPIX = {k: N(*v) for k, v in {
    'vgroup': (-2370, 670), 'bn1_116': (-2521, 79), 'eng121': (-2067, 45), 'parker': (-3696, 326), 'stl_oval': (-226, -653),
    'bn3_116': (22, -1244), 'bn1_115': (-313, -1520), 'bn3_115': (582, -1351), 'bn2_26': (319, -1487), 'bn3_26': (325, -1689),
    'bn3_18': (556, -1874), 'bn1_18': (831, -1942), 'bn1_16a': (1056, -2325), 'bn1_16b': (1351, -2700), 'bn2_16': (1593, -2223),
    'bn2_18': (2410, -2990), 'cabourg_n': (2390, -1417)}.items()}
DD_LAUNCH = [N(3905, 4601), N(4416, 4227)]  # the line 6,000 yards off Easy Red and Fox Green where the 741st's DD tanks swam off

# ---- roads: through the note's anchors; each draw's road follows the DEM's valley floor up from its mouth ----
def valley(mouth, goal, step=30, window=60):
    pts = [mouth]
    while math.dist(pts[-1], goal) > 200 and len(pts) < 80:
        x, y = pts[-1]; d = math.dist((x, y), goal); ux, uy = (goal[0] - x) / d, (goal[1] - y) / d
        cands = [(x + ux * step - uy * s, y + uy * step + ux * s) for s in range(-window, window + 1, 15)]
        pts.append(min(cands, key=lambda p: (z(*p) or 999) + 0.1 * abs((p[0] - x) * -uy + (p[1] - y) * ux)))
    pts.append(goal)
    return [(round(x), round(y)) for x, y in pts[::3] + [pts[-1]]]
D1 = valley(to_line(P['wn72'], -20), P['vierville_ch'])
D3 = valley(to_line(P['moulins'], -20), P['stl_ch'])
E1 = valley(to_line(P['ruquet'], -20), (400, -880))
E3 = valley(to_line(BOUNDS[5], -20), (1800, -1950))
F1 = valley(to_line((3100, -1050), -20), P['cabourg'])
COAST_RD = [(-HALF_EXTENT, 900), (-4000, 850), (-3000, 800), P['vierville'], P['hamel'], (-1100, 100), (-500, -500), P['stlaurent'],
            (400, -1000), (1000, -1450), P['colleville'], P['colleville_ch'], P['cabourg'], (3600, -1950), P['hameau'], (HALF_EXTENT, -2000)]
FORMIGNY_RD = [P['vierville'], (-2250, 300), (-2300, -400), (-2100, -1300), (-1900, -2400), P['formigny'], (-1600, -HALF_EXTENT)]
PROMENADE = contour(-25, P['wn72'][0], BOUNDS[5][0])
SHINGLE = contour(-8, BOUNDS[3][0], 3700)
SEA_WALL = contour(-8, P['wn72'][0], BOUNDS[3][0])

# ---- the obstacles: three staggered bands on the flat [OBH ch. 2] ----
# Element C about 250 yards out from the high-water line, log ramps 20 to 25 yards landward of it, hedgehogs 130 yards
# from shore: 229, 208 and 119 m. Each is a row of small posts every 18 m, in runs of about 120 m with gaps, from under
# the cliffs west of D-1 to Fox Red. They are baked into the map, and the tide covers them as it rises. The gaps the
# engineers blew (two in the 116th's half, four on Easy Red [OBH ch. 3]) are 50 m stretches drawn until the minute they
# went, 06:50 to 07:00 [INF].
def along_line(line, every):  # points every `every` metres along a polyline, with the distance at each
    out, acc = [], 0.0
    for a, b in zip(line, line[1:]):
        seg = math.dist(a, b); s = (every - acc % every) % every
        while s < seg: out.append((acc + s, (a[0] + (b[0] - a[0]) * s / seg, a[1] + (b[1] - a[1]) * s / seg))); s += every
        acc += seg
    return out
def post(p, r=1.6): return [[round(p[0] - r, 1), round(p[1] - r, 1)], [round(p[0] + r, 1), round(p[1] - r, 1)], [round(p[0] + r, 1), round(p[1] + r, 1)], [round(p[0] - r, 1), round(p[1] + r, 1)]]
GAPS = [((-700, 800), "06:55"), ((350, 230), "06:58"), ((1150, -250), "06:50"), ((1400, -330), "06:52"), ((1650, -420), "06:56"), ((1900, -520), "07:00")]
OBSTACLES = []
for w, phase in [(229, 0), (208, 60), (119, 30)]:
    for s, p in along_line(contour(w, -2600, 3700), 18):
        if (s + phase) % 160 >= 120: continue
        gap = next((t for c, t in GAPS if abs(p[0] - c[0]) < 25 * 1.1), None)
        OBSTACLES.append(dict(type="battery", poly=post(p), **({"until": gap} if gap else {})))

# ---- the strongpoints: earthworks 50 m across at each Widerstandsnest [INF] ----
def ring(c, r=25, n=8): return [[round(c[0] + r * math.cos(2 * math.pi * i / n)), round(c[1] + r * math.sin(2 * math.pi * i / n))] for i in range(n)]
WN = ['wn60', 'wn61', 'wn62', 'wn63', 'wn64', 'wn65', 'wn66', 'wn67', 'wn68', 'wn69', 'wn70', 'wn71', 'wn72', 'wn73', 'wn74']

def label(name, p, dx=0, dy=0, **kw): return dict(name=name, at=[p[0] + dx, p[1] + dy], **kw)
def rd(pts, name="", at=None, rot=0, **kw): return dict(type="road", name=name, pts=[list(p) for p in pts], **({"at": list(at), "rot": rot} if at else {}), **kw)
features = [dict(type="water", poly=[list(p) for p in sea(w)], **{"from": a, "until": b}) for a, b, w in TIDE_STEPS] + OBSTACLES + [
    dict(type="redoubt", poly=ring(P[k])) for k in WN] + [
    rd(COAST_RD, "coastal highway", (-1150, -80), -37), rd(FORMIGNY_RD, "road to Formigny", (-2380, -1500), 80), rd(D1), rd(D3), rd(E1), rd(E3), rd(F1),
    rd(PROMENADE),
    dict(type="works", name="sea wall", pts=[list(p) for p in SEA_WALL]), dict(type="works", name="shingle bank", pts=[list(p) for p in SHINGLE]),
    label("VIERVILLE", P['vierville'], dy=160), label("ST-LAURENT", P['stlaurent'], dy=-170), label("COLLEVILLE", P['colleville'], dx=-80, dy=170),
    label("les Moulins", P['moulins'], dx=-170, dy=-90), label("Hamel-au-Prêtre", P['hamel'], dy=-110),
    label("Cabourg", P['cabourg'], dy=-130), label("le Grand Hameau", P['hameau'], dy=140), label("Château de Vaumicel", P['vaumicel'], dx=-80, dy=-120),
    label("Louvières", P['louvieres'], dy=120), label("Gruchy", P['gruchy'], dy=-120), label("Vacqueville", P['vacqueville'], dy=-110),
    label("FORMIGNY", P['formigny'], dy=150), label("Surrain", P['surrain'], dy=130), label("le Bray", P['bray'], dy=-110),
    label("Pointe de la Percée", P['percee'], dx=150, dy=-130),
    label("D-1", D1[4], dx=-80), label("D-3", D3[5], dx=80), label("E-1", E1[4], dx=90), label("E-3", E3[4], dx=90), label("F-1", F1[3], dx=90),
    label("to Pointe du Hoc", (-4500, 1050), rot=-3),
]
# The eight sectors' names on the sand, each until the water reaches it
for i, name in enumerate(SECTORS):
    a = BOUNDS[i - 1] if i else (BOUNDS[0][0] - 700, BOUNDS[0][1] + 650)
    b = BOUNDS[i] if i < len(BOUNDS) else (BOUNDS[-1][0] + 700, BOUNDS[-1][1] - 250)
    p = to_line(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), 70)
    features.append(label(name.upper(), p, until=next(fmt(s) for s in range(sec(START), sec(END), 300) if not dry(p, s, -15))))
TREES_CLEAR = [[list(p) for p in sea(-40)]]
# The plateau was bocage, small fields in hedgerows [the note]. It is drawn as fields of 250 to 400 m on the plateau, a fifth
# left to trees, so woods stay on the bluff slopes, in the draws and in a few blocks inland [INF]; the hedgerows
# themselves are not drawn, since the note gives no line for them.
def quad(c, w, h, rot=20):
    r = math.radians(rot); u, v = (math.cos(r), math.sin(r)), (-math.sin(r), math.cos(r))
    return [[round(c[0] + a * w * u[0] + b * h * v[0]), round(c[1] + a * w * u[1] + b * h * v[1])] for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
RND = random.Random(1944)
FIELDS = []
for x in range(-4800, 5000, 330):
    for y in range(-4900, 3500, 280):
        c, w, h, rot = (x + RND.uniform(-90, 90), y + RND.uniform(-80, 80)), RND.uniform(120, 190), RND.uniform(90, 150), RND.uniform(5, 40)
        if RND.random() < 0.8 and seaward(c) < -300 and all((z(*p) or 0) > 25 for p in quad(c, w, h, rot)): FIELDS.append(quad(c, w, h, rot))

# ---- order of battle: (id, side, short, name, commander, type, strength, extra) ----
# Rifle companies 186 (six boat sections of 31), heavy-weapons companies 160 with the battalion headquarters, Ranger
# companies 65 [the note §2.1]; follow-up battalions about 870 [GK in the note]. German strengths are the note's
# inferences round the Allied estimate of 800 to 1,000 men in the strongpoints.
LOOSE = dict(loose=True)
OOB = [
    # 116th Regimental Combat Team (29th Infantry Division), Dog Green to Easy Green
    ("cmd116", "us", "Canham, Cota", "116th RCT command group with the 29th Division's assistant commander", "Col. Charles D. W. Canham; Brig. Gen. Norman D. Cota", "infantry", 100, LOOSE),
    ("a116", "us", "A/116", "A Company, 116th Infantry", "Capt. Taylor Fellers", "infantry", 186, LOOSE),
    ("b116", "us", "B/116", "B Company, 116th Infantry, scattered across nearly a mile", "", "infantry", 186, LOOSE),
    ("c116", "us", "C/116", "C Company, 116th Infantry", "", "infantry", 186, LOOSE),
    ("d116", "us", "D/116, 1st Bn HQ", "D Company and 1st Battalion headquarters, 116th Infantry", "", "infantry", 160, LOOSE),
    ("e116", "us", "E/116", "E Company, 116th Infantry: four sections a mile east of its sector, on Fox Green", "", "infantry", 124, LOOSE),
    ("e116w", "us", "E/116", "E Company, 116th Infantry: the two sections that landed on Easy Red", "", "infantry", 62, LOOSE),
    ("f116", "us", "F/116", "F Company, 116th Infantry", "", "infantry", 186, LOOSE),
    ("g116", "us", "G/116", "G Company, 116th Infantry", "", "infantry", 186, LOOSE),
    ("h116", "us", "H/116, 2nd Bn HQ", "H Company and 2nd Battalion headquarters, 116th Infantry", "Maj. Sidney Bingham (2nd Bn)", "infantry", 160, LOOSE),
    ("i116", "us", "I/116", "I Company, 116th Infantry", "", "infantry", 186, LOOSE),
    ("k116", "us", "K/116", "K Company, 116th Infantry", "", "infantry", 186, LOOSE),
    ("l116", "us", "L/116", "L Company, 116th Infantry", "", "infantry", 186, LOOSE),
    ("m116", "us", "M/116, 3rd Bn HQ", "M Company and 3rd Battalion headquarters, 116th Infantry", "", "infantry", 160, LOOSE),
    # 16th Regimental Combat Team (1st Infantry Division), Easy Red to Fox Red
    ("cmd16", "us", "Taylor", "16th RCT command group", "Col. George A. Taylor", "infantry", 100, LOOSE),
    ("a16", "us", "A/16", "A Company, 16th Infantry", "", "infantry", 186, LOOSE),
    ("b16", "us", "B/16", "B Company, 16th Infantry", "", "infantry", 186, LOOSE),
    ("c16", "us", "C/16", "C Company, 16th Infantry", "", "infantry", 186, LOOSE),
    ("d16", "us", "D/16, 1st Bn HQ", "D Company and 1st Battalion headquarters, 16th Infantry", "", "infantry", 160, LOOSE),
    ("e16", "us", "E/16", "E Company, 16th Infantry, less Spalding's section", "", "infantry", 155, LOOSE),
    ("spalding", "us", "Spalding", "Lt. John Spalding's section of E Company, 16th Infantry (a boat section, 31 men)", "Lt. John Spalding", "infantry", 31, LOOSE),
    ("f16", "us", "F/16", "F Company, 16th Infantry, scattered from E-3 to 1,000 yards east", "", "infantry", 186, LOOSE),
    ("g16", "us", "G/16", "G Company, 16th Infantry", "Capt. Joseph Dawson", "infantry", 186, LOOSE),
    ("h16", "us", "H/16, 2nd Bn HQ", "H Company and 2nd Battalion headquarters, 16th Infantry", "", "infantry", 160, LOOSE),
    ("i16", "us", "I/16", "I Company, 16th Infantry, carried almost to Port-en-Bessin before it turned back", "", "infantry", 186, LOOSE),
    ("k16", "us", "K/16", "K Company, 16th Infantry", "", "infantry", 186, LOOSE),
    ("l16", "us", "L/16", "L Company, 16th Infantry", "", "infantry", 186, LOOSE),
    ("m16", "us", "M/16, 3rd Bn HQ", "M Company and 3rd Battalion headquarters, 16th Infantry", "", "infantry", 160, LOOSE),
    # the Rangers
    ("rgr2a", "us", "A/2 Rangers", "A Company, 2nd Ranger Battalion", "", "infantry", 65, LOOSE),
    ("rgr2b", "us", "B/2 Rangers", "B Company, 2nd Ranger Battalion", "", "infantry", 65, LOOSE),
    ("rgr2c", "us", "C/2 Rangers", "C Company, 2nd Ranger Battalion, on Charlie", "Capt. Ralph Goranson", "infantry", 64, LOOSE),
    ("rgr5", "us", "5th Rangers", "5th Ranger Battalion, less A Company (its strength drawn as 380)", "Lt. Col. Max Schneider", "infantry", 380, LOOSE),
    ("rgr5a", "us", "A/5 Rangers", "A Company, 5th Ranger Battalion (drawn as 70)", "Lt. Charles Parker", "infantry", 70, LOOSE),
    # the tanks
    ("t743a", "us", "A/743 Tank", "A Company, 743rd Tank Battalion, with the tank dozers, landed from LCTs", "Lt. Col. John Upham (wounded), battalion", "armor", 16, {}),
    ("t743b", "us", "B/743 Tank", "B Company, 743rd Tank Battalion: DD tanks carried in to the beach on LCTs", "", "armor", 16, {}),
    ("t743c", "us", "C/743 Tank", "C Company, 743rd Tank Battalion: DD tanks carried in to the beach on LCTs", "", "armor", 16, {}),
    ("t741a", "us", "A/741 Tank", "A Company, 741st Tank Battalion, landed from LCTs", "Lt. Col. Robert Skaggs, battalion", "armor", 16, {}),
    ("t741dd", "us", "741st DD", "B and C Companies, 741st Tank Battalion: 32 DD tanks launched 6,000 yards out", "", "armor", 32, {}),
    ("t745b", "us", "B/745 Tank", "B Company, 745th Tank Battalion", "", "armor", 16, {}),
    # engineers
    ("setf116", "us", "Engineers", "Special Engineer Task Force, the 116th's half: 146th Engineer Combat Battalion and Navy Combat Demolition Units, eight assault and four support teams", "", "infantry", 492, LOOSE),
    ("setf16", "us", "Engineers", "Special Engineer Task Force, the 16th's half: 299th Engineer Combat Battalion and Navy Combat Demolition Units (drawn the same size as the 116th's half)", "", "infantry", 492, LOOSE),
    ("eng149", "us", "149th Engrs", "C Company, 149th Engineer Combat Battalion, with the 37th Engineer Combat Battalion, at E-1 (drawn as 300)", "", "infantry", 300, {}),
    ("eng336", "us", "336th Engrs", "336th Engineer Combat Battalion (drawn as 300)", "", "infantry", 300, {}),
    ("eng121", "us", "C/121 Engrs", "C Company, 121st Engineer Combat Battalion (drawn as 150)", "", "infantry", 150, {}),
    # artillery ashore in the afternoon
    ("fa7", "us", "7th FA", "7th Field Artillery Battalion, five 105 mm howitzers; six were lost on DUKWs", "", "artillery", 75, dict(guns=5)),
    ("fa58", "us", "58th AFA", "58th Armored Field Artillery Battalion: four of its M7s ashore", "", "artillery", 60, dict(guns=4)),
    ("fa62", "us", "62nd AFA", "62nd Armored Field Artillery Battalion: six M7s landed from 3 to 6:30 PM, eight more at dark", "", "artillery", 90, dict(guns=6)),
    ("fa111", "us", "111th FA", "111th Field Artillery Battalion: one howitzer ashore of the thirteen it loaded on DUKWs", "", "artillery", 14, dict(guns=1)),
    # the follow-up regiments
    ("r18_1", "us", "1/18", "1st Battalion, 18th Infantry", "Col. George A. Smith Jr., regiment", "infantry", 870, {}),
    ("r18_2", "us", "2/18", "2nd Battalion, 18th Infantry", "Col. George A. Smith Jr., regiment", "infantry", 870, {}),
    ("r18_3", "us", "3/18", "3rd Battalion, 18th Infantry", "Col. George A. Smith Jr., regiment", "infantry", 870, {}),
    ("r115_1", "us", "1/115", "1st Battalion, 115th Infantry", "Col. Eugene N. Slappey, regiment", "infantry", 870, {}),
    ("r115_2", "us", "2/115", "2nd Battalion, 115th Infantry", "Col. Eugene N. Slappey, regiment", "infantry", 870, {}),
    ("r115_3", "us", "3/115", "3rd Battalion, 115th Infantry", "Col. Eugene N. Slappey, regiment", "infantry", 870, {}),
    ("r26_2", "us", "2/26", "2nd Battalion, 26th Infantry", "Col. John F. R. Seitz, regiment", "infantry", 870, {}),
    ("r26_3", "us", "3/26", "3rd Battalion, 26th Infantry", "Col. John F. R. Seitz, regiment", "infantry", 870, {}),
    # Fire Support Group "O": destroyers, each drawn with four guns
    ("dd_mccook", "us", "McCook", "USS McCook, destroyer, supporting the 29th Division", "", "artillery", 60, dict(guns=4)),
    ("dd_carmick", "us", "Carmick", "USS Carmick, destroyer, supporting the 29th Division", "", "artillery", 60, dict(guns=4)),
    ("dd_frankford", "us", "Frankford", "USS Frankford, destroyer, the squadron's flagship, supporting the 1st Division", "Capt. Harry Sanders, squadron", "artillery", 60, dict(guns=4)),
    ("dd_doyle", "us", "Doyle", "USS Doyle, destroyer, supporting the 1st Division", "", "artillery", 60, dict(guns=4)),
    ("dd_harding", "us", "Harding", "USS Harding, destroyer, supporting the 1st Division", "", "artillery", 60, dict(guns=4)),
    ("dd_baldwin", "us", "Baldwin", "USS Baldwin, destroyer, supporting the 1st Division", "", "artillery", 60, dict(guns=4)),
    ("dd_emmons", "us", "Emmons", "USS Emmons, destroyer, supporting the 1st Division", "", "artillery", 60, dict(guns=4)),
    # Germans: the 916th Grenadier Regiment's coast defence sector 2, with III./726 attached, and its reserves
    ("wn60", "german", "WN 60", "Widerstandsnest 60 at F-1: a 7.5 cm gun, mortars, a 2 cm Flak 38 (40 men drawn)", "", "artillery", 40, dict(guns=1)),
    ("wn61", "german", "WN 61", "Widerstandsnest 61 on Fox Green: an 8.8 cm gun (more than 20 men)", "", "artillery", 20, dict(guns=1)),
    ("wn62", "german", "WN 62", "Widerstandsnest 62 east of E-3, the largest: two casemates for 7.5 cm guns and a 5 cm anti-tank gun (40 drawn)", "", "artillery", 40, dict(guns=3)),
    ("wn63", "german", "WN 63", "Widerstandsnest 63, the command post at Colleville, about here (40 drawn)", "", "infantry", 40, {}),
    ("wn64", "german", "WN 64", "Widerstandsnest 64 on the bluff east of E-1, about here: a Russian 7.62 cm gun and a 2 cm Flak (25 drawn)", "", "artillery", 25, dict(guns=2)),
    ("wn65", "german", "WN 65", "Widerstandsnest 65 on the east side of E-1: a 5 cm anti-tank gun in an H 677 bunker and a 7.5 cm gun (25 drawn)", "", "artillery", 25, dict(guns=2)),
    ("wn66", "german", "WN 66", "Widerstandsnest 66, west of D-3, about here: an unfinished 5 cm anti-tank bunker and an anti-tank ditch (30 drawn)", "", "artillery", 30, dict(guns=1)),
    ("wn67", "german", "WN 67", "Widerstandsnest 67 behind D-3, about here: Nebelwerfer Abteilung 84's rocket launchers (30 drawn)", "", "infantry", 30, {}),
    ("wn68", "german", "WN 68", "Widerstandsnest 68 on the bluff east of D-3, about here: a Panzer IV turret on a Tobruk and a 5 cm anti-tank gun (30 drawn)", "", "artillery", 30, dict(guns=2)),
    ("wn69", "german", "WN 69", "Widerstandsnest 69 in St-Laurent, about here: about a company (50 drawn)", "", "infantry", 50, {}),
    ("wn70", "german", "WN 70", "Widerstandsnest 70 on the bluff between D-1 and D-3, about here: two 7.5 cm guns (30 drawn)", "", "artillery", 30, dict(guns=2)),
    ("wn71", "german", "WN 71", "Widerstandsnest 71 on the plateau east of D-1, about here (30 drawn)", "", "infantry", 30, {}),
    ("wn72", "german", "WN 72", "Widerstandsnest 72 at the mouth of D-1, the best built: an 8.8 cm Pak 43 casemate and a 5 cm bunker (40 drawn)", "", "artillery", 40, dict(guns=2)),
    ("wn73", "german", "WN 73", "Widerstandsnest 73 on the west side of D-1: a 7.5 cm gun firing down on the beach (20 drawn)", "", "artillery", 20, dict(guns=1)),
    ("wn74", "german", "WN 74", "Widerstandsnest 74, the radar station at Pointe de la Percée (20 drawn)", "", "infantry", 20, {}),
    ("art1", "german", "352 AR", "352nd Artillery Regiment, a battery of four 10.5 cm howitzers (the batteries' places were not found: about here)", "", "artillery", 80, dict(guns=4)),
    ("art2", "german", "352 AR", "352nd Artillery Regiment, a battery of four 10.5 cm howitzers (about here)", "", "artillery", 80, dict(guns=4)),
    ("art3", "german", "352 AR", "352nd Artillery Regiment, a battery of four 10.5 cm howitzers (about here)", "", "artillery", 80, dict(guns=4)),
    ("art4", "german", "352 AR", "352nd Artillery Regiment, a battery of four 15 cm howitzers (about here)", "", "artillery", 80, dict(guns=4)),
    ("res916", "german", "II./916", "The 916th Grenadier Regiment's two reserve companies from Formigny, II. Bataillon's headquarters (300 drawn)", "Hauptmann Grimme", "infantry", 300, {}),
    ("ii915", "german", "II./915", "II./915, Kampfgruppe Meyer's battalion split off to the 916th, with an anti-tank company (600 drawn)", "", "infantry", 600, {}),
    ("eng352", "german", "352 Pioniere", "352nd Engineer Battalion, the division's last reserve, given to the 916th in the evening (400 drawn)", "", "infantry", 400, {}),
]
BASE = {row[0]: row for row in OOB}
DESTROYERS = [r[0] for r in OOB if r[0].startswith("dd_")]

# ---- movement ----
KEYS = {}
def K(t, p, **kw): return dict(t=t, x=round(p[0]), y=round(p[1]), **kw)
def carried(id, f): return next((k[f] for k in reversed(KEYS.get(id, [])) if f in k), None)
def keys(id, ks):  # every leg starts where the unit stands, unless it is coming out of hiding
    have = KEYS.setdefault(id, [])
    if have and ks:
        a, b = have[-1], ks[0]
        assert sec(b["t"]) >= sec(a["t"]), (id, a["t"], b["t"], "a key before the last one: the unit is still on its way")
        assert carried(id, "state") == "hidden" or (a["x"], a["y"]) == (b["x"], b["y"]), (id, a["t"], b["t"], "a leg must start where the unit stands")
        if a["t"] == b["t"]: a.update({k: v for k, v in b.items() if k != "t"}); ks = ks[1:]
    have += ks
def appear(id, t, p, h, state="line", **kw): keys(id, [K(t, p, h=h, state=state, **kw)])
for id in BASE: appear(id, START, (0, 0), 0, state="hidden")

# ---- assemble and check ----
TOP = {"infantry": 6, "artillery": 6, "armor": 30}  # km/h, the fastest any leg may go ashore
units = []
for id, side, short, name, commander, type, strength0, extra in OOB:
    units.append(dict(id=id, side=side, name=name, short=short, commander=commander, type=type, strength=strength0, keys=KEYS[id], **extra))
for f in features:
    if "at" in f:
        t_last = f.get("until", END)
        assert max(map(abs, f["at"])) < HALF_EXTENT - 100 and dry(f["at"], sec(t_last) - 60), (f.get("name"), f["at"], "a label off the map or under the water")

SOURCES = [
    "Terrain: " + T["source"] + ", 30 m. A surface model, which sets the sea to 0: its coast is the high-water line of 1944, and the tidal flat is built seaward of it as a straight 1:50 slope 274 m wide (300 yards), from 5.5 m at the shingle to the low-water mark.",
]
battle = dict(
    id="omaha-beach", name="Omaha Beach", date="1944-06-06", dateText="6 June 1944", place="Omaha Beach, Calvados, Normandy, France",
    origin=dict(lat=LAT0, lon=LON0), extent=2 * HALF_EXTENT, start=START, end=END, sunrise="05:59", sunset="22:05", speed=60, lapse=600, menPerDot=10,
    water=WATER, terrainExaggeration=1.5, contourInterval=5, trees=dict(density=0.0002, clear=TREES_CLEAR), fields=FIELDS, wind=dict(x=0.5, y=-0.4),
    view=dict(x=0, y=0, width=2 * HALF_EXTENT),
    sides=dict(us=dict(name="Americans (V Corps: the 1st Infantry Division, with the 29th's 116th and 115th Infantry and the Rangers)", color="#3a5f9e", light="#7d9bd0", dark="#1d3561"),
               german=dict(name="Germans (352nd Infantry Division, Kraiss)", color="#b8322a", light="#de5d50", dark="#5c1712")),
    features=features, units=units, events=[], sources=SOURCES,
)
json.dump(battle, open(HERE + "battle.json", "w"), indent=1, ensure_ascii=False)
print(len(units), "units,", len(TIDE_STEPS), "tide steps,", len(OBSTACLES), "obstacle posts,", len(changed), "flat cells")
