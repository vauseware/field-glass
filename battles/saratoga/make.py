# Builds battles/saratoga/battle.json. Run from the repo root: python3 battles/saratoga/make.py
# Local metres from 42.99800N 73.62100W (x east, y north), on the plateau between Burgoyne's headquarters and the
# Middle Ravine. The 7 km square holds Sword's House (2210,3000), Freeman's farm (the house site at -1394,802),
# Barber's wheatfield (-2043,321), the Neilson house at the apex of the American line (-1620,-1365) and the Great
# Redoubt (838,524). Anchors are the NPS tour stops and memorials as mapped in OpenStreetMap; roads follow US 4,
# Wilbur and Phillips Roads. The Hudson, Mill Creek (the Middle Ravine) and the Kroma Kill (the Great Ravine) are
# traced from the elevation grid. Times follow Digby, Wilkinson and the NPS for the fighting and Burgoyne for the
# retreat. Strengths below brigade are apportioned: no regimental returns survive in the sources read.
import json, math, datetime as dt
T = json.load(open("battles/saratoga/terrain.json"))
COLS, SP = T["cols"], T["spacing"]; HALF = COLS * SP / 2; STEP = int(SP / 2); WATER = 25.3
def z(x, y):
    c, r = int((x + HALF) / SP), int((HALF - y) / SP)
    return T["z"][r * COLS + c] if 0 <= c < COLS and 0 <= r < COLS else 999
def low(x, y, rad=150):  # lowest cell near a point: a creek bed
    best = (999, x, y)
    for dx in range(-rad, rad + 1, STEP):
        for dy in range(-rad, rad + 1, STEP):
            v = z(x + dx, y + dy)
            if v < best[0]: best = (v, x + dx, y + dy)
    return (best[1], best[2])
def bank(x, y, dx=1):  # first water cell east (dx=1) of a point along its row
    while z(x, y) > WATER and abs(x) < HALF: x += dx * SP / 2
    return (round(x), y)

