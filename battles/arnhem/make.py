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
    ("pol_n", "polish", "Poles", "The Poles who crossed the Rhine into the perimeter: 52 rowed over on the night of 22 September, 35 reaching it; 153 more on the 24th", "", "infantry", 35, LOOSE),
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
def heading(a, b): return round(math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) % 360)
def hold_until(id, t0):  # stand until the minute before t0, then turn and go
    if sec(t0) - sec(KEYS[id][-1]["t"]) > 120: keys(id, [K(plus(t0, -1), last(id))])
def at(id, t, **kw): hold_until(id, t); keys(id, [K(t, last(id), **kw)])  # a change in place
def appear(id, t, p, h, state="line", **kw): keys(id, [K(t, p, h=h, state=state, **kw)])
def hide(id, t): at(id, t, state="hidden")
def dense(pts, step=1200):  # no straight leg longer than `step`, so no leg runs past three hours
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        n = max(1, math.ceil(math.dist(a, b) / step))
        out += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(1, n + 1)]
    return [p for i, p in enumerate(out) if i == 0 or math.dist(p, out[i - 1]) > 5]
PACE = 4  # km/h, a column of foot on the road
def walk(t0, pts, state="column", kmh=PACE):  # keys along a path at a marching pace
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
def smoke(at, t0, t1, rate=10, spread=400): features.append(dict(type="smoke", at=list(at), rate=rate, spread=spread, **{"from": t0, "until": t1}))
def strike(name, at, t0, t1, spread=500, h=250): features.append(dict(type="airstrike", name=name, at=list(at), spread=spread, h=h, **{"from": t0, "until": t1}))
for id in BASE: appear(id, START, (0, 0), 0, state="hidden")

# Places the movements use, as local metres
DZX, LZZ, LZS, DZY, RVY = P['dzx'], P['lzz'], (P['lz_s'][0] + 150, P['lz_s'][1] + 100), P['heath_y'], P['rv_y']
DZKC = (sum(p[0] for p in DZK) / 4, sum(p[1] for p in DZK) / 4)
RAMP, BRIDGE_S, CHURCH, FLATS, HART, SCHOON = P['ramp'], bank((6250, -2200), -16), P['church'], P['flats'], P['hartenstein'], P['schoonoord']
NBANK = lambda x: bank((x, river_y(x)), 16)  # the north bank at x
SBANK = lambda x: bank((x, river_y(x)), -16)
LANDING_D = bank(G('682767'), 16)  # the Dorsets' landing below the Westerbouwing
def tiger(a, b): return along(UTRECHTSEWEG, a, b)
def lion(a, b): return along(RIVER_ROAD, a, b)
def leopard(a, b): return along(AMSTERDAMSEWEG, a, b)
SOUTH_EDGE_N = (2900, -7900)  # where the road to Nijmegen leaves the map, toward Elst

