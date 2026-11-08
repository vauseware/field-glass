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
    label("D-1", D1[2], dx=110), label("D-3", D3[5], dx=80), label("E-1", E1[4], dx=90), label("E-3", E3[4], dx=90), label("F-1", F1[3], dx=90),
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
def last(id): k = KEYS[id][-1]; return (k["x"], k["y"])
def heading(a, b): return round(math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) % 360)
def hold_until(id, t0):  # stand until the minute before t0, then turn and go
    if sec(t0) - sec(KEYS[id][-1]["t"]) > 120: keys(id, [K(plus(t0, -1), last(id))])
def at(id, t, **kw): hold_until(id, t); keys(id, [K(t, last(id), **kw)])  # a change in place
def dense(pts, step=600):  # no straight leg longer than `step`
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        n = max(1, math.ceil(math.dist(a, b) / step))
        out += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(1, n + 1)]
    return [p for i, p in enumerate(out) if i == 0 or math.dist(p, out[i - 1]) > 5]
PACE = 3  # km/h: foot inland through the hedgerows, or along the beach under fire
def walk(t0, pts, state="column", kmh=PACE):  # keys along a path at a pace
    pts = dense(pts); t, out = sec(t0), []
    for i, p in enumerate(pts):
        if i: t += math.dist(pts[i - 1], p) / (kmh / 3.6)
        out.append(K(fmt(t), p, h=heading(p, pts[i + 1]) if i + 1 < len(pts) else heading(pts[i - 1], p), **(dict(state=state) if i == 0 else {})))
    return out
def move(id, t0, pts, h=None, state="line", moving="column", kmh=PACE):  # from where it stands along pts at a pace; returns the arrival time
    hold_until(id, t0)
    ks = walk(t0, [last(id)] + list(pts), moving, kmh)
    if len(ks) == 1: at(id, t0, state=state, **({"h": h} if h is not None else {})); return t0
    ks[-1]["state"] = state
    if h is not None: ks[-1]["h"] = h
    keys(id, ks); return ks[-1]["t"]
def go(id, t0, t1, pts, h=None, state="line", moving="column"):  # from where it stands along pts, arriving at t1
    hold_until(id, t0)
    pts = dense([last(id)] + list(pts)); d = [0]
    if len(pts) == 1: return at(id, t1, state=state, **({"h": h} if h is not None else {}))
    for a, b in zip(pts, pts[1:]): d.append(d[-1] + math.dist(a, b))
    ks = [K(fmt(sec(t0) + (sec(t1) - sec(t0)) * d[i] / d[-1]), p, h=heading(p, pts[i + 1]) if i + 1 < len(pts) else heading(pts[i - 1], p)) for i, p in enumerate(pts)]
    ks[0]["state"] = moving; ks[-1]["state"] = state
    if h is not None: ks[-1]["h"] = h
    keys(id, ks)
def fire(id, t0, t1, state="line"): at(id, t0, state="firing"); at(id, t1, state=state)
def along(line, a, b):  # the stretch of a road between the points on it nearest a and b
    def proj(p):
        best = None
        for i, (u, v) in enumerate(zip(line, line[1:])):
            dx, dy = v[0] - u[0], v[1] - u[1]; f = max(0, min(1, ((p[0] - u[0]) * dx + (p[1] - u[1]) * dy) / (dx * dx + dy * dy or 1)))
            q = (u[0] + f * dx, u[1] + f * dy)
            if best is None or math.dist(p, q) < best[0]: best = (math.dist(p, q), i + f, q)
        return best[1], best[2]
    (sa, qa), (sb, qb) = proj(a), proj(b)
    mid = [line[i] for i in range(math.floor(min(sa, sb)) + 1, math.ceil(max(sa, sb)))]
    return [qa] + (mid if sa <= sb else mid[::-1]) + [qb]
def off(p, dx, dy): return (p[0] + dx, p[1] + dy)
LOSS = {}  # id: [(t0, t1, men)], losses falling evenly over each span; a negative figure is men joining
def lose(id, t0, t1, n): LOSS.setdefault(id, []).append((t0, t1, n))
def smoke(at, t0, t1, rate=10, spread=150): features.append(dict(type="smoke", at=list(at), rate=rate, spread=spread, **{"from": t0, "until": t1}))
def hull(c, h, L, W):  # a boat's outline, bow toward compass heading h
    s, co = math.sin(math.radians(h)), math.cos(math.radians(h))
    return [[round(c[0] + a * s + b * co, 1), round(c[1] + a * co - b * s, 1)] for a, b in [(-L / 2, -W / 2), (L / 2 - L / 6, -W / 2), (L / 2, 0), (L / 2 - L / 6, W / 2), (-L / 2, W / 2)]]
for id in BASE: appear(id, START, (0, 0), 0, state="hidden")

# Places the movements use, as local metres
ALONG = heading(BOUNDS[0], BOUNDS[-1])  # the beach's run, west-north-west to east-south-east
def shore(p, w=-15): return to_line(p, w)  # straight in from p to the shingle or the sea wall
def edge(p, t, w=0): return to_line(p, waterline(t) + w)  # the water's edge at t, straight in or out from p
def inland(p): return heading(p, to_line(p, -100))
DW_TOP = to_line(off(TD['c116'], -150, 0), -330)  # the bluff top above Dog White, where the 116th and the Rangers went up
VIERVILLE, STL, COLLEVILLE_W = P['vierville'], P['stlaurent'], (1600, -2060)

# Each company comes in on its craft at its minute and stands at the water's edge [the note §3.5]: six LCVPs for a
# rifle company, drawn from three minutes before touchdown to five after [INF].
def land(id, t, p, craft=6, h=None):
    q = edge(p, t, 10); h = inland(q) if h is None else h
    appear(id, t, q, h, state="line")
    run = (math.sin(math.radians(ALONG)), math.cos(math.radians(ALONG)))
    for i in range(craft):
        u = (i - (craft - 1) / 2) * 32; c = edge((q[0] + run[0] * u, q[1] + run[1] * u), t, 18)
        features.append(dict(type="ship", poly=hull(c, inland(c), 11, 3.2), **{"from": plus(t, -3), "until": plus(t, 5)}))
def cross(id, t0, t1, w=-15, state="line"):  # over the flat to the shingle or the wall, arriving at t1
    go(id, t0, t1, [shore(last(id), w)], h=inland(last(id)), state=state, moving="line")
def wade(id, t0, state="line"):  # up the beach at the edge of the water as the tide comes in, until the wall [OBH ch. 3]
    hold_until(id, t0); p0, t = last(id), sec(t0); ks = [K(t0, p0)]
    while True:
        t += 300; w = waterline(t) - 5
        q = to_line(p0, w if w > 10 else -15); ks.append(K(fmt(t), q, h=inland(q), state=state))
        if w <= 10: break
    keys(id, ks)

