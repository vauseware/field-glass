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
R_CHAUMONT = [EDGE_S, P['burnon'], P['chaumont'], P['hompre'], P['assenois']]                  # CCB's road north
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
    dict(type="creek", name="the brook (about here)", pts=[list(p) for p in BROOK], at=[2950, 1650], rot=-40),
    dict(type="fence", name="barbed-wire fences (about here)", pts=[[700, 1450], [1500, 1520]], at=[1100, 1300], rot=0),
    dict(type="fence", pts=[[700, 1600], [1500, 1660]]), dict(type="fence", pts=[[1000, 1380], [1000, 1700]]),
    label("BASTOGNE", P['town'], dy=650), label("Heintz Barracks", P['barracks'], dx=-450, dy=120), label("the seminary", P['seminary'], dx=420, dy=60),
    label("Hôtel Lebrun, CCB's CP (about here)", P['bastogne'], dy=-260),
    label("Mardasson", P['mardasson'], dy=160), label("Neffe château (about here)", P['chateau'], dy=-150), label("Neffe station", P['neffe_stn'], dx=350, dy=120),
    label("Hill 510 (about here)", P['hill510'], dy=170), label("Hill 500 (about here)", P['hill500'], dy=-170), label("Martaimont", P['martaimont'], dy=-200),
    label("Halt station (about here)", P['halt'], dx=550, dy=-60), label("Bois Jacques", P['bois_jacques'], dx=200, dy=350),
    label("Château de Rolley", P['rolley'], dy=170),
    label("Noville", P['noville'], dy=260), label("Vaux", P['vaux'], dy=200), label("Bourcy", P['bourcy'], dy=220), label("Cobru", P['cobru'], dx=-250, dy=120),
    label("Foy", P['foy'], dx=-220), label("Recogne", P['recogne'], dx=-320), label("Luzery", P['luzery'], dx=-300),
    label("Longchamps", P['longchamps'], dy=230), label("Monaville", P['monaville'], dy=-200), label("Bizory", P['bizory'], dx=-300, dy=80),
    label("Mageret", P['mageret'], dy=-220), label("Neffe", P['neffe'], dy=220), label("Mont", P['mont'], dy=-200),
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
    ("tigers", "german", "Tigers", "Five Tigers newly arrived near Kokott's CP, sent down the Clochimont road (Tiger sightings are often Mark IVs)", "", "armor", 5, {}),
    # 15th Panzergrenadier Division, Kampfgruppe Maucke
    ("m115_1", "german", "115 PGR", "Kampfgruppe Maucke: the 115th Panzergrenadier Regiment's spearhead, a battalion (drawn as 550)", "Col. W. Maucke", "infantry", 550, {}),
    ("m115_2", "german", "115 PGR", "Kampfgruppe Maucke: a second spearhead battalion (drawn as 550)", "Col. W. Maucke", "infantry", 550, {}),
    ("m115_t", "german", "115 Pz", "Kampfgruppe Maucke's armor: the eighteen tanks on the 327th's front", "Col. W. Maucke", "armor", 18, {}),
    # 5th Parachute Division, Col. L. Heilmann
    ("fj14", "german", "14 FJR", "A company of the 14th Parachute Regiment at Chaumont (drawn as 150)", "Col. L. Heilmann, division", "infantry", 150, {}),
    ("stug11", "german", "11 StuG Bde", "11th Assault Gun Brigade, 'ten to fifteen remodeled Mark III carriages with 75-mm. guns' (drawn as twelve)", "", "armor", 12, {}),
    ("assenois_g", "german", "Assenois", "Assenois's garrison, 'a mixed group from the 5th Parachute and 26th Volks Grenadier Divisions' (drawn as 500)", "", "infantry", 500, {}),
]
BASE = {row[0]: row for row in OOB}
assert len(BASE) == len(OOB), "a duplicate unit id"
# Units that ride: armored infantry in half-tracks, motorised guns
MOTOR = {"desobry_i", "ryerson_i", "cherry_hq", "ohara_i", "pyle_i", "harper_i", "b10aib", "r53aib", "pz2_recce"} | {r[0] for r in OOB if r[5] == "artillery"}

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
for id in BASE: appear(id, START, (0, 0), 0, state="hidden")

TINTS = []

# ---- assemble and check ----
for id in KEYS:
    if carried(id, "state") != "hidden" and sec(KEYS[id][-1]["t"]) < sec(END): KEYS[id].append(K(END, last(id)))
TOP = {"infantry": 6, "artillery": 6, "armor": 30}  # km/h, the fastest any leg may go; units that ride go at armor's pace
units = []
def state_at(id, t): return next((k["state"] for k in reversed(KEYS[id]) if sec(k["t"]) <= sec(t) and "state" in k), None)
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

events = []
battle = dict(
    id="bastogne", name="Bastogne", date="1944-12-18", dateText="18 to 26 December 1944", place="Bastogne, Province of Luxembourg, Belgium",
    origin=dict(lat=LAT0, lon=LON0), extent=2 * HALF_EXTENT, start=START, end=END, sunrise="08:33", sunset="16:37", speed=300, lapse=14400, menPerDot=20,
    water=WATER, terrainExaggeration=2, contourInterval=10, trees=dict(density=0.0003, clear=CLEAR), fields=FIELDS,
    wind=dict(x=0.5, y=0.2), view=dict(x=0, y=0, width=2 * HALF_EXTENT),
    sides=dict(american=dict(name="Americans (101st Airborne Division, McAuliffe; CCB 10th Armored, Roberts; 4th Armored Division)", color="#1f55c4", light="#4a83e6", dark="#122c66"),
               german=dict(name="Germans (XLVII Panzer Corps, Lüttwitz)", color="#b8322a", light="#de5d50", dark="#5c1712")),
    features=features, units=units, events=events, tints=TINTS,
    sources=["Terrain: " + T["source"] + ", 30 m, sampled to 32 m."],
)
json.dump(battle, open(HERE + "battle.json", "w"), indent=1, ensure_ascii=False)
print(len(units), "units (", sum(u["side"] == "american" for u in units), "American,", sum(u["side"] == "german" for u in units), "German ),", len(events), "chapters,", len(features), "features")