# ---- 17 September: the first lift ----
# The pathfinders at 12:40, a platoon to each zone; the company gathers on LZ-Z for the night.
for id, zone, h in (("pf_z", LZZ, 90), ("pf_s", LZS, 90), ("pf_x", DZX, 90)): appear(id, D(17, "12:40"), zone, h, "skirmish")
for id in ("pf_z", "pf_s", "pf_x"): at(id, D(17, "13:10"), state="line")
for id in ("pf_s", "pf_x"): hide(id, plus(move(id, D(17, "15:00"), [off(LZZ, 150, -100)]), 1))
lose("pf_z", D(17, "16:00"), D(17, "16:05"), -124)
# The gliders: the airlanding brigade on LZ-S from 13:00, Div HQ, the Recce Squadron and two batteries on LZ-Z from 13:19.
appear("st1", D(17, "13:00"), off(LZS, -200, 150), 120)
appear("border_hq", D(17, "13:15"), off(LZS, 200, -150), 200); appear("border_a", D(17, "13:15"), off(LZS, 400, 100), 200)
appear("border_b", D(17, "13:16"), off(LZS, -400, -100), 200); appear("border_c", D(17, "13:17"), off(LZS, 0, -300), 200); appear("border_d", D(17, "13:18"), off(LZS, -300, 300), 200)
appear("kosb", D(17, "13:30"), off(LZS, 300, 350), 300); appear("gp1", D(17, "13:20"), off(LZS, -100, 400), 180)
appear("divhq", D(17, "13:19"), off(LZZ, 100, 100), 90); appear("bty1", D(17, "13:15"), off(LZZ, -300, -100), 90); appear("bty3", D(17, "13:45"), off(LZZ, 300, -150), 90)
appear("recce", D(17, "13:40"), off(LZZ, -150, 200), 90)
# 1st Parachute Brigade on DZ-X, 13:50 to 14:08
appear("p3", D(17, "14:00"), off(DZX, 300, 0), 90); appear("p1", D(17, "14:03"), off(DZX, 0, 250), 90)
appear("p2", D(17, "13:55"), off(DZX, -200, -200), 120); appear("p2b", D(17, "13:56"), off(DZX, -450, -50), 120); appear("p2c", D(17, "13:57"), off(DZX, -50, -350), 120)
appear("p3c", D(17, "14:01"), off(DZX, 500, 200), 90)
for id in ("p1", "p2", "p2b", "p2c", "p3", "p3c"): at(id, D(17, "14:30"), state="column")
move("divhq", D(17, "14:00"), [P['lz_z_hq']], h=90); move("bty1", D(17, "14:00"), [off(P['lz_z_hq'], -200, -250)], h=60); move("bty3", D(17, "14:20"), [off(P['lz_z_hq'], 200, -250)], h=80)
move("gp1", D(17, "14:00"), [off(LZZ, 0, -350)], h=90)
# 15:00: the three battalions march; the airlanding brigade goes to its rendezvous round the zones.
move("border_hq", D(17, "13:40"), [P['jonkershoeve']], h=270); move("border_a", D(17, "13:40"), [G('6480')], h=270)
move("border_b", D(17, "13:40"), [G('6377'), P['renkum']], h=250); move("border_c", D(17, "13:40"), [G('6579')], h=240); move("border_d", D(17, "13:40"), [G('633784')], h=270)
move("st1", D(17, "13:40"), [off(P['jonkershoeve'], 250, 200)], h=270)
move("kosb", D(17, "15:00"), along(RAIL, off(LZS, 0, 0), (-5000, 3600)) + [off(DZY, 900, 0)], h=230)
move("p1", D(17, "14:35"), [(-2700, 900)], h=60, state="line")
go("p1", D(17, "15:40"), D(17, "16:00"), [P['wolfheze']], h=60, state="column")
move("recce", D(17, "15:40"), [(-2100, 1000)], h=60, state="column")
at("recce", D(17, "16:00"), state="firing"); at("recce", D(17, "16:30"), state="line")
# 3 Para: the Utrechtseweg; 2 Para and its attached troops: Heelsum, Doorwerth, Heveadorp and the river road
p3_route = [(-3800, -700)] + tiger((-3625, -1567), G('685785'))
go("p3", D(17, "15:00"), D(17, "17:00"), p3_route, h=90, state="firing")
LION_W = [(-3800, -900), (-3046, -1405), P['doorwerth'], P['heveadorp']]
go("p2", D(17, "15:00"), D(17, "20:00"), LION_W + lion(P['heveadorp'], RAMP), h=180, state="firing")
go("p2b", D(17, "15:05"), D(17, "18:30"), LION_W + lion(P['heveadorp'], (3093, -1541)) + [G('723782')], h=90, state="firing")
go("p2c", D(17, "15:10"), D(17, "18:30"), LION_W + lion(P['heveadorp'], (2313, -1733)) + [NBANK(2420)], h=160, state="firing")
go("p3c", D(17, "15:00"), D(17, "18:00"), p3_route[:-1] + [G('685785')], h=90, state="column")
# Krafft's battalion in the woods east of Wolfheze; its blocking line from about three, withdrawn north-east at 21:30.
appear("krafft", D(17, "13:00"), (-700, 600), 270)
go("krafft", D(17, "14:20"), D(17, "15:00"), [P['h_wolfheze']], h=270, state="line")
fire("krafft", D(17, "16:00"), D(17, "21:30"))
go("krafft", D(17, "21:31"), D(18, "00:30"), [(300, 700), (1300, 1400)], h=250, state="line", moving="retreat")
appear("weber", D(17, "16:30"), G('682824'), 230)
# 1 Para: Wolfheze station at four, R Company on the Amsterdamseweg at five, round to the south at six, firm at eight.
fire("p1", D(17, "16:00"), D(17, "16:30"), state="column")
go("p1", D(17, "16:30"), D(17, "17:00"), [G('673816')], h=60, state="firing"); fire("weber", D(17, "17:00"), D(17, "19:30"))
go("p1", D(17, "18:00"), D(17, "19:00"), [G('690809')], h=90, state="line"); go("p1", D(17, "19:30"), D(17, "20:00"), [G('695809')], h=90, state="line")
lose("p1", D(17, "17:00"), D(17, "20:00"), 70)
at("bty3", D(17, "17:00"), state="firing"); at("bty3", D(17, "17:30"), state="line")
# 3 Para's B Company meets armoured cars at the crossroads about five; C Company goes off along the railway at six;
# the battalion halts for the night at the Hartenstein at 21:30.
at("p3", D(17, "18:00"), state="line")
go("p3c", D(17, "18:00"), D(18, "00:00"), [G('690793'), P['hoog']] + along(RAIL, P['hoog'], P['centraal']), h=120, state="line")
go("p3", D(17, "20:30"), D(17, "21:30"), [HART], h=90, state="line")
lose("p3", D(17, "17:00"), D(17, "20:30"), 40)
# 2 Para: A Company at the ramp at eight; B Company on the Den Brink till dark, then to the pontoon bridge; C Company
# at the railway bridge as it is blown, then into the town.
at("p2", D(17, "20:45"), state="firing")
at("p2c", D(17, "18:45"), state="column")
go("p2c", D(17, "19:00"), D(17, "21:30"), lion(NBANK(2420), P['pavilion']) + [(5300, -1200)], h=90, state="firing")
at("p2b", D(17, "19:30"), state="line"); go("p2b", D(17, "21:00"), D(17, "23:30"), lion(G('723782'), P['pontoon']), h=120, state="line")
lose("p2b", D(17, "17:30"), D(17, "19:30"), 50)
# The rest of the airlanding brigade digs in round the zones; the Germans gather west of Arnhem.
move("gp1", D(17, "19:00"), [off(P['lz_z_hq'], 300, 200)], h=90)
appear("sp_n", D(17, "20:00"), off(DREIJENSEWEG[2], 200, 0), 270); appear("sp_t", D(17, "20:00"), (3500, -1100), 270)
appear("grabner", D(17, "18:00"), (6400, -1400), 180, "column")
go("grabner", D(17, "18:10"), D(17, "18:40"), [RAMP, BRIDGE_S] + NIJMEGEN_RD[1:] + [SOUTH_EDGE_N], h=200, state="column")
hide("grabner", D(17, "18:41"))
appear("brinkmann", D(17, "23:00"), (6900, -1900), 270)
# Lewis's party of 3 Para reaches the bridge in the night; B Company 2 Para, about 70, at 05:30.
go("p3c", D(18, "00:30"), D(18, "02:00"), [(6000, -1600), RAMP], h=90, state="line"); hide("p3c", D(18, "02:01")); lose("p2", D(18, "02:00"), D(18, "02:01"), -45)
go("p2b", D(18, "04:30"), D(18, "05:30"), along(RIVER_ROAD, P['pontoon'], RAMP), h=90, state="line"); hide("p2b", D(18, "05:31")); lose("p2", D(18, "05:30"), D(18, "05:31"), -70)

