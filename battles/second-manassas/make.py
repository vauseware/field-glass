# Builds battles/second-manassas/battle.json. Run from the repo root: python3 battles/second-manassas/make.py
# Local metres from 38.8180N 77.5300W (x east, y north). The 9 km square holds the Brawner farm (-3046,-521) and Stony
# Ridge in the west, the unfinished railroad from the Brawner farm to Sudley Church (-698,2521), Groveton, the Dogan
# farm, Chinn Ridge, Henry Hill, the Stone House (341,88), Buck Hill and the Stone Bridge (2278,706) over Bull Run.
# Gainesville, Thoroughfare Gap, Dawkins Branch, Centreville and Manassas Junction are outside it. Every place is kept in
# latitude and longitude below and converted once. Houses, monuments, hills and the railroad grade are OpenStreetMap and
# GNIS points and ways named in the research note; the roads (US 29 on the Warrenton Turnpike, VA 234 on the
# Manassas-Sudley road) and the streams are OpenStreetMap ways, simplified to 8 m and 15 m. Lewis Lane, Lewis Ford and
# Portici are placed from the narrative and labelled "about here". The woods are drawn from the note's descriptions,
# not from an 1862 map. Quarries the DEM shows on the turnpike east of Bull Run, north of Sudley and at the south edge
# are filled.
import json, math, re, datetime as dt
HERE = "battles/second-manassas/"
LAT0, LON0 = 38.8180, -77.5300
KX, KY = 111320 * math.cos(math.radians(LAT0)), 111320  # tools/fetch_terrain.py's metres per degree
def M(lat, lon): return (round((lon - LON0) * KX), round((lat - LAT0) * KY))

# ---- terrain: fill the modern quarries with a smooth (harmonic) surface from their rims ----
T = json.load(open(HERE + "terrain.json"))
COLS, SP = T["cols"], T["spacing"]; HALF = COLS * SP / 2
QUARRIES = [(2768, -34, 3868, 1316), (-1020, 3216, -482, 3916), (-232, -4480, 1268, -3534)]  # x0, y0, x1, y1 in metres
def fill(x0, y0, x1, y1):
    Z = T["z"]; c0, c1 = int((x0 + HALF) / SP), int((x1 + HALF) / SP); r0, r1 = int((HALF - y1) / SP), int((HALF - y0) / SP)
    rim = [Z[r * COLS + c] for r in (r0, r1) for c in range(c0, c1 + 1)] + [Z[r * COLS + c] for c in (c0, c1) for r in range(r0, r1 + 1)]
    v = {(r, c): sum(rim) / len(rim) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)}
    get = lambda r, c: v.get((r, c), Z[r * COLS + c])
    for _ in range(3000):  # over-relaxed Gauss-Seidel; the result depends only on the rim, so a second run changes nothing
        worst = 0
        for (r, c), old in v.items():
            new = old + 1.9 * ((get(r - 1, c) + get(r + 1, c) + get(r, c - 1) + get(r, c + 1)) / 4 - old); v[(r, c)] = new; worst = max(worst, abs(new - old))
        if worst < 1e-4: break
    for (r, c), val in v.items(): Z[r * COLS + c] = round(val, 1)
before = list(T["z"])
for q in QUARRIES: fill(*q)
assert min(T["z"]) > 0.1, min(T["z"])  # the page draws exactly 0 as missing data
if T["z"] != before: json.dump(T, open(HERE + "terrain.json", "w"), separators=(",", ":"))
def z(x, y):
    c, r = int((x + HALF) / SP), int((HALF - y) / SP)
    return T["z"][r * COLS + c] if 0 <= c < COLS and 0 <= r < COLS else 999

# ---- geography: places ----
PLACES = {
    # OpenStreetMap and GNIS, the ids in the research note
    'brawner': (38.81332, -77.56514), 'stony_guns': (38.81742, -77.55973), 'battery_heights': (38.81186, -77.55720),
    'monument': (38.82084, -77.55397), 'deep_cut_trail': (38.81968, -77.55448), 'dump': (38.82287, -77.55178),
    'stop6': (38.82570, -77.54859), 'groveton': (38.81261, -77.54832), 'dogan': (38.81297, -77.54907),
    'brooklyn14': (38.81295, -77.54626), 'ny5': (38.81039, -77.54387), 'ny10': (38.80986, -77.54415),
    'chinn_ridge': (38.80946, -77.53268), 'texas_mon': (38.80996, -77.53205), 'webster': (38.81011, -77.53196),
    'chinn_house': (38.80620, -77.53460), 'bald_hill': (38.80789, -77.52666), 'henry_house': (38.81482, -77.52266),
    'henry_hill': (38.81322, -77.52130), 'robinson': (38.81878, -77.51913), 'stone_house': (38.81879, -77.52606),
    'buck_hill': (38.82522, -77.52964), 'matthews_hill': (38.82515, -77.53210), 'sudley_church': (38.84067, -77.53805),
    'sudley_ford': (38.84234, -77.53703), 'stone_bridge': (38.82434, -77.50372), 'stuarts_hill': (38.79900, -77.57194),
    'mount_pone': (38.79428, -77.53638),
    # from the narrative and the Park Service marker; 200 to 500 m
    'portici': (38.80625, -77.50840), 'lewis_ford_note': (38.806, -77.498),
}
P = {k: M(*v) for k, v in PLACES.items()}

# ---- geography: lines (OpenStreetMap ways, simplified to 8 m; the streams to 15 m) ----
LINES_LL = {
    'pike': [(38.80376, -77.58246), (38.80583, -77.57379), (38.80936, -77.56111), (38.81013, -77.55905), (38.81061, -77.55723), (38.81483, -77.54091), (38.81723, -77.53106), (38.82213, -77.51248), (38.83004, -77.47754)],
    'sudley_rd': [(38.84235, -77.53864), (38.84104, -77.53766), (38.83622, -77.53700), (38.83355, -77.53567), (38.83207, -77.53540), (38.82971, -77.53552), (38.82883, -77.53535), (38.82429, -77.53306), (38.82362, -77.53221), (38.82237, -77.52969), (38.81832, -77.52667), (38.81021, -77.52309), (38.80356, -77.52089), (38.79742, -77.51812), (38.78146, -77.51166)],
    'featherbed': [(38.81276, -77.54893), (38.82466, -77.54911), (38.82545, -77.54888), (38.82640, -77.54899), (38.82704, -77.54886), (38.82790, -77.54823), (38.82871, -77.54718), (38.82953, -77.54541), (38.83105, -77.54430), (38.83372, -77.54350), (38.84029, -77.54104), (38.84039, -77.54086), (38.84050, -77.53883), (38.84130, -77.53777)],
    'groveton_rd': [(38.81276, -77.54893), (38.81178, -77.54873), (38.80937, -77.54910), (38.80318, -77.54894), (38.80078, -77.54913), (38.79868, -77.54895), (38.79787, -77.54938), (38.79668, -77.55107), (38.79630, -77.55141), (38.79539, -77.55160), (38.79429, -77.55153)],
    'pageland': [(38.85384, -77.57090), (38.85137, -77.57153), (38.84953, -77.57282), (38.84855, -77.57325), (38.84150, -77.57515), (38.84049, -77.57505), (38.83943, -77.57450), (38.83857, -77.57357), (38.83747, -77.57167), (38.83695, -77.57127), (38.83639, -77.57110), (38.82907, -77.57103), (38.82793, -77.57115), (38.82678, -77.57158), (38.82484, -77.57311), (38.82393, -77.57344), (38.82331, -77.57339), (38.82144, -77.57251), (38.82048, -77.57234), (38.81039, -77.57290), (38.80468, -77.57348)],
    'railroad': [(38.81131, -77.58246), (38.81938, -77.55773), (38.82072, -77.55476), (38.82181, -77.55303), (38.82377, -77.55068), (38.82584, -77.54863), (38.83103, -77.54231), (38.83178, -77.54156), (38.83268, -77.54082), (38.83554, -77.53891), (38.83904, -77.53720), (38.84674, -77.52972)],
    'bull_run': [(38.85887, -77.55155), (38.85741, -77.55178), (38.85626, -77.55248), (38.85404, -77.54776), (38.85317, -77.54731), (38.85094, -77.54860), (38.84902, -77.55037), (38.84666, -77.54940), (38.84661, -77.54898), (38.84699, -77.54811), (38.84634, -77.54745), (38.84625, -77.54702), (38.84677, -77.54569), (38.84770, -77.54545), (38.84800, -77.54655), (38.84824, -77.54689), (38.84868, -77.54695), (38.84880, -77.54635), (38.85002, -77.54524), (38.85023, -77.54451), (38.84981, -77.54309), (38.84907, -77.54183), (38.84778, -77.53857), (38.84782, -77.53720), (38.84714, -77.53510), (38.84666, -77.53491), (38.84434, -77.53644), (38.84252, -77.53707), (38.84076, -77.53628), (38.83931, -77.53486), (38.83880, -77.53280), (38.83705, -77.52993), (38.83745, -77.52796), (38.83700, -77.52360), (38.83714, -77.52270), (38.84004, -77.51499), (38.84062, -77.51235), (38.84139, -77.51111), (38.84145, -77.50955), (38.84092, -77.50861), (38.84029, -77.50832), (38.83987, -77.50883), (38.83927, -77.50877), (38.83763, -77.50760), (38.83721, -77.50758), (38.83667, -77.50817), (38.83667, -77.51005), (38.83637, -77.51075), (38.83545, -77.51108), (38.83432, -77.51059), (38.83355, -77.51056), (38.83249, -77.51096), (38.83118, -77.51220), (38.83040, -77.51237), (38.82942, -77.51130), (38.82518, -77.50352), (38.82417, -77.50378), (38.82242, -77.50517), (38.82195, -77.50504), (38.81979, -77.50605), (38.81859, -77.50548), (38.81624, -77.50514), (38.81456, -77.50246), (38.81371, -77.50055), (38.81327, -77.49719), (38.81136, -77.49116), (38.80890, -77.48928), (38.80556, -77.48990), (38.80041, -77.49426), (38.79893, -77.49432), (38.79762, -77.49376), (38.79753, -77.49097), (38.79654, -77.48686), (38.79715, -77.48489), (38.79709, -77.48296), (38.79646, -77.48082), (38.79683, -77.48033), (38.79807, -77.48038), (38.79892, -77.47986), (38.79914, -77.47939), (38.79925, -77.47754)],
    'youngs': [(38.81278, -77.56692), (38.80936, -77.56652), (38.80751, -77.56497), (38.80681, -77.56375), (38.80630, -77.56346), (38.80587, -77.56203), (38.80472, -77.56036), (38.80459, -77.55915), (38.80407, -77.55843), (38.80453, -77.55790), (38.80441, -77.55730), (38.80349, -77.55581), (38.80278, -77.55547), (38.80256, -77.55408), (38.80200, -77.55347), (38.80181, -77.55168), (38.80203, -77.55059), (38.80164, -77.54974), (38.80166, -77.54833), (38.80286, -77.54599), (38.80412, -77.54583), (38.80570, -77.54427), (38.80676, -77.54418), (38.80731, -77.54346), (38.80817, -77.54339), (38.80935, -77.54273), (38.80937, -77.54238), (38.81014, -77.54240), (38.81088, -77.54113), (38.81255, -77.54051), (38.81286, -77.53975), (38.81447, -77.53879), (38.81418, -77.53736), (38.81431, -77.53705), (38.81356, -77.53535), (38.81366, -77.53419), (38.81448, -77.53259), (38.81493, -77.53256), (38.81546, -77.53212), (38.81607, -77.53213), (38.81659, -77.53162), (38.81665, -77.53109), (38.81718, -77.53032), (38.81777, -77.52873), (38.81776, -77.52674), (38.81808, -77.52505), (38.81842, -77.52458), (38.81917, -77.52451), (38.81956, -77.52383), (38.82047, -77.52390), (38.82128, -77.52344), (38.82201, -77.52340), (38.82240, -77.52307), (38.82256, -77.52242), (38.82321, -77.52194), (38.82412, -77.51914), (38.82387, -77.51689), (38.82349, -77.51600), (38.82307, -77.51605), (38.82239, -77.51524), (38.82182, -77.51506), (38.82015, -77.51192), (38.81925, -77.51168), (38.81885, -77.51207), (38.81794, -77.51110), (38.81774, -77.51016), (38.81815, -77.50751)],
    'dogans': [(38.82240, -77.56063), (38.82050, -77.55887), (38.82028, -77.55806), (38.81885, -77.55709), (38.81826, -77.55614), (38.81771, -77.55585), (38.81764, -77.55514), (38.81691, -77.55393), (38.81644, -77.55158), (38.81599, -77.55141), (38.81537, -77.55028), (38.81479, -77.54718), (38.81477, -77.54580), (38.81391, -77.54346), (38.81420, -77.54244), (38.81412, -77.54189), (38.81328, -77.54067), (38.81278, -77.54055), (38.81273, -77.54029)],
    'chinn_br': [(38.80148, -77.53680), (38.80198, -77.53601), (38.80259, -77.53354), (38.80321, -77.53237), (38.80792, -77.53066), (38.80997, -77.52955), (38.81166, -77.52819), (38.81303, -77.52791), (38.81389, -77.52742), (38.81551, -77.52767), (38.81656, -77.52815), (38.81779, -77.52811)],
    'little_bull': [(38.81933, -77.58246), (38.81959, -77.58077), (38.82046, -77.58008), (38.82109, -77.57783), (38.82160, -77.57696), (38.82176, -77.57516), (38.82402, -77.57644), (38.82459, -77.57717), (38.82503, -77.57713), (38.82505, -77.57535), (38.82582, -77.57425), (38.82532, -77.57355), (38.82538, -77.57330), (38.82612, -77.57235), (38.82668, -77.57211), (38.82756, -77.56934), (38.82838, -77.56885), (38.82909, -77.56884), (38.83012, -77.56768), (38.83157, -77.56704), (38.83369, -77.56743), (38.83383, -77.56513), (38.83411, -77.56489), (38.83437, -77.56334), (38.83518, -77.56264), (38.83593, -77.56293), (38.83641, -77.56262), (38.83717, -77.56275), (38.83721, -77.56322), (38.83759, -77.56341), (38.83820, -77.56450), (38.83874, -77.56454), (38.83979, -77.56797), (38.84067, -77.56803), (38.84098, -77.56781), (38.84104, -77.56673), (38.83996, -77.56310), (38.84057, -77.56255), (38.84112, -77.56043), (38.84154, -77.56028), (38.84272, -77.55824), (38.84317, -77.55797), (38.84468, -77.55601), (38.84491, -77.55467), (38.84378, -77.55346), (38.84380, -77.55285), (38.84481, -77.55295), (38.84557, -77.55341), (38.84593, -77.55261), (38.84593, -77.55226), (38.84530, -77.55162), (38.84535, -77.55133), (38.84501, -77.55092), (38.84383, -77.55008), (38.84442, -77.54870), (38.84417, -77.54609), (38.84391, -77.54567), (38.84321, -77.54529), (38.84291, -77.54583), (38.84190, -77.54521), (38.84019, -77.54606), (38.83965, -77.54502), (38.84026, -77.54206), (38.84105, -77.54203), (38.84154, -77.54147), (38.84202, -77.53957), (38.84273, -77.53841), (38.84285, -77.53778)],
    'holkums': [(38.79894, -77.51726), (38.80037, -77.51551), (38.80083, -77.51562), (38.80135, -77.51520), (38.80550, -77.51436), (38.80723, -77.51320), (38.80761, -77.51189), (38.80834, -77.51097), (38.80875, -77.51077), (38.80909, -77.51096), (38.80970, -77.51055), (38.81147, -77.51019), (38.81262, -77.50950), (38.81317, -77.50863), (38.81367, -77.50872), (38.81413, -77.50846), (38.81441, -77.50765), (38.81515, -77.50764), (38.81641, -77.50690), (38.81654, -77.50666), (38.81629, -77.50629), (38.81624, -77.50514)],
}
L = {k: [M(*p) for p in v] for k, v in LINES_LL.items()}
PIKE, SUDLEY_RD, RR, BULL_RUN = L['pike'], L['sudley_rd'], L['railroad'], L['bull_run']