# ---- the DD tanks swim in, and the first tanks touch down at H-5 and H-Hour ----
# B and C Companies of the 741st are launched at 05:40, 6,000 yards out, and swim for Easy Red and Fox Green at about
# 4 knots; five reach the shore [OBH ch. 3].
DD_MID = ((DD_LAUNCH[0][0] + DD_LAUNCH[1][0]) / 2, (DD_LAUNCH[0][1] + DD_LAUNCH[1][1]) / 2)
appear("t741dd", "05:40", DD_MID, heading(DD_MID, BOUNDS[5]))
go("t741dd", "05:41", "06:29", [edge(off(BOUNDS[5], -150, 60), "06:29", 15)], state="line", moving="line")
lose("t741dd", "05:45", "06:25", 27)
land("t741a", "06:30", off(BOUNDS[5], 250, -120), craft=0); lose("t741a", "06:30", "06:32", 2); lose("t741a", "06:32", "06:45", 3)
land("t743b", "06:25", off(BOUNDS[0], 450, -230), craft=0); lose("t743b", "06:25", "06:40", 8)
land("t743c", "06:25", off(BOUNDS[1], 250, -160), craft=0)
land("t743a", "06:30", off(BOUNDS[3], 120, -50), craft=0)
for id in ("t741dd", "t741a", "t743b", "t743c", "t743a"):
    wade(id, plus(KEYS[id][-1]["t"], 1), state="firing")
# 17:00: D-1 open to Vierville, and the 741st's remaining tanks ordered inland by E-1; four attack St-Laurent [OBH ch. 5]
for id, dx in (("t743b", 0), ("t743c", 120)):
    move(id, "17:00", along(SEA_WALL, last(id), D1[0]) + D1 + [off(VIERVILLE, 150 + dx, 60)], h=200, kmh=6)
move("t741a", "17:00", along(SHINGLE, last("t741a"), E1[0]) + E1 + [(650, -900)], h=230, kmh=6)
move("t741dd", "17:10", along(SHINGLE, last("t741dd"), E1[0]) + E1 + [(150, -880)], h=260, kmh=6)
fire("t741dd", "19:30", "21:30")
move("t743a", "17:20", along(SHINGLE, last("t743a"), E1[0]) + E1[:4], h=200, kmh=6)
land("t745b", "16:30", off(BOUNDS[5], 700, -170), craft=0)
cross("t745b", "16:31", "16:50"); move("t745b", "19:00", along(SHINGLE, last("t745b"), F1[0]) + F1[:7], h=200, kmh=4)

# ---- the destroyers: on station by 05:50, firing to H-3; their own targets from 08:00; two close to 1,000 yards
# between 10:00 and 11:00 [OBH ch. 2, 4; NHF]. Stations are not recorded: drawn 1,700 to 2,600 m out off each
# division's sectors. Which two closed in is not recorded either: drawn as Carmick and Doyle, which went to 800 yards.
STATIONS = {"dd_mccook": ((-3300, 2350), 1500), "dd_carmick": (BOUNDS[1], 2000), "dd_harding": ((400, 200), 2500), "dd_frankford": ((1300, -300), 2100),
            "dd_baldwin": ((1950, -620), 2700), "dd_doyle": ((2600, -720), 1800), "dd_emmons": ((3700, -1080), 2300)}
for id, (p, w) in STATIONS.items():
    st = to_line(p, w); appear(id, START, st, heading(st, p))
    fire(id, "05:50", "06:27"); at(id, "08:00", state="firing")
    if id in ("dd_carmick", "dd_doyle"):
        close = to_line(p, 900); go(id, "10:00", "10:06", [close], h=heading(close, p), state="firing", moving="firing")
        go(id, "11:00", "11:06", [st], h=heading(st, p), state="firing", moving="firing")
        for a, b, c in (("05:30", "10:00", st), ("10:06", "11:00", close), ("11:06", END, st)):
            features.append(dict(type="ship", poly=hull(c, ALONG, 106, 11), **{"from": a, "until": b}))
    else: features.append(dict(type="ship", poly=hull(st, ALONG, 106, 11), **{"from": START}))
    at(id, "14:00", state="line")
AFLOAT = {id: END for id in STATIONS} | {"t741dd": "06:29"}

# ---- the first wave, 06:31: eight companies, most of them east of where they were sent [OBH ch. 3; Map V] ----
land("f116", "06:31", TD['f116']); land("g116", "06:31", TD['g116']); land("e116", "06:31", off(TD['fox_green'], -80, 30))
land("e116w", "06:31", TD['e116w'], craft=2); land("e16", "06:31", TD['e16']); land("spalding", "06:31", off(TD['e16'], -170, 60), craft=1)
land("f16", "06:31", off(TD['fox_green'], 90, -30)); land("a116", "06:36", TD['a116'])
land("setf116", "06:35", off(TD['c116'], 0, 0), craft=0); land("setf16", "06:35", off(TD['ab16'], 60, -30), craft=0)
lose("a116", "06:36", "06:51", 124)  # 'up to two-thirds'; the company out of action within fifteen minutes
lose("e16", "06:31", "07:00", 105); lose("setf116", "06:35", "07:05", 202); lose("setf16", "06:35", "07:05", 202)  # the engineers' 41%
for id, t in (("f116", "06:58"), ("g116", "06:55"), ("e116", "06:55"), ("e116w", "06:55"), ("e16", "07:00"), ("spalding", "06:50"), ("f16", "06:58")):
    cross(id, plus(KEYS[id][-1]["t"], 1), t)
wade("a116", "06:37")
for id in ("setf116", "setf16"): cross(id, "06:36", "07:15")
# C Company of the 2nd Rangers on Charlie at H+15: about 30 of 64 cross the sand, and go up the cliff 300 yards west;
# all are up by 07:30 and fight on the cliff top into the afternoon [OBH ch. 3, 4].
land("rgr2c", "06:45", TD['rgr2c'], craft=2); lose("rgr2c", "06:45", "07:00", 35); cross("rgr2c", "06:46", "07:00")
CLIFF = to_line(off(TD['rgr2c'], -220, 165), -70)
go("rgr2c", "07:00", "07:30", [CLIFF], h=heading(CLIFF, P['wn73']), moving="column"); fire("rgr2c", "07:35", "14:00")

# ---- the second group of waves, 07:00 to 07:40 ----
land("d116", "07:00", TD['d116']); land("b116", "07:00", TD['b116']); land("h116", "07:00", TD['h116'])
land("g16", "07:00", TD['g16']); land("k16", "07:00", TD['km16']); land("l16", "07:00", TD['l16'])
land("c116", "07:10", TD['c116']); lose("c116", "07:10", "07:20", 6)
lose("g16", "07:00", "07:30", 63); lose("k16", "07:00", "07:30", 53); lose("l16", "07:00", "08:00", 61)  # L reduced to 125
for id, t in (("d116", "07:20"), ("b116", "07:25"), ("h116", "07:20"), ("g16", "07:30"), ("k16", "07:25"), ("l16", "07:30"), ("c116", "07:20")):
    cross(id, plus(KEYS[id][-1]["t"], 1), t)
