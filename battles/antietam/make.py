# Builds battles/antietam/battle.json. Run from the repo root: python3 battles/antietam/make.py
# Local metres from 39.4630N 77.7450W (x east, y north). The 9 km square holds Joseph Poffenberger's farm and the I Corps
# gun line in the north, the Cornfield, the three woods and the Dunker Church, the Sunken Road, Sharpsburg, the three
# bridges over Antietam Creek, Snavely's Ford, the Pry House east of the creek and Boteler's Ford on the Potomac in the
# south-west, where McLaws, Anderson and A. P. Hill crossed and Lee's army recrossed. Every place is kept in latitude and
# longitude below and converted once. Farms, the church, bridges, monuments and death sites are OpenStreetMap points; the
# roads, the creek and the Sunken Road are OpenStreetMap ways on their 1862 lines. Pry's and Snavely's fords are placed
# from distances and the creek's bends, within 200 to 300 m, and labelled "about here". Boteler's Ford keeps the note's
# longitude but sits on the Potomac as the DEM draws it: the note's latitude falls 800 m south of the river, on the
# Virginia shore. The woods are the
# research note's boxes, drawn from the anchors; the Carman-Cope base sheet that holds the 1862 outlines was not read.
import json, math, re, datetime as dt
HERE = "battles/antietam/"
LAT0, LON0 = 39.4630, -77.7450
KX, KY = 111320 * math.cos(math.radians(LAT0)), 111320  # tools/fetch_terrain.py's metres per degree
def M(lat, lon): return (round((lon - LON0) * KX), round((lat - LAT0) * KY))

# ---- terrain ----
T = json.load(open(HERE + "terrain.json"))
COLS, SP = T["cols"], T["spacing"]; HALF = COLS * SP / 2
def z(x, y):
    c, r = int((x + HALF) / SP), int((HALF - y) / SP)
    return T["z"][r * COLS + c] if 0 <= c < COLS and 0 <= r < COLS else 999
WATER = 89.5  # the Potomac's surface in the DEM falls from about 89 m at the north edge to 84 m at the south
def wet(p): return z(*p) <= WATER
def summit(p, r=400):  # the DEM's highest cell within r metres; GNIS hill points sit off the crest
    return max(((z(p[0] + dx, p[1] + dy), (p[0] + dx, p[1] + dy)) for dx in range(-r, r + 1, 25) for dy in range(-r, r + 1, 25) if dx * dx + dy * dy <= r * r))[1]

# ---- geography: places ----
PLACES = {
    # OpenStreetMap buildings and points (about 15 m)
    'church': (39.47537, -77.74679), 'miller': (39.48435, -77.74936), 'j_poffenberger': (39.49001, -77.74884),
    'a_poffenberger': (39.47719, -77.75232), 'mumma': (39.47720, -77.74120), 'mumma_cemetery': (39.47849, -77.74150),
    'roulette': (39.47541, -77.73796), 'piper': (39.46472, -77.74187), 'piper_corn': (39.47013, -77.74002),
    'otto': (39.45411, -77.73715), 'corn40': (39.44732, -77.73965), 'newcomer': (39.46472, -77.72735), 'pry': (39.47605, -77.71418),
    'burnside_bridge': (39.45053, -77.73185), 'middle_bridge': (39.46529, -77.72550), 'upper_bridge': (39.48791, -77.71385),
    'sharpsburg': (39.45820, -77.74866), 'crossroads': (39.45819, -77.74607), 'cemetery_hill': (39.45944, -77.74149),
    'tower': (39.46951, -77.73608), 'sunken_w': (39.47095, -77.74534), 'sunken_roulette': (39.47130, -77.74147),
    'corn_w': (39.48078, -77.74841), 'corn_e': (39.48131, -77.74152), 'smoketown_mansfield': (39.48424, -77.74185),
    'mansfield_falls': (39.48314, -77.74089), 'starke_falls': (39.47837, -77.74877), 'philadelphia_bde': (39.47846, -77.75149),
    'early_marker': (39.47741, -77.75163), 'mclaws_marker': (39.47508, -77.75082), 'gb_anderson_marker': (39.47046, -77.73840),
    'rodman_falls': (39.45239, -77.74370), 'branch_falls': (39.44795, -77.74131), 'hf_branch': (39.44619, -77.74647),
    'sawmill_mid': (39.43838, -77.75560), 'porterstown': (39.46593, -77.71305), 'keedysville': (39.48627, -77.70054),
    # GNIS hill points, up to 300 m off the crest; the label goes on the DEM's summit near each
    'nicodemus_gnis': (39.48510, -77.75860), 'hauser_gnis': (39.47510, -77.75833), 'red_hill_gnis': (39.45316, -77.70027),
    # placed from distances and the creek's bends (200 to 300 m)
    'prys_ford': (39.4760, -77.7170), 'snavely_ford': (39.4414, -77.7284), 'boteler_ford': (39.4375, -77.7807),
}
P = {k: M(*v) for k, v in PLACES.items()}
NICODEMUS, HAUSER, RED_HILL = summit(P['nicodemus_gnis'], 300), summit(P['hauser_gnis'], 300), summit(P['red_hill_gnis'], 300)

# ---- geography: lines (OpenStreetMap ways, simplified to 8 m; the creek to 15 m) ----
LINES_LL = {
    'hagerstown_pike': [(39.45897, -77.74607), (39.46039, -77.74666), (39.46301, -77.7455), (39.46924, -77.74513), (39.47067, -77.74546), (39.47177, -77.74634), (39.47239, -77.74558), (39.47262, -77.74562), (39.47851, -77.7476), (39.48711, -77.75078), (39.48877, -77.751), (39.49632, -77.74993), (39.50315, -77.74835)],
    'boonsboro_pike': [(39.4932, -77.69174), (39.49157, -77.69854), (39.49094, -77.7001), (39.49039, -77.70088), (39.48908, -77.70208), (39.4837, -77.70499), (39.46553, -77.7252), (39.46475, -77.72625), (39.46413, -77.72777), (39.46198, -77.73747), (39.46145, -77.73911), (39.45965, -77.74356), (39.45824, -77.74874)],
    'shepherdstown_rd': [(39.45824, -77.74874), (39.45343, -77.76606), (39.45077, -77.76954), (39.44547, -77.77535), (39.44285, -77.77852), (39.44162, -77.78014), (39.44069, -77.78192), (39.43916, -77.78578), (39.43865, -77.78765), (39.4385, -77.78985), (39.43871, -77.79215), (39.4387, -77.79357), (39.43854, -77.79485), (39.43808, -77.79657)],
    'smoketown_rd': [(39.47582, -77.74665), (39.48093, -77.74149), (39.48383, -77.74194), (39.48872, -77.74086), (39.49212, -77.74096), (39.49232, -77.74086), (39.49618, -77.7364), (39.49652, -77.73623), (39.49732, -77.73616), (39.50257, -77.73637), (39.50281, -77.73627), (39.50412, -77.7335), (39.50428, -77.73347)],
    'keedysville_rd': [(39.50428, -77.73347), (39.50394, -77.72993), (39.504, -77.72855), (39.50387, -77.72695), (39.50118, -77.72256), (39.49729, -77.71956), (39.49665, -77.71873), (39.49619, -77.71735), (39.49484, -77.71604), (39.4922, -77.71547), (39.48981, -77.71394), (39.48808, -77.71415), (39.48763, -77.7135), (39.48556, -77.71448), (39.48542, -77.71441), (39.4843, -77.71092), (39.4838, -77.71039), (39.48295, -77.70894), (39.4824, -77.7065), (39.48226, -77.70636), (39.48164, -77.7063), (39.48132, -77.7058), (39.48265, -77.70745), (39.4829, -77.70744), (39.48364, -77.70783), (39.48381, -77.70839)],
    'rohrbach_rd': [(39.4384, -77.71966), (39.4407, -77.72037), (39.44189, -77.72037), (39.44548, -77.72345), (39.44575, -77.72473), (39.44607, -77.7253), (39.44638, -77.72561), (39.44743, -77.72615), (39.44836, -77.72739), (39.44997, -77.72895), (39.45079, -77.72919), (39.45255, -77.7289), (39.45308, -77.72907), (39.45358, -77.72947), (39.45385, -77.72995), (39.45398, -77.73066), (39.45401, -77.73513), (39.45493, -77.73738), (39.4554, -77.73936), (39.45535, -77.73997), (39.45509, -77.74076), (39.45514, -77.74165), (39.45659, -77.7448)],
    'old_bridge_rd': [(39.45496, -77.73843), (39.45439, -77.73706), (39.45396, -77.73643), (39.4532, -77.73405), (39.4529, -77.73376), (39.45152, -77.73313)],
    'harpers_ferry_rd': [(39.45572, -77.74765), (39.44902, -77.7466), (39.44726, -77.74612), (39.44518, -77.74688), (39.44433, -77.74692), (39.4407, -77.74624), (39.4375, -77.74505), (39.43588, -77.74494), (39.43418, -77.74532), (39.43313, -77.74481), (39.43231, -77.74377), (39.43202, -77.74363), (39.42712, -77.74446), (39.426, -77.74388), (39.42536, -77.74294), (39.42432, -77.74273), (39.4236, -77.74299), (39.42282, -77.74381), (39.42174, -77.74389)],
    'sawmill_rd': [(39.44619, -77.74647), (39.44306, -77.75875), (39.44169, -77.76172), (39.44124, -77.7618), (39.43839, -77.76126), (39.43523, -77.76184), (39.43377, -77.76271), (39.43327, -77.7637), (39.43193, -77.76469), (39.43058, -77.76469)],
    'mumma_lane': [(39.47114, -77.74336), (39.47141, -77.74345), (39.47359, -77.74281), (39.47595, -77.74151), (39.4762, -77.74149), (39.47768, -77.74183), (39.47859, -77.74381)],
    'roulette_lane': [(39.47116, -77.73955), (39.47246, -77.73853), (39.47427, -77.73666), (39.47482, -77.73733), (39.47522, -77.73725), (39.47558, -77.73764), (39.47572, -77.73799)],
    'sunken_w': [(39.47076, -77.7401), (39.47131, -77.74154), (39.47091, -77.74559)],
    'bloody_lane': [(39.4713, -77.74147), (39.47141, -77.74016), (39.46951, -77.73608)],
    'sunken_s': [(39.47076, -77.7401), (39.46923, -77.73651), (39.46876, -77.73634), (39.46705, -77.73717), (39.46638, -77.73505), (39.46304, -77.73516), (39.46282, -77.73532), (39.46256, -77.73602), (39.46234, -77.73602)],
    'porterstown_rd': [(39.44414, -77.69152), (39.44419, -77.69256), (39.44403, -77.69388), (39.4441, -77.69505), (39.44473, -77.69661), (39.44487, -77.69747), (39.4447, -77.69832), (39.44428, -77.69952), (39.4444, -77.69989), (39.44479, -77.70043), (39.44542, -77.70115), (39.44612, -77.70165), (39.44716, -77.70173), (39.45025, -77.70245), (39.45156, -77.70318), (39.45389, -77.7035), (39.45523, -77.70541), (39.45607, -77.70608), (39.45664, -77.70673), (39.4592, -77.7079), (39.46051, -77.7087), (39.4619, -77.7099), (39.46333, -77.71149), (39.46601, -77.71326), (39.46625, -77.71381), (39.46632, -77.71756), (39.46661, -77.71917), (39.46655, -77.72088), (39.46664, -77.72113), (39.46699, -77.72117)],
    'creek': [(39.50508, -77.70804), (39.50469, -77.70846), (39.50436, -77.70982), (39.50416, -77.71147), (39.50441, -77.71328), (39.50411, -77.71391), (39.50317, -77.7135), (39.50044, -77.70946), (39.4994, -77.70917), (39.49791, -77.70922), (39.49669, -77.70956), (39.49487, -77.71133), (39.49363, -77.71323), (39.4923, -77.71438), (39.49144, -77.71438), (39.48966, -77.71293), (39.48886, -77.71279), (39.48623, -77.71541), (39.48305, -77.71784), (39.48177, -77.7198), (39.4813, -77.72014), (39.48067, -77.72019), (39.47993, -77.7198), (39.47943, -77.71881), (39.47922, -77.71716), (39.47884, -77.71605), (39.47849, -77.71573), (39.47806, -77.71576), (39.47718, -77.71643), (39.47691, -77.7171), (39.47693, -77.71969), (39.4779, -77.72254), (39.47805, -77.72376), (39.4777, -77.72459), (39.47632, -77.7254), (39.47577, -77.72542), (39.47482, -77.72494), (39.47329, -77.72337), (39.47241, -77.72279), (39.47187, -77.72276), (39.47021, -77.72395), (39.46881, -77.72631), (39.46786, -77.72728), (39.46701, -77.72695), (39.4652, -77.72539), (39.46437, -77.72536), (39.45941, -77.72787), (39.45535, -77.73178), (39.45306, -77.73319), (39.45186, -77.73286), (39.4504, -77.73178), (39.44909, -77.72839), (39.44861, -77.72787), (39.44788, -77.72818), (39.448, -77.73032), (39.44768, -77.73092), (39.44732, -77.731), (39.44582, -77.72975), (39.4446, -77.72938), (39.44233, -77.72796), (39.44168, -77.728), (39.44138, -77.72842), (39.44129, -77.72974), (39.44025, -77.73351), (39.4397, -77.73714), (39.43842, -77.7408), (39.43782, -77.74135), (39.43694, -77.74107), (39.43632, -77.74035), (39.43589, -77.73961), (39.43561, -77.7381), (39.43592, -77.73605), (39.43735, -77.73422), (39.43805, -77.73271), (39.43797, -77.73163), (39.43722, -77.73062), (39.43613, -77.7308), (39.43356, -77.73321), (39.42849, -77.734), (39.42614, -77.73509), (39.42495, -77.73488), (39.42366, -77.73417), (39.42271, -77.73218), (39.42198, -77.73162), (39.42082, -77.73294)],
}
L = {k: [M(*p) for p in v] for k, v in LINES_LL.items()}
# The 1862 Hagerstown Pike is MD 65 south of the Sunken Road and north of Miller's, and Dunker Church Road between,
# where MD 65 now bends west round the West Woods: the church stands 25 m west of Dunker Church Road, and the note puts
# the Pike's fence by Starke's death site and the Cornfield's west end on it.
PIKE = L['hagerstown_pike']
SUNKEN = L['sunken_w'][1:][::-1] + L['bloody_lane'][1:]  # from the Pike east to the bend by the tower: Bloody Lane
SUNKEN_S = [P['tower']] + L['sunken_s'][3:]                # the lane on south toward the Boonsboro Pike
BRIDGE_RD = [p for p in L['rohrbach_rd'][::-1] if p[0] <= 565] + L['old_bridge_rd'][1:] + [P['burnside_bridge']]  # Sharpsburg to the bridge by the old road
CREEK = L['creek']

