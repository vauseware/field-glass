# Builds battles/monmouth/battle.json. Run from the repo root: python3 battles/monmouth/make.py
# Local metres from 40.2740N 74.3080W (x east, y north). The 9 km square holds Englishtown (-4264,2597), Tennent
# meeting house (-1527,1099), Perrine Hill (-807,581), the hedgerow ground, Combs Hill, the Rhea and Craig farms,
# Monmouth Court House (2863,-1531) and the Middletown road where Lee first struck the rear guard. Every place is kept
# in latitude and longitude below and converted once. Anchors are OpenStreetMap and GNIS points. The hedgerow, the
# Parsonage, the Point of Woods, the 1778 bridge, the Rhea farm and Ker's house are placed from the National Register
# nomination's prose, within 250 to 500 m, and labelled "about here". Wemrock Brook, the Middle Ravine and the reach of
# Weamaconk Creek east of the bridge are traced from the DEM. Strengths are Lender and Stone's (Fatal Sunday, 2016) as
# tabulated in Wikipedia's Monmouth order of battle; the British company figures are disputed, so treat them as ±10%.
import json, math
HERE = "battles/monmouth/"
LAT0, LON0 = 40.2740, -74.3080
KX, KY = 111320 * math.cos(math.radians(LAT0)), 111320  # tools/fetch_terrain.py's metres per degree
def M(lat, lon): return (round((lon - LON0) * KX), round((lat - LAT0) * KY))

# ---- terrain ----
T = json.load(open(HERE + "terrain.json"))
COLS, SP = T["cols"], T["spacing"]; HALF = COLS * SP / 2
def z(x, y):
    c, r = int((x + HALF) / SP), int((HALF - y) / SP)
    return T["z"][r * COLS + c] if 0 <= c < COLS and 0 <= r < COLS else 999
def valley(seed, step, n, window=150, stop=None):  # follow a valley floor row by row (step in y) or column by column (step in x)
    pts = [seed]
    for _ in range(n):
        x, y = pts[-1]
        if step[1]: cands = [(z(xx, y + step[1]), (xx, y + step[1])) for xx in range(x - window, x + window + 1, 25)]
        else: cands = [(z(x + step[0], yy), (x + step[0], yy)) for yy in range(y - window, y + window + 1, 25)]
        zz, p = min(cands)
        if stop and stop(zz, p): break
        pts.append(p)
    return pts
def thin(pts, every): return pts[::every] + ([pts[-1]] if (len(pts) - 1) % every else [])

# ---- geography: places ----
PLACES = {
    # OpenStreetMap and GNIS
    'englishtown': (40.29733, -74.35820), 'tennent': (40.28387, -74.32597), 'perrine_hill': (40.27922, -74.31750),
    'perrine_house': (40.27796, -74.32388), 'sutfin': (40.27608, -74.31364), 'craig': (40.27461, -74.29726),
    'combs_hill': (40.26417, -74.31944), 'pitcher_well': (40.27070, -74.30933), 'meet': (40.26868, -74.30529),
    'orchard': (40.26736, -74.31199), 'causeway': (40.26577, -74.27371), 'courthouse': (40.26025, -74.27431),
    'monument': (40.26348, -74.27771), 'wikoff': (40.28272, -74.26060), 'cr522_n': (40.2746, -74.3181),
    'cr522_s': (40.2708, -74.3091), 'old_rd': (40.2687, -74.2874),
    # from the street address; about 150 m
    'covenhoven': (40.2585, -74.2840),
    # from the National Register nomination's prose and the modern road; 250 to 500 m
    'west_ravine': (40.2715, -74.3300), 'bridge': (40.2725, -74.3130), 'hedge_n': (40.2715, -74.3140),
    'hedge_s': (40.2665, -74.3165), 'point_of_woods': (40.2690, -74.3090), 'rhea': (40.2686, -74.3021),
    'ker': (40.2665, -74.2960), 'clash_us': (40.2770, -74.2700), 'clash_br': (40.2780, -74.2620),
}
P = {k: M(*v) for k, v in PLACES.items()}
COMBS = (-950, -880)  # the DEM's summit of Combs Hill, 230 m north of the GNIS point, which sits on the slope

# ---- geography: lines ----
# OpenStreetMap sample points for the three brooks; Weamaconk Creek's reach between the bridge and Freehold and the
# whole of Wemrock Brook and the Middle Ravine come from the DEM below, since the nomination's distances put the
# Middle Ravine, a branch of Wemrock Brook, where OpenStreetMap has no stream.
WEAMACONK_LL = [(40.27785, -74.33702), (40.2715, -74.3300), (40.27125, -74.32327), (40.27077, -74.31750), (40.27280, -74.31357), (40.27368, -74.30934)]
MCGELLAIRDS_LL = [(40.28771, -74.32517), (40.28273, -74.30904), (40.27560, -74.28353), (40.28030, -74.26629)]
weamaconk_e = thin(valley((-114, -35), (25, 0), 60, window=150), 6)  # east from the OSM point to about x 1400
WEAMACONK = [(-4100, 2550), (-3300, 1400)] + [M(*p) for p in WEAMACONK_LL] + weamaconk_e[1:] + [(1700, -450), (2300, -650), P['causeway'], (3300, -1150)]
MCGELLAIRDS = [(-4100, 2560), (-2800, 2200)] + [M(*p) for p in MCGELLAIRDS_LL] + [(4500, 1050)]
WEMROCK = [P['west_ravine'], (-1500, -450), (-1200, -600), (-1000, -680), (-750, -730), (-680, -820), (-640, -900), (-600, -1000), (-500, -1060), (-300, -1100), (0, -1100), (150, -1120), (170, -1200), (175, -1300), (190, -1450), (200, -1600)]
# The Middle Ravine: from the valley head 620 m south of the Craig house down to Wemrock Brook's bottom
MIDDLE = thin(valley((850, -550), (0, -25), 30, window=150, stop=lambda zz, p: zz < 33.5), 3)
# The Englishtown road: the modern CR 522 to the bridge, then 50 to 150 m south of it across the Rhea farm to the
# East Morass causeway, and down Throckmorton Street into Freehold. The Middletown road (NJ 79) leaves the court house north-east.
ROAD = [(-4500, 2900), P['englishtown'], (-3600, 2050), (-2600, 1500), P['tennent'], P['cr522_n'], P['bridge'], (-100, -430), P['meet'], P['rhea'], (900, -560), (1300, -600), P['old_rd'], (2300, -660), P['causeway'], (2880, -1250), P['courthouse']]
MIDDLETOWN_RD = [P['courthouse'], (3100, -1000), (3500, -300), (3849, 500), (4200, 1300), (4500, 1950)]
HEDGEROW = [P['hedge_n'], P['hedge_s']]
def quad(cx, cy, w, h): return [(cx - w, cy - h), (cx + w, cy - h), (cx + w, cy + h), (cx - w, cy + h)]
FIELDS = [quad(-800, 520, 520, 220), quad(-450, 180, 300, 150), quad(-480, -560, 300, 260), quad(560, -560, 260, 180), quad(960, 60, 260, 200),
          quad(-1000, -960, 240, 160), quad(4000, 950, 300, 260), quad(3200, 250, 560, 400), quad(2200, -500, 400, 180)]
