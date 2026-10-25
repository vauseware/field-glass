# Builds battles/chippawa/battle.json and fits terrain.json to 1814. Run from the repo root: python3 battles/chippawa/make.py
# Local metres from 43.0545N 79.0360W (x east, y north). The 3.5 km square holds the plain between Street's Creek and
# the Chippawa (Welland) River, the woods on its west, Scott's and Ripley's camps south of the creek, the King's Bridge,
# the tête-de-pont and Riall's works at Chippawa. Every place is kept in latitude and longitude, or in the research
# note's local metres where the note derives it (N below), and converted once. Anchors are OpenStreetMap points and the
# Niagara Parks markers. The King's Bridge, the tête-de-pont, Street's and Ussher's houses, Ussher's lane and the 1814
# wood line are placed from Lossing, Scott and the park's panels, within 100 to 250 m, and labelled "about here".
# Strengths are Drummond's for the British; the American battalions are Scott's 1,377 split by Gardner's casualty return.
import json, math, re
HERE = "battles/chippawa/"
LAT0, LON0 = 43.0545, -79.0360
KX, KY = 111320 * math.cos(math.radians(LAT0)), 111320  # tools/fetch_terrain.py's metres per degree
def M(lat, lon): return (round((lon - LON0) * KX), round((lat - LAT0) * KY))
R_NOTE = 6371009 * math.pi / 180  # the note's equirectangular metres per degree
def N(x, y): return (LAT0 + y / R_NOTE, LON0 + x / (R_NOTE * math.cos(math.radians(LAT0))))  # a place the note gives in its metres
def NL(*pts): return [M(*N(x, y)) for x, y in pts]

# ---- plane geometry ----
def unit(v): L = math.hypot(*v); return (v[0] / L, v[1] / L)
def heading(a, b): return round(math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) % 360)
def seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]; t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)))
    return math.dist(p, (a[0] + t * dx, a[1] + t * dy))
def inside(p, poly):
    c, (x, y) = False, p
    for (xa, ya), (xb, yb) in zip(poly, poly[-1:] + poly[:-1]):
        if (ya > y) != (yb > y) and x < xa + (xb - xa) * (y - ya) / (yb - ya): c = not c
    return c
def point(pts, s):  # the point s metres along a polyline
    for a, b in zip(pts, pts[1:]):
        L = math.dist(a, b)
        if s <= L or b is pts[-1]: t = unit((b[0] - a[0], b[1] - a[1])); return (a[0] + t[0] * s, a[1] + t[1] * s)
        s -= L
def proj(pts, p):  # how far along a polyline its nearest point to p is
    best, run = None, 0
    for a, b in zip(pts, pts[1:]):
        L = math.dist(a, b); f = max(0, min(1, ((p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1])) / (L * L)))
        d = math.dist(p, (a[0] + f * (b[0] - a[0]), a[1] + f * (b[1] - a[1])))
        if best is None or d < best[0]: best = (d, run + f * L)
        run += L
    return best[1]
def stretch(pts, a, b):  # the part of a polyline between the points on it nearest a and b, in that order
    s0, s1 = proj(pts, a), proj(pts, b); lo, hi = min(s0, s1), max(s0, s1); out, run = [point(pts, lo)], 0
    for p, q in zip(pts, pts[1:]):
        run += math.dist(p, q)
        if lo < run < hi: out.append(q)
    out.append(point(pts, hi))
    return out if s0 <= s1 else out[::-1]
def rect(c, h, w, d):  # a rectangle w across heading h and d deep, centred on c
    s, co = math.sin(math.radians(h)), math.cos(math.radians(h))
    return [[round(c[0] + a * co + b * s), round(c[1] - a * s + b * co)] for a, b in [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)]]
def quad(x0, y0, x1, y1): return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
def label_on(p, q, off=0):  # a label rotated along the line p-q at p, `off` metres to its left
    t = unit((q[0] - p[0], q[1] - p[1])); return dict(at=[round(p[0] - t[1] * off), round(p[1] + t[0] * off)], rot=round(math.degrees(math.atan2(t[1], t[0]))))