land("i116", "07:25", off(TD['ik116'], -60, 25)); land("k116", "07:28", off(TD['ik116'], 60, -25)); land("l116", "07:35", TD['l116'])
land("m116", "07:30", TD['m116']); land("h16", "07:30", TD['h16']); land("m16", "07:40", off(TD['km16'], 130, -40))
land("cmd116", "07:30", off(BOUNDS[2], -60, 40), craft=3)
land("a16", "07:40", off(TD['ab16'], -60, 20)); land("b16", "07:42", off(TD['ab16'], 70, -25)); land("c16", "07:40", TD['c16'])
land("d16", "07:44", off(TD['ab16'], 190, -70)); land("rgr2a", "07:35", off(TD['rgr2ab'], -50, 25), craft=2); land("rgr2b", "07:37", off(TD['rgr2ab'], 50, -25), craft=2)
lose("rgr2a", "07:35", "07:40", 30); lose("rgr2b", "07:37", "07:40", 38)  # about 35 and 27 reach the wall
land("rgr5", "07:50", TD['rgr5'], craft=6); land("rgr5a", "07:50", off(TD['rgr5'], 110, -45), craft=2); lose("rgr5", "07:50", "07:58", 8)
land("cmd16", "08:00", off(TD['ab16'], 120, -40), craft=3); lose("cmd16", "08:00", "08:15", 36)  # the executive officer and 35 men on the flat
land("i16", "08:00", TD['i16'])
for id, t in (("i116", "07:45"), ("k116", "07:47"), ("l116", "07:52"), ("m116", "07:48"), ("h16", "07:50"), ("m16", "07:58"), ("cmd116", "07:45"),
              ("a16", "07:58"), ("b16", "08:00"), ("c16", "07:58"), ("d16", "08:02"), ("rgr2a", "07:40"), ("rgr2b", "07:41"), ("rgr5", "07:58"),
              ("rgr5a", "07:58"), ("cmd16", "08:15"), ("i16", "08:15")):
    cross(id, plus(KEYS[id][-1]["t"], 1), t)

# ---- off the beach at Dog White: upwards of 600 men on a front of less than 300 yards, 08:00 to 09:00 [OBH ch. 4, 5] ----
go("c116", "07:50", "08:50", [DW_TOP], h=215); go("cmd116", "07:51", "08:30", [off(DW_TOP, 80, 120)], h=215)
go("rgr5", "08:10", "09:00", [off(DW_TOP, -150, 40)], h=230); go("rgr5a", "08:12", "09:00", [off(DW_TOP, 120, -40)], h=200)
go("rgr2a", "08:00", "08:30", [to_line(last("rgr2a"), -280)], h=210); go("rgr2b", "08:01", "08:30", [to_line(last("rgr2b"), -280)], h=210)
move("g116", "07:30", along(SEA_WALL, last("g116"), shore(off(TD['c116'], 120, -40))), h=30, state="line", kmh=1.5)  # G's remnants reach Dog White about 08:30
go("g116", "08:35", "09:25", [off(DW_TOP, 160, 120)], h=180)
for id, dx in (("c116", 0), ("cmd116", 60), ("rgr5", -120), ("rgr2a", -200), ("rgr2b", -260)):  # Vierville by 11:00 [OBH ch. 5; HAR]
    go(id, "10:00", "10:55", along(COAST_RD, last(id), VIERVILLE)[1:] + [off(VIERVILLE, dx, 40 if dx else -40)], h=250)
# C/116 and B Company of the 5th Rangers go west on the coast road before noon; the Rangers' attempt south is given up
# at 14:00; the main Ranger force is on the coast road west of Vierville at 17:00 [OBH ch. 5]
go("c116", "11:00", "11:50", along(COAST_RD, VIERVILLE, (-2900, 800))[1:], h=270, state="firing"); at("c116", "12:30", state="line")
go("rgr5", "12:00", "12:50", [(-2250, 250)], h=200, state="firing"); go("rgr5", "14:00", "14:40", [(-2550, 700)], h=230)
go("rgr5", "16:20", "17:00", along(COAST_RD, (-2550, 700), (-2750, 780))[1:], h=260)
for id, p in (("c116", off(MAPIX['vgroup'], -80, 60)), ("rgr5", off(MAPIX['vgroup'], 60, -60)), ("rgr2a", off(MAPIX['vgroup'], 140, 60)), ("rgr2b", off(MAPIX['vgroup'], -160, -40))):
    go(id, "20:00", "21:00", [p], h=250)
go("rgr2c", "15:00", "16:30", [off(MAPIX['vgroup'], 0, 160)], h=250)
# A Company of the 5th Rangers, Parker's platoon, inland past Vaumicel; it leaves the château at 14:30 and joins the
# 2nd Rangers' inland group south of the Grandcamp road about 21:00 [OBH ch. 5; Map IX]
go("rgr5a", "10:00", "13:30", [(-1950, 250), off(P['vaumicel'], 120, 40)], h=200); go("rgr5a", "14:30", "21:00", [(-3000, 150), MAPIX['parker']], h=270)
go("cmd116", "13:00", "13:20", [off(VIERVILLE, 0, -90)], h=180)
# the 2nd Battalion's men up from Dog Red, and the 116th's elements in St-Laurent at midnight [OBH-IX]
for id, dx in (("f116", -60), ("h116", 60), ("g116", 0)):
    go(id, "09:40" if id != "g116" else "10:00", "12:30", [off(DW_TOP, 300 + dx, -150), off(MAPIX['stl_oval'], -250 + dx, 200)], h=150)
    go(id, "19:00", "20:00", [off(MAPIX['stl_oval'], dx * 2, 60)], h=160)
# A Company stays at the wall; B Company and the 1st Battalion's headquarters come up D-1 once it is open [INF]
move("d116", "13:10", along(SEA_WALL, last("d116"), D1[0])[:1] + [D1[0]], h=120, kmh=2)
move("d116", "15:00", D1 + [off(VIERVILLE, -120, -150)], h=180, kmh=2); go("d116", "21:00", "22:30", [MAPIX['bn1_116']], h=200)
move("b116", "17:00", along(SEA_WALL, last("b116"), D1[0])[1:] + D1 + [off(VIERVILLE, 60, -200)], h=180, kmh=2.5)

# ---- 3rd Battalion, 116th: past the bluff between D-3 and E-1 by 09:00, on the high ground by 10:00; short of the
# St-Laurent-Colleville road at dusk [OBH ch. 4, 5]; K Company loses 15 to 20 on the bluff ----
for id, dx, dy in (("i116", -150, 0), ("k116", 0, -100), ("l116", 160, 40), ("m116", 40, 140)):
    top = to_line(off(last(id), 0, 0), -450)
    go(id, "08:20", "09:30" if id != "m116" else "10:00", [top], h=210, moving="column")
    go(id, "11:00", "14:30", [off(MAPIX["bn3_116"], dx, dy + 300), off(MAPIX['bn3_116'], dx, dy)], h=180, moving="line")
lose("k116", "08:30", "09:00", 18)

# ---- Easy Red and Fox Green: G Company climbs west of E-3 and reaches Colleville; the 1st Battalion is at the crest by
# 09:30 and on the highway at 13:00 [OBH ch. 4, 5] ----
G_TOP = to_line(off(TD['g16'], -40, -40), -320)
go("g16", "07:31", "08:30", [G_TOP], h=200, moving="column")
go("g16", "09:30", "12:05", [(1650, -1200), COLLEVILLE_W], h=120); fire("g16", "12:06", "14:00")
go("g16", "20:00", "20:40", [off(MAPIX['bn2_16'], -80, 40)], h=150)
go("spalding", "07:45", "08:45", [to_line(off(last("spalding"), -60, 0), -300)], h=230, moving="column")
go("spalding", "09:00", "09:50", [off(P['wn64'], 80, -170)], h=330); fire("spalding", "09:51", "10:00")
go("spalding", "13:00", "15:00", [(1400, -1400), off(MAPIX['bn2_16'], 100, 120)], h=150)
for id, dx in (("a16", -120), ("b16", 0), ("c16", 120), ("d16", 60)):
    go(id, "08:30", "09:30", [to_line(off(last(id), 0, 0), -330)], h=210, moving="column")