features = [
    dict(type="creek", name="Weamaconk Creek (Spotswood Middle Brook)", pts=WEAMACONK, at=[-1700, -120], rot=-10),
    dict(type="creek", name="McGellaird's Brook (Spotswood North Brook)", pts=MCGELLAIRDS, at=[-700, 1300], rot=-20),
    dict(type="creek", name="Wemrock Brook (Spotswood South Brook)", pts=WEMROCK, at=[-1200, -800], rot=-30),
    dict(type="creek", name="Middle Ravine (about here)", pts=MIDDLE, at=[480, -960], rot=40),
    dict(type="road", name="Englishtown road", pts=ROAD, at=[-2700, 1700], rot=-28), dict(type="road", name="Middletown road", pts=MIDDLETOWN_RD, at=[3750, 900], rot=-65),
    dict(type="fence", name="the hedgerow (about here)", pts=HEDGEROW, at=[-900, -480], rot=70),
    dict(type="water", poly=quad(-1870, -280, 170, 110)), dict(type="water", poly=[(2700, -800), (3050, -980), (3120, -1120), (2760, -960)]),
    dict(name="West Ravine", at=[-1870, -560]), dict(name="East Morass", at=[2950, -1200]),
    dict(name="the Parsonage (about here)", at=[P['hedge_n'][0] + 40, P['hedge_n'][1] - 110]), dict(name="Point of Woods (about here)", at=[P['point_of_woods'][0], P['point_of_woods'][1] - 110]),
    dict(name="Perrine Hill", at=[P['perrine_hill'][0], P['perrine_hill'][1] + 110]), dict(name="Combs Hill", at=[COMBS[0], COMBS[1] - 110]),
    dict(name="Sutfin farm", at=[P['sutfin'][0], P['sutfin'][1] - 90]), dict(name="Craig house", at=[P['craig'][0], P['craig'][1] + 90]),
    dict(name="Rhea farm (about here)", at=[P['rhea'][0], P['rhea'][1] - 100]), dict(name="Ker's house (about here)", at=[P['ker'][0], P['ker'][1] - 100]),
    dict(name="Tennent meeting house", at=[P['tennent'][0], P['tennent'][1] + 100]), dict(name="Englishtown", at=[P['englishtown'][0] + 150, P['englishtown'][1] - 120]),
    dict(name="Monmouth Court House", at=[P['courthouse'][0], P['courthouse'][1] - 100]), dict(name="Covenhoven house, Clinton's headquarters", at=[P['covenhoven'][0], P['covenhoven'][1] - 100]),
    dict(name="Wikoff farm", at=[P['wikoff'][0], P['wikoff'][1] + 90]), dict(name="the park's Molly Pitcher well (1992 marker)", at=[P['pitcher_well'][0] + 60, P['pitcher_well'][1] - 90]),
    dict(name="Washington meets Lee (the park's site)", at=[P['meet'][0], P['meet'][1] - 100]), dict(name="to Middletown, 12 miles", at=[4150, 1700], rot=-65),
    dict(name="Battle monument (1884)", at=[P['monument'][0], P['monument'][1] + 90]),
]

# ---- order of battle: (id, side, short, name, commander, type, strength, extra) ----
OOB = [
    # Lee's vanguard, which marched from Englishtown at daylight
    ("grayson", "american", "Grayson", "Grayson's detachment (Scott's former brigade), which led the march", "Col. William Grayson", "infantry", 600, {}),
    ("durkee", "american", "Durkee", "Varnum's brigade", "Col. John Durkee", "infantry", 300, {}),
    ("wayne", "american", "Wayne", "Wayne's detachment: Grayson's Virginians, Butler's and Jackson's battalions; Lafayette led the morning attack", "Brig. Gen. Anthony Wayne", "infantry", 1000, {}),
    ("scott", "american", "Scott", "Scott's detachment of picked men", "Brig. Gen. Charles Scott", "infantry", 1440, {}),
    ("jackson", "american", "Jackson", "Jackson's detachment, isolated on Spotswood North Brook in the morning", "Col. Henry Jackson", "infantry", 250, {}),
    ("maxwell", "american", "Maxwell", "New Jersey brigade", "Brig. Gen. William Maxwell", "infantry", 1000, {}),
    ("oswald", "american", "Oswald", "Lee's artillery, eight of its twelve pieces", "Lt. Col. Eleazer Oswald", "artillery", 100, dict(guns=8)),
    ("oswald4", "american", "Oswald's four", "The four guns that stood with Lee's rearguard on the hill east of the bridge and at the hedgerow", "Lt. Col. Eleazer Oswald", "artillery", 50, dict(guns=4)),
    ("dickinson", "american", "Dickinson", "New Jersey and Pennsylvania militia, out in front since the 27th; about 800 by Hamilton's count", "Maj. Gen. Philemon Dickinson", "militia", 800, dict(loose=True)),
    # Washington's main body: Stirling's line on the Perrine ridge
    ("learned", "american", "Learned", "Learned's brigade", "Col. John Bailey", "infantry", 373, {}),
    ("glover", "american", "Glover", "Glover's brigade", "Brig. Gen. John Glover", "infantry", 636, {}),
    ("huntington", "american", "Huntington", "Huntington's brigade", "Brig. Gen. Jedediah Huntington", "infantry", 632, {}),
    ("poor", "american", "Poor", "Poor's brigade, sent to probe the British right at dusk", "Brig. Gen. Enoch Poor", "infantry", 754, {}),
    ("cilley", "american", "Cilley", "Cilley's picked New England battalion, which drove the 42nd from the Sutfin orchard", "Col. Joseph Cilley", "light_infantry", 350, {}),
    ("knox", "american", "Knox", "Knox's artillery on the Perrine ridge, ten guns", "Brig. Gen. Henry Knox", "artillery", 150, dict(guns=10)),
    # the forward screen under Wayne: the Pennsylvania brigades
    ("irvine", "american", "1st Pa.", "1st Pennsylvania Brigade", "Col. William Irvine", "infantry", 429, {}),
    ("pa2", "american", "2nd Pa.", "2nd Pennsylvania Brigade", "Col. Walter Stewart", "infantry", 487, {}),
    ("pa3", "american", "3rd Pa.", "3rd Pennsylvania Brigade, which Wayne led over the bridge at a quarter to five", "Col. Oliver Spencer", "infantry", 438, {}),
    # Lafayette's reserve on Perrine Hill
    ("clark", "american", "N.C.", "North Carolina brigade", "Col. Thomas Clark", "infantry", 425, {}),
    ("smallwood", "american", "1st Md.", "1st Maryland Brigade", "Brig. Gen. William Smallwood", "infantry", 790, {}),
    # Greene's right on Combs Hill
    ("woodford", "american", "Woodford", "Woodford's Virginia brigade", "Brig. Gen. William Woodford", "infantry", 475, {}),
    ("duplessis", "american", "du Plessis", "Greene's guns on Combs Hill, four pieces", "Lt. Col. Thomas-Antoine de Mauduit du Plessis", "artillery", 60, dict(guns=4)),
    # Steuben's reserve at Englishtown
    ("paterson", "american", "Paterson", "Paterson's brigade", "Brig. Gen. John Paterson", "infantry", 485, {}),
    ("md2", "american", "2nd Md.", "2nd Maryland Brigade", "Col. Mordecai Gist", "infantry", 602, {}),
    ("muhlenberg", "american", "Muhlenberg", "Muhlenberg's Virginia brigade", "Brig. Gen. Peter Muhlenberg", "infantry", 711, {}),
    ("weedon", "american", "Weedon", "Weedon's Virginia brigade", "Brig. Gen. George Weedon", "infantry", 587, {}),
    # Cornwallis's division: the rear guard under Erskine, then the whole division turned back
    ("dragoons16", "british", "16th L.D.", "16th Light Dragoons", "Lt. Col. William Harcourt", "cavalry", 365, {}),
    ("rangers", "british", "Queen's Rangers", "Queen's American Rangers", "Lt. Col. John Graves Simcoe", "light_infantry", 454, dict(loose=True)),
    ("li1", "british", "1st Light Inf.", "1st Light Infantry battalion", "Lt. Col. Robert Abercromby", "light_infantry", 730, {}),
    ("gren1", "british", "1st Grenadiers", "1st Grenadier battalion", "Lt. Col. William Meadows", "infantry", 761, {}),
    ("gren2", "british", "2nd Grenadiers", "2nd Grenadier battalion; Monckton killed at the hedgerow", "Lt. Col. Henry Monckton (killed)", "infantry", 737, {}),
    ("guards1", "british", "1st Guards", "1st Guards battalion", "Col. Henry Trelawny", "infantry", 502, {}),
    ("guards2", "british", "2nd Guards", "2nd Guards battalion", "Col. Thomas Howard", "infantry", 480, {}),
    ("r42", "british", "42nd", "42nd Foot (Royal Highland Regiment), of Grey's 3rd Brigade; in the Sutfin orchard late in the day", "Lt. Col. Thomas Stirling", "infantry", 639, {}),
    ("bde3", "british", "3rd Brigade", "3rd Brigade, the 15th, 17th and 44th Foot", "Maj. Gen. Charles Grey", "infantry", 1016, {}),
    ("bde4", "british", "4th Brigade", "4th Brigade, the 33rd, 37th, 46th and 64th Foot", "Maj. Gen. Charles Grey", "infantry", 1496, {}),
    ("bde5", "british", "5th Brigade", "5th Brigade, the 7th, 26th and 63rd Foot, in reserve", "Maj. Gen. Alexander Leslie", "infantry", 952, {}),
    ("hessians", "british", "Hessian grenadiers", "Hessian grenadier battalions Linsing, Minnigerode and Lengerke, left as a line to fall back on", "Col. Heinrich von Kospoth", "infantry", 1291, {}),
    ("ra", "british", "Royal Artillery", "Royal Artillery with Cornwallis's division: the ten pieces massed in front of the hedgerow", "Brig. Gen. James Pattison", "artillery", 150, dict(guns=10)),
]