def inside(x, y, poly):
    c = False
    for i in range(len(poly)):
        (xa, ya), (xb, yb) = poly[i], poly[i - 1]
        if (ya > y) != (yb > y) and x < xa + (xb - xa) * (y - ya) / (yb - ya): c = not c
    return c
def dist_line(p, line):
    best = 1e18
    for (xa, ya), (xb, yb) in zip(line, line[1:]):
        dx, dy = xb - xa, yb - ya; t = max(0, min(1, ((p[0] - xa) * dx + (p[1] - ya) * dy) / (dx * dx + dy * dy or 1)))
        best = min(best, math.hypot(p[0] - xa - t * dx, p[1] - ya - t * dy))
    return best
def along(line, a, b):  # the stretch of a line between the points on it nearest a and b
    def proj(p):
        best = None
        for i, (u, v) in enumerate(zip(line, line[1:])):
            dx, dy = v[0] - u[0], v[1] - u[1]; t = max(0, min(1, ((p[0] - u[0]) * dx + (p[1] - u[1]) * dy) / (dx * dx + dy * dy or 1)))
            q = (u[0] + t * dx, u[1] + t * dy)
            if best is None or math.dist(p, q) < best[0]: best = (math.dist(p, q), i + t, q)
        return best[1], best[2]
    (sa, qa), (sb, qb) = proj(a), proj(b)
    mid = [line[i] for i in range(math.floor(min(sa, sb)) + 1, math.ceil(max(sa, sb)))]
    return [(round(qa[0]), round(qa[1]))] + (mid if sa <= sb else mid[::-1]) + [(round(qb[0]), round(qb[1]))]
def at_x(line, x):  # where a west-east line crosses the meridian x
    for (xa, ya), (xb, yb) in zip(line, line[1:]):
        if min(xa, xb) <= x <= max(xa, xb) and xa != xb: return (x, round(ya + (yb - ya) * (x - xa) / (xb - xa)))
def offset(line, d):  # a line d metres to the right of another
    out = []
    for i, p in enumerate(line):
        a, b = line[max(0, i - 1)], line[min(len(line) - 1, i + 1)]; L_ = math.dist(a, b) or 1
        out.append((round(p[0] + d * (b[1] - a[1]) / L_), round(p[1] - d * (b[0] - a[0]) / L_)))
    return out
def heading(a, b): return round(math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) % 360)
def dv(h): r = math.radians(h); return (math.sin(r), math.cos(r))

# The railroad grade, measured from the point on it nearest Sudley Church south-west toward the Brawner farm. gp(s, off)
# is s metres along it and off metres out to its south-east, the Union side; SE(s) is the heading facing that way.
GRADE = along(RR, P['sudley_church'], RR[0])
def _seg(s):
    for a, b in zip(GRADE, GRADE[1:]):
        d = math.dist(a, b)
        if s <= d: return a, b, s / d
        s -= d
    return GRADE[-2], GRADE[-1], 1
def SE(s): a, b, _ = _seg(s); return (heading(a, b) - 90) % 360
def gp(s, off=0):
    a, b, f = _seg(s); ux, uy = dv(SE(s))
    return (round(a[0] + f * (b[0] - a[0]) + off * ux), round(a[1] + f * (b[1] - a[1]) + off * uy))
def s_of(p): return min(range(0, 4000, 10), key=lambda s: math.dist(gp(s), p))
DEEP_CUT = gp(s_of(P['monument']))  # the 1865 monument stands in the cut
DUMP = gp(s_of(P['dump']))
LEWIS_FORD = min(((x, y) for x, y in BULL_RUN), key=lambda q: math.dist(q, P['lewis_ford_note']))  # the run's nearest bend to the note's point
LEWIS_LANE = [at_x(PIKE, P['ny5'][0]), P['ny5'], P['ny10'], (P['ny10'][0] - 10, P['ny10'][1] - 250)]

# ---- woods and fields ----
# The note's 1862 woods: Stony Ridge behind the railroad grade, 700 m deep; the woods south of the grade from the Dump to
# Sudley, where Schurz, Grover and Kearny fought, 450 m deep; the Groveton woods south of the turnpike; and the woods on
# the Union left of Chinn Ridge round the Chinn house. Porter's pasture below the Deep Cut, the Brawner, Dogan, Chinn,
# Henry and Matthews farms are open. Steep slopes and the banks of Bull Run are wooded as well.
def quad(cx, cy, w, h): return [(cx - w, cy - h), (cx + w, cy - h), (cx + w, cy + h), (cx - w, cy + h)]
RR_IN = along(RR, (-4500, -720), P['sudley_church'])
RR_DUMP = along(RR, DUMP, P['sudley_church'])
WOODS = [RR_IN + offset(RR_IN, -700)[::-1], RR_DUMP + offset(RR_DUMP, 450)[::-1], quad(-1850, -1050, 450, 330), quad(-600, -1400, 300, 250)]
def hashf(i, j, s=0): return ((i * 73856093 ^ j * 19349663 ^ s * 83492791) & 0xffff) / 0xffff
CELL, PARCEL, N = 50, 700, 9000 // 50
def wooded(x, y):
    if any(inside(x, y, w) for w in WOODS): return True
    if dist_line((x, y), BULL_RUN) < 60: return True
    return math.hypot(z(x + 40, y) - z(x - 40, y), z(x, y + 40) - z(x, y - 40)) / 80 > 0.2
SEEDS = {(gx, gy): (gx * PARCEL + (hashf(gx, gy, 1) - 0.5) * PARCEL * 0.8, gy * PARCEL + (hashf(gx, gy, 2) - 0.5) * PARCEL * 0.8) for gx in range(-8, 9) for gy in range(-8, 9)}
def parcel(x, y):
    gx, gy = round(x / PARCEL), round(y / PARCEL)
    return min(((i, j) for i in range(gx - 2, gx + 3) for j in range(gy - 2, gy + 3) if (i, j) in SEEDS), key=lambda k: math.dist(SEEDS[k], (x, y)))
cells = {}
for j in range(N):
    for i in range(N):
        x, y = -4500 + (i + 0.5) * CELL, -4500 + (j + 0.5) * CELL
        if not wooded(x, y): cells.setdefault(parcel(x, y), set()).add((i, j))
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
def lab(name, k, dx=0, dy=90): return dict(name=name, at=[P[k][0] + dx, P[k][1] + dy])
features = [
    dict(type="creek", name="Bull Run", pts=BULL_RUN, **label_on(BULL_RUN[-30], BULL_RUN[-28], 70)),
    dict(type="creek", name="Young's Branch", pts=L['youngs'], **label_on((-225, -392), (-28, -91), 60)),
    dict(type="creek", name="Dogans Branch", pts=L['dogans'], **label_on(L['dogans'][4], L['dogans'][8], 50)),
    dict(type="creek", name="Chinn Branch", pts=L['chinn_br'], **label_on(L['chinn_br'][3], L['chinn_br'][4], -50)),
    dict(type="creek", name="Little Bull Run", pts=L['little_bull'], **label_on(L['little_bull'][3], L['little_bull'][5], 60)),
    dict(type="creek", name="Holkums Branch", pts=L['holkums']),
    dict(type="road", name="Warrenton Turnpike", pts=PIKE, **label_on(PIKE[1], PIKE[2], -60)),
    dict(type="road", name="Manassas-Sudley road", pts=SUDLEY_RD, **label_on(SUDLEY_RD[11], SUDLEY_RD[12], 60)),
    dict(type="road", name="Groveton-Sudley road", pts=L['featherbed'], **label_on(L['featherbed'][1], L['featherbed'][2], -50)),
    dict(type="road", name="road to Manassas", pts=L['groveton_rd'], **label_on(L['groveton_rd'][3], L['groveton_rd'][4], -50)),
    dict(type="road", name="Pageland Lane", pts=L['pageland'], **label_on(L['pageland'][11], L['pageland'][12], -50)),
    dict(type="road", name="Lewis Lane (about here)", pts=LEWIS_LANE, **label_on(LEWIS_LANE[0], LEWIS_LANE[1], -45)),
    dict(type="works", name="the unfinished railroad", pts=RR_IN, **label_on(gp(1300), gp(1500), -80)),
    lab("Brawner farm", 'brawner', 0, -90), lab("Dogan house", 'dogan', -60, -80), lab("Groveton", 'groveton', 120, -90),
    dict(name="the Deep Cut", at=[DEEP_CUT[0] + 140, DEEP_CUT[1] - 60]), dict(name="the Dump", at=[DUMP[0] + 120, DUMP[1] - 40]),
    lab("Stony Ridge", 'stony_guns', -150, 200), lab("Battery Heights", 'battery_heights', 0, -70),
    lab("Chinn Ridge", 'chinn_ridge', 160, 0), lab("Chinn house (ruins)", 'chinn_house', 0, -80), lab("Bald Hill", 'bald_hill', 120, -60),
    lab("Henry house (ruins)", 'henry_house', 60, 70), lab("Henry Hill", 'henry_hill', 150, -40), lab("Robinson house (ruins)", 'robinson', 60, 70),
    lab("Stone House", 'stone_house', 130, -50), lab("Buck Hill", 'buck_hill', 140, 60), lab("Matthews Hill", 'matthews_hill', -150, 90),
    lab("Sudley Church", 'sudley_church', -170, 40), lab("Sudley Springs Ford", 'sudley_ford', 60, 100),
    dict(name="Stone Bridge", at=[P['stone_bridge'][0] + 180, P['stone_bridge'][1] - 40]),
    dict(name="Lewis Ford (about here)", at=[LEWIS_FORD[0] - 230, LEWIS_FORD[1] + 60]), lab("Portici (about here)", 'portici', 0, -80),
    lab("Stuart's Hill, Lee's headquarters", 'stuarts_hill', 0, -90), lab("Mount Pone", 'mount_pone', 0, -80),
]