# ---- 18 September ----
# 1 Para south toward the town in the night, the railway bridge at seven, the factory, the junction at three;
# across the road under smoke to just west of the hospital at five, about 100 left.
go("p1", D(18, "01:00"), D(18, "03:00"), [G('697797')], h=150, state="firing")
go("p1", D(18, "03:30"), D(18, "04:30"), [G('709783')], h=120, state="firing")
go("p1", D(18, "06:00"), D(18, "07:00"), [G('712775')], h=90, state="line")
go("p1", D(18, "08:00"), D(18, "09:00"), [G('718776')], h=90, state="firing")
go("p1", D(18, "14:00"), D(18, "15:00"), [G('726778')], h=80, state="firing")
go("p1", D(18, "16:30"), D(18, "17:00"), [off(P['hospital'], -250, -50)], h=80, state="line")
lose("p1", D(18, "07:00"), D(18, "17:00"), 378)
# 3 Para from the Hartenstein onto the river road at 04:30, into Arnhem a mile short of the bridge by seven
go("p3", D(18, "04:30"), D(18, "07:00"), [off(HART, 250, -800)] + lion((1564, -1823), (4534, -1216)), h=80, state="firing")
at("p3", D(18, "12:00"), state="line"); fire("p3", D(18, "14:00"), D(18, "17:00"))
lose("p3", D(18, "07:00"), D(18, "17:00"), 250)
# Spindler's line: the Dreijenseweg to the railway, and the streets west of the hospital to the river
go("sp_n", D(18, "05:00"), D(18, "06:00"), [off(DREIJENSEWEG[2], 150, 0)], h=270, state="line")
go("sp_t", D(18, "05:00"), D(18, "06:00"), [(3950, -1250)], h=260, state="line")
fire("sp_t", D(18, "07:00"), D(18, "17:00")); fire("sp_t", D(18, "20:30"), D(18, "21:30"))
# Gräbner's charge over the bridge at 09:30: twelve of 22 vehicles lost in two hours
appear("grabner", D(18, "09:20"), (6100, -3000), 20, "column")
go("grabner", D(18, "09:21"), D(18, "09:30"), [BRIDGE_S], h=0, state="charge", moving="column")
go("grabner", D(18, "09:30"), D(18, "09:40"), [RAMP, off(RAMP, -100, 300)], h=0, state="charge", moving="charge")
fire("p2", D(18, "09:30"), D(18, "11:30"), state="firing")
lose("grabner", D(18, "09:35"), D(18, "11:30"), 12)
go("grabner", D(18, "11:30"), D(18, "11:45"), [RAMP, BRIDGE_S, (6100, -3000)], h=200, state="retreat", moving="retreat"); hide("grabner", D(18, "11:46"))
fire("brinkmann", D(18, "00:30"), D(18, "06:00"), state="firing")
appear("knaust", D(18, "21:00"), (6300, -1200), 180); appear("knaust_pz", D(18, "21:00"), (6100, -1150), 180)
fire("knaust", D(18, "22:00"), D(19, "02:00"), state="firing"); fire("knaust_pz", D(18, "22:00"), D(19, "02:00"), state="firing")
lose("p2", D(18, "09:30"), D(18, "23:00"), 150)
# The airlanding brigade on the zones: B Company 1 Border shelled at Renkum, D Company attacked at Heelsum, the KOSB on
# Ginkel Heath from nine; D Company KOSB cut off at Ginkel at ten. The Me 109s on LZ-Z at eleven.
appear("lippert1", D(18, "06:30"), (-7700, -2300), 90); appear("flieger", D(18, "06:30"), (-7000, -800), 90); appear("helle", D(18, "07:30"), (-4500, 2700), 330)
appear("schiff", D(18, "09:00"), (-7700, 900), 90)
fire("lippert1", D(18, "07:00"), D(18, "14:00")); fire("border_b", D(18, "07:00"), D(18, "14:00"))
go("flieger", D(18, "06:40"), D(18, "07:30"), [off(G('633784'), -900, 0)], h=90, state="firing"); fire("border_d", D(18, "07:30"), D(18, "15:00"))
at("flieger", D(18, "15:00"), state="line")
lose("border_b", D(18, "07:00"), D(18, "14:00"), 25); lose("border_d", D(18, "07:30"), D(18, "15:00"), 15)
go("helle", D(18, "08:00"), D(18, "09:00"), [off(DZY, 1700, -700)], h=300, state="firing"); fire("kosb", D(18, "09:00"), D(18, "15:30"))
appear("kosb_d", D(18, "08:00"), off(DZY, 900, 200), 60, "column"); lose("kosb", D(18, "08:00"), D(18, "08:01"), 150)
go("kosb_d", D(18, "08:01"), D(18, "09:30"), [P['ginkel']], h=180, state="firing")
go("schiff", D(18, "10:00"), D(18, "12:00"), [off(DZX, -1600, 200)], h=90, state="firing"); at("schiff", D(18, "15:30"), state="line")
lose("kosb", D(18, "09:00"), D(18, "15:30"), 40); lose("kosb_d", D(18, "09:30"), D(18, "15:30"), 30); lose("helle", D(18, "09:00"), D(18, "16:00"), 100)
strike("Me 109s over LZ-Z", LZZ, D(18, "11:00"), D(18, "11:20"), 700)
# Div HQ to 665783 at seven and the Hartenstein at five; the Staffords' first half for Arnhem at 09:45; 3 Bty by the church at ten
go("divhq", D(18, "06:30"), D(18, "07:00"), [G('665783')], h=90)
move("divhq", D(18, "16:00"), tiger(G('665783'), HART) + [HART], h=90)
go("st1", D(18, "09:45"), D(18, "13:00"), [P['h_wolfheze'], P['koude']] + tiger(P['koude'], G('713784')), h=90, state="firing")
at("st1", D(18, "13:30"), state="line")
move("bty3", D(18, "08:00"), tiger(G('665783'), (1065, -770)) + [off(CHURCH, 150, 120)], h=90, kmh=5)
at("bty3", D(18, "17:00"), state="firing"); at("bty3", D(18, "18:00"), state="line")
move("bty1", D(18, "16:00"), [G('663793')], h=90); move("recce", D(18, "06:00"), [G('656780')], h=90)
go("recce", D(18, "07:00"), D(18, "08:00"), [G("708782")], h=90, state="firing"); move("recce", D(18, "08:30"), [G('665783')], h=90)
# B Company 1 Border withdraws at two; D Company through C Company at five; the brigade to its Phase II line at night.
move("border_b", D(18, "14:00"), [G('6477'), G('6576'), G('6677')], h=270)
move("border_d", D(18, "15:00"), [G('665780')], h=270)
# The second lift, 15:09: 4th Parachute Brigade on DZ-Y under fire; the gliders on LZ-S and LZ-X
appear("p156", D(18, "15:09"), off(DZY, 300, 250), 90); appear("p10", D(18, "15:11"), off(DZY, -300, 0), 90); appear("p11", D(18, "15:13"), off(DZY, 500, -250), 120)
appear("st2", D(18, "15:10"), off(LZS, 300, 0), 120); appear("gp2", D(18, "15:12"), off(DZX, 200, -200), 90); appear("bty2", D(18, "15:14"), off(DZX, -300, 100), 90)
lose("p156", D(18, "15:09"), D(18, "15:20"), 10); lose("p10", D(18, "15:11"), D(18, "15:20"), 12); lose("p11", D(18, "15:13"), D(18, "15:20"), 10)
fire("helle", D(18, "15:09"), D(18, "15:40"), state="retreat")
move("helle", D(18, "15:41"), [(-3500, 2000)], h=90, state="line")
for id in ("p156", "p10"): at(id, D(18, "15:40"), state="column")
move("p156", D(18, "15:41"), [RVY], h=90); move("p10", D(18, "15:41"), [off(RVY, 400, -300)], h=90)
go("kosb_d", D(18, "16:00"), D(18, "17:00"), [off(DZY, 1100, -300)], h=90, state="line"); hide("kosb_d", D(18, "17:01")); lose("kosb", D(18, "17:00"), D(18, "17:01"), -120)
# 156 east along the north of the railway at five; 11 Para for Arnhem at 17:30; the Staffords' second half on the
# railway route at 17:30; Div HQ at the Hartenstein; 1 and 2 Btys to 663793.
NORTH_OF_RAIL = [(-5200, 3000), (-3500, 2300), (-2200, 1650), P['crossing']]
move("p156", D(18, "17:00"), NORTH_OF_RAIL, h=90, kmh=3); move("p10", D(18, "17:20"), [off(p, 0, 250) for p in NORTH_OF_RAIL], h=90, kmh=3)
move("p11", D(18, "17:30"), [(-4500, 3200), (-2500, 2000), P['wolfheze'], P['h_wolfheze']] + tiger(P['h_wolfheze'], (2533, -1042)), h=90, kmh=3.5)
move("st2", D(18, "17:30"), [P['wolfheze'], P['hoog'], P['mariendaal']], h=90, state="firing")
move("bty2", D(18, "17:00"), [off(G('663793'), 250, 150)], h=90); move("gp2", D(18, "16:00"), [off(G('663793'), 0, 500)], h=90)
at("st2", D(18, "21:00"), state="retreat"); move("st2", D(18, "21:01"), [G('717780')], h=90)
lose("st2", D(18, "20:00"), D(18, "21:00"), 40)
move("kosb", D(18, "19:00"), [(-4300, 3300), (-2500, 2050), (-1500, 1500), (0, 1100), off(LZL, -300, 100)], h=60, kmh=2)
move("border_hq", D(18, "19:00"), [G('682785')], h=270); move("border_a", D(18, "19:00"), [G('6878')], h=270); move("border_c", D(18, "19:00"), [G('679784')], h=270)
move("border_b", D(18, "21:00"), [G('6877')], h=250); move("border_d", D(18, "21:00"), [G('6778')], h=270)
go("st1", D(18, "18:30"), D(18, "20:00"), tiger(G('713784'), (3400, -1270)) + [off(G('726778'), -300, 0)], h=80)
move("gp1", D(18, "16:30"), tiger(G('665783'), (462, -849)), h=270)
# C Company 2 Para is taken in the town about noon.
at("p2c", D(18, "11:00"), state="surrender"); hide("p2c", D(18, "12:30")); lose("p2c", D(17, "21:30"), D(18, "11:00"), 60)
# 156's C Company ambushed at the edge of LZ-L at nine; firm base in the wood
move("p156", D(18, "20:15"), [G('694794')], h=90, state="firing"); at("p156", D(18, "22:00"), state="line")
move("p10", D(18, "20:30"), [off(G('694794'), -300, 200)], h=90)
move("krafft", D(18, "06:00"), [(1400, 1400)], h=250)
go("krafft", D(18, "07:30"), D(18, "08:00"), [off(LZL, 300, 300)], h=250, state="firing"); go("krafft", D(18, "09:00"), D(18, "10:00"), [(1500, 1300)], h=250, state="line", moving="retreat")
hide("weber", D(18, "06:00"))

