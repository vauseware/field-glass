# Builds battles/arnhem/battle.json and fits terrain.json to 1944. Run from the repo root: python3 battles/arnhem/make.py
# Local metres from 51.9950N 5.8200E (x east, y north), the Bilderberg west of Oosterbeek. The 16 km square holds the five
# British zones west of Oosterbeek (DZ-X, LZ-Z, LZ-S, DZ-Y on Ginkel Heath, LZ-L), the Polish zone DZ-K by Driel, the three
# routes into Arnhem, Oosterbeek whole and Arnhem to the road bridge (6247,-2303). Elst, Nijmegen and the Pannerden ferry are
# off the map to the south and east. Anchors are OpenStreetMap points and the war diaries' 1944 grid references, converted by
# the research note's fit (good to about 100 m); every place the note gives at 200 m or worse is labelled "about here".
# Clock times are the British clock, GMT+1, as the division's diaries wrote them.
import json, math, re, datetime as dt
HERE = "battles/arnhem/"
LAT0, LON0 = 51.9950, 5.8200
KX, KY = 111320 * math.cos(math.radians(LAT0)), 111320  # tools/fetch_terrain.py's metres per degree
def M(lat, lon): return (round((lon - LON0) * KX), round((lat - LAT0) * KY))
def G(ref):  # a 1944 grid reference on sheet "Ginkel 388" (six figures to 100 m, four to 1 km), by the note's affine fit
    n = len(ref) // 2; s = 10 ** (n - 2)
    E, N = int(ref[:n]) / s + 0.5 / s, int(ref[n:]) / s + 0.5 / s
    return M(51.233101 + 0.0005208 * E + 0.0091530 * N, 4.808639 + 0.0147118 * E + 0.0000552 * N)
HALF_EXTENT = 8000

# ---- terrain: the Rhine flattened inside its channel ----
# Copernicus GLO-30 reads the river as flat water, 6.0 m west of Oosterbeek and 6.5 to 7.0 m east of it, and the
# Oosterbeek Laag flats at 7.5 m and the Driel polder at 9.2 m. The channel is the run of those flat cells in each
# column of the DEM, followed from the Driel ferry east and west; inside it the ground goes to 5 m under a water level
# of 6. Elsewhere the ground is held above 6.1 m, so the flooded clay pits on the banks stay land as they were in 1944
# and only the river is drawn. Each step is idempotent, so the script can be rerun.
WATER = 6.0
T = json.load(open(HERE + "terrain.json"))
COLS, SP = T["cols"], T["spacing"]; HALF = COLS * SP / 2
assert HALF == HALF_EXTENT, "terrain.json is not the battle's extent"
def cell(x, y): return int((HALF - y) / SP) * COLS + int((x + HALF) / SP)
FERRY_MID = M(51.97309, 5.82397)  # between the ferry's two landings
low, st = set(), [cell(*FERRY_MID)]
while st:  # the flat water connected to the ferry crossing
    i = st.pop()
    if i in low or T["z"][i] > 7.05: continue
    low.add(i); r, c = divmod(i, COLS)
    st += [rr * COLS + cc for rr, cc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)) if 0 <= rr < COLS and 0 <= cc < COLS]