def inside(x, y, poly):
    c = False
    for i in range(len(poly)):
        (xa, ya), (xb, yb) = poly[i], poly[i - 1]
        if (ya > y) != (yb > y) and x < xa + (xb - xa) * (y - ya) / (yb - ya): c = not c
    return c
def near(x, y, line, d):
    for (xa, ya), (xb, yb) in zip(line, line[1:]):
        dx, dy = xb - xa, yb - ya; t = max(0, min(1, ((x - xa) * dx + (y - ya) * dy) / (dx * dx + dy * dy or 1)))
        if math.hypot(x - xa - t * dx, y - ya - t * dy) < d: return True
    return False
def pike_x(y):  # the Pike's x where it crosses the latitude y
    for (xa, ya), (xb, yb) in zip(PIKE, PIKE[1:]):
        if min(ya, yb) <= y <= max(ya, yb) and ya != yb: return xa + (xb - xa) * (y - ya) / (yb - ya)
    raise ValueError(y)

# ---- woods and fields ----
# The three woods are the note's boxes (North Woods y 2500 to 2900 astride the Pike; East Woods x 200 to 600, y 1900 to
# 2400; West Woods x -700 to -150, y 1300 to 2300, west of the Pike), their Pike sides following the road.
WEST_WOODS = [(-700, 2300), (-700, 1300)] + [(round(pike_x(y) - 25), y) for y in range(1300, 2301, 100)]
EAST_WOODS = [(200, 1900), (600, 1900), (600, 2400), (200, 2400)]
NORTH_WOODS = [(-750, 2500), (-250, 2500), (-250, 2900), (-750, 2900)]
WOODS = [WEST_WOODS, EAST_WOODS, NORTH_WOODS]
# Miller's Cornfield is "about 250 yards deep and 400 yards wide" north of Cornfield Avenue, between the Pike and the
# East Woods; Piper's cornfield and the 40-acre cornfield are the park's polygons, drawn here as squares on their centres.
def quad(cx, cy, w, h): return [(cx - w, cy - h), (cx + w, cy - h), (cx + w, cy + h), (cx - w, cy + h)]
CORNFIELD = [(round(pike_x(1980)) + 15, 1980), (300, 2036), (300, 2240), (round(pike_x(2210)) + 15, 2210)]
PIPER_CORN = quad(*P['piper_corn'], 160, 110)
CORN40 = quad(*P['corn40'], 200, 200)
NAMED_FIELDS = [CORNFIELD, PIPER_CORN, CORN40]
def hashf(i, j, s=0): return ((i * 73856093 ^ j * 19349663 ^ s * 83492791) & 0xffff) / 0xffff
CELL, PARCEL, N = 50, 700, 9000 // 50
def wooded(x, y):  # the three woods, and the steep bluffs of the Potomac and the creek, which the DEM shows
    if any(inside(x, y, w) for w in WOODS): return True
    slope = math.hypot(z(x + 40, y) - z(x - 40, y), z(x, y + 40) - z(x, y - 40)) / 80
    return slope > 0.22
SEEDS = {(gx, gy): (gx * PARCEL + (hashf(gx, gy, 1) - 0.5) * PARCEL * 0.8, gy * PARCEL + (hashf(gx, gy, 2) - 0.5) * PARCEL * 0.8) for gx in range(-8, 9) for gy in range(-8, 9)}
def parcel(x, y):
    for n, f in enumerate(NAMED_FIELDS):
        if inside(x, y, f): return ('named', n)
    gx, gy = round(x / PARCEL), round(y / PARCEL)
    return min(((i, j) for i in range(gx - 2, gx + 3) for j in range(gy - 2, gy + 3) if (i, j) in SEEDS), key=lambda k: math.dist(SEEDS[k], (x, y)))
cells = {}
for j in range(N):
    for i in range(N):
        x, y = -4500 + (i + 0.5) * CELL, -4500 + (j + 0.5) * CELL
        if not wooded(x, y) and not wet((x, y)): cells.setdefault(parcel(x, y), set()).add((i, j))
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
        r = [(-4500 + u * CELL, -4500 + v * CELL) for u, v in ring]
        k = max(range(len(r)), key=lambda n: math.dist(r[n], r[0]))
        out.append(dp(r[:k + 1], 30)[:-1] + dp(r[k:] + [r[0]], 30)[:-1])
    return out
FIELDS = []
for key in sorted(cells, key=str):
    rs = rings(cells[key]); outer = [r for r in rs if area(r) > 20000]
    for o in outer:
        for hole in (r for r in rs if area(r) < -10000 and inside(*r[0], o)):  # bridged in, so even-odd and non-zero fills both leave it out
            k = min(range(len(o)), key=lambda n: math.dist(o[n], hole[0]))
            o[:] = o[:k + 1] + hole + [hole[0]] + o[k:]
        FIELDS.append([(round(x), round(y)) for x, y in o])

# ---- features ----
def label_on(a, b, off=0):  # a label at the middle of a-b, along it, `off` metres to its left
    ux, uy = (b[0] - a[0]) / math.dist(a, b), (b[1] - a[1]) / math.dist(a, b)
    rot = math.degrees(math.atan2(-uy, ux)); rot = rot - 180 if rot > 90 else rot + 180 if rot < -90 else rot
    return dict(at=[round((a[0] + b[0]) / 2 - off * uy), round((a[1] + b[1]) / 2 + off * ux)], rot=round(rot))
def offset(line, d):  # a line d metres to the right of another
    out = []
    for i, p in enumerate(line):
        a, b = line[max(0, i - 1)], line[min(len(line) - 1, i + 1)]; L_ = math.dist(a, b) or 1
        out.append((round(p[0] + d * (b[1] - a[1]) / L_), round(p[1] - d * (b[0] - a[0]) / L_)))
    return out
def stretch(line, y0, y1):  # the part of a north-south line between two latitudes
    return [(round(pike_x(y0)), y0)] + [p for p in line if y0 < p[1] < y1] + [(round(pike_x(y1)), y1)]
PIKE_N = stretch(PIKE, 1380, 2800)  # post-and-rail fences both sides, the Dunker Church to Miller's and on north
PIKE_S = stretch(PIKE, 150, 890)    # stone walls south of the Sunken Road
HF_FENCE = [P['hf_branch'], (P['hf_branch'][0] - 345, P['hf_branch'][1] - 345)]  # right at the Branch Avenue tablet, left 535 yards south-west
BLUFF_PITS = [(1035, -1230), (1045, -1330), (1050, -1440), (1030, -1530)]  # on the west bluff over the Burnside Bridge
MUMMA_FIRE = "1862-09-17 06:30"
features = [
    dict(type="creek", name="Antietam Creek", pts=CREEK, **label_on((1772, 771), (1700, 1100), 70)),
    dict(type="road", name="Hagerstown Pike", pts=PIKE, **label_on(PIKE[-3], PIKE[-2], 60)),
    dict(type="road", name="Boonsboro Pike", pts=L['boonsboro_pike'], **label_on((2300, -50), (2900, 500), 60)),
    dict(type="road", name="road to Shepherdstown and Boteler's Ford", pts=L['shepherdstown_rd'], **label_on(L['shepherdstown_rd'][2], L['shepherdstown_rd'][4], 60)),
    dict(type="road", name="Smoketown Road", pts=L['smoketown_rd'], **label_on(L['smoketown_rd'][3], L['smoketown_rd'][4], 50)),
    dict(type="road", name="Keedysville road", pts=L['keedysville_rd'], **label_on(L['keedysville_rd'][-6], L['keedysville_rd'][-4], 60)),
    dict(type="road", name="road to the Lower Bridge", pts=BRIDGE_RD),
    dict(type="road", name="Harpers Ferry Road", pts=L['harpers_ferry_rd'], **label_on(L['harpers_ferry_rd'][-4], L['harpers_ferry_rd'][-2], 60)),
    dict(type="road", name="Millers Sawmill Road", pts=L['sawmill_rd'], **label_on(L['sawmill_rd'][0], L['sawmill_rd'][1], 50)),
    dict(type="road", pts=L['mumma_lane']), dict(type="road", pts=L['roulette_lane']), dict(type="road", pts=SUNKEN_S),
    dict(type="trench", name="the Sunken Road (Bloody Lane)", pts=SUNKEN, **label_on(SUNKEN[-2], SUNKEN[-1], -60)),
    dict(type="fence", pts=offset(PIKE_N, 12)), dict(type="fence", pts=offset(PIKE_N, -12)),
    dict(type="works", name="stone walls on the Pike", pts=offset(PIKE_S, -12), **label_on(PIKE_S[0], PIKE_S[-1], -70)),
    dict(type="fence", name="stone fence (about here)", pts=HF_FENCE, **label_on(*HF_FENCE, -50)),
    dict(type="works", name="rifle pits", pts=BLUFF_PITS, at=[900, -1600]),
    dict(type="smoke", at=list(P['mumma']), rate=1.2, spread=30, **{"from": MUMMA_FIRE, "until": "1862-09-17 11:00"}),
    dict(name="Potomac River", at=[-3450, -2300], rot=-60),
    dict(name="Dunker Church", at=[P['church'][0] - 110, P['church'][1] + 20]),
    dict(name="D. R. Miller farm", at=[P['miller'][0] - 150, P['miller'][1] + 30]),
    dict(name="J. Poffenberger farm", at=[P['j_poffenberger'][0] + 40, P['j_poffenberger'][1] + 70]),
    dict(name="A. Poffenberger farm", at=[P['a_poffenberger'][0] - 60, P['a_poffenberger'][1] - 60]),
    dict(name="Mumma farm", at=[P['mumma'][0] + 130, P['mumma'][1] - 10]),
    dict(name="Roulette farm", at=[P['roulette'][0] + 140, P['roulette'][1]]),
    dict(name="Piper farm", at=[P['piper'][0] + 100, P['piper'][1] - 40]),
    dict(name="Otto farm", at=[P['otto'][0] + 90, P['otto'][1] - 40]),
    dict(name="Newcomer farm", at=[P['newcomer'][0] - 60, P['newcomer'][1] - 70]),
    dict(name="Pry House, McClellan's headquarters", at=[P['pry'][0] + 60, P['pry'][1] + 70]),
    dict(name="the Cornfield", at=[0, 2120]), dict(name="Piper's cornfield", at=list(P['piper_corn'])), dict(name="the 40-acre cornfield", at=list(P['corn40'])),
    dict(name="North Woods", at=[-640, 2700]), dict(name="East Woods", at=[480, 2150]), dict(name="West Woods", at=[-520, 1450]),
    dict(name="Burnside (Lower) Bridge", at=[P['burnside_bridge'][0] + 230, P['burnside_bridge'][1] - 40]),
    dict(name="Middle Bridge", at=[P['middle_bridge'][0] + 150, P['middle_bridge'][1] - 50]),
    dict(name="Upper Bridge", at=[P['upper_bridge'][0] + 140, P['upper_bridge'][1] + 30]),
    dict(name="Pry's Ford (about here)", at=[P['prys_ford'][0] - 40, P['prys_ford'][1] - 100]),
    dict(name="Snavely's Ford (about here)", at=[P['snavely_ford'][0] + 230, P['snavely_ford'][1]]),
    dict(name="Boteler's Ford (about here)", at=[P['boteler_ford'][0] + 250, P['boteler_ford'][1] + 260]),
    dict(name="Sharpsburg", at=[P['sharpsburg'][0] - 260, P['sharpsburg'][1] + 40]),
    dict(name="Cemetery Hill", at=[P['cemetery_hill'][0] + 60, P['cemetery_hill'][1] + 80]),
    dict(name="Nicodemus Heights", at=[NICODEMUS[0] - 250, NICODEMUS[1] - 60]), dict(name="Hauser Ridge", at=[HAUSER[0], HAUSER[1] - 90]),
    dict(name="Red Hill", at=[RED_HILL[0], RED_HILL[1] + 90]),
    dict(name="Keedysville", at=[P['keedysville'][0], P['keedysville'][1] + 80]), dict(name="Porterstown", at=[P['porterstown'][0] + 60, P['porterstown'][1] + 70]),
]
for f in features:
    if "at" in f and f.get("name") and f.get("type") != "smoke" and "Potomac" not in f["name"]: assert not wet(f["at"]), (f["name"], "a label in the river")