# ---- order of battle: (id, side, short, name, commander, type, strength, extra) ----
# Brigades. The note's figures where it has them: Grover about 1,500, McLean 1,200, Warren about 1,000, Gibbon 2,100,
# the 13th Massachusetts and Ricketts's division 5,000, Hood's Texans from 3,000 at the start of the campaign, S. D. Lee's
# eighteen guns. Every other brigade is the note's estimate: 1,500 to a brigade of the Army of Virginia, 1,800 to one of
# the Army of the Potomac, 1,400 to one of Jackson's and 1,700 to one of Longstreet's, more or less by its regiments.
# Each drawn gun stands for a battery, with 100 men to a battery. The cavalry stands four ranks deep, for its squadrons.
CAV = dict(ranks=4)
OOB = [
    # Army of Virginia, I Corps (Sigel)
    ("stahel", "union", "Stahel", "Stahel's brigade (Schenck's division): 8th, 41st, 45th New York, 27th Pennsylvania", "Brig. Gen. Julius Stahel", "infantry", 1500, {}),
    ("mclean", "union", "McLean", "McLean's Ohio brigade (Schenck's division): 25th, 55th, 73rd, 75th Ohio", "Col. Nathaniel McLean", "infantry", 1200, {}),
    ("koltes", "union", "Koltes", "Koltes's brigade (von Steinwehr's division): 29th, 68th New York, 73rd Pennsylvania", "Col. John Koltes (killed)", "infantry", 1200, {}),
    ("schimmelfennig", "union", "Schimmelfennig", "Schimmelfennig's brigade (Schurz's division): 61st Ohio, 74th Pennsylvania, 8th West Virginia", "Brig. Gen. Alexander Schimmelfennig", "infantry", 1500, {}),
    ("krzyzanowski", "union", "Krzyzanowski", "Krzyzanowski's brigade (Schurz's division): 54th, 58th New York, 75th Pennsylvania", "Col. Wladimir Krzyzanowski", "infantry", 1500, {}),
    ("milroy", "union", "Milroy", "Milroy's independent brigade: 82nd Ohio, 2nd, 3rd, 5th West Virginia", "Brig. Gen. Robert Milroy", "infantry", 1800, {}),
    ("dogan_guns", "union", "Union guns", "The Union guns on Dogan Ridge: Sigel's on the 29th, 28 pieces under Porter on the 30th", "", "artillery", 500, dict(guns=5)),
    # III Corps (McDowell): King's division, then Hatch's
    ("hatch", "union", "Hatch", "Hatch's brigade, Sullivan's once Hatch had the division: 22nd, 24th, 30th, 84th New York (14th Brooklyn), 2nd U.S. Sharpshooters", "Brig. Gen. John Hatch, then Col. Timothy Sullivan", "infantry", 1800, {}),
    ("doubleday", "union", "Doubleday", "Doubleday's brigade (King's division): 76th, 95th New York, 56th Pennsylvania", "Brig. Gen. Abner Doubleday", "infantry", 1200, {}),
    ("patrick", "union", "Patrick", "Patrick's brigade (King's division): 21st, 23rd, 35th, 80th New York", "Brig. Gen. Marsena Patrick", "infantry", 1500, {}),
    ("gibbon", "union", "Gibbon", "Gibbon's brigade, the Black Hats: 19th Indiana, 2nd, 6th, 7th Wisconsin", "Brig. Gen. John Gibbon", "infantry", 2100, {}),
    ("b4us", "union", "B/4th U.S.", "Battery B, 4th U.S. Artillery, Gibbon's old battery", "", "artillery", 100, dict(guns=1)),
    # Ricketts's division
    ("duryee", "union", "Duryée", "Duryée's brigade (Ricketts's division): 97th, 104th, 105th New York, 107th Pennsylvania", "Brig. Gen. Abram Duryée", "infantry", 1250, {}),
    ("tower", "union", "Tower", "Tower's brigade (Ricketts's division): 26th, 94th New York, 88th, 90th Pennsylvania", "Brig. Gen. Zealous Tower (wounded)", "infantry", 1250, {}),
    ("stiles", "union", "Stiles", "Hartsuff's brigade under Stiles (Ricketts's division): 12th, 13th Massachusetts, 83rd New York, 11th Pennsylvania", "Col. John Stiles", "infantry", 1250, {}),
    ("thoburn", "union", "Thoburn", "Thoburn's brigade (Ricketts's division): 7th Indiana, 84th, 110th Pennsylvania, 1st West Virginia", "Col. Joseph Thoburn (wounded)", "infantry", 1250, {}),
    ("leppien", "union", "5th Maine Battery", "5th Maine Battery, five guns", "Capt. George Leppien", "artillery", 100, dict(guns=1)),
    # the Pennsylvania Reserves (Reynolds)
    ("meade", "union", "Meade", "Meade's brigade of Pennsylvania Reserves: 3rd, 4th, 7th, 8th, 13th", "Brig. Gen. George Meade", "infantry", 1500, {}),
    ("seymour", "union", "Seymour", "Seymour's brigade of Pennsylvania Reserves: 1st, 2nd, 5th, 6th", "Brig. Gen. Truman Seymour", "infantry", 1500, {}),
    ("hardin", "union", "Hardin", "C. F. Jackson's brigade of Pennsylvania Reserves under Hardin: 9th, 10th, 11th, 12th", "Col. Martin Hardin", "infantry", 1500, {}),
    ("piatt", "union", "Piatt", "Piatt's brigade (Sturgis's reserve): 63rd Indiana (four companies), 86th New York", "Brig. Gen. Abram Piatt", "infantry", 800, {}),
    # Army of the Potomac, III Corps (Heintzelman)
    ("robinson", "union", "Robinson", "Robinson's brigade (Kearny's division): 20th Indiana, 30th Ohio (six companies), 63rd, 105th Pennsylvania", "Brig. Gen. John Robinson", "infantry", 1500, {}),
    ("birney", "union", "Birney", "Birney's brigade (Kearny's division): 3rd, 4th Maine, 1st, 38th, 40th, 101st New York, 57th Pennsylvania", "Brig. Gen. David Birney", "infantry", 1800, {}),
    ("poe", "union", "Poe", "Poe's brigade (Kearny's division): 2nd, 3rd, 5th Michigan, 37th New York, 99th Pennsylvania", "Col. Orlando Poe", "infantry", 1500, {}),
    ("grover", "union", "Grover", "Grover's brigade (Hooker's division): 1st, 11th, 16th Massachusetts, 2nd New Hampshire, 26th Pennsylvania", "Brig. Gen. Cuvier Grover", "infantry", 1500, {}),
    ("taylor", "union", "Excelsior", "Taylor's Excelsior Brigade (Hooker's division): 70th to 74th New York", "Col. Nelson Taylor", "infantry", 1500, {}),
    ("carr", "union", "Carr", "Carr's brigade (Hooker's division): 5th to 8th New Jersey, 2nd New York, 115th Pennsylvania", "Brig. Gen. Joseph Carr", "infantry", 1800, {}),
    # V Corps (Porter)
    ("roberts", "union", "Roberts", "Roberts's brigade (Butterfield's division): 2nd Maine, 18th Massachusetts, 1st Michigan, 13th, 25th New York", "Col. Charles Roberts", "infantry", 1800, {}),
    ("weeks", "union", "Weeks", "Weeks's brigade (Butterfield's division): 16th Michigan, 12th, 17th, 44th New York, 83rd Pennsylvania", "Col. Henry Weeks", "infantry", 1800, {}),
    ("berdan", "union", "Berdan", "1st U.S. Sharpshooters", "Col. Hiram Berdan", "riflemen", 400, dict(loose=True)),
    ("hazlett", "union", "Hazlett", "Battery D, 5th U.S. Artillery, six guns", "Lt. Charles Hazlett", "artillery", 100, dict(guns=1)),
    ("buchanan", "union", "Buchanan", "Buchanan's brigade of regulars (Sykes's division): 3rd, 4th, 12th, 14th U.S.", "Lt. Col. Robert Buchanan", "infantry", 1800, {}),
    ("chapman", "union", "Chapman", "Chapman's brigade of regulars (Sykes's division): 1st, 2nd, 6th, 10th, 11th, 17th U.S.", "Lt. Col. William Chapman", "infantry", 1800, {}),
    ("warren", "union", "Warren", "Warren's brigade (Sykes's division): the 5th and 10th New York", "Col. Gouverneur Warren", "infantry", 1000, {}),
    # IX Corps (Reno)
    ("stevens", "union", "Stevens", "Stevens's division of the IX Corps: Christ's, Leasure's and Farnsworth's brigades", "Brig. Gen. Isaac Stevens", "infantry", 2500, {}),
    ("nagle", "union", "Nagle", "Nagle's brigade (Reno's division): 2nd Maryland, 6th New Hampshire, 48th Pennsylvania", "Brig. Gen. James Nagle", "infantry", 1250, {}),
    ("ferrero", "union", "Ferrero", "Ferrero's brigade (Reno's division): 21st Massachusetts, 51st New York, 51st Pennsylvania", "Brig. Gen. Edward Ferrero", "infantry", 1250, {}),
    ("buford", "union", "Buford", "Buford's cavalry brigade: 1st Michigan, 5th New York, 1st Vermont, 1st West Virginia", "Brig. Gen. John Buford (wounded)", "cavalry", 1500, CAV),
    # Army of Northern Virginia: Jackson's wing. Jackson's division (Taliaferro, then Starke)
    ("stonewall", "confederate", "Stonewall", "The Stonewall Brigade: 2nd, 4th, 5th, 27th, 33rd Virginia", "Col. William Baylor (killed), then Col. Andrew Grigsby", "infantry", 1400, {}),
    ("jones_bj", "confederate", "Johnson", "J. R. Jones's brigade under Bradley Johnson: 21st, 42nd, 48th Virginia, 1st Virginia Battalion", "Col. Bradley Johnson", "infantry", 1200, {}),
    ("taliaferro_ag", "confederate", "Taliaferro", "A. G. Taliaferro's brigade: 47th, 48th Alabama, 10th, 23rd, 37th Virginia", "Col. Alexander Taliaferro", "infantry", 1400, {}),
    ("stafford", "confederate", "Stafford", "Starke's Louisiana brigade under Stafford: 1st, 2nd, 9th, 10th, 15th Louisiana, 1st Louisiana Zouave Battalion", "Col. Leroy Stafford", "infantry", 1400, {}),
    ("jguns", "confederate", "Jackson's guns", "The artillery of Jackson's division, Wooding's, Poague's and Carpenter's batteries among them", "Maj. Lindsay Shumaker", "artillery", 700, dict(guns=7)),
    # A. P. Hill's Light Division
    ("branch", "confederate", "Branch", "Branch's North Carolina brigade: 7th, 18th, 28th, 33rd, 37th", "Brig. Gen. Lawrence Branch", "infantry", 1400, {}),
    ("pender", "confederate", "Pender", "Pender's North Carolina brigade: 16th, 22nd, 34th, 38th", "Brig. Gen. Dorsey Pender", "infantry", 1400, {}),
    ("thomas", "confederate", "Thomas", "Thomas's Georgia brigade: 14th, 35th, 45th, 49th Georgia", "Col. Edward Thomas", "infantry", 1400, {}),
    ("gregg", "confederate", "Gregg", "Gregg's South Carolina brigade: 1st, 12th, 13th, 14th South Carolina, Orr's Rifles", "Brig. Gen. Maxcy Gregg", "infantry", 1500, {}),
    ("archer", "confederate", "Archer", "Archer's brigade: 5th Alabama Battalion, 19th Georgia, 1st, 7th, 14th Tennessee", "Brig. Gen. James Archer", "infantry", 1200, {}),
    ("field", "confederate", "Field", "Field's Virginia brigade, Brockenbrough's after Field fell: 40th, 47th, 55th Virginia, 22nd Virginia Battalion", "Brig. Gen. Charles Field (wounded)", "infantry", 1200, {}),
    ("hguns", "confederate", "Hill's guns", "A. P. Hill's artillery", "Lt. Col. Reuben Walker", "artillery", 700, dict(guns=7)),
    # Ewell's division (Lawton after Ewell fell on the 28th)
    ("lawton", "confederate", "Lawton", "Lawton's Georgia brigade under Douglass: 13th, 26th, 31st, 38th, 60th, 61st Georgia", "Col. Marcellus Douglass", "infantry", 1800, {}),
    ("trimble", "confederate", "Trimble", "Trimble's brigade: 15th Alabama, 12th, 21st Georgia, 21st North Carolina, 1st North Carolina Sharpshooters", "Brig. Gen. Isaac Trimble (wounded)", "infantry", 1400, {}),
    ("early", "confederate", "Early", "Early's Virginia brigade: 13th, 25th, 31st, 44th, 49th, 52nd, 58th Virginia", "Brig. Gen. Jubal Early", "infantry", 1800, {}),
    ("hays", "confederate", "Hays", "Hays's Louisiana brigade under Forno, then Strong: 5th, 6th, 7th, 8th, 14th Louisiana", "Col. Henry Forno (wounded)", "infantry", 1400, {}),
    ("eguns", "confederate", "Ewell's guns", "Ewell's artillery", "Maj. Alfred Courtney", "artillery", 600, dict(guns=6)),
    # Longstreet's wing
    ("hood", "confederate", "Texas Brigade", "Hood's Texas Brigade: 1st, 4th, 5th Texas, 18th Georgia, Hampton's Legion", "Brig. Gen. John Bell Hood", "infantry", 2500, {}),
    ("law", "confederate", "Law", "Whiting's brigade under Law (Hood's division): 4th Alabama, 2nd, 11th Mississippi, 6th North Carolina", "Col. Evander Law", "infantry", 1700, {}),
    ("frobel", "confederate", "Frobel", "Hood's artillery: the Rowan, German and Palmetto batteries", "Maj. Bushrod Frobel", "artillery", 300, dict(guns=3)),
    ("evans", "confederate", "Evans", "Evans's South Carolina brigade under Stevens: 17th, 18th, 22nd, 23rd South Carolina, Holcombe Legion", "Brig. Gen. Nathan Evans", "infantry", 1800, {}),
    ("corse", "confederate", "Corse", "Kemper's brigade under Corse (Kemper's division): 1st, 7th, 11th, 17th, 24th Virginia", "Col. Montgomery Corse (wounded)", "infantry", 1400, {}),
    ("jenkins", "confederate", "Jenkins", "Jenkins's South Carolina brigade (Kemper's division): 1st, 2nd, 5th, 6th South Carolina, 4th Battalion, Palmetto Sharpshooters", "Col. Micah Jenkins (wounded)", "infantry", 1900, {}),
    ("hunton", "confederate", "Hunton", "Pickett's brigade under Hunton (Kemper's division): 8th, 18th, 19th, 28th, 56th Virginia", "Col. Eppa Hunton", "infantry", 1500, {}),
    ("benning", "confederate", "Benning", "Toombs's Georgia brigade under Benning (D. R. Jones's division): 2nd, 15th, 17th, 20th Georgia", "Col. Henry Benning", "infantry", 1500, {}),
    ("drayton", "confederate", "Drayton", "Drayton's brigade (D. R. Jones's division): 50th, 51st Georgia, Phillips Legion, 15th South Carolina, 3rd South Carolina Battalion", "Brig. Gen. Thomas Drayton", "infantry", 1700, {}),
    ("gtanderson", "confederate", "G. T. Anderson", "G. T. Anderson's Georgia brigade (D. R. Jones's division): 1st, 7th, 8th, 9th, 11th Georgia", "Col. George T. Anderson", "infantry", 1700, {}),
    ("wilcox", "confederate", "Wilcox", "Wilcox's Alabama brigade: 8th, 9th, 10th, 11th Alabama", "Brig. Gen. Cadmus Wilcox", "infantry", 1500, {}),
    ("pryor", "confederate", "Pryor", "Pryor's brigade (Wilcox's division): 14th Alabama, 2nd, 5th, 8th Florida, 3rd Virginia", "Brig. Gen. Roger Pryor", "infantry", 1500, {}),
    ("featherston", "confederate", "Featherston", "Featherston's Mississippi brigade (Wilcox's division): 12th, 16th, 19th Mississippi, 2nd Mississippi Battalion", "Brig. Gen. Winfield Featherston", "infantry", 1500, {}),
    ("armistead", "confederate", "Armistead", "Armistead's Virginia brigade (R. H. Anderson's division): 9th, 14th, 38th, 53rd, 57th Virginia, 5th Virginia Battalion", "Brig. Gen. Lewis Armistead", "infantry", 1700, {}),
    ("mahone", "confederate", "Mahone", "Mahone's Virginia brigade (R. H. Anderson's division): 6th, 12th, 16th, 41st Virginia", "Brig. Gen. William Mahone (wounded)", "infantry", 1500, {}),
    ("wright", "confederate", "Wright", "Wright's brigade (R. H. Anderson's division): 44th Alabama, 3rd, 22nd, 48th Georgia", "Brig. Gen. Ambrose Wright", "infantry", 1500, {}),
    ("sdlee", "confederate", "S. D. Lee", "S. D. Lee's battalion: the Brooks, Ashland, Bath, Bedford, Portsmouth and Parker batteries, eighteen guns", "Col. Stephen D. Lee", "artillery", 600, dict(guns=6)),
    ("walton", "confederate", "Walton", "Longstreet's reserve artillery: the Washington Artillery and three batteries", "Col. James Walton", "artillery", 700, dict(guns=7)),
    # Stuart's cavalry
    ("robertson", "confederate", "Robertson", "Robertson's cavalry brigade: 2nd, 6th, 7th, 12th Virginia Cavalry, 17th Virginia Battalion", "Brig. Gen. Beverly Robertson", "cavalry", 1500, CAV),
    ("fitzlee", "confederate", "Fitz Lee", "Fitzhugh Lee's cavalry brigade: 1st, 4th, 5th, 9th Virginia Cavalry", "Brig. Gen. Fitzhugh Lee", "cavalry", 1500, CAV),
    ("pelham", "confederate", "Pelham", "Stuart's horse artillery", "Maj. John Pelham", "artillery", 100, dict(guns=1)),
]
BASE = {row[0]: row for row in OOB}
assert len(BASE) == len(OOB)

