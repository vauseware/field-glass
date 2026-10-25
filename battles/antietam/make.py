# Builds battles/antietam/battle.json. Run from the repo root: python3 battles/antietam/make.py
# Local metres from 39.4630N 77.7450W (x east, y north). The 9 km square holds Joseph Poffenberger's farm and the I Corps
# gun line in the north, the Cornfield, the three woods and the Dunker Church, the Sunken Road, Sharpsburg, the three
# bridges over Antietam Creek, Snavely's Ford, the Pry House east of the creek and Boteler's Ford on the Potomac in the
# south-west, where McLaws, Anderson and A. P. Hill crossed and Lee's army recrossed. Every place is kept in latitude and
# longitude below and converted once. Farms, the church, bridges, monuments and death sites are OpenStreetMap points; the
# roads, the creek and the Sunken Road are OpenStreetMap ways on their 1862 lines. Pry's, Snavely's and Boteler's fords
# are placed from distances and the creek's bends, within 200 to 300 m, and labelled "about here". The woods are the
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
    'prys_ford': (39.4760, -77.7170), 'snavely_ford': (39.4414, -77.7284), 'boteler_ford': (39.4300, -77.7807),
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
    dict(name="Boteler's Ford (about here)", at=[P['boteler_ford'][0] + 260, P['boteler_ford'][1] + 80]),
    dict(name="Sharpsburg", at=[P['sharpsburg'][0] - 260, P['sharpsburg'][1] + 40]),
    dict(name="Cemetery Hill", at=[P['cemetery_hill'][0] + 60, P['cemetery_hill'][1] + 80]),
    dict(name="Nicodemus Heights", at=[NICODEMUS[0], NICODEMUS[1] + 90]), dict(name="Hauser Ridge", at=[HAUSER[0], HAUSER[1] - 90]),
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
    ("irwin", "union", "Irwin", "Irwin's brigade of Smith's division", "Col. William Irwin", "infantry", 1977, {}),
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
    # D. H. Hill's division: "less than 5,000" for both Maryland battles; drawn as 4,500, 196 to a regiment
    ("ripley", "confederate", "Ripley", "Ripley's brigade: 4th, 44th Georgia, 1st, 3rd North Carolina", "Brig. Gen. Roswell Ripley (wounded)", "infantry", 780, {}),
    ("rodes", "confederate", "Rodes", "Rodes's Alabama brigade: 3rd, 5th, 6th, 12th, 26th Alabama", "Brig. Gen. Robert Rodes (wounded)", "infantry", 980, {}),
    ("garland", "confederate", "Garland", "Garland's brigade, under McRae: 5th, 12th, 13th, 20th, 23rd North Carolina", "Col. Duncan McRae", "infantry", 980, {}),
    ("gb_anderson", "confederate", "G. B. Anderson", "G. B. Anderson's brigade: 2nd, 4th, 14th, 30th North Carolina", "Brig. Gen. George B. Anderson (mortally wounded)", "infantry", 780, {}),
    ("colquitt", "confederate", "Colquitt", "Colquitt's brigade: 13th Alabama, 6th, 23rd, 27th, 28th Georgia", "Col. Alfred Colquitt", "infantry", 980, {}),
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
    have += ks
def last(id): k = KEYS[id][-1]; return (k["x"], k["y"])
def appear(id, t, p, h, state="line", **kw): keys(id, [K(t, p, h=h, state=state, **kw)])

# Where each unit stands at two in the afternoon of the 16th; those still on the march are hidden.
HIDDEN = {"slocum", "smith", "irwin", "kershaw", "cobb", "semmes", "barksdale", "wilcox", "featherston", "pryor", "wright", "armistead",
          "branch", "gregg", "archer", "pender", "field", "rlwalker", "crawford", "gordon", "tyndale", "stainrook", "goodrich", "xii_guns"}
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
    "stuart": ((-1400, 2700), 60), "fitzlee": ((-1900, 2200), 60), "pelham": (NICODEMUS, 60),
}
for id in BASE:
    if id in HIDDEN: appear(id, START, (4400, 0), 270, state="hidden")
    else: p, h = AT_START[id]; appear(id, START, p, h)
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
events = []

battle = dict(
    id="antietam", name="Antietam", date="1862-09-17", dateText="16 to 19 September 1862", place="Sharpsburg, Maryland",
    origin=dict(lat=LAT0, lon=LON0), extent=9000, start=START, end=END, sunrise="05:43", sunset="18:06", speed=60, lapse=7200, menPerDot=20,
    water=WATER, terrainExaggeration=2, contourInterval=10, trees=dict(density=0.0004), fields=FIELDS, wind=dict(x=0.5, y=0.3), view=dict(x=300, y=300, width=9000),
    # Bachelder's convention, Union blue and Confederate red
    sides=dict(union=dict(name="Union (McClellan)", color="#2c4f96", light="#6f8fca", dark="#16294f"),
               confederate=dict(name="Confederate (Lee)", color="#b23a2e", light="#d77a6c", dark="#5c1a14")),
    features=features, units=units, events=events,
    sources=[],
)
json.dump(battle, open(HERE + "battle.json", "w"), indent=1)
print(len(units), "units,", len(events), "events,", len(features), "features,", len(FIELDS), "fields,",
      sum(u["strength"] for u in units if u["side"] == "union"), "Union,", sum(u["strength"] for u in units if u["side"] == "confederate"), "Confederate")