# ---- movement ----
def sec(t): h, m, *s = map(int, t.split(':')); return h * 3600 + m * 60 + (s[0] if s else 0)
def fmt(s): s = int(round(s)); return f"{s // 3600:02d}:{s % 3600 // 60:02d}" + (f":{s % 60:02d}" if s % 60 else "")
def plus(t, mins): return fmt(sec(t) + mins * 60)
def K(t, p, **kw): return dict(t=t, x=round(p[0]), y=round(p[1]), **kw)
def heading(a, b): return round(math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) % 360)
def dv(h): r = math.radians(h); return (math.sin(r), math.cos(r))
def rv(h): r = math.radians(h); return (math.cos(r), -math.sin(r))
def slot(c, h, u, back=0):  # u metres along the right-hand vector of a unit facing h; back metres to its rear
    dx, dy = dv(h); rx, ry = rv(h)
    return (round(c[0] + u * rx - back * dx), round(c[1] + u * ry - back * dy))
def length(pts): return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
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
def road(a, b): return along(ROAD, a, b)
KEYS = {}
def keys(id, ks): KEYS[id] = KEYS.get(id, []) + ks
def last(id): k = KEYS[id][-1]; return (k["x"], k["y"])
def hold(id, t): keys(id, [K(t, last(id))])

ENG, TEN, BRG, CSW, CH = P['englishtown'], P['tennent'], P['bridge'], P['causeway'], P['courthouse']
EDGE_NE, EDGE_NW = (4500, 1950), (-4500, 2900)

# ---- Dickinson's militia: out in front at the West Ravine all night, then off to the left ----
keys("dickinson", [K("04:00", (-250, -360), h=100, state="skirmish"), K("08:00", (-250, -360), state="firing"), K("08:20", (-250, -360), h=290, state="retreat", strength=795),
                   K("08:40", (-700, -60), h=110, state="line"), K("11:00", (-700, -60), state="column")] + go("11:01", "11:40", [(-700, -60), (-1000, 150), (-1250, 220)], 120) + [K("24:00", (-1250, 220))])

# ---- Lee's vanguard: Englishtown to the court house, the clash, the retreat, the rearguard, the rear ----
# The column leaves Englishtown about six and reaches the bridge about eight, where the militia and the Queen's Rangers
# have been firing; it halts there while Lee sorts out whether the enemy is advancing, goes on about a quarter to nine,
# and is over the East Morass by ten, turning north to come at the rear guard on the Middletown road.
def advance(id, camp, t_leave, t_bridge, halt_at, t_on, t_clash, spot, h):
    keys(id, [K("04:00", camp, h=120, state="line"), K(t_leave, camp, state="column")] + go(plus(t_leave, 1), t_bridge, [camp] + road(ENG, BRG) + [halt_at], h=100, state="line") + [K(t_on, halt_at, state="column")]
         + march(plus(t_on, 1), plus(t_clash, -15), [halt_at] + road((-100, -430), CSW)[1:] + [(3000, -400)]) + [K(t_clash, spot, h=h, state="line")])
advance("grayson", (-4150, 2650), "06:00", "07:50", (-150, -400), "08:45", "10:25", (3000, 100), 90)
advance("oswald", (-4300, 2450), "06:05", "07:55", (-220, -330), "08:46", "10:30", (2950, -20), 90)
advance("oswald4", (-4350, 2550), "06:08", "07:58", (-300, -300), "08:47", "10:32", (2900, 220), 90)
advance("durkee", (-4100, 2450), "06:15", "08:05", (-350, -420), "08:50", "10:35", (2900, -120), 90)
advance("wayne", (-4000, 2800), "06:20", "08:10", (-450, -250), "08:55", "10:20", (3400, 300), 70)
advance("scott", (-4250, 2850), "06:30", "08:20", (-600, -200), "09:00", "10:45", (2650, 350), 70)
advance("jackson", (-4400, 2750), "06:40", "08:30", (-700, -140), "09:05", "10:40", (2400, 650), 60)
advance("maxwell", (-4150, 2300), "06:50", "08:40", (-800, -80), "09:10", "10:50", (2600, -150), 90)
# the clash: Wayne attacks the rear guard, the dragoons charge and are shot back, then Clinton's division comes back
keys("wayne", [K("10:30", (3400, 300), state="charge"), K("10:42", (3700, 420), state="firing", strength=975), K("10:55", (3700, 420), strength=960), K("11:05", (3700, 420), h=250, state="retreat"),
               K("11:25", (3100, 0)), K("11:40", (2700, -700), strength=955)])