# ---- 19 September ----
# The last attempt on the bridge: 1 Para on the river road at four, the Staffords on the Utrechtseweg at 04:45, 11 Para behind
go("p1", D(19, "03:30"), D(19, "04:00"), [G('730779')], h=80, state="firing")
fire("sp_t", D(19, "04:00"), D(19, "13:59"))
lose("p1", D(19, "04:30"), D(19, "06:00"), 61); lose("p1", D(19, "09:00"), D(19, "11:00"), -161)
move("st1", D(19, "04:45"), tiger((3997, -1291), P['museum']), h=80, state="firing")
move("st2", D(19, "04:30"), [G('718776')], h=80, state="line")
move("p11", D(19, "00:30"), [G('713776')], h=80, state="line")
move("p3", D(19, "05:00"), [off(P['pavilion'], 250, 100)], h=80, state="firing")
lose("p3", D(19, "05:00"), D(19, "08:00"), 190)
go("p3", D(19, "07:30"), D(19, "08:00"), [P['pavilion']], h=80, state="line", moving="retreat")
lose("st1", D(19, "09:00"), D(19, "12:00"), 320); at("st1", D(19, "11:00"), state="retreat")
go("st1", D(19, "11:01"), D(19, "12:30"), tiger(P['museum'], (3400, -1270)), h=80, state="line", moving="retreat")
go("p11", D(19, "09:00"), D(19, "10:00"), [G('720778')], h=80, state="line")
go("p1", D(19, "10:30"), D(19, "11:00"), [off(P['hospital'], 100, 0)], h=80, state="firing")
go("p1", D(19, "13:30"), D(19, "14:00"), [G('726778')], h=80, state="line", moving="retreat")
move("st2", D(19, "08:00"), [G('723782')], h=80, state="firing"); at("st2", D(19, "13:30"), state="retreat")
lose("st2", D(19, "11:00"), D(19, "13:30"), 300)
go("sp_t", D(19, "14:00"), D(19, "14:30"), [(3700, -1150)], h=260, state="charge")
fire("p11", D(19, "14:00"), D(19, "14:30"), state="retreat"); lose("p11", D(19, "14:00"), D(19, "15:00"), 411)
for id, dst, t in (("p11", off(P['outpost'], 100, 50), "14:31"), ("st2", off(P['outpost'], 250, 150), "13:31"), ("st1", off(P['outpost'], 150, 300), "15:00"),
                   ("p3", off(P['outpost'], -200, 50), "16:00"), ("p1", off(G('712774'), 0, 0), "19:00")):
    move(id, D(19, t), lion(along(RIVER_ROAD, last(id), last(id))[0], dst) + [dst], h=80, moving="retreat")
lose("p3", D(19, "08:00"), D(19, "16:00"), 23); lose("p1", D(19, "11:00"), D(19, "19:30"), 84)
at("sp_t", D(19, "15:00"), state="line"); move("sp_t", D(19, "16:00"), [(3000, -1300)], h=250)
# 4th Parachute Brigade against the Dreijenseweg: 156 at 08:30, 10 Para toward the Lichtenbeek; broken off at two
go("p156", D(19, "06:30"), D(19, "07:00"), [G('696798')], h=80, state="line")
fire("p156", D(19, "08:30"), D(19, "10:00")); fire("sp_n", D(19, "08:30"), D(19, "14:00"))
lose("p156", D(19, "08:30"), D(19, "10:00"), 280)
go("p10", D(19, "05:00"), D(19, "07:30"), [(1000, 1500), (1450, 1450)], h=80, state="firing")
lose("p10", D(19, "07:30"), D(19, "13:30"), 280)
move("p156", D(19, "12:00"), [G('697797')], h=80)
appear("pol_gl", D(19, "14:00"), off(LZL, 100, -50), 90); lose("pol_gl", D(19, "14:00"), D(19, "14:10"), 9)
move("kosb", D(19, "08:00"), [off(LZL, -100, 300)], h=60)
fire("kosb", D(19, "13:30"), D(19, "15:00"))
fire("krafft", D(19, "13:30"), D(19, "15:00"))
move("p10", D(19, "13:30"), [P['crossing']], h=230, state="line", moving="retreat", kmh=3)
at("pol_gl", D(19, "14:30"), state="column")
move("pol_gl", D(19, "15:00"), [off(P['crossing'], 300, -150), G('674792')], h=90, kmh=3)
move("kosb", D(19, "15:15"), [(400, 1000), off(P['crossing'], 200, 100)], h=180, kmh=3)
move("p156", D(19, "16:00"), [G('673804')], h=270, state="firing")
lose("p156", D(19, "16:30"), D(19, "17:30"), 131)
move("p156", D(19, "17:30"), [P['crossing'], (-700, 450)], h=90)
move("krafft", D(19, "15:00"), [(200, 900), (-500, 1000)], h=250, state="firing")
lose("kosb", D(19, "17:00"), D(19, "17:30"), 155)
move("kosb", D(19, "17:00"), [G('674792'), HART], h=0)
move("kosb", D(19, "19:00"), [off(P['dreyeroord'], 0, -100)], h=0)
move("pol_gl", D(19, "18:00"), [off(HART, -150, 100)], h=90)
move("p10", D(19, "17:00"), [(-600, 300)], h=90)
lose("krafft", D(19, "13:30"), D(19, "16:00"), 100)
# The 1 and 2 Batteries and RHQ to the church at 18:30; 1 Border's companies hit at seven, and placed for the night
move("bty1", D(19, "17:00"), tiger((-480, -790), (1065, -770)) + [off(CHURCH, -250, 200)], h=60, kmh=5)
move("bty2", D(19, "17:00"), tiger((-480, -790), (1065, -770)) + [off(CHURCH, -50, 300)], h=60, kmh=5)
move("border_hq", D(19, "17:30"), [G('690783')], h=270)
for id in ("border_a", "border_b", "border_c", "border_d"): fire(id, D(19, "19:00"), D(19, "20:00"))
move("border_b", D(19, "21:00"), [G('685770')], h=250); move("border_d", D(19, "21:00"), [G('686775')], h=270)
move("border_c", D(19, "21:00"), [P['koude']], h=270); move("border_a", D(19, "21:00"), [off(P['koude'], 300, 500)], h=300)
move("recce", D(19, "16:00"), [G('693796')], h=0); move("recce", D(19, "22:00"), [off(HART, 300, 250)], h=0)
move("gp1", D(19, "10:00"), [off(HART, 400, -100)], h=60); move("gp2", D(19, "12:00"), [off(HART, -500, 300)], h=300)
move("divhq", D(19, "09:00"), [off(HART, 0, 30)], h=90)
move("pf_z", D(19, "16:00"), [off(HART, 250, 500)], h=30)
lose("st1", D(19, "15:00"), D(19, "23:00"), 0)
# The Germans at the bridge: the Tigers fire into the perimeter in the evening; the houses burn
appear("tigers", D(19, "17:00"), (6900, -1300), 230, "column"); go("tigers", D(19, "17:01"), D(19, "17:30"), [(6550, -1650)], h=230, state="firing")
fire("brinkmann", D(19, "17:00"), D(20, "18:00"), state="line"); fire("knaust", D(19, "08:00"), D(20, "18:00"), state="line"); fire("knaust_pz", D(19, "08:00"), D(19, "12:00"))
lose("p2", D(19, "08:00"), D(19, "23:00"), 200)
smoke(off(RAMP, 50, 150), D(19, "18:00"), D(21, "06:00"), rate=14, spread=300)
strike("Fw 190s over the gun area", G('663793'), D(19, "07:00"), D(19, "07:15"), 500)
# The Germans close round from the west: Lippert's school and the Schiffstammabteilung along the Utrechtseweg
appear("lippert2", D(19, "08:00"), (-7900, -2300), 80, "column"); appear("lippert3", D(19, "08:10"), (-7900, -2000), 80, "column")
move("lippert1", D(18, "15:00"), tiger(P['renkum'], (-3625, -1567)), h=90)
move("lippert2", D(19, "08:01"), tiger(P['renkum'], (-3046, -1405)) + [(-2000, -1700)], h=90)
move("lippert3", D(19, "08:11"), tiger(P['renkum'], (-2447, -1143)), h=90)
move("schiff", D(19, "07:00"), [(-3500, 300), (-2400, 0)], h=90)
move("flieger", D(19, "07:00"), [(-3800, -700), (-2600, -500)], h=90)
move("helle", D(19, "08:00"), [(-1700, 700)], h=110)

