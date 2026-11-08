# Builds battles/bastogne/battle.json. Run from the repo root: python3 battles/bastogne/make.py
# Local metres from 49.9900N 5.7370E (x east, y north). The 24 km square holds Bastogne (-1562,1197), Noville and Vaux to
# the north, Bourcy, Longvilly and Allerborn to the north-east and east, Wardin, Bras and Marvie to the south-east, the
# 4th Armored Division's last 12 km from Burnon (-5423,-11085) through Chaumont and Assenois, and Sibret, Senonchamps,
# Mande-Saint-Étienne, Flamierge and Champs to the west. Anchors are the research note's OpenStreetMap points; every place
# the note gives at 200 m or worse is labelled "about here". The note gives no road geometry, so each road is drawn
# straight between the places it joins. Clock times are GMT+1, the clock every source used.
import json, math, re, datetime as dt
HERE = "battles/bastogne/"
LAT0, LON0 = 49.9900, 5.7370
KX, KY = 111320 * math.cos(math.radians(LAT0)), 111320  # tools/fetch_terrain.py's metres per degree
def M(lat, lon): return (round((lon - LON0) * KX), round((lat - LAT0) * KY))
HALF_EXTENT = 12000
WATER = 250  # below the DEM's lowest cell: no river crosses the plateau

# ---- terrain ----
T = json.load(open(HERE + "terrain.json"))
COLS, SP = T["cols"], T["spacing"]; HALF = COLS * SP / 2
assert HALF == HALF_EXTENT, "terrain.json is not the battle's extent"
def z(x, y):
    c, r = int((x + HALF) / SP), int((HALF - y) / SP)
    return T["z"][r * COLS + c] if 0 <= c < COLS and 0 <= r < COLS else None
def on_map(p, margin=0): return max(map(abs, p)) < HALF_EXTENT - margin
def on_land(p): return on_map(p) and z(*p) is not None and z(*p) > WATER

# ---- places (WGS84), from the note's anchor table ----
PLACES = {  # OpenStreetMap
    'bastogne': (50.00075, 5.71518), 'seminary': (50.00670, 5.72131), 'town': (50.00231, 5.71734), 'barracks': (50.00812, 5.71957),
    'mardasson': (50.00928, 5.73816), 'noville': (50.06433, 5.76199), 'vaux': (50.07536, 5.75283), 'bourcy': (50.05870, 5.80845),
    'cobru': (50.06139, 5.75061), 'foy': (50.04447, 5.75057), 'recogne': (50.05190, 5.73682), 'luzery': (50.01697, 5.72958),
    'longchamps': (50.05354, 5.68925), 'monaville': (50.05579, 5.70256), 'bois_jacques': (50.03192, 5.76121), 'bizory': (50.01957, 5.76432),
    'mageret': (50.01436, 5.78503), 'neffe': (50.00543, 5.76232), 'neffe_stn': (50.00560, 5.76200), 'mont': (50.00283, 5.74393),
    'marvie': (49.98450, 5.74402), 'martaimont': (49.96583, 5.75835), 'wardin': (49.99019, 5.78573), 'bras': (49.98380, 5.82038),
    'benonchamps': (50.00443, 5.80868), 'niederwampach': (50.00989, 5.84088), 'oberwampach': (50.01475, 5.86000), 'arloncourt': (50.02763, 5.80451),
    'oubourcy': (50.03788, 5.79918), 'longvilly': (50.02495, 5.83682), 'chifontaine': (50.03134, 5.85744), 'allerborn': (50.03564, 5.87015),
    'mande': (50.01955, 5.63890), 'flamierge': (50.03378, 5.60447), 'champs': (50.03895, 5.66949), 'rolley': (50.03784, 5.68249),
    'hemroulle': (50.02396, 5.68561), 'savy': (50.01934, 5.70548), 'rouette': (50.05155, 5.65417), 'givry': (50.05640, 5.64216),
    'senonchamps': (50.00009, 5.65674), 'isle_hesse': (50.00373, 5.67701), 'isle_pre': (49.98877, 5.69219), 'villeroux': (49.97866, 5.65476),
    'chenogne': (49.99103, 5.61958), 'sibret': (49.96827, 5.63525), 'morhet': (49.96215, 5.58421), 'remoifosse': (49.96610, 5.71676),
    'assenois': (49.96651, 5.68158), 'clochimont': (49.95192, 5.66705), 'hompre': (49.94378, 5.68667), 'lutrebois': (49.95895, 5.73418),
    'villers': (49.93456, 5.74778), 'remichampagne': (49.93484, 5.64088), 'cobreville': (49.91232, 5.61185), 'chaumont': (49.91998, 5.67117),
    'burnon': (49.89042, 5.66123),
    # derived in the note from Marshall's text: the château ±150 m, Hill 510 ±250 m, Hill 500 ±300 m, the Halt station ±300 m,
    # Flamizoulle ±300 m, O'Hara's roadblock ±200 m
    'chateau': (50.00300, 5.76200), 'hill510': (50.01800, 5.77300), 'hill500': (49.97700, 5.74500), 'halt': (50.03000, 5.76100),
    'flamizoulle': (50.03000, 5.63000), 'ohara': (49.98500, 5.76100),
}
P = {k: M(*v) for k, v in PLACES.items()}
def off(p, dx, dy): return (p[0] + dx, p[1] + dy)
# Edges where units come on and go off, on the roads the note names [DERIVED]
EDGE_S = (-900, -11900)        # the Arlon road (N4), toward Martelange
EDGE_W = (-11900, 5500)        # the Marche road (N4 north-west), toward Champlon
EDGE_NW = (-4700, 11900)       # the Bertogne road
EDGE_N = (2500, 11900)         # the Houffalize road (N30)
EDGE_E = (11900, 5600)         # the Clervaux road, past Allerborn
EDGE_ESE = (11900, 2900)       # the Wiltz valley road past Oberwampach
EDGE_SE = (11900, -1500)       # the Wiltz road (N84) past Bras
EDGE_SW = (-11900, -5200)      # the Neufchâteau road (N85)
EDGE_SSW = (-8200, -11900)     # toward Bigonville and Vaux-lez-Rosières, CCR's road in
# The supply drop zone: "the mile-square drop zone" in the 2d Bn 327th's area [M p137], not placed in the note. Drawn
# behind 2/327's line from Marvie to the Arlon road, about here [DERIVED].
DZ_C = (-700, -700)

# ---- roads and railways ----
def rd(pts, name="", at=None, rot=0, **kw): return dict(type="road", name=name, pts=[list(p) for p in pts], **({"at": list(at), "rot": rot} if at else {}), **kw)
B = P['bastogne']
R_NORTH = [B, P['luzery'], P['foy'], P['noville'], EDGE_N]                                   # N30 to Houffalize
R_BOURCY = [B, off(P['halt'], -150, -100), P['bourcy']]                                       # north-east to Bourcy
R_NOV_BOURCY = [P['noville'], P['bourcy']]
R_NOV_VAUX = [P['noville'], P['vaux']]
R_FOY_RECOGNE = [P['foy'], P['recogne'], P['longchamps']]
R_FOY_BIZORY = [P['foy'], P['halt'], P['bizory']]
R_EAST = [B, P['mont'], P['neffe'], P['mageret'], P['longvilly'], P['chifontaine'], P['allerborn'], EDGE_E]  # N874 to Clervaux
R_BIZORY = [B, off(P['mardasson'], 0, 150), P['bizory'], P['hill510'], P['mageret']]
R_BENON = [P['mageret'], P['benonchamps'], P['niederwampach'], P['oberwampach'], EDGE_ESE]  # Bayerlein's night road, from the east
R_BENON_LONGVILLY = [P['benonchamps'], P['longvilly']]
R_WILTZ = [B, P['marvie'], P['ohara'], P['bras'], EDGE_SE]                                     # N84 to Wiltz
R_NEFFE_WARDIN = [P['neffe'], P['wardin'], P['bras']]
R_ARLON = [B, P['remoifosse'], EDGE_S]                                                         # N4 to Arlon
R_NEUF = [B, P['isle_pre'], P['sibret'], EDGE_SW]                                              # N85 to Neufchâteau
R_MARCHE = [B, P['isle_hesse'], P['mande'], P['flamizoulle'], P['flamierge'], EDGE_W]          # N4 to Marche
R_BERTOGNE = [B, P['savy'], P['monaville'], P['longchamps'], EDGE_NW]
R_CHAMPS = [P['longchamps'], P['rolley'], P['champs'], P['flamizoulle']]
R_HEMROULLE = [P['rolley'], P['hemroulle'], P['savy']]
R_SENON = [P['isle_hesse'], P['senonchamps'], P['villeroux'], P['sibret']]
R_ASSENOIS = [B, P['assenois'], P['clochimont'], P['remichampagne'], P['cobreville'], EDGE_SSW]  # CCR's road north
R_CHAUMONT = [(-5000, -11900), P['burnon'], P['chaumont'], P['hompre'], P['assenois']]                  # CCB's road north
R_SOUTH = [P['marvie'], P['lutrebois'], P['villers']]
RAIL_GOUVY = [off(B, 200, 300), P['halt'], off(P['bourcy'], 200, 200), (11900, 9800)]          # Bastogne-Gouvy, through the Bois Jacques
RAIL_WILTZ = [off(B, 300, -100), P['neffe_stn'], off(P['benonchamps'], 0, 200), (11900, 2000)]  # Bastogne-Wiltz, razed today
RAIL_LIBRAMONT = [off(B, -300, -200), (-6000, -4800), (-11900, -8600)]                         # the south-west arm toward Libramont
BROOK = [(-400, 1800), (500, 1700), (1300, 1750), (2000, 1800), (2600, 1600), (3100, 1000), (3400, 300), (3600, -100)]  # the DEM's valley floor