lose("a16", "08:30", "09:30", 48)
go("b16", "11:30", "13:00", [(900, -1250)], h=200); go("c16", "11:30", "13:00", [(1150, -1400)], h=200)
go("a16", "12:00", "13:30", [(1000, -1650)], h=190); go("d16", "12:00", "13:30", [(1250, -1600)], h=190)
go("b16", "18:00", "19:30", [MAPIX['bn1_16a']], h=190); go("c16", "18:00", "19:30", [MAPIX['bn1_16b']], h=190)
go("h16", "09:00", "10:00", [off(G_TOP, 120, -40)], h=200, moving="column"); go("h16", "13:00", "15:00", [off(COLLEVILLE_W, 60, -150)], h=120)
go("h16", "20:00", "20:40", [off(MAPIX['bn2_16'], 90, -50)], h=150)
for id in ("e16", "e116w", "f16", "e116"):
    go(id, "10:30", "11:30", [to_line(off(last(id), 0, 0), -300)], h=210, moving="column")
go("e16", "13:00", "15:00", [off(COLLEVILLE_W, -120, 40)], h=120)
go("cmd16", "09:00", "09:30", [to_line(last("cmd16"), -120)], h=200); go("cmd16", "20:00", "20:35", [(1550, -1500)], h=180)

# ---- 3rd Battalion, 16th: L Company up F-1 against WN 60, which falls at 09:00 with 31 prisoners; the battalion holds
# le Grand Hameau at night with about 100 men [OBH ch. 4; HAR; Map IX] ----
go("l16", "07:45", "08:45", [to_line(off(P['wn60'], 150, 150), -40)], h=230, moving="column"); fire("l16", "08:46", "09:00")
go("l16", "10:00", "12:30", [(3200, -1900)], h=180); go("l16", "18:00", "21:00", [off(P['hameau'], -80, 60)], h=120)
lose("l16", "12:30", "21:00", 25)
for id, dx in (("k16", -100), ("m16", 0), ("i16", 110)):
    go(id, "09:10", "10:10", [to_line(off(last(id), 0, 0), -300)], h=200, moving="column")
    go(id, "11:00", "13:00", [off(MAPIX['cabourg_n'], dx, 40 if dx else -60)], h=170)

# ---- the engineers, the guns and the follow-up regiments ----
land("eng149", "09:00", off(P['ruquet'], 150, 60), craft=4); cross("eng149", "09:01", "09:20")
go("eng149", "12:00", "13:00", E1[:5], h=200, moving="column")
land("eng336", "14:30", off(P['ruquet'], 300, 20), craft=4); cross("eng336", "14:31", "14:50")
move("eng336", "15:00", along(SHINGLE, last("eng336"), F1[0]) + [F1[0]], h=100, kmh=1.6)
land("eng121", "17:00", off(BOUNDS[0], 200, -110), craft=4); cross("eng121", "17:01", "17:25")
move("eng121", "17:30", along(SEA_WALL, last("eng121"), D1[0])[1:] + D1 + [MAPIX['eng121']], h=200, kmh=3)
for id, p, t in (("fa7", (1150, -330), "15:30"), ("fa62", (2250, -780), "15:00"), ("fa111", (1350, -380), "15:00"), ("fa58", (1500, -420), "16:30")):
    land(id, t, p, craft=0); cross(id, plus(t, 1), plus(t, 25), w=-70)
fire("fa7", "16:15", "18:00"); fire("fa62", "17:00", "19:00")
move("fa58", "18:00", along(SHINGLE, last("fa58"), E1[0]) + E1 + [(250, -950)], h=200, kmh=5); fire("fa58", "19:30", "21:30")
# 2nd Battalion, 18th, lands shortly after 10:00, is off the beach before noon and at Colleville at 15:00 [OBH ch. 4, 5]
land("r18_2", "10:15", off(P['ruquet'], 200, 30), craft=6); cross("r18_2", "10:16", "10:30")
go("r18_2", "10:45", "11:50", [to_line(off(last("r18_2"), 100, 0), -400)], h=200); go("r18_2", "13:30", "15:00", [(1350, -1500), (1500, -2350)], h=150)
go("r18_2", "18:00", "20:00", [MAPIX['bn2_18']], h=150)
# the 115th lands together on Easy Red near E-1 just before noon and is inland by nearly 14:00; 2/115 fights in
# St-Laurent till dusk; 3/115 is on a strongpoint at D-3 in the evening [OBH ch. 4, 5; G3]
for id, dx in (("r115_1", -150), ("r115_2", 0), ("r115_3", 150)):
    land(id, "11:50", off(P['ruquet'], 280 + dx, -20 - dx / 3), craft=6); cross(id, "11:51", "12:10")
    move(id, "12:30" if id == "r115_2" else "12:50" if id == "r115_1" else "13:10", along(SHINGLE, last(id), E1[0]) + E1, h=230, moving="column", kmh=1.5)
go("r115_2", "14:30", "15:00", [(30, -870)], h=270); fire("r115_2", "15:01", "21:50"); go("r115_2", "22:10", "22:50", [MAPIX['stl_oval']], h=210)
go("r115_1", "15:00", "17:30", [(350, -1350), MAPIX['bn1_115']], h=270)
go("r115_3", "15:30", "17:00", [(450, -600), (200, -330)], h=320); fire("r115_3", "19:00", "21:00"); go("r115_3", "22:00", "23:30", [(600, -900), MAPIX['bn3_115']], h=180)
# the 1st and 3rd Battalions, 18th, land about 13:00; 3/18 is still north of the coast road at 18:00 [OBH ch. 4, 5]
for id, dx in (("r18_1", -130), ("r18_3", 130)):
    land(id, "13:00", off(P['ruquet'], 420 + dx, -60 - dx / 3), craft=6); cross(id, "13:01", "13:20")
    move(id, "13:40" if id == "r18_1" else "14:30", along(SHINGLE, last(id), E1[0]) + E1, h=200, moving="column", kmh=1.2)
go("r18_1", "16:00", "18:00", [(700, -1350), MAPIX['bn1_18']], h=180)
go("r18_3", "16:30", "17:30", [(750, -1150)], h=180); go("r18_3", "19:00", "20:30", [MAPIX['bn3_18']], h=180)
go("r18_1", "23:45", "23:59", [off(MAPIX['bn1_18'], 60, -80)], h=150)  # committed at 23:45 to take over the 1st Battalion, 16th's mission
# the 26th lands at E-3 from 19:30 and is ashore by 21:00; at midnight 2/26 and 3/26 are on the move [G3; Map IX]
for id, t in (("r26_2", "19:40"), ("r26_3", "20:30")):
    land(id, t, off(BOUNDS[5], -40 if id == "r26_2" else 90, 0), craft=6); cross(id, plus(t, 1), plus(t, 20 if id == "r26_2" else 12))
    move(id, plus(t, 25), E3[:6] + [(1500, -1500), MAPIX['bn2_26' if id == "r26_2" else 'bn3_26']], h=270, moving="column", kmh=2.5)

# ---- the Germans: the strongpoints fire on the beach from H-Hour until they fall or are silenced ----
for k in WN:
    appear(k, START, P[k], heading(P[k], to_line(P[k], 300)))
for k, t1 in (("wn74", "09:50"), ("wn73", "13:00"), ("wn72", "13:00"), ("wn71", "13:00"), ("wn70", "13:00"), ("wn66", "12:00"), ("wn68", "12:00"),
              ("wn67", "12:00"), ("wn62", "13:00"), ("wn61", "07:10")):
    fire(k, "06:45" if k == "wn74" else "06:30", t1)