# ---- the clock: 28 to 30 August 1862, local mean time ----
UTC = dt.timezone.utc
T0 = dt.datetime(1862, 8, 28, tzinfo=UTC)
def D(day, hm): return f"1862-08-{day:02d} {hm}"
def sec(t): return (dt.datetime.strptime(t, "%Y-%m-%d %H:%M:%S" if t.count(":") == 2 else "%Y-%m-%d %H:%M").replace(tzinfo=UTC) - T0).total_seconds()
def fmt(s): s = round(s); return (T0 + dt.timedelta(seconds=s)).strftime("%Y-%m-%d %H:%M" + (":%S" if s % 60 else ""))
def plus(t, mins): return fmt(sec(t) + mins * 60)
def A(hm): return D(28, hm)
def B(hm): return D(29, hm)
def C(hm): return D(30, hm)
START, END = A("05:30"), C("23:00")

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
        elif "h" in b and b["h"] != carried(id, "h") and sec(b["t"]) - sec(a["t"]) > 120:  # wheel in the last minute, so a long halt stays quiet
            have.append(K(fmt(sec(b["t"]) - 60), (a["x"], a["y"])))
    have += ks
def last(id): k = KEYS[id][-1]; return (k["x"], k["y"])
def appear(id, t, p, h, state="line", **kw): keys(id, [K(t, p, h=h, state=state, **kw)])

# Where each unit stands at half past five on the 28th. Jackson's division is behind the railroad grade near the Dump,
# where Taliaferro's night march ended; Ewell's is on the turnpike east of the Stone Bridge, coming back over it. Everyone
# else is still off the map and hidden at the edge they will come in by.
WEST_IN = at_x(PIKE, -4480)   # the turnpike from Gainesville
EAST_IN = at_x(PIKE, 4480)    # the turnpike from Centreville
SOUTH_IN = SUDLEY_RD[-1]      # the Manassas-Sudley road from Manassas
AT_START = {
    "stafford": (gp(2100, -150), SE(2100)), "stonewall": (gp(2350, -150), SE(2350)), "jones_bj": (gp(2550, -150), SE(2550)),
    "taliaferro_ag": (gp(2750, -150), SE(2750)), "jguns": (gp(2450, -350), SE(2450)),
    "pelham": (gp(3000, -350), SE(3000)),
    "lawton": ((2650, 815), 290), "trimble": ((2950, 900), 290), "early": ((3250, 985), 290), "hays": ((3550, 1070), 290), "eguns": ((3850, 1160), 290),
}
for id in BASE:
    if id in AT_START: p, h = AT_START[id]; appear(id, START, p, h, state="column" if p[0] > 2000 else "line")
    else:
        side = BASE[id][1]
        edge = EAST_IN if id in ("branch", "pender", "thomas", "gregg", "archer", "field", "hguns", "robinson", "birney", "poe", "grover", "taylor", "carr", "stevens", "nagle", "ferrero") \
            else WEST_IN if side == "confederate" or id in ("hatch", "doubleday", "patrick", "gibbon", "b4us") else SOUTH_IN
        appear(id, START, (4480, -900) if id == "buford" else edge, 90, state="hidden")

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
def lose(id, n): return carried(id, "strength") - n
def show(id, t, p, h, state="column"): keys(id, [K(t, p, h=h, state=state)])
def hide(id, t): stand(id, t, state="hidden")
def NW(s): return (SE(s) + 180) % 360  # facing the railroad grade from the Union side
PIKE_AT = lambda x: at_x(PIKE, x)
GROVETON_X = L['groveton_rd'][0]          # the crossroads, where the Groveton roads leave the turnpike
STONE_X = along(PIKE, P['stone_house'], P['stone_house'])[0]
def pike(a, b): return along(PIKE, a, b)
def sudley(a, b): return along(SUDLEY_RD, a, b)
SOUTH_EDGE = (L['groveton_rd'][-1][0], -4450)
TO_MANASSAS = L['groveton_rd'] + [SOUTH_EDGE]   # the Groveton-Manassas road from the crossroads off the south edge

# ---- 28 August: Ewell and Hill come up; the woods of Stony Ridge ----
# Ewell back over the Stone Bridge and west on the turnpike, up the Groveton-Sudley road to the grade; Hill from
# Centreville by the turnpike and the Sudley road to the north end of the grade. Their hours are inferred.
FB = L['featherbed']; FB_GRADE = (-1650, 700)
for n, (id, s, off) in enumerate((("lawton", 3150, -200), ("trimble", 2850, -200), ("early", 2550, -260), ("hays", 2300, -260), ("eguns", 2950, -450))):
    walk(id, A("05:30"), *pike(last(id), GROVETON_X), *along(FB, GROVETON_X, FB_GRADE), gp(2100, -350), gp(s, off), h=SE(s), kmh=3)
for n, (id, s, off) in enumerate((("gregg", 450, -60), ("thomas", 1150, -60), ("branch", 350, -350), ("archer", 700, -330),
                                  ("pender", 950, -380), ("field", 1300, -350), ("hguns", 800, -200))):
    show(id, plus(A("08:00"), n * 12), EAST_IN, 270)
    walk(id, plus(A("08:00"), n * 12), *pike(EAST_IN, P['stone_house']), *sudley(P['stone_house'], (-560, 1800)), gp(s, off), h=SE(s), kmh=3)
# Jackson's division shifts west in the woods to face the turnpike by the Brawner farm
for id, s, off in (("taliaferro_ag", 3750, -200), ("stonewall", 3450, -200), ("jones_bj", 3500, -450), ("stafford", 3800, -450), ("pelham", 3650, -350)):
    walk(id, A("13:00"), gp(s, off), h=SE(s), kmh=2.5)
walk("jguns", A("13:00"), P['stony_guns'], h=160, kmh=2.5)

# McDowell east on the turnpike: Reynolds leads and goes on toward Manassas; King's four brigades follow at evening.
for n, id in enumerate(("meade", "seymour", "hardin")):
    show(id, plus(A("13:30"), n * 15), WEST_IN, 70)
    hide(id, plus(walk(id, plus(A("13:30"), n * 15), *pike(WEST_IN, P['stone_house']), *sudley(P['stone_house'], SOUTH_IN), kmh=3.2), 1))
