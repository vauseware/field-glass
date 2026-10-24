# Builds battles/fort-fisher/battle.json. Run from the repo root: python3 battles/fort-fisher/make.py
# Local metres from 33.9690N 77.9240W (x east, y north). The 4 km square holds the L of the fort, Battery Buchanan at
# the tip of Federal Point (-1598,-962), the beach north of the fort where the naval column formed, and the inshore
# fleet. The landing beach of 13 January near Myrtle Sound (four miles north), Terry's line from Battery Anderson to the
# river and Hoke's division at Sugar Loaf lie beyond the north edge; the Union columns come on there. Shepherd's Battery,
# the Northeast Bastion and Battery Buchanan are the Coast Survey's points; the traverses are spaced evenly along the
# 385 m between the first two; the sea face and the Mound Battery are placed from Comstock's two sheets of 1865, which
# disagree by about 300 m on the Mound, so it is put between them, about 1,000 m from the bastion. Since 1865 the sea
# has taken the bastion, 2,100 ft of the sea face and 100 ft of the land face, and New Inlet, south of Buchanan, has
# closed: the DEM is raised to beach height over the lost strip and the inlet is drawn as a water polygon.
import json, math
HERE = "battles/fort-fisher/"
LAT0, LON0 = 33.9690, -77.9240
KX, KY = 111320 * math.cos(math.radians(LAT0)), 111320  # tools/fetch_terrain.py's metres per degree
def M(lat, lon): return (round((lon - LON0) * KX), round((lat - LAT0) * KY))

# ---- terrain: the 3DEP tiles return noise over open water; the 1865 beach and sea face are raised from the sea ----
T = json.load(open(HERE + "terrain.json"))
COLS, SP = T["cols"], T["spacing"]; HALF = COLS * SP / 2
def inside(x, y, poly):
    c = False
    for i in range(len(poly)):
        (xa, ya), (xb, yb) = poly[i], poly[i - 1]
        if (ya > y) != (yb > y) and x < xa + (xb - xa) * (y - ya) / (yb - ya): c = not c
    return c
# The strip the sea took: 100 m of beach outside the land face and north of it, and the sea face down to the Mound.
LOST = [(1120, 1000), (1050, 500), (900, 250), (760, 30), (560, -420), (260, -920), (120, -1020), (-100, -1020), (-100, -600), (400, -60), (650, 350), (800, 1000)]
before = list(T["z"])
Z = [v if -5 < v < 50 else -1.0 for v in T["z"]]      # nodata, NaN and garbage over the sea
land = {i for i, v in enumerate(Z) if v > 0.3}
seen = set()
for s in land:                                           # drop specks of "land" in the sea: components under 60 cells
    if s in seen: continue
    comp, stack = [], [s]; seen.add(s)
    while stack:
        i = stack.pop(); comp.append(i)
        for j in (i - 1, i + 1, i - COLS, i + COLS):
            if j in land and j not in seen and abs(j % COLS - i % COLS) <= 1: seen.add(j); stack.append(j)
    if len(comp) < 60:
        for i in comp: Z[i] = -1.0
