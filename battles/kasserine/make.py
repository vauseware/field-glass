# Builds battles/kasserine/battle.json. Run from the repo root: python3 battles/kasserine/make.py
# Local metres from 35.3750N 8.6400E (x east, y north), the Bahiret Foussana basin between Kasserine Pass and Thala. The 52 km
# square holds Kasserine (17845,-22954), the pass narrows (9984,-13358), Djebel Semmama and Djebel Chambi, the Thala road to
# Thala (2805,21908), the Tébessa road across the basin to Djebel el Hamra (-18145,-5210), Bou Chebka pass (-9984,-13915) and
# Haïdra (-17636,21106). Every place is kept in latitude and longitude below and converted once. Towns, the two roads and the
# Oued el Hatab come from OpenStreetMap; the summits from the Copernicus DEM. The named hills (1191, 974, 712, 704, Zebbeus, Point
# 732, the Thala ridges, the Hamra passes) are DEM knolls fitted to Howe's prose, good to a kilometre or two; see the research notes.
import json, math, datetime as dt
HERE = "battles/kasserine/"
LAT0, LON0 = 35.375, 8.640
KX, KY = 111320 * math.cos(math.radians(LAT0)), 111320  # tools/fetch_terrain.py's metres per degree
def M(lat, lon): return (round((lon - LON0) * KX), round((lat - LAT0) * KY))