fire("wn66", "19:00", "21:00"); fire("wn68", "19:00", "21:00")
at("wn61", "09:05", state="surrender")  # reported lost [WP]
fire("wn60", "06:30", "09:00", state="surrender"); lose("wn60", "08:46", "09:00", 9)  # 31 prisoners
fire("wn64", "06:30", "10:00", state="surrender"); lose("wn64", "09:51", "10:00", 4)  # 21 prisoners
fire("wn65", "06:30", "11:30", state="surrender"); lose("wn65", "10:00", "11:30", 5)  # 20 prisoners
fire("wn63", "12:05", "14:00"); fire("wn69", "14:30", "21:50")
# the 352nd Artillery Regiment's four batteries behind the bluffs (places not found) [the note]
for id, p in (("art1", (-2600, -3500)), ("art2", (-700, -3900)), ("art3", (1300, -3400)), ("art4", (3200, -3700))):
    appear(id, START, p, 20); fire(id, "06:30", "18:00")
# the 916th's reserve from Formigny into St-Laurent; II./915 against Colleville in the early afternoon; the 352nd's
# engineers in the evening [WP; HAR; INF]
appear("res916", START, off(P['formigny'], 0, 80), 20)
go("res916", "08:30", "09:30", along(FORMIGNY_RD, P['formigny'], (-2100, -1300))[1:] + [(-600, -900)], h=70)
fire("res916", "15:00", "21:50"); go("res916", "22:10", "23:30", [(-1250, -2600)], h=200, moving="retreat")
appear("ii915", "11:00", (4900, -4300), 300, state="column")
go("ii915", "11:01", "12:50", [(3800, -3500), (2700, -2600)], h=290); go("ii915", "13:10", "13:30", [(2250, -2350)], h=290, state="firing", moving="charge")
at("ii915", "14:00", h=120, state="retreat"); go("ii915", "14:01", "15:30", [(3400, -3800)], h=150, state="line", moving="retreat")
appear("eng352", "19:00", (900, -4900), 0, state="column"); go("eng352", "19:01", "20:30", [(900, -3400)], h=0)

# ---- smoke and weather ----
smoke(to_line(off(BOUNDS[3], -200, 60), -150), "06:30", "10:00", rate=8, spread=200)  # grass fires on the bluff west of les Moulins [OBH ch. 3]
LCI91, LCI92 = edge(off(BOUNDS[2], -350, 170), "08:00", 40), edge(off(BOUNDS[2], 330, -100), "08:00", 40)
features += [dict(type="ship", poly=hull(LCI91, inland(LCI91), 48, 7), **{"from": "07:40", "until": "16:30"}),
             dict(type="ship", poly=hull(LCI92, inland(LCI92), 48, 7), **{"from": "07:50", "until": "16:30"})]
smoke(LCI91, "08:00", "16:30", rate=6, spread=40); smoke(LCI92, "08:00", "16:30", rate=6, spread=40)  # still burning at 16:00
smoke(P['wn72'], "12:00", "13:00", rate=10, spread=120)  # naval fire on the Vierville strongpoint [OBH ch. 5]
TINTS = [dict(color="rgba(196,200,206,0.28)", **{"from": START, "until": "07:30"})]  # a slight morning mist under partial overcast

# ---- strengths: each unit's losses fall evenly over their span ----
def pose(id, t):  # where a unit is at time t between its keys
    ks = KEYS[id]; a = max((k for k in ks if sec(k["t"]) <= sec(t)), key=lambda k: sec(k["t"])); b = next((k for k in ks if sec(k["t"]) > sec(t)), None)
    if b is None: return (a["x"], a["y"])
    f = (sec(t) - sec(a["t"])) / (sec(b["t"]) - sec(a["t"])); return (a["x"] + f * (b["x"] - a["x"]), a["y"] + f * (b["y"] - a["y"]))
def state_at(id, t): return next((k["state"] for k in reversed(KEYS[id]) if sec(k["t"]) <= sec(t) and "state" in k), None)
def curve(pts, base):
    def f(s):
        if s < pts[0][0]: return base
        on = [(a, b) for a, b in zip(pts, pts[1:]) if a[0] <= s <= b[0]]
        if not on: return pts[-1][1]
        (s0, v0), (s1, v1) = on[-1]
        return v1 if s1 == s0 else round(v0 + (s - s0) / (s1 - s0) * (v1 - v0))
    return f
for id in KEYS: KEYS[id].sort(key=lambda k: sec(k["t"]))
for id, spans in LOSS.items():
    spans = sorted(spans, key=lambda s: sec(s[0])); cur, pts = BASE[id][6], []
    for t0, t1, n in spans:
        assert state_at(id, t0) not in (None, "hidden") and state_at(id, t1) not in (None, "hidden"), (id, t0, t1, "losses while off the map")
        pts += [(sec(t0), cur), (sec(t1), cur - n)]; cur -= n
    assert cur >= 0, (id, cur)
    s_at = curve(pts, BASE[id][6]); have = {k["t"] for k in KEYS[id]}
    for s, _ in pts:
        t = fmt(s)
        if t not in have: KEYS[id].append(K(t, pose(id, t))); have.add(t)
    KEYS[id].sort(key=lambda k: sec(k["t"]))
    for k in KEYS[id]: k["strength"] = s_at(sec(k["t"]))
def strength(id, t): return next((k["strength"] for k in reversed(KEYS[id]) if sec(k["t"]) <= sec(t) and "strength" in k), BASE[id][6])
# The figures the note gives
assert strength("a116", "07:00") == 62, "A/116: up to two-thirds lost"
assert strength("c116", "08:00") == 180, "C/116: five or six casualties"
assert strength("e16", "08:00") == 50 and strength("g16", "08:00") == 123 and strength("k16", "08:00") == 133, "E, G and K/16: 105, 63 and 53"
assert strength("l16", "08:30") == 125 and strength("l16", "23:00") == 100, "L/16 reduced to 125; about 100 at le Grand Hameau"
assert strength("rgr2c", "07:10") == 29 and strength("rgr2a", "07:45") == 35 and strength("rgr2b", "07:45") == 27, "the Rangers who crossed"
assert strength("t741dd", "06:30") == 5 and strength("t743b", "07:00") == 8, "five DD tanks ashore; eight of B/743"
assert strength("wn60", "09:00") == 31 and strength("wn64", "10:00") == 21 and strength("wn65", "11:30") == 20, "the prisoners"
assert round(strength("setf116", "07:30") / 492, 2) == 0.59, "the engineers' 41%"
assert set(KEYS) == set(BASE), set(KEYS) ^ set(BASE)
for id in KEYS:
    if carried(id, "state") != "hidden" and sec(KEYS[id][-1]["t"]) < sec(END): KEYS[id].append(K(END, last(id)))