# ---- places ----
PLACES = {
    # OpenStreetMap and the markers' positions
    'monument': (43.05213, -79.02473), 'creek_mouth': (43.05182, -79.02254), 'slater': (43.05611, -79.02719),
    'kingsbridge_park': (43.06364, -79.04955), 'cummington': (43.05923, -79.05096),
    # from the note's text, within 100 to 250 m
    'kings_bridge': N(-950, 850), 'tete_de_pont': N(-800, 800), 'street': N(1050, -460), 'ussher': N(1000, -250),
}
P = {k: M(*v) for k, v in PLACES.items()}

# ---- lines ----
# Street's Creek on OpenStreetMap's ways, from the south edge round the bend and up the reach behind the shore to its
# mouth. It is too narrow for the 30 m survey, so the DEM does not show it.
CREEK = NL((-624, -1750), (-348, -1460), (56, -1278), (500, -1200), (960, -1118), (1065, -871), (1152, -652), (1115, -331), (1094, -298))
# The river road: the Niagara Parkway from the creek bridge to the Chippawa, then the 1814 leg to the King's Bridge and
# over it into Riall's works. South of the creek it runs along the shore to Fort Erie; the note gives no trace there, so
# it is kept 100 to 150 m inside the DEM's waterline.
ROAD_S = [(1400, -1750), (1360, -1500), (1320, -1200), (1290, -950), (1250, -700), (1200, -520)]
ROAD_N = NL((1121, -391), (1082, -367), (898, -49), (771, 140), (655, 361), (528, 528), (399, 613), (176, 665), (-151, 688), (-551, 759), (-870, 857), (-950, 850))
BRIDGE_N = (P['kings_bridge'][0] - 10, P['kings_bridge'][1] + 120)  # the north bank, across the 1814 channel
ROAD = ROAD_S + ROAD_N + [BRIDGE_N, (-1000, 1040)]
LANE = NL((1040, -240), (200, -240))  # Ussher's farm lane, west from the river road just north of the creek
BRIDGES = [(ROAD_N[-1], BRIDGE_N)]  # dry over water
STREETS_BRIDGE = M(*N(1115, -380))

# The 1814 wood line: Lossing's three-quarter mile from the river at the creek, narrowing to Scott's third at the north.
WOOD_LINE = NL((-300, -1300), (-300, 300), (-100, 650))
PLAIN = NL((-300, -1300), (-300, 300), (-169, 530), (450, 530), (750, 530), (1350, -300), (1250, -900), (960, -1150), (56, -1300))
ROADSIDE = NL((-1000, 800), (-1000, 900), (-550, 810), (-150, 740), (500, 700), (500, 590), (-110, 590), (-550, 700), (-950, 770))
CAMPS = [(-100, -1320), (1000, -1170), (1550, -1100), (1550, -1750), (-100, -1750)]
STRIP = NL((-100, 530), (450, 530), (450, 590), (-100, 590))  # the strip of trees that hid Riall's march

# ---- terrain: the 1814 plain ----
# The Copernicus surface model reads today's park woodland on the plain, and the trees along the creek and over the
# camps, as a plateau up to 12 m high. Inside the plain and the camps any cell above 180 m is set to 176, the plain's
# own level. The woods west of the 1814 wood line keep their canopy, which reads as wooded ground. Idempotent.
T = json.load(open(HERE + "terrain.json"))
COLS, SP = T["cols"], T["spacing"]; HALF = COLS * SP / 2
def cells(poly):  # the DEM cells whose centres lie inside a polygon, by scanline
    out = set()
    for r in range(COLS):
        y = HALF - (r + 0.5) * SP
        xs = sorted(xa + (xb - xa) * (y - ya) / (yb - ya) for (xa, ya), (xb, yb) in zip(poly, poly[1:] + poly[:1]) if (ya > y) != (yb > y))
        for x0, x1 in zip(xs[::2], xs[1::2]):
            out.update(range(r * COLS + max(0, math.ceil((x0 + HALF) / SP - 0.5)), r * COLS + min(COLS - 1, math.floor((x1 + HALF) / SP - 0.5)) + 1))
    return out