keys("grayson", [K("10:40", (3000, 100), state="firing"), K("11:00", (3000, 100), strength=590), K("11:08", (3000, 100), h=250, state="retreat")])
keys("durkee", [K("10:45", (2900, -120), state="firing"), K("11:05", (2900, -120), strength=295), K("11:10", (2900, -120), h=250, state="retreat")])
keys("oswald", [K("10:35", (2950, -20), state="firing"), K("11:00", (2950, -20), state="line"), K("11:05", (2950, -20), h=250, state="retreat")])
keys("oswald4", [K("10:40", (2900, 220), state="firing"), K("11:00", (2900, 220), state="line"), K("11:05", (2900, 220), h=250, state="retreat")])
keys("scott", [K("11:00", (2650, 350), h=220, state="retreat"), K("11:30", (2300, -500), strength=1420)])
keys("jackson", [K("11:20", (2400, 650), h=240, state="retreat"), K("11:50", (1600, -400), strength=245)])
keys("maxwell", [K("11:15", (2600, -150), h=240, state="retreat"), K("11:45", (2000, -650), strength=990)])
# the retreat to the Craig-Ker line, which is given up as soon as it is reached, then on to the hill east of the bridge
# and the Point of Woods, where Washington meets Lee and the rearguard turns to fight
def back(id, t_leave, t_ker, ker, t_on, t_stand, stand, h, **kw):
    keys(id, go(t_leave, t_ker, [last(id)] + road(last(id), ker)[1:], 90, moving="retreat") + [K(t_on, ker, state="column")]
         + go(plus(t_on, 1), t_stand, road(ker, stand) + [stand], h, **kw))
back("grayson", "11:09", "12:00", (1000, -600), "12:18", "12:40", (-200, -280), 100)
back("durkee", "11:11", "12:05", (1050, -700), "12:20", "12:42", (-300, -380), 100)
back("oswald4", "11:06", "11:55", (950, -520), "12:15", "12:35", (-240, -330), 100)
back("oswald", "11:06", "11:50", (900, -450), "12:05", "12:55", (-650, 60), 150)
back("wayne", "11:41", "12:00", (1150, -760), "12:22", "12:45", (-85, -560), 90)
back("scott", "11:31", "12:10", (1000, -950), "12:30", "13:40", (-800, 300), 150)
back("jackson", "11:51", "12:12", (950, -380), "12:28", "13:30", (-1600, 1150), 150)
back("maxwell", "11:46", "12:15", (1100, -880), "12:35", "13:35", (-1200, 800), 150)
# the rearguard fight, a quarter to one to half past: two battalions and four guns on the hill east of the bridge,
# pushed back to the hedgerow; Wayne in the Point of Woods; Monckton killed; the last men over the bridge about half past one
def stand(id, t_fire, hill, t_hedge, hedge, t_off, n1, n2, rear, t_rear):
    keys(id, [K(t_fire, hill, state="firing"), K(plus(t_fire, 15), hill, strength=n1), K(t_hedge, hedge, h=90, state="firing"), K(plus(t_hedge, 12), hedge, strength=n2),
              K(t_off, hedge, h=300, state="retreat")] + go(plus(t_off, 1), t_rear, [hedge, BRG, (-900, 300), rear], 150, moving="retreat"))
stand("grayson", "12:45", (-200, -280), "13:05", (-560, -480), "13:28", 580, 570, (-1700, 1050), "14:05")
stand("durkee", "12:47", (-300, -380), "13:06", (-640, -640), "13:29", 285, 275, (-1800, 950), "14:08")
stand("oswald4", "12:45", (-240, -330), "13:04", (-520, -420), "13:25", 50, 45, (-1050, 420), "13:50")
keys("wayne", [K("13:00", (-85, -560), state="firing"), K("13:12", (-85, -560), strength=935), K("13:24", (-85, -560), strength=915), K("13:32", (-85, -560), h=300, state="retreat")]
     + go("13:33", "14:10", [(-85, -560), (-250, -300), BRG, (-900, 300), (-1500, 1000)], 150, moving="retreat"))
keys("oswald", [K("13:00", (-650, 60), state="line")] + go("13:01", "13:30", [(-650, 60), (-1300, 1000)], 150))
keys("scott", [K("13:45", (-800, 300), h=160, state="line")])
# the main line on the Perrine ridge, Stirling's four brigades with Knox's guns in front, faces the hedgerow ground
RIDGE, RH = (-800, 560), 160
# Wayne's evening attack over the bridge with the 3rd Pennsylvania, and Cilley's turn against the 42nd
for id in ("grayson", "durkee", "jackson", "maxwell", "oswald", "oswald4", "scott", "wayne"): hold(id, "24:00")

# ---- Washington's main body: over Englishtown at ten, Tennent by half past eleven, the ridge by one ----
def main_body(id, t_in, t_eng, t_ten, t_line, spot, h, state="line"):
    keys(id, march(t_in, t_eng, [EDGE_NW, ENG]) + march(plus(t_eng, 10), t_ten, road(ENG, TEN)) + go(plus(t_ten, 5), t_line, road(TEN, (-900, 300)) + [spot], h, state))
main_body("learned", "09:30", "10:00", "11:05", "12:30", slot(RIDGE, RH, 450), RH)
main_body("glover", "09:35", "10:05", "11:10", "12:35", slot(RIDGE, RH, 150), RH)
main_body("knox", "09:38", "10:08", "11:15", "12:40", slot(RIDGE, RH, 0, -60), RH)
main_body("huntington", "09:40", "10:10", "11:20", "12:45", slot(RIDGE, RH, -150), RH)
main_body("poor", "09:45", "10:15", "11:25", "12:50", slot(RIDGE, RH, -450), RH)
main_body("cilley", "09:47", "10:17", "11:27", "12:55", slot(RIDGE, RH, -700), RH)
main_body("irvine", "09:50", "10:20", "11:30", "13:00", (-500, 280), RH)
main_body("pa2", "09:55", "10:25", "11:35", "13:05", (-200, 330), RH)
main_body("pa3", "10:00", "10:30", "11:40", "13:10", (-650, 420), RH)
main_body("clark", "10:05", "10:35", "11:45", "13:15", (-700, 900), RH)
main_body("smallwood", "10:10", "10:40", "11:50", "13:20", (-1000, 850), RH)
# Greene's wing goes right from Tennent about half past twelve, round by the West Ravine to Combs Hill by three
for id, t_in, spot, h in (("woodford", "10:15", (-1060, -960), 40), ("duplessis", "10:18", COMBS, 35)):
    keys(id, march(t_in, plus(t_in, 30), [EDGE_NW, ENG]) + march(plus(t_in, 40), "11:55", road(ENG, TEN))
         + go("12:30", "15:00", [TEN, (-1900, 400), (-2050, -400), (-1650, -900), (-1300, -1020), spot], h))
keys("duplessis", [K("15:15", COMBS, state="firing"), K("16:30", COMBS, state="line"), K("24:00", COMBS)])
keys("woodford", [K("24:00", (-1060, -960))])
# Steuben's four brigades wait at Englishtown and are ordered forward at six; they reach Tennent as the sun sets
for id, t_in, spot, rear in (("paterson", "10:20", (-4000, 2450), (-1750, 1250)), ("md2", "10:25", (-4050, 2250), (-1900, 1150)),
                             ("muhlenberg", "10:30", (-3850, 2600), (-1650, 1400)), ("weedon", "10:35", (-3800, 2350), (-1850, 1450))):
    keys(id, march(t_in, plus(t_in, 25), [EDGE_NW, ENG]) + [K(plus(t_in, 30), spot, h=120, state="line"), K("18:00", spot, state="column")]
         + go("18:01", "19:30", [spot] + road(spot, TEN)[1:] + [rear], 150) + [K("24:00", rear)])