# ---- order of battle: (id, side, short, name, commander, type, strength, extra) ----
# Brigades. Strengths are the note's: Hartwig's corps and division totals via Wikipedia, Early's report for Lawton, Hays
# and Trimble, Williams's for Greene's two small brigades, Toombs's muskets at the bridge. Where the note gives only a
# division or corps figure it is shared among its brigades by their count of regiments, or of brigades where the note
# lists no regiments. Each drawn gun stands for a battery, with 100 men to a battery. A division drawn whole stands six
# ranks deep, for its brigades one behind another; the cavalry four or six, for its squadrons in column.
LANE = dict(ranks=4)
OOB = [
    # I Corps, Hooker: "about 8,600" in the dawn attack, 205 to a regiment
    ("phelps", "union", "Phelps", "Phelps's brigade: 22nd, 24th, 30th, 84th New York, 2nd U.S. Sharpshooters", "Col. Walter Phelps", "infantry", 1025, {}),
    ("hofmann", "union", "Hofmann", "Hofmann's brigade, in reserve: 7th Indiana, 76th, 95th New York, 56th Pennsylvania", "Lt. Col. J. William Hofmann", "infantry", 820, {}),
    ("patrick", "union", "Patrick", "Patrick's brigade: 21st, 23rd, 35th, 80th New York", "Brig. Gen. Marsena Patrick", "infantry", 820, {}),
    ("gibbon", "union", "Iron Brigade", "Gibbon's Iron Brigade: 19th Indiana, 2nd, 6th, 7th Wisconsin", "Brig. Gen. John Gibbon", "infantry", 820, {}),
    ("campbell", "union", "B/4th U.S.", "Campbell's battery, B, 4th U.S. Artillery", "Capt. Joseph Campbell", "artillery", 100, dict(guns=1)),
    ("duryee", "union", "Duryée", "Duryée's brigade: 97th, 104th, 105th New York, 107th Pennsylvania", "Brig. Gen. Abram Duryée", "infantry", 820, {}),
    ("christian", "union", "Christian", "Christian's brigade: 26th, 94th New York, 88th, 90th Pennsylvania", "Col. William Christian", "infantry", 820, {}),
    ("hartsuff", "union", "Hartsuff", "Hartsuff's brigade: 12th, 13th Massachusetts, 83rd New York, 11th Pennsylvania", "Brig. Gen. George Hartsuff (wounded)", "infantry", 820, {}),
    ("seymour", "union", "Seymour", "Seymour's brigade, Pennsylvania Reserves: 1st, 2nd, 5th, 6th, 13th", "Brig. Gen. Truman Seymour", "infantry", 1025, {}),
    ("magilton", "union", "Magilton", "Magilton's brigade, Pennsylvania Reserves: 3rd, 4th, 7th, 8th", "Col. Albert Magilton", "infantry", 820, {}),
    ("anderson_r", "union", "Anderson", "Anderson's brigade, Pennsylvania Reserves: 9th, 10th, 11th, 12th", "Col. Robert Anderson", "infantry", 820, {}),
    ("i_guns", "union", "I Corps guns", "I Corps batteries on the ridge by Joseph Poffenberger's", "Hooker's corps artillery", "artillery", 800, dict(guns=8)),
    # II Corps, Sumner: Richardson 4,000, Sedgwick 5,400, French 5,700
    ("caldwell", "union", "Caldwell", "Caldwell's brigade: 5th New Hampshire, 7th, 61st, 64th New York, 81st Pennsylvania", "Brig. Gen. John Caldwell", "infantry", 1429, {}),
    ("meagher", "union", "Irish Brigade", "Meagher's Irish Brigade: 29th Massachusetts, 63rd, 69th, 88th New York", "Brig. Gen. Thomas Meagher (wounded)", "infantry", 1143, {}),
    ("brooke", "union", "Brooke", "Brooke's brigade: 2nd Delaware, 52nd, 57th, 66th New York, 53rd Pennsylvania", "Col. John Brooke", "infantry", 1428, {}),
    ("gorman", "union", "Gorman", "Gorman's brigade: 15th Massachusetts, 1st Minnesota, 34th, 82nd New York", "Brig. Gen. Willis Gorman", "infantry", 1662, {}),
    ("howard", "union", "Philadelphia Brigade", "Howard's Philadelphia Brigade: 69th, 71st, 72nd, 106th Pennsylvania", "Brig. Gen. Oliver Howard", "infantry", 1662, {}),
    ("dana", "union", "Dana", "Dana's brigade: 19th, 20th Massachusetts, 7th Michigan, 42nd, 59th New York", "Brig. Gen. Napoleon Dana (wounded)", "infantry", 2076, {}),
    ("kimball", "union", "Kimball", "Kimball's brigade: 14th Indiana, 4th, 8th Ohio, 132nd Pennsylvania, 7th West Virginia", "Brig. Gen. Nathan Kimball", "infantry", 2590, {}),
    ("morris", "union", "Morris", "Morris's brigade: 14th Connecticut, 108th New York, 130th Pennsylvania", "Col. Dwight Morris", "infantry", 1555, {}),
    ("weber", "union", "Weber", "Weber's brigade: 1st Delaware, 5th Maryland, 4th New York", "Brig. Gen. Max Weber (wounded)", "infantry", 1555, {}),
    # V Corps, Porter, in reserve: 9,476 without Humphreys, who came up on the 18th
    ("morell", "union", "Morell", "Morell's division: Barnes's, Griffin's and Stockton's brigades", "Maj. Gen. George Morell", "infantry", 4738, dict(ranks=6)),
    ("sykes", "union", "Sykes", "Sykes's division of regulars: Buchanan's, Lovell's and Warren's brigades", "Brig. Gen. George Sykes", "infantry", 4738, dict(ranks=6)),
    ("reserve_guns", "union", "Reserve guns", "The Artillery Reserve's heavy rifled batteries east of the creek", "Lt. Col. William Hays", "artillery", 400, dict(guns=4)),
    # VI Corps, Franklin, up from Rohrersville about noon: 11,862
    ("slocum", "union", "Slocum", "Slocum's division: Torbert's New Jersey brigade, Bartlett's, Newton's", "Maj. Gen. Henry Slocum", "infantry", 5931, dict(ranks=6)),
    ("smith", "union", "Smith", "Smith's division: Hancock's and Brooks's Vermont brigades", "Maj. Gen. William F. Smith", "infantry", 3954, dict(ranks=6)),
    ("irwin", "union", "Irwin", "Irwin's brigade of Smith's division", "Col. William Irwin", "infantry", 1777, {}),
    # the 7th Maine of Irwin's brigade, drawn apart for its charge at five; the note gives no strength, so 200 is a guess
    ("maine7", "union", "7th Maine", "The 7th Maine, of Irwin's brigade", "Irwin's brigade", "infantry", 200, {}),
    # IX Corps, Burnside with Cox commanding: 12,241, seven batteries
    ("christ", "union", "Christ", "Christ's brigade of Willcox's division", "Col. Benjamin Christ", "infantry", 1443, {}),
    ("welsh", "union", "Welsh", "Welsh's brigade of Willcox's division", "Col. Thomas Welsh", "infantry", 1443, {}),
    ("nagle", "union", "Nagle", "Nagle's brigade of Sturgis's division: the 2nd Maryland and 6th New Hampshire at the bridge", "Brig. Gen. James Nagle", "infantry", 1443, {}),
    ("ferrero", "union", "Ferrero", "Ferrero's brigade of Sturgis's division: the 51st New York and 51st Pennsylvania carried the bridge", "Brig. Gen. Edward Ferrero", "infantry", 1443, {}),
    ("fairchild", "union", "Fairchild", "Fairchild's brigade of Rodman's division, with the 9th New York", "Col. Harrison Fairchild", "infantry", 1443, {}),
    ("harland", "union", "Harland", "Harland's brigade of Rodman's division, with the 11th and 16th Connecticut", "Col. Edward Harland", "infantry", 1443, {}),
    ("ewing", "union", "Ewing", "Ewing's brigade of the Kanawha Division", "Col. Hugh Ewing", "infantry", 1443, {}),
    ("crook", "union", "Crook", "Crook's brigade of the Kanawha Division", "Col. George Crook", "infantry", 1443, {}),
    ("ix_guns", "union", "IX Corps guns", "The four IX Corps batteries that crossed the bridge in the afternoon", "Cox's corps artillery", "artillery", 400, dict(guns=4)),
    ("ix_guns_e", "union", "IX Corps guns", "IX Corps batteries on the east bank", "Cox's corps artillery", "artillery", 300, dict(guns=3)),
    # XII Corps, Mansfield (mortally wounded), then Williams: 7,200 infantry; Greene's "two small brigades ... about 1,700 men"
    ("crawford", "union", "Crawford", "Crawford's brigade: 10th Maine, 28th New York, 46th, 124th, 125th, 128th Pennsylvania", "Brig. Gen. Samuel Crawford (wounded)", "infantry", 2200, {}),
    ("gordon", "union", "Gordon", "Gordon's brigade: 27th Indiana, 2nd Massachusetts, 13th New Jersey, 107th New York, 3rd Wisconsin", "Brig. Gen. George Gordon", "infantry", 1833, {}),
    ("tyndale", "union", "Tyndale", "Tyndale's brigade of Greene's division: 5th, 7th, 66th Ohio, 28th Pennsylvania", "Lt. Col. Hector Tyndale", "infantry", 850, {}),
    ("stainrook", "union", "Stainrook", "Stainrook's brigade of Greene's division: 3rd Maryland, 102nd New York, 111th Pennsylvania", "Col. Henry Stainrook", "infantry", 850, {}),
    ("goodrich", "union", "Goodrich", "Goodrich's brigade of Greene's division: 3rd Delaware, Purnell Legion, 60th, 78th New York", "Col. William Goodrich (mortally wounded)", "infantry", 1467, {}),
    ("xii_guns", "union", "XII Corps guns", "XII Corps batteries, Best's seven", "Capt. Clermont Best", "artillery", 820, dict(guns=7)),
    # Cavalry, Pleasonton: 4,543
    ("pleasonton", "union", "Pleasonton", "Pleasonton's cavalry division: Whiting's, Farnsworth's, Rush's, McReynolds's and Davis's brigades", "Brig. Gen. Alfred Pleasonton", "cavalry", 3943, dict(ranks=6)),
    ("horse_guns", "union", "Horse batteries", "Pleasonton's six horse batteries", "Brig. Gen. Alfred Pleasonton", "artillery", 600, dict(guns=6)),

    # Jackson's command. Ewell's division under Lawton, then Early: Early's report gives Lawton 1,150, Hays 550, Trimble
    # "less than 700"; Early about 1,100
    ("lawton", "confederate", "Lawton", "Lawton's brigade, under Douglass (killed): 13th, 26th, 31st, 38th, 60th, 61st Georgia", "Col. Marcellus Douglass", "infantry", 1150, {}),
    ("hays", "confederate", "Hays", "Hays's Louisiana brigade: 5th, 6th, 7th, 8th, 14th Louisiana", "Brig. Gen. Harry Hays", "infantry", 550, {}),
    ("trimble", "confederate", "Trimble", "Trimble's brigade, under Walker: 15th Alabama, 12th, 21st Georgia, 21st North Carolina, 1st North Carolina Battalion", "Col. James A. Walker", "infantry", 700, {}),
    ("early", "confederate", "Early", "Early's brigade: 13th, 25th, 31st, 44th, 49th, 52nd, 58th Virginia", "Brig. Gen. Jubal Early", "infantry", 1100, {}),
    # Jackson's own division, about 1,600: Grigsby's first line and Starke's second
    ("jfirst", "confederate", "Grigsby", "Jackson's Division, first line: Winder's (Stonewall) brigade and J. R. Jones's", "Col. Andrew Grigsby", "infantry", 711, {}),
    ("jsecond", "confederate", "Starke", "Jackson's Division, second line: Starke's Louisiana brigade and Taliaferro's", "Brig. Gen. William Starke (killed)", "infantry", 889, {}),
    ("shumaker", "confederate", "Jackson's guns", "Jackson's Division artillery: Poague's, Carpenter's, Brockenbrough's, Raine's, Caskie's and Wooding's batteries", "Maj. Lindsay Shumaker", "artillery", 600, dict(guns=6)),
    # Longstreet's command. Hood's division, 2,300
    ("wofford", "confederate", "Texas Brigade", "Wofford's Texas Brigade: 18th Georgia, Hampton's Legion, 1st, 4th, 5th Texas", "Col. William Wofford", "infantry", 1278, {}),
    ("law", "confederate", "Law", "Law's brigade: 4th Alabama, 2nd, 11th Mississippi, 6th North Carolina", "Col. Evander Law", "infantry", 1022, {}),
    # D. H. Hill's division: "less than 5,000" for both Maryland battles; drawn as 4,500, 196 to a regiment. The four
    # brigades that held the Sunken Road stand four deep, as they would have to for the lane to hold them.
    ("ripley", "confederate", "Ripley", "Ripley's brigade: 4th, 44th Georgia, 1st, 3rd North Carolina", "Brig. Gen. Roswell Ripley (wounded)", "infantry", 780, {}),
    ("rodes", "confederate", "Rodes", "Rodes's Alabama brigade: 3rd, 5th, 6th, 12th, 26th Alabama", "Brig. Gen. Robert Rodes (wounded)", "infantry", 980, LANE),
    ("garland", "confederate", "Garland", "Garland's brigade, under McRae: 5th, 12th, 13th, 20th, 23rd North Carolina", "Col. Duncan McRae", "infantry", 980, LANE),
    ("gb_anderson", "confederate", "G. B. Anderson", "G. B. Anderson's brigade: 2nd, 4th, 14th, 30th North Carolina", "Brig. Gen. George B. Anderson (mortally wounded)", "infantry", 780, LANE),
    ("colquitt", "confederate", "Colquitt", "Colquitt's brigade: 13th Alabama, 6th, 23rd, 27th, 28th Georgia", "Col. Alfred Colquitt", "infantry", 980, LANE),
    # McLaws's division, about 2,800
    ("kershaw", "confederate", "Kershaw", "Kershaw's brigade: 2nd, 3rd, 7th, 8th South Carolina", "Brig. Gen. Joseph Kershaw", "infantry", 700, {}),
    ("cobb", "confederate", "Cobb", "Cobb's brigade: 16th, 24th Georgia, Cobb's Legion, 15th North Carolina", "Lt. Col. Christopher Sanders", "infantry", 700, {}),
    ("semmes", "confederate", "Semmes", "Semmes's brigade: 10th, 53rd Georgia, 15th, 32nd Virginia", "Brig. Gen. Paul Semmes", "infantry", 700, {}),
    ("barksdale", "confederate", "Barksdale", "Barksdale's brigade: 13th, 17th, 18th, 21st Mississippi", "Brig. Gen. William Barksdale", "infantry", 700, {}),
    # R. H. Anderson's division: "Anderson's five brigades (3,400)", Mahone's reduced to 40 men and put with Pryor's;
    # Armistead's, sent to McLaws, at the same 200 to a regiment
    ("wilcox", "confederate", "Wilcox", "Wilcox's brigade, under Cumming: 8th, 9th, 10th, 11th Alabama", "Col. Alfred Cumming", "infantry", 800, {}),
    ("featherston", "confederate", "Featherston", "Featherston's brigade, under Posey: 12th, 16th, 19th Mississippi, 2nd Mississippi Battalion", "Col. Carnot Posey", "infantry", 800, {}),
    ("pryor", "confederate", "Pryor", "Pryor's brigade, with the 40 men left of Mahone's: 14th Alabama, 2nd, 5th, 8th Florida, 3rd Virginia", "Brig. Gen. Roger Pryor", "infantry", 1000, {}),
    ("wright", "confederate", "Wright", "Wright's brigade: 44th Alabama, 3rd, 22nd, 48th Georgia", "Brig. Gen. Ambrose Wright (wounded)", "infantry", 800, {}),
    ("armistead", "confederate", "Armistead", "Armistead's brigade: 9th, 14th, 38th, 53rd, 57th Virginia", "Brig. Gen. Lewis Armistead", "infantry", 1000, {}),
    # D. R. Jones's division, "about 3,000 with 12 guns"; at the bridge Toombs's 2nd and 20th Georgia, some 400 muskets each,
    # and the 50th, under 120: about 550 engaged
    ("toombs", "confederate", "Toombs", "Toombs's men at the bridge: the 2nd, 20th and 50th Georgia", "Brig. Gen. Robert Toombs", "infantry", 550, {}),
    ("drayton", "confederate", "Drayton", "Drayton's brigade: 51st Georgia, Phillips's Legion, 15th South Carolina, 3rd South Carolina Battalion", "Brig. Gen. Thomas Drayton", "infantry", 400, {}),
    ("garnett", "confederate", "Garnett", "Garnett's brigade: 8th, 18th, 19th, 28th, 56th Virginia", "Brig. Gen. Richard Garnett", "infantry", 500, {}),
    ("kemper", "confederate", "Kemper", "Kemper's brigade: 1st, 7th, 11th, 17th, 24th Virginia", "Brig. Gen. James Kemper", "infantry", 500, {}),
    ("jenkins", "confederate", "Jenkins", "Jenkins's brigade, under Walker: 1st, 2nd Rifles, 5th, 6th South Carolina, 4th Battalion, Palmetto Sharpshooters", "Col. Joseph Walker", "infantry", 600, {}),
    ("gt_anderson", "confederate", "G. T. Anderson", "G. T. Anderson's brigade: 1st, 7th, 8th, 9th, 11th Georgia", "Col. George T. Anderson", "infantry", 500, {}),
    ("cemetery_guns", "confederate", "Washington Artillery", "The Washington Artillery, four companies, on Cemetery Hill", "Col. James Walton", "artillery", 400, dict(guns=4)),
    # Walker's division, about 3,200
    ("manning", "confederate", "Manning", "Manning's brigade: 3rd Arkansas, 27th, 46th, 48th North Carolina, 30th Virginia, French's battery", "Col. Van Manning", "infantry", 1778, {}),
    ("ransom", "confederate", "Ransom", "Ransom's brigade: 24th, 25th, 35th, 49th North Carolina, Branch's battery", "Brig. Gen. Robert Ransom", "infantry", 1422, {}),
    ("evans", "confederate", "Evans", "Evans's brigade, under Stevens: 17th, 18th, 22nd, 23rd South Carolina, Holcombe Legion", "Col. Peter Stevens", "infantry", 300, {}),
    ("sdlee", "confederate", "S. D. Lee", "S. D. Lee's artillery battalion, six batteries", "Col. Stephen D. Lee", "artillery", 600, dict(guns=6)),
    # A. P. Hill's Light Division from Harpers Ferry: "about 3,000", "about 2,000" in the three brigades engaged
    ("branch", "confederate", "Branch", "Branch's brigade: 7th, 18th, 28th, 33rd, 37th North Carolina", "Brig. Gen. Lawrence Branch (killed)", "infantry", 667, {}),
    ("gregg", "confederate", "Gregg", "Gregg's South Carolina brigade: 1st Provisional Army, 1st Rifles, 12th, 13th, 14th", "Brig. Gen. Maxcy Gregg (wounded)", "infantry", 667, {}),
    ("archer", "confederate", "Archer", "Archer's brigade: 5th Alabama Battalion, 19th Georgia, 1st, 7th, 14th Tennessee", "Brig. Gen. James Archer", "infantry", 666, {}),
    ("pender", "confederate", "Pender", "Pender's brigade: 16th, 22nd, 34th, 38th North Carolina", "Brig. Gen. Dorsey Pender", "infantry", 556, {}),
    ("field", "confederate", "Brockenbrough", "Field's brigade, under Brockenbrough: 40th, 47th, 55th Virginia, 22nd Virginia Battalion", "Col. John Brockenbrough", "infantry", 444, {}),
    ("rlwalker", "confederate", "Hill's guns", "A. P. Hill's artillery, four batteries", "Lt. Col. R. Lindsay Walker", "artillery", 400, dict(guns=4)),
    # Stuart's cavalry, about 4,500, and Pelham's guns on Nicodemus Heights
    ("stuart", "confederate", "Stuart", "Stuart's cavalry: Hampton's and Munford's brigades", "Maj. Gen. J. E. B. Stuart", "cavalry", 3000, dict(ranks=4)),
    ("fitzlee", "confederate", "Fitz Lee", "Fitz Lee's cavalry brigade", "Brig. Gen. Fitzhugh Lee", "cavalry", 1500, dict(ranks=4)),
    ("pelham", "confederate", "Pelham", "Stuart's horse artillery on Nicodemus Heights", "Maj. John Pelham", "artillery", 300, dict(guns=3)),
]
BASE = {row[0]: row for row in OOB}
assert len(BASE) == len(OOB)