CLAMP = NL((-350, -1300), (-350, 320), (-130, 660), (700, 640), (1350, -300), (1250, -900), (960, -1150), (56, -1300))
flat = cells(CLAMP) | cells(CAMPS)
Z = [176.0 if i in flat and v > 180 else v for i, v in enumerate(T["z"])]
if Z != T["z"]: T["z"] = Z; json.dump(T, open(HERE + "terrain.json", "w"), separators=(",", ":"))
WATER = 170.5  # the Niagara and the Chippawa read 169 to 170 m; the plain 174 to 178
def z(p):
    c, r = int((p[0] + HALF) / SP), int((HALF - p[1]) / SP)
    return T["z"][r * COLS + c] if 0 <= c < COLS and 0 <= r < COLS else 999
def wet(p): return z(p) <= WATER and not any(seg_dist(p, a, b) < 15 for a, b in BRIDGES)

# ---- ground ----
FIELDS = [quad(150, -1000, 850, -420), quad(450, -120, 850, 380), quad(-200, -1000, 100, -500), quad(-200, -100, 300, 350)]
features = [
    dict(type="creek", name="Street's Creek", **label_on((300, -1240), (700, -1170), -40), pts=CREEK),
    dict(type="road", name="the river road", pts=ROAD, **label_on((-300, 712), (-500, 748), 40)),
    dict(type="road", pts=[M(*N(1050, -360)), M(*N(1160, -400))]),  # the bridge over Street's Creek
    dict(type="road", name="Ussher's lane (about here)", pts=LANE, **label_on(LANE[1], LANE[0], 30)),
    dict(type="works", name="Fort Chippawa and Riall's works (about here)", pts=[(-1130, 975), (-880, 990), (-850, 1080)], at=[-1210, 1190]),
    dict(type="redoubt", name="tête-de-pont (about here)", poly=rect(P['tete_de_pont'], 160, 60, 40), at=[P['tete_de_pont'][0] + 40, P['tete_de_pont'][1] - 70]),
    dict(type="camp", poly=quad(-1150, 1000, -900, 1100)),
    dict(type="camp", name="Scott's camp", poly=quad(500, -1600, 1050, -1350), at=[775, -1640]),
    dict(type="camp", name="Ripley's camp", poly=quad(0, -1700, 450, -1450), at=[225, -1730]),
    dict(name="King's Bridge (about here)", at=[P['kings_bridge'][0] - 60, P['kings_bridge'][1] - 60]),
    dict(name="Chippawa", at=[P['cummington'][0], P['cummington'][1] - 60]),
    dict(name="Street's house (about here)", at=[P['street'][0] - 60, P['street'][1] - 50]),
    dict(name="Ussher's (about here)", at=[P['ussher'][0] - 90, P['ussher'][1] - 40]),
    dict(name="the plain", at=[300, -650]),
    dict(name="the woods", at=[-900, -400]), dict(name="the woods", at=[-1000, 300]),
    dict(name="Battlefield monument (2001)", at=[P['monument'][0] - 120, P['monument'][1] - 60]),
    dict(name="Navy Island", at=[1650, 400]),
    dict(name="Niagara River", **label_on((1300, -700), (1500, -100))),
    dict(name="Chippawa (Welland) River", **label_on((-1700, 50), (-1450, 380))),
    dict(name="to Fort Erie, 16 miles", at=[1250, -1700]),
]
for f in features:
    if "at" in f and f.get("name") and "River" not in f["name"]: assert not wet(f["at"]), (f["name"], "a label in the water")