# Knox's duel with the British guns, half past one to half past three
keys("knox", [K("13:30", slot(RIDGE, RH, 0, -60), state="firing"), K("14:30", slot(RIDGE, RH, 0, -60), strength=145), K("15:30", slot(RIDGE, RH, 0, -60), state="line"), K("17:00", slot(RIDGE, RH, 0, -60), state="firing"),
              K("17:45", slot(RIDGE, RH, 0, -60), state="line"), K("24:00", slot(RIDGE, RH, 0, -60))])
# Wayne over the bridge at a quarter to five with the 3rd Pennsylvania, against the grenadiers at the Parsonage; repulsed
keys("pa3", [K("16:40", (-650, 420), state="column")] + go("16:41", "16:55", [(-650, 420), BRG, (-330, -300)], 120, moving="charge")
     + [K("17:00", (-330, -300), state="firing"), K("17:06", (-330, -300), strength=420), K("17:10", (-330, -300), h=300, state="retreat", strength=408), K("17:20", (-420, -200), h=120, state="line"), K("24:00", (-420, -200))])
# Cilley's battalion works down from the left, along the brook, onto the 42nd in the Sutfin orchard; the 42nd gives way
keys("cilley", [K("16:55", slot(RIDGE, RH, -700), state="column")] + go("16:56", "17:25", [slot(RIDGE, RH, -700), (100, 900), (350, 650), (150, 380)], 230, state="firing")
     + [K("17:40", (150, 380), strength=345), K("17:50", (150, 380), state="charge"), K("18:00", (-100, 250), state="line", strength=340), K("24:00", (-100, 250))])
# Poor's brigade probes the British right at seven and is halted by sunset
keys("poor", [K("19:00", slot(RIDGE, RH, -450), state="column")] + go("19:01", "19:31", [slot(RIDGE, RH, -450), (0, 500), (300, 420)], 100) + [K("24:00", (300, 420))])
for id in ("learned", "glover", "huntington", "irvine", "pa2", "clark", "smallwood"): hold(id, "24:00")

# ---- Cornwallis's division ----
# In camp east and north-east of the court house at four; the division moves off up the Middletown road from five
# and is clear of the court house by a quarter past nine, leaving Erskine's rear guard on the road.
CAMP = {"guards1": (3300, -900), "guards2": (3450, -1050), "gren1": (3550, -600), "gren2": (3650, -780), "bde3": (3200, -1250), "r42": (3050, -1150), "bde4": (3450, -1400),
        "bde5": (3000, -1600), "hessians": (3750, -350), "ra": (3300, -520), "li1": (3700, -100), "rangers": (3500, 100), "dragoons16": (3400, -220)}
NJ79 = lambda a, b: along(MIDDLETOWN_RD, a, b)
OUT = [("hessians", "05:00", "06:05"), ("bde5", "05:20", "06:30"), ("bde4", "05:40", "06:55"), ("r42", "06:05", "07:15"), ("bde3", "06:15", "07:25"), ("ra", "06:40", "07:40"),
       ("gren2", "07:00", "08:05"), ("gren1", "07:20", "08:20"), ("guards2", "07:45", "08:45"), ("guards1", "08:10", "09:10")]
for id, t0, t1 in OUT:
    keys(id, [K("04:00", CAMP[id], h=40, state="line"), K(t0, CAMP[id], state="column")] + march(plus(t0, 1), t1, [CAMP[id]] + NJ79(CAMP[id], EDGE_NE)[1:] + [EDGE_NE]) + [K(plus(t1, 1), EDGE_NE, state="hidden")])
# Erskine's rear guard: the Rangers push out to the West Ravine and fire on the militia about eight, then come back;
# by a quarter past nine the three units stand on the Middletown road, the last British troops near the court house
keys("rangers", [K("04:00", CAMP["rangers"], h=270, state="skirmish"), K("06:40", CAMP["rangers"], state="column")] + march("06:41", "07:55", [CAMP["rangers"], (3000, -400)] + road(CSW, (-100, -430))[1:])
     + [K("08:00", (-100, -430), h=280, state="firing"), K("08:20", (-100, -430), strength=450), K("08:25", (-100, -430), h=100, state="retreat")]
     + go("08:26", "09:40", [(-100, -430)] + road((-100, -430), CSW)[1:] + [(3300, -400), P['clash_br']], 270, state="skirmish", moving="retreat"))
keys("li1", [K("04:00", CAMP["li1"], h=270, state="line"), K("09:00", CAMP["li1"], state="column")] + go("09:01", "09:15", [CAMP["li1"], (3900, 300)], 270))
keys("dragoons16", [K("04:00", CAMP["dragoons16"], h=270, state="line"), K("09:00", CAMP["dragoons16"], state="column")] + go("09:01", "09:15", [CAMP["dragoons16"], (4000, 650)], 270))
# the clash: Wayne comes on, the dragoons charge and are shot back, the rear guard holds until the division returns
keys("dragoons16", [K("10:35", (4000, 650), h=250, state="charge"), K("10:44", (3800, 500), strength=353), K("10:48", (3800, 500), h=70, state="retreat"), K("11:00", (4050, 700), h=250, state="line")])
keys("li1", [K("10:40", (3900, 300), state="firing"), K("11:00", (3900, 300), strength=720), K("11:10", (3900, 300), state="line")])
keys("rangers", [K("10:40", P['clash_br'], state="firing"), K("11:00", P['clash_br'], strength=448), K("11:10", P['clash_br'], state="skirmish")])
# Clinton turns Cornwallis back between half past ten and half past eleven: Guards on the right and Grenadiers on the
# left in two columns down the Middletown road, the 3rd Brigade sent across the creek to cut the vanguard's retreat,
# the 4th following in line, the 5th in reserve and the Hessian grenadiers left in a line to fall back on
def back_in(id, t_in, t_dep, spot, h, state="line"):
    keys(id, [K(plus(t_in, -1), EDGE_NE, state="hidden"), K(t_in, EDGE_NE, state="column")] + go(plus(t_in, 1), t_dep, NJ79(EDGE_NE, (3849, 500)) + [spot], h, state))