# ---- assemble and check ----
# The land check knows the tide: a unit may stand on the flat while the sea is below it, or wade up to WADE metres into
# it at the water's edge. The destroyers, and the DD tanks until they touch down, must be on the water.
TOP = {"infantry": 6, "artillery": 6, "armor": 30, "afloat": 45}  # km/h, the fastest any leg may go
units = []
for id, side, short, name, commander, type, strength0, extra in OOB:
    ks, state, h = KEYS[id], None, None
    for a, b in zip(ks, ks[1:]):
        state, h = a.get("state", state), a.get("h", h)
        assert sec(b["t"]) > sec(a["t"]), (id, a["t"], b["t"])
        if state == "hidden": continue
        moved = (a["x"], a["y"]) != (b["x"], b["y"])
        assert moved or b.get("h", h) == h or "strength" in b or sec(b["t"]) - sec(a["t"]) <= 600, (id, a["t"], b["t"], "a slow turn in place holds the time-lapse")
        assert not (moved and sec(b["t"]) - sec(a["t"]) > 3 * 3600), (id, a["t"], b["t"], "a march leg over three hours")
        kmh = math.dist((a["x"], a["y"]), (b["x"], b["y"])) / (sec(b["t"]) - sec(a["t"])) * 3.6
        afloat = id in AFLOAT and sec(a["t"]) < sec(AFLOAT[id])
        assert kmh <= TOP["afloat" if afloat else type], (id, a["t"], b["t"], f"{kmh:.1f} km/h")
        for s in range(sec(a["t"]), sec(b["t"]) + 1, 60):
            f = (s - sec(a["t"])) / (sec(b["t"]) - sec(a["t"])); q = (a["x"] + f * (b["x"] - a["x"]), a["y"] + f * (b["y"] - a["y"]))
            if id in AFLOAT and s <= sec(AFLOAT[id]): assert not dry(q, s), (id, fmt(s), q, "aground")
            else: assert dry(q, s, WADE), (id, fmt(s), q, f"{seaward(q) - waterline(s):.0f} m out in the water")
    for k in ks: assert max(abs(k["x"]), abs(k["y"])) < HALF_EXTENT, (id, k["t"], "off the map")
    units.append(dict(id=id, side=side, name=name, short=short, commander=commander, type=type, strength=strength0, keys=ks, **extra))
for f in features:
    if "at" in f and f.get("type") != "smoke":
        t_last = f.get("until", END)
        assert max(map(abs, f["at"])) < HALF_EXTENT - 100 and dry(f["at"], sec(t_last) - 60), (f.get("name"), f["at"], "a label off the map or under the water")