# ---- woods, villages and fields ----
def quad(c, w, h, rot=0):
    r = math.radians(rot); u, v = (math.cos(r), math.sin(r)), (-math.sin(r), math.cos(r))
    return [(round(c[0] + a * w * u[0] + b * h * v[0]), round(c[1] + a * w * u[1] + b * h * v[1])) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
VILLAGES = ['noville', 'foy', 'recogne', 'bourcy', 'vaux', 'cobru', 'longchamps', 'monaville', 'champs', 'hemroulle', 'savy', 'mande', 'flamierge',
            'senonchamps', 'villeroux', 'sibret', 'chenogne', 'isle_pre', 'isle_hesse', 'assenois', 'clochimont', 'hompre', 'remichampagne', 'chaumont',
            'burnon', 'remoifosse', 'lutrebois', 'villers', 'marvie', 'wardin', 'bras', 'mont', 'neffe', 'bizory', 'mageret', 'benonchamps',
            'niederwampach', 'oberwampach', 'arloncourt', 'oubourcy', 'longvilly', 'chifontaine', 'allerborn', 'luzery', 'rouette', 'givry', 'cobreville']
CLEAR = [quad(P['bastogne'], 900, 800)] + [quad(P[k], 260, 220) for k in VILLAGES]
FIELDS = [quad((1100, 1550), 700, 220, 5),     # the pasture between Mont and Neffe, crossed by wire fences [M p78]
          quad(off(P['noville'], 0, 0), 900, 700), quad(off(P['marvie'], 0, -300), 700, 500), quad(off(P['champs'], 300, -500), 900, 600),
          quad(off(P['hemroulle'], -900, 0), 800, 700), quad(DZ_C, 900, 700), quad(off(P['assenois'], 400, 600), 700, 500)]

# ---- the clock: 18 to 26 December 1944, GMT+1 ----
UTC = dt.timezone.utc
T0 = dt.datetime(1944, 12, 18, tzinfo=UTC)
def D(day, hm): return f"1944-12-{day:02d} {hm}"
def sec(t): return (dt.datetime.strptime(t, "%Y-%m-%d %H:%M:%S" if t.count(":") == 2 else "%Y-%m-%d %H:%M").replace(tzinfo=UTC) - T0).total_seconds()
def fmt(s): s = round(s); return (T0 + dt.timedelta(seconds=s)).strftime("%Y-%m-%d %H:%M" + (":%S" if s % 60 else ""))
def plus(t, mins): return fmt(sec(t) + mins * 60)
START, END = D(18, "15:30"), D(26, "20:30")

# ---- features ----
def label(name, p, dy=0, dx=0, **kw): return dict(name=name, at=[p[0] + dx, p[1] + dy], **kw)
features = [
    rd(R_NORTH, "Houffalize road", (1650, 7000), 70), rd(R_BOURCY, "Bourcy road", (3700, 6100), 45), rd(R_NOV_BOURCY), rd(R_NOV_VAUX), rd(R_FOY_RECOGNE), rd(R_FOY_BIZORY),
    rd(R_EAST, "Longvilly road", (5300, 3550), -12), rd(R_BIZORY), rd(R_BENON), rd(R_BENON_LONGVILLY), rd(R_WILTZ, "Wiltz road", (4200, -870), 3),
    rd(R_NEFFE_WARDIN), rd(R_ARLON, "Arlon road", (-1050, -6500), 87), rd(R_NEUF, "Neufchâteau road", (-9500, -3700), 30),
    rd(R_MARCHE, "Marche road", (-10700, 5400), 0), rd(R_BERTOGNE, "Bertogne road", (-4100, 9600), 75), rd(R_CHAMPS), rd(R_HEMROULLE), rd(R_SENON),
    rd(R_ASSENOIS, "Assenois road", (-7900, -7300), 50), rd(R_CHAUMONT, "Chaumont road", (-5000, -9600), 80), rd(R_SOUTH),
    rd(RAIL_GOUVY, "railway to Gouvy", (7500, 9000), 20), rd(RAIL_WILTZ, "railway to Wiltz", (8500, 2350), 5), rd(RAIL_LIBRAMONT, "railway to Libramont", (-9300, -7200), 35),
    dict(type="creek", name="the brook (about here)", pts=[list(p) for p in BROOK]),
    dict(type="fence", pts=[[700, 1450], [1500, 1520]]),
    dict(type="fence", pts=[[700, 1600], [1500, 1660]]), dict(type="fence", pts=[[1000, 1380], [1000, 1700]]),
    label("BASTOGNE", P['town'], dy=-50), label("Heintz Barracks", P['barracks'], dx=-600, dy=150), label("the seminary", P['seminary'], dx=500, dy=60),
    label("CCB's CP, the Hôtel Lebrun (about here)", P['bastogne'], dy=-450),
    label("Mardasson", P['mardasson'], dy=160), label("Neffe château (about here)", P['chateau'], dx=300, dy=-350),
    label("Hill 510 (about here)", P['hill510'], dy=-200), label("Hill 500 (about here)", P['hill500'], dy=-170), label("Martaimont", P['martaimont'], dy=-200),
    label("Halt station (about here)", P['halt'], dx=550, dy=-60), label("Bois Jacques", P['bois_jacques'], dx=200, dy=350),
    label("Château de Rolley", P['rolley'], dy=170),
    label("Noville", P['noville'], dy=260), label("Vaux", P['vaux'], dy=200), label("Bourcy", P['bourcy'], dy=220), label("Cobru", P['cobru'], dx=-250, dy=120),
    label("Foy", P['foy'], dx=-220), label("Recogne", P['recogne'], dx=-320), label("Luzery", P['luzery'], dx=-300),
    label("Longchamps", P['longchamps'], dy=230), label("Monaville", P['monaville'], dy=-200), label("Bizory", P['bizory'], dy=250),
    label("Mageret", P['mageret'], dy=-220), label("Neffe", P['neffe'], dy=220), label("Mont", P['mont'], dy=200),
    label("Marvie", P['marvie'], dx=-320), label("Wardin", P['wardin'], dy=-220), label("Bras", P['bras'], dy=-220),
    label("Benonchamps", P['benonchamps'], dy=-220), label("Niederwampach", P['niederwampach'], dy=-220), label("Oberwampach", P['oberwampach'], dy=220),
    label("Arloncourt", P['arloncourt'], dx=300), label("Oubourcy", P['oubourcy'], dy=200), label("Longvilly", P['longvilly'], dy=-230),
    label("Chifontaine", P['chifontaine'], dy=-220), label("Allerborn", P['allerborn'], dy=220),
    label("Mande-Saint-Étienne", P['mande'], dy=-230), label("Flamierge", P['flamierge'], dy=230), label("Flamizoulle (about here)", P['flamizoulle'], dy=230),
    label("Champs", P['champs'], dy=230), label("Hemroulle", P['hemroulle'], dy=-220), label("Savy", P['savy'], dy=-200),
    label("Rouette", P['rouette'], dy=200), label("Givry", P['givry'], dy=200), label("Senonchamps", P['senonchamps'], dy=230), label("Isle-la-Hesse", P['isle_hesse'], dy=230),
    label("Isle-le-Pré", P['isle_pre'], dy=-200), label("Villeroux", P['villeroux'], dy=-220), label("Chenogne", P['chenogne'], dy=220), label("Sibret", P['sibret'], dy=-230),
    label("Morhet", P['morhet'], dy=-220), label("Remoifosse", P['remoifosse'], dx=420), label("Assenois", P['assenois'], dy=-230),
    label("Clochimont", P['clochimont'], dx=-150, dy=-220), label("Hompré", P['hompre'], dy=-220), label("Lutrebois", P['lutrebois'], dy=-220),
    label("Villers-la-Bonne-Eau", P['villers'], dy=-220), label("Remichampagne", P['remichampagne'], dy=-220), label("Cobreville", P['cobreville'], dy=-220),
    label("Chaumont", P['chaumont'], dy=-230), label("Burnon", P['burnon'], dy=-220),
    label("to Houffalize", EDGE_N, dx=350, dy=-400, rot=70), label("to Clervaux", EDGE_E, dx=-500, dy=250), label("to Wiltz", EDGE_SE, dx=-500, dy=250),
    label("to Arlon", EDGE_S, dx=350, dy=500, rot=85), label("to Neufchâteau", EDGE_SW, dx=900, dy=-100, rot=25), label("to Marche", EDGE_W, dx=700, dy=250),
]
for f in features:
    if "at" in f: assert on_land(f["at"]) and on_map(f["at"], 100), (f.get("name"), f["at"], "a label off the map")
    for p in f.get("pts", []): assert on_map(p, -1), (f.get("name"), p, "a line off the map")

# ---- order of battle: (id, side, short, name, commander, type, strength, extra) ----
# The note gives no battalion strengths in men: the 101st's and CCB's are its TO&E figures ("about"), the German
# battalions its inferred 500 to 700. Armor counts vehicles, from the counts the note gives at each fight. Artillery
# battalions carry the note's guns; their men are drawn as 300 [INF], since the note gives none.
LOOSE = dict(loose=True)
def guns(n): return dict(guns=n)
OOB = [
    # 101st Airborne Division, Brig. Gen. A. C. McAuliffe acting
    ("p501_1", "american", "1/501", "1st Battalion, 501st Parachute Infantry (about 550, TO&E)", "Maj. R. V. Bottomly", "infantry", 550, LOOSE),
    ("p501_2", "american", "2/501", "2d Battalion, 501st Parachute Infantry (about 550, TO&E)", "Maj. S. N. Homan", "infantry", 550, LOOSE),
    ("p501_3", "american", "3/501", "3d Battalion, 501st Parachute Infantry, less Company I (about 400)", "Lt. Col. G. M. Griswold", "infantry", 400, LOOSE),
    ("p501_i", "american", "I/501", "Company I, 501st Parachute Infantry, sent to Wardin (drawn as 150)", "", "infantry", 150, LOOSE),
    ("p506_1", "american", "1/506", "1st Battalion, 506th Parachute Infantry, 'in full strength when it went to Team Desobry's support' (drawn as 600)", "Lt. Col. J. L. LaPrade (killed 19 Dec), then Maj. R. F. Harwick", "infantry", 600, LOOSE),
    ("p506_2", "american", "2/506", "2d Battalion, 506th Parachute Infantry (about 550, TO&E)", "Lt. Col. R. L. Strayer", "infantry", 550, LOOSE),
    ("p506_3", "american", "3/506", "3d Battalion, 506th Parachute Infantry (about 550, TO&E)", "Maj. G. M. Heilman", "infantry", 550, LOOSE),
    ("p502_1", "american", "1/502", "1st Battalion, 502d Parachute Infantry (about 550, TO&E)", "Maj. J. D. Hanlon", "infantry", 550, LOOSE),
    ("p502_2", "american", "2/502", "2d Battalion, 502d Parachute Infantry (about 550, TO&E)", "Lt. Col. T. H. Sutliffe", "infantry", 550, LOOSE),
    ("p502_3", "american", "3/502", "3d Battalion, 502d Parachute Infantry (about 550, TO&E)", "Lt. Col. J. P. Stopka", "infantry", 550, LOOSE),
    ("g327_1", "american", "1/327", "1st Battalion, 327th Glider Infantry (about 700, TO&E)", "Lt. Col. H. F. Salee", "infantry", 700, {}),
    ("g327_2", "american", "2/327", "2d Battalion, 327th Glider Infantry (about 700, TO&E)", "Lt. Col. R. L. Inman (wounded 20 Dec), then Maj. R. B. Galbreaith", "infantry", 700, {}),
    ("g327_3", "american", "3/327", "3d Battalion, 327th Glider Infantry, in fact the 1st Battalion, 401st Glider Infantry (about 700, TO&E)", "Lt. Col. R. C. Allen", "infantry", 700, {}),
    ("eng326", "american", "326 Engrs", "326th Airborne Engineer Battalion (about 400, TO&E)", "Lt. Col. H. A. Mozley", "infantry", 400, LOOSE),
    ("pf327", "american", "Pathfinders", "The pathfinders who jumped into the 2d Bn 327th's area on 23 December to mark the supply drop (their number is not in the note; drawn as 60, a dot of 20 from each of three aircraft)", "", "infantry", 60, LOOSE),
    ("fa321", "american", "321 GFA", "321st Glider Field Artillery Battalion", "Lt. Col. E. L. Carmichael", "artillery", 300, guns(12)),
    ("fa907", "american", "907 GFA", "907th Glider Field Artillery Battalion, 105 mm M3", "Lt. Col. C. F. Nelson", "artillery", 300, guns(12)),
    ("fa377", "american", "377 PFA", "377th Parachute Field Artillery Battalion, 75 mm pack howitzers", "Lt. Col. H. W. Elkins", "artillery", 300, guns(12)),
    ("fa463", "american", "463 PFA", "463d Parachute Field Artillery Battalion, 75 mm pack howitzers", "Lt. Col. J. T. Cooper", "artillery", 300, guns(12)),
    ("aa81", "american", "81 AA", "81st Airborne Antiaircraft Battalion, 57 mm and AA batteries; D and E Batteries put twelve guns in the Marvie gap on 23 December", "Lt. Col. X. B. Cox", "artillery", 300, guns(12)),
    # Combat Command B, 10th Armored Division, Col. W. L. Roberts
    ("desobry_t", "american", "Desobry", "Team Desobry's armor: B Company 3d Tank Battalion, a light tank platoon and a 609th TD platoon, fifteen tanks", "Maj. W. R. Desobry (wounded 19 Dec), then Maj. C. L. Hustead", "armor", 15, {}),
    ("desobry_i", "american", "Desobry", "Team Desobry's infantry: the 20th Armored Infantry Battalion less A and C Companies, engineers and a cavalry platoon (drawn as 400)", "Maj. W. R. Desobry", "infantry", 400, LOOSE),
    ("hyduke", "american", "Hyduke", "Team Cherry's advance guard: four Shermans and seven light tanks of A Company 3d Tank Battalion, a cavalry platoon and tank destroyers", "Lt. E. P. Hyduke", "armor", 11, {}),
    ("ryerson_t", "american", "Ryerson", "Team Cherry's main body, its tanks and two 105 mm assault guns (drawn as eight)", "Capt. W. F. Ryerson", "armor", 8, {}),
    ("ryerson_i", "american", "Ryerson", "Team Cherry's main body: C Company, 20th Armored Infantry Battalion (about 250, TO&E)", "Capt. W. F. Ryerson", "infantry", 250, {}),
    ("cherry_hq", "american", "Cherry HQ", "Team Cherry's headquarters at the Neffe château (drawn as 60)", "Lt. Col. H. T. Cherry", "infantry", 60, LOOSE),
    ("ohara_t", "american", "O'Hara", "Team O'Hara's mediums: C Company, 21st Tank Battalion (about 17, TO&E)", "Lt. Col. J. O'Hara", "armor", 17, {}),
    ("ohara_l", "american", "O'Hara light", "Team O'Hara's light tank platoon, five tanks", "Wishart", "armor", 5, {}),
    ("ohara_i", "american", "O'Hara", "Team O'Hara's infantry: the 54th Armored Infantry Battalion less A and C Companies, and engineers (drawn as 400)", "Lt. Col. J. O'Hara", "infantry", 400, {}),
    ("fa420", "american", "420 AFA", "420th Armored Field Artillery Battalion, eighteen 105 mm howitzers", "Lt. Col. B. D. Browne", "artillery", 300, guns(18)),
    ("pyle_t", "american", "Pyle", "Team Pyle's armor, from 21 December: 14 medium tanks, mostly from the 9th Armored", "", "armor", 14, {}),
    ("pyle_i", "american", "Pyle", "Team Pyle's infantry, 200 men, mostly from the 9th Armored", "", "infantry", 200, {}),
    ("snafu", "american", "SNAFU", "Team SNAFU, the stragglers gathered in Bastogne: about 250 on 19 December, 600 within a week", "Capt. C. Brown (110th Inf)", "infantry", 250, LOOSE),
    # the other units in the perimeter
    ("td705a", "american", "705 TD A", "A Company, 705th Tank Destroyer Battalion, M18s, less the platoon left at Laroche (drawn as eight)", "Lt. Col. C. D. Templeton, battalion", "armor", 8, {}),
    ("td705b", "american", "705 TD B", "B Company, 705th Tank Destroyer Battalion, M18s (drawn as twelve)", "Lt. Col. C. D. Templeton, battalion", "armor", 12, {}),
    ("td705c", "american", "705 TD C", "C Company, 705th Tank Destroyer Battalion, M18s (drawn as twelve)", "Lt. Col. C. D. Templeton, battalion", "armor", 12, {}),
    ("fa755", "american", "755 FA", "755th Field Artillery Battalion, twelve 155 mm howitzers", "", "artillery", 300, guns(12)),
    ("fa969", "american", "969 FA", "969th Field Artillery Battalion, twelve 155 mm howitzers", "", "artillery", 300, guns(12)),
    ("fa109", "american", "109 FA", "109th Field Artillery Battalion (28th Division), which came through as a unit and attached itself to the 907th", "", "artillery", 300, guns(12)),
    ("eng158", "american", "158 Engrs", "158th Engineer Combat Battalion, outposts at Mageret, Neffe, Mont and Foy (drawn as 300)", "", "infantry", 300, LOOSE),
    ("eng35", "american", "35 Engrs", "35th Engineer Combat Battalion, 'tired, understrength' (drawn as 300)", "", "infantry", 300, LOOSE),
    # CCR 9th Armored Division, outside the perimeter
    ("harper_t", "american", "TF Harper", "Task Force Harper, CCR 9th Armored: the 2d Tank Battalion less a company (drawn as 30)", "Lt. Col. R. S. Harper (killed 18 Dec)", "armor", 30, {}),
    ("harper_i", "american", "TF Harper", "Task Force Harper's infantry, two companies of the 52d Armored Infantry Battalion (drawn as 400)", "Lt. Col. R. S. Harper", "infantry", 400, {}),
    # 4th Armored Division, III Corps
    ("b8tk", "american", "8 Tk Bn", "CCB 4th Armored: the 8th Tank Battalion, 22 Shermans in fighting condition on the morning of 23 December", "Brig. Gen. H. E. Dager, CCB", "armor", 22, {}),
    ("b10aib", "american", "10 AIB", "CCB 4th Armored: the 10th Armored Infantry Battalion (about 700, TO&E)", "Lt. Col. H. Cohen", "infantry", 700, {}),
    ("b318", "american", "1/318", "1st Battalion, 318th Infantry (80th Division), under CCB 4th Armored (about 700, TO&E)", "", "infantry", 700, {}),
    ("r37tk", "american", "37 Tk Bn", "CCR 4th Armored: the 37th Tank Battalion, 'no more than twenty Shermans in operation' (drawn as seventeen, with Dwight's three apart)", "Lt. Col. C. W. Abrams Jr.", "armor", 17, {}),
    ("dwight", "american", "Dwight", "Capt. W. A. Dwight's light team of the 37th Tank Battalion, which went through Assenois; Lt. C. P. Boggess drove the first vehicle (drawn as three tanks)", "Capt. W. A. Dwight", "armor", 3, {}),
    ("r53aib", "american", "53 AIB", "CCR 4th Armored: the 53d Armored Infantry Battalion, 'short 230 men' (drawn as 770)", "Lt. Col. G. L. Jaques", "infantry", 770, {}),
    ("r94fa", "american", "CCR guns", "CCR 4th Armored's artillery: the 94th Armored FA Battalion and others, three battalions of 105 mm and a battery of 155 mm (drawn as 40 guns)", "", "artillery", 300, guns(40)),
    # XLVII Panzer Corps, Gen. d. Pz. Tr. H. von Lüttwitz: 2d Panzer Division, Col. M. von Lauchert
    ("pz2_recce", "german", "2 Pz Recce", "2d Panzer Division's Reconnaissance Battalion, half-tracks (drawn as 500)", "Col. M. von Lauchert, division", "infantry", 500, {}),
    ("pz2_t1", "german", "3 Pz Regt", "2d Panzer Division: the tanks of the 3d Panzer Regiment on the ridge short of Vaux, fourteen", "Col. M. von Lauchert, division", "armor", 14, {}),
    ("pz2_t2", "german", "2 Pz tanks", "2d Panzer Division: the rest of the 'more than 30 tanks' seen at Noville (drawn as sixteen)", "Col. M. von Lauchert, division", "armor", 16, {}),
    ("pzg2_1", "german", "2 PGR", "2d Panzergrenadier Regiment, a battalion (drawn as 550)", "", "infantry", 550, {}),
    ("pzg2_2", "german", "2 PGR", "2d Panzergrenadier Regiment, a battalion (drawn as 550)", "", "infantry", 550, {}),
    ("pzg304_1", "german", "304 PGR", "304th Panzergrenadier Regiment, a battalion, about Foy (drawn as 550)", "", "infantry", 550, {}),
    ("pzg304_2", "german", "304 PGR", "304th Panzergrenadier Regiment, a battalion (drawn as 550)", "", "infantry", 550, {}),
    ("pz2_88", "german", "2 Pz 88s", "2d Panzer Division's 88s at the road junction below Chifontaine (drawn as four)", "", "artillery", 80, guns(4)),
    # Panzer Lehr Division, Lt. Gen. F. Bayerlein
    ("kg902_t", "german", "KG 902", "Kampfgruppe 902's Mark V tanks, Bayerlein in a lead tank: fifteen, less the three left at Mageret", "Lt. Gen. F. Bayerlein", "armor", 12, {}),
    ("kg902_b", "german", "KG 902 block", "The three tanks Bayerlein left to block the road east of Mageret", "", "armor", 3, {}),
    ("kg902_i", "german", "902 PGR", "Kampfgruppe 902: a battalion of the 902d Panzergrenadier Regiment, 'four companies' (drawn as 550)", "", "infantry", 550, {}),
    ("pl901_1", "german", "901 PGR", "901st Panzergrenadier Regiment, a battalion (drawn as 550)", "", "infantry", 550, {}),
    ("pl901_2", "german", "901 PGR", "901st Panzergrenadier Regiment, a battalion (drawn as 550)", "", "infantry", 550, {}),
    ("pl_td", "german", "Lehr TDs", "The tank destroyer battalion with the 901st, 'about twenty TDs'", "", "armor", 20, {}),
    ("pl901_tk", "german", "901 tanks", "The 901st's tanks against Marvie, four", "", "armor", 4, {}),
    ("pl_art", "german", "Lehr guns", "Panzer Lehr's artillery battalion with the 901st (drawn as twelve guns)", "", "artillery", 200, guns(12)),
    ("pl_recce", "german", "Recce Lehr 130", "Reconnaissance Lehr Battalion 130 at Wardin (drawn as 500)", "", "infantry", 500, {}),
    ("pl_wardin_t", "german", "Lehr tanks", "The seven Panzer Lehr tanks against Wardin", "", "armor", 7, {}),
    # 26th Volksgrenadier Division, Maj. Gen. H. Kokott
    ("gr77_1", "german", "GR 77", "Grenadier Regiment 77, a battalion (drawn as 650)", "Maj. Gen. H. Kokott, division", "infantry", 650, {}),
    ("gr77_2", "german", "GR 77", "Grenadier Regiment 77, a battalion (drawn as 650)", "Maj. Gen. H. Kokott, division", "infantry", 650, {}),
    ("gr78_1", "german", "GR 78", "Grenadier Regiment 78, a battalion (drawn as 650)", "Maj. Gen. H. Kokott, division", "infantry", 650, {}),
    ("gr78_2", "german", "GR 78", "Grenadier Regiment 78, a battalion (drawn as 650)", "Maj. Gen. H. Kokott, division", "infantry", 650, {}),
    ("gr39_1", "german", "GR 39", "Grenadier Regiment 39, a battalion (drawn as 650)", "Maj. Gen. H. Kokott, division", "infantry", 650, {}),
    ("gr39_2", "german", "GR 39", "Grenadier Regiment 39, a battalion (drawn as 650)", "Maj. Gen. H. Kokott, division", "infantry", 650, {}),
    ("kunkel", "german", "KG Kunkel", "Reconnaissance (Füsilier) Battalion 26, 'Kampfgruppe Kunkel' (drawn as 500)", "", "infantry", 500, {}),
    ("vgd_t", "german", "Halt tanks", "The seven tanks with the 77th down the railway at Halt", "", "armor", 7, {}),
    ("arlon_t", "german", "Arlon tanks", "The twelve tanks that came up the Arlon road on the night of 23 December (their unit is not in the note)", "", "armor", 12, {}),
    ("flam_t", "german", "Flamierge tanks", "The twelve tanks that came out of the woods south of the St Hubert road with infantry in snow suits on 23 December (their unit is not in the note)", "", "armor", 12, {}),
    ("tigers", "german", "Tigers", "Five Tigers newly arrived near Kokott's CP, sent down the Clochimont road (Tiger sightings are often Mark IVs)", "", "armor", 5, {}),
    # 15th Panzergrenadier Division, Kampfgruppe Maucke
    ("m115_1", "german", "115 PGR", "Kampfgruppe Maucke: the 115th Panzergrenadier Regiment's spearhead, a battalion (drawn as 550)", "Col. W. Maucke", "infantry", 550, {}),
    ("m115_2", "german", "115 PGR", "Kampfgruppe Maucke: a second spearhead battalion (drawn as 550)", "Col. W. Maucke", "infantry", 550, {}),
    ("m115_t", "german", "115 Pz", "Kampfgruppe Maucke's armor: eleven of the eighteen tanks on the 327th's front, those that turned for Hemroulle", "Col. W. Maucke", "armor", 11, {}),
    ("m115_t7", "german", "115 Pz", "Kampfgruppe Maucke's armor: the seven of the eighteen that turned north toward Rolley", "Col. W. Maucke", "armor", 7, {}),
    # 5th Parachute Division, Col. L. Heilmann
    ("fj14", "german", "14 FJR", "A company of the 14th Parachute Regiment at Chaumont (drawn as 150)", "Col. L. Heilmann, division", "infantry", 150, {}),
    ("stug11", "german", "11 StuG Bde", "11th Assault Gun Brigade, 'ten to fifteen remodeled Mark III carriages with 75-mm. guns' (drawn as twelve)", "", "armor", 12, {}),
    ("assenois_g", "german", "Assenois", "Assenois's garrison, 'a mixed group from the 5th Parachute and 26th Volks Grenadier Divisions' (drawn as 500)", "", "infantry", 500, {}),
]
BASE = {row[0]: row for row in OOB}
assert len(BASE) == len(OOB), "a duplicate unit id"
# Units that ride: armored infantry in half-tracks, motorised guns
MOTOR = {"desobry_i", "ryerson_i", "cherry_hq", "ohara_i", "pyle_i", "harper_i", "b10aib", "r53aib", "pz2_recce", "kunkel", "kg902_i", "pl901_1", "pl901_2",
         "pl_recce", "pzg2_1", "pzg2_2", "pzg304_1", "pzg304_2", "m115_1", "m115_2"} | {r[0] for r in OOB if r[5] == "artillery"}

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
def last(id): k = KEYS[id][-1]; return (k["x"], k["y"])
def appear(id, t, p, h, state="line", **kw): keys(id, [K(t, p, h=h, state=state, **kw)])
TINTS = []
def hold_until(id, t0):  # stand until the minute before t0, then turn and go
    if sec(t0) - sec(KEYS[id][-1]["t"]) > 120: keys(id, [K(plus(t0, -1), last(id))])
def at(id, t, **kw): hold_until(id, t); keys(id, [K(t, last(id), **kw)])  # a change in place
def hide(id, t): at(id, t, state="hidden")
def dense(pts, step=1200):  # no straight leg longer than `step`, so no leg runs past three hours
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        n = max(1, math.ceil(math.dist(a, b) / step))
        out += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(1, n + 1)]
    return [p for i, p in enumerate(out) if i == 0 or math.dist(p, out[i - 1]) > 5]