back_in("guards1", "10:45", "11:30", (3500, 500), 250)
back_in("guards2", "10:50", "11:35", (3450, 300), 250)
back_in("gren1", "10:55", "11:40", (3400, 50), 250)
back_in("gren2", "11:00", "11:45", (3350, -150), 250)
back_in("ra", "11:05", "11:45", (3550, 150), 250)
back_in("bde3", "11:10", "12:00", (3000, -1100), 250)
back_in("r42", "11:15", "12:05", (2850, -950), 250)
back_in("bde4", "11:20", "12:10", (3200, -400), 250)
back_in("bde5", "11:30", "12:20", (3400, -700), 250)
back_in("hessians", "11:40", "12:30", (1150, -900), 270)
# The pursuit west: the Guards and Grenadiers cross the Middle Ravine about half past twelve and come at the Point of
# Woods and the hill east of the bridge; the grenadiers carry the hedgerow and Monckton falls leading the 2nd battalion
def pursue(id, t0, t1, pts, h, **kw): keys(id, [K(t0, last(id), state="column")] + go(plus(t0, 1), t1, [last(id)] + pts, h, **kw))
pursue("guards1", "11:35", "12:50", [(2400, -500), (1500, -600), (900, -520), (250, -600)], 270)
pursue("guards2", "11:40", "12:55", [(2300, -650), (1400, -750), (800, -700), (250, -800)], 270)
pursue("gren1", "11:45", "12:58", [(2600, -300), (1800, -450), (1000, -400), (60, -340)], 280)
pursue("gren2", "11:50", "13:03", [(2500, -450), (1700, -550), (950, -480), (0, -470)], 280)
pursue("ra", "11:50", "13:25", [(2600, -400), (1700, -480), (700, -500), (-380, -470)], 340)
pursue("bde4", "12:15", "13:30", [(2400, -550), (1500, -650), (350, -450)], 270)
pursue("bde5", "12:25", "13:45", [(2500, -700), (1600, -800), (900, -350)], 270)
pursue("bde3", "12:05", "13:30", [(2500, -900), (1800, -800), (600, -400)], 270)
pursue("r42", "12:10", "13:35", [(2400, -1000), (1700, -900), (500, -550)], 270)
pursue("li1", "11:15", "13:30", [(3500, -200), (2500, -400), (1600, -500), (300, -300)], 290)
pursue("rangers", "11:15", "13:35", [(3600, 50), (2600, -200), (1700, -350), (500, -250)], 290, state="skirmish")
pursue("dragoons16", "11:30", "13:40", [(3700, 100), (2700, -250), (1800, -400), (700, -300)], 290)
keys("guards1", [K("13:00", (250, -600), state="firing"), K("13:15", (250, -600), strength=490), K("13:20", (250, -600), state="charge"), K("13:32", (-100, -560), state="line", strength=477)])
keys("guards2", [K("13:03", (250, -800), state="firing"), K("13:18", (250, -800), strength=460), K("13:22", (250, -800), state="charge"), K("13:34", (-80, -760), state="line", strength=445)])
keys("gren1", [K("13:00", (60, -340), state="firing"), K("13:10", (60, -340), strength=745), K("13:12", (60, -340), state="charge"), K("13:22", (-330, -380), state="firing", strength=728), K("13:35", (-350, -330), h=300, state="line", strength=716)])
keys("gren2", [K("13:05", (0, -470), state="firing"), K("13:14", (0, -470), strength=720), K("13:16", (0, -470), state="charge"), K("13:26", (-430, -520), state="firing", strength=690), K("13:38", (-430, -520), h=290, state="line", strength=665)])
# the artillery duel, half past one to half past three; Greene's guns on Combs Hill rake the hedgerow and the British
# guns limber up; the right wing crosses the creek toward the Sutfin farm and the American left and is held there
keys("ra", [K("13:30", (-380, -470), state="firing"), K("14:30", (-380, -470), strength=145), K("15:25", (-380, -470), strength=140), K("15:30", (-380, -470), h=100, state="retreat"), K("15:50", (250, -520), h=320, state="line")])
keys("li1", [K("14:00", (300, -300), state="column")] + go("14:01", "14:25", [(300, -300), (350, -150), (300, 150)], 300, state="skirmish") + [K("15:00", (300, 150), strength=715), K("16:30", (300, 150), state="line")])
keys("rangers", [K("14:05", (500, -250), state="column")] + go("14:06", "14:30", [(500, -250), (550, -120), (520, 300)], 300, state="skirmish") + [K("15:00", (520, 300), strength=444), K("16:30", (520, 300), state="line")])
keys("dragoons16", [K("14:10", (700, -300), state="column")] + go("14:11", "14:35", [(700, -300), (750, -150), (720, 100)], 300))
keys("bde3", [K("14:30", (600, -400), state="column")] + go("14:31", "14:55", [(600, -400), (150, -120), (-150, 50)], 320) + [K("15:30", (-150, 50), strength=1004)])
keys("r42", [K("14:35", (500, -550), state="column")] + go("14:36", "15:05", [(500, -550), (100, -100), (-300, 120)], 330) + [K("15:20", (-300, 120), state="firing"), K("16:00", (-300, 120), strength=615), K("16:30", (-300, 120), state="line")])
# Half past four: the 3rd Brigade withdraws and Washington orders an attack. Wayne is repulsed at the Parsonage; the
# 42nd holds the Sutfin orchard against Cilley until about six, then gives way. By five the British are spent.
keys("gren1", [K("16:55", (-350, -330), state="firing"), K("17:08", (-350, -330), strength=706), K("17:15", (-350, -330), state="line")])
keys("gren2", [K("16:55", (-430, -520), state="firing"), K("17:08", (-430, -520), strength=657), K("17:15", (-430, -520), state="line")])
keys("r42", [K("17:25", (-300, 120), state="firing"), K("17:45", (-300, 120), strength=599), K("17:50", (-300, 120), h=110, state="retreat")] + go("17:51", "18:15", [(-300, 120), (100, -120), (600, -250)], 270, moving="retreat"))
# ---- the withdrawal east of the Middle Ravine at dusk, and the march for Middletown at eleven ----
def dusk(id, t0, t1, spot, h=270):
    keys(id, [K(t0, last(id), state="column")] + go(plus(t0, 1), t1, [last(id), spot], h))
dusk("bde3", "16:30", "17:00", (1200, -600)); dusk("li1", "16:35", "17:10", (1300, -250)); dusk("rangers", "16:40", "17:15", (1450, -150), 290); dusk("dragoons16", "16:45", "17:15", (1500, -400))
dusk("gren1", "17:30", "18:10", (1150, -450)); dusk("gren2", "17:35", "18:15", (1200, -600)); dusk("guards1", "17:40", "18:20", (1100, -700)); dusk("guards2", "17:45", "18:25", (1150, -850))
dusk("ra", "17:30", "18:00", (1250, -520)); dusk("bde4", "17:50", "18:30", (1350, -700)); dusk("bde5", "18:00", "18:30", (1550, -550)); dusk("r42", "18:16", "18:45", (1250, -300))
# the rear guard at Ker's house; at eleven the division files off through the court house for Middletown
NIGHT = [("hessians", "23:00"), ("bde5", "23:05"), ("bde4", "23:12"), ("bde3", "23:18"), ("r42", "23:22"), ("ra", "23:26"), ("guards2", "23:30"), ("guards1", "23:34"), ("gren2", "23:38"), ("gren1", "23:42"),
         ("dragoons16", "23:46"), ("rangers", "23:48"), ("li1", "23:50")]
for id, t in NIGHT:
    keys(id, [K(t, last(id), state="column")] + march(plus(t, 1), "24:00", [last(id)] + road(last(id), CH)[1:]))

# ---- assemble ----
assert set(KEYS) == {row[0] for row in OOB}, set(KEYS) ^ {row[0] for row in OOB}
units = []
for id, side, short, name, commander, type, strength, extra in OOB:
    ks = KEYS[id]
    for a, b in zip(ks, ks[1:]):
        assert sec(b["t"]) > sec(a["t"]), (id, a["t"], b["t"])
        moved = (a["x"], a["y"]) != (b["x"], b["y"])
        assert not (moved and sec(b["t"]) - sec(a["t"]) > 3 * 3600), (id, a["t"], b["t"], "a march leg over three hours")
    units.append(dict(id=id, side=side, name=name, short=short, commander=commander, type=type, strength=strength, keys=ks, **extra))