# ---- order of battle: (id, side, short, name, commander, type, strength, extra) ----
OOB = [
    # Brown's Left Division: Scott's brigade, the artillery, Ripley's brigade and Porter's volunteers and warriors
    ("r9", "american", "9th and 22nd", "1st battalion, 9th US Infantry, with a detachment of the 22nd", "Maj. Henry Leavenworth", "infantry", 577, {}),
    ("r11", "american", "11th", "2nd battalion, 11th US Infantry", "Col. John Campbell, then Maj. John McNeil", "infantry", 400, {}),
    ("r25", "american", "25th", "3rd battalion, 25th US Infantry", "Maj. Thomas Jesup", "infantry", 400, {}),
    ("towson", "american", "Towson", "Towson's company, US Artillery: three guns", "Capt. Nathan Towson", "artillery", 90, dict(guns=3)),
    ("ritchie", "american", "Ritchie", "Ritchie's company, US Artillery", "Capt. John Ritchie", "artillery", 75, dict(guns=3)),
    ("hall", "american", "Hall", "Hall's 12-pounder of Biddle's company", "Lt. Hall", "artillery", 25, dict(guns=1)),
    ("harris", "american", "Harris", "Harris's troop, US Light Dragoons", "Capt. Samuel Harris", "cavalry", 70, {}),
    ("r21", "american", "21st", "21st US Infantry, with the 19th's detachment (Ripley's brigade)", "Brig. Gen. Eleazer Ripley; Maj. Vose", "infantry", 680, {}),
    ("r23", "american", "23rd", "23rd US Infantry (Ripley's brigade)", "Maj. Daniel McFarland", "infantry", 400, {}),
    ("fenton", "american", "Pennsylvanians", "Fenton's 5th Pennsylvania Volunteers (Porter's brigade)", "Lt. Col. James Fenton; Brig. Gen. Peter B. Porter", "militia", 300, dict(loose=True)),
    ("sixnations", "american", "Six Nations", "Six Nations and allied warriors (Porter's brigade)", "Capt. Pollard; Red Jacket", "riflemen", 400, dict(loose=True)),
    # Riall's Right Division
    ("royals", "british", "Royal Scots", "1st battalion, 1st (Royal Scots) Foot", "Lt. Col. John Gordon", "infantry", 500, {}),
    ("r100", "british", "100th", "100th (Prince Regent's) Foot", "Lt. Col. the Marquis of Tweeddale", "infantry", 460, {}),
    ("r8", "british", "8th (King's)", "1st battalion, 8th (King's) Foot", "Maj. Thomas Evans", "infantry", 400, {}),
    ("lights", "british", "Light companies", "Light companies of the Royal Scots and the 100th", "Lt. Col. Thomas Pearson", "light_infantry", 150, dict(loose=True)),
    ("lincoln", "british", "2nd Lincoln", "2nd Lincoln Militia", "Lt. Col. Thomas Dickson", "militia", 200, dict(loose=True)),
    ("norton", "british", "Grand River", "Grand River Six Nations", "Capt. John Norton", "riflemen", 200, dict(loose=True)),
    ("western", "british", "Western Indians", "Western Indians", "Capt. Colvin", "riflemen", 100, dict(loose=True)),
    ("ra24", "british", "Royal Artillery", "Royal Artillery: two light 24-pounders and a 5.5-inch howitzer", "Capt. James Mackonochie", "artillery", 40, dict(guns=3)),
    ("ra6", "british", "6-pounders", "Royal Artillery: three 6-pounders", "Capt. James Mackonochie", "artillery", 30, dict(guns=3)),
    ("ld19", "british", "19th Dragoons", "19th Light Dragoons", "Maj. Robert Lisle", "cavalry", 70, {}),
]
BASE = {row[0]: row for row in OOB}

# ---- the clock: 5 July 1814, local mean time ----
def sec(t): h, m, *s = map(int, t.split(':')); return h * 3600 + m * 60 + (s[0] if s else 0)
def fmt(s): s = int(round(s)); return f"{s // 3600:02d}:{s % 3600 // 60:02d}" + (f":{s % 60:02d}" if s % 60 else "")
def plus(t, mins): return fmt(sec(t) + mins * 60)
START, END = "05:00", "19:45"

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
    have += ks