def heading(a, b): return round(math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) % 360)
PACE, DRIVE = 4, 20  # km/h: a column of foot on the road; vehicles on a road in winter
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
def drive(id, t0, pts, h=None, state="line", kmh=DRIVE): return move(id, t0, pts, h, state, "column", kmh)
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
def on_road(line, f):  # the point a fraction f of the way along a road
    L = [0]
    for a, b in zip(line, line[1:]): L.append(L[-1] + math.dist(a, b))
    s = f * L[-1]; i = max(j for j in range(len(L) - 1) if L[j] <= s); u = (s - L[i]) / (L[i + 1] - L[i])
    return (round(line[i][0] + u * (line[i + 1][0] - line[i][0])), round(line[i][1] + u * (line[i + 1][1] - line[i][1])))
LOSS = {}  # id: [(t0, t1, men)], losses falling evenly over each span; a negative figure is men joining
def lose(id, t0, t1, n): LOSS.setdefault(id, []).append((t0, t1, n))
def smoke(at, t0, t1, rate=8, spread=300): features.append(dict(type="smoke", at=list(at), rate=rate, spread=spread, **{"from": t0, "until": t1}))
def strike(name, at, t0, t1, spread=500, h=250): features.append(dict(type="airstrike", name=name, at=list(at), spread=spread, h=h, **{"from": t0, "until": t1}))
def drop(name, kind, zone, t0, t1, units, h, craft):
    features.append(dict(type="drop", kind=kind, name=name, zone=[list(p) for p in zone], h=h, craft=craft, units=list(units), **{"from": t0, "until": t1}))
for id in BASE: appear(id, START, (0, 0), 0, state="hidden")

# Places the movements use, as local metres
NOV, FOY, NEFFE, MAGERET, BIZORY, MONT, MARVIE, WARDIN = P['noville'], P['foy'], P['neffe'], P['mageret'], P['bizory'], P['mont'], P['marvie'], P['wardin']
LONGVILLY, HALT, MANDE, CHAMPS, HEMROULLE, ROLLEY, ASSENOIS = P['longvilly'], P['halt'], P['mande'], P['champs'], P['hemroulle'], P['rolley'], P['assenois']
BRAS, BENON, CHATEAU, HILL510, HILL500, OHARA = P['bras'], P['benonchamps'], P['chateau'], P['hill510'], P['hill500'], P['ohara']
def east(a, b): return along(R_EAST, a, b)
def north(a, b): return along(R_NORTH, a, b)
def marche(a, b): return along(R_MARCHE, a, b)
TOWN_N, TOWN_E, TOWN_S, TOWN_W = off(B, 200, 600), off(B, 600, 100), off(B, 0, -500), off(B, -600, 0)
NEFFE_W = (1250, 1680)          # where 1/501 met the fire west of Neffe, "about 2,000 yards from the city" [DERIVED]
LINE_501_1 = (900, 1950)        # the high ground west of Neffe, the 501st's line from dusk on 19 Dec [DERIVED]
LINE_501_2 = (1450, 3250)       # the high ground west of Bizory [DERIVED]
LINE_327_2 = (-300, -1300)      # 2/327 between Marvie and the Arlon road [DERIVED]
F_COY = on_road([B, P['remoifosse']], 0.62)  # F Company 327th on the Arlon road above Remoifosse [DERIVED]
LINE_326 = on_road([B, P['assenois']], 0.55)  # the 326th Engineers' line on the Assenois road, where the relief came in [DERIVED]
NEUF_RD = on_road([B, P['isle_pre']], 0.85)  # 1/327 and the 35th Engineers astride the Neufchâteau road [DERIVED]
SENON = P['senonchamps']
LINE_327_3 = (-5300, 4000)      # 3/327 after "Plan A", the high ground west of Champs [DERIVED]
DZ = quad(DZ_C, 420, 280, 30)   # the pathfinders' zone, a part of the mile-square zone [DERIVED]

# ---- Monday 18 December ----
# CCB 10th Armored comes up the Arlon road from 15:30 [INF: the start]; "the first two teams got through the town during
# daylight": Cherry east toward Longvilly, O'Hara south-east toward Wardin; "it was dark when the last team began moving",
# Desobry north [M p14]. Hyduke halts short of Longvilly at 19:20 [M p22].
for i, id in enumerate(("hyduke", "ryerson_t", "ryerson_i", "cherry_hq", "ohara_l", "ohara_t", "ohara_i", "fa420", "desobry_t", "desobry_i")):
    appear(id, plus(START, 4 * i), EDGE_S, 0, "column")
    drive(id, plus(START, 4 * i), along(R_ARLON, EDGE_S, B) + [TOWN_S], state="column", kmh=25)
go("hyduke", D(18, "16:15"), D(18, "19:20"), east(B, on_road(R_EAST, 0.62)), h=70, state="line")
go("ryerson_t", D(18, "16:20"), D(18, "19:35"), east(B, on_road(R_EAST, 0.55)), h=70, state="line")
go("ryerson_i", D(18, "16:22"), D(18, "19:40"), east(B, on_road(R_EAST, 0.51)), h=70, state="line")
drive("cherry_hq", D(18, "16:25"), east(B, NEFFE) + [CHATEAU], h=90)
drive("ohara_t", D(18, "16:35"), along(R_WILTZ, B, OHARA), h=100); drive("ohara_i", D(18, "16:38"), along(R_WILTZ, B, off(OHARA, -300, 0)), h=100)
drive("ohara_l", D(18, "16:32"), along(R_WILTZ, B, (3600, -760)), h=100)
drive("fa420", D(18, "16:40"), [off(B, 800, 1200)], h=60)
drive("desobry_t", D(18, "22:00"), north(B, NOV), h=30); drive("desobry_i", D(18, "22:05"), north(B, off(NOV, -150, -100)), h=30)
# Task Force Harper at Allerborn, under fire late in the afternoon; "after dark" panzers destroy two tank platoons and it is
# overrun [C13]. The survivors fall back on CCR's jam at Longvilly [INF].
appear("harper_t", START, off(P['allerborn'], -200, 0), 90); appear("harper_i", START, off(P['allerborn'], -400, 150), 90)
appear("pz2_t2", D(18, "16:00"), EDGE_E, 270, "column"); drive("pz2_t2", D(18, "16:00"), along(R_EAST, EDGE_E, off(P['allerborn'], 900, 150)), h=270)
appear("pz2_t1", D(18, "16:10"), EDGE_E, 270, "column"); drive("pz2_t1", D(18, "16:10"), along(R_EAST, EDGE_E, off(P['allerborn'], 1300, 250)), h=270)
for id in ("pz2_t2", "pz2_t1"): fire(id, D(18, "16:45"), D(18, "20:15"))
for id in ("harper_t", "harper_i"): fire(id, D(18, "16:45"), D(18, "20:00"), state="retreat")
lose("harper_t", D(18, "18:00"), D(18, "20:00"), 10); lose("harper_i", D(18, "18:00"), D(18, "20:00"), 150)
drive("harper_t", D(18, "20:05"), east(last("harper_t"), on_road(R_EAST, 0.7)), h=90, kmh=10)
drive("harper_i", D(18, "20:10"), east(last("harper_i"), on_road(R_EAST, 0.68)), h=90, kmh=10)
# Panzer Lehr: the advance guard, "about fifteen tanks and four companies of the 902d", enters Niederwampach in the early
# evening [C13]; at 22:00 it leaves on a mud road for Benonchamps, is there an hour after midnight, and at 02:00 in Mageret,
# where Bayerlein blocks the road east with three tanks, infantry and mines [M-E p182-183].
NWAMP = P['niederwampach']
for i, id in enumerate(("kg902_t", "kg902_b", "kg902_i")):
    appear(id, plus(D(18, "17:30"), 3 * i), EDGE_ESE, 250, "column"); drive(id, plus(D(18, "17:30"), 3 * i), along(R_BENON, EDGE_ESE, off(NWAMP, 150 * i, 0)), h=250)
    go(id, plus(D(18, "22:00"), 2 * i), plus(D(19, "01:00"), 2 * i), along(R_BENON, NWAMP, off(BENON, 100 * i, 0)), h=270, state="column")
    go(id, plus(D(19, "01:05"), 2 * i), plus(D(19, "02:00"), 2 * i), along(R_BENON, BENON, off(MAGERET, 200 - 100 * i, 0)), h=270, state="column")
at("kg902_b", D(19, "02:10"), h=90, state="line")
# Cherry's mine block east of Neffe and O'Hara's felled logs on the Wiltz road [M-E p183; M p119]
features += [dict(type="works", name="Cherry's roadblock", pts=[[2160, 2060], [2280, 1870]], **{"from": D(18, "18:00"), "until": D(19, "06:00")}),
             dict(type="works", name="Bayerlein's block", pts=[[3720, 2960], [3800, 2780]], **{"from": D(19, "02:00"), "until": D(21, "09:00")}),
             dict(type="works", name="O'Hara's roadblock (about here)", pts=[[1680, -460], [1760, -660]], **{"from": D(18, "18:00"), "until": D(20, "23:00")})]
# Desobry posts three outposts 800 yards out at 23:00 [M p51-52]; the 501st closes into Mande by midnight [M p30].
for i, id in enumerate(("p501_1", "p501_2", "p501_3", "p501_i")):
    appear(id, plus(D(18, "22:30"), 4 * i), EDGE_W, 90, "column"); move(id, plus(D(18, "22:30"), 4 * i), marche(EDGE_W, off(MANDE, 150 * i, 100)), h=90)
# The CCR batteries at Longvilly fire at enemy 200 yards off at 23:15; at 23:40 CCR begins to withdraw and freezes on the
# road [C13; M p24].
for id in ("harper_t", "harper_i"): fire(id, D(18, "23:15"), D(18, "23:40"))

# ---- Tuesday 19 December ----
# The rest of the 101st comes in by the Marche road through the night [INF: the order beyond the 501st]
for i, id in enumerate(("p506_1", "p506_2", "p506_3", "p502_1", "p502_2", "p502_3", "eng326", "fa321", "fa907", "fa377", "fa463", "aa81")):
    t = plus(D(19, "00:30"), 12 * i); appear(id, t, EDGE_W, 90, "column")
    if BASE[id][5] == "artillery": drive(id, t, marche(EDGE_W, off(MANDE, 300 - 60 * i, -250)), h=90, kmh=12)
    else: move(id, t, marche(EDGE_W, off(MANDE, -400 + 80 * i, -200)), h=90)
for i, id in enumerate(("g327_1", "g327_2", "g327_3")):
    t = plus(D(19, "09:00"), 25 * i); appear(id, t, EDGE_W, 90, "column"); move(id, t, marche(EDGE_W, off(MANDE, 100 * i, 300)), h=90)
# The 158th Engineers' outposts at Neffe and Mont [C19]; VIII Corps's artillery in the town [INF: the places]
appear("eng158", START, off(NEFFE, -250, -60), 80)
appear("fa755", D(19, "08:00"), off(B, -500, 1300), 60); appear("fa969", D(19, "08:00"), off(B, -900, -500), 120); appear("fa109", D(19, "11:00"), EDGE_W, 90, "column")
drive("fa109", D(19, "11:00"), marche(EDGE_W, B) + [off(B, 1300, 700)], h=80, kmh=12)
appear("snafu", D(19, "09:00"), off(B, -200, -150), 0)
lose("snafu", D(19, "10:00"), D(25, "12:00"), -350)
# 00:00 to 05:50: Bayerlein at Mageret, then down the road to Neffe; the lead tank hits a mine at Cherry's block and the
# advance resumes at 05:50 with eleven tanks on the highway and a company south of the tracks toward the château; at 07:00
# the armour pauses "almost an hour" at the Neffe station [M-E p183-184].
go("kg902_t", D(19, "05:30"), D(19, "05:40"), east(last("kg902_t"), (2300, 2010)), h=250, state="column")
lose("kg902_t", D(19, "05:40"), D(19, "05:41"), 1)
go("kg902_t", D(19, "05:50"), D(19, "07:00"), east((2300, 2010), off(P['neffe_stn'], 120, 60)), h=250, state="line")
go("kg902_i", D(19, "05:35"), D(19, "07:00"), east(last("kg902_i"), NEFFE) + [off(NEFFE, 0, -120)], h=250, state="line")
fire("eng158", D(19, "05:50"), D(19, "06:30"), state="retreat"); lose("eng158", D(19, "05:50"), D(19, "06:30"), 30)
move("eng158", D(19, "06:31"), east(last("eng158"), MONT) + [off(MONT, -300, 100)], h=80)
# Cherry's reconnaissance platoon at the Neffe road junction breaks back at 06:00 [M p49]; the 501st passes its CP "on the
# minute" at 06:00 [M p33], having come up from Mande in the night [INF]; 1/501 meets the fire west of Neffe about 08:20 [M p34; C19].
for i, id in enumerate(("p501_1", "p501_2", "p501_3", "p501_i")):
    move(id, plus(D(19, "04:15"), 3 * i), marche(last(id), off(B, -500, 300)), h=90, state="column")