for id, t0, end in (("hatch", "17:15", (-900, -340)), ("gibbon", "17:50", PIKE_AT(-2700)), ("b4us", "17:58", PIKE_AT(-2950)),
                    ("doubleday", "18:05", PIKE_AT(-3250)), ("patrick", "18:15", PIKE_AT(-3650))):
    show(id, A(t0), WEST_IN, 70); walk(id, A(t0), *pike(WEST_IN, end), state="column", kmh=3)

# ---- Brawner farm ----
# The two lines 75 yards apart across the farm north of the pike, the Union line south-west to north-east along the
# loop trail, facing north-west. U(f) is a point a fraction f along it; C(f) the Confederate line opposite.
U1, U2 = (-3150, -480), (-2250, -230)
def U(f): return (U1[0] + f * (U2[0] - U1[0]), U1[1] + f * (U2[1] - U1[1]))
FACE = (heading(U1, U2) - 90) % 360
def CL(f): ux, uy = dv(FACE); p = U(f); return (p[0] + 75 * ux, p[1] + 75 * uy)
fight("jguns", A("18:30"), A("21:00"), 640, h=150); fight("eguns", A("18:40"), A("21:00"), 560, h=150)
mv("gibbon", A("18:35"), A("18:55"), U(0.45), h=FACE, state="firing", moving="line")
mv("b4us", A("18:35"), A("18:50"), (-2560, -700), h=FACE, state="firing")
for id, f, t0 in (("taliaferro_ag", 0.1, "18:40"), ("stonewall", 0.35, "18:40"), ("lawton", 0.62, "18:50"), ("trimble", 0.88, "19:10")):
    mv(id, A(t0), plus(A(t0), 18), CL(f), h=(FACE + 180) % 360, state="firing", moving="line")
mv("pelham", A("18:45"), A("19:05"), (-3170, -390), h=110, state="firing")
mv("doubleday", A("19:20"), A("19:45"), PIKE_AT(-2550), U(0.85), h=FACE, state="firing", moving="line")
fight("gibbon", A("19:00"), A("21:00"), 1300); fight("b4us", A("18:50"), A("21:00"), 80)
fight("doubleday", A("19:45"), A("21:00"), 850)
for id, n in (("taliaferro_ag", 300), ("stonewall", 300), ("lawton", 400), ("trimble", 250)): fight(id, KEYS[id][-1]["t"], A("21:00"), lose(id, n))
fight("pelham", A("19:05"), A("21:00"), 90)
mv("gibbon", A("21:00"), A("21:20"), PIKE_AT(-2700), h=70); mv("doubleday", A("21:00"), A("21:20"), PIKE_AT(-2450), h=70)
mv("b4us", A("21:00"), A("21:15"), PIKE_AT(-2850), h=70)
for id, s, off in (("taliaferro_ag", 3200, -60), ("stonewall", 2900, -60), ("lawton", 1900, -60), ("trimble", 1550, -60), ("pelham", 3300, -400)):
    walk(id, A("22:00"), gp(s, off), h=SE(s), kmh=2.5)
for id, s, off in (("jones_bj", 2620, -60), ("stafford", 2330, -60), ("early", 1800, -380), ("hays", 2150, -380), ("eguns", 1700, -250)):
    walk(id, A("22:30"), gp(s, off), h=SE(s), kmh=2.5)
# Midnight: King's division goes off to Manassas by the Groveton road
for id, t0 in (("hatch", "00:00"), ("gibbon", "00:10"), ("b4us", "00:20"), ("doubleday", "00:25"), ("patrick", "00:35")):
    hide(id, plus(walk(id, B(t0), *pike(last(id), GROVETON_X), *TO_MANASSAS[1:], kmh=3.2), 1))

# ---- 29 August: Sigel up the Sudley road in the night; Schurz finds Jackson at seven ----
for n, (id, end) in enumerate((("schimmelfennig", (0, 650)), ("krzyzanowski", (150, 500)), ("milroy", (-250, 250)), ("stahel", (550, -350)),
                               ("mclean", (650, -550)), ("koltes", (450, -150)), ("dogan_guns", (300, -50)),
                               ("meade", (200, -800)), ("seymour", (350, -1000)), ("hardin", (100, -1050)))):
    show(id, plus(B("02:00"), n * 10), SOUTH_IN, 0)
    walk(id, plus(B("02:00"), n * 10), *sudley(SOUTH_IN, (400, -300)), end, h=290, kmh=3)
for id, s in (("schimmelfennig", 1150), ("krzyzanowski", 650)):
    walk(id, B("06:00"), *sudley(last(id), (-470, 1400)), gp(s, 320), h=NW(s), state="skirmish", kmh=3)
    stand(id, B("09:40"), state="line")
    mv(id, B("10:00"), B("10:10"), gp(s, 80), h=NW(s), state="firing", moving="charge")
    fight(id, B("10:10"), B("10:35"), lose(id, 250))
    mv(id, B("10:35"), B("10:55"), gp(s, 420), h=NW(s), moving="retreat")
for id in ("gregg", "thomas"): fight(id, B("07:00"), B("10:40"), lose(id, 120))
# Schenck and Reynolds west on the pike into the Groveton woods; Milroy up the Groveton-Sudley road
for id, end in (("stahel", (-1850, -900)), ("mclean", (-2050, -1100)), ("meade", (-1650, -1200)), ("seymour", (-1950, -1300)), ("hardin", (-1550, -980))):
    walk(id, B("06:30"), *pike(PIKE_AT(last(id)[0]) if last(id)[1] > -700 else P['stone_house'], PIKE_AT(end[0])), end, h=270, kmh=3)
walk("dogan_guns", B("06:30"), (-1300, -300), h=300, kmh=3)
walk("koltes", B("07:00"), (-800, -200), h=290, kmh=3)
walk("milroy", B("07:00"), (-1200, -300), *along(FB, (-1650, -300), (-1650, 300)), gp(2120, 450), h=NW(2120), kmh=3)
for id in ("dogan_guns", "jguns", "eguns"): fight(id, B("10:00"), B("12:00"), lose(id, 30))
mv("milroy", B("10:00"), B("10:12"), gp(2120, 30), h=NW(2120), state="firing", moving="charge")
fight("milroy", B("10:12"), B("10:25"), lose("milroy", 300)); fight("lawton", B("10:05"), B("10:30"), lose("lawton", 80))
mv("milroy", B("10:25"), B("10:50"), gp(2120, 650), (-1500, -250), h=60, moving="retreat")

# Longstreet in on the turnpike from Gainesville and deployed across the Union left, unseen by Pope
LONG = [("hood", (-2650, -1120), 70), ("law", (-2700, -770), 70), ("frobel", P['battery_heights'], 80), ("evans", (-2950, -1200), 70),
        ("wilcox", (-3150, -850), 70), ("pryor", (-3350, -950), 70), ("featherston", (-3200, -650), 70),
        ("corse", (-2850, -1500), 70), ("jenkins", (-3000, -1800), 70), ("hunton", (-3150, -2100), 70), ("sdlee", (-3350, -1150), 70),
        ("benning", (-3350, -2450), 60), ("drayton", (-3550, -2800), 60), ("gtanderson", (-3750, -3150), 60),
        ("robertson", (-3700, -3500), 60), ("fitzlee", (-4000, -3900), 60)]
for n, (id, end, h) in enumerate(LONG):
    t0 = plus(B("10:30"), n * 8); kmh = 8 if BASE[id][5] == "cavalry" else 3
    show(id, t0, WEST_IN, 70)
    walk(id, t0, *pike(WEST_IN, PIKE_AT(max(-3700, min(end[0], -2600)))), end, h=h, kmh=kmh)

# Hooker, Kearny and Reno from Centreville, over the Stone Bridge
for n, (id, end, h) in enumerate((("robinson", gp(560, 300), NW(560)), ("birney", (-520, 2120), 250), ("poe", (-450, 1600), 290),
                                  ("grover", gp(820, 420), NW(820)), ("taylor", (-500, 1150), 300), ("carr", (-380, 950), 300),
                                  ("stevens", (100, 800), 290), ("nagle", (-200, 1000), 300), ("ferrero", (-100, 650), 300))):
    t0 = plus(B("10:00"), n * 12)
    show(id, t0, EAST_IN, 270)
    walk(id, t0, *pike(EAST_IN, P['stone_house']), *sudley(P['stone_house'], (-470, 1450) if end[1] > 1300 else (-265, 700)), end, h=h, kmh=3.5)
for id in ("schimmelfennig", "krzyzanowski"): walk(id, B("13:30"), (-100, 500) if id == "schimmelfennig" else (100, 350), h=290, kmh=3)
# Grover's bayonet charge at three into the gap between Thomas's and Gregg's brigades
mv("grover", B("15:00"), B("15:10"), gp(820, 20), h=NW(820), state="charge", moving="charge")
mv("grover", B("15:10"), B("15:15"), gp(820, -80), h=NW(820), state="firing", moving="charge")
fight("grover", B("15:15"), B("15:30"), 1013)
mv("grover", B("15:30"), B("15:50"), gp(820, 450), h=NW(820), moving="retreat")
fight("gregg", B("15:10"), B("15:35"), lose("gregg", 150), h=SE(820) + 60)
mv("pender", B("15:12"), B("15:22"), gp(850, -180), h=SE(850), state="firing", moving="charge")
fight("pender", B("15:22"), B("15:40"), lose("pender", 150)); fight("thomas", B("15:10"), B("15:35"), lose("thomas", 150))
mv("pender", B("15:45"), B("16:05"), gp(950, -380), h=SE(950))
# About four Hays's brigade and then Early come up on Gregg's left by Sudley Church
walk("hays", B("15:40"), gp(1500, -420), gp(150, -60), h=SE(150), kmh=4)
walk("early", B("16:00"), gp(1500, -450), gp(400, -450), h=SE(400), kmh=4)
# Kearny at five on Jackson's far left; Gregg is badly hit; Branch and Early stop him and drive him back
for id, s, t0 in (("robinson", 560, "17:00"), ("birney", 280, "17:00")):
    mv(id, B(t0), B("17:12"), gp(s, 20), h=NW(s), state="charge", moving="charge")
    mv(id, B("17:12"), B("17:20"), gp(s, -110), h=NW(s), state="firing", moving="charge")
    fight(id, B("17:20"), B("17:35"), lose(id, 300))
    mv(id, B("17:35"), B("18:00"), gp(s, 380), h=NW(s), moving="retreat")
mv("birney", B("18:00"), B("18:20"), (-520, 2120), h=250)
fight("gregg", B("17:10"), B("17:35"), lose("gregg", 300)); fight("hays", B("17:10"), B("17:35"), lose("hays", 150))
mv("branch", B("17:20"), B("17:32"), gp(450, -130), h=SE(450), state="firing", moving="charge")
mv("early", B("17:20"), B("17:35"), gp(250, -130), h=SE(250), state="firing", moving="charge")
mv("early", B("17:40"), B("17:55"), gp(250, 60), h=SE(250), state="firing", moving="charge")
fight("branch", B("17:32"), B("17:50"), lose("branch", 120)); fight("early", B("17:55"), B("18:10"), lose("early", 100))
mv("early", B("18:10"), B("18:30"), gp(250, -100), h=SE(250)); mv("branch", B("18:00"), B("18:20"), gp(350, -350), h=SE(350))
# Schenck and Reynolds draw back from the Groveton woods in the afternoon; King's division comes back up the Sudley road
for id, end in (("stahel", (-650, -450)), ("mclean", (-450, -700)), ("meade", (-950, -700)), ("seymour", (-750, -900)), ("hardin", (-1050, -500))):
    walk(id, B("16:00"), end, h=270, kmh=3)
for n, (id, end) in enumerate((("hatch", (150, 200)), ("patrick", (50, 330)), ("doubleday", (300, 330)), ("gibbon", (480, 260)), ("b4us", (380, 160)))):
    show(id, plus(B("14:00"), n * 10), SOUTH_IN, 0)
    walk(id, plus(B("14:00"), n * 10), *sudley(SOUTH_IN, (330, 0)), end, h=280, kmh=3)
# Sunset: Hood's reconnaissance east along the pike meets Hatch's division coming west near Groveton about seven
for id, end, t0 in (("hatch", PIKE_AT(-1420), "18:25"), ("doubleday", PIKE_AT(-1150), "18:30"), ("patrick", PIKE_AT(-950), "18:35")):
    walk(id, B(t0), *pike(STONE_X, end), h=260, state="line", kmh=4)