# ---- the clock: 16 to 19 September 1862, local mean time ----
UTC = dt.timezone.utc
T0 = dt.datetime(1862, 9, 16, tzinfo=UTC)
def D(day, hm): return f"1862-09-{day:02d} {hm}"
def sec(t): return (dt.datetime.strptime(t, "%Y-%m-%d %H:%M:%S" if t.count(":") == 2 else "%Y-%m-%d %H:%M").replace(tzinfo=UTC) - T0).total_seconds()
def fmt(s): s = round(s); return (T0 + dt.timedelta(seconds=s)).strftime("%Y-%m-%d %H:%M" + (":%S" if s % 60 else ""))
def plus(t, mins): return fmt(sec(t) + mins * 60)
START, END = D(16, "14:00"), D(19, "09:30")

# ---- movement ----
KEYS = {}
def K(t, p, **kw): return dict(t=t, x=round(p[0]), y=round(p[1]), **kw)
def heading(a, b): return round(math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) % 360)
def carried(id, f): return next((k[f] for k in reversed(KEYS.get(id, [])) if f in k), {"state": "line", "strength": BASE[id][6]}.get(f))
def keys(id, ks):  # every leg starts where the unit stands, unless it is coming out of hiding
    have = KEYS.setdefault(id, [])
    if have and ks:
        a, b = have[-1], ks[0]
        assert carried(id, "state") == "hidden" or (a["x"], a["y"]) == (b["x"], b["y"]), (id, a["t"], b["t"], "a leg must start where the unit stands")
        if a["t"] == b["t"]: a.update({k: v for k, v in b.items() if k != "t"}); ks = ks[1:]
        elif "h" in b and b["h"] != carried(id, "h") and sec(b["t"]) - sec(a["t"]) > 120:  # wheel in the last minute, so a long halt stays quiet
            have.append(K(fmt(sec(b["t"]) - 60), (a["x"], a["y"])))
    have += ks
def last(id): k = KEYS[id][-1]; return (k["x"], k["y"])
def appear(id, t, p, h, state="line", **kw): keys(id, [K(t, p, h=h, state=state, **kw)])

# Where each unit stands at two in the afternoon of the 16th; those still on the march are hidden.
HIDDEN = {"slocum", "smith", "irwin", "kershaw", "cobb", "semmes", "barksdale", "wilcox", "featherston", "pryor", "wright", "armistead",
          "branch", "gregg", "archer", "pender", "field", "rlwalker", "maine7", "crawford", "gordon", "tyndale", "stainrook", "goodrich", "xii_guns"}
AT_START = {
    # I Corps at Keedysville, about to march
    "phelps": ((3700, 2700), 270), "hofmann": ((3850, 2750), 270), "patrick": ((3750, 2850), 270), "gibbon": ((3600, 2650), 270), "campbell": ((3650, 2580), 270),
    "duryee": ((3900, 2450), 270), "christian": ((4000, 2550), 270), "hartsuff": ((3950, 2350), 270),
    "seymour": ((3800, 2300), 270), "magilton": ((3900, 2200), 270), "anderson_r": ((4050, 2250), 270), "i_guns": ((4100, 2650), 270),
    # II Corps near the army's headquarters at the Pry House, Richardson behind the bluff over the creek
    "gorman": ((3000, 1750), 270), "howard": ((3150, 1750), 270), "dana": ((3075, 1850), 270),
    "kimball": ((3050, 1350), 270), "morris": ((3200, 1350), 270), "weber": ((3125, 1250), 270),
    "caldwell": ((2650, 1150), 270), "meagher": ((2750, 1050), 270), "brooke": ((2850, 1150), 270),
    # V Corps and the cavalry by the Middle Bridge; the heavy rifles on the ridge east of the creek
    "morell": ((2400, 150), 270), "sykes": ((2250, 450), 270), "reserve_guns": ((2350, 1950), 250),
    "pleasonton": ((2650, 650), 270), "horse_guns": ((2500, 500), 270),
    # IX Corps on the heights east of the Lower Bridge
    "nagle": ((1650, -1250), 260), "ferrero": ((1800, -1150), 260), "crook": ((1600, -1000), 260), "christ": ((2150, -1050), 260), "welsh": ((2250, -1250), 260),
    "fairchild": ((1800, -1750), 260), "harland": ((1700, -1900), 260), "ewing": ((1950, -1550), 260),
    "ix_guns": ((1550, -1350), 260), "ix_guns_e": ((1500, -1500), 260),
    # Longstreet's command outside the town, its left at Cemetery Hill on the Boonsboro Pike, its right toward the bridge
    "toombs": ((1030, -1380), 80), "drayton": ((450, -1150), 90), "kemper": ((350, -850), 90), "garnett": ((380, -550), 90), "jenkins": ((450, -250), 90),
    "gt_anderson": ((600, 0), 90), "evans": ((550, 200), 90), "cemetery_guns": ((330, -380), 90), "manning": ((300, -1800), 110), "ransom": ((100, -1650), 110),
    # D. H. Hill on Longstreet's left, toward the Mumma farm; S. D. Lee's guns on the ridge east of the church
    "ripley": ((250, 1480), 0), "colquitt": ((380, 1280), 20), "garland": ((520, 1180), 30), "rodes": ((250, 760), 20), "gb_anderson": ((600, 450), 20),
    "sdlee": ((120, 1400), 40),
    # Hood near the East Woods; Jackson's and Ewell's divisions forming on Longstreet's left through the West Woods
    "wofford": ((0, 1900), 20), "law": ((300, 2000), 20),
    "jfirst": ((-380, 1950), 30), "jsecond": ((-520, 1700), 30), "shumaker": ((-330, 2050), 20),
    "lawton": ((-350, 1450), 30), "trimble": ((-480, 1580), 30), "hays": ((-700, 1400), 40), "early": ((-800, 1700), 30),
    # Stuart on the left, out to the Potomac
    "stuart": ((-1400, 2700), 60), "fitzlee": ((-1350, 1900), 60), "pelham": (NICODEMUS, 60),
}
for id in BASE:
    if id in HIDDEN: appear(id, START, (4400, 0), 270, state="hidden")
    else: p, h = AT_START[id]; appear(id, START, p, h)
def A(hm): return D(16, hm)
def B(hm): return D(17, hm)
def C(hm): return D(18, hm)
def E(hm): return D(19, hm)
def path_from(id, pts):
    out = [last(id)] + [tuple(p) for p in pts]
    return [p for i, p in enumerate(out) if i == 0 or math.dist(p, out[i - 1]) > 5]
def mv(id, t0, t1, *pts, h=None, state="line", moving="column", **kw):  # from where it stands at t0 to the last point at t1, times spread by distance
    pts = path_from(id, pts)
    if len(pts) < 2: return stand(id, t1, state=state, **({"h": h} if h is not None else {}), **kw)
    d = [0]
    for a, b in zip(pts, pts[1:]): d.append(d[-1] + math.dist(a, b))
    ks = [K(t0, pts[0], h=heading(pts[0], pts[1]), state=moving)]
    for i in range(1, len(pts) - 1): ks.append(K(fmt(sec(t0) + (sec(t1) - sec(t0)) * d[i] / d[-1]), pts[i], h=heading(pts[i], pts[i + 1])))
    ks.append(K(t1, pts[-1], h=heading(pts[-2], pts[-1]) if h is None else h, state=state, **kw))
    keys(id, ks)
def walk(id, t0, *pts, h=None, state="line", kmh=3.5, **kw):  # at a marching pace from t0; returns the arrival time
    pts = path_from(id, pts); t = sec(t0)
    ks = [K(t0, pts[0], h=heading(pts[0], pts[1]), state="column")]
    for i in range(1, len(pts)):
        t += math.dist(pts[i - 1], pts[i]) / (kmh / 3.6)
        ks.append(K(fmt(t), pts[i], h=heading(pts[i], pts[i + 1]) if i + 1 < len(pts) else (h if h is not None else heading(pts[i - 1], pts[i]))))
    ks[-1].update(state=state, **kw); keys(id, ks); return ks[-1]["t"]
def stand(id, t, **kw): keys(id, [K(t, last(id), **kw)])
def fight(id, t0, t1, strength, h=None, after="line"):  # firing from t0 to t1, where it stands, down to `strength`
    stand(id, t0, state="firing", **({"h": h} if h is not None else {})); stand(id, t1, state=after, strength=strength)
def show(id, t, p, h, state="column"): keys(id, [K(t, p, h=h, state=state)])
def hide(id, t): stand(id, t, state="hidden")
def along(line, a, b):  # the stretch of a road between the points on it nearest a and b
    def proj(p):
        best = None
        for i, (u, v) in enumerate(zip(line, line[1:])):
            dx, dy = v[0] - u[0], v[1] - u[1]; t = max(0, min(1, ((p[0] - u[0]) * dx + (p[1] - u[1]) * dy) / (dx * dx + dy * dy or 1)))
            q = (u[0] + t * dx, u[1] + t * dy)
            if best is None or math.dist(p, q) < best[0]: best = (math.dist(p, q), i + t, q)
        return best[1], best[2]
    (sa, qa), (sb, qb) = proj(a), proj(b)
    mid = [line[i] for i in range(math.floor(min(sa, sb)) + 1, math.ceil(max(sa, sb)))]
    return [qa] + (mid if sa <= sb else mid[::-1]) + [qb]
# Boteler's Ford: units come and go at the Maryland end, the river itself being drawn as water. The ways from it are
# inferred: McLaws, Anderson and the withdrawal by the road to Shepherdstown and the town; A. P. Hill down the bank to
# Millers Sawmill Road, which the note gives as his lane up to the Harpers Ferry Road.
FORD = (P['boteler_ford'][0], P['boteler_ford'][1] + 135)
HF = L['harpers_ferry_rd']; SAW = L['sawmill_rd']
TOWN = (-228, -810)                                              # the Harpers Ferry Road's north end, at the town
FORD_TO_HF = [FORD, (-2200, -2700), (-1600, -2700)] + SAW[4::-1]  # the ford up to the Harpers Ferry Road at the Branch Avenue tablet
HF_TO_FORD = FORD_TO_HF[::-1]
FORD_TO_TOWN = [FORD] + along(L['shepherdstown_rd'], (-3020, -2380), L['shepherdstown_rd'][0])
TOWN_TO_FORD = FORD_TO_TOWN[::-1]

# ---- 16 September: Hooker over the Antietam, the skirmish at the East Woods, the night ----
# Doubleday by Pry's Ford, Ricketts and Meade by the Upper Bridge, to the ground north of the Cornfield.
UPPER, PRYS = P['upper_bridge'], P['prys_ford']
for id, t0, end, h in (("gibbon", "14:00", (-420, 2950), 190), ("phelps", "14:10", (-560, 3060), 190), ("patrick", "14:20", (-700, 2940), 200),
                       ("hofmann", "14:30", (-450, 3220), 190), ("campbell", "14:05", (-300, 3060), 190)):
    walk(id, A(t0), (3000, 2050), (PRYS[0] + 60, PRYS[1]), (PRYS[0] - 60, PRYS[1] + 20), (1700, 2000), (900, 2950), (100, 3200), end, h=h, kmh=2.5)
for id, t0, end, h in (("seymour", "14:00", (430, 2560), 200), ("magilton", "14:10", (150, 2720), 190), ("anderson_r", "14:20", (310, 2830), 190),
                       ("duryee", "14:30", (700, 2880), 190), ("christian", "14:40", (860, 2980), 190), ("hartsuff", "14:50", (640, 3080), 190),
                       ("i_guns", "15:00", (-150, 3060), 190)):
    walk(id, A(t0), (UPPER[0] + 80, UPPER[1]), (UPPER[0] - 80, UPPER[1] + 20), (1700, 3200), (900, 3050), end, h=h, kmh=2.2)