go("p501_1", D(19, "06:00"), D(19, "08:20"), east(off(B, -500, 300), NEFFE_W), h=80, state="firing")
fire("kg902_t", D(19, "08:20"), D(19, "09:00")); fire("kg902_i", D(19, "08:20"), D(19, "13:00"))
lose("kg902_i", D(19, "08:20"), D(19, "09:30"), 80)
at("p501_1", D(19, "09:30"), state="line")
move("kg902_t", D(19, "09:01"), [off(NEFFE, 500, 250)], h=250)
fire("cherry_hq", D(19, "10:05"), D(19, "17:00"), state="retreat")
smoke(CHATEAU, D(19, "14:00"), D(19, "17:30"), rate=6, spread=150)
move("cherry_hq", D(19, "17:01"), [MONT], h=80, kmh=6)
fire("kg902_i", D(19, "13:30"), D(19, "17:00"))
move("kg902_t", D(19, "12:00"), east(last("kg902_t"), off(MAGERET, -300, -100)), h=250)
# Hyduke ordered to hold Longvilly at 08:30 while Ryerson fights back through Mageret; at 09:45 Ryerson's lead tank is
# hit 300 yards east of Mageret and plugs the cut [M p25, p27].
MAG_E = on_road(east(MAGERET, LONGVILLY), 0.08)
go("ryerson_t", D(19, "09:00"), D(19, "09:45"), east(last("ryerson_t"), MAG_E), h=250, state="firing")
go("ryerson_i", D(19, "09:05"), D(19, "09:50"), east(last("ryerson_i"), off(MAG_E, 250, 100)), h=250, state="firing")
fire("kg902_b", D(19, "09:45"), D(19, "17:00"))
at("ryerson_t", D(19, "11:00"), state="line"); fire("ryerson_i", D(19, "15:00"), D(19, "16:30"))
# Noville: the half-tracks of 2d Panzer's reconnaissance battalion hit the Bourcy road outpost at 05:30 and withdraw after
# twenty minutes; three tanks duel the Houffalize-road outpost in the fog until 07:30; two Tigers nose out at 08:30 and are
# destroyed by bazookas [M p53-56]. 2d Panzer had turned north east of Longvilly for Noville [M-E p185]; its routes in the
# night are not recorded [INF].
appear("pz2_recce", D(18, "21:00"), EDGE_E, 270, "column")
go("pz2_recce", D(18, "21:00"), D(19, "04:50"), [(10500, 7000), (7500, 7900), off(P['bourcy'], 300, 0)], h=270, state="line")
go("pz2_recce", D(19, "05:10"), D(19, "05:30"), along(R_NOV_BOURCY, P['bourcy'], on_road(R_NOV_BOURCY, 0.25)), h=270, state="firing")
at("pz2_recce", D(19, "05:50"), state="retreat"); go("pz2_recce", D(19, "05:51"), D(19, "06:20"), [on_road(R_NOV_BOURCY, 0.6)], h=270, state="line", moving="retreat")
go("pz2_t2", D(18, "21:00"), D(19, "05:20"), [(10000, 7300), (6000, 9800), (2700, 10300)], h=200, state="line")
go("pz2_t2", D(19, "05:30"), D(19, "05:50"), [off(NOV, 450, 1200)], h=200, state="firing")
go("pz2_t1", D(18, "21:10"), D(19, "06:00"), [(10500, 7600), (6000, 10200), (1600, 10600), (900, 9300)], h=150, state="line")
lose("pz2_t2", D(19, "08:30"), D(19, "08:35"), 2)
for id in ("desobry_t", "desobry_i"): fire(id, D(19, "05:30"), D(19, "07:30"))
# 10:30: "the fog lifted like a curtain going up": more than 30 tanks, 14 in a line on the ridge short of Vaux; nine hit
# straightaway; the fight dies at 11:30 [M p56-58]
at("pz2_t1", D(19, "10:25"), state="firing"); at("pz2_t2", D(19, "10:25"), state="firing")
lose("pz2_t1", D(19, "10:30"), D(19, "11:30"), 9)
for id in ("desobry_t", "desobry_i"): fire(id, D(19, "10:30"), D(19, "11:30"))
lose("desobry_t", D(19, "10:30"), D(19, "11:30"), 3)
at("pz2_t1", D(19, "11:35"), state="line"); at("pz2_t2", D(19, "11:35"), state="line")
# The 2d Panzer grenadiers come up behind the tanks [INF: when and where]
for i, id in enumerate(("pzg2_1", "pzg2_2", "pzg304_1", "pzg304_2")):
    appear(id, plus(D(19, "07:00"), 20 * i), EDGE_N, 200, "column")
for id, p in (("pzg2_1", off(NOV, 900, 1400)), ("pzg2_2", off(NOV, 1300, 600)), ("pzg304_1", (3400, 7300)), ("pzg304_2", (3800, 8600))):
    drive(id, KEYS[id][-1]["t"], [p], h=220, kmh=12)
# 10:50: Higgins sends 1/506 to Noville, the 2d and 3d Bns 506th to reserve north of the town; 1/506 reaches Noville at 13:30
# [M p60-61]. The 506th has come through Bastogne from Mande [INF: the times].
for i, id in enumerate(("p506_1", "p506_2", "p506_3")):
    move(id, plus(D(19, "07:30"), 10 * i), marche(last(id), B) + [off(B, 100 * i, 500)], h=30, state="column")
move("p506_1", D(19, "11:40"), north(B, off(NOV, -100, -300)), h=20)
# 14:30: the Noville counterattack: three tanks up the Houffalize road, four east toward Bourcy, three companies between;
# held until dark, then back into Noville [M p62-63]
for id, p in (("p506_1", off(NOV, 650, 650)), ("desobry_t", off(NOV, 500, 900))):
    go(id, D(19, "14:30"), D(19, "15:10"), [p], h=40, state="firing", moving="charge")
for id in ("pz2_t1", "pz2_t2", "pzg2_1", "pzg2_2"): fire(id, D(19, "14:40"), D(19, "16:40"))
lose("pz2_t1", D(19, "14:40"), D(19, "16:40"), 3); lose("desobry_t", D(19, "14:40"), D(19, "16:40"), 1)
lose("p506_1", D(19, "13:30"), D(19, "17:30"), 90); lose("desobry_i", D(19, "05:30"), D(19, "17:30"), 50)
for id, p in (("p506_1", off(NOV, -100, -300)), ("desobry_t", NOV)): go(id, D(19, "16:45"), D(19, "17:30"), [p], h=40, state="line", moving="retreat")
smoke(off(NOV, 0, 50), D(19, "14:00"), D(20, "13:30"), rate=10, spread=250)
# 2/501 takes Bizory at 12:03 and stops on Hill 510 against the 26th VGD's reconnaissance; 3/501 reaches Mont; Company I
# to the woods west of Wardin, "no enemy" at 13:30; at 14:15 it is attacked in Wardin by seven tanks and a battalion of
# Panzer Lehr and scattered, 45 men and 4 officers lost [M p39-46]
go("p501_2", D(19, "10:00"), D(19, "12:03"), along(R_BIZORY, off(B, -500, 300), BIZORY), h=90, state="line")
go("p501_3", D(19, "10:05"), D(19, "12:00"), east(off(B, -500, 300), MONT) + [off(MONT, 200, 0)], h=100, state="line")
go("p501_i", D(19, "10:10"), D(19, "12:00"), east(off(B, -500, 300), MONT) + [off(MONT, 150, -150)], h=100, state="column")
go("p501_i", D(19, "12:15"), D(19, "13:30"), [(2600, 300)], h=110, state="line")
appear("kunkel", D(19, "10:30"), EDGE_ESE, 270, "column")
go("kunkel", D(19, "10:30"), D(19, "12:00"), along(R_BENON, EDGE_ESE, MAGERET) + [off(HILL510, 350, -100)], h=290, state="line")
go("p501_2", D(19, "12:10"), D(19, "12:45"), [off(HILL510, -300, 50)], h=110, state="firing")
fire("kunkel", D(19, "12:45"), D(19, "13:45"))
at("p501_2", D(19, "13:45"), state="line")
appear("pl_wardin_t", D(19, "10:30"), EDGE_SE, 280, "column"); appear("pl_recce", D(19, "10:40"), EDGE_SE, 280, "column")
drive("pl_wardin_t", D(19, "10:30"), along(R_WILTZ, EDGE_SE, off(BRAS, -800, 0)), h=280, state="line", kmh=12)
drive("pl_recce", D(19, "10:40"), along(R_WILTZ, EDGE_SE, off(BRAS, -500, 150)), h=280, state="line", kmh=12)
fire("ohara_l", D(19, "11:40"), D(19, "12:10"), state="retreat"); fire("pl_wardin_t", D(19, "11:40"), D(19, "12:10"))
drive("ohara_l", D(19, "12:11"), along(R_WILTZ, last("ohara_l"), off(OHARA, 200, 100)), h=100, kmh=12)
go("pl_wardin_t", D(19, "13:30"), D(19, "14:15"), [off(WARDIN, 700, -300)], h=290, state="firing")
go("pl_recce", D(19, "13:35"), D(19, "14:15"), [off(WARDIN, 600, 100)], h=280, state="firing")
go("p501_i", D(19, "13:45"), D(19, "14:10"), [off(WARDIN, -100, 0)], h=100, state="firing")
lose("p501_i", D(19, "14:15"), D(19, "15:00"), 49)
at("p501_i", D(19, "15:00"), state="rout"); go("p501_i", D(19, "15:01"), D(19, "16:30"), [off(MONT, 300, -300)], h=280, state="line", moving="rout")
go("pl_recce", D(19, "15:00"), D(19, "15:30"), [off(WARDIN, 100, 0)], h=280, state="line"); at("pl_wardin_t", D(19, "15:30"), state="line")
# The Longvilly road, 14:00 to about 16:00: Hyduke under direct fire at 14:00 and ordered back at 14:30, the road blocked;
# the Benonchamps force, the 901st and about twenty TDs, on Hill 490 a little after 14:00; the 77th VGR's guns; 2d Panzer's
# 88s below Chifontaine; "all three divisions engaged at one time" [M p26-27; M-E p189-190]. Hill 490 is not placed [INF].
HILL490 = (5650, 2650)
for i, id in enumerate(("pl_td", "pl901_1", "pl901_2", "pl_art")):
    appear(id, plus(D(19, "11:00"), 6 * i), EDGE_ESE, 260, "column")
    drive(id, plus(D(19, "11:00"), 6 * i), along(R_BENON, EDGE_ESE, BENON), h=320, state="column", kmh=10)
drive("pl_td", D(19, "13:40"), [HILL490], h=10, state="firing", kmh=10); drive("pl901_1", D(19, "13:45"), [off(HILL490, -300, -150)], h=10, state="line", kmh=8)
drive("pl901_2", D(19, "13:50"), [off(HILL490, 300, -200)], h=10, state="line", kmh=8); drive("pl_art", D(19, "13:55"), [off(BENON, 300, -300)], h=10, state="firing", kmh=8)
appear("pz2_88", D(19, "13:30"), off(P['chifontaine'], -100, -350), 270); fire("pz2_88", D(19, "14:00"), D(19, "16:00"))
appear("gr77_1", D(19, "11:30"), EDGE_ESE, 280, "column"); appear("gr77_2", D(19, "11:45"), EDGE_ESE, 280, "column")
for id in ("hyduke", "harper_t", "harper_i"): fire(id, D(19, "14:00"), D(19, "15:00"), state="rout")
lose("hyduke", D(19, "14:00"), D(19, "15:00"), 9); lose("harper_t", D(19, "14:00"), D(19, "15:00"), 15); lose("harper_i", D(19, "14:00"), D(19, "15:00"), 150)
at("pl_td", D(19, "16:05"), state="line"); at("pl_art", D(19, "16:05"), state="line")
go("hyduke", D(19, "15:01"), D(19, "15:30"), [off(last("ryerson_t"), 200, 150)], h=250, state="line", moving="rout")
for id in ("harper_t", "harper_i"): go(id, D(19, "15:05"), D(19, "15:40"), [off(last("ryerson_t"), 400, 250)], h=250, state="line", moving="rout"); hide(id, D(19, "16:30"))
# The 26th VGD comes up behind: the 77th to Bizory's east, the 78th against Hill 540 south-east of Foy, stopped by Sink's men;
# the 39th south of Panzer Lehr at Wardin [M-E p186-187]. Hill 540 is not placed; drawn at the Bois Jacques [INF].
move("gr77_1", D(19, "11:30"), along(R_BENON, EDGE_ESE, MAGERET) + [(3300, 3600)], h=260)
move("gr77_2", D(19, "11:45"), along(R_BENON, EDGE_ESE, MAGERET) + [(2900, 2700)], h=260)
for i, id in enumerate(("gr78_1", "gr78_2")):
    appear(id, plus(D(19, "09:00"), 15 * i), EDGE_E, 270, "column"); move(id, plus(D(19, "09:00"), 15 * i), along(R_EAST, EDGE_E, P['longvilly']) + [P['arloncourt'], (2400 + 500 * i, 5200 - 300 * i)], h=250)
for i, id in enumerate(("gr39_1", "gr39_2")):
    appear(id, plus(D(19, "12:00"), 15 * i), EDGE_SE, 280, "column"); move(id, plus(D(19, "12:00"), 15 * i), along(R_WILTZ, EDGE_SE, BRAS) + [(4300 - 300 * i, -900 - 400 * i)], h=290)
# The 502d to Longchamps in the afternoon, the 3d Bn on the hill south and the 1st in the Bois de Niblamont; the 3d Bn 506th
# to Foy, the 2d to Luzery [M p65, p86]; the 327th's CP at Mande at 15:00, its 1st Bn attached to the 501st at 16:30 [M p99];
# the 326th Engineers to Marvie [INF: when].
for id, p, h in (("p502_2", off(P['longchamps'], 300, 100), 20), ("p502_3", off(P['longchamps'], 400, -800), 40), ("p502_1", off(P['longchamps'], -300, -900), 300)):
    move(id, D(19, "12:30"), [off(MANDE, 0, 600), off(CHAMPS, 200, 0), ROLLEY, p], h=h)
move("p506_3", D(19, "13:00"), north(off(B, 200, 500), FOY) + [off(FOY, 100, 150)], h=40); move("p506_2", D(19, "13:00"), north(off(B, 100, 500), P['luzery']), h=40)
move("eng326", D(19, "07:00"), marche(last("eng326"), B) + along(R_WILTZ, B, MARVIE) + [off(MARVIE, 100, -100)], h=120)
move("g327_1", D(19, "16:30"), marche(last("g327_1"), B) + [(300, 500)], h=110)
fire("gr78_1", D(19, "15:30"), D(19, "16:30")); fire("p506_3", D(19, "15:30"), D(19, "16:30"))
# The 101st's guns in place by about ten: Battery B 907th GFA opens "a few minutes after 1000" from the left of the Longvilly
# road [M p36]; the other positions are not recorded [INF].
for id, p in (("fa907", off(P['mardasson'], -200, -250)), ("fa321", off(P['savy'], 400, -300)), ("fa377", off(B, -1100, 900)), ("fa463", off(P['hemroulle'], 400, -200)), ("aa81", off(B, 300, -600))):
    drive(id, D(19, "07:00"), marche(last(id), B) + [p], h=80, kmh=12)
fire("fa907", D(19, "10:05"), D(19, "13:00"))
# 17:00 to 18:00: the 501st falls back to the high ground west of Bizory and Neffe; O'Hara back to the high ground north
# of Marvie at 17:15; Cherry burned out of the château to Mont at dusk [M p46-50]
go("p501_1", D(19, "17:00"), D(19, "17:45"), [LINE_501_1], h=80, state="line")
go("p501_2", D(19, "17:00"), D(19, "17:50"), [LINE_501_2], h=100, state="line")
for id, p in (("ohara_t", off(MARVIE, 200, 350)), ("ohara_i", off(MARVIE, 450, 150)), ("ohara_l", off(MARVIE, 0, 500))):
    drive(id, D(19, "17:15"), along(R_WILTZ, last(id), MARVIE) + [p], h=110, kmh=10)
# 20:30: the 705th TD Battalion reaches Bastogne by Laroche and Champlon, from the north-west [M p21]
for i, id in enumerate(("td705a", "td705b", "td705c")):
    appear(id, plus(D(19, "19:50"), 4 * i), EDGE_W, 90, "column"); drive(id, plus(D(19, "19:50"), 4 * i), marche(EDGE_W, B) + [off(B, -300 + 200 * i, 400)], h=90)

# ---- Wednesday 20 December ----
# 00:30 CCB orders Ryerson out; he pulls out "a little after daybreak" and reaches the paratroopers 40 minutes later
# [M p48; C13], by Arloncourt and Bizory [INF: the route].
for id, p in (("ryerson_t", off(LINE_501_2, 300, 200)), ("ryerson_i", off(LINE_501_2, 150, 350)), ("hyduke", off(LINE_501_2, 450, 50))):
    go(id, D(20, "08:10"), D(20, "08:50"), [P['arloncourt'], p], h=90, state="line")