# ---- 20 September: the perimeter forms ----
# 156 as advance guard toward the perimeter: held in the woods; encircled in the hollow at one; Hackett breaks out at five
move("p156", D(20, "07:00"), [G('681786')], h=90, state="firing")
move("p156", D(20, "09:30"), [G('682786')], h=90, state="line")
lose("p156", D(20, "07:00"), D(20, "10:00"), 109)
move("p10", D(20, "07:00"), [off(G('682786'), 200, 200)], h=90, state="firing")
move("p10", D(20, "12:00"), [SCHOON], h=90, state="line"); lose("p10", D(20, "07:00"), D(20, "13:10"), 230)
move("p156", D(20, "12:30"), [G('684793')], h=90, state="firing")
lose("p156", D(20, "13:00"), D(20, "17:00"), 38)
move("p156", D(20, "17:00"), [G('697787')], h=90, state="charge", moving="charge")
move("helle", D(20, "09:00"), [off(G('684793'), -600, 300)], h=110, state="firing"); at("helle", D(20, "17:30"), state="line")
move("schiff", D(20, "06:00"), [(-1100, -100)], h=90, state="line")
lose("helle", D(20, "09:00"), D(20, "17:30"), 100)
# The KOSB on the north face, the White House; 1 Border attacked on the west face; C Company by flame-thrower tanks at three
fire("kosb", D(20, "09:00"), D(20, "13:00")); lose("kosb", D(20, "07:00"), D(20, "08:00"), 120)
move("sp_n", D(20, "06:00"), [(1500, 600)], h=200)
move("krafft", D(20, "06:00"), [(800, 500)], h=190, state="firing"); at("krafft", D(20, "13:00"), state="line")
fire("sp_n", D(20, "09:00"), D(20, "13:00"))
fire("border_a", D(20, "10:00"), D(20, "11:00")); move("lippert3", D(20, "08:00"), [off(G('6878'), -900, 400)], h=80, state="firing"); at("lippert3", D(20, "11:00"), state="line")
appear("pz224", D(20, "14:30"), (-1800, -1100), 80, "column")
move("lippert2", D(20, "07:00"), [off(G('679784'), -800, 0)], h=90)
go("pz224", D(20, "14:31"), D(20, "15:00"), [off(G('679784'), -250, 0)], h=90, state="firing"); fire("lippert2", D(20, "15:00"), D(20, "17:00"))
fire("border_c", D(20, "15:00"), D(20, "17:00")); lose("border_c", D(20, "15:00"), D(20, "17:00"), 30)
go("pz224", D(20, "17:00"), D(20, "17:30"), [(-1800, -1100)], h=270, state="line", moving="retreat")
lose("border_a", D(20, "10:00"), D(20, "11:00"), 15)
# Lonsdale takes the Oosterbeek Laag sector; the Staffords back to the laundry and the church; 11 Para's houses knocked down
move("st1", D(20, "11:00"), [P['laundry']], h=90); move("st2", D(20, "11:30"), [off(CHURCH, 150, 50)], h=90)
move("p3", D(20, "11:00"), [off(CHURCH, 300, 250)], h=80); move("p1", D(20, "08:00"), [off(P['outpost'], -350, -50)], h=80)
move("sp_t", D(20, "06:00"), [(2600, -1650)], h=260)
fire("sp_t", D(20, "13:00"), D(20, "19:00")); fire("p11", D(20, "15:00"), D(20, "18:30"), state="retreat")
lose("p11", D(20, "15:00"), D(20, "18:30"), 30)
move("p11", D(20, "18:31"), lion(P['outpost'], CHURCH) + [off(CHURCH, 300, -50)], h=80)
move("p1", D(20, "18:00"), [off(CHURCH, 350, 100)], h=80)
smoke(off(P['outpost'], 200, 0), D(20, "18:00"), D(20, "20:00"), rate=8, spread=200)
# The bridge: Frost wounded at 15:45; the last houses burn; the truce for the wounded
fire("p2", D(20, "06:00"), D(20, "21:00"))
lose("p2", D(20, "06:00"), D(21, "00:00"), 250)
move("p2", D(20, "21:00"), [off(RAMP, -150, 250)], h=90)
# The supply drops: SDP 685783 at 14:06, 17:15; the division's close perimeter at 15:05
move("divhq", D(20, "15:05"), [off(HART, 0, 0)], h=90)
move("pf_z", D(20, "12:00"), [off(SCHOON, 100, 400)], h=90, state="line")