for i, v in enumerate(Z):
    x, y = (i % COLS + 0.5) * SP - HALF, HALF - (i // COLS + 0.5) * SP
    if v < 1.5 and (inside(x, y, LOST) or math.dist((x, y), (-1598, -962)) < 75): Z[i] = 2.0   # the 1865 beach, barely above the tide, and Buchanan's eroded mound
T["z"] = Z
if T["z"] != before: json.dump(T, open(HERE + "terrain.json", "w"), separators=(",", ":"))

# ---- geography ----
SHEP, BASTION, HQ, BUCHANAN = (415, 334), (675, 50), (533, 41), (-1598, -962)   # Coast Survey points and the UDC column
MOUND, PULPIT, HOLLAND = (120, -880), (610, -90), (970, 720)                        # see the header; Holland is "500 yards north of the fort"
GATE = (392, 356)            # the River Road gate at the river end of the land face, over the slough by a causeway and bridge
FACE = (BASTION[0] - SHEP[0], BASTION[1] - SHEP[1]); FL = math.hypot(*FACE)        # the land face, 385 m, bearing 138
FU, FN = (FACE[0] / FL, FACE[1] / FL), (-FACE[1] / FL, FACE[0] / FL)               # along it, and its outward normal (north-east)
def face(f, d=0): return (round(SHEP[0] + FU[0] * f * FL + FN[0] * d), round(SHEP[1] + FU[1] * f * FL + FN[1] * d))  # f along the face, d metres outside it
IN = round(math.degrees(math.atan2(-FN[0], -FN[1])) % 360)   # the heading of an assault on the land face, 228
OUT = (IN + 180) % 360
ALONG = round(math.degrees(math.atan2(*FU)) % 360)            # along the face toward the bastion, 138
SEA = [BASTION, (700, 10), (640, -120), (560, -260), (470, -420), (380, -560), (290, -690), (200, -800), MOUND]   # the sea face to the Mound
SEA_DIR = math.atan2(MOUND[0] - BASTION[0], MOUND[1] - BASTION[1])
def sea(d, w=0):  # d metres down the sea face from the bastion, w metres inland of it
    return (round(BASTION[0] + math.sin(SEA_DIR) * d + math.cos(SEA_DIR) * w), round(BASTION[1] + math.cos(SEA_DIR) * d - math.sin(SEA_DIR) * w))
RIVER_RD = [(640, 2000), (560, 1500), (470, 1000), (430, 700), (410, 480), GATE]  # the road down the peninsula to the river gate
BEACH = [(1180, 2000), (1120, 1500), (1020, 1000), (900, 600), (800, 300), (720, 120)]  # the 1865 beach north of the bastion
WHARF = (-1480, -900)        # Buchanan's steamer wharf, on the river side
PLAIN = [sea(500, 45), sea(900, 45), (-300, -920), (-1100, -940), WHARF]   # the way across the sand plain from the fort to Buchanan
def rect(c, h, w, d, back=0):  # a rectangle w across the heading h, from `back` to d along it
    s, co = math.sin(math.radians(h)), math.cos(math.radians(h))
    return [[round(c[0] + a * co + b * s), round(c[1] - a * s + b * co)] for a, b in [(-w / 2, back), (w / 2, back), (w / 2, d), (-w / 2, d)]]
def ship(c, L=70, W=16, rot=0):
    co, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return [[round(c[0] + co * dx - s * dy), round(c[1] + s * dx + co * dy)] for dx, dy in [(-L / 2, -W / 2), (L / 2 - 8, -W / 2), (L / 2, 0), (L / 2 - 8, W / 2), (-L / 2, W / 2)]]
def ellipse(c, a, b, n=16): return [[round(c[0] + a * math.cos(2 * math.pi * i / n)), round(c[1] + b * math.sin(2 * math.pi * i / n))] for i in range(n)]

# ---- the clock: 13 to 15 January 1865 ----
def D(day, hm): return f"1865-01-{day:02d} {hm}"
def sec(t): h, m = map(int, t[11:].split(":")); return ((int(t[8:10]) - 13) * 24 + h) * 3600 + m * 60   # seconds from midnight on the 13th
def fmt(s): m = round(s / 60); return D(13 + m // 1440, f"{m % 1440 // 60:02d}:{m % 60:02d}")
def plus(t, mins): return fmt(sec(t) + mins * 60)
def K(t, p, **kw): return dict(t=t, x=round(p[0]), y=round(p[1]), **kw)
def heading(a, b): return round(math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) % 360)
def march(t0, t1, pts, state="column", **kw):  # keys along a path, times spread by distance; heading follows the path
    pts = [p for i, p in enumerate(pts) if i == 0 or math.dist(p, pts[i - 1]) > 5]
    if len(pts) < 2: return [K(t0, pts[0], state=state, **kw)]
    d = [0]
    for a, b in zip(pts, pts[1:]): d.append(d[-1] + math.dist(a, b))
    out = []
    for i, p in enumerate(pts):
        h = heading(p, pts[i + 1]) if i + 1 < len(pts) else out[-1]["h"]
        out.append(K(fmt(sec(t0) + (sec(t1) - sec(t0)) * d[i] / d[-1]), p, h=h, **(dict(state=state, **kw) if i == 0 else {})))
    return out
def go(t0, t1, pts, h, state="line", moving="column", **kw): return march(t0, t1, pts, moving)[:-1] + [K(t1, pts[-1], h=h, state=state, **kw)]
units = []
def unit(id, side, short, name, commander, type, strength, keys, **extra):
    units.append(dict(id=id, side=side, name=name, short=short, commander=commander, type=type, strength=strength, keys=keys, **extra))
def U(id): return next(u for u in units if u["id"] == id)
us = lambda *a, **k: unit(a[0], "union", *a[1:], **k)
cs = lambda *a, **k: unit(a[0], "confederate", *a[1:], **k)
END = D(15, "22:30")

# ---- the fleet: Line No. 1, the ironclads and the ships that fit the frame, as batteries on the water over a hull ----
# They come in from the east on the morning of the 13th and fire through daylight on three days; at 3:25 on the 15th
# the wooden ships lift their fire and the ironclads keep shelling the land face ahead of the assault.
SHIPS = [("ironsides", "New Ironsides", "USS New Ironsides, broadside ironclad, the head of Line No. 1", "Commodore William Radford", 7, (1480, 420), 76),
         ("monadnock", "Monadnock", "USS Monadnock, double-turreted monitor", "", 4, (1530, 170), 68), ("canonicus", "Canonicus", "USS Canonicus, monitor", "", 2, (1570, -90), 68),
         ("saugus", "Saugus", "USS Saugus, monitor", "", 2, (1540, 660), 68), ("mahopac", "Mahopac", "USS Mahopac, monitor", "", 2, (1590, 900), 68),
         ("brooklyn", "Brooklyn", "USS Brooklyn, steam sloop, with the gunboats of Line No. 1", "Capt. James Alden", 6, (1850, 280), 72),
         ("gb1", "gunboat", "Gunboat of Line No. 1", "", 3, (1900, 560), 60), ("gb2", "gunboat", "Gunboat of Line No. 1", "", 3, (1900, 20), 60),
         ("gb3", "gunboat", "Gunboat of Line No. 1", "", 3, (1880, -260), 60), ("gb4", "gunboat", "Gunboat of Line No. 1", "", 3, (1850, -560), 60),
         ("gb5", "gunboat", "Gunboat of Line No. 1", "", 3, (1880, 860), 60), ("gb6", "gunboat", "Gunboat of Line No. 1", "", 3, (1860, 1180), 60)]
IRONCLADS = ("ironsides", "monadnock", "canonicus", "saugus", "mahopac")
ship_features = []
for id, short, name, cmd, guns, st, L in SHIPS:
    h = heading(st, BASTION); iron = id in IRONCLADS
    ks = go(D(13, "07:20"), D(13, "08:30"), [(1995, st[1] + 60), st], h)
    for day in (13, 14):
        ks += [K(D(day, "09:00" if day == 13 else "08:00"), st, state="firing", fire=0.6 if iron else 0.4), K(D(day, "17:15"), st, state="line")]
    ks += [K(D(15, "08:00"), st, state="firing", fire=0.8 if iron else 0.5)]
    ks += [K(D(15, "15:25"), st, fire=0.3), K(D(15, "17:30"), st, state="line"), K(END, st)] if iron else [K(D(15, "15:25"), st, state="line"), K(END, st)]
    us(id, short, name, cmd, "artillery", guns * 15, ks, guns=guns)
    ship_features.append(dict(type="ship", poly=ship(st, L, 16 if iron else 13, 180 - h), **{"from": D(13, "08:30")}))  # broadside on, the hull along the shore

# ---- Union: the landing force comes on at the north edge on the evening of the 13th ----
# Terry's line from Battery Anderson to the river, two miles north of the fort, is beyond the frame: Paine's two
# brigades stand for it at the north edge, facing Hoke. Strengths are the division aggregates split evenly by brigade
# and regiment, since the returns by regiment were not found.
EDGE = (640, 1995)
def arrive(id, short, name, cmd, n, t_in, spot, h, state="line", **extra):
    path = [EDGE] + [p for p in RIVER_RD[1:] if p[1] > spot[1] + 60] + [spot]
    us(id, short, name, cmd, "infantry", n, go(t_in, plus(t_in, 40 + round(math.dist(EDGE, spot) / 60)), path, h, state), **extra)
arrive("paine2", "Ames's U.S.C.T.", "2nd Brigade, Paine's division: 4th, 6th, 30th and 39th U.S. Colored Troops, on the line facing Hoke", "Col. John W. Ames", 1640, D(13, "17:00"), (560, 1820), 0, ranks=8)
arrive("paine3", "Wright's U.S.C.T.", "3rd Brigade, Paine's division: 1st, 5th, 10th and 37th U.S. Colored Troops, on the line facing Hoke", "Col. Elias Wright", 1640, D(13, "17:20"), (1000, 1820), 0, ranks=8)
for id in ("paine2", "paine3"): U(id)["keys"].append(K(END, (U(id)["keys"][-1]["x"], U(id)["keys"][-1]["y"])))
# Ames's division bivouacs on the peninsula north of the fort; the 27th U.S.C.T. comes with it.
AMES = [  # id, short, name, commander, strength, bivouac
    ("ny3", "3rd N.Y.", "3rd New York (Curtis's brigade)", "", 350, (470, 1180)), ("ny112", "112th N.Y.", "112th New York (Curtis's brigade)", "", 350, (560, 1180)),
    ("ny117", "117th N.Y.", "117th New York (Curtis's brigade), whose colours went up on Shepherd's Battery", "", 350, (650, 1180)),
    ("ny142", "142nd N.Y.", "142nd New York (Curtis's brigade), which came within 75 yards of this battery on Christmas Day", "", 355, (740, 1180)),
    ("ny47", "47th N.Y.", "47th New York (Pennypacker's brigade)", "", 280, (480, 1290)), ("ny48", "48th N.Y.", "48th New York (Pennypacker's brigade)", "", 280, (570, 1290)),
    ("pa76", "76th Pa.", "76th Pennsylvania (Pennypacker's brigade)", "", 280, (660, 1290)),
    ("pa97", "97th Pa.", "97th Pennsylvania (Pennypacker's brigade); Pennypacker fell planting its colours on the third traverse", "", 290, (750, 1290)),
    ("pa203", "203rd Pa.", "203rd Pennsylvania (Pennypacker's brigade), which broke the sandbagged river gate", "", 285, (840, 1290)),
    ("in13", "13th Ind.", "13th Indiana (Bell's brigade), less its sharpshooters", "", 295, (500, 1400)), ("nh4", "4th N.H.", "4th New Hampshire (Bell's brigade)", "", 355, (590, 1400)),
    ("ny115", "115th N.Y.", "115th New York (Bell's brigade)", "", 355, (680, 1400)), ("ny169", "169th N.Y.", "169th New York (Bell's brigade)", "", 355, (770, 1400)),
]
BIV, STR = {r[0]: r[5] for r in AMES}, {r[0]: r[4] for r in AMES}
for n, (id, short, name, cmd, s, biv) in enumerate(AMES):
    arrive(id, short, name, cmd, s, plus(D(13, "17:40"), 6 * n), biv, 180, ranks=4)
us("sharps", "13th Ind. sharpshooters", "Sharpshooters of the 13th Indiana, within 175 yards of the western salient by two", "", "riflemen", 60,
   go(D(15, "12:30"), D(15, "14:00"), [(500, 1400), (470, 900), face(0.12, 160)], IN, "skirmish") + [K(D(15, "15:25"), face(0.12, 160), state="charge"), K(D(15, "15:33"), face(0.06, 20), state="firing", strength=52),
   K(D(15, "16:00"), face(0.06, -20), state="line"), K(END, face(0.06, -20))], loose=True)
ABBOTT = [("ct6", "6th Conn.", "6th Connecticut (Abbott's brigade)", "", 300, (880, 1560)), ("ct7", "7th Conn.", "7th Connecticut (Abbott's brigade)", "", 300, (970, 1560)),
          ("nh3", "3rd N.H.", "3rd New Hampshire (Abbott's brigade)", "", 300, (1060, 1560)), ("nh7", "7th N.H.", "7th New Hampshire (Abbott's brigade)", "", 300, (1150, 1560)),
          ("ny16ha", "16th N.Y. H.A.", "Detachment of the 16th New York Heavy Artillery, serving as infantry with Abbott", "", 294, (1240, 1560))]
for n, (id, short, name, cmd, s, biv) in enumerate(ABBOTT):
    arrive(id, short, name, cmd, s, plus(D(13, "19:00"), 6 * n), biv, 0, ranks=4)
arrive("usct27", "27th U.S.C.T.", "27th U.S. Colored Troops (Wright's brigade), sent down the sea face to Buchanan that night", "", 400, D(13, "19:30"), (860, 1680), 0, ranks=4)
PITS = [face(-0.05, 275), face(0.55, 275)]   # Curtis's rifle pits 300 yards north of the land face, dug on the 14th

# ---- Union: the assault, 15 January ----
# A front moves along the land face as the traverses fall: the first by 3:35, the third by 3:45, the fourth at four,
# the seventh by 4:45, the ninth in the evening, and the rest when the flank is turned. Regiments stand behind it in
# depth inside the parapet. The brigade losses are the official returns, split evenly.
FRONT = [(D(15, "15:35"), 0.06), (D(15, "15:45"), 0.19), (D(15, "16:00"), 0.25), (D(15, "16:45"), 0.44), (D(15, "20:00"), 0.56), (D(15, "20:40"), 0.8), (D(15, "21:00"), 0.95)]
def hold(back, lane, s, lost, start):  # a regiment following the front `back` of it, `lane` metres inside the face
    ks = []
    for i, (t, f) in enumerate(FRONT):
        if sec(t) < sec(start): continue
        ks.append(K(t, face(max(0.05, f - back), -lane), h=ALONG, state="firing" if i < len(FRONT) - 1 else "line", strength=s - round(lost * (i + 1) / len(FRONT))))
    return ks + [K(END, (ks[-1]["x"], ks[-1]["y"]))]
def assault(id, path, t_form, t_go, hit, back, lane, lost):
    """Form in line at the end of `path` on the 15th, charge at `t_go` to `hit` on the face, then fight along it."""
    s = STR[id]
    U(id)["keys"] += go(t_form, plus(t_form, 60), path, IN) + [K(t_go, path[-1], state="charge"), K(plus(t_go, 7), hit, state="firing", strength=s - lost // 3)] \
        + hold(back, lane, s - lost // 3, lost - lost // 3, plus(t_go, 10))
# Curtis: deployed 300 yards north at two; the axemen cut the palisade at 3:25 and the brigade lodged on the western salient.
for n, (id, f) in enumerate([("ny117", 0.04), ("ny142", 0.14), ("ny112", 0.24), ("ny3", 0.34)]):
    assault(id, [BIV[id], (520 + 70 * n, 900), face(f, 270)], D(15, "13:00"), D(15, "15:25"), face(f * 0.6 + 0.02, 12), 0.04 + 0.06 * n, 25 + 18 * n, 57)
# Pennypacker at 3:35, overlapping Curtis's right: the 203rd Pennsylvania breaks the river gate, the rest go over the palisade.
for n, (id, f) in enumerate([("pa203", -0.08), ("pa97", 0.02), ("ny47", 0.12), ("ny48", 0.22), ("pa76", 0.32)]):
    assault(id, [BIV[id], (500 + 70 * n, 900), face(f, 440)], D(15, "13:40"), D(15, "15:35"), GATE if id == "pa203" else face(max(0.02, f * 0.6), 12), 0.08 + 0.05 * n, 50 + 12 * n, 56)
# Bell at 3:50 over the causeway at the river gate; Bell shot crossing it.
for n, id in enumerate(["in13", "nh4", "ny115", "ny169"]):
    s, t_go = STR[id], plus(D(15, "15:50"), 3 * n)
    U(id)["keys"] += go(D(15, "14:20"), D(15, "15:20"), [BIV[id], (560, 1000), (470, 1000), (445 + 10 * n, 640 + 50 * n)], 190) + [K(t_go, (445 + 10 * n, 640 + 50 * n), state="charge"), K(plus(t_go, 5), GATE), K(plus(t_go, 9), face(0.03 + 0.04 * n, -40), state="firing", strength=s - 10)] \
        + hold(0.0 + 0.04 * n, 110 + 12 * n, s - 10, 19, plus(t_go, 12))
# Abbott's brigade through the river gate at six; in the evening it goes along inside the works and takes the last traverses.
for n, (id, short, name, cmd, s, biv) in enumerate(ABBOTT):
    f0, f1 = 0.16 + 0.08 * n, 0.6 + 0.08 * n
    U(id)["keys"] += go(plus(D(15, "17:15"), 5 * n), plus(D(15, "18:00"), 5 * n), [biv, (470, 1000), (430, 700), (410, 480), GATE, face(f0, -110)], ALONG) \
        + [K(plus(D(15, "19:30"), 4 * n), face(f0, -110), state="column"), K(plus(D(15, "20:05"), 4 * n), face(f1 - 0.1, -120), state="charge"),
           K(plus(D(15, "20:25"), 4 * n), face(f1, -45), state="firing", strength=s - 6), K(D(15, "21:00"), face(f1, -45), state="line"), K(END, face(f1, -45))]
# The 27th U.S.C.T. down the sea face to Buchanan at half past nine; the garrison surrenders there about ten.
U("usct27")["keys"] += [K(D(15, "20:40"), (860, 1680), state="column")] + march(D(15, "20:41"), D(15, "21:20"), [(860, 1680), (470, 1000), (430, 700), GATE, (430, 250), sea(140, 60)])[1:] \
    + march(D(15, "21:30"), D(15, "22:05"), [sea(140, 60)] + PLAIN[:-1] + [(-1340, -930)]) + [K(D(15, "22:10"), (-1340, -930), h=250, state="line", strength=395), K(END, (-1340, -930))]

# ---- Confederate: the garrison by sector, Hagood's men, Buchanan ----
# Lamb's deployment at 3:25: 250 at the western salient, 500 along the Northeast Bastion, Hagood's 350 in a commissary
# bombproof. The gun crews are the 36th North Carolina by sector; most land-face guns were in ruins by the night of the 14th.
BOMBARD = [(13, "09:00"), (14, "08:00"), (15, "08:00")]
def under_fire(p, h, n, fall, fire=None):  # a sector thinned by the shelling; a battery (fire given) answers the fleet by day
    ks = [K(D(13, "07:00"), p, h=h, state="line")]
    for day, t in BOMBARD:
        ks += ([K(D(day, t), p, state="firing", fire=fire)] if fire else []) + [K(D(day, "17:15" if day < 15 else "12:00"), p, state="line", strength=n - round(fall * (day - 12) / 3))]
    return ks
GIVE_UP = iter([(-1440, -900), (-1480, -950), (-1440, -1000), (-1540, -975), (-1400, -950), (-1520, -890), (-1560, -1000), (-1460, -1050)])
def to_buchanan(t0, p, n):  # the retreat down the sea face and across the sand plain to Buchanan at nine; the surrender about ten
    end = next(GIVE_UP)
    return [K(t0, p, state="retreat")] + march(plus(t0, 1), D(15, "21:45"), [p] + PLAIN[:-1] + [end], "retreat")[1:] \
        + [K(D(15, "21:50"), end, h=70, state="line", strength=n), K(D(15, "22:00"), end, state="surrender"), K(END, end)]
cs("salient", "Western salient", "The western salient: about 250 men at Shepherd's Battery and the river gate", "Col. William Lamb", "infantry", 250,
   under_fire(face(0.08, -20), OUT, 250, 20) + [K(D(15, "14:00"), face(0.08, -20), state="firing"), K(D(15, "15:33"), face(0.08, -20), strength=205), K(D(15, "15:36"), face(0.22, -25), state="retreat", h=OUT),
   K(D(15, "15:45"), face(0.3, -25), state="firing", strength=180), K(D(15, "16:00"), face(0.23, -20), state="charge"), K(D(15, "16:08"), face(0.33, -25), state="firing", strength=140),
   K(D(15, "16:45"), face(0.5, -25), strength=110), K(D(15, "20:00"), face(0.62, -25), strength=90), K(D(15, "20:40"), face(0.85, -30), strength=70)] + to_buchanan(D(15, "21:00"), face(0.85, -30), 65), ranks=4)
cs("gateguns", "Gate guns", "A Parrott rifle and a 12-pounder Napoleon at the river gate", "", "artillery", 20,
   [K(D(13, "07:00"), (408, 338), h=OUT, state="line"), K(D(15, "15:25"), (408, 338), state="firing"), K(D(15, "15:38"), (408, 338), state="surrender", strength=12), K(D(15, "16:30"), (408, 338), state="hidden")], guns=2)
cs("landface", "Land-face guns", "The land-face gun crews, 36th North Carolina: 24 guns among the traverses, most dismounted by the night of the 14th", "Maj. James Reilly", "infantry", 300,
   under_fire(face(0.5, -14), OUT, 300, 110) + [K(D(15, "15:25"), face(0.5, -14), state="firing"), K(D(15, "15:45"), face(0.5, -14), strength=175), K(D(15, "15:50"), face(0.58, -18), state="retreat", h=OUT),
   K(D(15, "16:00"), face(0.4, -18), state="charge"), K(D(15, "16:10"), face(0.55, -18), state="firing", strength=150), K(D(15, "16:45"), face(0.66, -18), strength=120), K(D(15, "20:00"), face(0.74, -18), strength=100),
   K(D(15, "20:40"), face(0.9, -25), strength=80)] + to_buchanan(D(15, "21:00"), face(0.9, -25), 75), ranks=4)
cs("bastion", "Bastion garrison", "The Northeast Bastion: about 500 men, who broke the naval column", "Maj. Gen. W. H. C. Whiting; Col. Lamb", "infantry", 500,
   under_fire(face(0.95, -30), 30, 500, 40) + [K(D(15, "15:00"), face(0.95, -30), h=OUT), K(D(15, "15:25"), face(0.95, -30), state="firing"), K(D(15, "15:50"), face(0.95, -30), strength=440),
   K(D(15, "16:30"), face(0.95, -30), strength=300), K(D(15, "16:45"), face(0.95, -30), state="firing", strength=290), K(D(15, "20:00"), face(0.95, -30), strength=270),
   K(D(15, "20:40"), face(0.98, -60), state="retreat", h=200)] + to_buchanan(D(15, "20:50"), face(0.98, -60), 230), ranks=4)
cs("reilly", "Reilly's party", "Reilly's counterattack along the land face, about 150 men, two-thirds of whom fell", "Maj. James Reilly", "infantry", 150,
   [K(D(15, "16:30"), face(0.62, -30), h=(ALONG + 180) % 360, state="charge"), K(D(15, "16:38"), face(0.47, -22), state="firing", strength=70), K(D(15, "16:44"), face(0.47, -22), state="retreat", h=ALONG, strength=50),
    K(D(15, "16:52"), face(0.9, -40), state="line", h=OUT), K(D(15, "16:55"), face(0.9, -40), state="hidden")], ranks=4)
cs("seaface", "Sea-face guns", "The sea-face batteries and the Pulpit: 22 guns, 36th and 40th North Carolina", "", "infantry", 200,
   under_fire(sea(450, 30), heading(BASTION, (1800, 300)), 200, 40) + [K(D(15, "15:25"), sea(450, 30), state="line")] + to_buchanan(D(15, "21:00"), sea(450, 30), 155), ranks=4)
cs("mound", "Mound guns", "The Mound Battery: two heavy guns on a mound 43 or 60 feet high, by one account or the other", "", "artillery", 40,
   under_fire(MOUND, 110, 40, 10, fire=0.5) + [K(D(15, "15:25"), MOUND, state="line")] + to_buchanan(D(15, "21:00"), MOUND, 30), guns=2)
cs("buchanan", "Chapman's sailors", "Battery Buchanan: four guns and a Confederate Navy detachment, which left by boat at nine", "Capt. Robert T. Chapman, CSN", "artillery", 100,
   under_fire(BUCHANAN, 80, 100, 5, fire=0.3) + [K(D(15, "14:30"), BUCHANAN, state="line"), K(D(15, "21:00"), BUCHANAN, state="column"), K(D(15, "21:10"), WHARF), K(D(15, "21:12"), WHARF, state="hidden")], guns=4)
cs("sc21", "21st S.C.", "21st South Carolina (Hagood's brigade), landed at Buchanan before dawn on the 15th", "", "infantry", 100,
   go(D(15, "05:00"), D(15, "06:40"), PLAIN[::-1] + [HQ], OUT) + [K(D(15, "15:25"), HQ, state="line"), K(D(15, "15:40"), HQ, state="column"), K(D(15, "15:50"), face(0.4, -60), h=OUT, state="firing"),
   K(D(15, "16:00"), face(0.3, -40), state="charge"), K(D(15, "16:10"), face(0.42, -50), state="firing", strength=75), K(D(15, "16:45"), face(0.55, -50), strength=65), K(D(15, "20:00"), face(0.68, -50), strength=60),
   K(D(15, "20:40"), face(0.9, -70), strength=55)] + to_buchanan(D(15, "21:00"), face(0.9, -70), 50), ranks=4)
cs("sc11", "11th and 25th S.C.", "11th and 25th South Carolina (Hagood's brigade): 250 who reached the fort from Buchanan at half past two, under the fleet's fire", "", "infantry", 250,
   go(D(15, "13:15"), D(15, "14:30"), PLAIN[::-1] + [face(0.6, -80)], OUT) + [K(D(15, "14:31"), face(0.6, -80), strength=235), K(D(15, "15:35"), face(0.6, -80), state="firing"),
   K(D(15, "16:00"), face(0.5, -60), state="charge"), K(D(15, "16:10"), face(0.62, -70), state="firing", strength=200), K(D(15, "16:45"), face(0.72, -70), strength=175), K(D(15, "20:00"), face(0.8, -70), strength=160),
   K(D(15, "20:40"), face(0.95, -90), strength=145)] + to_buchanan(D(15, "21:00"), face(0.95, -90), 140), ranks=4)

# ---- the naval column: 1,600 sailors and 400 marines on the beach north of the bastion ----
# Landed about midday, worked forward in trenches, and charged the bastion in one mass at 3:25; stopped about 500 yards
# out by some accounts, and routed up the beach. Losses are the Navy's return, split by division.
NAVY = [("cushman", "Cushman's sailors", "1st Division of the naval landing party", "Lt. Cdr. Charles H. Cushman", 530, 0, 150, 110),
        ("parker", "Parker's sailors", "2nd Division of the naval landing party", "Lt. Cdr. James Parker", 530, 1, 260, 100),
        ("selfridge", "Selfridge's sailors", "3rd Division of the naval landing party", "Lt. Cdr. Thomas O. Selfridge Jr.", 530, 2, 380, 90),
        ("marines", "Dawson's marines", "4th Division, the marines, to cover the column with rifle fire", "Capt. Lucien L. Dawson, USMC", 400, 3, 320, 61)]
def on_beach(d): return (BEACH[-1][0] + 140 + d * 0.22, BASTION[1] + 150 + d * 0.97)  # d metres up the beach from the bastion, on the sand by the surf
for id, short, name, cmd, s, n, stop, lost in NAVY:
    land = (1150 + 60 * (n % 2), 1600 - 90 * n)
    us(id, short, name, cmd, "infantry", s, [K(D(15, "11:40"), (1990, land[1] + 120), h=270, state="column"), K(plus(D(15, "12:00"), 5 * n), land, h=200, state="line")]
       + go(plus(D(15, "12:20"), 5 * n), plus(D(15, "14:30"), 5 * n), [land, on_beach(1000 + 120 * n), on_beach(620 + 110 * n)], heading(on_beach(600), BASTION))
       + [K(D(15, "15:25"), on_beach(620 + 110 * n), state="charge"), K(plus(D(15, "15:33"), n), on_beach(stop), state="firing"), K(plus(D(15, "15:40"), n), on_beach(stop), state="rout", h=20, strength=s - lost // 2),
          K(plus(D(15, "15:58"), 2 * n), on_beach(900 + 120 * n), strength=s - lost), K(plus(D(15, "16:10"), 2 * n), on_beach(1050 + 120 * n), h=200, state="line"), K(END, on_beach(1050 + 120 * n))], ranks=6)

# ---- hold in place through long gaps, so the time-lapse engages over the bombardment days ----
# A turn in place takes its last two minutes; a move of more than three hours takes its last fifteen.
def add_holds(ks):
    out = []
    for a, c in zip(ks, ks[1:] + [None]):
        out.append(a)
        if c is None or a.get("state") == "hidden": continue
        moved = (a["x"], a["y"]) != (c["x"], c["y"]); turned = "h" in c and c["h"] != next((k["h"] for k in reversed(out) if "h" in k), c["h"])
        gap = sec(c["t"]) - sec(a["t"])
        if (moved and gap > 3 * 3600) or (turned and not moved and gap > 600): out.append(dict(t=plus(c["t"], -15 if moved else -2), x=a["x"], y=a["y"]))
    return out
for u in units:
    u["keys"] = add_holds(u["keys"])
    bad = [(a["t"], b["t"]) for a, b in zip(u["keys"], u["keys"][1:]) if sec(b["t"]) <= sec(a["t"])]
    assert not bad, (u["id"], bad)

# ---- ground ----
features = [
    dict(type="works", name="the land face", pts=[(370, 372), SHEP] + [face(i / 16) for i in range(1, 16)] + [BASTION], at=list(face(0.45, 75)), rot=-42),
    dict(type="works", name="the sea face", pts=SEA, at=[sea(600)[0] - 150, sea(600)[1]], rot=59),
    dict(type="redoubt", name="Shepherd's Battery", poly=rect(SHEP, IN, 44, 34, -10), at=[SHEP[0] - 175, SHEP[1] - 20]),
    *[dict(type="redoubt", poly=rect(face(i / 16), IN, 9, 24, -4)) for i in range(1, 16)],   # the fifteen traverses
    dict(type="redoubt", name="Northeast Bastion", poly=rect(BASTION, IN, 60, 50, -22), at=[BASTION[0] + 150, BASTION[1] - 30]),
    dict(type="redoubt", name="the sally-port redoubt", poly=rect(face(0.5, 14), OUT, 20, 16), at=[face(0.5, 150)[0] + 60, face(0.5, 150)[1]]),
    dict(type="redoubt", name="the Pulpit", poly=ellipse(PULPIT, 22, 18), at=[PULPIT[0] - 110, PULPIT[1] - 20]),
    *[dict(type="battery", poly=rect(sea(d), heading(sea(d), (1800, 300)) + 180, 26, 14)) for d in (330, 480, 630, 780)],   # the sea-face batteries on the curtain
    dict(type="redoubt", name="Mound Battery", poly=ellipse(MOUND, 32, 30), at=[MOUND[0] - 130, MOUND[1] - 60]),
    dict(type="redoubt", name="Battery Buchanan", poly=ellipse(BUCHANAN, 60, 38), at=[BUCHANAN[0] - 40, BUCHANAN[1] - 95]),
    dict(type="fence", name="palisade", pts=[(355, 385)] + [face(f, 15) for f in (0, 0.25, 0.5, 0.75, 1.0)] + [(740, 20)], at=list(face(0.88, 55)), rot=-42),
    dict(type="trench", name="Curtis's rifle pits", pts=PITS, at=[PITS[1][0] + 60, PITS[1][1] + 70], **{"from": D(14, "20:00")}),
    dict(type="road", name="the River Road", pts=RIVER_RD, at=[520, 1150], rot=-80),
    dict(type="road", pts=[GATE, (440, 230), HQ]), dict(type="road", pts=[HQ, sea(140, 60)] + PLAIN),
    dict(type="creek", name="the slough", pts=[(300, 520), (350, 440), (380, 400), (395, 370)]),
    dict(type="water", name="New Inlet", poly=[(-1995, -1150), (-1250, -1180), (-700, -1280), (-200, -1420), (250, -1560), (320, -1995), (-1995, -1995)], at=[-1200, -1600]),
    *ship_features,
    dict(name="headquarters", at=[HQ[0] - 10, HQ[1] - 40]), dict(name="River Road gate", at=[GATE[0] - 115, GATE[1] + 75]),
    dict(name="Battery Holland, Terry's post", at=[HOLLAND[0] + 40, HOLLAND[1] + 50]), dict(name="the beach", at=[1080, 1300], rot=-78),
    dict(name="Buchanan's wharf", at=[WHARF[0] + 30, WHARF[1] + 75]), dict(name="Federal Point", at=[-700, -700]),
    dict(name="Cape Fear River", at=[-900, 800], rot=-62), dict(name="the Atlantic", at=[1500, -1300], rot=-70),
    dict(name="to Myrtle Sound and the landing, four miles", at=[700, 1930]), dict(name="Terry's line, two miles north; Hoke at Sugar Loaf beyond it", at=[760, 1880]),
]

# Woods on the ocean side of the peninsula north of the fort; open sand near the fort and along the beach.
CLEAR = [(-2000, 560), (150, 560), (330, 620), (520, 690), (700, 740), (820, 820), (880, 980), (930, 1200), (960, 1450), (1010, 1700), (1050, 2000), (2000, 2000), (2000, -2000), (-2000, -2000)]

# ---- chapters: (time, title, text, camera centre, metres across, playback speed, clock time the sources record or None) ----
CHAPTERS = [
    (D(13, "07:00"), "Fort Fisher", "An L of sand at the tip of Federal Point, guarding New Inlet and the blockade-runners' road to Wilmington. The land face runs a third of a mile from the river to the Northeast Bastion: a parapet 25 feet thick with twenty-odd guns in barbette among fifteen traverses, each a bombproof, a palisade in front and torpedo wires beyond it. The sea face runs nearly a mile down the beach to the Mound Battery; a mile of sand plain separates that from Battery Buchanan at the point. Colonel William Lamb built it and commands it.", [430, -250], 2600, 300, None),
    (D(13, "07:10"), "Christmas 1864", "Three weeks earlier Butler and Porter tried it. A powder ship was blown up off the fort at 1:40 on the morning of 24 December without effect; 64 warships fired some 10,000 rounds that day and as many on Christmas Day. Curtis landed three miles north with 500 men, and 250 of the 142nd New York came within 75 yards of Shepherd's Battery, where Lieutenant Walling took a flag. Butler called it off at dark, and Curtis and 600 men were left on the beach until the 27th.", [430, 250], 2400, 300, None),
    (D(13, "07:20"), "The fleet returns", "At twenty past seven on 13 January the gunboats open on the peninsula four miles north, and the second bombardment begins. Porter has 58 warships and 627 guns; five ironclads close in on the land face, the wooden lines beyond them. Terry's provisional corps, 9,632 men on the returns, is in the transports.", [1200, 300], 3000, 300, "7:20 AM"),
    (D(13, "08:00"), "The landing", "At eight the landing begins near Myrtle Sound, beyond the north edge of this sheet, and is not opposed; Hoke's division, about 6,400 at Sugar Loaf, does not attack. The fleet fires all day. Inside the fort Lamb has about 850 men, and 700 more come in during the day.", [700, 1500], 2600, 120, "8:00 AM"),
    (D(13, "17:00"), "South toward the fort", "At five Terry moves south with Paine's two brigades of U.S. Colored Troops and two of Ames's. Between two and eight next morning a line is dug across the peninsula from Battery Anderson to the river, two miles north of the fort, and Paine holds it facing Hoke. By Terry's count 4,700 stay on that line and 3,300 are for the fort.", [700, 1500], 2600, 120, "5 PM"),
    (D(14, "16:00"), "Battery Holland", "Late on the 14th Terry and Comstock go forward to Battery Holland, 500 yards north of the fort, and Porter agrees to the plan: the army on the western salient, a column of sailors and marines on the bastion. By nightfall most of the land-face guns are in ruins.", [800, 500], 1800, 120, None),
    (D(15, "05:00"), "Hagood's men", "Before dawn on the 15th the 21st South Carolina lands at Battery Buchanan from the river. Of about 1,000 of Hagood's brigade sent, 350 reach the fort; the 11th and 25th come across the sand plain at half past two under the fleet's fire. With them the garrison is about 1,900.", [-600, -700], 3000, 120, None),
    (D(15, "08:00"), "The last bombardment", "From eight the fleet fires on the land face alone; by noon all but two 8-inch columbiads there are silenced. Terry is at Battery Holland by midday. The naval column lands on the beach north of the fort and works forward in trenches.", [900, 500], 2000, 120, "8 AM"),
    (D(15, "14:00"), "Three hundred yards", "By two the sharpshooters of the 13th Indiana are within 175 yards of the western salient and Curtis's brigade is deployed 300 yards north of the fort, Pennypacker and Bell behind it. Lamb puts 250 men at the western salient, 500 along the Northeast Bastion, and Hagood's 350 in a commissary bombproof.", [620, 350], 1300, 60, "2 PM"),
    (D(15, "15:00"), "The signal", "At three precisely, by Towle, Terry signals the Navy to shift its fire from the land face; the Malvern's whistle sounds at 3:25, and Terry's dispatch puts the lodgment at 3:30. The sources give three, 3:25 and 3:30 for the start.", [700, 250], 1200, 30, "3 PM"),
    (D(15, "15:25"), "The naval column", "Two thousand sailors and marines charge the Northeast Bastion up the beach in one mass. The 500 there shoot it to a halt, about 500 yards out by some accounts, and it breaks and runs back along the beach. The Navy loses 393 men here.", [800, 300], 1100, 30, "3:25 PM"),
    (D(15, "15:30"), "The western salient", "About a hundred axemen cut the palisade and Curtis's brigade goes over the parapet at Shepherd's Battery; the 117th New York's colours go up on it. The fight for the traverses begins.", [470, 330], 800, 30, "3:30 PM"),
    (D(15, "15:35"), "The river gate", "Pennypacker's brigade overlaps Curtis's right. The 203rd Pennsylvania breaks the sandbagged river gate, the palisade is cleared to the river and some 400 prisoners are taken. About 3:45 Pennypacker is shot down planting the 97th Pennsylvania's colours on the third traverse, the fifth by Towle's count.", [440, 330], 800, 30, "3:35 PM"),
    (D(15, "15:50"), "Bell", "Bell's brigade comes over the causeway at the gate; Bell is shot crossing it. At four Whiting leads a counterattack and falls wounded at the third traverse; the Federals take the fourth. More than 4,000 Union troops are now in the western salient.", [470, 300], 800, 30, "3:50 PM"),
    (D(15, "16:30"), "Traverse by traverse", "The ironclads shell the land face ahead of the Federals, and the garrison falls back toward the bastion. At half past four Lamb is wounded and carried to the Pulpit bombproof. Reilly leads about 150 men back along the face; two-thirds fall, and the rest go to the bastion. By a quarter to five seven traverses are held.", [560, 200], 800, 30, "4:30 PM"),
    (D(15, "17:12"), "Sunset", "The sun sets at twelve past five and the fight goes on among the traverses in the dark. Curtis is wounded at half past five.", [580, 180], 900, 60, "sunset"),
    (D(15, "18:00"), "Abbott", "At six Abbott's brigade, 1,494 men, comes through the river gate from Terry's line and forms inside the fort.", [460, 230], 1000, 60, "6 PM"),
    (D(15, "19:30"), "The last traverses", "In the evening Ames turns the flank of the remaining traverses, and the last of them falls within a few minutes; nine traverses are taken in all, and the garrison abandons the bastion for the sea face and the sand plain.", [600, 100], 1000, 60, None),
    (D(15, "21:00"), "Battery Buchanan", "At nine Reilly carries Lamb and Whiting to Battery Buchanan, where Chapman's sailors have left by boat. At half past nine the 27th U.S. Colored Troops comes down the sea face after them; Colquitt, sent by Bragg to take command, rows away as it passes the wharf.", [-700, -750], 2800, 120, "9 PM"),
    (D(15, "22:00"), "Surrender", "About ten o'clock the garrison surrenders at Buchanan and Whiting gives up the fort to Terry: 112 officers and 1,971 men, by Terry's count. The army's official loss is 664, the Navy's 393; the Confederates lost about 500 killed and wounded and the rest captured. Next morning the main magazine blows up and kills or wounds about 200 more. Wilmington's last port is shut.", [-900, -850], 2200, 120, "about 10 PM"),
]
events = [dict(t=t, title=a, text=b, at=at, view=v, speed=s, **({"when": w} if w else {})) for t, a, b, at, v, s, w in CHAPTERS]
battle = dict(
    id="fort-fisher", name="Fort Fisher", date="1865-01-13", dateText="13 to 15 January 1865", place="Federal Point, below Wilmington, North Carolina",
    origin=dict(lat=LAT0, lon=LON0), extent=4000, start=D(13, "07:00"), end=END, sunrise="07:05", sunset="17:12", speed=60, lapse=7200, menPerDot=10,
    water=0.05, terrainExaggeration=2, contourInterval=1, trees=dict(density=0.0005, clear=[CLEAR]),
    wind=dict(x=-0.4, y=0.3), view=dict(x=500, y=300, width=3400),
    # Bachelder's convention, Union blue and Confederate red
    sides=dict(union=dict(name="Union (Terry, Porter)", color="#2c4f96", light="#6f8fca", dark="#16294f"),
               confederate=dict(name="Confederate (Lamb, Whiting)", color="#b23a2e", light="#d77a6c", dark="#5c1a14")),
    features=features, units=units, events=events,
    outcome={"result": "Union victory: the fort and its garrison taken", "losses": [
        ["union", "Army, official: 664 (111 killed, 540 wounded, 13 missing), by brigade Curtis 228, Pennypacker 280, Bell 115, Abbott 31. The January table gives 1,059. Navy: 393 (88 killed, 271 wounded, 34 missing). Another 104 soldiers at least in the magazine explosion of the 16th."],
        ["confederate", "About 500 killed and wounded and about 1,400 captured, 1,900 in all; Terry counted 112 officers and 1,971 men taken. Whiting mortally wounded, Lamb wounded."]],
        "note": "The fleet fired 19,682 projectiles in January, 1,652,638 pounds of iron; both attacks together nearly 40,000. The sources give three, 3:25 and 3:30 for the hour of the assault."},
    sources=[
        "Cyrus B. Comstock, <i>Plan and sections of Fort Fisher, carried by assault by the U.S. forces, Maj. Gen. A.H. Terry commanding, Jan. 15th, 1865</i> (Engineer Bureau, 1:3,840; Library of Congress 86690228), and Comstock and Schultze, <i>Sketch of vicinity of Fort Fisher</i> (1:12,000; LC 86690227): the traverses, the gate, the palisade, the rifle pits, the sea face and the road down the peninsula. The two sheets disagree by about 300 m on the Mound.",
        "<i>Fort Fisher</i>, National Register of Historic Places nomination, Polly M. Rettig, NPS Landmark Review Project, 1975 (from Frank B. Sarles Jr., 1961): the fort as built, its guns, the palisade and torpedoes, the December attack, and what the sea has taken since.",
        "North Carolina Historic Sites, Fort Fisher: \"1st Attack\", \"2nd Attack\" and \"Casualties and Other Numbers\", the clock of 13 to 16 January from Mark A. Moore, <i>The Wilmington Campaign and the Battles for Fort Fisher</i> (1999), with the strengths and losses from the Official Records, the naval records and <i>Battles and Leaders</i>.",
        "Terry's and Ames's reports of 16 January 1865 (OR Series I, vol. 46, part 1) and Lt. Col. George F. Towle's narrative of 31 December 1865, as reprinted in Senate Report 1578, 56th Congress (1900), on Galusha Pennypacker: the hour of the signal, the lodgment, the gate and the colours on the traverses.",
        "The orders of battle from OR I/46/1 pp. 403-405 and ORN I/11 (Porter, Breese); William Lamb, \"The Defense of Fort Fisher\", <i>Battles and Leaders</i> vol. IV; Rod Gragg, <i>Confederate Goliath</i> (1991); Chris Fonvielle, <i>The Wilmington Campaign</i> (1997). The last three not consulted directly.",
        "<i>Fort Fisher, captured by the Federals, Jan. 15, 1865</i>, manuscript map from Rear Adm. David D. Porter's papers (LC 99446439): the fleet's lines of battle and the fort's range arcs.",
        "Places: the U.S. Coast and Geodetic Survey's points for Shepherd's Battery, the Northeast Bastion and Battery Buchanan; the headquarters site under the UDC column and the modern shore from OpenStreetMap contributors (ODbL). Terrain: USGS 3DEP elevation at 10 m over a 4 km square, with the strip the sea has taken since 1865 (the bastion, 2,100 ft of the sea face and the beach north of it) raised to beach height, and New Inlet, closed in 1881, drawn as water.",
        "What is reconstructed: the Mound Battery's place, between Comstock's two sheets; the sea face's line and its batteries; the regimental strengths, split evenly from the brigade and division aggregates; where each regiment stood as the traverses fell; the naval column's landing place and approach; the stations of the ships on the 15th, from Porter's plan of lines rather than the day's positions; and the ships drawn as batteries on the water. Terry's line and the landing beach are beyond the north edge, so the Union columns come on there.",
    ],
)
json.dump(battle, open(HERE + "battle.json", "w"), indent=1)
print(len(units), "units,", len(events), "events,", len(features), "features")