for id in ("ryerson_t", "ryerson_i", "hyduke"): drive(id, D(20, "10:00"), along(R_BIZORY, last(id), B) + [off(B, 400, 300)], h=90, kmh=10)
hide("hyduke", D(20, "11:30"))
# 02:00: four TDs of B Company 705th at the south edge of Bizory [M p74]
drive("td705b", D(20, "01:20"), along(R_BIZORY, B, BIZORY) + [off(BIZORY, 0, -250)], h=90, kmh=10)
# 05:30 to 09:30: the 2d Bn of a 26th VGD regiment comes over the hill east of Bizory with a Mark IV, a Mark V and two SPs;
# firing opens at 07:30 and the attack is broken in about two hours [M p74-75]. Drawn as the 77th's [INF].
go("gr77_2", D(20, "05:30"), D(20, "07:30"), [off(BIZORY, 800, -100)], h=270, state="firing")
for id in ("td705b", "p501_2"): fire(id, D(20, "07:30"), D(20, "09:30"))
at("gr77_2", D(20, "09:30"), state="retreat"); go("gr77_2", D(20, "09:31"), D(20, "10:30"), [(3000, 2800)], h=270, state="line", moving="retreat")
# 04:00 to 06:00: the 327th's 2d Bn marches into Bastogne at 06:00 and goes straight on to Marvie, relieving the engineers [M p99]
move("g327_2", D(20, "04:20"), marche(last("g327_2"), B) + along(R_WILTZ, B, MARVIE) + [off(MARVIE, -100, 0)], h=120, kmh=4.5)
move("eng326", D(20, "07:30"), along(R_WILTZ, MARVIE, B) + [off(B, 0, -900)], h=200)
# 07:30: two tanks charge into Noville and are burned [M p86-87]
go("pz2_t2", D(20, "07:20"), D(20, "07:35"), [off(NOV, 300, 700)], h=200, state="firing"); at("pz2_t2", D(20, "08:00"), state="line")
lose("pz2_t2", D(20, "07:30"), D(20, "07:40"), 2)
# 08:00 to 10:30: two companies and three tanks attack 3/506 at Foy; it withdraws to the high ground south [M p90].
# Lüttwitz puts the 78th at Foy on the 20th [M-E p193].
go("gr78_1", D(20, "07:20"), D(20, "08:00"), [off(FOY, 450, 300)], h=230, state="firing"); fire("p506_3", D(20, "08:00"), D(20, "10:30"), state="retreat")
go("p506_3", D(20, "10:31"), D(20, "11:00"), [off(FOY, 0, -650)], h=20, state="line", moving="retreat")
go("gr78_1", D(20, "10:30"), D(20, "11:00"), [off(FOY, 150, 100)], h=200, state="line")
# 10:00: the fog lifts at Noville, 15 German tanks in view, four hit [M p88]
fire("pz2_t2", D(20, "10:00"), D(20, "10:40")); fire("desobry_t", D(20, "10:00"), D(20, "10:40"))
lose("pz2_t2", D(20, "10:00"), D(20, "10:40"), 4)
# 11:25: four tanks and six half-tracks attack Marvie from the woods south-east; two Mark IVs and a half-track killed by
# O'Hara's Shermans; the glider infantry clears the houses; 20 prisoners and 30 dead; clear by about 13:00 [M p101-106]
appear("pl901_tk", D(20, "10:30"), off(MARVIE, 1300, -800), 300, "line")
drive("pl901_1", D(20, "08:00"), along(R_WILTZ, BRAS, OHARA) + [off(MARVIE, 1000, -700)], h=300, kmh=8)
go("pl901_tk", D(20, "11:25"), D(20, "11:40"), [off(MARVIE, 450, -350)], h=300, state="firing")
go("pl901_1", D(20, "11:25"), D(20, "11:50"), [off(MARVIE, 300, -250)], h=300, state="firing")
lose("pl901_tk", D(20, "11:30"), D(20, "11:45"), 2); lose("pl901_1", D(20, "11:30"), D(20, "13:00"), 50); lose("g327_2", D(20, "11:30"), D(20, "13:00"), 20)
for id in ("ohara_t", "g327_2"): fire(id, D(20, "11:30"), D(20, "13:00"))
for id in ("pl901_tk", "pl901_1"): at(id, D(20, "13:00"), state="retreat")
go("pl901_tk", D(20, "13:01"), D(20, "13:30"), [off(MARVIE, 1300, -1300)], h=300, state="line", moving="retreat")
go("pl901_1", D(20, "13:01"), D(20, "13:50"), [off(MARVIE, 1100, -1100)], h=300, state="line", moving="retreat")
# 11:30: 3/502 toward Recogne to open the way for Noville [M p90]
go("p502_3", D(20, "11:30"), D(20, "12:30"), [off(P['recogne'], -300, -200)], h=60, state="line")
# 13:00 to dusk: out of Noville. C Company 506th leaves at 13:15 and the vehicles at 13:25; the column is ambushed at a
# farmhouse 500 yards short of Foy, Shermans burned, the infantry hooks right through the fields and takes 43 prisoners;
# Toms's TDs enter Foy at 14:30; at dusk the column is through Foy [M p93-97]. Desobry went with fifteen tanks and came back
# with four; 1/506 lost 13 officers and 199 men [M p97].
SHORT_FOY = on_road(north(FOY, NOV), 0.2)
go("p506_1", D(20, "13:15"), D(20, "14:00"), north(last("p506_1"), SHORT_FOY), h=200, state="firing")
go("desobry_t", D(20, "13:25"), D(20, "14:05"), north(last("desobry_t"), off(SHORT_FOY, 100, 150)), h=200, state="firing")
go("desobry_i", D(20, "13:25"), D(20, "14:10"), north(last("desobry_i"), off(SHORT_FOY, 150, 300)), h=200, state="firing")
fire("gr78_1", D(20, "14:00"), D(20, "16:00")); lose("gr78_1", D(20, "14:00"), D(20, "16:00"), 43)
lose("desobry_t", D(20, "14:00"), D(20, "14:30"), 7); lose("p506_1", D(19, "17:30"), D(20, "16:30"), 122); lose("desobry_i", D(20, "13:15"), D(20, "16:30"), 50)
drive("td705c", D(20, "12:30"), north(off(B, -100, 400), off(FOY, 0, -650)), h=20, kmh=8)
go("td705c", D(20, "14:00"), D(20, "14:30"), [off(FOY, 0, -100)], h=20, state="firing")
go("gr78_1", D(20, "16:01"), D(20, "16:30"), [off(FOY, 700, 500)], h=230, state="line", moving="retreat")
for id, p in (("p506_1", off(P['luzery'], 200, 300)), ("desobry_t", off(B, 500, 800)), ("desobry_i", off(B, 300, 900)), ("td705c", off(B, -200, 600))):
    go(id, D(20, "16:30"), D(20, "18:30") if id == "p506_1" else D(20, "17:30"), along(R_NORTH, last(id), B)[:-1] + [p], h=20, state="line")
smoke(off(NOV, -150, -100), D(20, "13:25"), D(20, "16:00"), rate=14, spread=150)
# 2d Panzer takes Noville "somewhere near the middle of the afternoon" [M-E p191]
for id, p in (("pz2_t1", off(NOV, 0, 300)), ("pz2_t2", off(NOV, 300, 100)), ("pzg2_1", off(NOV, -200, 0)), ("pzg2_2", off(NOV, 200, -300)), ("pz2_recce", off(NOV, 600, -200))):
    go(id, D(20, "14:30"), D(20, "15:30"), [p], h=200, state="line")
# Afternoon to 20:00: the 39th and the reconnaissance battalion swing south and west by Villers-la-Bonne-Eau and Hompré;
# "Sibret was captured about 2000"; the 39th is checked a kilometre north of Remoifosse and in the wood a kilometre north
# of Assenois, the reconnaissance battalion at Chenogne [M-E p192]. Lutremange, on their road, is off the map.
move("kunkel", D(20, "12:30"), [(3500, -2500), P['villers'], P['hompre'], P['sibret'], off(P['sibret'], -300, 200)], h=0, state="firing", kmh=8)
fire("kunkel", D(20, "19:40"), D(20, "20:10")); go("kunkel", D(20, "20:15"), D(20, "21:30"), [off(P['chenogne'], 250, -100)], h=60, state="line")
move("gr39_1", D(20, "13:00"), [(1500, -4000), P['lutrebois'], off(P['remoifosse'], -50, -700), off(P['remoifosse'], 0, 1000)], h=0)
move("gr39_2", D(20, "12:40"), [(1600, -4400), P['villers'], P['hompre'], off(ASSENOIS, 200, 300), off(ASSENOIS, 250, 1000)], h=10)
# 19:00: Panzer Lehr's 902d charges down the road from Neffe into "a dam of fire" from the eleven artillery battalions; two
# Panthers and a Tiger Royal destroyed at the last houses; 19:00 to 23:00 the attack between Neffe and Mont dies on the wire
# against 3/501 and Andrews's TDs [M p76-78]
drive("fa420", D(20, "14:00"), marche(last("fa420"), P['isle_hesse']) + along(R_SENON, P['isle_hesse'], off(SENON, 200, 300)), h=200, kmh=10)
drive("td705a", D(20, "16:00"), east(off(B, -300, 400), MONT) + [off(MONT, 350, 200)], h=80, kmh=8)
drive("kg902_t", D(20, "18:00"), east(last("kg902_t"), off(NEFFE, 300, 100)), h=250, kmh=10)
go("kg902_t", D(20, "19:00"), D(20, "19:15"), [off(NEFFE, -250, -20)], h=250, state="firing")
lose("kg902_t", D(20, "19:05"), D(20, "19:30"), 3)
go("kg902_i", D(20, "19:00"), D(20, "19:40"), [(1100, 1500)], h=260, state="firing")
for id in ("p501_3", "td705a", "p501_1"): fire(id, D(20, "19:00"), D(20, "23:00"))
for id in ("fa907", "fa321", "fa377", "fa463", "fa755", "fa969", "fa109", "fa420"): fire(id, D(20, "19:00"), D(20, "19:40"))
lose("kg902_i", D(20, "19:40"), D(20, "23:00"), 120)
go("kg902_t", D(20, "19:45"), D(20, "20:15"), [off(NEFFE, 500, 200)], h=250, state="line", moving="retreat")
at("kg902_i", D(20, "23:00"), state="retreat"); go("kg902_i", D(20, "23:01"), D(20, "23:45"), [off(NEFFE, 200, -100)], h=250, state="line", moving="retreat")
# 16:00 to 22:30: Company A 501st clears the woods south of the railway toward Halt; seven tanks and two companies of the
# 77th come down the railway and are ambushed in the fog; A Company falls back at 22:30 [M p80-82]
appear("vgd_t", D(20, "18:30"), off(HALT, 2400, 1700), 230, "column")
go("vgd_t", D(20, "19:30"), D(20, "20:30"), [off(HALT, 500, 400)], h=230, state="firing")
go("gr77_1", D(20, "18:30"), D(20, "20:30"), [off(HALT, 300, 200)], h=230, state="firing")
at("vgd_t", D(20, "22:30"), state="line"); at("gr77_1", D(20, "22:30"), state="line")
go("gr77_1", D(20, "23:00"), D(21, "01:00"), [off(HALT, -300, -100)], h=230, state="line")
TINT_FOG = "rgba(205,208,212,0.38)"
TINTS += [dict(color=TINT_FOG, **{"from": D(19, "06:00"), "until": D(19, "10:30")}), dict(color=TINT_FOG, **{"from": D(19, "13:30"), "until": D(19, "17:00")}),
          dict(color=TINT_FOG, **{"from": D(20, "06:00"), "until": D(20, "10:00")}), dict(color=TINT_FOG, **{"from": D(20, "13:00"), "until": D(20, "17:00")}),
          dict(color=TINT_FOG, **{"from": D(21, "06:00"), "until": D(21, "11:00")}), dict(color=TINT_FOG, **{"from": D(25, "06:30"), "until": D(25, "09:00")}),
          dict(color="rgba(236,238,242,0.12)", **{"from": D(20, "17:00"), "until": END}),
          dict(color="rgba(228,231,236,0.30)", **{"from": D(22, "13:00"), "until": D(22, "17:00")}), dict(color="rgba(228,231,236,0.12)", **{"from": D(23, "17:00"), "until": D(23, "20:00")})]

# ---- Thursday 21 December ----
# 04:00 to 11:00: D Company 506th finds its flank turned at 04:00; A and C Companies arrive about 08:15; "By about 1100 ...
# the envelopment was complete": about 100 of the 77th captured and 55 killed by the 506th, 80 driven into the 501st [M p83-85]
fire("gr77_1", D(21, "04:00"), D(21, "11:00"), state="retreat"); lose("gr77_1", D(21, "04:00"), D(21, "11:00"), 235)
go("p506_2", D(21, "04:00"), D(21, "05:00"), [off(HALT, -800, -300)], h=60, state="firing")
go("p506_1", D(21, "07:00"), D(21, "08:15"), [off(HALT, -600, 500)], h=110, state="firing")
fire("p501_1", D(21, "08:00"), D(21, "11:00"))
for id in ("p506_2", "p506_1"): at(id, D(21, "11:00"), state="line")
go("gr77_1", D(21, "11:01"), D(21, "12:30"), [(3300, 4200)], h=230, state="line", moving="retreat")
go("p506_2", D(21, "12:00"), D(21, "12:45"), [off(HALT, -150, 0)], h=50, state="line")
go("p506_1", D(21, "12:00"), D(21, "13:30"), [off(P['luzery'], 200, 300)], h=40, state="line")
# Panzer Lehr leaves for Morhet and the west; the 77th replaces the 902d before Neffe; the 78th takes over 2d Panzer's
# sector, and 2d Panzer is strung out from Tenneville, off the map to the north-west, back to Bourcy [M-E p193]. The roads
# they took are not recorded [INF].
LEHR_W = [(2500, -2500), (-200, -4500), P['hompre'], P['sibret'], off(P['morhet'], 300, 0)]
for i, id in enumerate(("kg902_t", "kg902_b", "kg902_i", "pl_recce", "pl_wardin_t", "pl_art")):
    drive(id, plus(D(21, "06:00"), 15 * i), LEHR_W, h=270, state="column", kmh=12); hide(id, plus(KEYS[id][-1]["t"], 2))
go("gr77_2", D(21, "07:00"), D(21, "09:00"), [off(NEFFE, 400, 0)], h=250, state="line")
for i, id in enumerate(("pz2_t1", "pz2_t2", "pzg2_1", "pzg2_2", "pzg304_2", "pz2_88")):
    drive(id, plus(D(21, "08:00"), 20 * i), [off(NOV, -800, 900), (-2500, 9800), (-7000, 9600), (-11900, 9400)], h=270, state="column", kmh=12)
    hide(id, plus(KEYS[id][-1]["t"], 1))
go("pzg304_1", D(21, "08:00"), D(21, "09:30"), [off(P['bourcy'], -300, -200)], h=230, state="line")
go("gr78_2", D(21, "07:00"), D(21, "09:00"), [off(NOV, 300, -700)], h=200, state="line")
go("pz2_recce", D(21, "07:30"), D(21, "08:30"), [off(P['bourcy'], 200, 200)], h=230, state="line")
# Kampfgruppe Kunkel nearly reaches the highway near Mande [M-E p193]; Team Pyle to Senonchamps to cover the 420th; Germans in
# American dress from Sibret; the fight into the Bois de Fragotte; by night Browne holds 4,000 yards with 300 infantry and
# 19 tanks [M p113]. The 420th had moved to Senonchamps by then [INF: when].
for id in ("pyle_t", "pyle_i"): appear(id, D(21, "08:00"), off(B, -300, -100), 260, "column")
drive("pyle_t", D(21, "08:00"), marche(B, P['isle_hesse']) + along(R_SENON, P['isle_hesse'], off(SENON, 0, -250)), h=180, kmh=8)
drive("pyle_i", D(21, "08:05"), marche(B, P['isle_hesse']) + along(R_SENON, P['isle_hesse'], off(SENON, -300, -300)), h=180, kmh=8)
go("kunkel", D(21, "08:30"), D(21, "10:00"), [off(SENON, -300, -1100)], h=10, state="firing")
for id in ("pyle_t", "pyle_i"): fire(id, D(21, "10:00"), D(21, "13:00"))
go("kunkel", D(21, "13:00"), D(21, "14:30"), [off(SENON, -1700, -300)], h=60, state="line", moving="retreat")
# Early afternoon: Germans across the Arlon road; 1/327 to the south-west, astride the Neufchâteau road; the 35th
# Engineers block that road at early dark [M p118-119; C19]
move("g327_1", D(21, "12:30"), [NEUF_RD], h=220)
appear("eng35", D(21, "14:00"), off(B, -200, -300), 220, "column"); move("eng35", D(21, "14:00"), along(R_NEUF, B, off(NEUF_RD, -500, -200)), h=220)
move("eng326", D(21, "13:00"), [LINE_326], h=210)
# The 39th astride the southern roads and the Assenois garrison [M-E p195; C21] [INF: the places]
appear("assenois_g", D(21, "06:00"), off(ASSENOIS, 0, 150), 30)
go("gr39_1", D(21, "09:00"), D(21, "10:00"), [off(F_COY, 0, -600)], h=0, state="line")
go("g327_2", D(21, "09:00"), D(21, "09:30"), [LINE_327_2], h=160, state="line")  # between Marvie and the Arlon road, covering Hill 500 [DERIVED]
# 07:30: 1/502 east toward Recogne; Stopka's line pulled back south of Recogne at noon [M p150-151]
go("p502_1", D(21, "07:30"), D(21, "08:45"), [off(P['recogne'], -1200, -600)], h=60, state="line")
go("p502_3", D(21, "12:00"), D(21, "12:40"), [off(P['recogne'], -200, -700)], h=40, state="line")