# Chapters: (time, title, text, camera centre, metres across, playback speed, clock time the sources record or None).
# Morning times are Wikipedia's (after Lender and Stone) and the court-martial record's; afternoon times are Wikipedia's
# or inferred, since the witnesses gave durations, not clocks. The heat is Stone's 96°F; no thermometer reading survives.
CHAPTERS = [
    ("04:00", "Monmouth Court House, before dawn", "Clinton has halted his army at the court house since the 26th, headquarters in the Covenhoven house, and sends Knyphausen's division and the 1,500-wagon train off for Middletown about four. Washington followed him from Valley Forge with about 14,000 men; Lee's vanguard, some 4,700 with twelve guns, lies at Englishtown, Dickinson's militia out in front at the West Ravine. Hamilton brought Lee Washington's orders between one and two. Cornwallis's division, some 9,500 men, will follow the train up the Middletown road from five and not clear the court house until a quarter past nine. The day will be clear and, by Stone's reckoning, about 96 degrees.", [-300, 300], 9000, 300, "4 AM"),
    ("06:00", "Lee's advance", "Grayson's detachment forms at daylight and leaves Englishtown about six, once a guide is found; the rest of the vanguard files after it toward Tennent meeting house and the West Ravine. Scott's detachment was ordered to move at five. Lee rides ahead at seven.", [-2300, 1300], 5200, 300, "about 6 AM"),
    ("08:00", "First shots at the bridge", "About eight the Queen's Rangers fire on Dickinson's militia near a bridge over a ravine, which this plan puts at the West Ravine. Grayson comes up in support, and the column halts while Lee sorts out whether the enemy is retreating or advancing. He goes on about a quarter to nine.", [-450, -150], 2400, 60, "about 8 AM"),
    ("10:30", "The first clash", "Over the East Morass and north toward the Middletown road, Lee comes out of the woods about half past ten to find Wayne already engaged with Erskine's rear guard: Simcoe's Rangers, the 16th Light Dragoons and the 1st Light Infantry, about 1,500 men. The dragoons charge and are shot back. Behind them Clinton has turned Cornwallis's whole division round.", [3300, 250], 3000, 30, "about half past 10"),
    ("11:35", "The retreat over the ravines", "The Guards and Grenadiers come back down the road in two columns, the 3rd Brigade crossing the creek to cut the vanguard off, the 4th behind it, the 5th in reserve, the Hessian grenadiers left as a line to fall back on. Scott pulls back south-west over Spotswood Middle Brook, Maxwell after him, Jackson down from the north brook. Lee, with barely half his vanguard still under his hand, falls back toward a line from Craig's house to Ker's, then gives that up too. By noon he is near Ker's house.", [2500, -300], 4200, 60, None),
    ("12:45", "Washington meets Lee", "Washington's main body, over Englishtown at ten, has Stirling's brigades climbing the Perrine ridge when he rides forward and meets the retreat about a quarter to one, by the park's reckoning here on the Rhea farm: 'whence arises this disorder and confusion?' Lender and Stone find the exchange less harsh than tradition has it. Lee is told to hold the enemy while the line forms. The Guards and Grenadiers crossed the Middle Ravine about half past twelve.", [-100, -200], 2600, 30, "about a quarter to 1"),
    ("13:05", "The hedgerow", "Two battalions and four of Oswald's guns stand on the hill east of the bridge and are pushed back to the hedgerow, a fence, Stewart told the court, 'about fifty yards in front'. Wayne's men fire from the Point of Woods. The grenadiers carry the hedgerow with the bayonet and Monckton, leading the 2nd battalion, is killed; he is the highest-ranking British casualty of the day. The rearguard action lasts about half an hour, and Lee is among the last over the bridge at half past one.", [-350, -480], 1700, 20, None),
    ("13:45", "Perrine Hill: the artillery duel", "Knox's ten guns on the ridge and Clinton's ten in front of the hedgerow fire at each other across 1,200 yards of open ground for two hours. Stirling's four brigades, 2,400 men, hold the ridge with the Pennsylvanians and Scott's men in front of them and Lafayette's reserve behind. The light infantry and the Rangers try the American left over the creek and are held. Men drop from the heat on both sides.", [-500, 50], 2600, 120, None),
    ("14:30", "Molly Pitcher", "A surgeon wrote five days later of a patient's story of a woman at a gun; two veterans told of one decades on, one carrying cartridges and one water; Joseph Plumb Martin's memoir of 1830 has her serving a piece. Mary Ludwig Hays is the name most often given. Lender and Stone conclude that very likely several women helped the gun crews that afternoon, and that the legend is an amalgam. The park's marker of 1992 is at a well near Stirling's artillery line, shown here.", [-400, 100], 1900, 120, None),
    ("15:15", "Combs Hill", "Greene, sent right from Tennent at half past twelve, has brought Woodford's brigade and du Plessis's four guns round by the West Ravine onto Combs Hill, about three by Stone and a quarter to four by Lender and Stone. The guns rake the hedgerow from the flank and the British artillery withdraws out of their reach.", [-650, -650], 2300, 60, None),
    ("16:45", "Wayne at the Parsonage", "At half past four Washington learns the 3rd Brigade is withdrawing and orders an attack. Wayne takes the 3rd Pennsylvania, about 400 men, over the bridge against the grenadiers at the Parsonage and its orchard, is repulsed, and falls back to the Parsonage farm. By five, in Washington's words, the British and Hessians are so spent they can do no more.", [-380, -330], 1600, 20, "a quarter to 5"),
    ("17:20", "The British withdrawal", "Cilley's picked New England battalion works down from the left under cover of the brook bottom onto the 42nd Foot in the Sutfin orchard, and the Highlanders give way. The battle ends shortly after five. Clinton pulls his units back across the Middle Ravine to the Craig and Ker farms.", [-50, 0], 2800, 60, "shortly after 5 PM"),
    ("19:00", "Sunset", "Poor's brigade is sent to probe the British right at seven and is halted by sunset, at 7:31, before making contact. Steuben's four brigades, ordered up from Englishtown at six, reach Tennent as the light goes. The armies rest within a mile of each other, the nearest British at Ker's house. Washington's return gives 69 killed, 161 wounded and 140 missing; Clinton's 65 killed, 170 wounded, 64 missing and 59 dead of fatigue. Stone has nearly half the losses on both sides down to the heat, and the Monmouth County historians count 304 British dead buried on the field.", [-200, -100], 5200, 300, "about 7 PM"),
    ("23:00", "In silence", "About eleven, midnight by Washington's report, Clinton files his division off through the court house for Middletown without a drum, and rejoins Knyphausen between eight and nine in the morning. Monckton is buried in the Tennent churchyard. Lee demands a court martial, is tried from 4 July, found guilty on all three charges on 12 August, and suspended for a year.", [2200, -900], 4000, 300, "about 11 PM"),
]
events = [dict(t=t, title=a, text=b, at=at, view=v, speed=s, **({"when": w} if w else {})) for t, a, b, at, v, s, w in CHAPTERS]