# ---- chapters: (time, title, text, camera centre, metres across, playback speed, when) ----
# `when` holds the clock time the sources record, on the GMT+2 clock the Allies' "B" zone and German summer time share.
CHAPTERS = [
    ("05:30", "Low water", "6 June 1944. V Corps is to land the 1st Infantry Division, with the 29th Division's 116th Infantry and the Rangers, on Omaha Beach: eight sectors from Charlie to Fox Red, under bluffs 100 to 170 feet high cut by five draws. Low water was at 05:25, and the tide's range today is 18 feet. Bare on 300 yards of firm sand stand the obstacles: Element C gates about 250 yards out, log ramps behind them, hedgehogs 130 yards from shore. Allied intelligence expects about a reinforced battalion in the strongpoints, WN 60 to WN 74; the 352nd Infantry Division's 916th Grenadier Regiment holds them. The Ancon, Force O's headquarters ship, anchored 23,000 yards out at 02:51.", [300, 200], 7500, 60, "5:30 AM"),
    ("05:40", "The DD tanks", "At H-50 minutes, 6,000 yards off shore, the 741st Tank Battalion launches the 32 swimming DD tanks of its B and C Companies for Easy Red and Fox Green. A north-west wind of 10 to 18 knots raises waves of 3 to 4 feet, up to 6. 27 founder on the run-in; two swim ashore, and three more are beached from an LCT.", [3800, 3300], 3500, 30, "5:40 AM"),
    ("05:50", "The bombardment", "From 05:50, H-40, the fleet fires about 600 heavy rounds on Pointe du Hoc and the D-3 strongpoints; at 05:37 guns near Port-en-Bessin put ten rounds close to the destroyer Emmons. From 05:55 to 06:14, 329 of 446 Liberators bomb about three miles inland and miss the beach. Sunrise is at 05:58, under a partial overcast and a slight mist.", [800, 1400], 7000, 30, "5:50 AM"),
    ("06:30", "H-Hour", "The 743rd Tank Battalion's B and C Companies came in on their LCTs at H-5 on Dog Green and Dog White. At 06:30 its A Company lands with the tank dozers on Easy Green and Dog Red, and the 741st's A Company astride Easy Red and Fox Green. From 06:31 the first wave, eight infantry companies, touches down; the division's report has it landed at 06:35. The current runs east at nearly 2.7 knots, and practically all the craft that land in the wrong place land east of their targets. The engineers' sixteen assault teams follow at H+3 to H+8; only five hit their sectors.", [600, 300], 6500, 30, "6:30 AM"),
    ("06:36", "Dog Green", "A Company, 116th Infantry, comes in on Dog Green in front of the Vierville draw. Its craft ground in water 4 to 6 feet deep, 30 yards short of the outer obstacles, and the company is out of action within fifteen minutes: up to two-thirds of it lost. Some men on the beach will reach the wall by staying at the edge of the water and going up the beach with the tide. WN 72's 8.8 cm casemate at the mouth of D-1 and WN 73 above it fire down the sand.", [-1650, 1150], 1800, 20, "6:36 AM"),
    ("06:45", "Charlie", "C Company of the 2nd Rangers lands at H+15 on Charlie, to the right of the Vierville draw. Of its 64 men 35 are lost, and about 30 cross the sand. They go up the cliff 300 yards west, and all are up by 07:30. Goranson's Rangers fight on the cliff top into the afternoon.", [-2250, 1750], 1600, 20, "6:45 AM"),
    ("07:00", "The tide in the obstacles", "The tide is flowing into the obstacle belt; in the next hour it will rise eight feet and be through it. The engineers have blown six complete gaps and three partial ones, four complete on Easy Red and two in the 116th's half, and only one is marked. They lose 41% of their men, most in the first half hour; Support Team F has 15 killed. At 06:55 USS Chase heard that the entire first wave had floundered. The second waves come in: B Company, 116th, scattered over a mile, the 2nd Battalion's headquarters on Dog Red, G Company, 16th, on Easy Red, K Company on Fox Green and L Company on Fox Red.", [700, 150], 5500, 30, "7:00 AM"),
    ("07:10", "Pointe du Hoc", "Beyond the map's west edge D, E and F Companies of the 2nd Ranger Battalion land under Pointe du Hoc at 07:10, 40 minutes late, and are all up the cliff by 07:40. The rest of the Ranger force, waiting offshore, has heard nothing; 15 minutes past its 07:00 time limit it turns for Dog Green. On Dog White C Company, 116th, lands 1,000 yards east of the Vierville exit and re-forms under the sea wall with five or six casualties.", [-1600, 1100], 4000, 30, "7:10 AM"),
    ("07:30", "Cota on Dog White", "By 07:30 assault units line the whole of the 116th's front. The command parties land, Col. Canham and Brig. Gen. Cota near les Moulins. The 116th's 3rd Battalion comes in 5 to 10 minutes late east of les Moulins, and the 16th's 1st Battalion on time between E-1 and E-3. About 07:35 A and B Companies of the 2nd Rangers land on Dog Green: about 35 of 65 and 27 reach the sea wall. At 07:35 the German 726th Regiment reports 100 to 200 Americans through its front.", [-600, 600], 2600, 30, "7:30 AM"),
    ("08:00", "The beach stopped", "LCI 91 and 92 are hit off Dog White and Dog Red; they are still burning at 16:00. The 5th Rangers reached the sea wall just before 08:00, losing eight men, and cross the road about 08:10. German observers on the bluff judge the landing stopped. The destroyers begin to engage targets of their own. I Company, 16th, carried almost as far east as Port-en-Bessin, lands on Fox Green. Col. Taylor lands at 08:15 with the second section of the 16th's command group; the first lost its executive officer and 35 men on the flat. At 08:30 the 7th Naval Beach Battalion suspends all vehicle landings.", [-350, 500], 2400, 30, "8:00 AM"),
    ("08:30", "Up the bluff", "Between 08:00 and 09:00 upwards of 600 men go off Dog White on a front of less than 300 yards: C Company, 116th, which Cota led up from 07:50, the 5th Rangers, and G Company's remnants, who reached Dog White about 08:30. A and B Companies of the 2nd Rangers fight up to the top at Dog Green. East of les Moulins the 116th's 3rd Battalion works up between D-3 and E-1, K Company losing 15 to 20 men. On Easy Red G Company, 16th, is on the bluff top west of E-3.", [-200, 300], 4500, 30, "8:30 AM"),
    ("09:00", "F-1 falls", "About 09:00 L Company, 16th, down to 125 men, subdues WN 60 at F-1 and takes 31 prisoners. The 3rd Battalion subdues the draw north-east of Colleville. WN 61 on Fox Green, its 8.8 cm gun knocked out by a DD tank about 07:10, is reported lost at 09:05. At 09:30 the 16th's 1st Battalion is at the crest.", [2800, -1100], 2400, 60, "9:00 AM"),
    ("10:00", "Spalding", "Mid-morning Lt. John Spalding's section of E Company, 16th, comes on WN 64 above E-1 from the rear and takes 21 prisoners without loss. About 10:00 C Company of the 149th Engineers bulldozes the first gap through the dunes just east of E-1, and the 18th's 2nd Battalion begins to land. Most of the 116th's 3rd Battalion is on the high ground. At 09:50 the destroyer McCook destroyed a gun position in WN 74 at Pointe de la Percée.", [1200, -500], 1800, 60, "about 10 AM"),
    ("10:30", "The destroyers close in", "Between 10:00 and 11:00 two destroyers close to within 1,000 yards and fire on the strongpoints; which two is not recorded, and they are drawn here as Carmick and Doyle. On the plateau above Dog White Cota helps start the units moving inland, and with the leading men of the 116th and the Rangers he enters Vierville before 11:00.", [300, 900], 6000, 60, "about 10:30 AM"),
    ("11:00", "High water", "The tide stands at the shingle. Vierville is clear by 11:00. Col. Taylor orders all tanks to E-3; three get there, and two are knocked out going up the draw. WN 62 above E-3, the largest strongpoint, is still firing. The division's report has the 18th's 2nd Battalion landed at 11:10.", [1700, -700], 2600, 60, "11:00 AM"),
    ("11:30", "E-1 opens", "About 11:30 the last defences in front of E-1 surrender, a pillbox of WN 65 with 20 prisoners. The mines are cleared within half an hour and E-1 becomes the main exit; the 18th's 2nd Battalion is off the beach before noon. Just before noon the 115th's three battalions land together on Easy Red near E-1, not on Dog Red and Easy Green as planned. West of Vierville C Company, 116th, and B Company of the 5th Rangers set off along the coast road toward Pointe du Hoc.", [900, -450], 2200, 60, "11:30 AM"),
    ("12:30", "Colleville", "A little after noon a section of G Company, 16th, gets into the west edge of Colleville and is held just beyond the church; the division logs the 2nd Battalion in the town at 12:33. For two hours G Company fights on the defensive there, the nearest approach to a counter-attack in strength. II./915, Kampfgruppe Meyer's battalion split off to the 916th, comes in with an anti-tank company near Colleville in the early afternoon and is stopped. At noon LXXXIV Corps reported the landings completely smashed.", [2300, -2300], 2800, 60, "12:30 PM"),
    ("15:00", "The 18th at Colleville", "At 15:00 the 18th's 2nd Battalion reaches Colleville, passing west of G Company. The 1st and 3rd Battalions landed about 13:00. Vehicles have been moving off the beach again since 14:00, and jam on E-1 against St-Laurent, where the 115th, inland by nearly 14:00, is fighting for the village. The Vierville strongpoint was silenced by 13:00 after an hour of naval fire. At 13:35 the 352nd Division reported the assault hurled back into the sea, with fighting only at Colleville; at 13:41 the Navy reported Dog Green, White and Red clear. The 336th Engineers set out for F-1.", [900, -1300], 4500, 120, "3:00 PM"),
    ("17:00", "The exits open", "D-1 is open to Vierville. All the 741st's remaining tanks are ordered inland by E-1, and four attack St-Laurent before dark. The 336th Engineers reach F-1. The main Ranger force comes up on the coast road west of Vierville; at 16:35 the two Ranger battalions reported no opposition in their sector. The 7th Field Artillery fired its first mission at 16:15, four of the 58th Armored Field Artillery's guns were ashore by 16:55, and B Company, 745th Tank Battalion, landed on Fox Green at 16:30. The ebb has bared the obstacles again, and by evening the engineers have 13 gaps opened and marked.", [100, -200], 6500, 120, "5:00 PM"),
    ("19:30", "The 26th lands", "From 19:30 the 26th Infantry comes in at E-3, and it is ashore by 21:00; at 20:10 it is ordered to move a battalion behind the 16th to clear toward St-Laurent. Maj. Gen. Huebner, the division's commander, landed on Easy Red at 19:00. B Company, 745th, is on the high ground by F-1 at 20:00. In St-Laurent the 115th's 2nd Battalion fights on until dusk, when naval fire stops its attack and it withdraws; its 3rd Battalion is on a strongpoint at the D-3 exit.", [900, -1000], 5000, 120, "7:30 PM"),
    ("22:05", "Night", "Sunset is at 22:05, and the Moon is full. At midnight the beachhead is hardly more than a mile and a half deep at Colleville: the Rangers and C Company, 116th, west of Vierville; the 116th's 1st Battalion near Vaumicel; the 115th in and south of St-Laurent; the 18th and the 26th between St-Laurent and Colleville; the 16th's 2nd Battalion at Colleville's west end, and its 3rd at le Grand Hameau with about 100 men. Some 34,000 men are ashore. V Corps lost between two and three thousand killed, wounded and missing, the 16th and 116th about 1,000 each; the 352nd Division about 1,200. At 23:45 the 18th's 1st Battalion is committed to take over the mission of the 16th's 1st.", [0, -900], 7500, 300, "10:05 PM"),
]
events = [dict(t=t, title=a, text=b, at=list(at_), view=v, speed=s, **({"when": w} if w else {})) for t, a, b, at_, v, s, w in CHAPTERS]
for e in events:  # without `when` the card speaks the nearest hour (app.js chapterWhen), so it must be near the frame's clock
    s = sec(e["t"]); hh = [n % 12 or 12 for n in (s // 3600, s // 3600 + 1)]; num = re.search(r"\d+", e.get("when", ""))
    assert not num or int(num[0]) in hh, (e["t"], e["when"], "the card's hour is not the frame's")
    assert "when" in e or abs(s - math.floor(s / 3600 + 0.5) * 3600) <= 15 * 60, (e["t"], e["title"], "give it a when")
    assert e["speed"] in (1, 2, 5, 10, 20, 30, 60, 120, 300, 600, 1800, 3600, 7200), (e["title"], e["speed"], "not a speed the menu offers (sim.js SPEEDS)")
    assert max(map(abs, e["at"])) + e["view"] / 4 < HALF_EXTENT + 1000, (e["title"], "a frame off the map")
assert [sec(e["t"]) for e in events] == sorted(sec(e["t"]) for e in events)

OUTCOME = {"result": "V Corps ashore on Omaha Beach, the beachhead nowhere more than a mile and a half deep at nightfall", "losses": [
    ["us", "About 3,000 killed, wounded and missing in V Corps on 6 June by Omaha Beachhead, the 16th and 116th Infantry about 1,000 each; about 2,000 by Harrison, whose footnote gives 2,374 from the V Corps history. A Company, 116th, lost up to two-thirds; 27 of the 741st's 32 swimming tanks went down at sea; 26 guns were lost, and about 50 landing craft and 10 larger vessels."],
    ["german", "About 1,200 killed, wounded and missing in the 352nd Infantry Division, nearly a fifth of its combat effectives (Harrison). Prisoners taken at the strongpoints: 31 at WN 60, 21 at WN 64, 20 at E-1."]],
    "note": "Off the map, the 2nd Rangers held Pointe du Hoc until relieved on 8 June, and the airborne divisions dropped behind Utah Beach in the early hours; both are battles of their own. Clock times are GMT+2, the Allies' double summer time."}
SOURCES = [
    "<i>Omaha Beachhead (6 June to 13 June 1944)</i>, American Forces in Action (Historical Division, War Department, 1945), <a href='https://www.ibiblio.org/hyperwar/USA/USA-A-Omaha/index.html' target='_blank'>chapters 2 to 5</a> and Maps V to IX: the plan, the beach and its obstacles, the sector landings and their times, the climbs, the strongpoints' falls and the positions at midnight.",
    "Gordon A. Harrison, <a href='https://www.ibiblio.org/hyperwar/USA/USA-E-XChannel/USA-E-XChannel-8.html' target='_blank'><i>Cross-Channel Attack</i></a> (US Army in World War II, 1951), chapters VIII and IX: Vierville clear at 11:00, the 3rd Battalion, 16th, at le Grand Hameau, Kampfgruppe Meyer and the casualties.",
    "1st Infantry Division G-3 after-action report, June 1944, <a href='https://www.dday-overlord.com/?p=140717' target='_blank'>transcribed at dday-overlord.com</a>: the division's timed entries. COMINCH P-006, <a href='https://www.ibiblio.org/hyperwar/USN/rep/Normandy/Cominch/Neptune4.html' target='_blank'><i>Amphibious Operations: Invasion of Northern France</i></a>, chapter IV. David F. Winkler, <a href='https://navyhistory.org/2019/06/destroyers-at-normandy/' target='_blank'>Destroyers at Normandy</a> (Naval Historical Foundation, 2019), after Kirkland: which destroyer supported which division.",
    "The tide: Donald W. Olson, <a href='https://skyandtelescope.org/astronomy-news/astronomy-d-day-sun-moon-tides/' target='_blank'>Astronomy and D-Day</a>, <i>Sky &amp; Telescope</i> (2019), and Olson and Doescher, <i>Physics Today</i> 65(1), 2012. No tide table or harmonic constants were read: the curve is fitted to Omaha Beachhead's low water at 05:25, high water at 11:00, 18-foot range and eight feet between 07:00 and 08:00, and to Olson's computed rates; the afternoon low at 17:50 and the evening flood are inferred.",
    "Wikipedia, 'Omaha Beach' and '916th Grenadier Regiment (Wehrmacht)' (read 7 November 2026), for the German side, WN 61's and WN 74's times and the 34,000 ashore; the Jewish Virtual Library's copy of omaha-beach.org's strongpoint list for each Widerstandsnest's weapons.",
    "Places: OpenStreetMap contributors (ODbL) for the strongpoints, villages, churches and memorials. WN 63 to WN 71 are placed from Maps V and VI or a description, within 200 to 300 m. The sector boundaries and each company's touchdown are read from Maps V and VI, within 100 to 150 m; the midnight positions from Map IX, within 400 m. Sunrise 05:59 and sunset 22:05 from the NOAA formulae.",
    "Terrain: " + T["source"] + ", 30 m. A surface model, which sets the sea to 0: its coast is the high-water line of 1944, and the tidal flat is built seaward of it as a straight 1:50 slope 274 m wide (300 yards). The sea is drawn every five to thirty minutes at the tide's height on that slope.",
    "Placed by inference, not from the sources: the obstacle rows' runs and gaps, drawn as rows of posts; the roads, through the villages and up the DEM's valley floors; the bocage, drawn as fields without its hedgerows; the shingle bank and the sea wall along the high-water line; the strengths of the boat sections, the follow-up battalions, the engineers, the guns and every German unit; the destroyers' stations, and Carmick and Doyle as the two that closed in; the craft drawn at each landing; the 352nd's batteries, placed toward the map's south edge; the routes between recorded places; the 916th's reserve marching from Formigny into St-Laurent; II./915's road in from the south-east; when WN 62, WN 66, WN 68 and the D-1 strongpoints stopped firing, which is not recorded; where the follow-up battalions landed beyond the beach the sources name; and L Company, 16th, standing for the 3rd Battalion's 100 men at le Grand Hameau. The tanks Taylor sent to E-3 are not drawn moving there.",
]
battle = dict(
    id="omaha-beach", name="Omaha Beach", date="1944-06-06", dateText="6 June 1944", place="Omaha Beach, Calvados, Normandy, France",
    origin=dict(lat=LAT0, lon=LON0), extent=2 * HALF_EXTENT, start=START, end=END, sunrise="05:59", sunset="22:05", speed=60, lapse=600, menPerDot=10,
    water=WATER, terrainExaggeration=1.5, contourInterval=5, trees=dict(density=0.0002, clear=TREES_CLEAR), fields=FIELDS, wind=dict(x=0.5, y=-0.4),
    view=dict(x=0, y=0, width=2 * HALF_EXTENT),
    sides=dict(us=dict(name="Americans (V Corps: the 1st Infantry Division, with the 29th's 116th and 115th Infantry and the Rangers)", color="#3a5f9e", light="#7d9bd0", dark="#1d3561"),
               german=dict(name="Germans (352nd Infantry Division, Kraiss)", color="#b8322a", light="#de5d50", dark="#5c1712")),
    features=features, units=units, events=events, tints=TINTS, outcome=OUTCOME, sources=SOURCES,
)
json.dump(battle, open(HERE + "battle.json", "w"), indent=1, ensure_ascii=False)
print(len(units), "units,", len(events), "chapters,", len(TIDE_STEPS), "tide steps,", len(OBSTACLES), "obstacle posts,", len(changed), "flat cells")
# Which units each chapter's frame holds at its moment, so a caption never names a unit the camera leaves out.
for e in events:
    r = e["view"] / 2; inside = [u["id"] for u in units if state_at(u["id"], e["t"]) not in (None, "hidden") and abs(pose(u["id"], e["t"])[0] - e["at"][0]) <= r and abs(pose(u["id"], e["t"])[1] - e["at"][1]) <= r]
    print(f"{e['t']} {e['title']}: {' '.join(inside)}")