# ---- Friday 22 December ----
# 09:00: a German block on the Mont road south-east of Flamizoulle, cleared before noon by 3/327, 25 prisoners [M p150]
move("g327_3", D(21, "10:00"), [off(P['flamizoulle'], 300, -500)], h=270)
go("kunkel", D(22, "08:00"), D(22, "09:00"), [off(P['flamizoulle'], 600, -1300)], h=0, state="firing"); fire("g327_3", D(22, "09:00"), D(22, "11:30"))
lose("kunkel", D(22, "09:00"), D(22, "11:30"), 25); at("kunkel", D(22, "11:30"), state="retreat")
go("kunkel", D(22, "11:31"), D(22, "12:30"), [off(SENON, -1500, -500)], h=60, state="line", moving="retreat")
# 11:30: four Germans with a white flag come up the road from Remoifosse to F Company 327th; "Nuts!" goes back at 13:50;
# two small attacks on F Company at 15:55 and 17:00 are beaten off by fire [M p115-117]
fire("gr39_1", D(22, "15:55"), D(22, "16:15")); fire("gr39_1", D(22, "17:00"), D(22, "17:20"))
fire("g327_2", D(22, "15:55"), D(22, "16:15")); fire("g327_2", D(22, "17:00"), D(22, "17:20"))
# Noon: A Company 502d to Champs and the 1st Bn 502d to Hemroulle, facing west [M p151]
go("p502_1", D(22, "11:00"), D(22, "12:30"), [off(HEMROULLE, -350, 700)], h=270, state="line")
# Afternoon: three attacks from the woods near Senonchamps; at twilight Browne reports "terrible casualties" [C19]
go("kunkel", D(22, "13:30"), D(22, "14:30"), [off(SENON, -700, -500)], h=60, state="firing")
for id in ("pyle_t", "pyle_i", "fa420"): fire(id, D(22, "14:30"), D(22, "16:30"))
at("kunkel", D(22, "16:30"), state="line")
# The 4th Armored: CCB starts at 04:30 and is in sight of Burnon at noon, "about seven miles from Bastogne"; it clears the
# rear guard after midnight [C21]
for i, id in enumerate(("b8tk", "b10aib")):
    appear(id, plus(D(22, "11:30"), 5 * i), (-5000 - 200 * i, -11900), 0, "column")
    drive(id, plus(D(22, "11:30"), 5 * i), [off(P['burnon'], 200 * i, -600)], h=0, state="line", kmh=8)
appear("fj14", D(22, "10:00"), off(P['burnon'], 0, 150), 180)
fire("fj14", D(22, "12:30"), D(22, "13:30")); go("fj14", D(23, "00:30"), D(23, "01:30"), [off(P['chaumont'], 0, -250)], h=180, state="line", moving="retreat")
go("b10aib", D(23, "00:30"), D(23, "01:30"), [off(P['burnon'], 200, 100)], h=0, state="line")
go("b8tk", D(23, "01:00"), D(23, "01:40"), [off(P['burnon'], -100, 200)], h=0, state="line")

# The perimeter as it stood on 22 December, from the battalions' places [DERIVED in the note from its §3]
PERIMETER = [(1500, 3350), (950, 1950), (650, 1250), (550, -450), (-1450, -2250), (-2900, -950), (-3450, -350), (-5600, 300), (-6300, 1300),
             (-7300, 3000), (-7500, 4250), (-4900, 5900), (-3400, 7350), (-100, 6550), (900, 5550), (1700, 4450), (1500, 3350)]
features.append(dict(type="works", name="the perimeter, 22 December", pts=[list(p) for p in PERIMETER], **{"from": D(22, "06:00")}))
# The 77th to the north-west sector from 22 December [M-E p195], round the north [INF: the road]
for i, id in enumerate(("gr77_1", "gr77_2")):
    move(id, plus(D(22, "05:00"), 30 * i), [(2600, 6200), off(NOV, -500, -400), (-2500, 9300), (-5600, 6900 - 500 * i)], h=150)
go("p502_1", D(22, "13:00"), D(22, "14:00"), [off(CHAMPS, 400, -400)], h=280, state="line")
move("pl_td", D(20, "09:00"), [(3300, -1300)], h=270, kmh=8)
move("pl901_2", D(20, "09:00"), [(2700, -1800)], h=280, kmh=8)

# ---- Saturday 23 December ----
# 09:35: "several large planes were circling"; the pathfinders jump in the 2d Bn 327th's area [M p137]. Three aircraft, the
# run-in heading and the rally at 09:45 on the zone are [INF].
drop("Pathfinders over the 327th", "para", DZ, D(23, "09:35"), D(23, "09:37"), ["pf327"], 60, 3)
appear("pf327", D(23, "09:45"), DZ_C, 60, "line")
features.append(label("drop zone (about here)", DZ_C, dy=-420, **{"from": D(23, "09:00"), "until": D(24, "16:00")}))
# Noon to dark: twelve tanks and infantry in snow suits come out of the woods south of the St Hubert road; 3/327's outposts
# withdraw about 13:30 and the Germans halt on the ridge near Cochleval (not placed) and fire into C Company; at dark the
# Flamierge roadblock is overrun from the north-west, four tanks hit C Company and ten more come over the ridge from the
# south; under Allen's "Plan A" the battalion withdraws to the high ground west of Champs [M p152-154]. The 26th VGD's
# reconnaissance battalion closes its grip on the Bastogne-Champlon road [M-E p196].
appear("flam_t", D(23, "11:00"), (-9400, 3100), 30, "line")
go("flam_t", D(23, "12:00"), D(23, "13:00"), [(-8700, 3700)], h=40, state="firing")
fire("g327_3", D(23, "12:30"), D(23, "13:30"))
go("flam_t", D(23, "13:30"), D(23, "14:00"), [(-8300, 3900)], h=50, state="firing")
at("flam_t", D(23, "16:00"), state="line")
move("kunkel", D(23, "09:00"), [(-9000, 2000), (-10200, 5600)], h=110, state="line", kmh=8)
go("kunkel", D(23, "16:45"), D(23, "17:30"), [off(P['flamierge'], 700, -100)], h=110, state="firing")
go("flam_t", D(23, "16:50"), D(23, "17:30"), [(-7700, 3900)], h=50, state="firing")
fire("g327_3", D(23, "17:00"), D(23, "18:00"), state="retreat")
go("g327_3", D(23, "18:01"), D(23, "19:30"), [LINE_327_3], h=250, state="line", moving="retreat")
go("kunkel", D(23, "18:30"), D(23, "20:00"), [off(P['flamizoulle'], 200, 0)], h=90, state="line")
go("flam_t", D(23, "18:30"), D(23, "19:30"), [off(MANDE, -300, 400)], h=60, state="line")
# 13:30 to dusk: CCB 4th Armored assaults Chaumont after fighter-bomber strikes; ten to fifteen assault guns of the 11th
# Brigade counterattack; it is repulsed at dusk with eleven Shermans lost and about 65 men of A Company 10th AIB [C21]
strike("Fighter-bombers on Chaumont", P['chaumont'], D(23, "13:00"), D(23, "13:15"), 400, h=20)
go("b8tk", D(23, "12:00"), D(23, "13:30"), along(R_CHAUMONT, last("b8tk"), off(P['chaumont'], -100, -700)), h=10, state="firing")
go("b10aib", D(23, "12:10"), D(23, "13:30"), along(R_CHAUMONT, last("b10aib"), off(P['chaumont'], 150, -650)), h=10, state="firing")
fire("fj14", D(23, "13:30"), D(23, "14:30"), state="retreat"); go("fj14", D(23, "14:31"), D(23, "15:00"), [off(P['chaumont'], 300, 500)], h=200, state="line", moving="retreat")
go("b8tk", D(23, "14:00"), D(23, "14:40"), [off(P['chaumont'], -100, -100)], h=10, state="line")
go("b10aib", D(23, "14:05"), D(23, "14:45"), [off(P['chaumont'], 150, 0)], h=10, state="line")
appear("stug11", D(23, "14:00"), off(P['hompre'], -100, -400), 200, "column")
go("stug11", D(23, "15:00"), D(23, "15:40"), [off(P['chaumont'], 500, 600)], h=210, state="firing")
for id in ("b8tk", "b10aib"): fire(id, D(23, "15:40"), D(23, "16:30"), state="retreat")
lose("b8tk", D(23, "13:30"), D(23, "16:30"), 11); lose("b10aib", D(23, "13:30"), D(23, "16:30"), 65)
go("b8tk", D(23, "16:31"), D(23, "17:15"), [off(P['chaumont'], -300, -1500)], h=10, state="line", moving="retreat")
go("b10aib", D(23, "16:31"), D(23, "17:20"), [off(P['chaumont'], 0, -1400)], h=10, state="line", moving="retreat")
at("stug11", D(23, "16:40"), state="line"); go("fj14", D(23, "17:00"), D(23, "17:30"), [off(P['chaumont'], 0, 50)], h=180, state="line")
# Afternoon: Kokott sends five Tigers down the Clochimont road against the 4th Armored [M-E p196]
appear("tigers", D(23, "14:00"), off(ASSENOIS, 300, 100), 220, "column")
drive("tigers", D(23, "14:00"), along(R_ASSENOIS, ASSENOIS, P['clochimont']) + [off(P['clochimont'], 100, -500)], h=190, kmh=10)
# 17:25: Marvie shelled by tanks in the firs above Martaimont; 17:35 tanks and snow-suited infantry attack; after 18:40 a
# platoon of G Company is surrounded on Hill 500 and overwhelmed some time after 19:00; at 20:00 German infantry are in the
# south end of Marvie and two Shermans are sent in; near midnight the Shermans knock out the lead German tank; Rouzie's
# scratch force and twelve guns of the 81st close the gap [M p121-130]. 18:30: McAuliffe sends Team Cherry [C19].
move("pl_td", D(23, "16:00"), [off(P['martaimont'], -150, 350)], h=330, state="line", kmh=8)
fire("pl_td", D(23, "17:25"), D(23, "19:30"))
go("pl901_tk", D(23, "17:35"), D(23, "18:10"), [off(MARVIE, 200, -450)], h=330, state="firing")
go("pl901_1", D(23, "17:35"), D(23, "18:20"), [off(MARVIE, 0, -450)], h=340, state="firing")
fire("g327_2", D(23, "17:35"), D(24, "01:00"))
go("pl901_2", D(23, "18:00"), D(23, "18:40"), [off(HILL500, 350, -150)], h=290, state="firing")
lose("g327_2", D(23, "18:40"), D(23, "19:30"), 60); lose("g327_2", D(23, "20:00"), D(24, "01:00"), 12)
at("pl901_2", D(23, "19:40"), state="line")
go("pl901_1", D(23, "20:00"), D(23, "20:30"), [off(MARVIE, 0, -250)], h=340, state="firing")
for id, p in (("ryerson_t", off(MARVIE, -100, 200)), ("ryerson_i", off(MARVIE, -300, 250))): drive(id, D(23, "18:30"), along(R_WILTZ, last(id), MARVIE)[:-1] + [p], h=160, kmh=8)
fire("ryerson_t", D(23, "23:45"), D(24, "00:45")); lose("pl901_tk", D(23, "23:50"), D(24, "00:10"), 1)
drive("aa81", D(23, "23:00"), along(R_WILTZ, last("aa81"), MARVIE)[:-1] + [off(MARVIE, -350, 400)], h=150, kmh=8)
fire("aa81", D(24, "00:00"), D(24, "01:00"))
for id in ("pl901_1", "pl901_tk"): at(id, D(24, "01:00"), state="line")
smoke(off(MARVIE, 0, -150), D(23, "20:00"), D(24, "06:00"), rate=8, spread=200)
# 20:00: twelve tanks come north up the Arlon road at F Company; two break through into Bastogne [M p123, p129]
appear("arlon_t", D(23, "19:20"), on_road(R_ARLON, 0.55), 0, "column")
go("arlon_t", D(23, "19:30"), D(23, "20:00"), along(R_ARLON, last("arlon_t"), off(F_COY, 0, -400)), h=0, state="firing")
at("arlon_t", D(23, "20:45"), state="retreat"); go("arlon_t", D(23, "20:46"), D(23, "21:20"), [on_road(R_ARLON, 0.55)], h=180, state="line", moving="retreat")
hide("arlon_t", D(23, "21:30"))

# ---- Sunday 24 December ----
# 08:30 to 15:30 the second airdrop, about 100 tons from 160 planes [M p138]; 13:40 and 16:45, six P-47s bomb and strafe
# Marvie in error [M p130-131]; 19:45 Bastogne bombed [M p131]
strike("P-47s on Marvie, in error", MARVIE, D(24, "13:40"), D(24, "13:50"), 350, h=300)
strike("P-47s on Marvie again", MARVIE, D(24, "16:45"), D(24, "16:55"), 350, h=120)
strike("The Luftwaffe over Bastogne", B, D(24, "19:45"), D(24, "20:00"), 600, h=240)
smoke(off(B, 150, 100), D(24, "20:00"), D(25, "10:00"), rate=8, spread=350)
drive("ryerson_t", D(24, "10:00"), along(R_WILTZ, last("ryerson_t"), B) + [off(B, 400, 300)], h=270, kmh=8)
drive("ryerson_i", D(24, "10:05"), along(R_WILTZ, last("ryerson_i"), B) + [off(B, 300, 400)], h=270, kmh=8)
drive("td705c", D(24, "14:00"), along(R_BERTOGNE, B, P['savy']) + [off(HEMROULLE, -300, 500)], h=260, kmh=8)
appear("b318", D(24, "12:00"), (-5300, -11900), 0, "column"); move("b318", D(24, "12:00"), [off(P['burnon'], -400, 200)], h=0)
# 22:00: the forward elements of the 15th Panzergrenadier Division reach the sector facing Champs and Hemroulle, from the
# north-west; Kokott sets the attack for 03:00 [M-E p197]
for i, id in enumerate(("m115_t", "m115_t7", "m115_1", "m115_2")):
    appear(id, plus(D(24, "20:00"), 8 * i), EDGE_W, 90, "column")
    drive(id, plus(D(24, "20:00"), 8 * i), marche(EDGE_W, MANDE) + [off(MANDE, 700 + 150 * i, 250 - 100 * i)], h=60, kmh=12)

# ---- Monday 25 December, Christmas ----
# 02:45 shelling; bombs round Rolley about 03:00 [M p157; C19]; 03:30 to 05:45 Company A 502d in Champs, house to house;
# two battalions of the 77th make the attack [M p157-159, p169]
strike("Bombs round Rolley", ROLLEY, D(25, "02:55"), D(25, "03:10"), 500, h=120)
go("gr77_1", D(25, "03:00"), D(25, "03:30"), [off(CHAMPS, -150, 250)], h=130, state="firing")
go("gr77_2", D(25, "03:05"), D(25, "03:35"), [off(CHAMPS, -400, -50)], h=110, state="firing")
fire("p502_1", D(25, "03:30"), D(25, "09:00"))
lose("gr77_1", D(25, "03:30"), D(25, "09:00"), 100); lose("gr77_2", D(25, "03:30"), D(25, "09:00"), 79)
for id in ("gr77_1", "gr77_2"): at(id, D(25, "09:00"), state="retreat")
go("gr77_1", D(25, "09:01"), D(25, "10:00"), [off(CHAMPS, -1000, 900)], h=130, state="line", moving="retreat")
go("gr77_2", D(25, "09:01"), D(25, "10:00"), [off(CHAMPS, -1300, 300)], h=110, state="line", moving="retreat")
# 05:00: 18 tanks formed just east of Mande; 07:10 they and the infantry break through A and B Companies 3/327, and split,
# seven north toward Rolley and the rest toward Hemroulle; C Company 502d fires into the riders from the woods, two hidden
# TDs of C Company 705th take the turning tanks in flank, the 463d fires over open sights; "By 0900 ... the action was
# cleared up around Rolle"; all 18 tanks disabled; C Company 502d counted 67 dead and 35 prisoners, and 3/327's A Company,
# 68 survivors, took 92 prisoners [M p160-169]
BREAK = off(LINE_327_3, -150, -150)
go("m115_t", D(25, "06:30"), D(25, "07:10"), [BREAK], h=60, state="firing", moving="charge"); go("m115_t7", D(25, "06:35"), D(25, "07:10"), [off(BREAK, 100, 200)], h=60, state="firing", moving="charge")
go("m115_1", D(25, "06:40"), D(25, "07:10"), [off(BREAK, -100, 100)], h=60, state="firing")
fire("g327_3", D(25, "07:00"), D(25, "09:00")); lose("g327_3", D(25, "07:10"), D(25, "07:30"), 9)
go("m115_t7", D(25, "07:15"), D(25, "07:45"), [off(ROLLEY, -500, -400)], h=30, state="firing", moving="charge")
go("m115_t", D(25, "07:15"), D(25, "07:45"), [off(HEMROULLE, -500, 100)], h=80, state="firing", moving="charge")
go("m115_1", D(25, "07:15"), D(25, "07:50"), [off(HEMROULLE, -700, 300)], h=70, state="firing")
lose("m115_t7", D(25, "07:30"), D(25, "09:00"), 7); lose("m115_t", D(25, "07:30"), D(25, "09:00"), 11); lose("m115_1", D(25, "07:10"), D(25, "09:00"), 194)
for id in ("td705c", "fa463"): fire(id, D(25, "07:30"), D(25, "09:00"))
for id in ("m115_t7", "m115_t"): hide(id, D(25, "09:10"))
at("m115_1", D(25, "09:00"), state="retreat"); go("m115_1", D(25, "09:01"), D(25, "10:00"), [off(MANDE, 900, 500)], h=60, state="line", moving="retreat")
# about 08:00: Force Cherry through Hemroulle to the high ground south of the 502d [M p169]
for id, p in (("ryerson_t", off(HEMROULLE, -200, 600)), ("ryerson_i", off(HEMROULLE, 0, 750))):
    drive(id, D(25, "07:20"), along(R_BERTOGNE, B, P['savy']) + along(R_HEMROULLE, P['savy'], HEMROULLE) + [p], h=290, kmh=10)