D = lambda d, hm: f"1943-02-{d:02d} {hm}"
def sec(s): return dt.datetime.strptime(s, "%Y-%m-%d %H:%M").timestamp()
def fmt(ts): return dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
def K(t, p, **kw): return dict(t=t, x=p[0], y=p[1], **kw)
def hd(p, q): return round(math.degrees(math.atan2(q[0] - p[0], q[1] - p[1])) % 360)
def off(p, dx, dy): return (p[0] + dx, p[1] + dy)
def march(t0, t1, pts, **kw):  # keys along a path, times spread by distance; heading follows the path
    d = [0]
    for i in range(1, len(pts)): d.append(d[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    out = []
    for i, p in enumerate(pts):
        j = min(i + 1, len(pts) - 1); q = pts[j] if j != i else pts[i - 1]
        h = hd(p, q) if j != i else out[-1]["h"]
        out.append(K(fmt(sec(t0) + (sec(t1) - sec(t0)) * d[i] / d[-1]), p, h=h, **({"state": "column"} if i == 0 else {}), **(kw if i == 0 else {})))
    return out

# ---- terrain ----
T = json.load(open(HERE + "terrain.json"))
COLS, SP = T["cols"], T["spacing"]; HALF = COLS * SP / 2
def z(x, y):
    c, r = int((x + HALF) / SP), int((HALF - y) / SP)
    return T["z"][r * COLS + c] if 0 <= c < COLS and 0 <= r < COLS else 999

# ---- geography: places ----
PLACES = {
    # OpenStreetMap and the DEM summits
    'kasserine': (35.1688, 8.8366), 'chambi': (35.2069, 8.6813), 'semmama': (35.3309, 8.7848), 'foussana': (35.3497, 8.6256),
    'thala': (35.5718, 8.6709), 'haidra': (35.5646, 8.4457), 'fork': (35.2416, 8.7470), 'thala_rd_hatab': (35.2539, 8.7465),
    'bend': (35.3415, 8.7156),
    # DEM knolls fitted to Howe's descriptions; about a kilometre, the Hamra passes and Bou Chebka two
    'narrows': (35.255, 8.750), 'tebessa_rd_hatab': (35.2541, 8.7226), 'zebbeus': (35.2483, 8.7176), 'hill712': (35.2554, 8.7562),
    'hill704': (35.290, 8.730), 'hill974': (35.3255, 8.7308), 'hill1191': (35.277, 8.768), 'point732': (35.2986, 8.6042),
    'hamra': (35.3282, 8.4401), 'hamra_centre': (35.3405, 8.41), 'hamra_north': (35.372, 8.4625), 'bou_chebka': (35.25, 8.53),
    'ridge1': (35.4617, 8.7137), 'ridge_leic': (35.545, 8.685), 'irwin155': (35.572, 8.655), 'irwin105': (35.548, 8.672),
    # from the narrative, within a few kilometres
    'rommel_cp': (35.20, 8.80), 'dak_bivouac': (35.17, 8.75), 'se_entrance': (35.215, 8.790),
}
P = {k: M(*v) for k, v in PLACES.items()}

# ---- geography: lines (OpenStreetMap; the Tébessa road west of 8.515 E and the Haïdra track are drawn from the narrative) ----
THALA_RD = [(35.1745, 8.7943), (35.2416, 8.7470), (35.2539, 8.7465), (35.2586, 8.7482), (35.2657, 8.7452), (35.2787, 8.7392), (35.2929, 8.7375),
            (35.3059, 8.7302), (35.3200, 8.7211), (35.3415, 8.7156), (35.4617, 8.7137), (35.5718, 8.6709), (35.5890, 8.6638), (35.606, 8.655)]
TEBESSA_RD = [(35.2416, 8.7470), (35.2472, 8.7380), (35.2541, 8.7226), (35.2560, 8.7154), (35.2639, 8.7059), (35.2814, 8.6795), (35.2946, 8.6566),
              (35.3060, 8.6371), (35.3210, 8.6035), (35.3287, 8.5649), (35.3403, 8.5383), (35.3499, 8.5151), (35.372, 8.4625), (35.382, 8.358)]
HAIDRA_TRACK = [(35.5646, 8.4457), (35.47, 8.452), (35.372, 8.4625)]
BOU_CHEBKA_RD = [(35.3060, 8.6371), (35.28, 8.58), (35.25, 8.53), (35.146, 8.37)]
KASSERINE_ROADS = [[(35.1745, 8.7943), (35.1688, 8.8366), (35.18, 8.922)], [(35.1688, 8.8366), (35.142, 8.83)]]  # to Sbeïtla and to Fériana
HATAB = [(35.4202, 8.4795), (35.3542, 8.5873), (35.3174, 8.6512), (35.2697, 8.7279), (35.2539, 8.7465), (35.2392, 8.7579), (35.2289, 8.7951),
         (35.2126, 8.8371), (35.2032, 8.8696), (35.195, 8.922)]
L = lambda pts: [M(*p) for p in pts]

units = []
def unit(id, short, side, name, commander, type, strength, keys, **extra):
    units.append(dict(id=id, side=side, name=name, short=short, commander=commander, type=type, strength=strength, keys=keys, **extra))
al = lambda *a, **k: unit(a[0], a[1], "allied", *a[2:], **k)
ax = lambda *a, **k: unit(a[0], a[1], "axis", *a[2:], **k)

T0 = D(19, "06:00")
SE = P['se_entrance']                                   # where the Kasserine road enters the pass, below Hill 1191's eastern spurs
INNER = P['tebessa_rd_hatab']                           # the inner defile on the Tébessa road, under Zebbeus
HAMRA_FOOT = M(35.335, 8.470)                           # the east foot of Djebel el Hamra, where the pass's stragglers were formed into companies
BC_RIDGE = M(35.272, 8.535)                             # the ridge north of Bou Chebka pass, where the 33d FA stood on 22 Feb
NORTH_EDGE, EAST_EDGE, SOUTH_EDGE, WEST_EDGE = M(35.606, 8.655), M(35.18, 8.922), M(35.142, 8.83), M(35.382, 8.358)
def hide(keys, t): return keys + [K(t, (keys[-1]["x"], keys[-1]["y"]), state="hidden")]

# ---- Stark Force in the pass, 19-20 February ----
# Recorded: 1/26 astride the Thala road about two miles north-west of the fork, Co A on Hill 1191; the 19th Engineers from the Hatab
# through Hill 712 and across the Tébessa road to Zebbeus; the guns behind; Co I/13 and the 805th in reserve. Inferred: where each
# cut-off party went after dusk on the 20th (Howe: west across the Foussana valley or north to Thala).
def cut_off(p, n_dusk, n_end, dest=HAMRA_FOOT, via=None, t_out=D(20, "18:30"), t_in=D(21, "08:00")):  # the pocket on Semmama empties overnight
    path = [p] + ([via] if via else []) + [dest]
    return [K(D(20, "17:30"), p, strength=n_dusk)] + march(t_out, t_in, path, strength=n_end) + [K(fmt(sec(t_in) + 300), dest, state="line", h=100)]
THALA_LINE = M(35.268, 8.745)
al("i26_1", "1/26 Inf", "1st Battalion, 26th Infantry (less Company A), astride the Thala road about two miles north-west of the fork; Col. Stark's own regiment", "Col. Alexander N. Stark Jr. (Stark Force)", "infantry", 650,
   [K(T0, THALA_LINE, h=150, state="line"), K(D(19, "12:30"), THALA_LINE, state="firing"), K(D(19, "18:15"), THALA_LINE, state="line", strength=620),
    K(D(20, "08:30"), THALA_LINE, state="firing"), K(D(20, "13:00"), THALA_LINE, strength=560)] + cut_off(THALA_LINE, 500, 440, via=M(35.33, 8.69)), loose=True)
H1191 = P['hill1191']
def on_1191(id, short, name, n, t_up, p):  # Company A, 26th and Company L, 39th on the hill: cut off the first night, lost in the second
    keys = ([K(T0, p, h=140, state="line")] if t_up == T0 else march(fmt(sec(t_up) - 2 * 3600), t_up, [M(35.3415, 8.7156), M(35.272, 8.750), p]) + [K(fmt(sec(t_up) + 300), p, state="line", h=140)])
    keys += [K(D(19, "19:00"), p, state="firing"), K(D(19, "21:30"), off(p, -500, 400), state="line", h=120, strength=round(n * 0.7)), K(D(20, "08:30"), off(p, -500, 400), state="firing")]
    keys += cut_off(off(p, -500, 400), round(n * 0.5), round(n * 0.35), dest=M(35.46, 8.705), via=M(35.35, 8.74), t_in=D(21, "06:00"))
    al(id, short, name, "", "infantry", n, keys, loose=True)
on_1191("a26", "A/26", "Company A, 26th Infantry, on Hill 1191, the key to the Semmama side; its commander was briefly captured in the night of 19–20 February", 150, T0, H1191)
on_1191("l39", "L/39", "Company L, 39th Infantry, sent up to Hill 1191 with Company A on the afternoon of the 19th", 150, D(19, "16:00"), off(H1191, 400, -300))
def engineers(id, short, name, n, p, h, path_out, t_out):
    keys = [K(T0, p, h=h, state="line"), K(D(19, "15:30"), p, state="firing"), K(D(19, "18:15"), p, state="line", strength=n - 30),
            K(D(20, "08:30"), p, state="firing"), K(D(20, "11:30"), p, strength=n - 110), K(fmt(sec(t_out) - 300), p, state="retreat", h=hd(p, path_out[0]))]
    keys += march(t_out, D(21, "07:30"), [p] + path_out + [HAMRA_FOOT], strength=n - 130)[1:] + [K(D(21, "07:35"), HAMRA_FOOT, state="line", h=100)]
    al(id, short, name, "Col. Anderson T. W. Moore (19th Engineers)", "infantry", n, keys, loose=True)
engineers("eng19e", "19th Engr", "19th Combat Engineer Regiment, its right half: from the Hatab through Hill 712 to the Tébessa road. Its command post was overrun before noon on the 20th", 550, M(35.2545, 8.740), 140,
          [M(35.2639, 8.7059), M(35.2946, 8.6566), M(35.33, 8.60)], D(20, "13:30"))
engineers("eng19w", "19th Engr", "19th Combat Engineer Regiment, its left half: across the Tébessa road to Djebel Zebbeus (Hill 812). Howe calls the whole line 'almost three miles' long", 550, M(35.2515, 8.722), 140,
          [M(35.2639, 8.7059), M(35.2946, 8.6566), M(35.32, 8.60)], D(20, "14:30"))
GUNS33 = M(35.270, 8.733)
al("fa33", "33d FA", "Two batteries of the 33d Field Artillery Battalion, 105 mm howitzers, behind the line; pulled back early on the afternoon of the 20th and found on the ridge north of Bou Chebka pass on the 22nd, where Battery C lost five howitzers", "", "artillery", 200,
   [K(T0, GUNS33, h=140, state="line"), K(D(19, "12:30"), GUNS33, state="firing", fire=0.5), K(D(19, "18:15"), GUNS33, state="line"), K(D(20, "08:30"), GUNS33, state="firing", fire=0.5), K(D(20, "13:00"), GUNS33, state="line")] +
   march(D(20, "13:10"), D(20, "16:30"), [GUNS33, M(35.2639, 8.7059), M(35.2946, 8.6566), M(35.3060, 8.6371), M(35.28, 8.58), BC_RIDGE])[1:] +
   [K(D(20, "16:35"), BC_RIDGE, state="line", h=120), K(D(22, "07:10"), BC_RIDGE, state="firing", h=90), K(D(22, "08:30"), BC_RIDGE, state="line", strength=140), K(D(22, "16:00"), BC_RIDGE, state="firing"), K(D(22, "18:00"), BC_RIDGE, state="line")], guns=8)
FR75 = M(35.259, 8.736)
al("fr75", "French 75s", "A battery of towed French 75s of the 67th African Artillery, with Stark Force; it fired until its ammunition ran out on the 20th and the crews disabled the guns", "", "artillery", 80,
   [K(T0, FR75, h=140, state="line"), K(D(19, "12:30"), FR75, state="firing", fire=0.5), K(D(19, "18:15"), FR75, state="line"), K(D(20, "08:30"), FR75, state="firing", fire=0.5), K(D(20, "13:30"), FR75, state="line"), K(D(20, "13:40"), FR75, state="hidden")], guns=4)
TD805 = M(35.279, 8.736)
al("td805", "805th TD", "805th Tank Destroyer Battalion, 75 mm guns on half-tracks, Stark's reserve 'to protect the rear'; five of its destroyers came out with Gore Force at dusk on the 20th. Its strength is not recorded", "", "armor", 12,
   [K(T0, TD805, h=150, state="line"), K(D(20, "13:00"), M(35.262, 8.742), state="firing", h=150), K(D(20, "16:30"), M(35.262, 8.742), strength=8), K(D(20, "17:30"), M(35.262, 8.742), strength=5, state="retreat", h=330)] +
   march(D(20, "18:00"), D(21, "01:00"), [M(35.262, 8.742), P['hill704'], P['bend'], M(35.44, 8.714)])[1:] + [K(D(21, "01:05"), M(35.44, 8.714), state="line", h=180)])
I13 = M(35.259, 8.714)
al("i13", "I/13 AR", "Company I, 13th Armored Regiment, eight medium tanks in reserve near the Tébessa road; astride it at the inner defile by midday on the 20th, where a platoon was overrun at dusk", "", "armor", 8,
   [K(T0, I13, h=150, state="line"), K(D(20, "11:30"), I13, state="column", h=hd(I13, INNER)), K(D(20, "12:00"), off(INNER, 200, 300), state="firing", h=140), K(D(20, "17:30"), off(INNER, 200, 300), strength=3),
    K(D(20, "18:15"), off(INNER, 200, 300), state="retreat", h=300)] + march(D(20, "18:30"), D(21, "07:00"), [off(INNER, 200, 300), M(35.2639, 8.7059), M(35.2946, 8.6566), M(35.3210, 8.6035), HAMRA_FOOT])[1:] + [K(D(21, "07:05"), HAMRA_FOOT, state="line", h=100)])
CENTRE = M(35.262, 8.757)
al("i39_3", "3/39 Inf", "3rd Battalion, 39th Infantry (Companies I and K): Company I to the heights in the centre, Company K split between the flanks, on the afternoon of the 19th", "", "infantry", 450,
   march(D(19, "12:30"), D(19, "15:00"), [P['bend'], M(35.3059, 8.7302), M(35.272, 8.750), CENTRE]) + [K(D(19, "15:05"), CENTRE, state="line", h=140), K(D(19, "16:00"), CENTRE, state="firing"), K(D(19, "18:15"), CENTRE, state="line", strength=430),
    K(D(20, "08:30"), CENTRE, state="firing"), K(D(20, "13:00"), CENTRE, strength=380)] + cut_off(CENTRE, 330, 270, via=M(35.33, 8.70)), loose=True)
AI6_3 = M(35.274, 8.758)
al("ai6_3", "3/6 AI", "3rd Battalion, 6th Armored Infantry, put under Stark early on the 20th; it climbed toward Hill 1191 and was cut off on Semmama at dusk", "", "infantry", 600,
   march(D(20, "04:00"), D(20, "07:00"), [P['bend'], M(35.3059, 8.7302), M(35.282, 8.745), AI6_3]) + [K(D(20, "07:05"), AI6_3, state="line", h=120), K(D(20, "10:00"), M(35.276, 8.763), state="firing", h=110), K(D(20, "17:00"), M(35.276, 8.763), strength=470)] +
   cut_off(M(35.276, 8.763), 470, 420, dest=M(35.455, 8.708), via=M(35.35, 8.745), t_in=D(21, "06:30")), loose=True)
TD894 = M(35.2814, 8.6795)
al("td894", "894th TD", "894th Tank Destroyer Battalion, brought up early on the 20th for a counterattack that never came; with Combat Command B on Djebel el Hamra from the 21st. Its strength is not recorded", "Lt. Col. Charley P. Eastburn", "armor", 12,
   march(D(20, "05:00"), D(20, "08:00"), [WEST_EDGE, M(35.372, 8.4625), M(35.3499, 8.5151), M(35.3210, 8.6035), TD894]) + [K(D(20, "08:05"), TD894, state="line", h=120), K(D(20, "14:00"), M(35.263, 8.705), state="firing", h=130),
    K(D(20, "16:30"), M(35.263, 8.705), strength=10), K(D(20, "17:00"), M(35.263, 8.705), state="retreat", h=300)] +
   march(D(20, "17:15"), D(21, "06:00"), [M(35.263, 8.705), M(35.2946, 8.6566), M(35.3210, 8.6035), M(35.3499, 8.5151), M(35.345, 8.462)])[1:] + [K(D(21, "06:05"), M(35.345, 8.462), state="line", h=100)])

# ---- Gore Force, 20 February: eleven tanks, a motor company and a battery, from the 26th Armoured Brigade ----
GORE = M(35.287, 8.737)
GORE_IN = [M(35.36, 8.715), P['bend'], M(35.3059, 8.7302), GORE]
def gore(id, short, name, type, n, dx, dy, n_end, **x):
    p, f = off(GORE, dx, dy), off(M(35.279, 8.742), dx, dy)
    keys = march(D(20, "02:00"), D(20, "04:00"), [off(q, dx, dy) for q in GORE_IN]) + [K(D(20, "04:05"), p, state="line", h=150), K(D(20, "10:00"), p, state="column", h=hd(p, f)), K(D(20, "10:30"), f, state="line", h=150),
            K(D(20, "13:00"), f, state="firing"), K(D(20, "16:30"), f, strength=round((n + n_end) / 2)), K(D(20, "17:45"), f, strength=n_end), K(D(20, "18:00"), f, state="retreat", h=340)]
    keys += march(D(20, "18:10"), D(21, "01:00"), [f, off(P['hill704'], dx, dy), P['bend'], M(35.445, 8.713)])[1:] + [K(D(21, "01:05"), M(35.445, 8.713), state="line", h=180)]
    al(id, short, name, "Lt. Col. A. C. Gore", type, n, keys, **x)
gore("gore", "Gore Force", "Gore Force's eleven tanks, from the 26th Armoured Brigade: they fought in the north-west corner of the pass 'until their last tank was destroyed'", "armor", 11, 0, 0, 1)
gore("gore_inf", "Gore's company", "Gore Force's motor company (Howe writes '10th Battalion, Royal Buffs'; the brigade's motor battalion was the 10th Rifle Brigade), with its anti-tank guns", "infantry", 150, -500, 300, 90, loose=True)
gore("gore_bty", "Gore's battery", "Gore Force's field battery", "artillery", 80, -300, 900, 70, guns=4)

# ---- The 26th Armoured Brigade and Nickforce on the Thala road, 20-22 February ----
# Recorded: fifty tanks, mostly Valentines (Atkinson); six Crusaders lost in the morning fog of the 21st; the first ridge held until
# 1600 at the cost of fifteen tanks; the second line for over an hour; through the Leicesters about 1900; 21 tanks by midnight;
# five or more lost in the dawn counterattack of the 22nd. Inferred: how those losses fell between the two regiments.
RIDGE2 = M(35.50, 8.700)
MELEE = M(35.551, 8.681)
def bde26(id, short, name, n, dx, fog, first, second, night, dawn, dawn_out):
    thala, south, r1, r2, m = off(M(35.565, 8.676), dx, 0), off(M(35.43, 8.714), dx, 0), off(P['ridge1'], dx, 0), off(RIDGE2, dx, 0), off(MELEE, dx, 0)
    keys = [K(T0, thala, h=180, state="line"), K(D(20, "10:00"), thala, state="column", h=180)] + march(D(20, "10:00"), D(20, "13:00"), [thala, south])[1:] + [K(D(20, "13:05"), south, state="line", h=180),
            K(D(21, "05:30"), south, state="column", h=0), K(D(21, "06:00"), r1, state="line", h=180), K(D(21, "07:30"), r1, strength=n - fog), K(D(21, "09:30"), r1, state="firing"), K(D(21, "16:00"), r1, strength=n - fog - first),
            K(D(21, "16:10"), r1, state="retreat", h=0), K(D(21, "16:40"), r2, state="firing", h=180), K(D(21, "17:50"), r2, strength=n - fog - first - second), K(D(21, "18:00"), r2, state="retreat", h=0),
            K(D(21, "19:00"), off(P['ridge_leic'], dx, 200), state="column"), K(D(21, "19:20"), m, state="firing", h=180), K(D(21, "22:00"), m, strength=night), K(D(21, "22:10"), m, state="line")]
    if dawn: keys += [K(D(22, "06:20"), m, state="charge", h=180), K(D(22, "06:40"), off(m, 0, -1200), state="firing", h=180), K(D(22, "07:30"), off(m, 0, -1200), strength=dawn_out, state="retreat", h=0), K(D(22, "08:00"), m, state="line", h=180)]
    keys += [K(D(23, "07:30"), m)]
    al(id, short, name, "Brig. Charles Dunphie (26th Armoured Brigade)", "armor", n, keys)
bde26("lancers", "17/21 Lancers", "17th/21st Lancers (less a squadron), 26th Armoured Brigade: Valentines and some Crusaders. Six light Crusaders were knocked out in the morning fog of the 21st", 25, -600, 6, 8, 2, 9, False, 9)
bde26("lothians", "2 Lothians", "2nd Lothians and Border Horse, 26th Armoured Brigade: Valentines. Some of the brigade's remaining tanks counterattacked just before dawn on the 22nd and lost five or more", 25, 600, 0, 7, 3, 12, True, 7)
BUFFS = M(35.455, 8.709)
al("buffs", "10 RB", "The 26th Armoured Brigade's motor battalion (less Gore's company), on the Thala road with the tanks", "", "infantry", 400,
   [K(T0, M(35.568, 8.678), h=180, state="line")] + march(D(20, "10:30"), D(20, "13:30"), [M(35.568, 8.678), M(35.44, 8.713)])[1:] + [K(D(20, "13:35"), M(35.44, 8.713), state="line", h=180),
    K(D(21, "06:00"), BUFFS, state="line", h=180), K(D(21, "10:00"), BUFFS, state="firing"), K(D(21, "16:00"), BUFFS, strength=370, state="retreat", h=0), K(D(21, "17:00"), off(RIDGE2, 0, 300), state="firing", h=180),
    K(D(21, "18:00"), off(RIDGE2, 0, 300), state="retreat", h=0, strength=350), K(D(21, "19:00"), M(35.552, 8.676), state="line", h=180), K(D(21, "19:20"), M(35.552, 8.676), state="firing"), K(D(21, "22:00"), M(35.552, 8.676), state="line", strength=320)], loose=True)
LEIC = P['ridge_leic']
al("leic", "2/5 Leicesters", "2nd/5th Battalion, Leicestershire Regiment, on 'the last ridge south of Thala' from the 21st. About 300 were taken prisoner that night; Atkinson has the battalion muster forty able-bodied men afterwards", "Brig. Cameron Nicholson (Nickforce)", "infantry", 800,
   [K(D(21, "06:00"), LEIC, h=180, state="line"), K(D(21, "19:00"), LEIC, state="firing"), K(D(21, "22:00"), LEIC, state="line", strength=480), K(D(22, "06:20"), LEIC, state="firing"), K(D(22, "08:00"), LEIC, state="line", strength=460),
    K(D(23, "07:30"), LEIC)], loose=True)
NICK_GUNS = M(35.556, 8.676)
al("nick_arty", "Nickforce guns", "Nickforce's field and anti-tank batteries behind the Leicesters: F Battery, 12th (HAC) Regiment RHA, a troop of the 71st and a battery each of the 23rd Field and 58th Anti-Tank Regiments", "Brig. Cameron Nicholson (Nickforce)", "artillery", 250,
   [K(D(21, "06:00"), NICK_GUNS, h=180, state="line"), K(D(21, "11:00"), NICK_GUNS, state="firing", fire=0.5), K(D(21, "22:30"), NICK_GUNS, state="line"), K(D(22, "06:20"), NICK_GUNS, state="firing", fire=0.5), K(D(22, "15:00"), NICK_GUNS, state="line"),
    K(D(23, "07:30"), NICK_GUNS)], guns=12)
def irwin(id, short, name, n, guns, p, t_in, dt_h):  # the 9th Division Artillery: over 800 miles in four days, into Thala at 8 PM on the 21st, emplaced in the early hours of the 22nd
    keys = march(t_in, fmt(sec(t_in) + 2 * 3600), [NORTH_EDGE, M(35.59, 8.664), off(P['thala'], 300, 400)]) + [K(fmt(sec(t_in) + 2 * 3600 + 300), off(P['thala'], 300, 400), state="line", h=180)]
    t_up = D(22, "02:00")
    keys += [K(t_up, off(P['thala'], 300, 400), state="column", h=hd(off(P['thala'], 300, 400), p)), K(fmt(sec(t_up) + dt_h * 3600), p, state="line", h=180), K(D(22, "07:00"), p, state="firing", fire=0.6), K(D(22, "15:30"), p, state="line"),
             K(D(23, "07:30"), p)]
    al(id, short, name, "Brig. Gen. S. LeRoy Irwin (9th Division Artillery)", "artillery", n, keys, guns=guns)
irwin("irwin155", "34th FA", "34th Field Artillery Battalion, twelve 155 mm howitzers, emplaced along the road west of Thala; with the 105s and the cannon companies, 48 guns and 2,200 men that fired 1,904 rounds on 22–23 February", 300, 12, P['irwin155'], D(21, "18:00"), 1.0)
irwin("irwin105", "60th & 84th FA", "60th and 84th Field Artillery Battalions, twenty-four 105 mm howitzers, about 3,000 yards south of the 155s; the twelve 75s of the 47th and 60th Infantry's cannon companies went in with them", 600, 24, P['irwin105'], D(21, "18:15"), 1.5)

# ---- Combat Command B on Djebel el Hamra and the 1st Infantry Division at Bou Chebka, 21-22 February ----
# Recorded: CCB down the dirt road from Haïdra in the night of 20-21, on the ridge's eastern face and in its passes by morning,
# 2/13 in hull defilade; the Stukas and the guns at 1630; 2/16 at the crossroads east of Hamra and Bou Chebka pass; the
# counterattack at 1600 on the 22nd. Inferred: CCB's tank count (Howe gives none) and the exact ground each battalion held.
HAMRA_E = M(35.355, 8.455)
CCB_IN = [P['haidra'], M(35.47, 8.452), P['hamra_north']]
def counter(p, q, t0=D(22, "16:00")):  # the 1600 counterattack on the 22nd: forward to q, fire, and stand there
    return [K(t0, p, state="column", h=hd(p, q)), K(fmt(sec(t0) + 5400), q, state="firing", h=100), K(D(22, "18:30"), q, state="line")]
al("ar13_2", "2/13 AR", "2nd Battalion, 13th Armored Regiment (with Companies G and I), Combat Command B's tanks, 'in hull defilade astride the enemy's path' on Djebel el Hamra. Howe gives no count; II Corps had 99 medium tanks running on the evening of the 20th", "Brig. Gen. Paul McD. Robinett (CCB)", "armor", 40,
   march(D(20, "22:00"), D(21, "07:00"), CCB_IN + [HAMRA_E]) + [K(D(21, "07:05"), HAMRA_E, state="line", h=110), K(D(21, "16:30"), HAMRA_E, state="firing"), K(D(21, "18:30"), HAMRA_E, state="line", strength=38)] +
   counter(HAMRA_E, M(35.318, 8.565)) + [K(D(23, "06:30"), M(35.318, 8.565), state="column", h=120), K(D(23, "07:30"), M(35.305, 8.61))])
AI6_2 = M(35.312, 8.455)
al("ai6_2", "2/6 AI", "2nd Battalion, 6th Armored Infantry, Combat Command B, on the southern end of Djebel el Hamra; the DAK's envelopment struck it near Bou Chebka pass at daylight on the 22nd", "Brig. Gen. Paul McD. Robinett (CCB)", "infantry", 700,
   march(D(20, "22:30"), D(21, "08:00"), CCB_IN + [M(35.345, 8.445), AI6_2]) + [K(D(21, "08:05"), AI6_2, state="line", h=110), K(D(21, "23:00"), AI6_2, state="column", h=hd(AI6_2, M(35.285, 8.515))), K(D(22, "01:30"), M(35.285, 8.515), state="line", h=120),
    K(D(22, "07:10"), M(35.285, 8.515), state="firing"), K(D(22, "12:00"), M(35.285, 8.515), strength=650)] + counter(M(35.285, 8.515), M(35.292, 8.568)), loose=True)
AFA = M(35.348, 8.432)
al("afa27", "27th & 68th AFA", "27th and 68th Armored Field Artillery Battalions, 105 mm self-propelled, in the Hamra passes; their fire stopped the DAK 'about four miles short' of the ridge on the 21st", "Brig. Gen. Paul McD. Robinett (CCB)", "artillery", 500,
   march(D(20, "23:00"), D(21, "08:30"), CCB_IN + [AFA]) + [K(D(21, "08:35"), AFA, state="line", h=110), K(D(21, "16:30"), AFA, state="firing", fire=0.6), K(D(21, "18:30"), AFA, state="line"), K(D(22, "07:30"), AFA, state="firing", fire=0.4),
    K(D(22, "09:30"), AFA, state="line"), K(D(22, "16:00"), AFA, state="firing", fire=0.6), K(D(22, "18:30"), AFA, state="line")], guns=24)
RECON13 = M(35.31, 8.58)
al("recon13", "Recon/13 AR", "Reconnaissance Company, 13th Armored Regiment, out in the basin ahead of Combat Command B; it met the 33d Reconnaissance Battalion about eight miles east of Hamra before dawn on the 21st", "", "light_infantry", 120,
   march(D(20, "23:30"), D(21, "01:30"), [P['hamra_north'], M(35.34, 8.53), RECON13]) + [K(D(21, "01:35"), RECON13, state="line", h=110), K(D(21, "03:00"), RECON13, state="skirmish"), K(D(21, "05:30"), RECON13, state="retreat", h=290, strength=115),
    K(D(21, "07:30"), M(35.345, 8.48), state="line", h=110), K(D(23, "07:30"), M(35.345, 8.48))], loose=True)
I16_2 = M(35.298, 8.503)
al("i16_2", "2/16 Inf", "2nd Battalion, 16th Infantry, 1st Infantry Division, with Senegalese troops, at the crossroads east of Djebel el Hamra and Bou Chebka pass; Company G went north at midnight to cover the 33d FA", "Lt. Col. Joseph B. Crawford", "infantry", 800,
   march(D(21, "07:00"), D(21, "10:00"), [WEST_EDGE, M(35.36, 8.42), M(35.32, 8.47), I16_2]) + [K(D(21, "10:05"), I16_2, state="line", h=110), K(D(22, "07:10"), I16_2, state="firing", h=100), K(D(22, "12:00"), I16_2, strength=740)] +
   counter(I16_2, M(35.283, 8.562)), loose=True)

# ---- Kampfgruppe DAK: the pass on 19-20 February, Djebel el Hamra on the 21st, Bou Chebka on the 22nd ----
# Recorded: the 33d Recon's failed surprise at daybreak; 35-40 truckloads unloading at 1015; the two Panzer Grenadier battalions;
# Hill 974 about noon; the Tébessa road attack at 1530 and five tanks in the minefield; Hill 1191 after dark; the 0830 assault;
# the 1630 side-by-side attack; Buelowius' main force out of the pass at 1400 on the 21st; the night envelopment to Bou Chebka;
# the 1600 counterattack and the Bersaglieri overtaken near Hill 732. Inferred: every tank count and the headcounts.
def to_hamra(p, fight, back, t_out=D(21, "14:00"), t_fight=D(21, "16:30"), n_fight=None, bc=None, n_bc=None, back2=None, n_back2=None, n_end=None):
    # out of the pass along the Tébessa road on the afternoon of the 21st, pushed back at dusk, round by the south in the night to Bou Chebka pass, back into the pass in the night of 22-23
    road = [q for q in [M(35.2639, 8.7059), M(35.2946, 8.6566), M(35.3060, 8.6371)] if q[0] < fight[0]]
    keys = march(t_out, t_fight, [p] + road + [fight]) + [K(fmt(sec(t_fight) + 300), fight, state="firing", h=280), K(D(21, "18:00"), fight, state="retreat", h=120, **({"strength": n_fight} if n_fight else {})), K(D(21, "19:30"), back, state="line", h=280)]
    if bc:
        keys += march(D(22, "01:00"), D(22, "06:30"), [back, M(35.27, 8.60), bc]) + [K(D(22, "07:00"), bc, state="firing", h=290), K(D(22, "15:30"), bc, state="line", **({"strength": n_bc} if n_bc else {})),
                 K(D(22, "16:30"), bc, state="retreat", h=100), K(D(22, "18:00"), back2 or back, state="line", h=280, **({"strength": n_back2} if n_back2 else {}))]
    keys += march(D(22, "23:00"), D(23, "05:00"), [back2 or back, M(35.2946, 8.6566), M(35.2639, 8.7059), off(INNER, 400, -200)]) + [K(D(23, "05:05"), off(INNER, 400, -200), state="line", h=300, **({"strength": n_end} if n_end else {}))]
    return keys
ax("recon33", "33d Recon", "33d Reconnaissance Battalion, Kampfgruppe DAK: 'too small' to take the pass by surprise at daybreak on the 19th; it led the move on Djebel el Hamra at 0200 on the 21st with a few Italian tanks", "Generalmajor Karl Buelowius (Kampfgruppe DAK)", "light_infantry", 400,
   march(D(19, "06:00"), D(19, "07:00"), [SE, M(35.238, 8.760)]) + [K(D(19, "07:05"), M(35.238, 8.760), state="skirmish", h=320), K(D(19, "08:30"), M(35.232, 8.768), state="line", h=320, strength=385),
    K(D(20, "16:30"), M(35.232, 8.768), state="column", h=hd(M(35.232, 8.768), M(35.262, 8.712))), K(D(20, "19:00"), M(35.262, 8.712), state="line", h=300)] +
   march(D(21, "02:00"), D(21, "04:30"), [M(35.262, 8.712), M(35.2946, 8.6566), M(35.3060, 8.6371), off(P['point732'], 0, 400)])[1:] + [K(D(21, "04:35"), off(P['point732'], 0, 400), state="skirmish", h=280), K(D(21, "05:30"), off(P['point732'], 0, 400), state="line", h=280),
    K(D(21, "16:30"), off(P['point732'], 0, 400), state="firing"), K(D(21, "18:00"), off(P['point732'], 0, 400), state="retreat", h=120, strength=370), K(D(21, "19:30"), M(35.29, 8.655), state="line", h=280),
    K(D(22, "22:30"), M(35.29, 8.655), state="column", h=140)] + march(D(22, "22:30"), D(23, "03:30"), [M(35.29, 8.655), M(35.2639, 8.7059), M(35.245, 8.738)])[1:] + [K(D(23, "03:35"), M(35.245, 8.738), state="line", h=300)], loose=True)
def menton(id, short, name, n, p_unload, climb, night, n_night, day2, t_day2, fight, back, bc, n_bc, back2, n_end, **x):
    keys = [K(D(19, "10:15"), p_unload, h=310, state="column"), K(D(19, "12:00"), p_unload, state="line", h=310), K(D(19, "12:15"), p_unload, state="column", h=hd(p_unload, climb)), K(D(19, "13:30"), climb, state="skirmish", h=300),
            K(D(19, "15:30"), climb, state="firing"), K(D(19, "18:15"), climb, state="line", strength=n - 30), K(D(19, "18:45"), climb, state="column", h=hd(climb, night)), K(D(19, "20:30"), night, state="firing", h=270),
            K(D(19, "21:30"), night, state="line", strength=n_night), K(D(20, "08:30"), night, state="firing"), K(D(20, "13:00"), night, strength=n_night - 40), K(fmt(sec(t_day2) - 1800), night, state="charge", h=hd(night, day2)),
            K(t_day2, day2, state="firing", h=290), K(D(20, "18:30"), day2, state="line", strength=n_night - 70)] + to_hamra(day2, fight, back, n_fight=n_night - 90, bc=bc, n_bc=n_bc, back2=back2, n_end=n_end)
    ax(id, short, name, "Oberst Menton (Panzer Grenadier Regiment Afrika)", "infantry", n, keys, loose=True, **x)
menton("menton1", "I/PzGren Afrika", "1st Battalion, Panzer Grenadier Regiment Afrika, Group Menton: up the eastern spurs of Semmama on the 19th, over the centre of the pass on the 20th, to Djebel el Hamra on the 21st and round by Bou Chebka on the 22nd. Headcounts are not recorded", 600,
       off(SE, -300, 400), M(35.262, 8.775), M(35.268, 8.762), 540, M(35.260, 8.750), D(20, "16:30"), M(35.312, 8.595), M(35.297, 8.632), M(35.266, 8.548), 440, M(35.288, 8.645), 420)
menton("menton2", "II/PzGren Afrika", "2nd Battalion, Panzer Grenadier Regiment Afrika, Group Menton: a detachment of it reached Hill 1191 after dark on the 19th", 600,
       off(SE, 300, 900), M(35.265, 8.790), off(H1191, 300, -200), 550, M(35.272, 8.752), D(20, "17:00"), M(35.322, 8.588), M(35.305, 8.628), M(35.258, 8.565), 460, M(35.296, 8.640), 440)
ROMMEL_BNS = M(35.250, 8.724)
ax("menton3", "Rommel's battalions", "The 'nearly two battalions' of infantry Rommel added to Group Menton on the morning of the 20th; they went along the Tébessa road onto Djebel Zebbeus at 1630, and a battalion of them reached Point 732 at 1530 on the 21st", "Generalmajor Karl Buelowius (Kampfgruppe DAK)", "infantry", 1000,
   march(D(20, "11:00"), D(20, "13:00"), [SE, M(35.236, 8.752)]) + [K(D(20, "13:05"), M(35.236, 8.752), state="firing", h=300), K(D(20, "16:00"), M(35.236, 8.752), state="charge", h=300), K(D(20, "16:30"), ROMMEL_BNS, state="firing", h=300),
    K(D(20, "18:30"), off(P['zebbeus'], 200, 300), state="line", h=300, strength=940)] + to_hamra(off(P['zebbeus'], 200, 300), M(35.296, 8.612), M(35.288, 8.648), t_fight=D(21, "15:30"), n_fight=910, bc=M(35.262, 8.580), n_bc=860, back2=M(35.28, 8.660), n_end=850), loose=True)
STOTTEN_IN = M(35.243, 8.741)
ax("stotten", "I/8 Pz Regt", "Group Stotten: 1st Battalion, 8th Panzer Regiment, the DAK's tanks. Five were lost in the minefield on the Tébessa road on the 19th; on the 20th they finished Gore Force. Its count is not recorded", "Major Stotten", "armor", 25,
   march(D(19, "14:30"), D(19, "15:30"), [SE, STOTTEN_IN]) + [K(D(19, "15:35"), STOTTEN_IN, state="firing", h=300), K(D(19, "17:30"), STOTTEN_IN, strength=20), K(D(19, "18:15"), STOTTEN_IN, state="retreat", h=140)] +
   march(D(19, "18:30"), D(19, "20:30"), [STOTTEN_IN, SE, P['dak_bivouac']])[1:] + [K(D(19, "20:35"), P['dak_bivouac'], state="line", h=300)] +
   march(D(20, "13:00"), D(20, "14:30"), [P['dak_bivouac'], SE, P['fork'], off(INNER, 600, -500)])[1:] + [K(D(20, "14:35"), off(INNER, 600, -500), state="firing", h=300), K(D(20, "16:30"), off(INNER, 600, -500), state="column", h=hd(INNER, M(35.278, 8.742))),
    K(D(20, "17:00"), M(35.276, 8.743), state="firing", h=340), K(D(20, "18:30"), off(P['hill704'], 300, -400), state="line", h=330, strength=18)] +
   to_hamra(off(P['hill704'], 300, -400), M(35.318, 8.582), M(35.300, 8.635), n_fight=17, bc=M(35.268, 8.560), n_bc=16, back2=M(35.290, 8.650), n_back2=15))
CENTAURO = M(35.185, 8.78)
ax("centauro", "Centauro tanks", "The Centauro Division's tank battalion, Italian M14s, which joined the DAK in the night of 19–20 February and pursued five miles down the Tébessa road on the 20th and 'found no one'. Its count is not recorded", "", "armor", 20,
   march(D(19, "23:30"), D(20, "02:00"), [SOUTH_EDGE, P['kasserine'], CENTAURO]) + [K(D(20, "02:05"), CENTAURO, state="line", h=310)] +
   march(D(20, "14:00"), D(20, "15:30"), [CENTAURO, SE, P['fork'], off(INNER, 300, -700)])[1:] + [K(D(20, "15:35"), off(INNER, 300, -700), state="firing", h=300), K(D(20, "16:30"), off(INNER, 300, -700), state="column", h=300)] +
   march(D(20, "16:30"), D(20, "17:30"), [off(INNER, 300, -700), M(35.2639, 8.7059), M(35.2946, 8.6566)])[1:] + [K(D(20, "19:00"), M(35.267, 8.703), state="line", h=300, strength=19)] +
   march(D(21, "02:00"), D(21, "04:30"), [M(35.267, 8.703), M(35.2946, 8.6566), M(35.3060, 8.6371), off(P['point732'], 600, -300)])[1:] + [K(D(21, "04:35"), off(P['point732'], 600, -300), state="firing", h=280), K(D(21, "05:30"), off(P['point732'], 600, -300), state="line", h=280)] +
   to_hamra(off(P['point732'], 600, -300), M(35.322, 8.575), M(35.300, 8.645), n_fight=18, bc=M(35.272, 8.572), n_bc=17, back2=M(35.295, 8.655)))
BERSAG = M(35.19, 8.80)
ax("bersag", "5th Bersaglieri", "5th Bersaglieri Battalion, up from Fériana in the night of 19–20 February; overtaken near Hill 732 by Combat Command B's tanks on the 22nd with the loss of 'many vehicles and supplies'", "", "infantry", 600,
   march(D(19, "23:00"), D(20, "02:00"), [SOUTH_EDGE, P['kasserine'], BERSAG]) + [K(D(20, "02:05"), BERSAG, state="line", h=310)] +
   march(D(20, "16:30"), D(20, "18:30"), [BERSAG, SE, P['fork'], M(35.252, 8.716)])[1:] + [K(D(20, "18:35"), M(35.252, 8.716), state="line", h=300)] +
   march(D(21, "14:30"), D(21, "17:00"), [M(35.252, 8.716), M(35.2639, 8.7059), M(35.2946, 8.6566), M(35.304, 8.603)])[1:] + [K(D(21, "17:05"), M(35.304, 8.603), state="firing", h=280), K(D(21, "18:00"), M(35.304, 8.603), state="retreat", h=120), K(D(21, "19:30"), M(35.292, 8.660), state="line", h=280)] +
   march(D(22, "01:30"), D(22, "07:00"), [M(35.292, 8.660), M(35.275, 8.61), M(35.272, 8.572)])[1:] + [K(D(22, "07:05"), M(35.272, 8.572), state="firing", h=290), K(D(22, "16:00"), M(35.272, 8.572), state="retreat", h=90),
    K(D(22, "17:00"), off(P['point732'], 0, -700), state="rout", h=120, strength=470), K(D(22, "19:00"), M(35.283, 8.672), state="line", h=280)] +
   march(D(22, "23:00"), D(23, "04:30"), [M(35.283, 8.672), M(35.2639, 8.7059), M(35.240, 8.748)])[1:] + [K(D(23, "04:35"), M(35.240, 8.748), state="line", h=300)], loose=True)
DAK_GUNS = M(35.226, 8.777)
ax("dak_arty", "DAK guns", "Kampfgruppe DAK's artillery: the corps guns, dual-purpose 88s and 'a battery of new German rocket projectors', the Nebelwerfer, whose first barrage on American troops opened the 0830 assault on the 20th", "Generalmajor Karl Buelowius (Kampfgruppe DAK)", "artillery", 500,
   [K(D(19, "11:00"), DAK_GUNS, h=310, state="line"), K(D(19, "15:30"), DAK_GUNS, state="firing", fire=0.6), K(D(19, "18:15"), DAK_GUNS, state="line"), K(D(20, "08:30"), DAK_GUNS, state="firing", fire=0.8), K(D(20, "18:00"), DAK_GUNS, state="line")] +
   march(D(21, "14:00"), D(21, "16:00"), [DAK_GUNS, SE, P['fork'], M(35.2639, 8.7059), M(35.288, 8.665)])[1:] + [K(D(21, "16:05"), M(35.288, 8.665), state="firing", fire=0.6, h=280), K(D(21, "18:30"), M(35.288, 8.665), state="line"),
    K(D(22, "07:00"), M(35.288, 8.665), state="firing", fire=0.5), K(D(22, "17:30"), M(35.288, 8.665), state="line")] +
   march(D(22, "23:00"), D(23, "04:00"), [M(35.288, 8.665), M(35.2639, 8.7059), M(35.236, 8.758)])[1:] + [K(D(23, "04:05"), M(35.236, 8.758), state="line", h=300)], guns=24)
H974 = P['hill974']
ax("h974co", "On Hill 974", "The German party that took Hill 974 on Semmama's shoulder about noon on the 19th and 'could not get down its west face'", "", "infantry", 150,
   march(D(19, "09:30"), D(19, "12:00"), [M(35.322, 8.765), H974]) + [K(D(19, "12:05"), H974, state="firing", h=270), K(D(19, "13:00"), H974, state="line", strength=140), K(D(20, "16:30"), H974, state="charge", h=260),
    K(D(20, "17:30"), M(35.322, 8.722), state="firing", h=270), K(D(20, "18:30"), M(35.322, 8.722), state="line"), K(D(20, "19:00"), M(35.322, 8.722), state="hidden")], loose=True)
MTN = M(35.236, 8.715)
ax("mtnco", "Mountain coy", "A mountain company that tried to get round the American right above Hill 812 on the afternoon of the 19th and failed", "", "light_infantry", 120,
   march(D(19, "14:30"), D(19, "15:30"), [M(35.225, 8.740), MTN]) + [K(D(19, "15:35"), MTN, state="skirmish", h=320), K(D(19, "18:00"), MTN, state="retreat", h=140, strength=105), K(D(19, "18:30"), M(35.230, 8.724), state="line", h=320),
    K(D(20, "16:30"), M(35.230, 8.724), state="charge", h=320), K(D(20, "18:30"), off(P['zebbeus'], -400, -200), state="line", h=300), K(D(20, "19:00"), off(P['zebbeus'], -400, -200), state="hidden")], loose=True)

# ---- The 10th Panzer Division up the Thala road, 20-22 February ----
# Recorded: the motorcycle battalion committed along the Thala road late on the morning of the 20th; the armoured infantry over
# Hill 974 at 1630; the division's advance up the Thala road from about 0930 on the 21st with thirty tanks, twenty self-propelled
# guns and thirty-five half-track carriers; through the Leicesters directly after Dunphie about 1900; stopped about 2200 and back
# 1,200 yards; nine tanks lost at Thala (Atkinson); the attack postponed on the 22nd and the division holding the pass on the 23rd.
S_RIDGE1 = M(35.445, 8.7145)
S_RIDGE2 = M(35.487, 8.704)
STOPPED = M(35.530, 8.690)
def ridges(n_r1=None, n_r2=None, n_night=None, melee=M(35.540, 8.687), dx=0):  # the two ridges, the night melee, back 1,200 yards, into the pass on the 23rd
    r1, r2, m, s = off(S_RIDGE1, dx, 0), off(S_RIDGE2, dx, 0), off(melee, dx, 0), off(STOPPED, dx, 0)
    keys = [K(D(21, "11:00"), r1, state="firing", h=0), K(D(21, "16:00"), r1, **({"strength": n_r1} if n_r1 else {})),
            K(D(21, "16:10"), r1, state="column", h=0), K(D(21, "16:40"), r2, state="firing", h=0), K(D(21, "18:00"), r2, **({"strength": n_r2} if n_r2 else {})), K(D(21, "18:50"), r2, state="charge", h=0), K(D(21, "19:15"), m, state="firing", h=0),
            K(D(21, "22:00"), m, state="retreat", h=180, **({"strength": n_night} if n_night else {})), K(D(21, "22:30"), s, state="line", h=0), K(D(22, "06:20"), s, state="firing"), K(D(22, "08:00"), s, state="line")]
    keys += march(D(22, "23:00"), D(23, "06:00"), [s, P['bend'], off(M(35.300, 8.736), dx, 0)]) + [K(D(23, "06:05"), off(M(35.300, 8.736), dx, 0), state="line", h=0)]
    return keys
START_LINE = M(35.40, 8.716)  # where the division formed up on the Thala road about 0930 on the 21st
KRAD = M(35.262, 8.748)
ax("krad10", "Krad Bn 10", "10th Panzer Division's motorcycle battalion, committed along the Thala road late on the morning of the 20th; in the night its armoured cars and self-propelled guns pushed the British rear guards north and, in the morning fog, knocked out six Crusaders", "Generalleutnant Fritz Freiherr von Broich (10th Panzer)", "light_infantry", 500,
   march(D(20, "11:00"), D(20, "13:00"), [SE, P['fork'], P['thala_rd_hatab'], KRAD]) + [K(D(20, "13:05"), KRAD, state="firing", h=330), K(D(20, "16:30"), KRAD, state="charge", h=330), K(D(20, "17:30"), M(35.284, 8.738), state="firing", h=340),
    K(D(20, "18:30"), off(P['hill704'], 400, 400), state="line", h=340, strength=470)] +
   march(D(21, "03:00"), D(21, "07:00"), [off(P['hill704'], 400, 400), P['bend'], off(START_LINE, -600, 500)]) + [K(D(21, "07:05"), off(START_LINE, -600, 500), state="skirmish", h=0), K(D(21, "09:30"), off(START_LINE, -600, 500), state="column", h=0)] +
   ridges(n_r1=450, n_night=420, melee=M(35.537, 8.684), dx=-600), loose=True)
PZ7 = M(35.195, 8.790)
ax("pz7", "7th Pz Regt", "7th Panzer Regiment, 10th Panzer Division: 'thirty tanks' for Thala, the division being at half strength and its Tigers left with von Arnim. A captured Valentine led its column through the Leicesters on the night of the 21st (Atkinson); nine panzers were lost at Thala", "Generalleutnant Fritz Freiherr von Broich (10th Panzer)", "armor", 30,
   march(D(20, "15:00"), D(20, "18:00"), [EAST_EDGE, P['kasserine'], PZ7]) + [K(D(20, "18:05"), PZ7, state="line", h=310)] + march(D(21, "06:00"), D(21, "09:30"), [PZ7, P['fork'], P['thala_rd_hatab'], P['bend'], START_LINE]) + ridges(n_r1=28, n_r2=26, n_night=21))
PZGREN10 = M(35.318, 8.747)
ax("pzgren10", "10th Pz PzGren", "10th Panzer Division's armoured infantry, in thirty-five half-track carriers: over Hill 974 to the valley floor at 1630 on the 20th, then up the Thala road behind the tanks", "Generalleutnant Fritz Freiherr von Broich (10th Panzer)", "infantry", 900,
   march(D(20, "12:00"), D(20, "14:30"), [SE, M(35.26, 8.80), M(35.30, 8.77), PZGREN10]) + [K(D(20, "14:35"), PZGREN10, state="line", h=270), K(D(20, "16:30"), PZGREN10, state="charge", h=265), K(D(20, "18:00"), M(35.318, 8.721), state="firing", h=270),
    K(D(20, "19:00"), M(35.318, 8.721), state="line", strength=870)] + march(D(21, "07:00"), D(21, "09:30"), [M(35.318, 8.721), P['bend'], off(START_LINE, 500, -400)]) + ridges(n_r1=850, n_night=800, melee=M(35.536, 8.690), dx=500), loose=True)
SP10 = M(35.42, 8.718)
ax("sp10", "10th Pz SP guns", "10th Panzer Division's twenty self-propelled guns, whose shelling of Thala on the morning of the 22nd Irwin's 48 guns answered", "Generalleutnant Fritz Freiherr von Broich (10th Panzer)", "artillery", 300,
   march(D(21, "07:00"), D(21, "11:00"), [M(35.30, 8.737), P['bend'], SP10]) + [K(D(21, "11:05"), SP10, state="firing", fire=0.5, h=0), K(D(21, "16:30"), SP10, state="column", h=0), K(D(21, "17:30"), M(35.478, 8.706), state="firing", fire=0.5, h=0),
    K(D(21, "22:30"), M(35.478, 8.706), state="line"), K(D(22, "06:00"), M(35.478, 8.706), state="firing", fire=0.6), K(D(22, "13:00"), M(35.478, 8.706), state="line")] +
   march(D(22, "22:30"), D(23, "05:30"), [M(35.478, 8.706), P['bend'], M(35.296, 8.740)])[1:] + [K(D(23, "05:35"), M(35.296, 8.740), state="line", h=0)], guns=20)
REC580 = M(35.243, 8.762)
ax("rec580", "580th Recon", "580th Reconnaissance Battalion, sent from the 21st Panzer Division to hold the pass in the night of 20–21 February", "", "light_infantry", 400,
   march(D(21, "00:00"), D(21, "03:00"), [EAST_EDGE, P['kasserine'], SE, REC580]) + [K(D(21, "03:05"), REC580, state="line", h=300), K(D(23, "07:30"), REC580)], loose=True)

# Aircraft: cosmetic, never moving a unit. Recorded: Stukas on Combat Command B at 1630 on the 21st; 114 XII Air Support Command
# sorties over Thala on the morning of the 22nd, in low cloud (the places within the German positions are inferred).
def strike(name, at, t0, t1, spread=700, h=255): return dict(type="airstrike", name=name, at=list(at), spread=spread, h=h, **{"from": t0, "until": t1})
air = [strike("Stukas on Combat Command B", HAMRA_E, D(21, "16:30"), D(21, "16:50"), 900, 280),
       strike("XII Air Support Command over the 10th Panzer", M(35.50, 8.70), D(22, "09:00"), D(22, "09:30"), 900, 350),
       strike("XII Air Support Command over the 10th Panzer", M(35.47, 8.708), D(22, "11:00"), D(22, "11:30"), 900, 350)]

features = air + [
    dict(type="road", name="Thala road", pts=L(THALA_RD), at=list(off(P['ridge1'], 1800, 2000)), rot=-78),
    dict(type="road", name="Tébessa road", pts=L(TEBESSA_RD), at=list(off(M(35.3287, 8.5649), 0, -900)), rot=-20),
    dict(type="road", name="track from Haïdra", pts=L(HAIDRA_TRACK), at=list(off(M(35.47, 8.452), 1500, 0)), rot=-85),
    dict(type="road", name="to Bou Chebka", pts=L(BOU_CHEBKA_RD), at=list(off(P['bou_chebka'], 0, -1200)), rot=40),
    dict(type="road", pts=L(KASSERINE_ROADS[0])), dict(type="road", pts=L(KASSERINE_ROADS[1])),
    dict(type="creek", name="Oued el Hatab", pts=L(HATAB), at=list(off(M(35.2697, 8.7279), -1800, 900)), rot=-30),
    dict(name="Kasserine", at=list(off(P['kasserine'], 0, 900))), dict(name="Kasserine Pass", at=list(off(P['narrows'], 1200, 600))),
    dict(name="Bordj Chambi", at=list(off(P['fork'], 1300, -500))), dict(name="Djebel Chambi (1544)", at=list(off(P['chambi'], 0, -900))),
    dict(name="Djebel Zebbeus (812)", at=list(off(P['zebbeus'], -500, -800))), dict(name="Hill 712", at=list(off(P['hill712'], 900, 300))),
    dict(name="Hill 704", at=list(off(P['hill704'], -1100, 300))), dict(name="Hill 974", at=list(off(P['hill974'], 1000, 400))),
    dict(name="Hill 1191", at=list(off(P['hill1191'], 1000, -500))), dict(name="Djebel Semmama (1356)", at=list(off(P['semmama'], 0, 900))),
    dict(name="Bahiret Foussana", at=list(off(P['foussana'], 0, 2500))), dict(name="Foussana", at=list(off(P['foussana'], 0, 500))),
    dict(name="Point 732 (about here)", at=list(off(P['point732'], 0, -800))), dict(name="Djebel el Hamra (1112)", at=list(off(P['hamra'], 0, -1200)), rot=-80),
    dict(name="Bou Chebka pass (about here)", at=list(off(P['bou_chebka'], 0, 900))), dict(name="Thala", at=list(off(P['thala'], 0, 900))),
    dict(name="Haïdra", at=list(off(P['haidra'], 0, 900))), dict(name="to Tébessa", at=list(off(M(35.382, 8.358), 2200, 600))),
    dict(name="to Sbeïtla and Sbiba", at=list(off(M(35.18, 8.922), -2600, 600))), dict(name="to Fériana and Thélepte", at=list(off(M(35.142, 8.83), -2800, 700))),
    dict(name="to Le Kef", at=list(off(M(35.606, 8.655), -1800, -500))),
    dict(name="Rommel's CP (about here)", at=list(off(P['rommel_cp'], 0, -700)), **{"from": D(20, "11:00"), "until": D(22, "20:00")}),
]
events = []
PACE, WHEN = {}, {}

# Hold in place through long gaps: without this a unit creeps toward a key hours away and the time-lapse never engages.
# A turn in place takes its last two minutes; a move of more than three hours takes its last fifteen.
def add_holds(units):
    ts = lambda s: dt.datetime.strptime(s.replace("T", " ")[:16], "%Y-%m-%d %H:%M").timestamp()
    for u in units:
        ks, out = u["keys"], []
        for a, c in zip(ks, ks[1:] + [None]):
            out.append(a)
            if c is None or a.get("state") == "hidden": continue
            moved = (a["x"], a["y"]) != (c["x"], c["y"]); turned = "h" in c and c["h"] != next((k["h"] for k in reversed(out) if "h" in k), c["h"])
            gap = ts(c["t"]) - ts(a["t"]); lead = 900 if moved else 120
            if (moved and gap > 3 * 3600) or (turned and not moved and gap > 600):
                out.append(dict(t=dt.datetime.fromtimestamp(ts(c["t"]) - lead).strftime("%Y-%m-%d %H:%M"), x=a["x"], y=a["y"]))
        u["keys"] = out
for u in units: u["keys"] = [{k: v for k, v in key.items() if v is not None} for key in u["keys"]]
add_holds(units)
battle = dict(
    id="kasserine", name="Kasserine Pass", date="1943-02-19", dateText="19 to 23 February 1943", place="Kasserine Pass, Tunisia",
    origin=dict(lat=LAT0, lon=LON0), extent=52000, start=D(19, "06:00"), end=D(23, "07:30"), speed=300, lapse=7200, menPerDot=20,
    sunrise="07:08", sunset="18:12", terrainExaggeration=2, contourInterval=10,
    sides=dict(allied=dict(name="Allies (US II Corps, British 26th Armoured Brigade, French)", color="#1f55c4", light="#4a83e6", dark="#122c66"),
               axis=dict(name="Axis (Kampfgruppe DAK, 10th Panzer Division, Centauro)", color="#b8322a", light="#de5d50", dark="#5c1712")),
    tints=[dict(color="rgba(200,206,214,0.35)", **{"from": D(20, "06:30"), "until": D(21, "17:00")}),  # fog and rain over the battle area, 20-21 Feb
           dict(color="rgba(205,210,218,0.25)", **{"from": D(22, "07:00"), "until": D(22, "17:30")})],  # low cloud and showers, 22 Feb
    features=features, units=units,
    events=[dict(t=t, title=a, text=b, at=list(at), view=v, **({"speed": PACE[a]} if a in PACE else {}), **({"when": WHEN[a]} if a in WHEN else {})) for t, a, b, at, v in events],
    sources=[
        "George F. Howe, <i>Northwest Africa: Seizing the Initiative in the West</i> (US Army Center of Military History, 1957), chapters XXIII and XXIV: the ground, Stark Force and its reinforcements, Gore Force, the German groups, the clock times, the Thala and Djebel el Hamra fighting, the claims and the loss table for 16–24 February.",
        "Rick Atkinson, <i>An Army at Dawn</i> (2002), the Thala chapter: the 26th Armoured Brigade's tank counts, the Leicesters, Irwin's march and the night of 21–22 February.",
        "J. Rickard, 'Battle of the Kasserine Pass, 19–22 February 1943', historyofwar.org (2017): a few clock times Howe lacks, marked as his.",
        "Terrain: " + T["source"] + ". GLO-30 sampled at 100 m over a 52 km square; it is a surface model, so the modern city of Kasserine and the farms of the Foussana basin show. Roads and the Oued el Hatab from OpenStreetMap; the Tébessa road west of the basin, the track from Haïdra and the Bou Chebka road are drawn from the narrative.",
        "Clock: the times as recorded, read as a GMT+1 clock; sunrise 7:08 and sunset 18:12 are computed for 19 February on that assumption. Fog and rain covered the field on 20 and 21 February and low cloud and showers on the 22nd.",
        "What is reconstructed: the named hills (1191, 974, 712, 704, Zebbeus, Point 732, the Thala ridges, the Hamra passes, Bou Chebka pass), fitted to Howe's prose on the Copernicus DEM within a kilometre or two; every Axis tank and infantry count below the figures Howe gives (30 tanks, 20 self-propelled guns and 35 half-tracks for the 10th Panzer at Thala; eleven tanks for Gore; eight for Company I, 13th Armored); the 19th Engineers', 805th and 894th Tank Destroyers' strengths; the routes between recorded places; and the hours of the night movements of 19–20 and 20–21 February, which Howe says cannot be clearly reconstructed.",
    ],
)
json.dump(battle, open(HERE + "battle.json", "w"), indent=1, ensure_ascii=False)
print(len(units), "units (", sum(u["side"] == "allied" for u in units), "Allied,", sum(u["side"] == "axis" for u in units), "Axis ),", len(events), "events,", len(features), "features")
print("DEM at the hills:", {k: z(*P[k]) for k in ('narrows', 'zebbeus', 'hill712', 'hill704', 'hill974', 'hill1191', 'semmama', 'chambi', 'point732', 'hamra', 'bou_chebka', 'ridge1', 'ridge_leic')})