mv("law", A("17:20"), A("17:50"), (420, 2260), h=20); mv("wofford", A("17:20"), A("17:50"), (150, 2150), h=20)
fight("seymour", A("18:00"), A("18:30"), 985, h=200); fight("law", A("18:00"), A("18:30"), 1000, h=20)
# At ten Lawton and Trimble relieve Hood, who goes back behind the church; Hays to the north-west of the church.
mv("lawton", A("22:00"), A("22:40"), (-80, 1980), h=20); mv("trimble", A("22:00"), A("22:40"), (300, 1760), h=30)
mv("hays", A("22:00"), A("22:20"), (-300, 1520), h=30)
mv("law", A("22:40"), A("23:20"), (-250, 1300), h=30); mv("wofford", A("22:40"), A("23:20"), (-360, 1250), h=30)
# The XII Corps over the Upper Bridge about midnight to the ground north of the Smoketown Road.
for id, t0, end in (("tyndale", "23:30", (1300, 3300)), ("stainrook", "23:40", (1450, 3300)), ("goodrich", "23:50", (1600, 3420)),
                    ("crawford", "23:55", (1400, 3520)), ("gordon", "23:58", (1560, 3620)), ("xii_guns", "23:45", (1720, 3320))):
    show(id, A(t0), (UPPER[0] + 200, UPPER[1] + 60), 280)
    walk(id, A(t0), (UPPER[0] - 80, UPPER[1] + 20), (2000, 3200), end, h=230, kmh=2.5)

# ---- 17 September, dawn: Hooker down the Pike and into the Cornfield ----
fight("i_guns", B("05:30"), B("10:00"), 760, h=190)
fight("reserve_guns", B("05:45"), B("12:00"), 400, h=260)
fight("pelham", B("05:30"), B("10:00"), 270, h=80)
fight("sdlee", B("05:30"), B("08:15"), 520, h=20)
fight("shumaker", B("05:45"), B("06:50"), 520, h=20)
# Gibbon leads down the Pike, Phelps and Patrick behind, Hofmann in reserve
mv("gibbon", B("05:30"), B("06:00"), (-490, 2700), (-430, 2420), h=180, state="firing")
mv("campbell", B("05:30"), B("06:00"), (-450, 2650), (-330, 2470), h=180, state="firing")
mv("phelps", B("05:30"), B("06:10"), (-560, 2800), (-300, 2400), h=180)
mv("patrick", B("05:40"), B("06:10"), (-650, 2700), (-620, 2420), h=200, state="firing")
mv("hofmann", B("05:50"), B("06:20"), (-470, 2780), h=180)
fight("seymour", B("05:30"), B("06:30"), 860, h=200)
fight("lawton", B("05:30"), B("06:00"), 950, h=20)
# Ricketts forms at six, Hartsuff leading, Duryée on the right into the Cornfield, Christian on the left
mv("duryee", B("06:00"), B("06:25"), (300, 2500), (100, 2250), h=190, state="firing")
mv("hartsuff", B("06:00"), B("06:30"), (450, 2600), (250, 2220), h=200, state="firing")
mv("christian", B("06:00"), B("06:35"), (650, 2600), (430, 2280), h=200, state="firing")
fight("trimble", B("05:45"), B("07:00"), 472, h=30)
# Hays over the Pike 120 yards north of the church, between Lawton and Trimble, and into the Cornfield
mv("hays", B("05:45"), B("06:10"), (-150, 1485), (120, 1900), h=20, state="firing")
mv("hays", B("06:30"), B("06:40"), (100, 2080), h=10, state="firing")
fight("hays", B("06:40"), B("07:00"), 227)
mv("gibbon", B("06:20"), B("06:45"), (-340, 2080), h=170, state="firing")
mv("phelps", B("06:15"), B("06:35"), (-150, 2180), h=180, state="firing")
fight("lawton", B("06:00"), B("07:00"), 596, h=20)
fight("duryee", B("06:25"), B("06:50"), 620, h=190)
# Grigsby's first line fights over half an hour, then falls back 380 yards to the woods' edge
fight("jfirst", B("06:00"), B("06:35"), 330, h=40)
mv("jfirst", B("06:35"), B("06:50"), (-500, 1650), h=30)
# Meade forms about half past six; Seymour left and forward, Magilton and Anderson into the gap
mv("magilton", B("06:30"), B("06:55"), (-80, 2340), h=190, state="firing")
mv("anderson_r", B("06:30"), B("07:00"), (80, 2380), h=190, state="firing")
mv("seymour", B("06:30"), B("06:45"), (520, 2200), h=210, state="firing")
# Starke's second line to the Pike fence, shot down in flank; Starke killed; back to the West Woods
mv("jsecond", B("06:30"), B("06:40"), (-300, 1800), h=40, state="firing")
fight("jsecond", B("06:40"), B("06:55"), 300)
mv("jsecond", B("06:55"), B("07:15"), (-600, 1560), h=40, state="retreat")
stand("jsecond", B("07:16"), state="line")
mv("shumaker", B("06:50"), B("07:20"), (-900, 1700), h=40)
mv("duryee", B("06:50"), B("07:10"), (200, 2500), state="retreat")
mv("duryee", B("07:10"), B("07:40"), (500, 2900), h=190)
# Ripley fires the Mumma buildings and crosses the Smoketown Road, Colquitt and Garland behind
mv("ripley", B("06:30"), B("07:15"), (250, 1700), (150, 1950), h=10, state="firing")
mv("colquitt", B("07:00"), B("07:45"), (380, 1650), (350, 1990), h=10, state="firing")
mv("garland", B("07:00"), B("07:45"), (520, 1600), (500, 1950), h=10, state="firing")
# About seven Hood relieves Lawton, Hays and Trimble: Wofford on the Pike to the north edge of the Cornfield, Law into the East Woods
mv("wofford", B("07:00"), B("07:25"), (-180, 1500), (-160, 1950), (-150, 2230), h=10, moving="charge", state="firing")
mv("law", B("07:00"), B("07:25"), (100, 1700), (350, 2100), h=20, moving="charge", state="firing")
mv("law", B("07:25"), B("07:35"), (520, 2160), h=60, state="firing")
for id, end in (("lawton", (-700, 1080)), ("hays", (-880, 980)), ("trimble", (-560, 940))): mv(id, B("07:00"), B("07:40"), (-200, 1450), end, h=30, state="line", moving="retreat")
fight("magilton", B("06:55"), B("07:40"), 600); fight("anderson_r", B("07:00"), B("07:40"), 650)
fight("hartsuff", B("06:30"), B("07:15"), 400); fight("christian", B("06:35"), B("07:15"), 600)
fight("seymour", B("06:45"), B("07:15"), 750)
mv("hartsuff", B("07:15"), B("07:40"), (450, 2650), h=200, state="line", moving="retreat")
mv("christian", B("07:15"), B("07:45"), (650, 2700), h=200, state="line", moving="retreat")
mv("seymour", B("07:15"), B("07:40"), (400, 2620), h=200, state="line", moving="retreat")
# Gibbon and Phelps driven out of the Cornfield; Early, back from Stuart's guns, and Grigsby's 200 turn Gibbon's and Patrick's flank
fight("gibbon", B("06:45"), B("07:05"), 600); fight("phelps", B("06:35"), B("07:05"), 800)
mv("gibbon", B("07:05"), B("07:25"), (-420, 2420), h=180, state="firing")
mv("phelps", B("07:05"), B("07:25"), (-260, 2450), h=180, state="firing")
mv("early", B("05:30"), B("05:55"), (-1150, 2300), h=60)
mv("early", B("06:55"), B("07:20"), (-550, 2050), h=40, state="firing")
mv("jfirst", B("07:00"), B("07:20"), (-480, 2180), h=40, state="firing")
fight("patrick", B("06:10"), B("07:15"), 640)
fight("early", B("07:20"), B("07:45"), 1000); fight("jfirst", B("07:20"), B("07:45"), 100)
fight("campbell", B("06:00"), B("07:30"), 60)
for id, end in (("gibbon", (-470, 2920)), ("phelps", (-560, 3050)), ("patrick", (-690, 2950)), ("campbell", (-300, 3020))):
    mv(id, B("07:30"), B("07:55"), end, h=190, state="line", moving="retreat")
mv("magilton", B("07:40"), B("08:00"), (-100, 2760), h=190, state="line", moving="retreat")
mv("anderson_r", B("07:40"), B("08:00"), (60, 2800), h=190, state="line", moving="retreat")
mv("jfirst", B("07:45"), B("08:05"), (-560, 1700), h=40); mv("early", B("07:45"), B("08:05"), (-640, 1800), h=40)
mv("hofmann", B("07:40"), B("08:00"), (-450, 3100), h=190)
# Hood checked at the edge of the Cornfield and the East Woods, and back to the West Woods with 60 percent lost
fight("wofford", B("07:25"), B("07:45"), 511); fight("law", B("07:35"), B("07:45"), 409)
mv("wofford", B("07:45"), B("08:15"), (-160, 1950), (-200, 1450), (-480, 1250), h=40, state="line", moving="retreat")
mv("law", B("07:45"), B("08:15"), (100, 1700), (-150, 1400), (-330, 1180), h=40, state="line", moving="retreat")

# ---- 17 September, 7 to 9: Mansfield's XII Corps and Greene to the Dunker Church ----
mv("crawford", B("06:00"), B("07:00"), (750, 2900), h=200)
mv("gordon", B("06:00"), B("07:00"), (0, 2860), h=190)
mv("crawford", B("07:30"), B("07:50"), (260, 2250), h=200, state="firing")
mv("gordon", B("07:30"), B("07:50"), (0, 2200), h=180, state="firing")
fight("crawford", B("07:50"), B("08:40"), 1500); fight("gordon", B("07:50"), B("08:40"), 1300)
fight("ripley", B("07:15"), B("08:00"), 520); fight("colquitt", B("07:45"), B("08:00"), 800); fight("garland", B("07:45"), B("08:00"), 800)
for id, t0, wait, end in (("tyndale", "06:30", (350, 3100), (170, 2450)), ("stainrook", "06:35", (650, 3150), (340, 2420)),
                          ("goodrich", "06:40", (950, 3250), (420, 2620)), ("xii_guns", "06:45", (1150, 3100), (520, 2560))):
    walk(id, B(t0), wait, h=200, kmh=2.5); mv(id, B("07:35"), B("08:00"), end, h=200)
# Greene turns the Confederate right in the East Woods, crosses the Smoketown Road and makes the Mumma ridge by the church
mv("tyndale", B("08:00"), B("08:20"), (330, 2050), h=210, state="firing")
mv("stainrook", B("08:00"), B("08:20"), (480, 2000), h=210, state="firing")
mv("ripley", B("08:00"), B("08:35"), (-300, 1520), h=40, state="line", moving="retreat")
mv("colquitt", B("08:00"), B("08:45"), (300, 1500), (40, 900), h=10, state="line", moving="retreat")
mv("garland", B("08:00"), B("08:45"), (420, 1500), (180, 910), h=10, state="line", moving="retreat")
mv("tyndale", B("08:20"), B("08:50"), (50, 1460), h=230, state="firing")
mv("stainrook", B("08:20"), B("08:50"), (210, 1440), h=230, state="firing")
mv("goodrich", B("08:10"), B("08:40"), (320, 2150), h=200)
mv("xii_guns", B("08:30"), B("09:10"), (330, 1810), h=230, state="firing")
mv("crawford", B("08:40"), B("09:00"), (300, 2400), h=200); mv("gordon", B("08:40"), B("09:00"), (100, 2450), h=200)
# S. D. Lee's guns, on the ridge east of the church since daybreak, 600 yards south of it at 8:15 and to Sharpsburg at nine
mv("sdlee", B("08:15"), B("08:35"), (-120, 830), h=20, state="firing")
mv("sdlee", B("09:00"), B("09:30"), (-60, 0), (-230, -360), h=60)
mv("gt_anderson", B("07:30"), B("08:35"), (40, 200), (-60, 900), (-230, 1250), h=10)

# ---- 17 September, 7:30 to 10: Sedgwick into the West Woods; McLaws, Walker and the rout ----
SEDG = [(PRYS[0] + 60, PRYS[1]), (PRYS[0] - 60, PRYS[1] + 20), (1200, 1850), (600, 2050), (-260, 1910)]
mv("gorman", B("07:30"), B("09:00"), *SEDG); mv("gorman", B("09:00"), B("09:12"), (-660, 1900), h=270)
mv("dana", B("07:35"), B("09:03"), *SEDG); mv("dana", B("09:03"), B("09:14"), (-510, 1880), h=270)
mv("howard", B("07:40"), B("09:06"), *SEDG); mv("howard", B("09:06"), B("09:15"), (-360, 1890), h=270)
# McLaws and Anderson over Boteler's Ford about daybreak and sunrise, to the town
for id, t0, end in (("kershaw", "05:10", (-560, -230)), ("cobb", "05:15", (-640, -330)), ("barksdale", "05:20", (-720, -430)), ("semmes", "05:25", (-800, -530)),
                    ("armistead", "05:35", (-880, -630)), ("wilcox", "05:40", (-500, -900)), ("featherston", "05:45", (-600, -1000)),
                    ("pryor", "05:50", (-700, -1100)), ("wright", "05:55", (-800, -1200))):
    show(id, B(t0), FORD, 60); walk(id, B(t0), *FORD_TO_TOWN[1:], end, h=30, kmh=4)