battle = dict(
    id="monmouth", name="Battle of Monmouth", date="1778-06-28", dateText="28 June 1778", place="Monmouth Court House (Freehold), New Jersey",
    origin=dict(lat=LAT0, lon=LON0), extent=9000, start="04:00", end="24:00", sunrise="04:29", sunset="19:31", speed=60, lapse=1800, menPerDot=10,
    terrainExaggeration=2, contourInterval=3, trees=dict(density=0.0005), fields=FIELDS, wind=dict(x=0.5, y=0.3), view=dict(x=0, y=-100, width=8800),
    palette=dict(ground="#b0ab86", high="#d8d2aa", tree="rgba(95,80,55,0.42)", field="rgba(236,222,170,0.55)"),
    sides=dict(american=dict(name="Americans (Washington, Lee)", color="#1f55c4", light="#4a83e6", dark="#122c66"),
               british=dict(name="British and Hessians (Clinton, Cornwallis)", color="#c02a1f", light="#e2584a", dark="#5e1510")),
    features=features, units=units, events=events,
    outcome={"result": "Drawn: the Americans held the field, Clinton got his army and train to Sandy Hook", "losses": [
        ["american", "370 by Washington's return: 69 killed, 161 wounded, 140 missing. Lender and Stone think the true figure could have passed 500. The missing are not drawn."],
        ["british", "358 by Clinton's return: 65 killed, 59 dead of fatigue, 170 wounded, 64 missing. The Monmouth County Historical Association counts 304 dead buried on the field and puts the loss at 1,134; 256 Germans deserted on the march."]],
        "note": "Nearly half the casualties on both sides were from the heat, about 96°F by Stone's reckoning. The last general action in the north, and the longest of the war."},
    sources=[
        "Wikipedia, <a href='https://en.wikipedia.org/wiki/Battle_of_Monmouth' target='_blank'>Battle of Monmouth</a> and <a href='https://en.wikipedia.org/wiki/Monmouth_order_of_battle' target='_blank'>Monmouth order of battle</a> (read 23 October 2026), which follow Mark Edward Lender and Garry Wheeler Stone, <i>Fatal Sunday: George Washington, the Monmouth Campaign, and the Politics of Battle</i> (Oklahoma, 2016): the clock times, the strengths and the returns. <i>Fatal Sunday</i> itself and its maps were not consulted.",
        "<i>Proceedings of a General Court-Martial ... for the Trial of Major-General Lee</i> (New York, 1864 reprint of the 1778 record), read in the Internet Archive scan for the testimony of Mercer, Edwards, Lafayette, Wayne, Scott, Grayson, Stewart, Hamilton and the aides: Scott's five o'clock, the halts at the meeting house and the bridge, Wayne's 'five thousand, with twelve pieces of artillery', Stewart's fence 'about fifty yards in front'.",
        "Richard Greenwood, <i>Monmouth Battlefield</i>, National Historic Landmark nomination (National Park Service, 1975): the three ravines, the hedgerow 'from Wemrock Brook almost all the way to Weamaconk Creek' with the parsonage at its north end, the Englishtown road 'slightly to the north of the original', the first clash 'between the east ravine and the road to Middletown', the Craig house '700 yards north of the middle ravine', the battery on Combs Hill.",
        "Garry Wheeler Stone, <a href='https://continentalline.org/CL/?p=1113' target='_blank'>What really happened at the Battle of Monmouth</a> (1995): the Dividing Brook crossed about half past twelve, ten guns a side, Greene on Combs Hill about three, Cilley against the 42nd, the heat 'would reach 96°F', the withdrawal about eleven. Jim Piecuch's review of <i>Fatal Sunday</i>, <i>Michigan War Studies Review</i> (2017): the British company strengths are inaccurate, the Washington-Lee meeting less harsh than tradition.",
        "Michael Adelberg, <a href='https://www.monmouthhistory.org/250' target='_blank'>Dead and wounded after the Battle of Monmouth</a>, Monmouth County Historical Association: the burials, the wounded left at the court house, the heat deaths. <i>Journal of the American Revolution</i>, 'Did Charles Lee disobey Washington's attack order at Monmouth?' (2024): the 27 June and pre-dawn times, Grayson's 1,500 at daylight, the court martial. <i>American Heritage</i>, 'Monmouth' (August 1976): Washington's report.",
        "Terrain: USGS 3DEP elevation at 10 m, sampled to 22.5 m; Freehold borough and the modern roads are left as the DEM shows them. Anchors from OpenStreetMap (ODbL) and GNIS: Englishtown, Tennent church, the Perrine, Sutfin and Craig houses, the hill points, the park's Molly Pitcher well and its Washington-meets-Lee trail, Veterans Park, the Hall of Records. Sunrise and sunset from the NOAA solar formulae for Freehold, local apparent time.",
        "What is reconstructed: the hedgerow, the Parsonage, the Point of Woods, the 1778 bridge, the Rhea farm and Ker's house are placed from the nomination's prose, within 250 to 500 m, and labelled 'about here'. Wemrock Brook and the Middle Ravine, a branch of it, are traced from the DEM, which puts the ravine on a diagonal from the Craig farm toward the brook rather than north-south; OpenStreetMap's Wemrock Brook points did not match the valley and were not used. Of the two 'east ravines' in the sources, this plan takes the driving tour's East Morass on Weamaconk Creek at Veterans Park, since the vanguard's road and Scott's retreat 'south-west across the Spotswood Middle Brook' both cross it; the nomination's McGellaird's Brook reading would put the retreat north of the road where only Jackson's detachment was. Of the two sites for the meeting with Lee, 700 m apart, this plan takes the park's trail on the Rhea farm over the nomination's plaque at the bridge. Every afternoon clock time is Wikipedia's or inferred; the witnesses gave durations. The two-day prelude, Knyphausen's division, Morgan's riflemen at Richmond Mills and the rejoining on 29 June are off the map. Combs Hill's guns stand on the DEM's summit, 230 m north of the GNIS point. Oswald's twelve guns are drawn as eight with the column and the four that stood with the rearguard. Cilley's battalion is drawn apart from the brigades it was picked from.",
    ],
)
json.dump(battle, open(HERE + "battle.json", "w"), indent=1)
print(len(units), "units,", len(events), "events,", sum(u["strength"] for u in units if u["side"] == "american"), "Americans,", sum(u["strength"] for u in units if u["side"] == "british"), "British")
print("Middle Ravine traced:", MIDDLE)
# Which units each chapter's frame holds at its moment, so a caption never names a unit the camera leaves out.
def at(u, t):
    ks = [k for k in u["keys"] if sec(k["t"]) <= sec(t)]
    if not ks: return None
    k = ks[-1]; nxt = [k2 for k2 in u["keys"] if sec(k2["t"]) > sec(t)]
    if k.get("state") == "hidden": return None
    if nxt and (k["x"], k["y"]) != (nxt[0]["x"], nxt[0]["y"]):
        f = (sec(t) - sec(k["t"])) / (sec(nxt[0]["t"]) - sec(k["t"])); return (k["x"] + f * (nxt[0]["x"] - k["x"]), k["y"] + f * (nxt[0]["y"] - k["y"]))
    return (k["x"], k["y"])
for e in events:
    r = e["view"] / 2; inside = []
    for u in units:
        p = at(u, e["t"])
        if p and abs(p[0] - e["at"][0]) <= r and abs(p[1] - e["at"][1]) <= r: inside.append(u["id"])
    print(f"{e['t']} {e['title']}: {' '.join(inside)}")