# ---- 21 September ----
at("p2", D(21, "03:00"), state="surrender"); at("p2", D(21, "05:00"), state="surrender"); hide("p2", D(21, "06:00"))
lose("p2", D(21, "00:00"), D(21, "05:00"), 0)
for id in ("brinkmann", "knaust"): move(id, D(21, "05:00"), [off(RAMP, 150 if id == "knaust" else 450, 300)], h=200)
go("knaust_pz", D(21, "10:40"), D(21, "11:25"), [RAMP, BRIDGE_S] + NIJMEGEN_RD[1:] + [SOUTH_EDGE_N], h=200, state="column"); hide("knaust_pz", D(21, "11:26"))
hide("knaust", plus(move("knaust", D(21, "11:00"), [RAMP, BRIDGE_S] + NIJMEGEN_RD[1:] + [SOUTH_EDGE_N], h=200, state="column"), 1))
hide("tigers", D(21, "06:00")); move("lippert1", D(21, "06:00"), [off(G('6778'), -800, -200)], h=80)
# The Westerbouwing at nine: Worrowski with four French tanks; B Company 1 Border off the high ground, Breeseforce formed
appear("worrowski", D(21, "08:00"), (-1700, -2050), 80, "column")
move("pz224", D(21, "07:00"), [(-1500, -2050)], h=80)
go("worrowski", D(21, "08:01"), D(21, "09:00"), [off(P['westerbouwing'], -300, 0)], h=80, state="firing")
go("pz224", D(21, "08:30"), D(21, "09:00"), [off(P['westerbouwing'], -150, -50)], h=80, state="charge", moving="column")
fire("border_b", D(21, "09:00"), D(21, "09:30"), state="retreat"); lose("border_b", D(21, "09:00"), D(21, "09:30"), 60)
lose("pz224", D(21, "09:00"), D(21, "09:40"), 3)
move("border_b", D(21, "09:31"), [P['hemelsche'], G('693774')], h=250)
at("pz224", D(21, "09:40"), state="line"); move("worrowski", D(21, "09:30"), [P['westerbouwing']], h=80)
fire("p10", D(21, "07:00"), D(21, "08:00")); move("pf_z", D(21, "18:00"), [off(HART, 200, 200)], h=60)
# The concentrated attack from eight; the Staffords' sector at two; B Troop 1 Battery by tanks at three
for id in ("sp_t", "lippert2", "lippert3", "schiff", "krafft", "helle", "flieger", "sp_n"): fire(id, D(21, "08:00"), D(21, "11:00"))
for id in ("border_a", "border_c", "border_d", "kosb", "st1", "st2", "p1", "p3", "p11", "gp1", "gp2"): fire(id, D(21, "08:00"), D(21, "10:00"))
fire("sp_t", D(21, "14:00"), D(21, "16:00")); fire("st1", D(21, "14:00"), D(21, "15:30")); fire("st2", D(21, "14:00"), D(21, "15:30")); fire("bty1", D(21, "15:00"), D(21, "16:00"))
lose("bty1", D(21, "15:00"), D(21, "16:00"), 25)
# The White House at 16:30: an SS company destroyed by two bayonet charges
go("sp_n", D(21, "16:00"), D(21, "16:30"), [off(P['dreyeroord'], 300, 350)], h=230, state="charge")
fire("kosb", D(21, "16:30"), D(21, "17:00"), state="charge"); lose("sp_n", D(21, "16:30"), D(21, "17:00"), 100)
go("kosb", D(21, "17:00"), D(21, "17:15"), [off(P['dreyeroord'], 0, -100)], h=0, state="line", moving="charge")
go("sp_n", D(21, "17:00"), D(21, "17:30"), [(1500, 600)], h=200, state="line", moving="retreat")
move("kosb", D(21, "21:30"), [G('694787')], h=0); move("p10", D(21, "21:30"), [G('695788')], h=60)
for id in ("border_a", "border_c"): fire(id, D(21, "19:00"), D(21, "19:45"))
# The Poles drop on DZ-K from 17:15 under fire from the north bank; they find the ferry sunk
appear("pol2", D(21, "17:15"), off(DZKC, -200, 300), 330); appear("pol3", D(21, "17:16"), off(DZKC, 400, -300), 330); appear("pol_hq", D(21, "17:18"), off(DZKC, 0, -100), 330)
for id, n in (("pol2", 10), ("pol3", 10), ("pol_hq", 10)): lose(id, D(21, "17:20"), D(21, "17:45"), n)
for id, dst in (("pol2", off(P['driel'], 400, 300)), ("pol3", off(P['driel'], 600, -300)), ("pol_hq", off(P['driel'], 0, 50))):
    at(id, D(21, "17:50"), state="column"); move(id, D(21, "18:00"), [dst], h=0, kmh=2.5)
move("pol2", D(21, "23:30"), [off(P['ferry_s'], 0, -250)], h=0)
appear("ss10", D(21, "19:30"), (6250, -500), 180, "column")
go("ss10", D(21, "19:31"), D(21, "20:15"), [RAMP, BRIDGE_S] + NIJMEGEN_RD[1:] + [SOUTH_EDGE_N], h=200, state="column"); hide("ss10", D(21, "20:16"))
go("brinkmann", D(21, "20:20"), D(21, "21:00"), [RAMP, BRIDGE_S, (6100, -3000)], h=200, state="column"); hide("brinkmann", D(21, "21:01"))

# ---- 22 September: XXX Corps reaches Driel ----
move("pol2", D(22, "04:00"), [off(P['driel'], 400, 300)], h=0)
appear("hcr", D(22, "08:15"), (900, -7900), 340, "column")
move("hcr", D(22, "08:16"), [off(P['driel'], 300, -300)], h=0, kmh=25)
appear("driel_kg", D(22, "08:30"), (2400, -5000), 290, "column")
move("driel_kg", D(22, "08:31"), [(1300, -4500)], h=290, state="firing")
for id in ("pol2", "pol3", "pol_hq"): fire(id, D(22, "09:00"), D(22, "11:30"))
lose("driel_kg", D(22, "09:00"), D(22, "11:30"), 60); lose("pol3", D(22, "09:00"), D(22, "11:30"), 15)
move("driel_kg", D(22, "11:31"), [(2400, -5800)], h=130, state="column", moving="retreat"); hide("driel_kg", D(22, "12:30"))
for id in ("border_a", "border_c", "border_d"): fire(id, D(22, "05:45"), D(22, "07:00"))
fire("border_d", D(22, "15:00"), D(22, "16:30")); lose("border_d", D(22, "15:00"), D(22, "16:30"), 98)
fire("lippert1", D(22, "15:00"), D(22, "16:30"))
smoke(off(SCHOON, 0, 0), D(22, "06:00"), D(25, "21:00"), rate=6, spread=250)
appear("rdg", D(22, "19:30"), (900, -7900), 340, "column"); appear("dcli", D(22, "19:30"), (700, -7900), 340, "column")
move("rdg", D(22, "19:31"), [off(P['driel'], -300, -400)], h=0, kmh=10)
move("dcli", D(22, "19:31"), [off(P['driel'], 200, 600)], h=0)
# The first crossing: 8 Para Company on six rubber boats and a cable from 23:00; 35 reach the perimeter
move("pol3", D(22, "22:00"), [off(SBANK(900), 0, -300)], h=0)
lose("pol3", D(22, "23:00"), D(23, "04:00"), 52)
appear("pol_n", D(23, "02:00"), off(NBANK(900), 0, 60), 0)
move("pol_n", D(23, "04:00"), [off(FLATS, 0, 80), off(CHURCH, -150, 250)], h=0)
move("pol3", D(23, "04:30"), [off(P['driel'], 600, -300)], h=0)