# McLaws deploys about nine from the Pike opposite the Sunken Road to 250 yards north-west of the Hauser house
mv("cobb", B("08:15"), B("09:00"), (-450, 300), (-260, 1000), h=20)
mv("kershaw", B("08:15"), B("09:00"), (-450, 400), (-380, 1150), h=20)
mv("barksdale", B("08:15"), B("09:00"), (-600, 400), (-680, 1290), h=20)
mv("semmes", B("08:15"), B("09:00"), (-800, 400), (-980, 1450), h=20)
# Walker from the bridge sector to the church, between eight and nine
mv("ransom", B("08:10"), B("09:15"), (-80, -400), (-300, 900), (-470, 1480), h=20)
mv("manning", B("08:00"), B("09:20"), (-40, -700), (-60, 600), (-250, 1250), h=40)
# The blow on Sedgwick's left and front: Kershaw by the church, Barksdale and Semmes up through the woods, Ransom and
# G. T. Anderson from the south; in less than twenty minutes nearly half of his 5,000
mv("kershaw", B("09:10"), B("09:25"), (-220, 1500), (-260, 1720), h=10, moving="charge", state="firing")
mv("barksdale", B("09:10"), B("09:25"), (-540, 1750), h=20, moving="charge", state="firing")
mv("semmes", B("09:10"), B("09:30"), (-780, 1820), h=20, moving="charge", state="firing")
mv("gt_anderson", B("09:05"), B("09:20"), (-330, 1620), h=10, state="firing")
fight("ransom", B("09:20"), B("09:40"), 1250, h=10)
mv("early", B("09:10"), B("09:25"), (-700, 1820), h=60, state="firing")
fight("gorman", B("09:15"), B("09:25"), 1250, h=270); fight("dana", B("09:15"), B("09:25"), 1600); fight("howard", B("09:15"), B("09:22"), 1300)
mv("howard", B("09:22"), B("09:42"), (-300, 2650), h=10, state="line", moving="rout", strength=1024)
mv("dana", B("09:25"), B("09:45"), (-430, 2620), h=10, state="line", moving="rout", strength=1176)
mv("gorman", B("09:25"), B("09:48"), (-560, 2600), h=10, state="line", moving="rout", strength=1000)
for id in ("howard", "dana", "gorman"): stand(id, B("10:00"), h=190)
mv("barksdale", B("09:25"), B("09:45"), (-470, 2150), h=10, state="firing")
mv("semmes", B("09:30"), B("09:50"), (-660, 2200), h=10, state="firing")
fight("kershaw", B("09:25"), B("09:45"), 520); fight("gt_anderson", B("09:20"), B("09:45"), 380); fight("early", B("09:25"), B("09:45"), 900)
mv("armistead", B("09:00"), B("09:45"), (-750, 400), (-600, 1350), h=20)
# Stuart's and Jackson's push across the open fields toward the batteries, driven back to the West Woods
mv("stuart", B("09:30"), B("09:50"), (-950, 2650), h=90, state="charge")
mv("stuart", B("09:50"), B("10:15"), (-1400, 2700), h=60, state="line", moving="retreat")
# McLaws's effort to cross the Pike, checked by Greene and the gun line from Mumma's cemetery north
mv("kershaw", B("09:45"), B("09:55"), (-130, 1560), h=80, state="firing")
fight("kershaw", B("09:55"), B("10:10"), 450)
fight("tyndale", B("08:50"), B("10:20"), 700); fight("stainrook", B("08:50"), B("10:20"), 700)
fight("xii_guns", B("09:10"), B("11:30"), 760)
mv("kershaw", B("10:10"), B("10:30"), (-380, 1450), h=60, state="line", moving="retreat")
fight("barksdale", B("09:45"), B("10:05"), 500); fight("semmes", B("09:50"), B("10:05"), 480)
mv("barksdale", B("10:05"), B("10:30"), (-550, 1700), h=60); mv("semmes", B("10:05"), B("10:30"), (-760, 1760), h=60)
mv("gt_anderson", B("09:45"), B("10:10"), (-350, 1500), h=60); mv("early", B("09:45"), B("10:10"), (-750, 1650), h=60)
# Manning against Greene about ten, and back
mv("manning", B("10:00"), B("10:10"), (-30, 1430), h=70, moving="charge", state="firing")
fight("manning", B("10:10"), B("10:20"), 1050)
mv("manning", B("10:20"), B("10:40"), (-330, 1300), h=60, state="line", moving="retreat")
mv("ransom", B("09:40"), B("10:10"), (-420, 1560), h=40)
# Greene into the woods west of the church
mv("tyndale", B("10:30"), B("10:50"), (-230, 1390), h=260, state="firing")
mv("stainrook", B("10:30"), B("10:50"), (-200, 1300), h=240, state="firing")
fight("tyndale", B("10:50"), B("12:00"), 600); fight("stainrook", B("10:50"), B("12:00"), 600)

# ---- 17 September, 8 to 1: French and Richardson against the Sunken Road ----
for id, t0, t1, end in (("weber", "08:15", "09:30", (430, 1050)), ("morris", "08:25", "09:45", (420, 1150)), ("kimball", "08:35", "10:00", (440, 1260))):  # in three lines
    mv(id, B(t0), B(t1), (PRYS[0] + 60, PRYS[1]), (PRYS[0] - 60, PRYS[1] + 20), (1500, 1700), (900, 1650), (P['roulette'][0] + 50, P['roulette'][1] + 30), end, h=195, state="firing")
mv("rodes", B("08:30"), B("09:00"), (330, 925), h=10)
mv("gb_anderson", B("09:00"), B("09:40"), (600, 650), (580, 830), h=30)
for id, t0 in (("rodes", "09:30"), ("colquitt", "09:30"), ("garland", "09:30"), ("gb_anderson", "09:45")): stand(id, B(t0), state="firing", h=20)
# R. H. Anderson's division to the Pike south of the lane about nine, then behind the lane and into Piper's cornfield
mv("featherston", B("08:20"), B("09:00"), (-230, -360), (-60, 200), h=20)
mv("pryor", B("08:25"), B("09:10"), (-230, -360), (100, 250), h=20)
mv("wright", B("08:30"), B("09:20"), (-230, -360), (300, 250), h=20)
mv("wilcox", B("08:20"), B("09:10"), (-230, -360), (560, 280), h=20)
mv("featherston", B("10:15"), B("10:40"), (80, 800), h=20, state="firing")
mv("pryor", B("10:15"), B("10:40"), (300, 790), h=20, state="firing")
mv("wright", B("10:15"), B("10:40"), (470, 740), h=20, state="firing")
mv("wilcox", B("10:15"), B("10:45"), (680, 600), h=30, state="firing")
# Richardson over Pry's Ford about 9:30, into the ravine east of Roulette's: Meagher right, Caldwell left, Brooke in reserve
for id, t0, t1, end in (("meagher", "09:15", "10:30", (950, 1300)), ("caldwell", "09:25", "10:45", (1050, 1150)), ("brooke", "09:35", "11:00", (1150, 1300))):
    mv(id, B(t0), B(t1), (PRYS[0] + 60, PRYS[1]), (PRYS[0] - 60, PRYS[1] + 20), (1500, 1450), end, h=220)
mv("meagher", B("10:40"), B("10:55"), (720, 990), h=200, state="firing")
fight("meagher", B("10:55"), B("11:40"), 603)
mv("meagher", B("11:40"), B("11:55"), (820, 1140), h=200)
mv("caldwell", B("11:20"), B("11:40"), (860, 900), h=210, state="firing")
mv("brooke", B("11:30"), B("11:55"), (900, 1050), h=200)
fight("weber", B("09:30"), B("12:00"), 950); fight("morris", B("09:45"), B("12:00"), 1050); fight("kimball", B("10:00"), B("12:00"), 1940)
fight("colquitt", B("09:30"), B("11:50"), 450); fight("garland", B("09:30"), B("11:50"), 480)
fight("rodes", B("09:30"), B("11:50"), 520); fight("gb_anderson", B("09:45"), B("11:55"), 400)
fight("featherston", B("10:40"), B("11:55"), 520); fight("pryor", B("10:40"), B("11:55"), 620)
fight("wright", B("10:40"), B("11:55"), 450); fight("wilcox", B("10:45"), B("11:55"), 520)
# About noon the lane is carried: Rodes goes by a mistaken order, Barlow fires down the lane, the rest back to and beyond Piper's
mv("caldwell", B("11:40"), B("12:05"), (720, 700), h=230, state="firing")
fight("caldwell", B("12:05"), B("12:30"), 1100)
for id, t0, end in (("rodes", "11:50", (150, 330)), ("colquitt", "11:55", (-60, 440)), ("garland", "11:55", (40, 520)), ("gb_anderson", "11:55", (450, 330)),
                    ("featherston", "12:00", (-20, 240)), ("pryor", "12:00", (160, 170)), ("wright", "12:00", (350, 120)), ("wilcox", "12:00", (560, 160))):
    mv(id, B(t0), plus(B(t0), 30), end, h=20, state="line", moving="retreat")
for id, end in (("weber", (420, 960)), ("morris", (420, 1060)), ("kimball", (450, 1160))): mv(id, B("12:05"), B("12:30"), end, h=190, state="firing")
mv("brooke", B("12:10"), B("12:40"), (650, 700), h=200, state="firing")
for id in ("weber", "morris", "kimball", "brooke", "caldwell"): stand(id, B("13:00"), state="line")
for id in ("rodes", "colquitt", "garland", "gb_anderson", "featherston", "pryor", "wright", "wilcox"): fight(id, B("12:30"), B("13:00"), carried(id, "strength") - 40)
# Franklin's VI Corps about noon, Smith's division first; Irwin's charge toward the church fails; Greene out of the church woods
for id, t0, t1, end in (("irwin", "11:15", "12:10", (480, 1560)), ("maine7", "11:15", "12:12", (560, 1600)), ("smith", "11:30", "12:30", (700, 1720)), ("slocum", "12:00", "13:15", (900, 1950))):
    show(id, B(t0), (PRYS[0] + 150, PRYS[1] - 80), 280); mv(id, B(t0), B(t1), (PRYS[0] - 60, PRYS[1] + 20), (1300, 1700), end, h=240)
mv("irwin", B("12:15"), B("12:30"), (120, 1430), h=260, moving="charge", state="firing")
fight("irwin", B("12:30"), B("12:40"), 1450)
mv("irwin", B("12:40"), B("13:00"), (460, 1560), h=260, state="line", moving="retreat")
mv("tyndale", B("12:00"), B("12:30"), (230, 1760), h=230, state="line", moving="retreat")
mv("stainrook", B("12:00"), B("12:30"), (400, 1700), h=230, state="line", moving="retreat")
mv("ransom", B("11:45"), B("12:10"), (-330, 1420), h=60, state="firing"); fight("ransom", B("12:10"), B("12:40"), 1150)
fight("kershaw", B("11:50"), B("12:20"), 440, h=60)

# ---- 17 September, 10 to 1: the Lower Bridge and Snavely's Ford ----
fight("ix_guns_e", B("10:00"), B("13:00"), 280, h=280)
fight("cemetery_guns", B("10:00"), B("15:20"), 330, h=80)
# Pleasonton's cavalry and horse batteries over the Middle Bridge, the guns 880 yards south-east of the tower
MID = P['middle_bridge']
mv("pleasonton", B("10:00"), B("10:30"), (MID[0] + 60, MID[1] + 10), (MID[0] - 60, MID[1] - 10), (1150, 420), h=250)
mv("horse_guns", B("10:00"), B("10:25"), (MID[0] + 60, MID[1] + 10), (MID[0] - 60, MID[1] - 10), (1330, 160), h=250, state="firing")
fight("horse_guns", B("10:25"), B("12:30"), 560)
mv("horse_guns", B("12:30"), B("13:00"), (MID[0] - 60, MID[1] - 10), (MID[0] + 60, MID[1] + 10), (2150, 380), h=250)
# Sykes's regulars over the Middle Bridge after noon; Evans across the Boonsboro Pike against them about one
mv("sykes", B("12:20"), B("13:10"), (MID[0] + 60, MID[1] + 10), (MID[0] - 60, MID[1] - 10), (1120, 60), h=250, state="firing")
mv("evans", B("12:40"), B("13:00"), (660, -90), h=80, state="firing")
fight("sykes", B("13:10"), B("16:20"), 4500); fight("evans", B("13:00"), B("16:00"), 220)
# The 11th Connecticut and Crook about ten; Crook over the ford a few hundred yards above the bridge a little before eleven
mv("harland", B("09:40"), B("10:00"), (1330, -1360), h=225, state="firing")
fight("harland", B("10:00"), B("10:30"), 1330)
mv("harland", B("10:30"), B("10:55"), (1750, -1820), h=200)
mv("crook", B("09:40"), B("10:00"), (1300, -1100), h=260, state="firing")
fight("crook", B("10:00"), B("10:35"), 1370)
mv("crook", B("10:35"), B("10:55"), (1200, -1000), (960, -1000), h=250, state="firing")
fight("crook", B("10:55"), B("13:00"), 1300)
fight("toombs", B("10:00"), B("13:00"), 420, h=80)
# Rodman's division and Ewing's brigade downstream to Snavely's Ford at eleven
SNAV = P['snavely_ford']
mv("fairchild", B("11:00"), B("12:10"), (1800, -2000), (1700, -2330), h=230)
mv("harland", B("11:05"), B("12:15"), (1900, -2050), (1800, -2400), h=230)
mv("ewing", B("11:10"), B("12:20"), (1950, -2000), (1900, -2300), h=230)
# Nagle repulsed at noon; Ferrero's assault from half past twelve, the bridge carried at one
mv("nagle", B("11:40"), B("12:00"), (1260, -1370), h=260, moving="charge", state="firing")
fight("nagle", B("12:00"), B("12:15"), 1300)
mv("nagle", B("12:15"), B("12:35"), (1560, -1240), h=260, state="line", moving="retreat")
mv("ferrero", B("12:10"), B("12:30"), (1260, -1330), h=250, state="firing")
fight("ferrero", B("12:30"), B("12:58"), 1250)
BR = P['burnside_bridge']
mv("ferrero", B("12:58"), B("13:15"), (BR[0] + 40, BR[1] + 10), (BR[0] - 40, BR[1] + 10), (900, -1290), (800, -1240), h=270, moving="charge", state="firing")
mv("nagle", B("13:05"), B("13:35"), (BR[0] + 40, BR[1] + 10), (BR[0] - 40, BR[1] + 10), (850, -1460), h=270)
mv("crook", B("13:05"), B("13:30"), (820, -1140), h=270)
mv("toombs", B("13:00"), B("13:40"), (700, -1200), (100, -1000), h=90, state="line", moving="retreat")
# Rodman over Snavely's Ford about one, Toombs's right driven from it, up the right bank to Sturgis's left
for id, t0, t1, end in (("fairchild", "12:55", "13:50", (700, -1640)), ("harland", "13:05", "14:00", (820, -1880)), ("ewing", "13:15", "14:10", (950, -1760))):
    mv(id, B(t0), B(t1), (SNAV[0] + 60, SNAV[1] + 20), (SNAV[0] - 80, SNAV[1] + 10), (1200, -2300), end, h=280)
for id in ("fairchild", "harland", "ewing"): stand(id, B("14:15"), state="line")

# ---- 17 September, 2 to 6: A. P. Hill, the advance on Sharpsburg, the flank attack ----
# Willcox over the stone bridge at two, relieving Sturgis; four batteries over
mv("christ", B("13:45"), B("14:30"), (BR[0] + 40, BR[1] + 10), (BR[0] - 40, BR[1] + 10), (737, -1006), (650, -900), h=280)
mv("welsh", B("13:50"), B("14:35"), (BR[0] + 40, BR[1] + 10), (BR[0] - 40, BR[1] + 10), (620, -1150), h=280)
mv("ix_guns", B("14:15"), B("14:50"), (BR[0] + 40, BR[1] + 10), (BR[0] - 40, BR[1] + 10), (760, -1090), h=280, state="firing")
mv("ferrero", B("14:30"), B("14:50"), (960, -1330), h=270); mv("nagle", B("14:30"), B("14:50"), (1000, -1450), h=270)
# A. P. Hill's division, out of Harpers Ferry at 7:30, at Boteler's Ford about two and on the Harpers Ferry Road at 2:30
for id, t0, end, h in (("archer", "13:35", (-110, -1520), 80), ("gregg", "13:40", (-110, -1860), 80), ("branch", "13:45", (-150, -2150), 80)):
    show(id, B(t0), FORD, 60); walk(id, B(t0), *FORD_TO_HF[1:], end, h=h, kmh=4.5)