def last(id): k = KEYS[id][-1]; return (k["x"], k["y"])
def at(id, t, **kw): keys(id, [K(t, last(id), **kw)])  # a change in place
def appear(id, t, p, state="line", **kw): keys(id, [K(t, p, state=state, **kw)])

# Where each unit stands at five in the morning: Scott's brigade in its camp behind the creek, Ripley's beside it, the
# British behind their works at Chippawa, and the militia and warriors who sniped at the pickets along the creek.
# Porter's brigade is still on the road from Buffalo.
DAWN = dict(
    r9=((900, -1450), 0), r11=((760, -1450), 0), r25=((620, -1450), 0), towson=((1000, -1400), 0), harris=((850, -1560), 0),
    r21=((300, -1560), 0), r23=((130, -1600), 0), ritchie=((400, -1660), 0), hall=((330, -1660), 0),
    royals=((-1250, 1150), 150), r100=((-1350, 1030), 150), r8=((-1050, 1060), 150), lights=((-1320, 1120), 150),
    norton=((-1400, 1200), 150), ra24=((-960, 1010), 160), ra6=((-1100, 1000), 160), ld19=((-1250, 1000), 150),
    lincoln=((300, -1040), 180), western=((700, -1000), 200),
)
for id, (p, h) in DAWN.items(): appear(id, START, p, h=h)
appear("fenton", "12:00", ROAD_S[0], "column", h=0); appear("sixnations", "12:04", ROAD_S[0], "column", h=0)

assert set(KEYS) == set(BASE), set(KEYS) ^ set(BASE)
for id in KEYS:
    if carried(id, "state") != "hidden" and sec(KEYS[id][-1]["t"]) < sec(END): at(id, END)

# ---- assemble and check ----
units = []
TOP = {"infantry": 6, "light_infantry": 6, "militia": 6, "riflemen": 6, "artillery": 6, "cavalry": 15}  # km/h, the fastest any leg may go
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
        for f in (i / 20 for i in range(1, 20)):
            q = (a["x"] + f * (b["x"] - a["x"]), a["y"] + f * (b["y"] - a["y"]))
            assert not wet(q), (id, a["t"], b["t"], q, "a leg through the water")
    state = None
    for k in ks:
        state = k.get("state", state)
        assert state == "hidden" or not wet((k["x"], k["y"])), (id, k["t"], (k["x"], k["y"]), "afloat")
    units.append(dict(id=id, side=side, name=name, short=short, commander=commander, type=type, strength=strength, keys=ks, **extra))

events = []