# CCB 4th Armored takes Chaumont; CCR passes Vaux-lez-Rosières, takes Remonville and halts at a crater near Cobreville [C21]
for id, p in (("b8tk", off(P['chaumont'], -100, 0)), ("b10aib", off(P['chaumont'], 200, 100)), ("b318", off(P['chaumont'], -300, -300))):
    go(id, D(25, "09:00"), D(25, "10:30"), [p], h=10, state="firing")
for id in ("fj14", "stug11"): fire(id, D(25, "10:00"), D(25, "11:30"), state="retreat")
for id in ("b8tk", "b10aib", "b318"): at(id, D(25, "11:30"), state="line")
go("fj14", D(25, "11:31"), D(25, "12:30"), [off(P['hompre'], 300, -200)], h=30, state="line", moving="retreat")
go("stug11", D(25, "11:31"), D(25, "12:10"), [off(P['hompre'], 100, -100)], h=30, state="line", moving="retreat")
CRATER = off(P['cobreville'], 300, -350)
for i, id in enumerate(("dwight", "r37tk", "r53aib", "r94fa")):
    appear(id, plus(D(25, "14:00"), 6 * i), EDGE_SSW, 340, "column")
    drive(id, plus(D(25, "14:00"), 6 * i), along(R_ASSENOIS, EDGE_SSW, off(CRATER, 0, -150 * i)), h=0, state="line", kmh=10)

# ---- Tuesday 26 December ----
# Morning: Kokott's last effort toward Hemroulle and Savy [C19; M p170] [INF: the times]
go("m115_2", D(26, "08:00"), D(26, "08:40"), [off(HEMROULLE, -900, -300)], h=70, state="firing")
fire("m115_2", D(26, "08:40"), D(26, "10:00"), state="retreat")
go("m115_2", D(26, "10:01"), D(26, "10:45"), [off(MANDE, 1100, 0)], h=60, state="line", moving="retreat")
fire("fa463", D(26, "08:30"), D(26, "09:30"))
# CCB on to Hompré [INF: the times]; the Tigers fall back before CCR [INF]
go("tigers", D(26, "12:30"), D(26, "13:30"), [off(P['lutrebois'], -800, -300)], h=90, state="column"); hide("tigers", D(26, "13:31"))
for id in ("fj14", "stug11"): hide(id, D(26, "10:00"))
for id, p in (("b8tk", off(P['hompre'], -100, -300)), ("b10aib", off(P['hompre'], 200, -400)), ("b318", off(P['hompre'], -300, -600))):
    go(id, D(26, "10:00"), D(26, "13:00"), along(R_CHAUMONT, last(id), P['hompre'])[:-1] + [p], h=10, state="line")
# CCR: the drive begins about 11:00 after its "cat nap"; the advance guard is checked at a creek near Cobreville about
# 14:00; about 15:00 it is on the high ground over Clochimont, ordered on to Sibret; at 15:20 Abrams calls Dwight forward for
# Assenois; the team moves at 16:20; at 16:34 ten volleys from thirteen batteries on Assenois; at 16:50 Boggess drives the
# first vehicle into the 326th Engineers' line; about 17:10 Abrams meets McAuliffe; Assenois is cleared by 20:00 with 428
# prisoners [M p170-172; C21]. The creek and the high ground are not placed [INF].
CREEK = on_road(along(R_ASSENOIS, P['cobreville'], P['remichampagne']), 0.35)
OVER_CLOCHIMONT = off(P['clochimont'], -600, -500)
for i, id in enumerate(("dwight", "r37tk", "r53aib")):
    go(id, plus(D(26, "11:00"), 5 * i), plus(D(26, "13:50"), 5 * i), along(R_ASSENOIS, last(id), off(CREEK, 0, -200 * i)), h=40, state="firing" if id == "dwight" else "line")
at("dwight", D(26, "14:20"), state="line")
for i, id in enumerate(("dwight", "r37tk", "r53aib")):
    go(id, plus(D(26, "14:20"), 5 * i), plus(D(26, "15:00"), 5 * i), along(R_ASSENOIS, last(id), P['remichampagne'])[:-1] + [P['remichampagne'], off(OVER_CLOCHIMONT, 150 * i, -150 * i)], h=40, state="line")
drive("r94fa", D(26, "11:00"), along(R_ASSENOIS, last("r94fa"), P['remichampagne'])[:-1] + [off(P['remichampagne'], 300, -300)], h=40, kmh=8)
fire("r94fa", D(26, "16:34"), D(26, "16:50"))
go("dwight", D(26, "16:20"), D(26, "16:50"), along(R_ASSENOIS, P['clochimont'], LINE_326), h=30, state="line", moving="charge")
fire("assenois_g", D(26, "16:34"), D(26, "20:00"), state="surrender"); lose("assenois_g", D(26, "16:40"), D(26, "20:00"), 428)
go("gr39_2", D(26, "16:40"), D(26, "17:10"), [off(ASSENOIS, 1300, 700)], h=270, state="line", moving="retreat")
go("r37tk", D(26, "16:45"), D(26, "17:20"), along(R_ASSENOIS, P['clochimont'], ASSENOIS)[:-1] + [off(ASSENOIS, -150, -200)], h=30, state="firing")
go("r53aib", D(26, "16:50"), D(26, "17:30"), along(R_ASSENOIS, P['clochimont'], ASSENOIS)[:-1] + [off(ASSENOIS, -250, 0)], h=30, state="firing")
for id in ("r37tk", "r53aib"): at(id, D(26, "20:00"), state="line")


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
    spans = sorted((s for s in spans if s[2]), key=lambda s: sec(s[0])); cur, pts = BASE[id][6], []
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
def lost(id, t): return BASE[id][6] - strength(id, t)
# The figures the note gives
assert strength("desobry_t", D(20, "18:00")) == 4, "Desobry went to Noville with fifteen tanks and came back with four"
assert lost("p506_1", D(20, "18:30")) == 212, "1/506 lost 13 officers and 199 men at Noville"
assert lost("p501_i", D(19, "16:00")) == 49, "Company I: 45 men and 4 officers at Wardin"
assert lost("eng158", D(19, "08:00")) == 30, "about 30 of the 158th at Neffe"
assert lost("kg902_i", D(19, "10:00")) == 80, "about eighty Germans at Neffe within the first hour"
assert lost("pz2_t1", D(21, "00:00")) + lost("pz2_t2", D(21, "00:00")) == 20, "between twenty and thirty known enemy tanks at Noville"
assert lost("pl901_1", D(20, "14:00")) == 50 and lost("pl901_tk", D(20, "14:00")) == 2, "Marvie, 20 Dec: 20 prisoners, 30 dead, two Mark IVs"
assert lost("g327_2", D(20, "14:00")) == 20, "2/327 at Marvie on 20 Dec: 5 killed, 15 wounded"
assert lost("gr77_1", D(21, "12:00")) == 235, "the Halt woods: 100 captured, 55 killed, 80 into the 501st"
assert lost("b8tk", D(23, "18:00")) == 11 and lost("b10aib", D(23, "18:00")) == 65, "Chaumont: eleven Shermans, about 65 of A Company"
assert strength("m115_t", D(25, "09:05")) + strength("m115_t7", D(25, "09:05")) == 0, "all 18 tanks on the 327th's front disabled"
assert lost("gr77_1", D(25, "10:00")) + lost("gr77_2", D(25, "10:00")) - 235 == 179, "A Company 502d counted 98 killed and 81 captured"
assert lost("m115_1", D(25, "10:00")) == 67 + 35 + 92, "C Company 502d's 67 dead and 35 prisoners, and 3/327's 92 prisoners"
assert lost("assenois_g", D(26, "20:00")) == 428, "Assenois: 428 prisoners"
assert strength("snafu", D(25, "12:00")) == 600, "Team SNAFU: 600 within a week"
assert set(KEYS) == set(BASE), set(KEYS) ^ set(BASE)
BUSY = {"skirmish", "firing", "charge", "retreat", "rout"}
for id in KEYS: assert state_at(id, END) not in BUSY, (id, state_at(id, END), "a last key busy holds time-lapse to the end")

# ---- assemble and check ----
for id in KEYS:
    if carried(id, "state") != "hidden" and sec(KEYS[id][-1]["t"]) < sec(END): KEYS[id].append(K(END, last(id)))
TOP = {"infantry": 6, "artillery": 6, "armor": 30}  # km/h, the fastest any leg may go; units that ride go at armor's pace
units = []
for id, side, short, name, commander, type, strength0, extra in OOB:
    ks, state, h = KEYS[id], None, None
    top = TOP["armor"] if id in MOTOR else TOP[type]
    for a, b in zip(ks, ks[1:]):
        state, h = a.get("state", state), a.get("h", h)
        assert sec(b["t"]) > sec(a["t"]), (id, a["t"], b["t"])
        if state == "hidden": continue
        moved = (a["x"], a["y"]) != (b["x"], b["y"])
        assert moved or b.get("h", h) == h or "strength" in b or sec(b["t"]) - sec(a["t"]) <= 600, (id, a["t"], b["t"], "a slow turn in place holds the time-lapse")
        assert not (moved and sec(b["t"]) - sec(a["t"]) > 3 * 3600), (id, a["t"], b["t"], "a march leg over three hours")
        kmh = math.dist((a["x"], a["y"]), (b["x"], b["y"])) / (sec(b["t"]) - sec(a["t"])) * 3.6
        assert kmh <= top, (id, a["t"], b["t"], f"{kmh:.1f} km/h")
    state = None
    for k in ks:
        state = k.get("state", state)
        assert state == "hidden" or on_land((k["x"], k["y"])), (id, k["t"], (k["x"], k["y"]), "off the map")
    units.append(dict(id=id, side=side, name=name, short=short, commander=commander, type=type, strength=strength0, keys=ks, **extra))
for f in features:
    if f.get("type") in ("smoke", "airstrike"): assert on_land(f["at"]), (f.get("name"), f["at"])
    for id in f["units"] if f.get("type") == "drop" else []:
        rally = next((k for k in KEYS[id] if sec(k["t"]) > sec(f["from"]) and state_at(id, k["t"]) != "hidden"), None)
        assert state_at(id, f["from"]) == "hidden" and rally and sec(rally["t"]) >= sec(f["until"]), (f["name"], id, "on the map before the last of its drop is down")
    if f.get("type") == "drop": assert all(on_land(p) for p in f["zone"]), (f["name"], "a drop zone corner off the map")