mv("hood", B("18:30"), B("19:00"), (-1650, -700), h=70, state="firing", moving="line")
mv("law", B("18:30"), B("19:00"), (-1700, -480), h=70, state="firing", moving="line")
mv("evans", B("18:35"), B("19:05"), (-2000, -850), h=70)
fight("hatch", B("19:00"), B("19:35"), lose("hatch", 250), h=250); fight("doubleday", B("19:05"), B("19:35"), lose("doubleday", 120), h=250)
fight("hood", B("19:00"), B("19:35"), lose("hood", 150)); fight("law", B("19:00"), B("19:35"), lose("law", 120))
for id, end in (("hatch", (-150, -100)), ("doubleday", (50, -50)), ("patrick", (-100, 100))):
    mv(id, B("19:35"), B("20:05"), *pike(last(id), PIKE_AT(end[0])), h=280, moving="retreat")
for id, (end, h) in (("hood", ((-2650, -1120), 70)), ("law", ((-2700, -770), 70)), ("evans", ((-2950, -1200), 70))):
    walk(id, B("22:30"), end, h=h, kmh=2)

# The night of the 29th: Ricketts up the Sudley road; R. H. Anderson's division in by the pike at three, alone east of Groveton
for n, (id, end) in enumerate((("duryee", (-320, 700)), ("tower", (-160, 580)), ("stiles", (-60, 430)), ("thoburn", (-380, 480)), ("leppien", (-220, 380)))):
    show(id, plus(B("21:00"), n * 10), SOUTH_IN, 0)
    walk(id, plus(B("21:00"), n * 10), *sudley(SOUTH_IN, (289, 36)), (0, 200), end, h=290, kmh=3)
for n, (id, x) in enumerate((("armistead", -1450), ("mahone", -1330), ("wright", -1210))):
    show(id, plus(C("01:55"), n * 8), WEST_IN, 70); walk(id, plus(C("01:55"), n * 8), *pike(WEST_IN, PIKE_AT(x)), state="column", kmh=3)
for n, (id, end) in enumerate((("armistead", (-3250, -1350)), ("mahone", (-3400, -1500)), ("wright", (-3550, -1650)))):
    walk(id, plus(C("05:00"), n * 6), *pike(last(id), PIKE_AT(-3100)), end, h=70, kmh=3)
show("walton", C("04:00"), WEST_IN, 70); walk("walton", C("04:00"), *pike(WEST_IN, PIKE_AT(-3000)), (-3000, -1300), h=70, kmh=3)
# Porter's corps from Manassas at dawn, to the ground behind Henry Hill
for n, (id, end) in enumerate((("roberts", (480, -300)), ("weeks", (650, -450)), ("berdan", (400, -120)), ("hazlett", (300, -250)),
                               ("buchanan", (820, -700)), ("chapman", (900, -880)), ("warren", (700, -950)))):
    show(id, plus(C("05:30"), n * 10), SOUTH_IN, 0)
    walk(id, plus(C("05:30"), n * 10), *sudley(SOUTH_IN, (700, -1200)), end, h=290, kmh=3)
show("piatt", C("07:00"), EAST_IN, 270); walk("piatt", C("07:00"), *pike(EAST_IN, (1000, 300)), (950, -150), h=270, kmh=3)

# ---- 30 August: the morning probes; Porter's attack at three ----
mv("stevens", C("10:00"), C("10:40"), (-700, 1050), h=300); mv("stevens", C("11:30"), C("12:10"), (100, 800), h=290)
for id, s in (("duryee", 1500), ("thoburn", 1300)):
    walk(id, C("10:00"), gp(s, 420), h=NW(s), kmh=3)
    mv(id, C("11:00"), C("11:10"), gp(s, 40), h=NW(s), state="firing", moving="charge")
    fight(id, C("11:10"), C("11:25"), lose(id, 150))
    mv(id, C("11:25"), C("11:45"), gp(s, 500), h=NW(s), moving="retreat")
    walk(id, C("12:00"), (-320, 700) if id == "duryee" else (-380, 480), h=290, kmh=3)
fight("trimble", C("11:05"), C("11:25"), lose("trimble", 60)); fight("field", C("11:05"), C("11:25"), lose("field", 40), h=SE(1300))
# Reynolds to Chinn Ridge with McLean; then McDowell takes him across the pike, leaving McLean and Warren south of it
for id, end in (("meade", (-350, -800)), ("seymour", (-250, -1050)), ("hardin", (150, -1150))): walk(id, C("12:20"), end, h=270, kmh=3)
walk("mclean", C("12:40"), P['chinn_ridge'], h=270, kmh=3)
for id, end in (("meade", (-750, -80)), ("seymour", (-550, 20)), ("hardin", (-350, -150))): walk(id, C("13:40"), *pike(PIKE_AT(last(id)[0]), PIKE_AT(end[0])), end, h=290, kmh=3)
walk("sdlee", C("11:30"), (-2800, -320), h=75, kmh=3)
# Porter forms in the Groveton woods and north of the pike: Weeks and Roberts left and centre, Hatch's division right
FORM = (("weeks", 2750, 560), ("roberts", 2480, 560), ("hatch", 2150, 280), ("patrick", 1900, 300), ("doubleday", 2050, 620), ("gibbon", 1800, 650))
for id, s, off in FORM: walk(id, C("13:00"), *pike(PIKE_AT(last(id)[0]), PIKE_AT(gp(s, off)[0])), gp(s, off), h=NW(s), kmh=2.5)
walk("berdan", C("13:10"), *pike(PIKE_AT(last("berdan")[0]), PIKE_AT(-1700)), gp(2600, 300), h=NW(2600), state="skirmish", kmh=3)
for id, end in (("buchanan", (-1150, -260)), ("chapman", (-950, -200))): walk(id, C("13:00"), *pike(PIKE_AT(last(id)[0]), PIKE_AT(end[0])), end, h=300, kmh=3)
walk("warren", C("13:20"), *pike(PIKE_AT(last("warren")[0]), LEWIS_LANE[0]), P['ny5'], h=250, kmh=3)
walk("hazlett", C("13:20"), *pike(PIKE_AT(last("hazlett")[0]), LEWIS_LANE[0]), (LEWIS_LANE[0][0], LEWIS_LANE[0][1] - 90), h=260, kmh=3)
walk("b4us", C("13:00"), (-1250, -250), h=300, kmh=3)
fight("berdan", C("14:30"), C("15:00"), lose("berdan", 40))
for id in ("dogan_guns", "b4us"): fight(id, C("14:30"), C("16:00"), lose(id, 20))
for id, s, off in FORM[:4]:
    mv(id, C("15:00"), C("15:12"), gp(s, 40), h=NW(s), state="firing", moving="charge")
    fight(id, C("15:12"), C("15:35"), lose(id, 450 if id in ("weeks", "roberts") else 350))
    mv(id, C("15:35"), C("15:55"), gp(s, 750), h=NW(s), moving="retreat"); stand(id, C("16:00"), state="line")
mv("berdan", C("15:00"), C("15:15"), gp(2600, 650), h=NW(2600), moving="retreat")
for id in ("stafford", "jones_bj", "stonewall", "taliaferro_ag"): fight(id, C("15:05"), C("15:40"), lose(id, 250))
fight("sdlee", C("15:00"), C("15:50"), lose("sdlee", 20), h=60); fight("jguns", C("15:00"), C("15:50"), lose("jguns", 20), h=120)
mv("lawton", C("15:10"), C("15:30"), gp(2200, -160), h=SE(2200), state="firing"); fight("lawton", C("15:30"), C("15:45"), lose("lawton", 60))
mv("field", C("15:05"), C("15:35"), gp(2000, -200), h=SE(2000), state="firing"); fight("field", C("15:35"), C("15:50"), lose("field", 40))

# ---- Longstreet's counterattack: Hood overruns Warren at four ----
mv("hood", C("15:20"), C("15:50"), (-1950, -880), h=90, moving="line"); mv("law", C("15:20"), C("15:50"), (-1950, -620), h=80, moving="line")
mv("evans", C("15:25"), C("15:55"), (-2150, -1000), h=90, moving="line")
mv("hood", C("16:00"), C("16:08"), (P['ny5'][0] - 90, P['ny5'][1]), h=90, state="firing", moving="charge")
fight("warren", C("16:00"), C("16:10"), 588, h=250)
mv("warren", C("16:10"), C("16:35"), (350, -700), h=90, state="line", moving="rout")
mv("hazlett", C("16:08"), C("16:25"), (300, -300), h=90, moving="retreat")
mv("law", C("16:00"), C("16:12"), (LEWIS_LANE[0][0] - 100, LEWIS_LANE[0][1] - 40), h=80, state="firing", moving="charge")
fight("hood", C("16:08"), C("16:15"), lose("hood", 150)); fight("law", C("16:12"), C("16:20"), lose("law", 80))
mv("hood", C("16:15"), C("16:45"), (P['texas_mon'][0] - 120, P['texas_mon'][1] + 30), h=95, state="firing", moving="charge")
mv("law", C("16:20"), C("16:55"), (-450, -520), h=110, state="firing", moving="line")
mv("evans", C("16:00"), C("16:35"), (-700, -720), h=100, moving="line")
# McLean's Ohioans at the fence line on Chinn Ridge; Corse's Virginians and Evans's charge on his flank; Hardin shattered
fight("mclean", C("16:25"), C("17:00"), 800, h=270)
for id, end, t0, t1 in (("corse", (-500, -1050), "15:50", "16:30"), ("jenkins", (-480, -1330), "15:55", "16:50"), ("hunton", (-430, -1560), "16:00", "16:55")):
    mv(id, C(t0), C(t1), end, h=75, state="firing", moving="line")
fight("corse", C("16:30"), C("17:10"), lose("corse", 300)); fight("jenkins", C("16:50"), C("17:50"), lose("jenkins", 250)); fight("hunton", C("16:55"), C("17:50"), lose("hunton", 200))
mv("evans", C("16:40"), C("16:50"), (-350, -800), h=150, state="firing", moving="charge")
mv("evans", C("16:50"), C("17:10"), (-750, -700), h=150, moving="retreat", strength=lose("evans", 200))
walk("hardin", C("16:00"), (150, -1150), h=260, kmh=4)
fight("hardin", C("16:30"), C("16:55"), 900); mv("hardin", C("16:55"), C("17:20"), (850, -950), h=80, moving="rout")
fight("hood", C("16:45"), C("17:40"), lose("hood", 330))
mv("mclean", C("17:00"), C("17:25"), (750, -650), h=90, moving="retreat")
# Ricketts and Sigel's men south over Young's Branch and up the ridge: Tower, Stiles, Koltes, Stahel; the 5th Maine
for id, end, t0 in (("tower", (-120, -820), "16:30"), ("stiles", (-60, -700), "16:35"), ("leppien", (-150, -930), "16:30"),
                    ("koltes", (-300, -760), "16:20"), ("stahel", (-200, -620), "16:25")):
    walk(id, C(t0), end, h=260, state="firing", kmh=4.5)
for id, n in (("tower", 400), ("stiles", 350), ("koltes", 400), ("stahel", 350)): fight(id, KEYS[id][-1]["t"], C("17:50"), lose(id, n))
fight("leppien", C("17:30"), C("18:00"), 20)
for id, end in (("tower", (700, -450)), ("stiles", (650, -250)), ("koltes", (900, -350)), ("stahel", (950, -200))):
    mv(id, C("17:50"), C("18:15"), end, h=80, moving="retreat")
mv("leppien", C("18:00"), C("18:20"), (750, -150), h=80, moving="retreat")
# About five Lee sends Dick Anderson's three brigades and part of Wilcox's division from the Brawner farm to Chinn Ridge
for id, end, t0 in (("armistead", (-350, -1000), "17:00"), ("mahone", (-250, -1250), "17:05"), ("wright", (-150, -1450), "17:10"), ("wilcox", (-650, -780), "17:00")):
    walk(id, C(t0), end, h=90, kmh=3.6)
for id, end in (("mahone", (420, -1150)), ("wright", (480, -1350))):
    mv(id, C("18:15"), C("18:45"), end, h=60, state="firing", moving="line"); fight(id, C("18:45"), C("19:20"), lose(id, 250))
# Benning's and G. T. Anderson's Georgians against Henry Hill; Milroy in the Sudley road's bed; the 15th Georgia breaks him
for id, mid, end in (("benning", (-200, -1250), (380, -780)), ("gtanderson", (-100, -1500), (430, -1080))):
    walk(id, C("16:05"), (-1600, -2000), mid, h=70, kmh=3.6)
    mv(id, C("17:40"), C("17:55"), end, h=70, state="firing", moving="charge")