show("rlwalker", B("13:50"), FORD, 60); walk("rlwalker", B("13:50"), *FORD_TO_HF[1:], (-230, -1700), h=80, kmh=4.5)
for id, t0, end in (("pender", "13:55", (700, -2440)), ("field", "14:00", (260, -2630))):
    show(id, B(t0), FORD, 60); walk(id, B(t0), *FORD_TO_HF[1:4], (-600, -2550), end, h=150, kmh=4.5)
# S. D. Lee's guns on the high ground over the Boonsboro Pike at three
mv("sdlee", B("14:40"), B("15:00"), (100, -250), h=80, state="firing")
fight("rlwalker", B("15:10"), B("17:30"), 360)
# At three Willcox, Rodman and the Kanawha Division go forward on Sharpsburg, a mile-wide line
mv("christ", B("15:00"), B("15:35"), (420, -760), h=290, state="firing")
mv("welsh", B("15:00"), B("15:35"), (300, -1000), h=290, state="firing")
mv("fairchild", B("15:00"), B("15:25"), (380, -1320), h=300, state="firing")
mv("harland", B("15:05"), B("15:35"), (470, -1740), h=290, state="firing")
mv("ewing", B("15:10"), B("15:40"), (620, -1640), h=280)
fight("ix_guns", B("15:00"), B("16:30"), 360)
# Jones's brigades on the ridge south of the town, driven back through the streets; the guns leave Cemetery Hill
fight("drayton", B("15:00"), B("15:35"), 220, h=100); fight("kemper", B("15:10"), B("15:35"), 360, h=100)
fight("garnett", B("15:10"), B("15:40"), 360, h=90); fight("jenkins", B("15:00"), B("15:45"), 460, h=90)
mv("cemetery_guns", B("15:20"), B("15:45"), (-420, -250), h=90)
for id, end in (("drayton", (-480, -720)), ("kemper", (-520, -470)), ("garnett", (-470, -300))): mv(id, B("15:40"), B("16:05"), end, h=110, state="line", moving="retreat")
mv("jenkins", B("15:45"), B("16:05"), (-280, -150), h=100, state="line", moving="retreat")
mv("fairchild", B("15:25"), B("15:45"), (-30, -820), h=300, state="firing")
fight("christ", B("15:35"), B("16:20"), 1250); fight("welsh", B("15:35"), B("16:20"), 1200)
mv("colquitt", B("14:20"), B("14:55"), (430, -170), h=80, state="firing"); mv("garland", B("14:20"), B("14:55"), (500, -320), h=80, state="firing")
fight("colquitt", B("14:55"), B("16:15"), 340); fight("garland", B("14:55"), B("16:15"), 380)
# Between half past three and four, Hill's three brigades with Toombs on their left come in from the Harpers Ferry Road
mv("toombs", B("15:20"), B("15:45"), (170, -1330), h=90, state="firing")
mv("archer", B("15:25"), B("15:50"), (220, -1450), h=80, state="firing")
mv("gregg", B("15:25"), B("15:40"), (380, -1760), h=80, state="firing")
mv("branch", B("15:30"), B("15:55"), (300, -1690), h=60, state="firing")
fight("harland", B("15:40"), B("15:55"), 1000); fight("fairchild", B("15:45"), B("16:05"), 850)
mv("harland", B("15:55"), B("16:20"), (900, -1700), h=270, state="line", moving="rout", strength=900)
mv("fairchild", B("16:05"), B("16:35"), (500, -1150), (820, -1400), h=270, state="line", moving="retreat")
mv("ewing", B("15:40"), B("15:50"), (560, -1680), h=250, state="firing"); fight("ewing", B("15:50"), B("16:20"), 1100)
mv("ewing", B("16:20"), B("16:45"), (950, -1800), h=260, state="line", moving="retreat")
# Nagle to Rodman's left checks Hill's right; Ferrero to Willcox's right at Otto's lane
mv("nagle", B("15:50"), B("16:15"), (640, -1930), h=270, state="firing"); fight("nagle", B("16:15"), B("16:45"), 1200)
mv("nagle", B("16:45"), B("17:05"), (960, -1560), h=260)
mv("ferrero", B("15:50"), B("16:15"), (760, -930), h=280)
fight("archer", B("15:50"), B("16:15"), 560); fight("gregg", B("15:40"), B("16:15"), 500); fight("branch", B("15:55"), B("16:15"), 560)
fight("toombs", B("15:45"), B("16:15"), 380)
for id, end in (("archer", (300, -1450)), ("gregg", (420, -1700)), ("branch", (360, -1920))): mv(id, B("16:15"), B("16:30"), end, h=80)
# The whole IX Corps drawn back to the high ground over the Antietam; the cavalry, the horse batteries and the regulars back over the creek
mv("christ", B("16:30"), B("17:00"), (820, -1060), h=280, state="line", moving="retreat")
mv("welsh", B("16:30"), B("17:00"), (860, -1250), h=280, state="line", moving="retreat")
mv("ix_guns", B("16:30"), B("17:00"), (980, -1250), h=280)
mv("ferrero", B("16:40"), B("17:05"), (900, -1120), h=280)
mv("horse_guns", B("14:45"), B("15:15"), (MID[0] + 60, MID[1] + 10), (MID[0] - 60, MID[1] - 10), (1330, 160), h=250, state="firing")
fight("horse_guns", B("15:15"), B("16:30"), 540)
mv("horse_guns", B("16:30"), B("17:00"), (MID[0] - 60, MID[1] - 10), (MID[0] + 60, MID[1] + 10), (2250, 420), h=250)
mv("pleasonton", B("16:30"), B("17:00"), (MID[0] - 60, MID[1] - 10), (MID[0] + 60, MID[1] + 10), (2500, 620), h=250)
mv("sykes", B("16:20"), B("17:10"), (MID[0] - 60, MID[1] - 10), (MID[0] + 60, MID[1] + 10), (2250, 450), h=250)
mv("toombs", B("17:00"), B("17:30"), (-80, -1080), h=90)
fight("sdlee", B("15:00"), B("16:30"), 480)
# About five the 7th Maine charges over the Bloody Lane 450 yards west of the tower, reaches Piper's barn and is driven back
mv("maine7", B("16:30"), B("16:55"), (420, 1080), h=190)
mv("maine7", B("16:55"), B("17:20"), (360, 910), (300, 330), h=190, moving="charge", state="firing")
fight("maine7", B("17:20"), B("17:30"), 120)
mv("maine7", B("17:30"), B("17:55"), (360, 910), (420, 1080), h=190, state="line", moving="retreat")
fight("rodes", B("17:15"), B("17:35"), carried("rodes", "strength") - 10)

# ---- 18 September: the armies lie on their arms; Morell relieves Willcox ----
for id, end in (("christ", (1900, -1100)), ("welsh", (2000, -1250))):
    mv(id, C("08:30"), C("09:40"), (BR[0] - 40, BR[1] + 10), (BR[0] + 40, BR[1] + 10), (1600, -1200), end, h=260)
mv("morell", C("08:00"), C("09:30"), (2000, -500), (1400, -1300), (BR[0] + 40, BR[1] + 10), (BR[0] - 40, BR[1] + 10), (840, -1150), h=280)
# The night of the 18th: Longstreet leads over Boteler's Ford at midnight, the rest after him; Fitz Lee covers and A. P.
# Hill's brigades come last, over about half past nine on the 19th. The order of march is inferred.
GO = ["cobb", "kershaw", "barksdale", "semmes", "armistead", "wilcox", "featherston", "pryor", "wright", "drayton", "kemper", "garnett", "jenkins", "toombs",
      "cemetery_guns", "gt_anderson", "evans", "manning", "ransom", "wofford", "law", "sdlee", "rodes", "colquitt", "garland", "gb_anderson", "ripley",
      "lawton", "hays", "trimble", "early", "jfirst", "jsecond", "shumaker", "pelham", "stuart"]
for n, id in enumerate(GO):
    src = last(id)
    pts = HF_TO_FORD if src[1] < -1000 else ([(-350, 500)] if src[1] > 600 else []) + TOWN_TO_FORD
    hide(id, plus(walk(id, plus(C("23:00"), n * 8), *pts, h=240, kmh=4), 5))
for n, id in enumerate(["archer", "gregg", "branch", "rlwalker", "pender", "field"]):
    walk(id, plus(C("23:59"), n * 10), *HF_TO_FORD[:-1], (-2500 - n * 60, -2620), h=60, kmh=3.5)
    stand(id, E("08:30"), state="line"); hide(id, plus(walk(id, plus(E("08:30"), n * 8), FORD, h=240, kmh=3), 3))
walk("fitzlee", C("23:00"), (-1200, -1500), (-1200, -2600), h=60, kmh=6)
walk("fitzlee", E("06:00"), (-1600, -2700), FORD, h=240, kmh=5); hide("fitzlee", E("07:30"))
# Smith's division goes forward on the morning of the 19th and finds the field empty
walk("smith", E("07:00"), (300, 1500), (-250, 1350), (-450, 1000), h=230, kmh=3)
walk("irwin", E("07:10"), (100, 1300), (-250, 900), h=230, kmh=3)

for id in KEYS:
    if sec(KEYS[id][-1]["t"]) < sec(END): keys(id, [K(END, last(id))])

# ---- assemble and check ----
units = []
TOP = {"infantry": 6, "artillery": 6, "cavalry": 15}  # km/h, the fastest any leg may go
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
        for f in (i / 10 for i in range(1, 10)):
            q = (a["x"] + f * (b["x"] - a["x"]), a["y"] + f * (b["y"] - a["y"]))
            assert not wet(q), (id, a["t"], b["t"], q, "a leg through the river")
    state = None
    for k in ks:
        state = k.get("state", state)
        assert state == "hidden" or not wet((k["x"], k["y"])), (id, k["t"], (k["x"], k["y"]), "in the river")
    units.append(dict(id=id, side=side, name=name, short=short, commander=commander, type=type, strength=strength, keys=ks, **extra))