# ---- 23 and 24 September: the siege ----
fire("pf_z", D(23, "07:15"), D(23, "07:45")); lose("pf_z", D(23, "07:15"), D(23, "07:45"), 15)
for id in ("p10", "p156"): fire(id, D(23, "08:00"), D(23, "15:00"))
for id in ("sp_n", "krafft"): fire(id, D(23, "08:00"), D(23, "15:00"))
for id in ("border_a", "border_c"): fire(id, D(23, "12:00"), D(23, "15:30"))
fire("lippert3", D(23, "12:00"), D(23, "15:30")); fire("lippert2", D(23, "12:00"), D(23, "15:30"))
lose("border_a", D(23, "12:00"), D(23, "15:30"), 40); lose("border_d", D(23, "12:00"), D(23, "13:00"), 12)
fire("kosb", D(23, "07:30"), D(23, "10:00")); lose("kosb", D(23, "07:30"), D(24, "12:00"), 165)
appear("pol1", D(24, "17:30"), (-100, -7900), 0, "column"); move("pol1", D(24, "17:31"), [off(P['driel'], -500, 0)], h=0)
# The second crossing, 03:00 to 05:05: 153 Poles reach the north bank
move("pol3", D(23, "23:00"), [off(SBANK(900), 0, -250)], h=0); move("pol_hq", D(23, "23:00"), [off(SBANK(900), 300, -250)], h=0)
lose("pol3", D(24, "03:00"), D(24, "05:05"), 95); lose("pol_hq", D(24, "03:00"), D(24, "05:05"), 58); lose("pol_n", D(24, "03:00"), D(24, "05:05"), -153)
move("pol_n", D(24, "02:30"), [off(FLATS, 0, 120)], h=0)
move("pol_n", D(24, "10:00"), [off(SCHOON, 250, 150)], h=90)
move("pol3", D(24, "06:00"), [off(P['driel'], 600, -300)], h=0); move("pol_hq", D(24, "06:00"), [off(P['driel'], 0, 50)], h=0)
move("pf_z", D(24, "11:00"), [off(HART, 150, 150)], h=60)
strike("Typhoons over the woods west of the perimeter", (-700, -1300), D(24, "14:15"), D(24, "14:35"), 700, 90)
for id in ("p10", "border_a", "border_c"): fire(id, D(24, "18:00"), D(24, "19:05"))
lose("border_d", D(24, "08:00"), D(24, "19:00"), 6)
lose("p10", D(23, "08:00"), D(24, "19:00"), 20)
appear("dorsets", D(24, "19:30"), off(SBANK(250), -100, -400), 0, "column")
move("dorsets", D(24, "19:31"), [off(SBANK(-150), 0, -100)], h=0)