walk("drayton", C("16:10"), (-1300, -2100), h=60, kmh=3)
# Pope's line on Henry Hill: Reynolds's Reserves and Sykes's regulars, Milroy in front in the road's cut
for id, end, t0 in (("buchanan", (620, -430), "16:40"), ("chapman", (660, -660), "16:45"), ("meade", (720, -900), "16:50"), ("seymour", (780, -1120), "16:55")):
    walk(id, C(t0), *pike(PIKE_AT(last(id)[0]), STONE_X), end, h=255, kmh=4.5)
walk("milroy", C("17:10"), *pike(PIKE_AT(last("milroy")[0]), STONE_X), *sudley(STONE_X, (520, -650)), h=250, kmh=4.5)
walk("piatt", C("17:00"), (980, -700), h=260, kmh=3)
for id in ("buchanan", "chapman", "meade", "seymour"): fight(id, C("17:55"), C("19:00"), lose(id, 250))
fight("milroy", C("17:55"), C("18:30"), lose("milroy", 300))
mv("milroy", C("18:30"), C("18:50"), (850, -500), h=80, moving="retreat")
fight("benning", C("17:55"), C("18:40"), lose("benning", 300)); fight("gtanderson", C("17:55"), C("18:40"), lose("gtanderson", 300))
for id, end in (("benning", (60, -900)), ("gtanderson", (120, -1250))): mv(id, C("18:40"), C("19:05"), end, h=70, moving="retreat")

# ---- six o'clock: Jackson comes down off the railroad; the Union right goes back to the Sudley road ----
for id, end, t0 in (("taliaferro_ag", (-1400, -350), "18:00"), ("stonewall", (-1250, -150), "18:00"), ("jones_bj", (-1100, 50), "18:00"), ("stafford", (-950, 250), "18:00"),
                    ("lawton", (-850, 450), "18:05"), ("trimble", (-750, 650), "18:05"), ("hays", (-650, 1100), "18:10"), ("early", (-600, 1350), "18:10"),
                    ("thomas", (-750, 850), "18:05"), ("pender", (-650, 1550), "18:10"), ("field", (-1000, 650), "18:05"), ("archer", (-800, 1750), "18:15"),
                    ("jguns", (-1650, -350), "18:20"), ("eguns", (-1300, 300), "18:20"), ("hguns", (-1050, 1300), "18:20")):
    mv(id, C(t0), plus(C(t0), 50), end, h=100, state="firing", moving="line")
UNION_RIGHT = (("dogan_guns", (350, 250)), ("b4us", (450, 150)), ("weeks", (200, 350)), ("roberts", (250, 500)), ("hatch", (150, 650)), ("patrick", (200, 800)),
               ("doubleday", (300, 950)), ("gibbon", (350, 1100)), ("duryee", (100, 1000)), ("thoburn", (50, 1200)), ("schimmelfennig", (-50, 1050)),
               ("krzyzanowski", (250, 1250)), ("stevens", (150, 1400)), ("nagle", (300, 1550)), ("ferrero", (-100, 1550)), ("grover", (-150, 1350)),
               ("taylor", (0, 1650)), ("carr", (200, 1750)), ("robinson", (-250, 1800)), ("birney", (-300, 2000)), ("poe", (-100, 1900)))
for id, end in UNION_RIGHT:
    mv(id, C("18:05"), C("18:50"), end, h=270, moving="retreat")
for id in ("taliaferro_ag", "stonewall", "jones_bj", "stafford", "lawton", "trimble", "thomas", "field"): stand(id, C("19:10"), state="line")
for id in ("hood", "corse", "jenkins", "hunton", "armistead", "wilcox", "evans", "law"): stand(id, C("18:00"), state="line")

# ---- seven: Lewis Ford. Robertson's cavalry round the south end; Buford meets it for ten minutes ----
walk("robertson", C("17:40"), (-1500, -3200), (1200, -2500), (2700, -1950), h=90, kmh=9)
show("buford", C("18:20"), (4480, -900), 240); walk("buford", C("18:20"), (3300, -1900), (2950, -1960), h=270, kmh=9)
mv("robertson", C("19:00"), C("19:03"), (2850, -1950), h=90, state="firing", moving="charge")
fight("robertson", C("19:03"), C("19:12"), lose("robertson", 100)); fight("buford", C("19:00"), C("19:12"), lose("buford", 150), h=270)
mv("buford", C("19:12"), C("19:35"), (3300, -1900), (3700, -1650), h=60, moving="retreat")
mv("robertson", C("19:20"), C("19:50"), (2200, -1900), h=250)

# ---- eight: Pope orders the retreat to Centreville, by the Stone Bridge and the turnpike, and by Lewis Ford ----
SOUTHERN = ("hardin", "seymour", "meade", "piatt", "chapman", "warren", "mclean", "milroy")
order = [id for id, end in UNION_RIGHT] + ["berdan", "hazlett", "stiles", "tower", "leppien", "koltes", "stahel", "buchanan"]
for n, id in enumerate(order):
    p = last(id); way = sudley(p, STONE_X) + pike(STONE_X, EAST_IN) if p[1] > 300 else pike(PIKE_AT(max(-90, min(1500, p[0]))), EAST_IN)
    hide(id, plus(walk(id, plus(C("20:00"), n * 3), *way, kmh=4), 1))
for n, id in enumerate(SOUTHERN):
    t0 = plus(C("20:10"), n * 6)
    hide(id, plus(walk(id, t0, (1600, -1500), (LEWIS_FORD[0] - 100, LEWIS_FORD[1] + 30), (LEWIS_FORD[0] + 100, LEWIS_FORD[1] - 10), (4450, -1700), kmh=3.5), 1))
hide("buford", plus(walk("buford", C("20:30"), (4450, -1500), kmh=6), 1))

for id in KEYS:
    if sec(KEYS[id][-1]["t"]) < sec(END): keys(id, [K(END, last(id))])

# ---- assemble and check ----
CROSSINGS = [P['stone_bridge'], LEWIS_FORD, P['sudley_ford']]
def wet(p): return dist_line(p, BULL_RUN) < 20 and min(math.dist(p, c) for c in CROSSINGS) > 150
units = []
TOP = {"infantry": 6, "riflemen": 6, "artillery": 6, "cavalry": 15}  # km/h, the fastest any leg may go
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
            assert not wet(q), (id, a["t"], b["t"], q, "a leg through Bull Run")
    state = None
    for k in ks:
        state = k.get("state", state)
        assert state == "hidden" or (not wet((k["x"], k["y"])) and max(abs(k["x"]), abs(k["y"])) <= 4500), (id, k["t"], (k["x"], k["y"]), "in Bull Run or off the map")
    units.append(dict(id=id, side=side, name=name, short=short, commander=commander, type=type, strength=strength, keys=ks, **extra))
for f in features:
    if "at" in f: assert not wet(f["at"]) and max(map(abs, f["at"])) <= 4500, (f.get("name"), "a label in Bull Run or off the map")