D = lambda d, hm: f"1777-{'09' if d >= 19 else '10'}-{d:02d} {hm}"
def sec(s): return dt.datetime.strptime(s, "%Y-%m-%d %H:%M").timestamp()
def fmt(ts): return dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
def K(t, p, **kw): return dict(t=t, x=p[0], y=p[1], **kw)
def march(t0, t1, pts, **kw):  # keys along a path, times spread by distance; heading follows the path
    d = [0]
    for i in range(1, len(pts)): d.append(d[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    out = []
    for i, p in enumerate(pts):
        j = min(i + 1, len(pts) - 1); q = pts[j] if j != i else pts[i - 1]
        h = round(math.degrees(math.atan2(q[0] - p[0], q[1] - p[1])) % 360) if j != i else out[-1]["h"]
        out.append(K(fmt(sec(t0) + (sec(t1) - sec(t0)) * d[i] / d[-1]), p, h=h, **({"state": "column"} if i == 0 else {}), **(kw if i == 0 else {})))
    return out
def go(t0, t1, pts, h, state="line", **kw):  # march, then face h and take up state at the end
    return march(t0, t1, pts)[:-1] + [K(t1, pts[-1], h=h, state=state, **kw)]
def cut(pts, back):  # the path stopped `back` metres short of its end: where a column's later companies halt
    out, left = [pts[-1]], back
    for i in range(len(pts) - 1, 0, -1):
        (x1, y1), (x0, y0) = pts[i], pts[i - 1]; seg = math.hypot(x1 - x0, y1 - y0)
        if left <= seg: f = left / seg; return pts[:i] + [(round(x1 + (x0 - x1) * f), round(y1 + (y0 - y1) * f))]
        left -= seg
    return pts[:1]
def blink(t, p, n, state="line"):  # a detachment told off out of sight: strength changes with no casualty markers
    return [K(t, p, state="hidden"), K(fmt(sec(t) + 60), p, state=state, strength=n)]
units = []
def unit(id, short, side, name, commander, type, strength, keys, **extra):
    units.append(dict(id=id, side=side, name=name, short=short, commander=commander, type=type, strength=strength, keys=keys, **extra))
us = lambda *a, **k: unit(a[0], a[1], "american", *a[2:], **k)
br = lambda *a, **k: unit(a[0], a[1], "british", *a[2:], **k)

SWORD, FREEMAN, BARBER, CHATFIELD, NEILSON, WOODWORTH = (2210, 3000), (-1394, 802), (-2043, 321), (-1809, -335), (-1620, -1365), (-1730, -1660)
BREYMANN, BOOT, GREAT, BURIAL, TAYLOR, HOSPITAL, HQ = (-1426, 1263), (-1493, 1151), (838, 524), (827, 778), (1263, 799), (968, 390), (28, 444)
WILBUR = [SWORD, (1200, 2748), (127, 2480), (-900, 2224), (-1884, 1984)]
FR_RT = WILBUR + [(-1900, 1500), (-1950, 1150)]                                   # Fraser: Wilbur Rd, then south by the Quaker road
HAM_RT = WILBUR[:3] + [(127, 1777), (122, 999), (-300, 980), (-800, 990)]          # Hamilton: Phillips Rd over the Great Ravine
RIVER_RD = [(2200, 3480), (2045, 2693), (1880, 1948), (1602, 1233), (1229, 620), (872, 75), (687, -315), (434, -845), (71, -1452), (-350, -1780), (-1000, -2150), (-1000, -2450), (-1013, -3028), (-1050, -3490)]
RIED_RT = [SWORD, (2045, 2693), (1880, 1948), (1602, 1233), (1229, 620), (990, 250)]  # the left column's halt, 800 paces past Taylor's
NORTH = [(1229, 620), (1602, 1233), (1880, 1948), (2045, 2693), (2200, 3480)]      # the retreat
FREEMAN_RD = [NEILSON, CHATFIELD, BARBER, FREEMAN, BREYMANN]
LATERAL = [FREEMAN, (-800, 700), (-200, 560), HQ, (500, 500), GREAT, (1229, 620)]
MILL = [low(*p) for p in [(-2331, -166), (-1940, -60), (-1555, 63), (-1200, 130), (-855, 186), (-526, -82), (-380, -450), (-240, -847), (-150, -1200), (-56, -1560)]]
MILL.append(bank(*MILL[-1]))
KROMA = [low(*p) for p in [(-224, 1953), (-100, 1550), (16, 1166), (122, 999), (400, 750), (683, 485), (878, 86)]]
KROMA.append(bank(*KROMA[-1]))
def ellipse(cx, cy, a, b, n=16): return [(round(cx + a * math.cos(2 * math.pi * i / n)), round(cy + b * math.sin(2 * math.pi * i / n))) for i in range(n)]
def sq(cx, cy, s=40): return [(cx - s / 2, cy - s / 2), (cx + s / 2, cy - s / 2), (cx + s / 2, cy + s / 2), (cx - s / 2, cy + s / 2)]
def flats(road, y0, y1):  # river meadows: the strip between the road and the water
    side = [(round(road(y)), y) for y in range(y0, y1 + 1, 100)]
    return side + [bank(x, y) for x, y in side][::-1]
def road_x(pts):
    def f(y):
        for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
            if min(ya, yb) <= y <= max(ya, yb): return xa + (xb - xa) * (y - ya) / (yb - ya)
    return f

# ---- the American army: camps inside the Bemis Heights line ----
CAMP = dict(morgan=(-1640, -1820), dearborn=(-1520, -1800), cilley=(-1560, -1500), scammell=(-1450, -1560), hale=(-1340, -1620), vanc=(-1230, -1700),
            liv=(-1500, -1680), ct=(-1380, -1790), learned=(-1250, -1880), paterson=(-1080, -1840), nixon=(-930, -1850), putnam=(-1150, -2000),
            glover=(-560, -1880), tenbroeck=(-1450, -2100))
TO_FARM = [NEILSON, CHATFIELD, (-1950, 150), (-1700, 560)]
def out19(id, t0, t1, spot, h=0):  # from camp by the Neilson farm road to the south edge of Freeman's clearing
    return go(D(19, t0), D(19, t1), [CAMP[id]] + TO_FARM + [spot], h)
def home(id, t0, t1, p): return march(t0, t1, [p, (-1800, 300), CHATFIELD, NEILSON, CAMP[id]])[1:-1] + [K(t1, CAMP[id], h=0, state="line")]
us("morgan", "Morgan", "Morgan's corps of Virginia and Pennsylvania riflemen, first out on both days", "Col. Daniel Morgan", "riflemen", 500,
   [K(D(19, "09:00"), CAMP["morgan"], h=0, state="line")] + go(D(19, "11:35"), D(19, "12:27"), [CAMP["morgan"]] + TO_FARM + [(-1420, 740)], 0, "firing") +
   [K(D(19, "12:33"), (-1420, 740), state="charge"), K(D(19, "12:40"), (-1360, 900), state="firing", strength=480), K(D(19, "12:42"), (-1360, 900), state="rout", h=200),
    K(D(19, "12:55"), (-1500, 520), strength=460), K(D(19, "13:02"), (-1380, 640), h=0, state="line"), K(D(19, "13:10"), (-1260, 660), state="firing"), K(D(19, "13:30"), (-1260, 660), state="firing", fire=0.3),
    K(D(19, "14:00"), (-1240, 660), state="firing"), K(D(19, "16:40"), (-1240, 660), state="charge", strength=445), K(D(19, "16:48"), (-1220, 800), state="firing"), K(D(19, "16:58"), (-1220, 800), state="retreat", h=180),
    K(D(19, "17:06"), (-1240, 660), h=20, state="firing"), K(D(19, "18:05"), (-1240, 660), state="firing", h=80), K(D(19, "18:15"), (-1260, 640), state="retreat", h=200, strength=430)] +
   home("morgan", D(19, "18:40"), D(19, "20:10"), (-1450, 450)) +
   # 7 October: the circuit through the woods to the height on the British right, then north to Breymann's
   go(D(7, "13:40"), D(7, "14:36"), [CAMP["morgan"], (-2100, -1100), (-2700, -350), (-2720, 150)], 20, "firing") +
   [K(D(7, "14:44"), (-2720, 150), state="column"), K(D(7, "14:58"), (-2470, 420), h=100, state="firing"), K(D(7, "15:14"), (-2470, 420), state="charge"),
    K(D(7, "15:24"), (-2280, 450), state="firing", strength=420), K(D(7, "15:40"), (-2280, 450), state="line")] +
   go(D(7, "16:30"), D(7, "17:22"), [(-2280, 450), (-1900, 950), (-1720, 1320)], 100, "firing") +
   [K(D(7, "17:48"), (-1720, 1320), state="charge"), K(D(7, "17:55"), (-1530, 1320), state="line", strength=410)] +
   # 8 October: into the abandoned camp, sniping at the British round the Great Redoubt
   go(D(8, "07:40"), D(8, "08:40"), [(-1530, 1320), (-1000, 1000), (-300, 850), (150, 800)], 90, "firing", fire=0.2) + [K(D(8, "17:30"), (150, 800), state="line")])
us("dearborn", "Dearborn", "Dearborn's light infantry battalion, 300 picked men serving with Morgan", "Maj. Henry Dearborn", "light_infantry", 300,
   [K(D(19, "09:00"), CAMP["dearborn"], h=0, state="line")] + out19("dearborn", "11:40", "12:36", (-1560, 650)) +
   [K(D(19, "12:40"), (-1560, 650), state="firing"), K(D(19, "13:00"), (-1400, 665), state="line", strength=290), K(D(19, "14:00"), (-1400, 665), state="firing"),
    K(D(19, "18:10"), (-1400, 665), state="firing", strength=270), K(D(19, "18:20"), (-1400, 665), state="retreat", h=200)] + home("dearborn", D(19, "18:40"), D(19, "20:10"), (-1550, 450)) +
   go(D(7, "13:45"), D(7, "14:58"), [CAMP["dearborn"], (-2050, -1100), (-2550, -350), (-2290, 170)], 15, "firing") +
   [K(D(7, "15:10"), (-2290, 170), state="charge"), K(D(7, "15:18"), (-2240, 300), state="firing", strength=262), K(D(7, "15:40"), (-2240, 300), state="line")] +
   go(D(7, "16:35"), D(7, "17:20"), [(-2240, 300), (-1900, 900), (-1660, 1180)], 90, "firing") +
   [K(D(7, "17:48"), (-1660, 1180), state="charge"), K(D(7, "17:55"), (-1500, 1180), state="line", strength=260)] +
   go(D(8, "07:45"), D(8, "08:45"), [(-1500, 1180), (-1000, 900), (-300, 720), (150, 660)], 90, "firing", fire=0.2) + [K(D(8, "17:30"), (150, 660), state="line")])

# Poor's brigade went in by regiments on 19 September and against Acland's grenadiers on 7 October.
SEE = {"cilley": [("16:05", (-1600, 800))], "scammell": [("15:40", (-1500, 790)), ("16:50", (-1480, 800))], "hale": [("15:20", (-1720, 800))], "vanc": [], "liv": [], "ct": []}
def poor(id, short, name, cmd, n, t0, t1, spot, loss19, spot7, loss7, bal, type="infantry", **x):
    k = [K(D(19, "09:00"), CAMP[id], h=0, state="line")] + out19(id, t0, t1, spot) + [K(D(19, t1), spot, h=0, state="firing")]
    left = n
    for tc, p in SEE[id]:  # the see-saw over the clearing: a rush into the open and back
        left -= loss19 // 3
        k += [K(D(19, tc), spot, state="charge"), K(fmt(sec(D(19, tc)) + 420), p, state="firing", strength=left), K(fmt(sec(D(19, tc)) + 840), p, state="retreat", h=180),
              K(fmt(sec(D(19, tc)) + 1260), spot, h=0, state="firing")]
    k += [K(D(19, "18:15"), spot, state="firing", strength=n - loss19), K(D(19, "18:25"), spot, state="retreat", h=200)] + home(id, D(19, "18:45"), D(19, "20:20"), (spot[0], 450))
    s7 = n - loss19
    k += go(D(7, "14:05"), D(7, "14:56"), [CAMP[id], (CAMP[id][0], -1100), (spot7[0] + 120, -400), (spot7[0], 160), spot7], 0, "firing") + \
        [K(D(7, "15:08"), spot7, state="charge"), K(D(7, "15:15"), (spot7[0], spot7[1] + 110), state="firing", strength=s7 - loss7 // 2), K(D(7, "15:40"), (spot7[0], spot7[1] + 110), state="line")]
    k += go(D(7, "16:20"), D(7, "16:52"), [(spot7[0], spot7[1] + 110), (bal[0] - 200, bal[1] - 100)], 70, "line") + [K(D(7, "16:56"), (bal[0] - 200, bal[1] - 100), state="charge"),
         K(D(7, "17:06"), bal, state="firing"), K(D(7, "17:24"), bal, state="retreat", h=250, strength=s7 - loss7), K(D(7, "17:38"), (bal[0] - 260, bal[1] - 60), h=70, state="line")]
    k += go(D(8, "07:50"), D(8, "08:50"), [(bal[0] - 260, bal[1] - 60), (bal[0] + 400, bal[1] - 150), (bal[0] + 900, bal[1] - 200)], 90)
    us(id, short, name, cmd, type, n, k, **x)
poor("cilley", "1st NH", "1st New Hampshire, Poor's brigade; on 7 October Cilley sat astride a captured 12-pounder", "Col. Joseph Cilley", 250, "13:00", "13:50", (-1620, 680), 50, (-1620, 300), 14, (-1520, 700))
poor("scammell", "3rd NH", "3rd New Hampshire, Poor's brigade", "Col. Alexander Scammell", 250, "13:05", "13:56", (-1520, 675), 50, (-1520, 300), 14, (-1510, 820))
poor("hale", "2nd NH", "2nd New Hampshire, Poor's brigade", "Col. Nathan Hale", 250, "13:40", "14:30", (-1720, 690), 40, (-1720, 290), 10, (-1530, 590))
poor("vanc", "2nd NY", "2nd New York, Poor's brigade", "Col. Philip Van Cortlandt", 250, "13:50", "14:40", (-1820, 695), 25, (-1420, 310), 8, (-1520, 930))
poor("liv", "4th NY", "4th New York, Poor's brigade", "Lt. Col. Henry B. Livingston", 250, "14:00", "14:50", (-1920, 690), 25, (-1320, 320), 8, (-1600, 500))
poor("ct", "Connecticut militia", "Cook's and Latimer's Connecticut militia, extending Poor's left", "Cols. Thaddeus Cook and Jonathan Latimer", 300, "14:10", "15:00", (-2040, 670), 20, (-1560, 190), 6, (-1680, 640), type="militia")
us("learned", "Learned", "Learned's brigade: the 2nd, 8th and 9th Massachusetts and the 1st Canadian, with Marshall's 10th Massachusetts on 19 September", "Brig. Gen. Ebenezer Learned", "infantry", 700,
   [K(D(19, "09:00"), CAMP["learned"], h=0, state="line")] + out19("learned", "16:30", "17:40", (-2150, 720), 20) +
   [K(D(19, "17:50"), (-2150, 720), state="firing"), K(D(19, "18:40"), (-2150, 720), state="line", strength=690), K(D(19, "18:45"), (-2150, 720), state="retreat", h=180)] +
   home("learned", D(19, "19:00"), D(19, "20:30"), (-2100, 450)) +
   go(D(7, "14:15"), D(7, "15:05"), [CAMP["learned"], (-1600, -1300), CHATFIELD, (-1880, 140)], 0, "firing") +
   [K(D(7, "15:20"), (-1880, 140), state="retreat", h=180, strength=675), K(D(7, "15:27"), (-1880, 60), h=0, state="line"), K(D(7, "15:40"), (-1880, 60), state="charge"),
    K(D(7, "15:48"), (-1880, 330), state="firing", strength=665), K(D(7, "15:55"), (-1880, 330), state="line")] +
   go(D(7, "16:40"), D(7, "17:26"), [(-1880, 330), (-1720, 720), (-1640, 1000), (-1560, 1060)], 80, "charge") +
   [K(D(7, "17:34"), (-1450, 1065), state="firing"), K(D(7, "17:44"), (-1450, 1065), state="charge", h=20), K(D(7, "17:52"), (-1400, 1180), state="firing", strength=650), K(D(7, "18:00"), (-1400, 1180), state="line")] +
   go(D(8, "07:40"), D(8, "08:40"), [(-1400, 1180), (-900, 900), (-400, 700)], 90))
us("arnold", "Arnold", "Arnold and a few aides. Relieved of command after quarrelling with Gates, he rode out on 7 October without orders", "Maj. Gen. Benedict Arnold", "cavalry", 10,
   [K(D(7, "15:29"), WOODWORTH, h=0, state="hidden")] + go(D(7, "15:30"), D(7, "15:39"), [WOODWORTH, (-1700, -900), CHATFIELD, (-1880, 60)], 0) +
   [K(D(7, "15:40"), (-1880, 60), state="charge"), K(D(7, "15:48"), (-1880, 330), state="line")] + go(D(7, "16:30"), D(7, "16:52"), [(-1880, 330), (-1700, 560)], 70) +
   [K(D(7, "16:56"), (-1700, 560), state="charge"), K(D(7, "17:06"), (-1520, 700), state="line")] +
   go(D(7, "17:24"), D(7, "17:34"), [(-1520, 700), (-1540, 860), (-1530, 1040)], 20) + [K(D(7, "17:44"), (-1530, 1040), state="charge"), K(D(7, "17:52"), BOOT, h=60, state="line", strength=9),
   K(D(7, "18:20"), BOOT, state="hidden")])
us("tenbroeck", "Ten Broeck's militia", "Ten Broeck's Albany County militia, among the militia that joined Gates in early October; the sources give 1,200 to 3,000", "Brig. Gen. Abraham Ten Broeck", "militia", 1200,
   go(D(5, "10:00"), D(5, "11:30"), [RIVER_RD[-1], RIVER_RD[-2], RIVER_RD[-3], (-1200, -2300), CAMP["tenbroeck"]], 0) +
   go(D(7, "15:30"), D(7, "16:00"), [CAMP["tenbroeck"], (-1700, -1300), CHATFIELD, (-1800, -100)], 0) + go(D(7, "16:02"), D(7, "16:22"), [(-1800, -100), (-1800, 250)], 0), ranks=3)
# The right wing stayed in the works on 19 September; Lincoln brought part of it out on 7 October.
def works(id, short, name, cmd, n, keys=(), **x): us(id, short, name, cmd, "infantry", n, [K(D(19, "09:00"), CAMP[id], h=10, state="line")] + list(keys), ranks=4, **x)
works("glover", "Glover", "Glover's brigade, in the works on the river flats below the bluff", "Brig. Gen. John Glover", 1300)
works("nixon", "Nixon", "Nixon's brigade (less the 5th and 6th Massachusetts), on the bluff by the river batteries", "Brig. Gen. John Nixon", 600)
works("putnam", "Putnam", "The 5th and 6th Massachusetts of Nixon's brigade; on 7 October they stormed the front of Breymann's works", "Col. Rufus Putnam", 400,
      go(D(7, "15:40"), D(7, "17:24"), [CAMP["putnam"], (-1400, -1200), (-1500, -300), (-2050, 450), (-1900, 950), (-1590, 1250)], 90, "firing") +
      [K(D(7, "17:46"), (-1590, 1250), state="charge", strength=395), K(D(7, "17:54"), (-1470, 1250), state="line", strength=385)])
works("paterson", "Paterson", "Paterson's brigade of Massachusetts regiments, which Lincoln brought up late on 7 October", "Brig. Gen. John Paterson; Maj. Gen. Benjamin Lincoln", 900,
      go(D(7, "15:40"), D(7, "16:58"), [CAMP["paterson"], (-1300, -1200), (-1450, -300), (-1800, 500), (-1760, 760)], 80, "firing") +
      [K(D(7, "17:40"), (-1760, 760), state="line", strength=890)])
us("riverguns", "River batteries", "Stevens's batteries on the bluff above the river road, part of the twenty-two guns in the American lines", "Maj. Ebenezer Stevens", "artillery", 120,
   [K(D(19, "09:00"), (-960, -1740), h=20, state="line")], guns=8)
us("neilsonguns", "Fort Neilson", "The battery at Neilson's barn, the apex of the American line", "", "artillery", 80, [K(D(19, "09:00"), (-1600, -1400), h=330, state="line")], guns=6)
us("amguns", "American guns", "Guns brought up on 8 October to fire on the Great Redoubt and the bridge of boats (the place is a guess)", "", "artillery", 50,
   [K(D(8, "09:00"), (250, 230), h=60, state="hidden"), K(D(8, "09:01"), (250, 230), state="line"), K(D(8, "09:30"), (250, 230), state="firing", fire=0.4), K(D(8, "21:00"), (250, 230), state="line")], guns=4)

# ---- Burgoyne's army: three columns from Sword's House on 19 September, then the fortified camp ----
CB = dict(li=(-1390, 900, 260), gren=(-1340, 770, 260), r24=(-1390, 640, 240), breymann=(-1450, 1240, 270), prov=(-1250, 1380, 300), r21=(-1080, 690, 200),
          r62=(-880, 640, 200), r20=(-680, 590, 200), r9=(-440, 530, 200), jones=(-760, 620, 200), riedesel=(-180, 480, 190), rhetz=(110, 420, 190),
          specht=(380, 370, 190), hanau=(1000, 230, 160), r47=(1290, 540, 90), pausch=(-1330, 980, 270), phillips=(-1320, 680, 250))
def camp(id, t0="12:00", t1="13:30"):  # 20 September: into the fortified camp
    x, y, h = CB[id]
    return lambda p: go(D(20, t0), D(20, t1), [p, (x, y)], h)
GR = dict(gren=(660, 880, 250), li=(650, 740, 250), r24=(700, 620, 240), german=(720, 1000, 270), breymann=(870, 1080, 280), howitzers=(790, 700, 250), phillips=(800, 580, 240),
          jones=(790, 830, 260), r62=(950, 880, 260), r20=(990, 740, 250), r21=(950, 990, 270), r9=(1060, 520, 200), riedesel=(1050, 1140, 300), rhetz=(1150, 1040, 290),
          specht=(1150, 900, 270), hanau=(1000, 240, 180), r47=(1290, 540, 90))
def night7(id, t0, p, mins=60):  # night of 7-8 October: back to the Great Redoubt and the flats
    x, y, h = GR[id]; t0 = D(7 if t0 >= "12:00" else 8, t0)
    return go(t0, fmt(sec(t0) + mins * 60), [p, (-200, 560), (x - 120, y), (x, y)], h)
def retreat(id, t0, day=8, mins=110):  # the retreat north up the river road in the rain, out of the map
    x, y, h = GR[id]
    t1 = fmt(sec(D(day, t0)) + mins * 60)
    return march(D(day, t0), t1, [(x, y)] + NORTH) + [K(fmt(sec(t1) + 60), NORTH[-1], state="hidden")]
def fraser(id, short, name, cmd, n, t0, t1, spot, h, keys, type="infantry", **x):
    br(id, short, name, cmd, type, n, go(D(19, t0), D(19, t1), FR_RT + [spot], h) + keys, **x)
fraser("prov", "Loyalists and Indians", "Canadians, Peters's and Jessup's Loyalists and Fraser's Indians: scouts on the right in September, sent round the American flank on 7 October", "", 300,
       "09:00", "12:15", (-2280, 820), 200, [K(D(19, "13:00"), (-2280, 820), state="firing", fire=0.3), K(D(19, "18:00"), (-2280, 820), state="line", strength=290)] + camp("prov")((-2280, 820)) +
       go(D(7, "12:40"), D(7, "14:20"), [(-1250, 1380), (-1900, 1350), (-2600, 950), (-2650, 300)], 160, "firing", fire=0.3) +
       [K(D(7, "14:38"), (-2650, 300), state="rout", h=330, strength=270), K(D(7, "15:00"), (-2500, 1000)), K(D(7, "15:01"), (-2500, 1000), state="hidden")], type="light_infantry")
fraser("li", "Light infantry", "The British light infantry battalion of Fraser's Advanced Corps, the right of the line on 7 October", "Maj. Alexander Lindsay, Earl of Balcarres", 450,
       "09:05", "12:20", (-2000, 860), 190, [K(D(19, "13:00"), (-2000, 860), state="firing", fire=0.3), K(D(19, "13:30"), (-2000, 860), state="line", strength=440), K(D(19, "17:50"), (-2000, 860), state="firing"),
       K(D(19, "18:40"), (-2000, 860), state="line", strength=425)] + camp("li")((-2000, 860)) +
       [K(D(7, "10:00"), CB["li"][:2], state="column", h=200)] + go(D(7, "13:00"), D(7, "13:40"), [CB["li"][:2], (-1700, 650), (-2230, 330)], 185) +
       [K(D(7, "15:04"), (-2230, 330), state="firing", h=230), K(D(7, "15:14"), (-2230, 330), state="retreat", h=30, strength=400), K(D(7, "15:20"), (-2150, 440), h=210, state="firing"),
        K(D(7, "15:36"), (-2150, 440), state="retreat", h=40, strength=385), K(D(7, "16:00"), (-1700, 720)), K(D(7, "16:20"), CB["li"][:2], h=260, state="line"),
        K(D(7, "16:56"), CB["li"][:2], state="firing"), K(D(7, "17:40"), CB["li"][:2], state="line", strength=365)] + night7("li", "23:00", CB["li"][:2]) +
       [K(D(8, "09:00"), GR["li"][:2], state="firing", fire=0.2), K(D(8, "17:30"), GR["li"][:2], state="line")] + retreat("li", "23:00"))
fraser("gren", "Grenadiers", "The British grenadier battalion of the Advanced Corps (Digby's 53rd company among them), the left of the line on 7 October and the rear guard of the retreat", "Maj. John Dyke Acland (wounded and taken 7 Oct)", 450,
       "09:10", "12:30", (-1840, 890), 190, [K(D(19, "15:30"), (-1840, 890), state="firing"), K(D(19, "16:30"), (-1840, 890), state="line", strength=420)] + camp("gren")((-1840, 890)) +
       [K(D(7, "10:00"), CB["gren"][:2], state="column", h=200)] + go(D(7, "13:05"), D(7, "13:45"), [CB["gren"][:2], (-1500, 600), (-1620, 405)], 180) +
       [K(D(7, "15:00"), (-1620, 405), state="firing"), K(D(7, "15:10"), (-1620, 405), state="rout", h=40, strength=330), K(D(7, "15:20"), (-1500, 540), h=200, state="line", strength=320),
        K(D(7, "15:24"), (-1500, 540), state="firing"), K(D(7, "15:32"), (-1500, 540), state="rout", h=30, strength=285), K(D(7, "15:50"), (-1400, 660)), K(D(7, "16:05"), CB["gren"][:2], h=260, state="line", strength=270)] +
       night7("gren", "22:30", CB["gren"][:2]) + retreat("gren", "04:00", day=9, mins=95))
fraser("r24", "24th Foot", "The 24th Regiment of Foot, with the light infantry on the right", "Maj. William Agnew", 300,
       "09:15", "12:35", (-1690, 930), 170, [K(D(19, "15:00"), (-1690, 930), state="firing"), K(D(19, "17:00"), (-1690, 930), state="line", strength=275)] + camp("r24")((-1690, 930)) +
       [K(D(7, "10:00"), CB["r24"][:2], state="column", h=200)] + go(D(7, "13:02"), D(7, "13:42"), [CB["r24"][:2], (-1700, 560), (-2080, 345)], 185) +
       [K(D(7, "15:06"), (-2080, 345), state="firing"), K(D(7, "15:20"), (-2080, 345), state="firing", strength=250), K(D(7, "15:36"), (-2080, 345), state="retreat", h=40, strength=240),
        K(D(7, "16:00"), (-1700, 600)), K(D(7, "16:20"), CB["r24"][:2], h=240, state="line"), K(D(7, "16:56"), CB["r24"][:2], state="firing"), K(D(7, "17:40"), CB["r24"][:2], state="line", strength=225)] +
       night7("r24", "23:10", CB["r24"][:2]) + retreat("r24", "23:15"), ranks=3)
fraser("breymann", "Breymann", "Breymann's German reserve: Brunswick grenadiers, Bärner's light infantry and jägers; by 7 October about 200 held his redoubt, the rest out with the reconnaissance", "Lt. Col. Heinrich von Breymann (killed 7 Oct)", 500,
       "09:20", "12:45", (-2170, 980), 210, [K(D(19, "16:00"), (-2170, 980), state="firing"), K(D(19, "16:30"), (-2170, 980), state="line", strength=485)] + camp("breymann")((-2170, 980)) +
       blink(D(7, "09:50"), CB["breymann"][:2], 200) + [K(D(7, "17:30"), CB["breymann"][:2], state="firing"), K(D(7, "17:50"), CB["breymann"][:2], state="rout", h=80, strength=120),
       K(D(7, "18:02"), (-1150, 1250), strength=105), K(D(7, "18:12"), (-950, 1150), h=270, state="line")] + night7("breymann", "22:00", (-950, 1150)) + retreat("breymann", "22:45"), ranks=3)
def hamilton(id, short, name, cmd, n, t0, t1, wait, form, h, keys, type="infantry", **x):
    br(id, short, name, cmd, type, n, go(D(19, t0), D(19, t1), HAM_RT + [wait], 250) + keys, **x)
hamilton("picquets", "Picquets", "The army's picquets, the advance guard of Hamilton's column, which walked into Morgan's riflemen at Freeman's farm", "Maj. Gordon Forbes", 100, "10:00", "12:10", (-1150, 980), None, 0,
         [K(D(19, "12:20"), (-1250, 960), state="column", h=240), K(D(19, "12:27"), (-1390, 870), h=200, state="line"), K(D(19, "12:30"), (-1390, 870), state="firing"),
          K(D(19, "12:34"), (-1390, 870), state="rout", h=30, strength=75), K(D(19, "12:45"), (-1250, 1020), h=200, state="line", strength=65), K(D(20, "12:00"), (-1250, 1020), state="hidden")])
def centre(id, short, name, cmd, n, t0, t1, wait, form, h, losses, pushes=(), **x):
    k = [K(D(19, "13:40"), wait, state="column"), K(D(19, "14:05"), form, h=h, state="firing")]
    left = n
    for tc in pushes:  # the 62nd went at the American line four times
        left -= losses // (len(pushes) + 1)
        p = (form[0], form[1] - 120)
        k += [K(D(19, tc), form, state="charge"), K(fmt(sec(D(19, tc)) + 420), p, state="firing", strength=left), K(fmt(sec(D(19, tc)) + 840), p, state="retreat", h=0),
              K(fmt(sec(D(19, tc)) + 1260), form, h=h, state="firing")]
    k += [K(D(19, "19:00"), form, state="line", strength=n - losses)] + camp(id)(form)
    hamilton(id, short, name, cmd, n, t0, t1, wait, form, h, k, **x)
centre("r62", "62nd Foot", "The 62nd Regiment of Foot, the centre of Hamilton's line; it lost more than half its men", "Lt. Col. John Anstruther", 350, "10:05", "12:30", (-1100, 1000), (-1360, 885), 180, 210,
       ["15:20", "16:05", "16:45", "17:25"], ranks=3)
centre("r20", "20th Foot", "The 20th Regiment of Foot, the left of Hamilton's line", "", 350, "10:10", "12:40", (-1000, 1010), (-1220, 880), 180, 90, ["17:00"], ranks=3)
centre("r21", "21st Fusiliers", "The 21st Regiment of Foot (Royal North British Fusiliers), the right of Hamilton's line", "", 400, "10:15", "12:45", (-950, 1030), (-1500, 885), 180, 80, ["16:20"], ranks=3)
hamilton("r9", "9th Foot", "The 9th Regiment of Foot, about 250 men, kept in reserve behind a ravine; it led the retreat on 8 October", "", 250, "10:20", "12:50", (-900, 1050), None, 0,
         [K(D(19, "14:00"), (-900, 1050), state="column"), K(D(19, "14:20"), (-1300, 1060), h=180, state="line"), K(D(19, "17:00"), (-1300, 1060), strength=235)] + camp("r9")((-1300, 1060)) +
         night7("r9", "21:30", CB["r9"][:2]) + retreat("r9", "12:00", mins=120), ranks=3)
hamilton("jones", "Jones's guns", "Four 6-pounders with Hamilton's brigade; 36 of their 48 gunners were hit and Captain Jones killed", "Capt. Thomas Jones RA (killed)", 48, "10:12", "12:42", (-1050, 1000), None, 0,
         [K(D(19, "13:45"), (-1050, 1000), state="column"), K(D(19, "14:00"), (-1290, 875), h=180, state="firing", fire=0.8), K(D(19, "15:40"), (-1290, 875), state="line", strength=28),
          K(D(19, "15:55"), (-1290, 875), state="firing", fire=0.4), K(D(19, "16:40"), (-1290, 875), state="line", strength=12)] + camp("jones")((-1290, 875)) +
         night7("jones", "21:40", CB["jones"][:2]) + retreat("jones", "21:30"), guns=4)
# The left column on the river road: Riedesel's Germans, the 47th, the guns and the baggage.
def left(id, short, name, cmd, type, n, t0, t1, back, h, keys, **x):
    p = cut(RIED_RT, back)
    br(id, short, name, cmd, type, n, go(D(19, t0), D(19, t1), p, h) + keys(p[-1]), **x)
RELIEF = [(700, 450), (200, 650), (-500, 760)]
left("riedesel", "Riedesel", "Riedesel's own Brunswick regiment with two companies of Rhetz: the column that struck the American right at sunset on 19 September", "Maj. Gen. Friedrich Adolf Riedesel", "infantry", 650, "10:00", "11:40", 0, 200,
     lambda p: go(D(19, "17:00"), D(19, "17:50"), [p] + RELIEF + [(-950, 760)], 250) + [K(D(19, "17:56"), (-950, 760), state="charge"), K(D(19, "18:06"), (-1110, 700), state="firing"),
     K(D(19, "18:40"), (-1110, 700), state="line", strength=630)] + go(D(19, "20:00"), D(19, "21:00"), [(-1110, 700)] + RELIEF[::-1] + [p], 200) + camp("riedesel")(p) +
     night7("riedesel", "21:00", CB["riedesel"][:2]) + retreat("riedesel", "21:00"), ranks=3)
left("pausch", "Pausch", "Two Hesse-Hanau 6-pounders that went with Riedesel on 19 September; both were taken on 7 October", "Capt. Georg Pausch", "artillery", 24, "10:10", "11:50", 120, 200,
     lambda p: go(D(19, "17:02"), D(19, "17:52"), [p] + RELIEF + [(-1000, 820)], 240, "firing") + [K(D(19, "18:40"), (-1000, 820), state="line")] +
     go(D(19, "20:00"), D(19, "21:00"), [(-1000, 820)] + RELIEF[::-1] + [p], 200) + camp("pausch")(p) +
     [K(D(7, "10:00"), CB["pausch"][:2], state="column")] + go(D(7, "13:04"), D(7, "13:44"), [CB["pausch"][:2], (-1480, 700), (-1700, 500), (-1760, 383)], 185) +
     [K(D(7, "15:00"), (-1760, 383), state="firing"), K(D(7, "15:50"), (-1760, 383), state="surrender", strength=14), K(D(7, "16:30"), (-1760, 383), state="hidden")], guns=2)
left("phillips", "Phillips's guns", "Four guns Phillips brought across from the river road to steady the centre late on 19 September; later in the Balcarres Redoubt", "Maj. Gen. William Phillips", "artillery", 48, "10:15", "11:55", 200, 200,
     lambda p: go(D(19, "16:00"), D(19, "16:40"), [p, (700, 450), (200, 650), (-500, 800), (-1000, 900), (-1180, 890)], 200, "firing") + [K(D(19, "19:00"), (-1180, 890), state="line")] + camp("phillips")((-1180, 890)) +
     [K(D(7, "16:56"), CB["phillips"][:2], state="firing"), K(D(7, "17:40"), CB["phillips"][:2], state="line")] + night7("phillips", "22:10", CB["phillips"][:2]) + retreat("phillips", "23:45"), guns=4)
left("rhetz", "Rhetz", "The Brunswick regiment Rhetz, less two companies", "", "infantry", 300, "10:20", "12:00", 300, 200,
     lambda p: camp("rhetz")(p) + night7("rhetz", "21:10", CB["rhetz"][:2]) + retreat("rhetz", "21:15"), ranks=3)
left("specht", "Specht", "The Brunswick regiment Specht, which stayed on the river road with the 47th and the heavy guns on 19 September", "Lt. Col. Johann Specht", "infantry", 450, "10:30", "12:10", 450, 200,
     lambda p: camp("specht")(p) + night7("specht", "21:20", CB["specht"][:2]) + retreat("specht", "21:30"), ranks=3)
left("hanau", "Hesse-Hanau", "The Hesse-Hanau regiment Erbprinz, camped on the river flats", "", "infantry", 500, "10:40", "12:20", 620, 200,
     lambda p: camp("hanau")(p) + retreat("hanau", "21:45"), ranks=3)
left("r47", "47th Foot", "Six companies of the 47th Foot guarding the bateaux, the stores and the hospital on the flats", "", "infantry", 300, "10:50", "12:30", 800, 200,
     lambda p: camp("r47")(p) + retreat("r47", "12:10", mins=120), ranks=3)
br("canadians", "Canadian companies", "Two companies of Canadians posted in the stockaded cabins between the two redoubts; absent from their post at the crisis", "", "militia", 100,
   [K(D(20, "13:30"), (-1420, 1060), h=270, state="hidden"), K(D(20, "13:31"), (-1420, 1060), state="line"), K(D(7, "17:30"), (-1420, 1060), state="rout", h=60, strength=90),
    K(D(7, "17:40"), (-1150, 1180)), K(D(7, "17:41"), (-1150, 1180), state="hidden")], ranks=1)
br("german", "Germans", "About 300 Germans drawn from every regiment, the centre of the reconnaissance in force", "Lt. Col. Johann Specht", "infantry", 300,
   [K(D(7, "09:50"), CB["breymann"][:2], h=180, state="hidden"), K(D(7, "09:51"), CB["breymann"][:2], state="column")] + go(D(7, "09:51"), D(7, "10:15"), [CB["breymann"][:2], (-1490, 1000), (-1470, 700)], 200, "column")[1:] +
   go(D(7, "13:03"), D(7, "13:43"), [(-1470, 700), (-1700, 520), (-1900, 370)], 185) +
   [K(D(7, "15:06"), (-1900, 370), state="firing"), K(D(7, "15:44"), (-1900, 370), state="firing", strength=240), K(D(7, "15:50"), (-1900, 370), state="rout", h=40, strength=210),
    K(D(7, "16:10"), (-1550, 650), strength=180), K(D(7, "16:25"), (-1350, 560), h=250, state="line", strength=170)] + night7("german", "22:20", (-1350, 560)) + retreat("german", "22:30"), ranks=3)
def recon_guns(id, short, name, cmd, n, guns, spot, lost_at, keys=None):
    k = [K(D(7, "09:50"), (-1350, 700), h=180, state="hidden"), K(D(7, "09:51"), (-1350, 700), state="column")] + go(D(7, "13:05"), D(7, "13:45"), [(-1350, 700), (-1500, 580), spot], 185) + [K(D(7, "14:58"), spot, state="firing")]
    k += keys or [K(D(7, lost_at), spot, state="surrender", strength=n // 3), K(D(7, "16:30"), spot, state="hidden")]
    br(id, short, name, cmd, "artillery", n, k, guns=guns)
recon_guns("twelves", "12-pounders", "Two 12-pounders and two 6-pounders with the grenadiers; overrun with all their horses killed", "Maj. Griffith Williams RA (taken)", 45, 4, (-1530, 410), "15:12")
recon_guns("sixes", "6-pounders", "Two British 6-pounders in the centre with Pausch's guns", "", 24, 2, (-1820, 378), "15:50")
recon_guns("howitzers", "Howitzers", "Two howitzers, the only guns of the reconnaissance to get back", "", 14, 2, (-1460, 420), None,
           [K(D(7, "15:14"), (-1460, 420), state="column", h=30), K(D(7, "15:50"), (-1330, 700), h=250, state="line", strength=12)] + night7("howitzers", "22:40", (-1330, 700)) + retreat("howitzers", "23:30"))
br("breyguns", "Breymann's guns", "The two guns in Breymann's works", "", "artillery", 20,
   [K(D(30, "12:00"), (-1440, 1180), h=270, state="hidden"), K(D(30, "12:01"), (-1440, 1180), state="line"), K(D(7, "17:30"), (-1440, 1180), state="firing"),
    K(D(7, "17:52"), (-1440, 1180), state="surrender", strength=8), K(D(7, "19:00"), (-1440, 1180), state="hidden")], guns=2)
br("funeral", "Fraser's burial", "The party carrying Fraser's body from the Taylor house to the Great Redoubt", "Chaplain Brudenel", "infantry", 30,
   [K(D(8, "17:20"), TAYLOR, h=270, state="hidden")] + go(D(8, "17:21"), D(8, "17:40"), [TAYLOR, (1050, 800), BURIAL], 270) + [K(D(8, "18:15"), BURIAL, state="hidden")], ranks=2)
# The 20th, 21st and 62nd go back to the Great Redoubt on the night of 7 October and march with the main body.
for id, t0, r in [("r62", "21:50", "22:15"), ("r20", "22:00", "22:05"), ("r21", "22:10", "22:20")]:
    next(u for u in units if u["id"] == id)["keys"] += night7(id, t0, CB[id][:2]) + retreat(id, r)

# ---- Ground ----
BAL = [(-1440, 1000), (-1330, 1010), (-1300, 800), (-1310, 600), (-1380, 560), (-1450, 620), (-1430, 800)]
AM_LINE = [(-260, -1850), (-950, -1750), (-1300, -1520), (-1620, -1365), (-1790, -1640), (-1850, -2050)]
BR_LINE = [(-1310, 620), (-1000, 500), (-600, 400), (-200, 320), (250, 250), (600, 230)]
FIELDS = [ellipse(-1360, 790, 175, 88), [(-2160, 230), (-1940, 230), (-1940, 430), (-2160, 430)], [(-1910, 280), (-1690, 280), (-1690, 480), (-1910, 480)],
          ellipse(*CHATFIELD, 90, 90, 10), ellipse(*NEILSON, 170, 150), ellipse(*WOODWORTH, 100, 90, 10), [(-1590, 1110), (-1475, 1110), (-1475, 1380), (-1590, 1380)],
          [(900, 600), (1180, 640), (1260, 820), (1000, 860), (880, 760)], flats(road_x(RIVER_RD), -100, 1100), flats(road_x(RIVER_RD), -2400, -1500)]
features = [
    dict(type="works", name="American lines on Bemis Heights", pts=AM_LINE, at=[-1150, -1520], rot=-35),
    dict(type="battery", name="river batteries", poly=sq(-960, -1740, 50), at=[-960, -1690]), dict(type="battery", poly=sq(-1620, -1365, 40)), dict(type="battery", poly=sq(-1850, -2050, 40)),
    dict(type="works", name="Balcarres Redoubt", pts=BAL + BAL[:1], at=[-1200, 560], **{"from": D(20, "14:00")}), dict(type="redoubt", poly=sq(-1650, 820, 30), **{"from": D(20, "14:00")}),
    dict(type="works", name="Breymann's works", pts=[(-1455, 1120), (-1470, 1240), (-1460, 1350)], at=[-1360, 1380], **{"from": D(30, "12:00")}),
    *[dict(type="redoubt", poly=sq(x, y, 16), **{"from": D(20, "13:30"), "until": D(7, "17:35")}) for x, y in [(-1420, 1040), (-1390, 1075)]],
    dict(type="works", name="British lines", pts=BR_LINE, at=[-450, 300], rot=-15, **{"from": D(21, "12:00")}),
    *[dict(type="redoubt", poly=sq(x, y, 45), **{"from": D(20, "14:00")}) for x, y in [(840, 520), (830, 650), (827, 778)]],
    dict(type="road", name="bridge of boats", pts=[(1000, 110), (1400, 110)], at=[1200, 40], **{"from": D(22, "12:00"), "until": D(8, "21:00")}),
    dict(type="road", name="river road to Albany", pts=RIVER_RD, at=[-620, -2050], rot=-55), dict(type="road", name="Wilbur Road", pts=WILBUR, at=[300, 2600], rot=14),
    dict(type="road", name="Quaker road", pts=FR_RT[-3:], at=[-2020, 1550], rot=-88), dict(type="road", name="Phillips Road", pts=HAM_RT[2:], at=[220, 1450], rot=-88),
    dict(type="road", pts=FREEMAN_RD), dict(type="road", pts=[(-2300, 320), (-1600, 345)]), dict(type="road", pts=LATERAL),
    dict(type="fence", name="Weiser's fence", pts=[(-2160, 330), (-1940, 330), (-1910, 380), (-1690, 380)], at=[-2050, 280], **{"until": D(8, "12:00")}),
    dict(type="creek", name="Mill Creek, the Middle Ravine", pts=MILL, at=[-1300, 30], rot=-10), dict(type="creek", name="Kroma Kill, the Great Ravine", pts=KROMA, at=[480, 820], rot=-45),
    dict(name="Hudson River", at=[1070, -700], rot=-88), dict(name="Freeman's farm", at=[-1360, 780]), dict(name="Barber's wheatfield", at=[-1930, 200]),
    dict(name="Chatfield farm", at=[-1809, -460]), dict(name="Neilson farm", at=[-1800, -1240]), dict(name="Gates's headquarters", at=[-1900, -1720]),
    dict(name="Burgoyne's headquarters", at=[28, 520], **{"from": D(20, "12:00")}), dict(name="Taylor house", at=[1263, 870]), dict(name="Great Redoubt", at=[650, 450], **{"from": D(20, "14:00")}),
    dict(name="British hospital", at=[1020, 330], **{"from": D(20, "12:00")}), dict(name="Canadian cabins", at=[-1250, 1060], **{"from": D(20, "13:30"), "until": D(7, "17:35")}),
    dict(name="Sword's House", at=[2050, 3100]), dict(name="to Saratoga", at=[1950, 3300], rot=-70), dict(name="to Stillwater and Albany", at=[-1300, -3350], rot=-85),
    dict(name="Bemis Heights", at=[-1300, -2250], rot=-35), dict(name="Fraser fell here", at=[-2108, 470], **{"from": D(7, "15:42")}),
    dict(name="Arnold wounded", at=[-1600, 1180], **{"from": D(7, "17:52")}), dict(name="Fraser's grave", at=[700, 790], **{"from": D(8, "17:40")}),
]
events = [
    (D(19, "09:00"), "Three columns", "Burgoyne's army, about 7,000 men, moves south from its camp at Sword's House toward Gates on Bemis Heights, three miles off through thick woods. Fraser takes the right through the forest with the Advanced Corps and Breymann's Germans. Hamilton's brigade, with Burgoyne, takes the centre by a road over the Great Ravine. Riedesel and Phillips keep the left on the river road with the heavy guns and the boats. A morning fog hides both armies.", [100, 2300], 5000, 300),
    (D(19, "11:00"), "The signal gun", "Riedesel records the signal gun at eleven. Hamilton's column crosses the Great Ravine by a small bridge and turns west for Freeman's farm. On the river road Riedesel's column halts beyond the Taylor house to rebuild bridges. Gates keeps most of his army in the works, wary of the column on the river road, and sends Morgan's riflemen and Dearborn's light infantry up the road from the Neilson farm.", [0, 1900], 4600, 300),
    (D(19, "12:30"), "Freeman's farm", "The British picquets come out into Freeman's clearing, an old farm of stumps and weeds, and are shot down from the house and the fences by Morgan's riflemen. Almost every picquet officer is hit. The riflemen chase the survivors straight into Hamilton's main body, are fired on and scatter back into the woods.", [-1380, 850], 1300, 30),
    (D(19, "13:00"), "Poor's regiments", "Morgan rallies his men on the south edge of the clearing. Gates sends Cilley's and Scammell's New Hampshire regiments up to Morgan's left. Fraser's light infantry, on the high ground to the west, has its first brush with them. The firing dies down for a while about half past one.", [-1450, 700], 1800, 60),
    (D(19, "14:00"), "Hamilton's line", "About two o'clock the British regiments come out opposite the Freeman house: the 21st on the right, the 62nd in the centre, the 20th on the left, Jones's four guns between them and the 9th in reserve behind a ravine. One gun fires a shot through the empty house. Hale's New Hampshire, Van Cortlandt's and Livingston's New York regiments and the Connecticut militia come up one after another, stretching the American line west toward Fraser.", [-1550, 800], 1800, 60),
    (D(19, "15:00"), "The action becomes general", "By three every regiment in the centre is in action across the clearing, at close range, in smoke. The Americans fire from the edge of the woods. Wilkinson says no American general came onto the field until evening; the Park Service has Arnold directing the regiments as they arrived. Fraser holds his height on the right and is only partly engaged.", [-1500, 790], 1500, 60),
    (D(19, "16:00"), "The clearing", "For three hours the fight swings back and forth over the field. The 62nd charges into the woods four times and is shot back each time. The guns are taken and retaken; 36 of Jones's 48 gunners are hit and Jones is killed. Phillips brings four more guns across from the river road to steady the line. Breymann's grenadiers turn back an attempt to get round Fraser's right.", [-1400, 800], 1500, 60),
    (D(19, "17:00"), "Riedesel marches", "Riedesel hears the firing grow and asks Burgoyne for leave to help. He takes his own regiment, two companies of Rhetz and Pausch's two guns back over the ravine and about a mile and a half through the woods toward the sound. Toward evening Learned's brigade comes up on the American left and meets Fraser's light infantry and some Germans.", [-900, 750], 2800, 120),
    (D(19, "18:00"), "Riedesel strikes", "About six, with the sun going down, the Brunswickers come out on the American right at the double with their drums beating. Pausch's guns fire grape into the woods. The Germans cross a muddy ditch, fire into the American flank and go in with the bayonet. The Americans give way.", [-1200, 720], 1400, 60),
    (D(19, "19:00"), "Darkness", "Firing ends about seven, when darkness separates the two sides, and the Americans go back to Bemis Heights. The British hold the field and lie on their arms all night in the cold. Burgoyne has lost about 600 men, the 62nd more than half its strength. Gates reports 65 killed, 218 wounded and 38 missing.", [-1500, 400], 3000, 300),
    (D(20, "12:00"), "The fortified camp", "Burgoyne forms to attack again in the fog of the 20th, then calls it off at Fraser's advice: the grenadiers are worn out. He entrenches where he stands. Fraser's corps builds a log and earth redoubt round Freeman's farm. The camp stretches east over the plateau to three redoubts on the bluff above the river, the Great Redoubt, guarding the hospital, the stores and the boats on the flats below.", [-300, 650], 3800, 1800),
    (D(22, "12:00"), "Digging in", "A bridge of boats goes across the Hudson below the Great Redoubt. For two weeks more than a thousand men a day cut trees for a field of fire in front of the British lines. The pickets face each other across the Middle Ravine by the Chatfield farm, and there are alarms and sniping every night.", [-500, 0], 5000, 1800),
    (D(30, "12:00"), "Breymann's post", "On a rise north-west of Freeman's farm Breymann's Germans build a wall of logs about 750 feet long, commanding the road into the rear of the British camp. Two stockaded cabins between it and the Balcarres works are given to two companies of Canadians. Militia keep coming in to Gates; Burgoyne's army shrinks.", [-1400, 1100], 1800, 1800),
    (D(4, "12:00"), "Council of war", "On 4 October Burgoyne cuts the rations and calls a council of war. No help has come from the south: Clinton takes the Highlands forts on the 6th, but the news never reaches Burgoyne. He decides on a reconnaissance in force against the American left.", [-500, 0], 5000, 1800),
    (D(7, "10:00"), "The reconnaissance in force", "At ten about 1,500 regulars, drawn from every regiment but the 47th, parade on the right of the camp with ten guns. Burgoyne, Phillips, Riedesel and Fraser all go with them. The light infantry and the 24th will take the right, about 300 Germans the centre and the grenadiers with most of the guns the left. The rest of the army stays in the lines.", [-1450, 750], 1600, 300),
    (D(7, "13:00"), "Barber's wheatfield", "About one the column moves off south-west and deploys across Barber's wheatfield above the Middle Ravine, a front of more than 1,000 yards with woods on both flanks. Foragers cut the wheat; officers climb onto a cabin roof with telescopes. Wilkinson rides forward to watch them. Gates tells him to order Morgan to begin. Morgan circles west through the woods for the height on the British right; Poor goes for their left.", [-1900, 200], 2600, 120),
    (D(7, "15:00"), "Poor and the grenadiers", "About three the British guns open. Poor's brigade comes up through the brush against the grenadiers, takes their fire and charges. The grenadiers break, rally and are overrun; every gun horse is killed and Cilley sits astride a captured 12-pounder. Acland and Williams of the artillery are taken. On the right Morgan's riflemen come in on the flank of the light infantry, and Dearborn's men fire, jump the fence and charge.", [-1900, 380], 1500, 60),
    (D(7, "15:30"), "Fraser falls", "Learned's brigade is thrown back by the Germans in the centre, then comes on again with Arnold at its head. The light infantry, called back by a misunderstanding, leaves the Germans open on both sides. Fraser rides along the line on a grey horse to rally it and is shot through the body; the shot was later credited to Timothy Murphy, a story Luzader thinks was invented in the nineteenth century. Ten Broeck's Albany militia come up behind Learned.", [-2000, 380], 1500, 60),
    (D(7, "16:00"), "Back to the works", "Wilkinson says the British line gave way 52 minutes after the first shot. Within the hour the survivors are back in the Balcarres Redoubt, leaving eight guns and more than 400 killed, wounded and taken. Lincoln brings Paterson's brigade and Putnam's two regiments out of the river works.", [-1650, 600], 2200, 120),
    (D(7, "17:00"), "Arnold at the Balcarres Redoubt", "Arnold takes Poor's men straight at the log and earth walls round Freeman's farm. The light infantry and the 24th fire over the parapet and Phillips's guns fire grape, and the attack is beaten off. Paterson's brigade comes into line in front of the works.", [-1500, 750], 1300, 60),
    (D(7, "17:30"), "The Canadian cabins", "Arnold rides north between the lines, under fire from both, to Learned's men, who drive the Canadians out of the cabins between the two redoubts. That opens the way round the south end and the rear of Breymann's works. Morgan, Dearborn and Putnam are in the woods in front of it, about 120 yards off.", [-1500, 1150], 1100, 60),
    (D(7, "17:50"), "Breymann's redoubt", "A few minutes after sunset Putnam's Massachusetts men storm across the open field into the front of Breymann's works while Learned's come in at the south end and Arnold rides in at the rear. Within five minutes the Germans are overturned. Breymann is killed. Arnold's horse is killed under him and he is wounded in the leg. The Americans take the tents, the guns and the baggage, and the British right is open.", [-1470, 1230], 900, 30),
    (D(7, "18:30"), "Night", "Darkness ends the fighting. A German counter-attack under Lt. Col. von Speth loses its way in the dark and is captured. Burgoyne gives up the camp: the tents are struck, the guns and baggage taken down toward the river and the fires left burning. Before daybreak the army is round the Great Redoubt and the hospital flats.", [-300, 800], 3800, 600),
    (D(8, "08:00"), "The abandoned camp", "The Americans march into the empty British camp and push riflemen up close to the Great Redoubt; they try to put a battery in and are shelled off. Fraser dies at the Taylor house: about eight by Baroness Riedesel's account, about eleven by Digby's. A sharpshooter's ball breaks General Lincoln's leg. At noon the 9th and the 47th set off north as the vanguard of the retreat.", [300, 700], 2800, 1800),
    (D(8, "17:40"), "Fraser's burial", "As he asked, Fraser is buried in one of the redoubts on the bluff. Digby has it at sunset, Baroness Riedesel at six exactly. The chaplain reads the service under American cannon fire. Gates said later that he would not have fired had he known what it was.", [830, 760], 900, 60),
    (D(8, "21:00"), "The retreat", "About nine, Burgoyne says, the army moves off north up the river road in heavy rain, Riedesel in the van and Phillips in the rear. More than 800 sick and wounded stay behind in the hospital with a letter to Gates. The pontoons of the bridge are taken up.", [1300, 1500], 3000, 600),
    (D(9, "04:00"), "Saratoga", "About four in the morning Digby's grenadiers, the rear guard, follow, breaking the bridges behind them. The army reaches Saratoga, off the map to the north, on the night of the 9th. On 17 October it marches out at ten and grounds its arms; at noon Burgoyne surrenders to Gates.", [1800, 2500], 3500, 600),
]
# Hold in place through long gaps: without this a unit creeps toward a key hours away and the time-lapse never engages.
def add_holds(units):
    ts = lambda s: dt.datetime.strptime(s[:16], "%Y-%m-%d %H:%M").timestamp()
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
add_holds(units)
for u in units:  # a key's place must be dry ground, and so must the road between keys
    for a, c in zip(u["keys"], u["keys"][1:] + [None]):
        if a.get("state") == "hidden": continue
        c = c or a
        for f in (0, 0.25, 0.5, 0.75):
            x, y = a["x"] + (c["x"] - a["x"]) * f, a["y"] + (c["y"] - a["y"]) * f
            if z(x, y) <= WATER: print("in the river:", u["id"], a["t"], round(x), round(y))
battle = dict(
    id="saratoga", name="Saratoga", date="1777-09-19", dateText="19 September to 8 October 1777", place="Freeman's Farm and Bemis Heights, Stillwater, New York",
    origin=dict(lat=42.99800, lon=-73.62100), extent=7000, start=D(19, "09:00"), end=D(9, "05:40"), speed=120, lapse=43200, menPerDot=10,
    sunrise="06:04", sunset="17:56", water=WATER, terrainExaggeration=2, contourInterval=5, trees=dict(density=0.001),
    wind=dict(x=0.5, y=0.3), palette=dict(ground="#a6ab80", high="#d2cc9e", tree="rgba(55,85,45,0.5)", water="#7f9fc0"), fields=FIELDS,
    view=dict(x=-600, y=500, width=5200),
    tints=[dict(color="rgba(232,234,232,0.45)", **{"from": D(19, "09:00"), "until": D(19, "10:20")}), dict(color="rgba(150,160,178,0.35)", **{"from": D(8, "18:10"), "until": D(9, "05:40")})],
    sides=dict(american=dict(name="Americans (Gates)", color="#2a63c4", light="#5a8fe0", dark="#163a7a"),
               british=dict(name="British and Germans (Burgoyne)", color="#c9332e", light="#e06a5a", dark="#6e1b18")),
    features=features, units=units,
    events=[dict(t=t, title=a, text=b, at=at, view=v, speed=s) for t, a, b, at, v, s in events],
    outcome={"result": "American victory: Burgoyne surrenders at Saratoga, 17 October", "losses": [
        ["american", "Freeman's Farm: 65 killed, 218 wounded, 38 missing (Gates's return). Bemis Heights: about 150 killed and wounded, Arnold among the wounded."],
        ["british", "Freeman's Farm: about 600 killed and wounded. Bemis Heights: over 600 killed, wounded and taken, with Fraser and Breymann dead and ten guns lost. The returns of 17 October counted 3,379 British and 2,202 Germans."]],
        "note": "Burgoyne put his own loss on 19 September at 500 or more; the Park Service gives 590 and 630 for the two days. Gates's army had grown past 13,000 rank and file present by the surrender."},
    sources=[
        "John Burgoyne, <i>A State of the Expedition from Canada, as laid before the House of Commons</i> (London: J. Almon, 1780): his letter to Germain of 20 October 1777 and the testimony of Balcarres, Money, Harrington, Forbes, Bloomfield and Kingston.",
        "William Digby, journal, in James Phinney Baxter, ed., <i>The British Invasion from the North ... with the Journal of Lieut. William Digby</i> (Albany: Joel Munsell's Sons, 1887), with Baroness Riedesel's account in the notes and the returns of 17 October 1777.",
        "Max von Eelking, <i>Memoirs, and Letters and Journals, of Major General Riedesel during his Residence in America</i>, trans. William L. Stone, 2 vols. (Albany: Munsell, 1868), vol. 1.",
        "James Wilkinson, <i>Memoirs of My Own Times</i>, vol. 1 (Philadelphia: Abraham Small, 1816). Gates's adjutant-general, hostile to Arnold.",
        "John Luzader, <i>Historic Structure Report: The Right Wing of the British Fortified Camp at Saratoga, Balcarres and Breymann Redoubts</i> (Saratoga NHP, c.1973), quoting Hadden, Pausch, Uhlig, Milius, Riedesel's papers, Kingston, Rufus Putnam, Benjamin Warren and Dearborn.",
        "<i>Saratoga National Historical Park, New York</i>, NPS Historical Handbook No. 4 (1950, rev. 1959); NPS, Saratoga NHP: \"Battle of Freemans Farm\", \"Battle of Bemus Heights\", the Battlefield Road Audio Tour, tour stops 2 to 7, the park brochure (2024) and the Battles of Saratoga Student Research Packet.",
        "Richard M. Ketchum, <i>Saratoga: Turning Point of America's Revolutionary War</i> (1997); John F. Luzader, <i>Saratoga: A Military History of the Decisive Campaign of the American Revolution</i> (2008); Hoffman Nickerson, <i>The Turning Point of the Revolution</i> (1928): read through Wikipedia, \"Battles of Saratoga\" and \"Battle of Bemis Heights order of battle\".",
        "Mark Maloy, \"The Battle of Freeman's Farm\" (American Battlefield Trust, 2021), and the Trust's Saratoga battle page.",
        "Places: OpenStreetMap contributors (ODbL), the NPS tour stops and memorials, US 4, Wilbur and Phillips Roads. Terrain: USGS 3DEP elevation at 23 m over a 7 km square, with the Hudson at its canal pool, about 25 m.",
        "What is reconstructed: the line of the reconnaissance on 7 October (placed from the Park Service's descriptions, not the 1780 engraved plans, within about 250 m); the field outlines; Fraser's position and Riedesel's route on 19 September; the hours between recorded moments (the sources disagree by up to two hours on when the reconnaissance set out and when Poor attacked); the strength of every regiment, apportioned from brigade and column totals; the losses by regiment, split from each side's total for the day; the place of the American guns on 8 October; the arrival of Ten Broeck's militia; and the British camp line. The Middle and Great Ravines are taken to be Mill Creek and the Kroma Kill. Sunrise and sunset are set midway between 19 September and 7 October, which differ by about 25 minutes.",
    ],
)
WHEN = {"Three columns": "9:00 AM", "The signal gun": "11:00 AM", "Freeman's farm": "about 12:30 PM", "Poor's regiments": "1:00 PM", "Hamilton's line": "about 2:00 PM",
        "The action becomes general": "3:00 PM", "Riedesel strikes": "about 6:00 PM", "Darkness": "7:00 PM", "The fortified camp": "noon",
        "The reconnaissance in force": "10:00 AM", "Barber's wheatfield": "about 1:00 PM", "Poor and the grenadiers": "about 3:00 PM", 
        "Breymann's redoubt": "a few minutes after sunset", "The abandoned camp": "8:00 AM", "Fraser's burial": "sunset", "The retreat": "9:00 PM", "Saratoga": "about 4:00 AM"}  # chapter times the sources record; the story gives the others to the nearest hour
for e in battle["events"]:
    if e["title"] in WHEN: e["when"] = WHEN[e["title"]]
json.dump(battle, open("battles/saratoga/battle.json", "w"), indent=1)
print(len(units), "units,", len(events), "events,", len(features), "features; Mill Creek", len(MILL), "Kroma Kill", len(KROMA))