battle = dict(
    id="chippawa", name="Battle of Chippawa", date="1814-07-05", dateText="5 July 1814", place="Chippawa, on the Niagara River, Upper Canada (Ontario)",
    origin=dict(lat=LAT0, lon=LON0), extent=3500, start=START, end=END, sunrise="04:26", sunset="19:42", speed=30, lapse=1800, menPerDot=5,
    water=WATER, terrainExaggeration=3, contourInterval=1, trees=dict(density=0.003, clear=[PLAIN, ROADSIDE, CAMPS]), fields=FIELDS,
    wind=dict(x=0.5, y=0.4), view=dict(x=0, y=0, width=3500),
    sides=dict(american=dict(name="Americans (Brown, Scott)", color="#27497f", light="#6f8fc4", dark="#12254a"),
               british=dict(name="British, Canadians and allies (Riall)", color="#b3331f", light="#d87a68", dark="#5a150c")),
    features=features, units=units, events=events,
    outcome={"result": "American victory: Riall's line beaten on the plain and driven back over the Chippawa", "losses": [
        ["american", "328 by Gardner's return: 60 killed, 249 wounded and 19 missing. Scott's three battalions lost 260 of them and the artillery 20; Porter's Pennsylvanians 12 and the warriors 23. The 19th's 7 and the 23rd's 1 are not drawn; nor are the missing."],
        ["british", "515 by the Montreal return of 13 July: 148 killed, 321 wounded and 46 missing. The Royal Scots lost 213 and the 100th 204; the 2nd Lincoln 43, the heaviest loss of any Canadian militia unit in one action of the war. Later counts give 108 dead. The missing are not drawn."]],
        "note": "Brown's first report counted four hundred British killed and wounded left on the field; Drummond wrote of about 500, a third of the men. The clock times are officers' watches, good to about a quarter of an hour."},
    sources=[
        "E. A. Cruikshank, ed., <a href='https://archive.org/details/cihm_05281' target='_blank'><i>The Documentary History of the Campaign upon the Niagara Frontier in 1814</i></a>, Part I (Lundy's Lane Historical Society, 1896), pp. 31-52: Riall's report of 6 July and his abstract of casualties; Drummond's letters of 9 and 10 July with the regimental strengths; Brown's reports of 6 and 7 July; Scott's and Hindman's reports; Gardner's return of the American loss; the Montreal General Order of 13 July; and eyewitness letters from the Ontario Messenger, a captain of Fenton's Pennsylvanians and a US artillery officer.",
        "William Hamilton Merritt's journal, in William Wood, ed., <a href='https://archive.org/details/selectbritishdoc0003will' target='_blank'><i>Select British Documents of the Canadian War of 1812</i></a>, vol. III (Champlain Society, 1926-28), pp. 613-616: Riall's march at three, the King's arriving that morning, the Western Indians and the 2nd Lincoln in the woods.",
        "Winfield Scott, <a href='https://archive.org/details/memoirsoflieutge01scotrich' target='_blank'><i>Memoirs of Lieut.-General Scott</i></a>, vol. I (1864), ch. X: the bridge, the nine guns, 'Buffalo militia', the obtuse angle and the final charge at sixty or seventy paces. Written fifty years after.",
        "Benson J. Lossing, <a href='https://archive.org/details/pictorialfieldbo00lossuoft' target='_blank'><i>The Pictorial Field-Book of the War of 1812</i></a> (1868), pp. 805-812: the plain three-quarters of a mile wide, Street's and Ussher's houses, the tête-de-pont, Porter's force and the thunder-gust.",
        "Niagara Parks Commission, the six interpretive panels and the monument at Chippawa Battlefield Park (2001), after Donald Graves, <i>Red Coats and Grey Jackets</i> (1994), as transcribed at the <a href='https://www.hmdb.org/m.asp?m=49399' target='_blank'>Historical Marker Database</a>: the dawn sniping, Ussher's lane, the 50 m advance and the 75 m range.",
        "Wikipedia, <a href='https://en.wikipedia.org/wiki/Battle_of_Chippawa' target='_blank'>Battle of Chippawa</a> (read 24 October 2026), for Graves's brigade strengths of 3 July and Hendry's revised British losses; The Canadian Encyclopedia; warhistory.org.",
        "Terrain: " + T["source"] + ". Resampled to 10 m. The surface model's modern woodland over the 1814 plain and the camps is flattened to the plain's level. The Chippawa's mouth is today's widened hydro channel, not the 1814 river. Places from OpenStreetMap contributors (ODbL): Street's Creek, the Niagara Parkway, the battlefield park and monument, Kingsbridge Park on the site of Fort Chippawa.",
        "What is reconstructed: the King's Bridge and the tête-de-pont from Lossing and the modern street plan, within 250 m; Street's and Ussher's houses and Ussher's lane from Lossing's sketches and the park's panels, within 100 m; the 1814 wood line from Lossing's three-quarter mile and Scott's 'third narrower'; the camps; the river road south of the creek. American battalion strengths are Scott's 1,377 split by each battalion's casualties; Graves's returns would settle them. Clock times between the recorded ones are placed from the sources' durations.",
    ],
)
json.dump(battle, open(HERE + "battle.json", "w"), indent=1)
print(len(units), "units,", len(events), "events,", len(features), "features,", sum(u["strength"] for u in units if u["side"] == "american"), "Americans,", sum(u["strength"] for u in units if u["side"] == "british"), "British")