# Chapters: (time, title, text, camera centre, metres across, playback speed, clock time the sources record or None).
# Times are Greene's and the Park Service panels', with Jackson's report, the 13th Massachusetts and Wikipedia where
# they are silent. Porter's attack is 2:30 to 4 in the sources; this replay takes Greene's three.
CHAPTERS = [
    (A("05:30"), "Jackson behind the railroad", "On the 27th Hill's and Taliaferro's divisions moved to Manassas Junction, south of this map, and routed Taylor's New Jersey brigade there; Taylor was mortally wounded. At nine that night Taliaferro's division marched up the Manassas-Sudley road, reached the turnpike near the Stone House at midnight, crossed it near Groveton and halted near the battlefield of July 1861, in the woods of Stony Ridge, 1,000 yards north of the turnpike. Ewell's and Hill's divisions, misdirected across Bull Run, Hill all the way to Centreville, join Jackson today.", [300, 400], 7000, 300, "sunrise"),
    (A("14:00"), "McDowell on the turnpike", "About ten this morning McDowell's corps pushed east on the turnpike, Reynolds's division leading, then King's four brigades, Ricketts's division in the rear. Ricketts turned off to Thoroughfare Gap, 16 km west, where Wyndham's troopers met Longstreet's vanguard at half past nine; by two he had only reached Haymarket. Jackson's divisions lie in the woods of Stony Ridge, unseen.", [-2700, -700], 3500, 300, None),
    (A("18:30"), "Brawner farm", "About five McDowell had Pope's order to march to Centreville, King's division leading. About half past six Jackson's guns on Stony Ridge open on Gibbon's brigade on the turnpike. 'By this time it was sunset,' Jackson reported. 'I determined to attack at once, which was vigorously done by the divisions of Taliaferro and Ewell.' Gibbon turns north into the Brawner farm to meet them.", [-2750, -600], 1800, 60, "about 6:30 PM"),
    (A("20:00"), "Seventy-five yards apart", "The two lines trade volleys 75 yards apart. Trimble's and Lawton's brigades attack without coordination; A. G. Taliaferro's three regiments go against the 19th Indiana, and Pelham's guns fire at the Hoosiers from less than 100 yards. After dark Doubleday's 56th Pennsylvania and 76th New York go into the gap between the 6th and 7th Wisconsin, and fire at the muzzle flashes.", [-2750, -380], 1500, 60, None),
    (A("21:00"), "Back to the turnpike", "Both lines stood 'exposed to the discharges of musketry and artillery until about 9 o'clock,' Jackson reported. At nine Gibbon and Doubleday withdraw to the turnpike in good order. Of about 7,000 men engaged, nearly a third have fallen: about 1,150 Federals and 1,250 Confederates. Ewell and W. B. Taliaferro are wounded.", [-2700, -600], 1800, 300, "9 PM"),
    (B("00:00"), "King's division marches off", "At midnight King's division leaves the turnpike for Manassas. At daybreak Pope learns that Ricketts and King have gone south.", [-1000, -1800], 5000, 600, "midnight"),
    (B("07:00"), "Schurz finds Jackson", "Jackson's line runs about 3,000 yards along the unfinished railroad, from near the turnpike toward Sudley Church: his own division under Starke on the right, Ewell's under Lawton in the centre, A. P. Hill's on the left by the church, Gregg's and Thomas's brigades in front. About 20,000 men. Sigel's corps, fewer than 12,000, comes on. Schurz's division, north on the Sudley road, finds Jackson about seven and skirmishes with Gregg and Thomas in the woods south of the railroad; Milroy moves on the centre, Schenck and Reynolds west on the turnpike toward Groveton.", [-900, 1300], 3500, 120, "about 7 AM"),
    (B("10:00"), "The 82nd Ohio at the Dump", "'About 10 o'clock the Federal artillery opened with spirit and animation upon our right,' Jackson reported. Sigel's offensive runs until ten, Schurz making a second assault on Hill's division. Milroy's two regiments are repulsed along the Groveton-Sudley road by Lawton, and part of the 82nd Ohio breaks briefly into the line near the Dump, a 75-yard low point in the grade. Schenck and Reynolds come under heavy artillery fire in the woods around Groveton.", [-1500, 500], 2800, 60, "about 10 AM"),
    (B("11:00"), "Longstreet from Gainesville", "Late in the morning Lee arrives with Longstreet's wing, 25,000 men in five divisions, on the march from Thoroughfare Gap since six. Hood's division forms astride the turnpike at the Brawner farm, Kemper's on its right, D. R. Jones's out toward the Manassas Gap Railroad, Wilcox's behind Hood. Lee makes his headquarters on Stuart's Hill.", [-3200, -1700], 3600, 120, "late in the morning"),
    (B("13:00"), "Pope on the field", "Pope reaches the field at one. Hooker's division and Stevens's come up to reinforce Sigel, and Kearny's and Reno's divisions come up as well. About two, by Jackson's report, 'the Federal infantry in large force advanced to the attack of our left.'", [-300, 900], 3500, 120, "1 PM"),
    (B("15:00"), "Grover's bayonet charge", "About three Cuvier Grover's brigade, five regiments and about 1,500 men, attacks with bayonets fixed along a front about a quarter mile wide, into the 125-yard gap between Thomas's and Gregg's brigades. Gregg's regiments strike its flank and Pender's brigade its front, and within 30 minutes Grover's men fall back. The brigade loses 487.", list(gp(820, 150)), 1400, 60, "about 3 PM"),
    (B("17:00"), "Kearny at Sudley", "About four Hays's brigade, under Forno, came to help Gregg, and Early's came up to relieve him. At five Phil Kearny attacks Hill's Light Division with nearly 3,000 men and breaks through the unfinished railroad. Gregg's brigade is badly hit, and Branch's North Carolinians and Jubal Early's troops stop and push back the attack; Early 'drove them from the wood and railroad cut.' Hill reports six separate and distinct assaults met and repulsed today.", list(gp(380, 0)), 1500, 60, "5 PM"),
    (B("19:00"), "Hood and Hatch at dusk", "At sunset Hood's brigades, parts of Wilcox's and Kemper's divisions behind them, go forward south of the turnpike in a reconnaissance in force. About seven they meet Hatch's division, King's under Hatch, near Groveton, in a brief, violent clash in the dark, and the Union troops fall back. At half past four Pope sent Porter an explicit order; it was delivered at half past six. Porter's corps stands at Dawkins Branch, off this map to the south-west.", [-1500, -550], 2000, 60, "7 PM"),
    (B("20:50"), "The night of the 29th", "At ten to nine Pope orders Fitz John Porter to join the army by morning. In the dark Hood draws back to the Brawner farm.", [-1500, -400], 5000, 600, "8:50 PM"),
    (C("03:00"), "Anderson's division in the dark", "At three in the morning Richard H. Anderson's division arrives after a seventeen-mile march and halts east of Groveton. At dawn, finding itself alone, it falls back. Longstreet's last divisions and his reserve artillery come up before dawn.", [-2400, -950], 3500, 300, "3 AM"),
    (C("08:00"), "Pope's council on Buck Hill", "At eight Pope holds a council of war at his headquarters above the Stone House on Buck Hill. About 70,000 Northerners face 55,000 Southerners; about 25,000 men of the Army of the Potomac are held back, Franklin's corps at Annandale and Sumner's.", [0, 300], 3500, 300, "8 AM"),
    (C("11:00"), "Ricketts is repulsed", "At ten Ricketts, Stevens and Reynolds reconnoitre and find Jackson's men still firmly in position. Late in the morning Ricketts attacks and is repulsed by Jackson's line.", list(gp(1400, 300)), 2400, 120, "late in the morning"),
    (C("13:00"), "Pope orders the attack", "Shortly after noon Pope orders Porter's corps, with Hatch and Reynolds in support, west along the turnpike; at one he orders Porter's two divisions and Hatch's to assault. Porter's corps, about 10,000 men, takes nearly two hours to form. Reynolds goes back to Chinn Ridge, where McLean's Ohio brigade reinforces him: about 8,000 Federals south of the turnpike against Longstreet's roughly 30,000. Eighteen guns, S. D. Lee's, are placed north-east of the Brawner farm to support Jackson's right.", [-1300, -350], 4000, 120, "1 PM"),
    (C("15:00"), "Porter at the Deep Cut", "Berdan's sharpshooters opened the fight at half past two and skirmished for nearly 30 minutes. At three Porter attacks: Weeks's and Roberts's brigades on the left and centre, Hatch's division on the right, Sykes's two regular brigades in reserve. Porter's men cross 600 yards of pasture, the last 150 rising sharply uphill; Hatch's, 300 yards. Starke's division holds the railroad: Stafford's Louisianians near the Dump, Bradley Johnson's Virginians at the Deep Cut, the Stonewall Brigade and Taliaferro's men on the right. S. D. Lee's guns fire into the Union ranks from the heights north of the Brawner farm, and Lawton's division and Field's Virginia brigade come up to finish the repulse. Baylor of the Stonewall Brigade is killed.", [-1950, 250], 1800, 30, "3 PM"),
    (C("16:00"), "Hood overruns Warren", "McDowell has sent Reynolds across the turnpike, leaving about 2,200 men south of it, McLean's brigade and Warren's. At four Longstreet attacks. Hood's division, with the Texas Brigade and Evans's South Carolinians, leads on the left near the turnpike, Kemper's division on its right, D. R. Jones's brigades in support. Warren's two New York regiments, roughly 1,000 men beside Hazlett's six-gun battery on a knoll above Groveton, are overrun along Lewis Lane. The 5th New York loses almost 300 of its roughly 500 men in the first ten minutes.", [-1500, -900], 2400, 30, "4 PM"),
    (C("16:30"), "McLean on Chinn Ridge", "McLean's Ohio brigade, about 1,200 men, holds Chinn Ridge, 800 yards east of Warren's ground, until Corse's Virginia brigade attacks; heavy firing at the fence line lasts about ten minutes. Evans's charge on McLean's flank is repulsed. The Ohioans lose about a third and buy Pope roughly 30 minutes. McDowell orders Ricketts to disengage and reinforce the left on Chinn Ridge, and Hardin's brigade is shattered there.", [-250, -1000], 1800, 30, "4:30 PM"),
    (C("17:30"), "The 5th Maine's guns", "Ricketts's brigades come from north of the turnpike by the Stone House, over Young's Branch and up the ridge, Tower's leading, Stiles's behind, Koltes's and Stahel's with them. Tower's brigade covers Leppien's 5th Maine Battery, five guns; after a fight of about 30 minutes the Confederates take four. Tower is badly wounded, Koltes is killed, and Fletcher Webster of the 12th Massachusetts falls, mortally wounded. Hunton's and Jenkins's brigades fire into the Union line from the Chinn Branch swale. By about six Longstreet holds Chinn Ridge.", [-200, -950], 1600, 30, "5:30 PM"),
    (C("18:00"), "Jackson off the railroad", "At six Jackson's divisions attack north of the turnpike. They come down off the grade across the Dogan farm and overrun Union artillery and infantry, and the Union right falls back east.", [-500, 500], 3500, 30, "6 PM"),
    (C("18:30"), "Henry Hill", "Pope has formed a four-brigade line along the western slope of Henry Hill, nearly half a mile from the ruins of the Henry house to the south end of the plateau, with two more brigades in reserve. About five Lee sent Dick Anderson's three brigades, with part of Wilcox's division, from the Brawner farm toward Chinn Ridge, and Benning's and G. T. Anderson's Georgians, about 3,000 men, against Henry Hill. Milroy's brigade holds the washed-out bed of the Sudley road; the Georgians charge again and again and fall back to Chinn Branch, until the 15th Georgia breaks the Union line. Mahone's and Wright's brigades come up on the Confederate right and push the Union reserves back toward the Henry house.", [450, -850], 1800, 30, "6:30 PM"),
    (C("19:00"), "Lewis Ford", "About seven Pope has an unbroken line north of the turnpike, aligned with Henry Hill. Stuart's cavalry tries to get round the Union left at Lewis Ford, Robertson's brigade with the 2nd Virginia under Munford charging, and Buford's cavalry blocks it in a fight of about ten minutes. Buford is wounded. Darkness has come on, and a drizzling rain.", [1700, -1300], 3500, 60, "about 7 PM"),
    (C("20:00"), "Pope orders the retreat", "At eight Pope orders a general withdrawal to Centreville, and it is orderly. The stone bridge over Bull Run lets most of the army go back by the turnpike. The Cub Run bridge, beyond the map, jams in the night.", [1400, 300], 4500, 120, "8 PM"),
    (C("22:50"), "The field at night", "About eleven Pope's troops have left the field and begin entering the Centreville defenses. In the morning Jackson found 'that the Federal Army had retreated in the direction of Centreville.' On 1 September the armies meet again at Chantilly, in a thunderstorm; Kearny and Stevens are killed there.", [-500, -200], 8000, 120, "about 11 PM"),
]
events = [dict(t=t, title=a, text=b, at=at_, view=v, speed=s, **({"when": w} if w else {})) for t, a, b, at_, v, s, w in CHAPTERS]
for e in events:  # without `when` the card speaks the nearest hour (app.js chapterWhen), so it must be near the frame's clock
    s = sec(e["t"]) % 86400; hh = [n % 12 or 12 for n in (int(s // 3600), int(s // 3600) + 1)]; num = re.search(r"\d+", e.get("when", ""))
    assert not num or int(num[0]) in hh, (e["t"], e["when"], "the card's hour is not the frame's")
    assert "when" in e or abs(s - math.floor(s / 3600 + 0.5) * 3600) <= 15 * 60, (e["t"], e["title"], "give it a when")
    assert e["speed"] in (1, 2, 5, 10, 20, 30, 60, 120, 300, 600, 1800, 3600, 7200), (e["title"], e["speed"], "not a speed the menu offers (sim.js SPEEDS)")

battle = dict(
    id="second-manassas", name="Second Manassas", date="1862-08-28", dateText="28 to 30 August 1862", place="Bull Run, near Manassas Junction, Virginia",
    origin=dict(lat=LAT0, lon=LON0), extent=9000, start=START, end=END, sunrise="05:25", sunset="18:38", speed=60, lapse=7200, menPerDot=20,
    terrainExaggeration=2, contourInterval=3, trees=dict(density=0.0004), fields=FIELDS, wind=dict(x=0.5, y=0.3), view=dict(x=-1000, y=0, width=9000),
    # Bachelder's convention, Union blue and Confederate red
    sides=dict(union=dict(name="Union (Pope)", color="#2c4f96", light="#6f8fca", dark="#16294f"),
               confederate=dict(name="Confederate (Lee)", color="#b23a2e", light="#d77a6c", dark="#5c1a14")),
    tints=[dict(color="rgba(150,156,164,0.35)", **{"from": C("19:00"), "until": END})],  # "darkness had now come on and a drizzling rain"
    features=features, units=units, events=events,
    outcome={"result": "Confederate victory: Pope's army falls back to Centreville", "losses": [
        ["union", "14,462: 1,747 killed, 8,452 wounded, 4,263 captured or missing. Greene counts nearly 10,000 killed and wounded. Koltes killed and Fletcher Webster mortally wounded; Hatch, Tower, Schenck, Buford and Sigel among the wounded."],
        ["confederate", "7,298: 1,096 killed, 6,202 wounded; another count gives 7,387 with 89 missing, and Greene about 1,300 killed and more than 7,000 wounded. Baylor killed; Ewell and W. B. Taliaferro wounded on the 28th, Trimble, Field and Forno on the 29th, Mahone, Jenkins and Corse on the 30th."]],
        "note": "About 62,000 Union and 50,000 Confederate troops were engaged. At the Brawner farm on the 28th about 1,150 Federals and 1,250 Confederates fell; Grover's brigade lost 487 on the 29th; on the 30th the 5th New York lost 297 of about 500, McLean's brigade about a third, the Texas Brigade 628."},
    sources=[
        "A. Wilson Greene, <i>The Second Battle of Manassas</i>, National Park Service Civil War Series (Eastern National, 2006), read at <a href='https://npshistory.com/publications/civil_war_series/18/' target='_blank'>npshistory.com</a>: the clock times and the order of the attacks, from Taliaferro's night march to the retreat, and the strengths of Grover's, McLean's and Warren's brigades.",
        "T. J. Jackson's report of the operations of 15 August to 5 September 1862, <i>Official Records</i> Series I, vol. 12, part 2, as transcribed by the <a href='https://www.battlefields.org/learn/primary-sources/battle-second-manassas-official-report-lieut-general-thomas-j-jackson' target='_blank'>American Battlefield Trust</a>, with the Trust's maps of the 29th and 30th.",
        "National Park Service, Manassas National Battlefield Park: 'Battle of Second Manassas' and the tour stops and panels at the Brawner farm, the unfinished railroad, Sudley, Chinn Ridge, the 5th Maine's guns and Henry Hill, each dated to the hour.",
        "Wikipedia, 'Second Battle of Bull Run', its Union and Confederate orders of battle, 'Battle of Thoroughfare Gap' and 'Texas Brigade' (read 25 October 2026), for the organisation, the army totals, the losses and the times the Park Service does not give. The 13th Massachusetts' letters and timeline at <a href='https://13thmass.org/1862/second_bull_run.html' target='_blank'>13thmass.org</a>, and Warren's brigade from his report and the regimental returns at ironbrigader.com.",
        "Terrain: USGS 3DEP elevation at 10 m, sampled to 22.5 m, with three modern quarries filled. Farms, ruins, monuments, hills, the railroad grade, the roads and the streams from OpenStreetMap (ODbL). Sunrise and sunset from the NOAA solar formulae for Groveton, local mean time.",
        "What is reconstructed: John Hennessy's <i>Return to Bull Run</i> and his troop-movement maps for the Park Service were not consulted, so most brigade strengths are estimates (1,500 to a brigade of the Army of Virginia, 1,800 to one of the Army of the Potomac, 1,400 to one of Jackson's and 1,700 to one of Longstreet's), and the positions between the recorded times are inferred, as are the losses of every brigade the sources do not count. The woods are drawn from the sources' descriptions, not from an 1862 map. Lewis Lane, Lewis Ford and Portici are placed within 200 to 500 m. Reynolds's and King's routes on the 28th and 29th, Ricketts's and Porter's approaches, and the routes of the retreat are inferred from the roads. Grover's attack is set where Thomas's brigade met Gregg's, 600 m north-east of the Dump. Longstreet's line of the 29th is taken from his order of the 30th, and Hood's twilight clash is set by Groveton, as Greene has it.",
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