# ---- 25 September: the Dorsets, the Tigers, Berlin ----
hide("dorsets", D(25, "01:00"))
appear("dorsets", D(25, "01:30"), LANDING_D, 0, "firing")
lose("dorsets", D(25, "02:00"), D(25, "08:00"), 240)
fire("worrowski", D(25, "02:00"), D(25, "08:00"))
move("dorsets", D(25, "08:00"), [P['hemelsche'], off(G('693774'), -100, 100)], h=270)
strike("Typhoons", (-900, -900), D(25, "09:45"), D(25, "10:05"), 700, 90)
appear("tigers", D(25, "09:30"), (2300, -1450), 250, "column")
go("tigers", D(25, "09:31"), D(25, "10:00"), [off(CHURCH, 450, 100)], h=250, state="charge")
go("sp_t", D(25, "09:40"), D(25, "10:10"), [off(CHURCH, 600, 250)], h=250, state="charge")
fire("bty1", D(25, "10:00"), D(25, "10:30"), state="line"); fire("bty2", D(25, "10:00"), D(25, "10:30"), state="line")
lose("bty1", D(25, "10:00"), D(25, "10:30"), 35); lose("bty2", D(25, "10:00"), D(25, "10:30"), 40)
lose("sp_t", D(25, "10:00"), D(25, "11:00"), 120)
go("tigers", D(25, "10:30"), D(25, "11:00"), [(2000, -1500)], h=80, state="line", moving="retreat")
go("sp_t", D(25, "10:40"), D(25, "11:15"), [(2500, -1650)], h=260, state="line", moving="retreat")
fire("st1", D(25, "12:15"), D(25, "13:00")); fire("st2", D(25, "12:15"), D(25, "13:00"))
strike("Typhoons", (-600, -1500), D(25, "12:00"), D(25, "12:20"), 700, 90); strike("Typhoons", (2300, -1300), D(25, "14:15"), D(25, "14:35"), 700, 270)
strike("Typhoons", (1500, 500), D(25, "17:30"), D(25, "17:50"), 700, 180); strike("Typhoons", (-800, -500), D(25, "18:50"), D(25, "19:10"), 700, 90)
fire("border_d", D(25, "15:30"), D(25, "16:00")); fire("lippert1", D(25, "15:30"), D(25, "16:00"))
lose("border_d", D(25, "15:30"), D(25, "16:05"), 19); at("border_d", D(25, "16:00"), state="surrender"); hide("border_d", D(25, "16:30"))
# Operation Berlin: the KOSB leaves first at 21:45; the batteries' fire covers the crossing from 22:00; the boats ply from
# the flats until 05:30, and each unit is taken off the map as its last men go over.
BERLIN = [  # (unit, leaves, crosses, men left north of the river and not drawn as crossing)
    ("kosb", "21:45", D(26, "02:00")), ("p10", "20:15", D(26, "00:30")), ("p156", "20:20", D(26, "00:45")), ("recce", "20:50", D(25, "23:30")),
    ("divhq", "22:00", D(25, "23:45")), ("pf_z", "22:00", D(26, "01:15")), ("border_hq", "22:40", D(26, "00:15")), ("border_a", "22:50", D(26, "01:30")),
    ("border_b", "22:55", D(26, "01:45")), ("border_c", "23:10", D(26, "05:15")), ("st1", "23:40", D(26, "02:30")), ("st2", "23:45", D(26, "02:45")),
    ("p1", "23:15", D(26, "03:00")), ("p3", "23:20", D(26, "03:15")), ("p11", "23:25", D(26, "03:30")), ("gp1", "22:15", D(26, "00:00")),
    ("gp2", "22:30", D(26, "02:15")), ("bty1", "22:30", D(26, "01:00")), ("bty2", "22:35", D(26, "01:10")), ("bty3", "22:40", D(26, "01:20")),
    ("pol_n", "23:00", D(26, "03:45")), ("pol_gl", "23:00", D(26, "04:00")), ("dorsets", "22:45", D(26, "04:30")),
]
for i, (id, t, cross) in enumerate(BERLIN):
    spot = off(FLATS, -150 + (i % 6) * 60, -40 - (i // 6) * 25)
    t0 = D(25, t) if t >= "20:00" else D(26, t)
    move(id, t0, [spot], h=180, state="column")
    hide(id, cross)
smoke(off(CHURCH, 0, 0), D(25, "10:00"), D(25, "11:30"), rate=8, spread=250)
for id in ("pol2", "pol3", "pol_hq", "pol1"): at(id, D(25, "21:30"), state="line")
TINTS = [dict(color="rgba(200,206,214,0.30)", **{"from": D(23, "06:00"), "until": D(23, "10:00")}),
         dict(color="rgba(190,196,206,0.40)", **{"from": D(25, "20:30"), "until": D(26, "06:00")})]

# ---- strengths: each unit's losses fall evenly over their span ----
def pose(id, t):  # where a unit is at time t between its keys
    ks = KEYS[id]; a = max((k for k in ks if sec(k["t"]) <= sec(t)), key=lambda k: sec(k["t"])); b = next((k for k in ks if sec(k["t"]) > sec(t)), None)
    if b is None: return (a["x"], a["y"])
    f = (sec(t) - sec(a["t"])) / (sec(b["t"]) - sec(a["t"])); return (a["x"] + f * (b["x"] - a["x"]), a["y"] + f * (b["y"] - a["y"]))
def state_at(id, t): return next((k["state"] for k in reversed(KEYS[id]) if sec(k["t"]) <= sec(t) and "state" in k), None)
def curve(pts, base):  # strength at a time, falling linearly through each span of losses
    def f(s):
        if s <= pts[0][0]: return base
        for (s0, v0), (s1, v1) in zip(pts, pts[1:]):
            if s0 <= s <= s1: return v1 if s1 == s0 else round(v0 + (s - s0) / (s1 - s0) * (v1 - v0))
        return pts[-1][1]
    return f
for id in KEYS:
    KEYS[id].sort(key=lambda k: sec(k["t"]))
for id, spans in LOSS.items():
    spans = sorted((s for s in spans if s[2]), key=lambda s: sec(s[0])); cur, pts = BASE[id][6], []
    for t0, t1, n in spans:
        assert state_at(id, t0) not in (None, "hidden") and state_at(id, t1) not in (None, "hidden"), (id, t0, t1, "losses while off the map")
        pts += [(sec(t0), cur), (sec(t1), cur - n)]; cur -= n
    assert cur >= 0, (id, cur)
    if not pts: continue
    s_at = curve(pts, BASE[id][6]); have = {k["t"] for k in KEYS[id]}
    for s, _ in pts:
        t = fmt(s)
        if t not in have: KEYS[id].append(K(t, pose(id, t))); have.add(t)
    KEYS[id].sort(key=lambda k: sec(k["t"]))
    for k in KEYS[id]: k["strength"] = s_at(sec(k["t"]))
def strength(id, t): return next((k["strength"] for k in reversed(KEYS[id]) if sec(k["t"]) <= sec(t) and "strength" in k), BASE[id][6])
# The figures the diaries give
assert strength("p1", D(19, "23:00")) == 116, ("1 Para in Cain's force at 23:00 on 19 Sep", strength("p1", D(19, "23:00")))
assert strength("p3", D(19, "23:00")) == 40, ("3 Para's 40", strength("p3", D(19, "23:00")))
assert strength("p11", D(19, "23:00")) == 150, ("11 Para's 150", strength("p11", D(19, "23:00")))
assert strength("st1", D(19, "23:00")) + strength("st2", D(19, "23:00")) == 100, ("the Staffords' 100", strength("st1", D(19, "23:00")), strength("st2", D(19, "23:00")))
assert strength("kosb", D(20, "08:00")) == 270, ("7 KOSB about 270 at 08:00 on 20 Sep", strength("kosb", D(20, "08:00")))
assert strength("p2", D(18, "05:31")) == 740, ("about 740 at the bridge on the morning of the 18th", strength("p2", D(18, "05:31")))
assert strength("p156", D(20, "10:00")) == 91, ("156: 30 HQ, 15 A, 6 B, 40 C at 10:00 on 20 Sep", strength("p156", D(20, "10:00")))
assert strength("p156", D(20, "18:30")) == 53, ("3 officers and 50 men at 18:30 on 20 Sep", strength("p156", D(20, "18:30")))
assert strength("p10", D(20, "13:10")) == 60, ("about 60 of 10 Para into the perimeter", strength("p10", D(20, "13:10")))
assert strength("border_d", D(22, "16:30")) == 37 and strength("border_d", D(23, "13:00")) == 25 and strength("border_d", D(24, "19:00")) == 19, "D Coy 1 Border: 37, 25, 19"
assert strength("grabner", D(18, "11:30")) == 10, "Gräbner: 12 of 22 vehicles lost"
assert strength("pf_z", D(25, "21:00")) == 171, strength("pf_z", D(25, "21:00"))
assert strength("dorsets", D(25, "08:00")) == 75, "about 75 Dorsets reach the perimeter"
assert strength("pol_n", D(24, "05:05")) == 188, "35 and 153 Poles"
assert strength("pol_gl", D(19, "14:10")) == 84, "nine of the Polish glider element killed"
assert strength("pz224", D(21, "09:40")) == 1, "three tanks destroyed at the Westerbouwing"
assert set(KEYS) == set(BASE), set(KEYS) ^ set(BASE)
for id in KEYS:
    if carried(id, "state") != "hidden" and sec(KEYS[id][-1]["t"]) < sec(END): KEYS[id].append(K(END, last(id)))

# ---- assemble and check ----
TOP = {"infantry": 6, "artillery": 6, "armor": 30}  # km/h, the fastest any leg may go
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
        assert kmh <= TOP[type], (id, a["t"], b["t"], f"{kmh:.1f} km/h")
    state = None
    for k in ks:
        state = k.get("state", state)
        assert state == "hidden" or (on_land((k["x"], k["y"])) and max(abs(k["x"]), abs(k["y"])) < HALF_EXTENT), (id, k["t"], (k["x"], k["y"]), "in the river or off the map")
    units.append(dict(id=id, side=side, name=name, short=short, commander=commander, type=type, strength=strength0, keys=ks, **extra))
for f in features:
    if f.get("type") in ("smoke", "airstrike"): assert on_land(f["at"]), (f.get("name"), f["at"])

battle = dict(
    id="arnhem", name="Arnhem", date="1944-09-17", dateText="17 to 26 September 1944", place="Arnhem and Oosterbeek, Gelderland, the Netherlands",
    origin=dict(lat=LAT0, lon=LON0), extent=2 * HALF_EXTENT, start=START, end=END, sunrise="06:14", sunset="18:47", speed=300, lapse=14400, menPerDot=10,
    water=WATER, terrainExaggeration=1.5, contourInterval=5, trees=dict(density=0.00035, clear=list(TOWNS.values())), fields=FIELDS,
    wind=dict(x=0.5, y=0.2), view=dict(x=0, y=0, width=2 * HALF_EXTENT),
    sides=dict(british=dict(name="British (1st Airborne Division, Urquhart; XXX Corps)", color="#3a5f9e", light="#7d9bd0", dark="#1d3561"),
               polish=dict(name="Poles (1st Independent Parachute Brigade, Sosabowski)", color="#5d7f86", light="#97b4ba", dark="#2e4246"),
               german=dict(name="Germans (II SS Panzer Corps, Bittrich; Kampfgruppe von Tettau)", color="#b8322a", light="#de5d50", dark="#5c1712")),
    features=features, units=units, events=[], tints=TINTS,
)
json.dump(battle, open(HERE + "battle.json", "w"), indent=1, ensure_ascii=False)
print(len(units), "units,", len(features), "features,", len(channel), "river cells, river from", RIVER[0], "to", RIVER[-1])