CENTRE, channel = {}, set()
def follow(cols):  # in each column the run of low cells nearest the last one's middle, at most 8 cells (256 m) wide
    row = None
    for c in cols:
        rows = sorted(i // COLS for i in low if i % COLS == c)
        runs, run = [], []
        for r in rows:
            if run and r != run[-1] + 1: runs.append(run); run = []
            run.append(r)
        if run: runs.append(run)
        if not runs: continue
        if row is None: row = (runs[0][0] + runs[0][-1]) / 2
        best = min(runs, key=lambda u: abs((u[0] + u[-1]) / 2 - row))
        if abs((best[0] + best[-1]) / 2 - row) > 10: continue  # a bridge deck or a gap: keep the last middle
        if len(best) > 8: m = round(row); best = [r for r in best if abs(r - m) <= 4]
        row = (best[0] + best[-1]) / 2; CENTRE[c] = row; channel.update(r * COLS + c for r in best)
c0 = cell(*FERRY_MID) % COLS
follow(range(c0, COLS)); follow(range(c0, -1, -1))
Z = [5.0 if i in channel else round(max(v, 6.1), 2) for i, v in enumerate(T["z"])]
if Z != T["z"]: T["z"] = Z; json.dump(T, open(HERE + "terrain.json", "w"), separators=(",", ":"))
def z(x, y):
    c, r = int((x + HALF) / SP), int((HALF - y) / SP)
    return T["z"][r * COLS + c] if 0 <= c < COLS and 0 <= r < COLS else None
def on_land(p): return z(*p) is not None and z(*p) > WATER
RIVER = [(round(c * SP - HALF + SP / 2), round(HALF - (CENTRE[c] + 0.5) * SP)) for c in sorted(CENTRE)][::8]  # the channel's middle, every 256 m
def river_y(x): return min(RIVER, key=lambda p: abs(p[0] - x))[1]

# ---- places (WGS84) ----
PLACES = {  # OpenStreetMap, from the research note's anchor table
    'bridge': (51.97431, 5.91114), 'ramp': (51.97640, 5.91100), 'school': (51.97695, 5.91456), 'walburgis': (51.97903, 5.91370),
    'eusebius': (51.97904, 5.91020), 'pontoon': (51.97848, 5.90397), 'centraal': (51.98507, 5.89998), 'museum': (51.98549, 5.89220),
    'onderlangs': (51.98310, 5.89567), 'boterdijk': (51.98160, 5.89815), 'pavilion': (51.98330, 5.89450), 'hospital': (51.98500, 5.88603),
    'prison': (51.98536, 5.87834), 'mariendaal': (51.98535, 5.86313), 'railbridge': (51.97236, 5.85588), 'laag': (51.97771, 5.85003),
    'church': (51.97797, 5.83781), 'flats': (51.97720, 5.83317), 'hartenstein': (51.98769, 5.83263), 'schoonoord': (51.98779, 5.83809),
    'tafelberg': (51.98451, 5.83710), 'dreyeroord': (51.99450, 5.83623), 'hoog': (51.99478, 5.84049), 'dw_n': (52.00633, 5.84550),
    'dw_s': (51.99896, 5.84415), 'johannahoeve': (51.99863, 5.83888), 'koepel': (51.99558, 5.86132), 'h_wolfheze': (51.99406, 5.80292),
    'wolfheze': (52.00567, 5.79239), 'crossing': (52.00179, 5.80391), 'bilderberg': (51.99500, 5.82153), 'westerbouwing': (51.97553, 5.82296),
    'ferry_n': (51.97359, 5.82352), 'ferry_s': (51.97259, 5.82442), 'heveadorp': (51.97576, 5.80918), 'driel': (51.95916, 5.81622),
    'heelsum': (51.98320, 5.75538), 'renkum': (51.97511, 5.73357), 'brickworks': (51.96900, 5.73600), 'jonkershoeve': (51.99367, 5.76141),
    'dzx': (51.99800, 5.76000), 'lzz': (51.99918, 5.78183), 'reijerscamp': (52.01507, 5.78067), 'monument': (52.03693, 5.73406),
    'heath_y': (52.03128, 5.72078), 'arnhem': (51.98426, 5.91086), 'oosterbeek': (51.98845, 5.84205), 'doorwerth': (51.97887, 5.80484),
    'elden': (51.95820, 5.88330), 'deelen': (52.06130, 5.88700),
}
P = {k: M(*v) for k, v in PLACES.items()}
# The note puts the north ramp 150 m north of the span's centre; the surface model's water reaches that point, so the
# ramp is drawn 100 m further north, on the DEM's bank.
def bank(p, dy):  # the first land from p, stepping dy metres north or south
    while not on_land(p): p = (p[0], p[1] + dy)
    return (p[0], p[1] + dy)
P['ferry_s'] = bank(P['ferry_s'], -16)  # the note's south landing is the ferry way's centre, in midstream: drawn on the DEM's south bank
for k in ('rv_y', '611838'), ('ginkel', '631833'), ('lz_s', '662815'), ('lz_z_hq', '658799'), ('koude', '6878'), ('hemelsche', '689776'), ('laundry', '697775'), ('outpost', '705774'):
    P[k[0]] = G(k[1])
LZL = (1100, 950)  # LZ-L, between Johannahoeve and the Amsterdamseweg, about 300 m [DERIVED in the note]
DZK = [G('686759'), G('698754'), G('699738'), G('682737')]  # Annexure G's corners

# ---- roads and the railway: OpenStreetMap ways' centres, in order along each road ----
def ll(*pts): return [M(*p) for p in pts]
UTRECHTSEWEG = ll((51.97312, 5.7347), (51.97414, 5.73961), (51.97623, 5.74498), (51.97846, 5.75072), (51.98048, 5.75591), (51.9819, 5.76004), (51.98092, 5.76711),
                  (51.98157, 5.77162), (51.98238, 5.77556), (51.98359, 5.78062), (51.98473, 5.7843), (51.98532, 5.79053), (51.98772, 5.80664), (51.9879, 5.813),
                  (51.98708, 5.82041), (51.98737, 5.82674), (51.98807, 5.83061), (51.98808, 5.83554), (51.98779, 5.83809), (51.98753, 5.84153), (51.98664, 5.84851),
                  (51.98564, 5.85695), (51.98514, 5.86378), (51.98359, 5.8696), (51.9834, 5.87831), (51.98423, 5.88489), (51.98516, 5.88945), (51.98506, 5.89267))
# West of Wolfheze the Amsterdamseweg is drawn straight past the Ginkel Heath monument toward Ede [DERIVED].
AMSTERDAMSEWEG = ll((52.04400, 5.70350), (52.03693, 5.73406), (52.02159, 5.803), (52.01738, 5.81113), (52.01429, 5.82088), (52.01047, 5.83342), (52.00689, 5.84473),
                    (52.00445, 5.85258), (52.0014, 5.85986), (51.9976, 5.86809), (51.99517, 5.87451), (51.9926, 5.88025), (51.99027, 5.88839), (51.98796, 5.89465),
                    (51.98585, 5.89937), (51.98515, 5.90482))
# 'Lion': Heveadorp, the Westerbouwing, the Benedendorpsweg past the church, Klingelbeekseweg, the Onderlangs and the Rijnkade to the ramp.
RIVER_ROAD = [P['heveadorp']] + ll((51.97682, 5.82063), (51.97679, 5.8236), (51.97729, 5.82613), (51.97833, 5.83201), (51.97849, 5.83692), (51.97823, 5.83866),
                (51.97862, 5.84282), (51.97923, 5.84655), (51.97943, 5.85375), (51.97928, 5.85997), (51.97987, 5.86412), (51.98116, 5.86512), (51.98081, 5.8693),
                (51.98159, 5.87362), (51.98277, 5.87691), (51.98374, 5.88281), (51.98408, 5.88615), (51.98427, 5.89058), (51.9831, 5.89568), (51.98199, 5.89868),
                (51.97938, 5.90247), (51.97847, 5.90396), (51.97682, 5.90802)) + [P['ramp']]
WOLFHEZERWEG = ll((52.01881, 5.807), (52.01661, 5.803), (52.01351, 5.8008), (52.00824, 5.7946), (52.00723, 5.79343), (52.00547, 5.79177), (52.00264, 5.79422),
                  (51.99958, 5.79698), (51.99665, 5.79991), (51.99449, 5.80233), (51.99341, 5.80398), (51.99049, 5.80896), (51.9879, 5.813))
DREIJENSEWEG = ll((52.00653, 5.84563), (52.00601, 5.84536), (52.00261, 5.84473), (51.99896, 5.84415))
STATIONSWEG = [P['hoog']] + ll((51.99346, 5.84044), (51.99189, 5.84013), (51.99084, 5.83954), (51.98969, 5.83888), (51.98881, 5.83843)) + [P['schoonoord']]
PIETERSBERGSEWEG = [P['schoonoord']] + ll((51.98634, 5.83745), (51.98429, 5.83682), (51.98306, 5.8366), (51.9825, 5.83618), (51.98219, 5.83462))
# South of the Nijmeegseweg's first stretch the road is drawn straight through Elden toward Elst [DERIVED].
NIJMEGEN_RD = [P['bridge'], M(51.97144, 5.90832), P['elden'], M(51.92370, 5.85900)]
# The railway's line between its stations and bridges; west of Wolfheze it is drawn straight toward Ede [DERIVED].
RAIL = [M(52.02170, 5.70328), P['wolfheze'], P['crossing'], P['hoog'], M(51.98754, 5.86372), P['centraal'], M(51.98557, 5.9107), M(51.98487, 5.92086), M(51.98222, 5.93156)]
RAIL_NIJMEGEN = ll((51.98482, 5.86575), (51.97924, 5.86021), (51.97778, 5.85925)) + [P['railbridge'], M(51.9546, 5.85191), M(51.92370, 5.84700)]
DRIEL_RD = [P['ferry_s'], M(51.96600, 5.82150), P['driel']] + ll((51.95592, 5.81695), (51.95353, 5.81758)) + [M(51.92370, 5.82000)]

# ---- woods, towns and fields ----
def quad(c, w, h, rot=0):
    r = math.radians(rot); u, v = (math.cos(r), math.sin(r)), (-math.sin(r), math.cos(r))
    return [(round(c[0] + a * w * u[0] + b * h * v[0]), round(c[1] + a * w * u[1] + b * h * v[1])) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
ZONES = {  # centres from the note, outlines derived: DZ-X 400 m, LZ-Z and LZ-L 300 m
    'DZ-X': quad(P['dzx'], 700, 450, 10), 'LZ-Z': quad(P['lzz'], 650, 400, 10), 'LZ-S': quad((P['lz_s'][0] + 150, P['lz_s'][1] + 100), 700, 500, 15),
    'DZ-Y': quad(P['heath_y'], 1100, 550, 20), 'LZ-L': quad(LZL, 450, 350, 25), 'DZ-K': DZK,
}
POLDER = [(-HALF_EXTENT, -HALF_EXTENT)] + [(x, y + 150) for x, y in RIVER] + [(HALF_EXTENT, -HALF_EXTENT)]  # the Betuwe south of the river and the meadows on its north bank
TOWNS = {
    'Arnhem': [(3500, -500), (4500, 300), (7900, 300), (7900, -2600), (6300, -2250), (5300, -1550), (4200, -1350), (3400, -1300)],
    'Oosterbeek': [(500, -300), (1500, 0), (2500, -600), (2900, -1300), (2300, -1800), (1300, -1950), (400, -1900), (200, -900)],
    'Wolfheze': quad(M(52.00350, 5.79200), 350, 300), 'Heelsum': quad(P['heelsum'], 600, 350), 'Renkum': quad(M(51.97700, 5.73600), 700, 450),
    'Doorwerth': quad(P['doorwerth'], 500, 300), 'Heveadorp': quad(P['heveadorp'], 300, 200),
}
FIELDS = list(ZONES.values()) + [POLDER, quad((1400, 600), 500, 300, 25), quad((-3400, 1400), 600, 350, 15)]

# ---- the clock: 17 to 26 September 1944, British clock (GMT+1) ----
UTC = dt.timezone.utc
T0 = dt.datetime(1944, 9, 17, tzinfo=UTC)
def D(day, hm): return f"1944-09-{day:02d} {hm}"
def sec(t): return (dt.datetime.strptime(t, "%Y-%m-%d %H:%M:%S" if t.count(":") == 2 else "%Y-%m-%d %H:%M").replace(tzinfo=UTC) - T0).total_seconds()
def fmt(s): s = round(s); return (T0 + dt.timedelta(seconds=s)).strftime("%Y-%m-%d %H:%M" + (":%S" if s % 60 else ""))
def plus(t, mins): return fmt(sec(t) + mins * 60)
START, END = D(17, "12:30"), D(26, "06:00")

# ---- features ----
def label(name, p, dy=0, dx=0, **kw): return dict(name=name, at=[p[0] + dx, p[1] + dy], **kw)
def rd(pts, name="", at=None, rot=0, **kw): return dict(type="road", name=name, pts=pts, **({"at": at, "rot": rot} if at else {}), **kw)
PERIMETER = [P['dreyeroord'], (1300, -150), *STATIONSWEG[2:], P['tafelberg'], P['church'], P['flats'], (500, -2050), P['hemelsche'], (-300, -1900),
             P['koude'], (-150, -900), P['bilderberg'], (700, -200), P['dreyeroord']]  # 21 September, from the companies' positions [DERIVED in the note]
KRAFFT = [P['crossing'], P['h_wolfheze'], (-600, -700)]
SPINDLER = [P['dw_n'], P['dw_s'], P['hoog'], (2900, -400), (3400, -900), P['prison'], (4300, -1500)]
features = [
    rd(UTRECHTSEWEG, "Utrechtseweg", [-3000, -1250], -12), rd(AMSTERDAMSEWEG, "Amsterdamseweg", [-1600, 3230], 20), rd(RIVER_ROAD, "the river road", [2900, -1640], 10),
    rd(WOLFHEZERWEG, "Wolfhezerweg", [-1450, 1900], -60), rd(DREIJENSEWEG, "Dreijenseweg", [1980, 900], -85), rd(STATIONSWEG, "Stationsweg"), rd(PIETERSBERGSEWEG),
    rd(NIJMEGEN_RD, "road to Nijmegen", [4500, -4500], 55), rd(DRIEL_RD, "road to Driel", [-180, -3200], 80),
    rd(RAIL, "railway to Utrecht", [-5000, 2300], 17), rd(RAIL_NIJMEGEN, "railway to Nijmegen", [2700, -3500], 80),
    dict(type="trench", name="Krafft's blocking line", pts=KRAFFT, **{"from": D(17, "15:00"), "until": D(17, "21:30")}),
    dict(type="trench", name="Spindler's blocking line", pts=SPINDLER, **{"from": D(18, "06:00"), "until": D(20, "06:00")}),
    dict(type="works", name="the perimeter, 21 September", pts=PERIMETER, **{"from": D(20, "15:00")}),
    label("ARNHEM", P['arnhem'], dy=500), label("Oosterbeek", P['oosterbeek'], dy=250), label("Wolfheze", P['wolfheze'], dx=-350, dy=150),
    label("Heelsum", P['heelsum'], dy=-200), label("Renkum", P['renkum'], dy=250), label("Doorwerth", P['doorwerth'], dy=-150), label("Heveadorp", P['heveadorp'], dy=150),
    label("Driel", P['driel'], dx=-400), label("Elden", P['elden'], dy=150), label("Deelen airfield", P['deelen'], dy=-650),
    label("road bridge", P['bridge'], dx=420, dy=60), label("Van Limburg Stirum school", P['school'], dx=450, dy=60), label("St Elisabeth hospital", P['hospital'], dy=-120),
    label("Municipal Museum", P['museum'], dy=110), label("Rhine Pavilion (about here)", P['pavilion'], dx=-120, dy=-140), label("Den Brink (about here)", G('723782'), dy=120),
    label("Koepel prison", P['prison'], dy=-110), label("Hartenstein", P['hartenstein'], dx=-250, dy=60), label("Schoonoord crossroads", P['schoonoord'], dx=380, dy=60),
    label("Tafelberg", P['tafelberg'], dx=230), label("Oosterbeek church", P['church'], dx=60, dy=-110), label("the White House (Dreyeroord)", P['dreyeroord'], dx=-200, dy=110),
    label("Hotel Wolfheze", P['h_wolfheze'], dx=-350), label("Johannahoeve", P['johannahoeve'], dx=320, dy=-60), label("Lichtenbeek (about here)", P['koepel'], dy=150),
    label("Westerbouwing", P['westerbouwing'], dx=-350, dy=80), label("Driel ferry", P['ferry_n'], dx=-300, dy=-40), label("railway bridge", P['railbridge'], dx=380, dy=40),
    label("pontoon bridge (about here)", P['pontoon'], dx=-350, dy=-80), label("Arnhem station", P['centraal'], dy=120), label("Oosterbeek Hoog station", P['hoog'], dx=420, dy=40),
    label("Jonkershoeve (about here)", P['jonkershoeve'], dy=-150), label("Reijerscamp", P['reijerscamp'], dy=-150), label("Ginkel", P['ginkel'], dy=-150),
    label("Bilderberg", P['bilderberg'], dx=-250, dy=-80), label("Koude Herberg (about here)", P['koude'], dx=-400), label("Mariëndaal", P['mariendaal'], dy=-130),
    label("Renkum brickworks (about here)", P['brickworks'], dx=150, dy=200),
    label("DZ-X (about here)", P['dzx'], dy=520, until=D(18, "23:59")), label("LZ-Z (about here)", P['lzz'], dy=-470, until=D(18, "23:59")),
    label("LZ-S", (P['lz_s'][0] + 150, P['lz_s'][1] + 650), until=D(18, "23:59")), label("DZ-Y, Ginkel Heath", P['heath_y'], dy=-650, until=D(18, "23:59")),
    label("LZ-L (about here)", LZL, dy=420, until=D(19, "23:59")), label("DZ-K", (G('690748')[0] + 300, G('690748')[1]), until=D(21, "23:59")),
]
for f in features:
    if "at" in f: assert on_land(f["at"]) and max(map(abs, f["at"])) < HALF_EXTENT - 100, (f.get("name"), f["at"], "a label off the map or in the river")
for k in ('ramp', 'ferry_n', 'ferry_s', 'flats', 'westerbouwing', 'church', 'pontoon', 'laag'):
    assert on_land(P[k]), (k, P[k], "an anchor in the river")

# ---- order of battle: (id, side, short, name, commander, type, strength, extra) ----
# British "went in" strengths from the Pegasus Archive's order of battle, the Poles' from its Polish order, the Germans'
# as the force each kampfgruppe brought. Units the sources give no strength for are drawn at a size named in the unit.
LOOSE = dict(loose=True)
OOB = [
    # 1st Airborne Division
    ("pf_z", "british", "21 Ind Coy", "21st Independent Parachute Company, the pathfinders: 186 men from twelve Stirlings at 12:40, a platoon to each zone; this platoon marked LZ-Z", "Maj. B. Wilson", "infantry", 62, LOOSE),
    ("pf_s", "british", "21 Ind Coy", "21st Independent Parachute Company: the platoon that marked LZ-S", "Maj. B. Wilson", "infantry", 62, LOOSE),
    ("pf_x", "british", "21 Ind Coy", "21st Independent Parachute Company: the platoon that marked DZ-X", "Maj. B. Wilson", "infantry", 62, LOOSE),
    ("divhq", "british", "Div HQ", "1st Airborne Division headquarters and defence platoon, with the signals, provost, REME and RAOC", "Maj. Gen. R. E. Urquhart", "infantry", 140, LOOSE),
    ("recce", "british", "Recce Sqn", "1st Airborne Reconnaissance Squadron, jeeps by glider to LZ-Z and men by parachute to DZ-X", "Maj. F. Gough", "infantry", 180, LOOSE),
    ("p1", "british", "1 Para", "1st Parachute Battalion, the northern route along the Amsterdamseweg ('Leopard')", "Lt. Col. D. Dobie (captured 19 Sep)", "infantry", 548, LOOSE),
    ("p2", "british", "2 Para", "A and HQ Companies, 2nd Parachute Battalion, with 1st Parachute Brigade HQ, 1st Parachute Squadron RE, RASC, a detachment of 1st Airlanding Anti-Tank Battery, 8 of the Reconnaissance Squadron and 12 glider pilots: the force at the bridge", "Lt. Col. J. Frost (wounded 20 Sep), then Maj. F. Gough", "infantry", 625, LOOSE),
    ("p2b", "british", "B/2 Para", "B Company, 2nd Parachute Battalion (the company's strength is not in the sources read; drawn as 120)", "", "infantry", 120, LOOSE),
    ("p2c", "british", "C/2 Para", "C Company, 2nd Parachute Battalion, sent for the railway bridge (drawn as 120)", "", "infantry", 120, LOOSE),
    ("p3", "british", "3 Para", "3rd Parachute Battalion, the middle route along the Utrechtseweg ('Tiger')", "Lt. Col. J. Fitch (killed 19 Sep)", "infantry", 543, LOOSE),
    ("p3c", "british", "C/3 Para", "Maj. Lewis's party of C Company, 3rd Parachute Battalion, sent along the railway: the 45 who reached the bridge", "Maj. P. Lewis", "infantry", 45, LOOSE),
    ("border_hq", "british", "1 Border HQ", "1st Battalion, The Border Regiment: headquarters and support (788 went in; the four rifle companies are drawn as 150 each)", "Maj. S. Cousens, for Lt. Col. T. Haddon", "infantry", 188, {}),
    ("border_a", "british", "A/1 Border", "A Company, 1st Border", "", "infantry", 150, {}),
    ("border_b", "british", "B/1 Border", "B Company, 1st Border", "", "infantry", 150, {}),
    ("border_c", "british", "C/1 Border", "C Company, 1st Border", "", "infantry", 150, {}),
    ("border_d", "british", "D/1 Border", "D Company, 1st Border", "", "infantry", 150, {}),
    ("st1", "british", "2 S Staffords", "2nd South Staffords, the half that came on the first lift", "Lt. Col. D. McCardie (captured 19 Sep), then Maj. R. Cain", "infantry", 380, {}),
    ("st2", "british", "2 S Staffords", "2nd South Staffords, the half that came on the second lift", "Lt. Col. D. McCardie", "infantry", 380, {}),
    ("kosb", "british", "7 KOSB", "7th King's Own Scottish Borderers, which held DZ-Y for the second lift and LZ-L for the third", "Lt. Col. R. Payton-Reid", "infantry", 615, {}),
    ("kosb_d", "british", "D/7 KOSB", "D Company, 7th KOSB, cut off at Ginkel on 18 September (drawn as 150 of the battalion's 765)", "", "infantry", 150, {}),
    ("gp1", "british", "Glider pilots", "Glider Pilot Regiment, the pilots of the first lift (1,262 pilots in all, drawn as two bodies of 600)", "Lt. Col. I. Murray", "infantry", 600, LOOSE),
    ("gp2", "british", "Glider pilots", "Glider Pilot Regiment, the pilots of the second lift", "", "infantry", 600, LOOSE),
    ("bty1", "british", "1 Bty RA", "1 Battery, 1st Airlanding Light Regiment RA, 75 mm pack howitzers", "Lt. Col. W. Thompson (wounded 21 Sep), regiment", "artillery", 124, dict(guns=8)),
    ("bty2", "british", "2 Bty RA", "2 Battery and RHQ, 1st Airlanding Light Regiment RA, on the second lift", "Lt. Col. W. Thompson", "artillery", 124, dict(guns=7)),
    ("bty3", "british", "3 Bty RA", "3 Battery, 1st Airlanding Light Regiment RA", "Lt. Col. W. Thompson", "artillery", 124, dict(guns=6)),
    ("p156", "british", "156 Para", "156th Parachute Battalion, 4th Parachute Brigade", "Lt. Col. Sir R. des Voeux (killed 20 Sep)", "infantry", 621, LOOSE),
    ("p10", "british", "10 Para", "10th Parachute Battalion, 4th Parachute Brigade", "Lt. Col. K. Smyth (mortally wounded 21 Sep)", "infantry", 582, LOOSE),
    ("p11", "british", "11 Para", "11th Parachute Battalion, 4th Parachute Brigade, sent on to Arnhem", "Lt. Col. G. Lea (captured 19 Sep), then Maj. R. Lonsdale", "infantry", 571, LOOSE),
    # 1st Polish Independent Parachute Brigade Group
    ("pol_gl", "polish", "Polish A/Tk", "The Polish glider element: 93 men with ten 6-pounders on LZ-L; nine killed and three guns serviceable", "Capt. J. Wardzala", "artillery", 93, dict(guns=3)),
    ("pol_hq", "polish", "Polish HQ", "Polish Brigade HQ, engineers, signals and medical, dropped at Driel (the drop's 1,000 are drawn as this and two battalions)", "Maj. Gen. S. Sosabowski", "infantry", 350, LOOSE),
    ("pol2", "polish", "2 Polish Bn", "2nd Battalion, 1st Polish Independent Parachute Brigade", "Maj. W. Ploszewski", "infantry", 351, LOOSE),
    ("pol3", "polish", "3 Polish Bn", "3rd Battalion, 1st Polish Independent Parachute Brigade, the part that dropped at Driel (drawn as 300)", "Capt. W. Sobocinski", "infantry", 300, LOOSE),
    ("pol1", "polish", "1 Polish Bn", "1st Battalion and the rest of the 3rd: 551 men dropped near Grave on 23 September", "Maj. M. Tonn", "infantry", 551, LOOSE),
    ("pol_n", "polish", "Poles", "The Poles who crossed the Rhine into the perimeter: 52 rowed over on the night of 22 September, 35 reaching it; 153 more on the 24th", "", "infantry", 188, LOOSE),
    # XXX Corps
    ("hcr", "british", "Household Cavalry", "2nd Household Cavalry Regiment's armoured cars, the first of XXX Corps to reach Driel (drawn as two cars)", "", "armor", 2, {}),
    ("rdg", "british", "4/7 RDG", "4th/7th Royal Dragoon Guards, 43rd (Wessex) Division's tanks (drawn as ten)", "", "armor", 10, {}),
    ("dcli", "british", "5 DCLI", "5th Duke of Cornwall's Light Infantry, 130th Brigade, 43rd (Wessex) Division (drawn as 400)", "", "infantry", 400, {}),
    ("dorsets", "british", "4 Dorsets", "4th Dorsets, 130th Brigade, which crossed on the night of 24 September", "Lt. Col. G. Tilly", "infantry", 315, {}),
    # Germans
    ("krafft", "german", "Krafft", "SS Panzergrenadier Ausbildungs- und Ersatz-Bataillon 16 (Bataillon Krafft), two companies", "SS-Sturmbannführer S. Krafft", "infantry", 435, {}),
    ("weber", "german", "KG Weber", "Kampfgruppe Weber, Luftwaffe signals troops from Deelen with armoured vehicles (strength not recorded; drawn as 200)", "", "infantry", 200, {}),
    ("sp_n", "german", "Spindler", "Sperrverband Spindler, its northern half on the Dreijenseweg: the 9th SS artillery regiment as infantry (1,400 in all, with Allworden, Harder, Bruhn and Möller; which kampfgruppe held which stretch is not recorded)", "SS-Sturmbannführer L. Spindler", "infantry", 700, {}),
    ("sp_t", "german", "Spindler", "Sperrverband Spindler, its southern half in the streets west of the hospital, the Den Brink and the river road", "SS-Sturmbannführer L. Spindler", "infantry", 700, {}),
    ("grabner", "german", "Gräbner", "SS Aufklärungs-Abteilung 9, armoured cars and half-tracks: 400 men, 22 vehicles in the charge", "SS-Hauptsturmführer V. Gräbner (killed 18 Sep)", "armor", 22, {}),
    ("brinkmann", "german", "Brinkmann", "Kampfgruppe Brinkmann, the 10th SS reconnaissance battalion under the 9th SS (strength not recorded; drawn as 300)", "SS-Sturmbannführer H. Brinkmann", "infantry", 300, {}),
    ("knaust", "german", "Knaust", "Kampfgruppe Knaust, Panzergrenadier Ersatz-Bataillon Bocholt (200 to 300 men)", "Maj. H. Knaust", "infantry", 250, {}),
    ("knaust_pz", "german", "Knaust tanks", "Kampfgruppe Knaust's eight Mark III and IV training tanks", "Maj. H. Knaust", "armor", 8, {}),
    ("tigers", "german", "Tigers", "schwere Panzer-Kompanie Hummel: Tigers, three of them drawn", "", "armor", 3, {}),
    ("helle", "german", "Helle", "SS Wach-Bataillon 3, Kampfgruppe von Tettau", "Helle", "infantry", 600, {}),
    ("flieger", "german", "Fliegerhorst", "Fliegerhorst-Bataillon from Soesterberg, Kampfgruppe von Tettau (600)", "", "infantry", 600, {}),
    ("lippert1", "german", "SS NCO School", "SS NCO School Arnhem, a battalion (the school's 3,000 are drawn as three of 1,000), Kampfgruppe von Tettau", "Lippert", "infantry", 1000, {}),
    ("lippert2", "german", "SS NCO School", "SS NCO School Arnhem, a battalion", "Lippert", "infantry", 1000, {}),
    ("lippert3", "german", "SS NCO School", "SS NCO School Arnhem, a battalion", "Lippert", "infantry", 1000, {}),
    ("schiff", "german", "Schiffstamm 10", "Schiffstammabteilung 10, naval troops as infantry, Kampfgruppe von Tettau", "", "infantry", 600, {}),
    ("worrowski", "german", "Worrowski", "Bataillon Worrowski of the Hermann Göring Schule Regiment (strength not recorded; drawn as 600)", "Worrowski", "infantry", 600, {}),
    ("pz224", "german", "Pz Abt 224", "Panzer-Abteilung 224, captured French tanks (17 in all; four drawn)", "", "armor", 4, {}),
    ("ss10", "german", "10th SS", "A column of the 10th SS Panzer Division Frundsberg with Brinkmann's half-tracks, over the bridge for Elst (its make-up is not recorded; drawn as twelve vehicles)", "SS-Brigadeführer H. Harmel", "armor", 12, {}),
    ("driel_kg", "german", "Germans", "German infantry with armoured vehicles against Driel, about a battalion (unit not recorded; drawn as 600)", "", "infantry", 600, {}),
]
BASE = {row[0]: row for row in OOB}

# ---- movement ----
KEYS = {}
def K(t, p, **kw): return dict(t=t, x=round(p[0]), y=round(p[1]), **kw)
def appear(id, t, p, h, state="line", **kw): KEYS.setdefault(id, []).append(K(t, p, h=h, state=state, **kw))
for id in BASE: appear(id, START, (0, 0), 0, state="hidden")

# ---- assemble and check ----
TOP = {"infantry": 6, "artillery": 6, "armor": 30}  # km/h, the fastest any leg may go
units = []
for id, side, short, name, commander, type, strength, extra in OOB:
    ks = KEYS[id]
    for a, b in zip(ks, ks[1:]): assert sec(b["t"]) > sec(a["t"]), (id, a["t"], b["t"])
    units.append(dict(id=id, side=side, name=name, short=short, commander=commander, type=type, strength=strength, keys=ks, **extra))

battle = dict(
    id="arnhem", name="Arnhem", date="1944-09-17", dateText="17 to 26 September 1944", place="Arnhem and Oosterbeek, Gelderland, the Netherlands",
    origin=dict(lat=LAT0, lon=LON0), extent=2 * HALF_EXTENT, start=START, end=END, sunrise="06:14", sunset="18:47", speed=300, lapse=14400, menPerDot=10,
    water=WATER, terrainExaggeration=1.5, contourInterval=5, trees=dict(density=0.00035, clear=list(TOWNS.values())), fields=FIELDS,
    wind=dict(x=0.5, y=0.2), view=dict(x=0, y=0, width=2 * HALF_EXTENT),
    sides=dict(british=dict(name="British (1st Airborne Division, Urquhart; XXX Corps)", color="#3a5f9e", light="#7d9bd0", dark="#1d3561"),
               polish=dict(name="Poles (1st Independent Parachute Brigade, Sosabowski)", color="#5d7f86", light="#97b4ba", dark="#2e4246"),
               german=dict(name="Germans (II SS Panzer Corps, Bittrich; Kampfgruppe von Tettau)", color="#b8322a", light="#de5d50", dark="#5c1712")),
    features=features, units=units, events=[],
)
json.dump(battle, open(HERE + "battle.json", "w"), indent=1, ensure_ascii=False)
print(len(units), "units,", len(features), "features,", len(channel), "river cells, river from", RIVER[0], "to", RIVER[-1])