# Chapters: (time, title, text, camera centre, metres across, playback speed, clock time the sources record or None).
# Times are the War Department tablets' (after Carman), with the Historical Handbook, the Park Service and Wikipedia
# where the tablets are silent; they agree within half an hour except on A. P. Hill's arrival.
CHAPTERS = [
    (A("14:00"), "Hooker crosses the Antietam", "Lee's army stands before Sharpsburg. Longstreet's command crossed the Middle Bridge at noon on the 15th and formed outside the town, its left at Cemetery Hill on the Boonsboro Pike, D. H. Hill on its left. Jackson's and Ewell's divisions came up from Harpers Ferry this morning and form on the left again, from the Hagerstown Pike 250 yards north of the Dunker Church west through the West Woods. At two Hooker's I Corps leaves Keedysville: Doubleday's division by Pry's Ford, Ricketts's and Meade's by the Upper Bridge.", [2300, 2500], 4000, 120, "2 PM"),
    (A("18:00"), "The East Woods at dusk", "About six Meade's division meets Hood's near the East Woods. The I Corps forms facing south and south-west, Meade in the centre, Doubleday on the right, Ricketts on the left. The firing stops about half past six.", [350, 2450], 1600, 60, "about 6 PM"),
    (A("22:00"), "A wet night", "Drizzling rain. Lawton's and Trimble's brigades cross the Pike and relieve Hood's division near the south edge of Miller's Cornfield and in Mumma's field south of the Smoketown Road; Hays bivouacs north-west of the church, Early in the farm lane on Jackson's left. Sedgwick's and French's divisions lie near the army's headquarters at the Pry House, Richardson's behind the bluff over the Antietam. About midnight Greene's division of the XII Corps crosses the Upper Bridge.", [900, 2300], 5500, 300, "about 10 PM"),
    (B("05:30"), "Hooker attacks", "The morning breaks gray and misty. Doubleday's division moves to the attack at half past five, Gibbon's Iron Brigade leading down the Pike, Phelps and Patrick behind it, Hofmann in reserve; Seymour's brigade of Meade's division opens on Lawton's. Hooker's guns are on the ridge by Joseph Poffenberger's, and the heavy rifles east of the creek fire into Jackson's line from the flank. Some 8,600 Union men against about 7,700. The sun rises at 5:43.", [-100, 2450], 1700, 60, "5:30 AM"),
    (B("06:00"), "The Cornfield", "Ricketts forms at six, Hartsuff leading, and goes in to the west edge of the East Woods and the south edge of the Cornfield. Doubleday's brigades strike Lawton's left. Jackson's skirmishers behind a ledge west of the Pike fire into Gibbon's flank, and Gibbon and Patrick deploy west of the road with Campbell's battery. Hays crosses the Pike north of the church with 550 men, fills the gap between Lawton and Trimble, pushes into the Cornfield and loses more than half. Grigsby's first line fights over half an hour and falls back 380 yards to the edge of the woods.", [-50, 2150], 1400, 30, "6 AM"),
    (B("06:30"), "Starke at the Pike fence", "Meade forms about half past six, Seymour's brigade on the left and forward, Magilton's and Anderson's filling the gap between Doubleday and Ricketts. Starke's second line goes forward to the Pike fence and is shot down from the flank; Starke is killed, and Jackson's Division falls back into the West Woods. Ripley's brigade fires the Mumma buildings and crosses the Smoketown Road toward the Cornfield, Colquitt's and Garland's behind it.", [-150, 1950], 1400, 30, "about 6:30 AM"),
    (B("07:00"), "Hood's counterattack", "About seven Hood's division crosses the Pike north of the church and relieves Lawton, Hays and Trimble: Wofford's Texas Brigade along the Pike, Law's into the East Woods. It reaches the north edge of the Cornfield and the east edge of the woods, is checked and goes back, having lost 60 percent. Lawton's and Hays's remnants withdraw south-west of the church. Early, back from supporting Stuart's guns, turns Gibbon's and Patrick's flank with Grigsby's 200 and drives them back to Miller's barn.", [0, 2050], 1400, 30, "about 7 AM"),
    (B("07:30"), "Mansfield's corps", "Williams's division of the XII Corps formed near the North Woods at seven, Gordon on the right, Crawford across the Smoketown Road. Mansfield is mortally wounded at the edge of the East Woods while deploying them, and Hooker is wounded. Doubleday's brigades withdraw to the fields north of Miller's after more than an hour; Hooker's corps has lost about 2,500 in two hours. Lee sends G. T. Anderson's brigade from Evans to the left, and Sedgwick's division starts from the Pry House for Pry's Ford.", [150, 2350], 1600, 60, "7:30 AM"),
    (B("08:00"), "Greene to the Dunker Church", "About eight Greene's two small brigades, about 1,700 men, form north-west of the Smoketown Road, Tyndale's on the right and Stainrook's on the left. They turn the Confederate right in the East Woods, cross the road and press on to the Mumma ridge opposite the church. Ripley goes back to the West Woods, Colquitt and Garland toward the Sunken Road. S. D. Lee's batteries, on the ridge east of the church since daybreak, leave it about a quarter past eight, and Walker's division sets out from the bridge sector for the church.", [150, 1800], 1500, 60, "about 8 AM"),
    (B("09:00"), "Sedgwick in the West Woods", "Sedgwick's division, Gorman's, Dana's and Howard's brigades in three lines, crosses the Pike about a third of a mile north of the church into the West Woods. McLaws, over Boteler's Ford at daybreak, deploys about nine from the Pike opposite the Sunken Road to north-west of the Hauser house. With Walker's division, G. T. Anderson and Stuart he strikes Sedgwick's left and front and drives the division north beyond Miller's. In less than twenty minutes nearly half of Sedgwick's 5,000 are struck down.", [-450, 1950], 1000, 20, "about 9 AM"),
    (B("09:30"), "French at the Sunken Road", "French's division, over Pry's Ford about half past eight, wheels left at the East Woods, drives the outposts from the Roulette buildings and about half past nine engages Rodes, Colquitt and Garland in the west end of the Sunken Road, a farm lane worn into a trench, its bank piled with fence rails. G. B. Anderson's brigade comes up a ravine from the Boonsboro Pike onto Rodes's right. Richardson's division crosses Pry's Ford. North of the church, McLaws's push over the Pike is checked by Greene and the guns from Mumma's cemetery north.", [400, 1100], 1400, 30, "about 9:30 AM"),
    (B("10:00"), "The first try at the bridge", "Burnside has the order to attack. A little before ten the 11th Connecticut and Crook's brigade try the Lower Bridge, twelve feet wide, under Toombs's Georgians in rifle pits on the bluff 80 feet above the west bank, and fail. Toombs has the 2nd and 20th Georgia, about 400 muskets each, and fewer than 120 of the 50th. Near the church Manning's brigade attacks Greene.", [1150, -1250], 1300, 30, "about 10 AM"),
    (B("10:30"), "Anderson's division and the Irish Brigade", "French's brigades go at the lane 'with parade-like precision'. Lee sends R. H. Anderson's division, 3,400 men, to D. H. Hill; it forms behind the lane, its left at the Pike and its right in the ravine 300 yards east of Piper's stone barn, and attacks into Piper's cornfield. Richardson forms in the ravine east of Roulette's, Meagher's Irish Brigade on the right, Caldwell's on the left, Brooke's in reserve, and goes in on French's left. The Irish Brigade loses 540 men.", [450, 950], 1300, 30, "about 10:30 AM"),
    (B("11:00"), "Downstream to Snavely's Ford", "Rodman's division and Ewing's brigade are sent down the creek toward Snavely's Ford, nearly a mile below the bridge past a sharp bend. A little before eleven Crook gets over at a ford a few hundred yards above the bridge.", [1400, -1850], 1800, 60, "about 11 AM"),
    (B("12:00"), "Bloody Lane", "At the lane Caldwell's brigade goes in, Rodes's brigade leaves the lane on a mistaken order, and Barlow's men fire down its length. About noon French and Richardson carry the Bloody Lane, and its defenders go back to and beyond Piper's. Some 5,600 men have fallen there, 3,000 Union and 2,600 Confederate. Franklin's VI Corps comes up about noon, Smith's division first; Irwin's brigade charges toward the church and fails, and Greene is driven out of the woods by the church.", [450, 850], 1100, 30, "about noon"),
    (B("12:30"), "Ferrero's charge", "Nagle's brigade, the 2nd Maryland and 6th New Hampshire leading, was thrown back from the bridge at noon. At half past twelve Ferrero's brigade, the 51st New York and the 51st Pennsylvania, begins its assault.", [1150, -1330], 1100, 30, "12:30 PM"),
    (B("13:00"), "Over the bridge", "At one Ferrero's brigade carries the bridge, and Sturgis's division and Crook's brigade cross and take the high ground beyond; the fight there costs some 600 men. Rodman crosses at Snavely's Ford about one and drives Toombs's right from it. Toombs, out of ammunition, falls back to the edge of the town. Evans deploys across the Boonsboro Pike against Sykes's regulars, over the Middle Bridge. At the lane, both sides halt, exhausted.", [950, -1450], 1700, 60, "1 PM"),
    (B("14:30"), "A. P. Hill comes up", "A. P. Hill's division left Harpers Ferry at half past seven and has marched 17 miles in seven hours; hundreds fell out on the way. It is at Boteler's Ford about two, and by the tablet on the Harpers Ferry Road at half past two. Pender's and Field's brigades are sent to cover the lower Antietam; Branch's, Gregg's and Archer's form along the road on D. R. Jones's right. The IX Corps has taken nearly two hours to cross, re-form and draw ammunition. Willcox's division crossed the bridge at two and relieves Sturgis, and four batteries cross.", [-500, -2150], 3500, 60, "2:30 PM"),
    (B("15:00"), "The advance on Sharpsburg", "At three Willcox's, Rodman's and the Kanawha divisions go forward on Sharpsburg in a line a mile wide, over 8,000 men and 22 guns: Willcox up the road, Rodman over the hill on his left, Fairchild's brigade on the right and Harland's in echelon on the left, Ewing's in support. Willcox's skirmishers reach the town and the Confederate guns leave Cemetery Hill. Fairchild drives D. R. Jones's right back through the streets; his 9th New York loses 63 percent. About 2,500 Confederates hold the ridge; Evans, with the remnants of Colquitt's and Garland's brigades, joins Jones.", [250, -1050], 1800, 30, "3 PM"),
    (B("15:40"), "Hill strikes the flank", "The sources put it from half past three to four. Hill's three brigades, Toombs on their left, cross the fields from the Harpers Ferry Road and strike Harland's two regiments in the 40-acre cornfield and the Kanawha line; Gregg's brigade falls on the 16th Connecticut. Rodman is mortally wounded and Branch is killed. Nagle's brigade, sent to Rodman's left, checks Hill's right, and Ferrero's goes to Willcox's right at Otto's lane.", [400, -1500], 1400, 30, "between 3:30 and 4 PM"),
    (B("17:00"), "Back to the creek", "The IX Corps is drawn back to the high ground over the Antietam, and Pleasonton's cavalry, his horse batteries and the regulars on the Boonsboro Pike go back over the creek. About five the 7th Maine charges across the Bloody Lane 450 yards west of the tower, reaches Piper's barn and is driven back. By half past five the battle is over, and with sunset, at 6:06, the firing dies away.", [600, -300], 3000, 60, "about 5 PM"),
    (C("09:00"), "The next day", "The armies lay on their arms through the night, and Lee held a council at his headquarters west of the town. Today he gives up a plan against the Union right after seeing the guns on the Poffenberger ridge. McClellan does not attack. Morell's division relieves Willcox's over the bridge.", [700, 300], 6000, 300, "the next morning"),
    (D(19, "00:00"), "Over the Potomac", "At midnight Longstreet leads the way across Boteler's Ford, Fitz Lee's cavalry covering the withdrawal. McLaws's division, on the field until now, recrosses tonight, and A. P. Hill's brigades fall back at midnight as the rear guard.", [-1500, -1500], 6500, 300, "midnight"),
    (E("09:00"), "The last brigade over", "Hill's rear guard recrosses about half past nine. Smith's division of the VI Corps goes forward and finds the field empty.", [-1700, -1500], 6500, 120, "about 9:30 AM"),
]
events = [dict(t=t, title=a, text=b, at=at_, view=v, speed=s, **({"when": w} if w else {})) for t, a, b, at_, v, s, w in CHAPTERS]
for e in events:  # without `when` the card speaks the nearest hour (app.js chapterWhen), so it must be near the frame's clock
    s = sec(e["t"]) % 86400; hh = [n % 12 or 12 for n in (int(s // 3600), int(s // 3600) + 1)]; num = re.search(r"\d+", e.get("when", ""))
    assert not num or int(num[0]) in hh, (e["t"], e["when"], "the card's hour is not the frame's")
    assert "when" in e or abs(s - math.floor(s / 3600 + 0.5) * 3600) <= 15 * 60, (e["t"], e["title"], "give it a when")
    assert e["speed"] in (1, 2, 5, 10, 20, 30, 60, 120, 300, 600, 1800, 3600, 7200), (e["title"], e["speed"], "not a speed the menu offers (sim.js SPEEDS)")

battle = dict(
    id="antietam", name="Antietam", date="1862-09-17", dateText="16 to 19 September 1862", place="Sharpsburg, Maryland",
    origin=dict(lat=LAT0, lon=LON0), extent=9000, start=START, end=END, sunrise="05:43", sunset="18:06", speed=60, lapse=7200, menPerDot=20,
    water=WATER, terrainExaggeration=2, contourInterval=10, trees=dict(density=0.0004), fields=FIELDS, wind=dict(x=0.5, y=0.3), view=dict(x=300, y=300, width=9000),
    # Bachelder's convention, Union blue and Confederate red
    sides=dict(union=dict(name="Union (McClellan)", color="#2c4f96", light="#6f8fca", dark="#16294f"),
               confederate=dict(name="Confederate (Lee)", color="#b23a2e", light="#d77a6c", dark="#5c1a14")),
    tints=[dict(color="rgba(150,156,164,0.35)", **{"from": A("19:30"), "until": B("05:00")}),   # the drizzle of the night of the 16th
           dict(color="rgba(214,218,222,0.4)", **{"from": B("05:00"), "until": B("06:30")})],  # the gray, misty morning, clearing early
    features=features, units=units, events=events,
    outcome={"result": "Lee held his ground on the 17th and recrossed the Potomac on the night of the 18th", "losses": [
        ["union", "12,410 by Sears: 2,108 killed, 9,549 wounded, 753 missing, a quarter of the force. McClellan's return of 29 September gives 12,469. Mansfield, Richardson and Rodman killed or mortally wounded; Hooker, Sedgwick and Ricketts among the wounded."],
        ["confederate", "10,316 by Sears's estimate: 1,546 killed, 7,752 wounded, 1,018 missing, 31 percent. Starke, Branch and G. B. Anderson killed or mortally wounded; Lawton, J. R. Jones, Ripley, Rodes, R. H. Anderson and Toombs among the wounded."]],
        "note": "About 72,000 Union troops were available on the 17th, by Hartwig's count, against about 37,600 Confederates. Close to 13,000 men fell in the morning alone, and about 5,600 at the Sunken Road."},
    sources=[
        "Antietam Battlefield Board, the War Department tablets (1890s), written from Ezra Carman's reconstruction, read as transcribed at <a href='https://antietam.stonesentinels.com/' target='_blank'>antietam.stonesentinels.com</a>: the clock times, the order of the brigades and the yardages, from Hooker's crossing on the 16th to A. P. Hill's rear guard on the 19th.",
        "<i>The War of the Rebellion: Official Records</i>, Series I, vol. 19, part 1 (1887), in the Internet Archive scan: McClellan's strengths and returns, the Confederate return, and the reports of Early, D. H. Hill, Toombs and Williams for the strengths of Lawton's, Hays's and Trimble's brigades, Toombs's muskets at the bridge and Greene's 1,700.",
        "Frederick Tilberg, <i>Antietam National Battlefield Site</i>, National Park Service Historical Handbook 31 (1960, rev. 1961): the weather, the Cornfield, Sedgwick's losses, the Sunken Road, the Lower Bridge and Snavely's Ford, Hill's march and the withdrawal. National Park Service, Antietam: the Final Attack Trail timeline, 'Burnside Bridge' and 'The Final Attack'. American Battlefield Trust, 'Antietam, Final Assault'.",
        "Wikipedia, <a href='https://en.wikipedia.org/wiki/Battle_of_Antietam' target='_blank'>Battle of Antietam</a> and the Union and Confederate orders of battle (read 24 October 2026), for D. Scott Hartwig's strengths (<i>I Dread the Thought of the Place</i>, 2023) and Stephen Sears's losses (<i>Landscape Turned Red</i>, 1983). Neither book, nor Carman's manuscript, nor the Carman-Cope atlas of 1904 and 1908 was consulted.",
        "Terrain: USGS 3DEP elevation at 10 m, sampled to 22.5 m. Farms, the church, the bridges, monuments and the places where generals fell, the roads, Antietam Creek and the Sunken Road from OpenStreetMap (ODbL); the park avenues, the National Cemetery and the railway are later and not drawn. Sunrise and sunset from the NOAA solar formulae for Sharpsburg, local mean time.",
        "What is reconstructed: the three woods are boxes drawn from the tablets' landmarks, not the 1862 outlines, which are on the Carman-Cope base sheet; the fences and stone walls along the Pike and the Harpers Ferry Road follow the road, not the sheet. Pry's and Snavely's fords are placed from distances and the creek's bends, within 200 to 300 m. Boteler's Ford keeps the note's longitude on the Potomac as the elevation model draws it; the note's latitude put it 800 m south of the river. The roads between the ford and the town are inferred. Positions between the tablets' times are inferred, as is every brigade strength the sources do not give: those are a division's or corps's total shared by regiments. A. P. Hill's arrival runs from 2:30 to 4 in the sources; this replay has him on the Harpers Ferry Road at 2:30 and attacking about 3:40. The 7th Maine's strength is a guess. Humphreys's division, which came up on the 18th, and Couch's, which never reached the field, are left out.",
    ],
)
json.dump(battle, open(HERE + "battle.json", "w"), indent=1)
print(len(units), "units,", len(events), "events,", len(features), "features,", len(FIELDS), "fields,",
      sum(u["strength"] for u in units if u["side"] == "union"), "Union,", sum(u["strength"] for u in units if u["side"] == "confederate"), "Confederate")
# Which units each chapter's frame holds at its moment, so a caption never names a unit the camera leaves out.
def where(u, t):
    ks = [k for k in u["keys"] if sec(k["t"]) <= sec(t)]
    if not ks or next((k["state"] for k in reversed(ks) if "state" in k), None) == "hidden": return None
    k = ks[-1]; nxt = [k2 for k2 in u["keys"] if sec(k2["t"]) > sec(t)]
    if nxt and (k["x"], k["y"]) != (nxt[0]["x"], nxt[0]["y"]):
        f = (sec(t) - sec(k["t"])) / (sec(nxt[0]["t"]) - sec(k["t"])); return (k["x"] + f * (nxt[0]["x"] - k["x"]), k["y"] + f * (nxt[0]["y"] - k["y"]))
    return (k["x"], k["y"])
for e in events:
    r = e["view"] / 2; inside = [u["id"] for u in units if (p := where(u, e["t"])) and abs(p[0] - e["at"][0]) <= r and abs(p[1] - e["at"][1]) <= r]
    print(f"{e['t']} {e['title']}: {' '.join(inside)}")