# ---- chapters: (time, title, text, camera centre, metres across, playback speed, when) ----
# `when` holds the clock time the sources record, GMT+1. Where Marshall and Cole differ, Marshall's time is used.
CHAPTERS = [
    (D(18, "16:00"), "Three teams", "Monday 18 December 1944, the third day of the German offensive in the Ardennes. Bastogne is the hub of a radial road net. At four the 101st Airborne Division's party under Brig. Gen. A. C. McAuliffe reaches the VIII Corps command post, and Col. W. L. Roberts of Combat Command B, 10th Armored Division, ahead of his column, reports to Middleton at the same moment. Middleton's order: 'One team will go to the southeast of Wardin, one team to the vicinity of Longvilly and one team to the vicinity of Noville ... Hold these positions at all costs.' Teams Cherry and O'Hara get through the town in daylight; sunset is at 4:37.", (-1300, -1500), 11000, 300, "4:00 PM"),
    (D(18, "19:20"), "Longvilly", "Team Cherry drives east on the Longvilly road. At 7:20 Lt. E. P. Hyduke's advance guard, four Shermans and seven light tanks, halts just short of Longvilly, whose streets are jammed with the vehicles of CCR 9th Armored. Beyond it CCR's Task Force Harper has been under fire at Allerborn since late afternoon; after dark German armour destroys two of its tank platoons and overruns it, and Lt. Col. Harper is killed. At 11:40 that night CCR begins to pull out of Longvilly, and its column freezes on the road until morning.", (7600, 4200), 5000, 300, "7:20 PM"),
    (D(18, "23:00"), "Noville", "Team Desobry left the town after dark, the last of the three. At eleven it assembles at Noville with fifteen tanks, and Maj. W. R. Desobry posts three outposts 800 yards out on the Bourcy, Houffalize and Vaux roads. Noville lies under two ridges about 800 yards off and is 'a perfect sinkhole for fog'. The 101st has driven through the night from Mourmelon in 380 trucks; by midnight its 501st Parachute Infantry has closed into Mande-Saint-Étienne, half an hour early.", (1700, 8300), 3200, 300, "11:00 PM"),
    (D(19, "02:00"), "Bayerlein at Mageret", "Tuesday. Panzer Lehr's advance guard, about fifteen tanks and four companies of the 902d, left Niederwampach at ten on a mud road, Lt. Gen. F. Bayerlein in a lead tank, and reached Benonchamps an hour after midnight, 'so dark was the night'. At two it is in Mageret, behind Team Cherry. A Belgian tells Bayerlein of 'fifty tanks and forty other armored vehicles' gone east, and he blocks the road east with three tanks, infantry and mines.", (3600, 2600), 4500, 300, "2:00 AM"),
    (D(19, "06:00"), "Ewell moves out", "The 101st's advance party reached Bastogne at three. At six the 501st Parachute Infantry passes Ewell's command post 'on the minute', heading east on the Neffe road into fog. Bayerlein's column moved off from Mageret at 5:30; its lead tank hit a mine at Cherry's roadblock east of Neffe, and at 5:50 it came on with eleven tanks on the highway and a company south of the tracks toward the château. At six Cherry's reconnaissance platoon at the Neffe road junction is hit and breaks back. At Noville the outposts have fought half-tracks of the 2d Panzer Division's reconnaissance battalion on the Bourcy road since 5:30, and three tanks in the fog on the Houffalize road.", (600, 1700), 5000, 120, "6:00 AM"),
    (D(19, "08:20"), "Contact at Neffe", "Fog limits sight to 500 yards. About 8:20, a little more than two hours after starting, the 1st Battalion 501st, Maj. R. V. Bottomly, is fired on west of Neffe. Bayerlein's tanks, which reached the Neffe station at seven and waited almost an hour, recoil, and his infantry will not move; about eighty Germans are killed or wounded at Neffe in the first hour or so. Team Cherry's headquarters holds the walled château 300 yards south of the village.", (1500, 1650), 2600, 120, "8:20 AM"),
    (D(19, "10:30"), "The fog lifts at Noville", "At 8:30 two tanks Marshall calls Tigers nosed out of the fog into Noville and were destroyed by bazookas at 20 yards. At 10:30 'the fog lifted like a curtain going up': more than 30 tanks are in sight, fourteen in a line along the ridge short of Vaux, and nine are hit straightaway. The fight dies at 11:30. At 10:50 Higgins sends Lt. Col. J. L. LaPrade's 1st Battalion 506th to Noville, and the 506th's other two battalions to reserve north of the town.", (1600, 8800), 3200, 120, "10:30 AM"),
    (D(19, "12:03"), "Bizory and Hill 510", "At 12:03 the 2d Battalion 501st, Maj. S. N. Homan, takes Bizory. Ordered on to Mageret, it meets the 26th Volksgrenadier Division's reconnaissance on the crest of Hill 510 and stops. The 3d Battalion reaches Mont, and its Company I goes on to the woods west of Wardin: 'no enemy' at 1:30. Battery B of the 907th Glider Field Artillery opened a few minutes after ten. At 11:40 O'Hara's screen met the head of a German column on the Wiltz road near Bras, two Mark IVs and a carrier.", (2200, 2300), 4600, 120, "12:03 PM"),
    (D(19, "14:00"), "The Longvilly road", "At two the German armour puts direct fire on Hyduke's position at Longvilly. He is ordered back at 2:30, but the road is blocked. The 901st Panzergrenadiers, with about twenty tank destroyers and a battalion of guns, come up from Benonchamps to Hill 490 and fire at 1,500 to 2,000 yards; the 77th Volksgrenadiers' guns join from the south-east and 2d Panzer's 88s from the road junction below Chifontaine: 'all three divisions engaged at one time', for about two hours. Hyduke loses five of his seven light tanks and his mediums, and by three most of the survivors have joined Ryerson east of Mageret.", (6300, 3500), 5200, 60, "2:00 PM"),
    (D(19, "14:15"), "Wardin", "Company I 501st is in Wardin when, at 2:15, 'seven tanks and one infantry battalion from Panzer Lehr' attack it. The company is scattered, losing 45 men and 4 officers, and Panzer Lehr's reconnaissance battalion holds the village.", (3200, 0), 2600, 60, "2:15 PM"),
    (D(19, "14:30"), "Counterattack from Noville", "The 1st Battalion 506th reached Noville at 1:30. At 2:30 it attacks with Desobry's tanks: three tanks north up the Houffalize road, four east toward the high ground west of Bourcy, three paratroop companies fanned out between. They hold the slopes until dark, then fall back into Noville, which is burning. In the evening an 88 shell kills LaPrade and wounds Desobry; Maj. R. F. Harwick and Maj. C. L. Hustead take over. At 6:20 Sink asks to pull Noville back. Middleton: 'No; if we are to hold on to Bastogne, you cannot keep falling back.'", (2000, 8600), 3200, 300, "2:30 PM"),
    (D(20, "07:30"), "Bizory holds", "Wednesday. At dusk on the 19th the 501st fell back to the high ground west of Bizory and Neffe, and Cherry led his men out of the burning château to Mont: 'We're not driven out ... we were burned out.' The 705th Tank Destroyer Battalion came in from the north-west at 8:30 that evening, and four of its B Company's TDs reached the south edge of Bizory at two. From 5:30 a battalion of the 26th Volksgrenadiers comes over the hill east of the village with a Mark IV, a Mark V and two self-propelled guns. Firing opens at 7:30, and in about two hours the attack is broken by the TDs and 'all the artillery that General McAuliffe could turn eastward'.", (2100, 3000), 3200, 120, "7:30 AM"),
    (D(20, "11:25"), "Marvie", "The 2d Battalion 327th Glider Infantry marched into Bastogne at six and went straight on to Marvie, relieving the engineers. At 11:25 four tanks and six half-tracks attack from the woods south-east. O'Hara's Shermans kill two Mark IVs and a half-track broadside at 700 yards, and the glider infantry clears the houses: 20 prisoners and 30 German dead, and the village clear by about one, for 5 killed and 15 wounded. At Foy the 3d Battalion 506th, attacked by two companies and three tanks from eight, withdrew at 10:30 to the high ground south of the village.", (700, -500), 2600, 120, "11:25 AM"),
    (D(20, "13:15"), "Out of Noville", "Radio contact with Noville is restored at one, with the order to withdraw. C Company 506th leaves at 1:15 and the vehicles at 1:25, the ammunition dump blown behind them, as the fog closes in again. A farmhouse 500 yards short of Foy hides an ambush; Shermans burn, and the infantry hooks right through the fields and takes 43 prisoners. Toms's tank destroyers enter Foy at 2:30, and at dusk the column finds its way through. Desobry's team went to Noville with fifteen tanks and comes back with four, and the 1st Battalion 506th has lost 13 officers and 199 men. 2d Panzer takes Noville in the middle of the afternoon.", (1300, 7000), 4200, 120, "1:15 PM"),
    (D(20, "19:00"), "The dam of fire", "Heavy shelling falls along the 501st, and at seven Panzer Lehr's 902d charges down the road from Neffe. 'All the guns from the eleven artillery battalions in Bastogne dropped a dam of fire across the road one or two hundred yards west of Neffe'; two Panthers and a Tiger Royal are destroyed at the last houses. Until eleven the attack between Neffe and Mont dies on the barbed-wire fences of the pasture, five or six strands thirty to fifty yards apart, under the 3d Battalion 501st and Andrews's tank destroyers. To the north seven tanks and two companies of the 77th come down the railway at Halt, into Company A 501st's ambush in the fog.", (1300, 2300), 3600, 120, "7:00 PM"),
    (D(20, "20:00"), "Sibret", "Since the afternoon Maj. Gen. H. Kokott's 39th Grenadier Regiment and his reconnaissance battalion have swung south and west round the town by Villers-la-Bonne-Eau and Hompré. 'Sibret was captured about 2000.' The 39th is checked a kilometre north of Remoifosse and in the wood a kilometre north of Assenois, the reconnaissance battalion at Chenogne. That night the Neufchâteau road is cut, isolating Bastogne; McAuliffe had driven it half an hour before. The first snow flurries fall.", (-4300, -2300), 9000, 300, "8:00 PM"),
    (D(21, "08:15"), "The Halt woods", "Thursday, heavy with fog. The 77th's men who came down the railway in the night turned D Company 506th's flank at four. A and C Companies arrive about 8:15, and 'by about 1100 ... the envelopment was complete': the 506th captures about 100 and kills 55, and drives 80 more into the 501st. Kokott has moved his command post to Bras. Panzer Lehr leaves for Morhet and the west, its 901st staying under Kokott, and 2d Panzer is strung out from Bourcy west toward Tenneville. By noon the Germans have cut all seven roads into Bastogne.", (1200, 4300), 3000, 300, "8:15 AM"),
    (D(22, "11:30"), "The surrender demand", "Friday. Since the 21st Team Pyle, 14 tanks and 200 men, has fought Kampfgruppe Kunkel into the Bois de Fragotte by Senonchamps, and by night Lt. Col. B. D. Browne held 4,000 yards there with 300 infantry and 19 tanks. At 11:30 four Germans with a white flag come up the road from Remoifosse to F Company 327th with Lüttwitz's demand for surrender. McAuliffe: 'Aw, nuts!' The reply goes back at 1:50: 'Nuts!' Two small attacks on F Company, at 3:55 and five, are beaten off by fire. That night the Luftwaffe begins bombing the town, and repeats it on the next four nights.", (-900, -1500), 3200, 300, "11:30 AM"),
    (D(23, "09:35"), "The pathfinders", "Saturday 23 December is clear and cold, visibility unlimited. At 9:35 'several large planes were circling', and pathfinders jump into the 2d Battalion 327th's area to mark a drop zone. Its place is not recorded; it is drawn here, in that battalion's area.", DZ_C, 1400, 30, "9:35 AM"),
    (D(23, "11:50"), "Supplies from the sky", "At 11:50 'men all along the front saw the planes coming in'. By 4:06, '241 planes had dropped 1,446 bundles weighing 144 tons by parachute into the mile-square drop zone', and 95 per cent are recovered. Kokott sees the drop and thinks it reinforcements. On the 24th 160 planes drop about 100 tons more.", DZ_C, 4000, 300, "11:50 AM"),
    (D(23, "13:30"), "Chaumont", "III Corps attacked at six on the 22nd, its 4th Armored Division from north of Arlon by three separate routes; by noon its CCB, Brig. Gen. H. E. Dager, was in sight of Burnon, about seven miles from Bastogne. Today, after fighter-bomber strikes, CCB's 8th Tank Battalion, 22 Shermans fit to fight, and the 10th Armored Infantry assault Chaumont at 1:30, the Shermans churning in the mud of the afternoon thaw. Ten to fifteen assault guns of the 11th Brigade counterattack, and at dusk CCB is thrown back with eleven Shermans lost and about 65 men of A Company. In the west, twelve tanks and infantry in snow suits come out of the woods south of the St Hubert road toward Flamierge.", (-4800, -8300), 3800, 300, "1:30 PM"),
    (D(23, "17:35"), "Hill 500", "At 5:25 tanks in a small plantation of firs above Martaimont shell Marvie, and at 5:35, in a light snow, tanks and snow-suited infantry of the 901st attack. After 6:40 a platoon of G Company 327th is surrounded on Hill 500 ('We're still holding on') and overwhelmed some time after seven. McAuliffe sent Team Cherry at 6:30. By eight German infantry are in the south end of Marvie, and twelve tanks come up the Arlon road at F Company, two of them breaking into the town. Near midnight the Shermans knock out the lead German tank, and twelve guns of the 81st close the gap. At dark the Flamierge roadblock was overrun, and the 327th's 3d Battalion fell back to the high ground west of Champs.", (300, -1100), 3000, 300, "5:35 PM"),
    (D(25, "03:30"), "Christmas at Champs", "Sunday brought the second airdrop and, twice, six P-47s bombing Marvie in error; Bastogne was bombed at 7:45 that evening. At ten the forward elements of the 15th Panzergrenadier Division reached the sector facing Champs and Hemroulle, and Kokott set the attack for three, Bastogne to be taken by eight. Christmas morning: the 502d's officers turned in at 1:30 after midnight Mass at Rolley; at 2:45 comes 'an intense shelling', and at 3:30 two battalions of the 77th are in Champs, 'on top of' A Company 502d. They fight house to house, and B Company holds at the edge till light.", (-4700, 5400), 2600, 120, "3:30 AM"),
    (D(25, "07:10"), "Eighteen tanks", "Eighteen tanks of Kampfgruppe Maucke formed just east of Mande-Saint-Étienne at five. At 7:10, in ground fog, the tanks and the 77th's infantry break through A and B Companies of 3/327, the 115th Panzergrenadiers with them, and split: seven north toward Rolley, the rest toward Hemroulle. C Company 502d falls back to the woods and fires into the riders, two hidden TDs of the 705th's C Company take the turning tanks in flank, and the 463d fires over open sights. 'By 0900, December 25, the action was cleared up around Rolle.' All eighteen tanks are disabled. Force Cherry comes through Hemroulle about eight. By ten Kokott knows his plan is lost.", (-4600, 4300), 3200, 120, "7:10 AM"),
    (D(26, "15:20"), "Abrams turns for Assenois", "On Christmas Day CCB took Chaumont, and the 4th Armored's CCR, Col. W. Blanchard, came up by Vaux-lez-Rosières and Remonville to halt at a crater near Cobreville. Its drive began again about eleven today; the advance guard was checked at a creek near Cobreville about two, and by three it is on the high ground over Clochimont, ordered on to Sibret, with C-47s overhead. Lt. Col. C. W. Abrams's 37th Tank Battalion has no more than twenty Shermans in operation. At 3:20 he calls Capt. W. A. Dwight forward with a light team for Assenois.", (-5300, -4700), 4200, 120, "3:20 PM"),
    (D(26, "16:50"), "The ring is broken", "Dwight's team moves at 4:20. At 4:34 Abrams calls down ten volleys from thirteen batteries on Assenois. At 4:50, ten minutes after sunset, 1st Lt. Charles P. Boggess drives the first vehicle of the 4th Armored Division into the lines of the 326th Airborne Engineer Battalion, and about 5:10 Abrams meets McAuliffe. Assenois is cleared by eight with 428 prisoners, and the convoys enter Bastogne after midnight. The 101st counted 105 officers and 1,536 men as battle casualties, CCB 10th Armored about 25 officers and 478 men, and the 4th Armored about 1,000 men in seven days. German losses for the siege were not found.", (-3400, -1800), 3600, 120, "4:50 PM"),
]
events = [dict(t=t, title=a, text=b, at=list(at_), view=v, speed=s, **({"when": w} if w else {})) for t, a, b, at_, v, s, w in CHAPTERS]
for e in events:  # without `when` the card speaks the nearest hour (app.js chapterWhen), so it must be near the frame's clock
    s = sec(e["t"]) % 86400; hh = [n % 12 or 12 for n in (int(s // 3600), int(s // 3600) + 1)]; num = re.search(r"\d+", e.get("when", ""))
    assert not num or int(num[0]) in hh, (e["t"], e["when"], "the card's hour is not the frame's")
    assert "when" in e or abs(s - math.floor(s / 3600 + 0.5) * 3600) <= 15 * 60, (e["t"], e["title"], "give it a when")
    assert e["speed"] in (1, 2, 5, 10, 20, 30, 60, 120, 300, 600, 1800, 3600, 7200), (e["title"], e["speed"], "not a speed the menu offers (sim.js SPEEDS)")
    assert on_map(e["at"], 500), (e["title"], e["at"])
assert [sec(e["t"]) for e in events] == sorted(sec(e["t"]) for e in events)

OUTCOME = {"result": "American victory: the 101st Airborne Division and CCB 10th Armored held Bastogne, and the 4th Armored Division broke the ring on 26 December", "losses": [
    ["american", "The 101st Airborne Division: 105 officers and 1,536 men battle casualties (Cole). CCB 10th Armored: about 25 officers and 478 men. The 4th Armored Division: about 1,000 men in the seven days from 22 December, eleven Shermans at Chaumont on the 23rd alone. Wikipedia gives more than 3,000 for all Americans at Bastogne, 2,000 of them in the 101st. The perimeter battalions are drawn at full strength where the note gives no figure."],
    ["german", "Not found for the siege. In the fights shown: about 80 at Neffe on the 19th; 20 to 30 tanks at Noville on the 19th and 20th; 20 prisoners and 30 dead at Marvie on the 20th; about 235 in the Halt woods on the 21st; on Christmas Day all 18 tanks on the 327th's front, 98 killed and 81 taken by A Company 502d, 67 dead and 35 taken by C Company, and 92 taken by A Company 3/327; at Assenois 428 prisoners (Cole: about 500)."]],
    "note": "Clock times are GMT+1, the clock of every source. Where Marshall and Cole differ, Marshall's time is used: the first contact at Noville (5:30, Cole 7:20), the fog lifting there (10:30, Cole 10:00), the night attack at Marvie (5:35, Cole about 6:45) and the relief (4:50, Cole 4:45)."}
SOURCES = [
    "S. L. A. Marshall, <a href='https://www.govinfo.gov/content/pkg/GOVPUB-D114-PURL-gpo153609/pdf/GOVPUB-D114-PURL-gpo153609.pdf' target='_blank'><i>Bastogne: The Story of the First Eight Days</i></a> (Infantry Journal Press, 1946; CMH facsimile), written in 1945 from interviews with the 101st, CCB 10th Armored and the 705th TD Battalion: the clock times, the fights, the quotations. Its appendix 'The Enemy Story', from Marshall's 1945 conferences with Lüttwitz, Bayerlein and Kokott: the German side and its times. Chapter 18 and the plates were not read.",
    "Hugh M. Cole, <i>The Ardennes: Battle of the Bulge</i> (US Army in World War II, 1965), chapters <a href='https://www.ibiblio.org/hyperwar/USA/USA-E-Ardennes/USA-E-Ardennes-13.html' target='_blank'>XIII</a> (CCR 9th Armored, Longvilly), <a href='https://www.ibiblio.org/hyperwar/USA/USA-E-Ardennes/USA-E-Ardennes-19.html' target='_blank'>XIX</a> (the Battle of Bastogne) and <a href='https://www.ibiblio.org/hyperwar/USA/USA-E-Ardennes/USA-E-Ardennes-21.html' target='_blank'>XXI</a> (III Corps's counterattack): the 4th Armored's advance, the tank counts and the casualties.",
    "Wikipedia, 'Siege of Bastogne' (read 7 November 2026), for its infobox figures; 'Panzer Lehr Division', '2nd Panzer Division' and historyofwar.org's Panzer Lehr page, as search summaries, for the German divisions; the 10th Armored Division Veterans' Bastogne plaque release for CCB's strength.",
    "Places: OpenStreetMap contributors (ODbL) for the villages, the seminary, the Heintz Barracks, the Château de Rolley and the old railways. Neffe château, Hill 510, Hill 500, the Halt station, Flamizoulle and O'Hara's roadblock are placed from Marshall's text, 150 to 300 m out, and labelled 'about here'. Each road is drawn straight between the places it joins. Sunrise 8:33 and sunset 4:37 for 19 December from the NOAA formulae, GMT+1.",
    "Terrain: " + T["source"] + ", 30 m, sampled to 32 m. A surface model: woods stand 15 to 25 m above the ground, and the modern town and the A26 motorway show. The brook from Mont past Neffe toward Wardin is traced from its valley floor.",
    "Placed by inference, not from the sources: every battalion's and team's strength in men (TO&E figures for the 101st and CCB, 500 to 700 for each German battalion, 300 men for each artillery battalion); Team Cherry's and Team O'Hara's tank counts; the routes between recorded places, including 2d Panzer's night march to Noville, Panzer Lehr's road to Morhet, the 77th's to the north-west, and the 101st's arrival order after the 501st; the places of the guns, of Hill 490 and of the units round the perimeter; Marshall's 'second battalion of the 76th' at Bizory drawn as the 77th's; how the tanks Marshall counts at Noville, at Marvie, at Flamierge and on the Arlon road were split into units; when losses fell between the figures the sources give; Task Force Harper's losses; and, in the drop, the pathfinders' number (60), their three aircraft, the run-in heading, the zone and the rally on it. The supply drops are not drawn: the drop feature needs men, so the 23 and 24 December bundles are a caption.",
]

battle = dict(
    id="bastogne", name="Bastogne", date="1944-12-18", dateText="18 to 26 December 1944", place="Bastogne, Province of Luxembourg, Belgium",
    origin=dict(lat=LAT0, lon=LON0), extent=2 * HALF_EXTENT, start=START, end=END, sunrise="08:33", sunset="16:37", speed=300, lapse=14400, menPerDot=20,
    water=WATER, terrainExaggeration=2, contourInterval=10, trees=dict(density=0.0003, clear=CLEAR), fields=FIELDS,
    wind=dict(x=0.5, y=0.2), view=dict(x=0, y=0, width=2 * HALF_EXTENT),
    sides=dict(american=dict(name="Americans (101st Airborne Division, McAuliffe; CCB 10th Armored, Roberts; 4th Armored Division)", color="#1f55c4", light="#4a83e6", dark="#122c66"),
               german=dict(name="Germans (XLVII Panzer Corps, Lüttwitz)", color="#b8322a", light="#de5d50", dark="#5c1712")),
    features=features, units=units, events=events, tints=TINTS, outcome=OUTCOME, sources=SOURCES,
)
json.dump(battle, open(HERE + "battle.json", "w"), indent=1, ensure_ascii=False)
print(len(units), "units (", sum(u["side"] == "american" for u in units), "American,", sum(u["side"] == "german" for u in units), "German ),", len(events), "chapters,", len(features), "features")
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
