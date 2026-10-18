# Builds battles/trenton-princeton/battle.json. Run from the repo root: python3 battles/trenton-princeton/make.py
# Local metres from 40.2850N 74.7650W (x east, y north), open ground between Trenton and Lawrenceville. The 22 km
# square holds McConkey's Ferry (-9273,1147), Trenton (the Battle Monument at 19,-6585) and Princeton (Nassau Hall
# at 8968,7090). The Delaware and the creeks are traced from the elevation grid: the river falls from the ferry to
# Trenton, so no single water level fits it. Positions follow Stryker (1898), Fischer (2004) and the Trenton
# Historical Society's street plan; anchors off the modern road net are good to a few hundred metres.
import json, math, datetime as dt
T = json.load(open("battles/trenton-princeton/terrain.json"))
COLS, SP = T["cols"], T["spacing"]; HALF = COLS * SP / 2; STEP = int(SP / 2)
def z(x, y):
    c, r = int((x + HALF) / SP), int((HALF - y) / SP)
    return T["z"][r * COLS + c] if 0 <= c < COLS and 0 <= r < COLS else 999
def low(x, y, rad=300):  # lowest cell near a point: a creek bed
    best = (999, x, y)
    for dx in range(-rad, rad + 1, STEP):
        for dy in range(-rad, rad + 1, STEP):
            v = z(x + dx, y + dy)
            if v < best[0]: best = (v, x + dx, y + dy)
    return (best[1], best[2])
def river(centre, search=900, tol=1.5, maxhalf=320):  # a water polygon from the grid: at each step find the bed, then the banks
    L, R = [], []
    for i in range(1, len(centre)):
        (x0, y0), (x1, y1) = centre[i - 1], centre[i]
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / 150))
        for k in range(n):
            x, y = x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n
            dx, dy = x1 - x0, y1 - y0; m = math.hypot(dx, dy); px, py = -dy / m, dx / m
            bed = min(range(-search, search + 1, STEP), key=lambda s: z(x + px * s, y + py * s))
            zb = z(x + px * bed, y + py * bed)
            a = bed
            while a > bed - maxhalf and z(x + px * (a - SP / 2), y + py * (a - SP / 2)) <= zb + tol: a -= SP / 2
            b = bed
            while b < bed + maxhalf and z(x + px * (b + SP / 2), y + py * (b + SP / 2)) <= zb + tol: b += SP / 2
            a, b = a - SP / 4, b + SP / 4
            L.append((round(x + px * a), round(y + py * a))); R.append((round(x + px * b), round(y + py * b)))
    return L + R[::-1]
DELAWARE = river([(-10950, 2900), (-9900, 1800), (-8773, 1136), (-7500, -255), (-6000, -1900), (-4500, -3540), (-3000, -5180), (-2000, -6280), (-1114, -7250), (-600, -7900),
                  (-278, -8300), (-700, -8900), (-1300, -9500), (-1500, -10200), (-1600, -10950)], search=250, tol=1.2, maxhalf=260)  # through the two Trenton bridges
ASSUNPINK = [low(*p) for p in [(6454, -111), (5600, -1500), (4700, -2800), (3600, -4300), (2300, -5800)]] + [(1300, -6800), (764, -7236), (85, -7525), (-425, -8015)]
STONY = [low(*p) for p in [(4600, 4500), (5500, 5200), (6326, 5399), (6556, 4865), (7400, 4500), (8500, 4300), (9600, 4700), (10950, 5200)]]
SHABAKUNK = [low(*p) for p in [(3200, -2400), (2100, -2800), (1061, -3228), (-300, -4100), (-1600, -4900), (-2900, -5600)]]
JACOBS = [low(*p) for p in [(-4700, 800), (-5400, 300), (-6072, -111), (-6700, -600), (-7300, -900)]]

D = lambda d, hm: f"{'1776-12' if d >= 25 else '1777-01'}-{d:02d} {hm}"
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
units = []
def unit(id, short, side, name, commander, type, strength, keys, **extra):
    units.append(dict(id=id, side=side, name=name, short=short, commander=commander, type=type, strength=strength, keys=keys, **extra))
us = lambda *a, **k: unit(a[0], a[1], "american", *a[2:], **k)
br = lambda *a, **k: unit(a[0], a[1], "british", *a[2:], **k)

WEST, FERRY_PA, FERRY_NJ, BEAR, JACOB, BIRM = (-10900, 1100), (-9273, 1147), (-8767, 1592), (-6963, 2560), (-6072, -111), (-4501, -2171)
PENN_RD, PICKET, HEAD = (-3057, -3340), (-1189, -5455), (19, -6585)
RIVER_RD, HERMITAGE, BARRACKS, BRIDGE, MILLHILL = (-4300, -3500), (-1741, -6590), (-318, -7252), (85, -7525), (300, -7700)
SANDTOWN, QUAKER_BR, MEETING, WORTH, COCHRAN, ORCHARD, TCLARKE, FIELD = (6072, -5510), (6454, -111), (6556, 4865), (6326, 5399), (5859, 5009), (7218, 5343), (7379, 5043), (7450, 5250)
FROG, BREASTWORK, NASSAU, NE, MAIDENHEAD, FIVEMILE, SHAB, STOCKTON = (8067, 6568), (8577, 6902), (8968, 7090), (10900, 8900), (3015, 1369), (2548, 0), (1061, -3228), (764, -5789)
TO_FERRY = [FERRY_NJ, BEAR, JACOB, BIRM]
GREENE_RD = [BIRM, PENN_RD, (-2100, -4500), PICKET, HEAD]
SULLIVAN_RD = [BIRM, RIVER_RD, (-3000, -5000), HERMITAGE, (-900, -7050), BARRACKS]
BACK = [HEAD, PICKET, (-2100, -4500), PENN_RD, BIRM, JACOB, BEAR, FERRY_NJ]
NIGHT = [MILLHILL, (2500, -7000), SANDTOWN, (6300, -3000), QUAKER_BR, (6500, 2400), MEETING]
POST_S = [NASSAU, (8577, 6902), (7600, 6100), WORTH, COCHRAN, (4600, 3000), MAIDENHEAD, FIVEMILE, (1800, -1700), SHAB, STOCKTON, HEAD]

# ---- the army of 25 December: crossing, march, fight, return, recrossing, and the camp south of the Assunpink ----
def crossing(t_cross0, t_cross1, t_fight_keys, back_t0, lead=0):
    """Column from the Pennsylvania bank over the ferry, the march on Trenton, the fight, the march back and the recrossing,
    then hidden in Pennsylvania until the second crossing on 29-30 December and the camp at Trenton."""
    keys = [K(D(25, "14:30"), WEST, h=90, state="column"), K(D(25, "16:00"), FERRY_PA), K(t_cross0, FERRY_PA), K(t_cross1, FERRY_NJ), K(D(26, "04:00"), FERRY_NJ)]
    keys += march(D(26, "04:00"), D(26, "06:45"), TO_FERRY)[1:]
    keys += t_fight_keys
    keys += march(back_t0, fmt(sec(back_t0) + 5 * 3600), BACK)[1:] + [K(fmt(sec(back_t0) + 7 * 3600), FERRY_PA), K(fmt(sec(back_t0) + 7.1 * 3600), FERRY_PA, state="hidden")]
    keys += [K(D(29, "10:00"), FERRY_PA, h=90, state="column"), K(D(30, "08:00"), FERRY_NJ)] + march(D(30, "08:00"), D(30, "14:00"), TO_FERRY + GREENE_RD[1:] + [BRIDGE])[1:]
    return keys
def greene(id, short, name, cmd, n, t0, t1, fight, back, **x):
    us(id, short, name, cmd, "infantry", n, crossing(t0, t1, march(D(26, "06:45"), D(26, "08:00"), GREENE_RD)[1:] + fight, back), **x)
def sullivan(id, short, name, cmd, n, t0, t1, fight, back, **x):
    us(id, short, name, cmd, "infantry", n, crossing(t0, t1, march(D(26, "06:45"), D(26, "08:05"), SULLIVAN_RD)[1:] + fight, back), **x)
# Fights on 26 December, then the Assunpink line on 2 January and Princeton on 3 January, appended per brigade below.
def camp(p, h=0): return [K(D(30, "14:30"), p, h=h, state="line")]
def assunpink(p, h=0, hold=True):  # the line on Mill Hill from the evening of 2 January; firing at the bridge attacks
    return [K(D(2, "15:30"), p, h=h, state="line")] + ([K(D(2, "17:00"), p, state="firing"), K(D(2, "18:00"), p, state="line")] if hold else [])
def night(t_leave, t_arrive): return march(t_leave, t_arrive, NIGHT)
greene("stephen", "Stephen", "Stephen's brigade: 4th, 5th and 6th Virginia, the advance guard", "Brig. Gen. Adam Stephen", 450, D(25, "18:00"), D(25, "19:30"),
       [K(D(26, "08:06"), (-60, -6420), h=180, state="line"), K(D(26, "08:12"), (-60, -6420), state="firing"), K(D(26, "08:40"), (-60, -6420), state="line"), K(D(26, "09:00"), (300, -6700), h=160, state="firing"),
        K(D(26, "09:20"), (300, -6700), state="line"), K(D(26, "12:00"), (300, -6700))], D(26, "12:10"))
units[-1]["keys"] += camp((-200, -8000), 20) + assunpink((-300, -7900), 20) + night(D(3, "01:20"), D(3, "07:30")) + march(D(3, "08:20"), D(3, "08:40"), [MEETING, (7000, 5000), (7350, 5350)]) + \
    [K(D(3, "08:40"), (7350, 5350), h=20, state="firing"), K(D(3, "08:48"), (7350, 5350), state="line", strength=440)] + march(D(3, "09:10"), D(3, "10:00"), [(7350, 5350), (7900, 6000), (8577, 6902)]) + march(D(3, "11:00"), D(3, "12:30"), [(8577, 6902), NASSAU, NE]) + [K(D(3, "12:31"), NE, state="hidden")]
greene("mercer", "Mercer", "Mercer's brigade: 20th and 27th Continental, 1st Virginia, Smallwood's Maryland and Haslet's Delaware", "Brig. Gen. Hugh Mercer (mortally wounded 3 Jan)", 350, D(25, "19:30"), D(25, "21:00"),
       [K(D(26, "08:15"), (-500, -6900), h=90, state="line"), K(D(26, "08:20"), (-500, -6900), state="firing"), K(D(26, "08:45"), (-350, -6950), state="line"), K(D(26, "09:00"), (-350, -6950), state="firing"), K(D(26, "09:20"), (-350, -6950), state="line"), K(D(26, "12:00"), (-350, -6950))], D(26, "12:15"))
units[-1]["keys"] += camp((50, -7900), 20) + assunpink((100, -7750), 20) + night(D(3, "01:10"), D(3, "07:20")) + march(D(3, "07:45"), D(3, "08:05"), [MEETING, (6500, 5200), (6900, 5350)]) + \
    [K(D(3, "08:10"), ORCHARD, h=250, state="line"), K(D(3, "08:12"), ORCHARD, state="firing"), K(D(3, "08:17"), ORCHARD, state="rout", strength=310), K(D(3, "08:24"), (7500, 5050), strength=300), K(D(3, "08:40"), (7650, 5000), h=270, state="line"),
     K(D(3, "08:46"), (7650, 5000), state="charge"), K(D(3, "08:52"), (7300, 5300), state="line", h=270)] + march(D(3, "09:20"), D(3, "10:10"), [(7300, 5300), (7900, 6000), (8577, 6902)]) + march(D(3, "11:05"), D(3, "12:35"), [(8577, 6902), NASSAU, NE]) + [K(D(3, "12:36"), NE, state="hidden")]
greene("stirling", "Stirling", "Stirling's brigade, with Weedon's 3rd Virginia, which charged down King Street and took the Hessian guns", "Brig. Gen. William Alexander, Lord Stirling", 500, D(25, "21:00"), D(25, "22:30"),
       [K(D(26, "08:10"), (-130, -6500), h=180, state="line"), K(D(26, "08:20"), (-130, -6500), state="charge"), K(D(26, "08:26"), (-110, -6850), state="firing"), K(D(26, "08:45"), (-110, -6850), state="line"), K(D(26, "09:00"), (50, -6900), h=120, state="firing"),
        K(D(26, "09:20"), (50, -6900), state="line"), K(D(26, "12:00"), (50, -6900))], D(26, "12:20"))
units[-1]["keys"] += camp((400, -8050), 20) + assunpink((500, -7650), 20) + night(D(3, "01:30"), D(3, "07:40")) + march(D(3, "08:30"), D(3, "08:50"), [MEETING, (7000, 5050), (7250, 5450)]) + \
    [K(D(3, "08:50"), (7250, 5450), h=30, state="firing"), K(D(3, "08:56"), (7250, 5450), state="line", strength=490)] + march(D(3, "09:15"), D(3, "10:05"), [(7250, 5450), (7900, 6000), (8400, 6800)]) + march(D(3, "11:10"), D(3, "12:40"), [(8400, 6800), NASSAU, NE]) + [K(D(3, "12:41"), NE, state="hidden")]
greene("hand", "Hand's riflemen", "Fermoy's brigade: Hand's 1st Pennsylvania Rifles and Haussegger's German Battalion, blocking the Princeton road", "Brig. Gen. de Fermoy; Col. Edward Hand", 350, D(25, "22:30"), D(26, "00:00"),
       [K(D(26, "08:12"), (450, -6250), h=150, state="line"), K(D(26, "08:50"), (450, -6250), state="firing"), K(D(26, "09:20"), (450, -6250), state="line"), K(D(26, "12:00"), (450, -6250))], D(26, "12:25"), loose=True)
units[-1]["keys"] += [K(D(30, "14:30"), (2400, -300), h=0, state="line"), K(D(2, "10:30"), (2400, -300), state="skirmish"), K(D(2, "11:00"), (2400, -300), state="retreat", h=200),
    K(D(2, "12:00"), (900, -3450), state="skirmish", h=10), K(D(2, "14:00"), (900, -3450), state="retreat", h=200, strength=340), K(D(2, "15:00"), (700, -5900), state="skirmish", h=10), K(D(2, "15:40"), (700, -5900), state="retreat", h=190),
    K(D(2, "16:05"), (-50, -7100), state="skirmish", h=0), K(D(2, "16:20"), (-50, -7100), state="retreat", h=180, strength=330), K(D(2, "16:35"), (150, -7800), state="line", h=0)] + \
    night(D(3, "01:40"), D(3, "07:45")) + march(D(3, "08:25"), D(3, "08:40"), [MEETING, (7100, 5100), (7500, 5500)]) + [K(D(3, "08:40"), (7500, 5500), h=300, state="skirmish"), K(D(3, "08:48"), (7500, 5500), state="line", strength=325)] + \
    march(D(3, "09:10"), D(3, "10:00"), [(7500, 5500), (7900, 6000), (8577, 6902)]) + march(D(3, "11:00"), D(3, "12:30"), [(8577, 6902), NASSAU, NE]) + [K(D(3, "12:31"), NE, state="hidden")]
us("greeneguns", "Forrest and Hamilton", "Knox's guns with Greene's column: Forrest's and Hamilton's companies at the head of King and Queen Streets", "Col. Henry Knox; Capt. Thomas Forrest; Capt. Alexander Hamilton", "artillery", 120,
   crossing(D(26, "01:30"), D(26, "03:00"), march(D(26, "06:50"), D(26, "08:08"), GREENE_RD)[1:] + [K(D(26, "08:10"), HEAD, h=180, state="firing", fire=0.5), K(D(26, "09:30"), HEAD, state="line"), K(D(26, "12:00"), HEAD)], D(26, "12:30"))
   + camp((250, -7650), 20) + [K(D(2, "15:30"), (250, -7650), h=10, state="line"), K(D(2, "17:00"), (250, -7650), state="firing", fire=0.6), K(D(2, "18:00"), (250, -7650), state="firing", fire=0.1), K(D(2, "23:30"), (250, -7650), state="line")]
   + night(D(3, "01:50"), D(3, "07:50")) + march(D(3, "08:30"), D(3, "09:40"), [MEETING, (7200, 5100), (7900, 6000), (8700, 6800)]) + [K(D(3, "09:40"), (8700, 6800), h=60, state="firing", fire=0.5), K(D(3, "09:50"), (8700, 6800), state="line")]
   + march(D(3, "11:15"), D(3, "12:45"), [(8700, 6800), NASSAU, NE]) + [K(D(3, "12:46"), NE, state="hidden")], guns=9)
sullivan("stclair", "St Clair", "St Clair's brigade: Stark's, Reed's and Poor's New Hampshire and Paterson's Massachusetts; Stark's bayonet charge on the Knyphausen regiment", "Brig. Gen. Arthur St Clair; Col. John Stark", 350, D(26, "00:00"), D(26, "01:00"),
         [K(D(26, "08:20"), (-150, -7400), h=90, state="line"), K(D(26, "08:35"), (-150, -7400), state="charge"), K(D(26, "08:45"), (250, -7380), state="firing"), K(D(26, "09:35"), (450, -7400), state="firing"), K(D(26, "09:45"), (450, -7400), state="line"), K(D(26, "12:00"), (450, -7400))], D(26, "12:35"))
units[-1]["keys"] += camp((700, -7850), 20) + assunpink((750, -7500), 20) + night(D(3, "01:00"), D(3, "07:15")) + march(D(3, "07:55"), D(3, "08:45"), [MEETING, (7300, 5000), (7800, 5900)]) + \
    [K(D(3, "08:45"), (7800, 5900), h=40, state="firing"), K(D(3, "09:00"), (7800, 5900), state="charge"), K(D(3, "09:12"), FROG, state="firing", strength=345), K(D(3, "09:25"), (8450, 6800), state="line", h=40), K(D(3, "09:40"), (8900, 7000), state="line", h=90), K(D(3, "09:55"), (8900, 7000))] + \
    march(D(3, "11:00"), D(3, "12:20"), [(8900, 7000), NASSAU, NE]) + [K(D(3, "12:21"), NE, state="hidden")]
sullivan("glover", "Glover", "Glover's brigade: the Marblehead regiment that rowed the army over, seizing the Assunpink bridge", "Brig. Gen. John Glover", 250, D(26, "01:00"), D(26, "02:00"),
         [K(D(26, "08:25"), (-200, -7500), h=90, state="line"), K(D(26, "08:40"), BRIDGE, h=90, state="line"), K(D(26, "08:50"), (120, -7650), h=0, state="line"), K(D(26, "12:00"), (120, -7650))], D(26, "12:40"))
units[-1]["keys"] += camp((-50, -7650), 20) + assunpink((-50, -7680), 20) + night(D(3, "01:15"), D(3, "07:25")) + march(D(3, "08:05"), D(3, "08:55"), [MEETING, (7400, 4950), (7900, 5800)]) + \
    [K(D(3, "08:55"), (7900, 5800), h=40, state="line"), K(D(3, "09:05"), (7900, 5800), state="charge"), K(D(3, "09:18"), (8200, 6450), state="line", h=40, strength=246)] + march(D(3, "09:30"), D(3, "10:00"), [(8200, 6450), (8600, 6850)]) + march(D(3, "11:05"), D(3, "12:25"), [(8600, 6850), NASSAU, NE]) + [K(D(3, "12:26"), NE, state="hidden")]
sullivan("sargent", "Sargent", "Sargent's brigade: 13th and 16th Continental and Ward's Connecticut", "Col. Paul Dudley Sargent", 250, D(26, "02:00"), D(26, "03:00"),
         [K(D(26, "08:25"), (-500, -7250), h=90, state="line"), K(D(26, "08:45"), (-300, -7150), state="firing"), K(D(26, "09:20"), (-300, -7150), state="line"), K(D(26, "12:00"), (-300, -7150))], D(26, "12:45"))
units[-1]["keys"] += camp((1000, -7750), 20) + assunpink((1000, -7400), 20) + night(D(3, "01:05"), D(3, "07:20")) + march(D(3, "08:00"), D(3, "08:50"), [MEETING, (7350, 4900), (7950, 5700)]) + \
    [K(D(3, "08:50"), (7950, 5700), h=40, state="line"), K(D(3, "09:00"), (7950, 5700), state="charge"), K(D(3, "09:14"), (8150, 6300), state="firing", strength=246), K(D(3, "09:25"), (8300, 6600), state="line", h=40), K(D(3, "09:45"), (8700, 7150), h=90)] + march(D(3, "11:00"), D(3, "12:20"), [(8700, 7150), NASSAU, NE]) + [K(D(3, "12:21"), NE, state="hidden")]
us("sullivanguns", "Sullivan's guns", "Knox's guns with Sullivan's column, Sargent's and Hugg's companies among them; Moulder's two 4-pounders joined for Princeton", "Col. Henry Knox; Capt. Joseph Moulder", "artillery", 120,
   crossing(D(26, "02:00"), D(26, "03:00"), march(D(26, "06:50"), D(26, "08:15"), SULLIVAN_RD)[1:] + [K(D(26, "08:20"), (-350, -7300), h=90, state="firing", fire=0.4), K(D(26, "09:40"), (-350, -7300), state="line"), K(D(26, "12:00"), (-350, -7300))], D(26, "12:50"))
   + camp((-100, -7850), 20) + [K(D(2, "15:30"), (50, -7700), h=10, state="line"), K(D(2, "17:00"), (50, -7700), state="firing", fire=0.6), K(D(2, "18:00"), (50, -7700), state="line")]
   + night(D(3, "01:45"), D(3, "07:45")) + march(D(3, "08:15"), D(3, "08:28"), [MEETING, (7000, 5000), (7420, 5180)]) + [K(D(3, "08:28"), (7420, 5180), h=300, state="firing", fire=0.6), K(D(3, "08:46"), (7420, 5180), state="line", strength=110)]
   + march(D(3, "09:20"), D(3, "10:10"), [(7420, 5180), (7900, 6000), (8500, 6850)]) + march(D(3, "11:20"), D(3, "12:50"), [(8500, 6850), NASSAU, NE]) + [K(D(3, "12:51"), NE, state="hidden")], guns=9)
# Militia and the New England brigade that came up for the second week.
us("cadwalader", "Cadwalader", "Cadwalader's Philadelphia Associators and Pennsylvania militia, up from Crosswicks on the night of 1 January", "Col. John Cadwalader", "militia", 1100,
   [K(D(1, "20:00"), (1500, -10950), h=320, state="column"), K(D(2, "03:00"), (400, -8300), state="line", h=10)] + assunpink((300, -7850), 10) + night(D(3, "01:35"), D(3, "07:45")) +
   march(D(3, "08:15"), D(3, "08:28"), [MEETING, (7000, 4900), (7350, 5150)]) + [K(D(3, "08:28"), (7350, 5150), h=300, state="line"), K(D(3, "08:31"), (7350, 5150), state="firing"), K(D(3, "08:34"), (7350, 5150), state="rout", strength=1080), K(D(3, "08:40"), (7550, 4950)),
   K(D(3, "08:44"), (7550, 4950), h=300, state="line"), K(D(3, "08:50"), (7550, 4950), state="charge"), K(D(3, "08:56"), (7300, 5250), state="line")] + march(D(3, "09:25"), D(3, "10:15"), [(7300, 5250), (7900, 6000), (8300, 6700)]) + march(D(3, "11:10"), D(3, "12:40"), [(8300, 6700), NASSAU, NE]) + [K(D(3, "12:41"), NE, state="hidden")], ranks=3)
us("mifflin", "Mifflin", "Mifflin's Pennsylvania militia, from Bordentown; the right at Princeton", "Brig. Gen. Thomas Mifflin", "militia", 1600,
   [K(D(1, "22:00"), (1800, -10950), h=320, state="column"), K(D(2, "05:00"), (900, -8200), state="line", h=10)] + assunpink((1100, -7300), 10, hold=False) + night(D(3, "02:00"), D(3, "08:00")) +
   march(D(3, "08:30"), D(3, "08:50"), [MEETING, (6900, 5200), (7150, 5600)]) + [K(D(3, "08:50"), (7150, 5600), h=330, state="line"), K(D(3, "09:00"), (7150, 5600))] + march(D(3, "09:30"), D(3, "10:20"), [(7150, 5600), (7900, 6000), (8200, 6900)]) + march(D(3, "11:15"), D(3, "12:45"), [(8200, 6900), NASSAU, NE]) + [K(D(3, "12:46"), NE, state="hidden")], ranks=4)
us("hitchcock", "Hitchcock", "Hitchcock's New England brigade: Rhode Island and Massachusetts Continentals, who broke Mawhood's line", "Col. Daniel Hitchcock", "infantry", 450,
   [K(D(1, "21:00"), (1600, -10950), h=320, state="column"), K(D(2, "04:00"), (0, -8200), state="line", h=10)] + assunpink((-100, -7720), 10) + night(D(3, "01:25"), D(3, "07:35")) +
   march(D(3, "08:20"), D(3, "08:38"), [MEETING, (7100, 4950), (7600, 5150)]) + [K(D(3, "08:38"), (7600, 5150), h=300, state="line"), K(D(3, "08:40"), (7600, 5150), state="firing"), K(D(3, "08:44"), (7600, 5150), state="charge"), K(D(3, "08:50"), (7250, 5350), state="line", strength=438)] +
   march(D(3, "09:20"), D(3, "10:10"), [(7250, 5350), (7900, 6000), (8450, 6750)]) + march(D(3, "11:05"), D(3, "12:35"), [(8450, 6750), NASSAU, NE]) + [K(D(3, "12:36"), NE, state="hidden")])
us("rearparty", "Rear party", "Five hundred men left to feed the fires and dig within earshot of the British, who slipped away before morning", "", "infantry", 500,
   [K(D(2, "15:30"), (200, -7600), h=10, state="line"), K(D(3, "04:00"), (200, -7600), state="column", h=90), K(D(3, "06:30"), (3000, -7200)), K(D(3, "06:31"), (3000, -7200), state="hidden")])
us("kelly", "Kelly's party", "Maj. Kelly's party tearing up the Stony Brook bridge as Leslie's advance guard came up", "Maj. John Kelly", "infantry", 60,
   [K(D(3, "09:30"), (6900, 5300), h=270, state="column"), K(D(3, "09:50"), WORTH, state="line", h=200), K(D(3, "10:05"), WORTH, state="retreat", h=60), K(D(3, "10:30"), (7900, 6000), state="column"), K(D(3, "10:31"), (7900, 6000), state="hidden")])

# ---- Rall's brigade at Trenton ----
def hessian(id, short, name, cmd, n, p, h, keys, **x): br(id, short, name, cmd, "infantry", n, [K(D(25, "14:00"), p, h=h, state="line")] + keys, **x)
hessian("rall", "Rall", "Grenadier Regiment Rall, the regiment of the day, quartered about King and Second Streets", "Col. Johann Rall (mortally wounded)", 430, (-140, -7200), 0,
        [K(D(26, "08:12"), (-140, -7200), state="column"), K(D(26, "08:20"), (-120, -6900), state="firing"), K(D(26, "08:32"), (-120, -6900), state="retreat", h=90, strength=415), K(D(26, "08:42"), (552, -6924), state="line", h=270),
         K(D(26, "08:48"), (552, -6924), state="charge"), K(D(26, "08:56"), (250, -6900), state="firing", strength=405), K(D(26, "09:06"), (250, -6900), state="retreat", h=90), K(D(26, "09:15"), (552, -6924), state="line", h=270, strength=400),
         K(D(26, "09:25"), (552, -6924), state="surrender"), K(D(26, "12:00"), (552, -6924))] + march(D(26, "12:30"), D(26, "19:00"), BACK)[1:] + [K(D(26, "19:01"), FERRY_NJ, state="hidden")], ranks=3)
hessian("lossberg", "Lossberg", "Fusilier Regiment von Lossberg, on upper King Street", "Lt. Col. Francis Scheffer", 380, (-100, -6850), 0,
        [K(D(26, "08:14"), (-100, -6850), state="column", h=90), K(D(26, "08:22"), (120, -6800), state="firing", h=0), K(D(26, "08:34"), (120, -6800), state="retreat", h=90, strength=350), K(D(26, "08:42"), (600, -6800), state="line", h=270),
         K(D(26, "08:48"), (600, -6800), state="charge"), K(D(26, "08:56"), (300, -6780), state="firing", strength=330), K(D(26, "09:06"), (300, -6780), state="retreat", h=90), K(D(26, "09:15"), (600, -6800), state="line", h=270, strength=320),
         K(D(26, "09:25"), (600, -6800), state="surrender"), K(D(26, "12:00"), (600, -6800))] + march(D(26, "12:35"), D(26, "19:05"), BACK)[1:] + [K(D(26, "19:06"), FERRY_NJ, state="hidden")], ranks=3)
hessian("altenbockum", "Altenbockum's company", "Altenbockum's company of the Lossberg regiment, the outpost on the Princeton road at the head of Queen Street", "Capt. von Altenbockum", 100, (120, -6450), 0,
        [K(D(26, "08:05"), (120, -6450), state="firing"), K(D(26, "08:14"), (120, -6450), state="retreat", h=160, strength=95), K(D(26, "08:22"), (150, -6800), state="line", h=0), K(D(26, "08:24"), (150, -6800), state="hidden")])
hessian("knyphausen", "Knyphausen", "Fusilier Regiment von Knyphausen, at Queen and Second Streets; it bogged in the mill-pond marsh trying to reach the creek", "Maj. Friedrich von Dechow (mortally wounded)", 390, (110, -7258), 180,
        [K(D(26, "08:20"), (110, -7258), state="column", h=180), K(D(26, "08:30"), (150, -7330), state="firing", h=270), K(D(26, "08:45"), (150, -7330), state="firing", strength=375), K(D(26, "09:25"), (150, -7330), state="column", h=100),
         K(D(26, "09:38"), (594, -7425), state="line", h=180, strength=370), K(D(26, "09:45"), (594, -7425), state="surrender"), K(D(26, "12:00"), (594, -7425))] + march(D(26, "12:40"), D(26, "19:10"), BACK)[1:] + [K(D(26, "19:11"), FERRY_NJ, state="hidden")], ranks=3)
br("hessguns", "Hessian guns", "Six brass 3-pounders, two to a regiment, parked in King Street by Rall's headquarters; two fired six rounds each before they were taken", "Lts Engelhardt and Fischer", "artillery", 40,
   [K(D(25, "14:00"), (-110, -7000), h=0, state="line"), K(D(26, "08:14"), (-110, -6850), state="firing", fire=0.5), K(D(26, "08:24"), (-110, -6850), state="surrender", strength=22), K(D(26, "12:00"), (-110, -6850))] + march(D(26, "12:30"), D(26, "19:00"), BACK)[1:] + [K(D(26, "19:01"), FERRY_NJ, state="hidden")], guns=6)
br("jagers", "Jägers and dragoons", "Fifty jägers at the Hermitage on the River Road and twenty of the 16th Light Dragoons, who fled over the bridge to Donop", "Lt. von Grothausen", "light_infantry", 70,
   [K(D(25, "14:00"), (-1650, -6650), h=270, state="line"), K(D(26, "08:03"), (-1650, -6650), state="skirmish"), K(D(26, "08:08"), (-1650, -6650), state="rout", h=110), K(D(26, "08:25"), BRIDGE), K(D(26, "08:40"), (600, -9500)), K(D(26, "08:41"), (600, -9500), state="hidden")], loose=True)
br("picket", "Pennington Road picket", "The picket at Howell's cooper shop, a mile out on the Pennington Road, under Lt. Wiederhold", "Lt. Andreas Wiederhold", "infantry", 24,
   [K(D(25, "14:00"), PICKET, h=320, state="line"), K(D(25, "19:30"), PICKET, state="firing"), K(D(25, "19:45"), PICKET, state="line"), K(D(26, "08:00"), PICKET, state="firing"), K(D(26, "08:03"), PICKET, state="retreat", h=150, strength=22),
    K(D(26, "08:12"), (40, -6450), state="line", h=330), K(D(26, "08:20"), (40, -6450), state="hidden")], ranks=1)
br("bridgeguard", "Bridge guard", "The Knyphausen regiment's guard on the Assunpink bridge, which went off with the jägers", "", "infantry", 50,
   [K(D(25, "14:00"), (85, -7560), h=180, state="line"), K(D(26, "08:30"), (85, -7560), state="rout", h=170), K(D(26, "08:45"), (500, -9500)), K(D(26, "08:46"), (500, -9500), state="hidden")], ranks=1)

# ---- Cornwallis, 2-3 January ----
def column(id, short, name, cmd, type, n, t0, t1, path, keys, **x): br(id, short, name, cmd, type, n, march(t0, t1, path) + keys, **x)
column("van", "Light infantry and jägers", "Cornwallis's van: British light infantry and Hessian jägers, the skirmish line that fought Hand all the way to Trenton", "Lt. Col. Robert Abercromby", "light_infantry", 800, D(2, "07:30"), D(2, "16:00"), POST_S,
       [K(D(2, "16:00"), HEAD, state="firing", h=180), K(D(2, "16:30"), (-100, -7100), state="firing", strength=780), K(D(2, "16:50"), (-100, -7100), state="line"), K(D(3, "08:30"), (-100, -7100), state="column", h=0)] +
       march(D(3, "08:30"), D(3, "13:00"), POST_S[::-1])[1:] + [K(D(3, "13:30"), NASSAU)], loose=True)
column("hessgren", "Hessian grenadiers", "Donop's Hessian grenadiers, who stormed the Assunpink bridge in column and were shot back twice", "Col. Carl von Donop", "infantry", 1200, D(2, "08:00"), D(2, "16:40"), POST_S,
       [K(D(2, "16:40"), HEAD, state="line", h=180), K(D(2, "17:10"), (85, -7380), state="charge"), K(D(2, "17:20"), (85, -7440), state="firing", strength=1150), K(D(2, "17:28"), (85, -7440), state="retreat", h=0),
        K(D(2, "17:40"), (100, -7150), state="line", h=180), K(D(2, "17:45"), (100, -7150), state="charge"), K(D(2, "17:55"), (85, -7450), state="firing", strength=1080), K(D(2, "18:05"), (85, -7450), state="retreat", h=0), K(D(2, "18:20"), (100, -7100), state="line", h=180),
        K(D(3, "09:00"), (100, -7100), state="column", h=0)] + march(D(3, "09:00"), D(3, "13:20"), POST_S[::-1])[1:], ranks=4)
column("britgren", "Grenadiers and Guards", "The British grenadiers and the Guards", "Lt. Gen. Charles Cornwallis", "infantry", 1500, D(2, "08:20"), D(2, "17:00"), POST_S,
       [K(D(2, "17:00"), HEAD, state="line", h=180), K(D(2, "17:30"), (-300, -7300), state="line", h=160), K(D(2, "17:50"), (-200, -7600), state="charge"), K(D(2, "18:00"), (-200, -7600), state="firing", strength=1460), K(D(2, "18:10"), (-200, -7600), state="retreat", h=0),
        K(D(2, "18:25"), (-300, -7250), state="line", h=170), K(D(3, "09:10"), (-300, -7250), state="column", h=0)] + march(D(3, "09:10"), D(3, "13:30"), [(-300, -7250)] + POST_S[::-1])[1:], ranks=4)
column("grant", "Grant's brigade", "Grant's brigade and the rest of the army, which reached Trenton at dark", "Maj. Gen. James Grant", "infantry", 1500, D(2, "09:00"), D(2, "17:30"), POST_S,
       [K(D(2, "17:30"), HEAD, state="line", h=180), K(D(3, "09:20"), HEAD, state="column", h=0)] + march(D(3, "09:20"), D(3, "13:40"), POST_S[::-1])[1:], ranks=4)
column("britguns", "Royal Artillery", "Twenty-eight guns, bogged on the thawed road all day", "", "artillery", 200, D(2, "08:30"), D(2, "17:20"), POST_S,
       [K(D(2, "17:20"), (100, -6700), state="firing", h=180, fire=0.5), K(D(2, "18:30"), (100, -6700), state="line"), K(D(3, "09:30"), (100, -6700), state="column", h=0)] + march(D(3, "09:30"), D(3, "13:50"), [(100, -6700)] + POST_S[::-1])[1:], guns=10)
br("leslie", "Leslie", "Leslie's brigade, left at Maidenhead to come on in the morning; its advance guard reached Stony Brook as the Americans were leaving Princeton", "Brig. Gen. Alexander Leslie", "infantry", 1500,
   march(D(2, "08:00"), D(2, "11:00"), POST_S[:7]) + [K(D(2, "11:00"), MAIDENHEAD, state="line", h=200), K(D(3, "08:30"), MAIDENHEAD, state="column", h=20)] + march(D(3, "08:30"), D(3, "10:00"), [MAIDENHEAD, (4600, 3000), COCHRAN])[1:] +
   [K(D(3, "10:00"), COCHRAN, state="line", h=40), K(D(3, "10:30"), COCHRAN, state="column")] + march(D(3, "10:30"), D(3, "11:40"), [COCHRAN, (6100, 5500), WORTH, (7600, 6100), (8577, 6902)])[1:] + [K(D(3, "12:00"), (8577, 6902), state="line")], ranks=4)
# Mawhood's 4th Brigade at Princeton.
br("r17", "17th Foot", "The 17th Foot, marching for Maidenhead with the baggage, turned back over Stony Brook when Mawhood sighted the Americans", "Lt. Col. Charles Mawhood", "infantry", 350,
   [K(D(2, "08:00"), (8700, 7000), h=240, state="line"), K(D(3, "06:30"), (8700, 7000), state="column")] + march(D(3, "06:30"), D(3, "08:00"), [(8700, 7000), (7600, 6100), WORTH, COCHRAN])[1:] +
   [K(D(3, "08:00"), COCHRAN, state="column", h=60), K(D(3, "08:06"), WORTH), K(D(3, "08:10"), (7050, 5400), state="line", h=70), K(D(3, "08:12"), (7050, 5400), state="firing"), K(D(3, "08:16"), (7050, 5400), state="charge"), K(D(3, "08:20"), (7300, 5300), state="line", h=120, strength=335),
    K(D(3, "08:28"), (7300, 5300), state="firing"), K(D(3, "08:46"), (7300, 5300), state="line", strength=300), K(D(3, "08:48"), (7300, 5300), state="rout", h=250), K(D(3, "08:58"), WORTH, strength=260), K(D(3, "09:05"), COCHRAN, state="column", h=230), K(D(3, "10:00"), MAIDENHEAD), K(D(3, "10:01"), MAIDENHEAD, state="hidden")])
br("r55", "55th Foot", "The 55th Foot, following the 17th, sent back to hold the ravine at Stockton's farm with the 40th", "", "infantry", 350,
   [K(D(2, "08:00"), (8450, 6850), h=240, state="line"), K(D(3, "06:45"), (8450, 6850), state="column")] + march(D(3, "06:45"), D(3, "08:00"), [(8450, 6850), (7600, 6100), (7000, 5700)])[1:] +
   [K(D(3, "08:05"), (7000, 5700), state="line", h=120), K(D(3, "08:30"), (7700, 6000), state="firing", h=230), K(D(3, "08:50"), (7700, 6000), state="retreat", h=40, strength=340), K(D(3, "09:00"), FROG, state="firing", h=220),
    K(D(3, "09:15"), FROG, state="retreat", h=40, strength=320), K(D(3, "09:30"), (8700, 7250), state="rout"), K(D(3, "09:50"), (10000, 8300), strength=300), K(D(3, "10:10"), NE), K(D(3, "10:11"), NE, state="hidden")])
br("r40", "40th Foot", "The 40th Foot, guarding the stores in Princeton; part took refuge in Nassau Hall", "", "infantry", 300,
   [K(D(2, "08:00"), BREASTWORK, h=240, state="line"), K(D(3, "08:40"), (8150, 6650), state="line", h=220), K(D(3, "09:05"), (8150, 6650), state="firing"), K(D(3, "09:18"), (8150, 6650), state="retreat", h=40, strength=285),
    K(D(3, "09:30"), BREASTWORK, state="line", h=220), K(D(3, "09:40"), (8968, 7090), state="line", h=230, strength=194), K(D(3, "09:55"), (8968, 7090), state="surrender"), K(D(3, "12:30"), (8968, 7090)), K(D(3, "12:31"), (8968, 7090), state="hidden")])
br("r40out", "40th (the rest)", "The rest of the 40th and 55th, off north by the King's Highway, leaving two guns", "", "infantry", 100,
   [K(D(3, "09:40"), BREASTWORK, h=60, state="rout"), K(D(3, "10:00"), (10000, 8200), strength=80), K(D(3, "10:15"), NE), K(D(3, "10:16"), NE, state="hidden")])
br("dragoons", "16th Light Dragoons", "Trewren's troop of the 16th Light Dragoons, with Mawhood", "Capt. Thomas Trewren", "cavalry", 50,
   [K(D(2, "08:00"), (8800, 6900), h=240, state="line"), K(D(3, "06:20"), (8800, 6900), state="column")] + march(D(3, "06:20"), D(3, "07:50"), [(8800, 6900), (7600, 6100), WORTH, COCHRAN])[1:] +
   [K(D(3, "08:00"), COCHRAN, state="column", h=60), K(D(3, "08:08"), (6900, 5500), state="line", h=70), K(D(3, "08:16"), (6900, 5500), state="charge"), K(D(3, "08:22"), (7450, 5100), state="line", h=120), K(D(3, "08:46"), (7450, 5100), state="rout", h=250),
    K(D(3, "08:55"), WORTH, strength=46), K(D(3, "09:02"), COCHRAN, state="column", h=230), K(D(3, "09:45"), MAIDENHEAD), K(D(3, "09:46"), MAIDENHEAD, state="hidden")])
br("mawguns", "Mawhood's guns", "Two guns with Mawhood's column, taken in the orchard and turned on the British", "", "artillery", 20,
   [K(D(3, "06:35"), (8700, 7000), h=240, state="column")] + march(D(3, "06:35"), D(3, "08:04"), [(8700, 7000), (7600, 6100), WORTH, COCHRAN])[1:] + [K(D(3, "08:04"), COCHRAN, state="column", h=60), K(D(3, "08:12"), (7000, 5450), state="firing", h=70, fire=0.5),
    K(D(3, "08:30"), (7000, 5450), state="line"), K(D(3, "08:48"), (7000, 5450), state="surrender"), K(D(3, "11:00"), (7000, 5450)), K(D(3, "11:01"), (7000, 5450), state="hidden")], guns=2)
br("brit32", "The 32-pounder", "Donop's earthwork on the Trenton road with one iron 32-pounder; a straggler fired it at Cornwallis's van and held him up an hour", "", "artillery", 10,
   [K(D(2, "08:00"), (8500, 6850), h=240, state="line"), K(D(3, "09:30"), (8500, 6850), state="surrender"), K(D(3, "12:00"), (8500, 6850), state="line", fire=0.5), K(D(3, "12:10"), (8500, 6850), state="line", fire=0)], guns=1)

features = [
    dict(type="water", poly=DELAWARE),
    dict(type="creek", name="Assunpink Creek", pts=ASSUNPINK, at=[3200, -4900], rot=40), dict(type="creek", name="Stony Brook", pts=STONY, at=[5300, 5300], rot=20),
    dict(type="creek", name="Shabakunk Creek", pts=SHABAKUNK, at=[-800, -4300], rot=30), dict(type="creek", name="Jacob's Creek", pts=JACOBS, at=[-6300, -550], rot=-40),
    dict(type="road", name="road to the ferry", pts=[WEST, FERRY_PA]), dict(type="road", pts=TO_FERRY), dict(type="road", name="Pennington Road", pts=GREENE_RD, at=[-2700, -3900], rot=-50),
    dict(type="road", name="River Road", pts=SULLIVAN_RD, at=[-3200, -5400], rot=-40), dict(type="road", name="King Street", pts=[HEAD, (-110, -6991), (-127, -7269), (-100, -7450), BRIDGE], at=[-250, -6900], rot=85),
    dict(type="road", name="Queen Street", pts=[HEAD, (110, -7258), BRIDGE], at=[250, -6900], rot=85), dict(type="road", name="Post Road to Princeton", pts=POST_S, at=[1900, -1200], rot=-55),
    dict(type="road", name="the back road by the Quaker Bridge", pts=NIGHT + [(6900, 5000), (7900, 6000), (8577, 6902)], at=[6900, -3000], rot=85), dict(type="road", pts=[NASSAU, NE]),
    dict(type="road", pts=[BRIDGE, (300, -8600), (1500, -10950)]), dict(type="works", name="Donop's earthwork", pts=[(8420, 6780), (8520, 6900), (8620, 6820)], at=[8560, 6700]),
    dict(type="fence", name="the orchard fence", pts=[(7120, 5280), (7260, 5420)], at=[7200, 5470], **{"from": D(3, "08:00")}),
    dict(name="McConkey's Ferry", at=[-9000, 1400]), dict(name="Pennsylvania", at=[-9800, -2500], rot=-45), dict(name="New Jersey", at=[-7500, -3500], rot=-45), dict(name="Bear Tavern", at=[-6963, 2700]),
    dict(name="Birmingham", at=[-4501, -2320]), dict(name="Trenton", at=[-700, -6500]), dict(name="the Hermitage", at=[-1741, -6700]), dict(name="Rall's headquarters", at=[-350, -7050], **{"until": D(26, "12:00")}),
    dict(name="the orchard", at=[650, -6650]), dict(name="Mill Hill", at=[450, -7850]), dict(name="Trenton ferry", at=[-425, -8150]), dict(name="to Bordentown and Donop, 7 miles", at=[1500, -10700]),
    dict(name="Stockton Hollow", at=[950, -5789]), dict(name="Five Mile Run", at=[2548, 150]), dict(name="Maidenhead", at=[3015, 1520]), dict(name="Sandtown", at=[6072, -5660]), dict(name="Quaker Bridge", at=[6600, -250]),
    dict(name="the Barrens", at=[6400, -2800]), dict(name="Quaker meeting house", at=[6556, 4720]), dict(name="Worth's Mill", at=[6150, 5550]), dict(name="Clarke farm", at=[7379, 4900]), dict(name="Maxwell's Field", at=[7700, 5300]),
    dict(name="Frog Hollow", at=[8067, 6450]), dict(name="Princeton", at=[8800, 7350]), dict(name="Nassau Hall", at=[9100, 6950]), dict(name="to Kingston and Brunswick", at=[10300, 8300], rot=38),
    dict(name="to Newtown", at=[-10500, 1250]), dict(name="Mercer fell here", at=[7250, 5200], **{"from": D(3, "08:17")}),
]
PACE = {"Eight o'clock": 30, "Rall forms": 30, "The orchard at Trenton": 30, "The Knyphausen regiment": 30, "The bridge": 60, "Mawhood turns back": 30, "The orchard": 10, "Washington's rally": 15, "Frog Hollow and Nassau Hall": 60, "Into Trenton": 60}
events = [
    (D(25, "14:30"), "Christmas Day", "Washington's army, 2,400 men and eighteen guns, marches from its camps around Newtown to McConkey's Ferry. Rall's brigade of three Hessian regiments holds Trenton nine miles downstream, with no works: Rall has refused to dig. Ewing is to cross below the town and Cadwalader at Bristol; the ice will stop them both.", [-8000, 400], 7000),
    (D(25, "18:00"), "The crossing", "Glover's Marblehead fishermen begin ferrying the army in Durham boats and flat ferries at about six, ninety minutes after sunset, the river full of floating ice. The plan is to be over by midnight.", [-9000, 1350], 2500),
    (D(25, "23:00"), "The storm", "About eleven a nor'easter comes on: rain, then sleet and snow on a hard north-east wind. The last guns and horses are not over until three, three hours late. Washington gives up a dawn attack and goes on anyway.", [-9000, 1350], 2500),
    (D(26, "04:00"), "The march on Trenton", "At four the column moves off through the storm, up the bluff to the Bear Tavern and down through the ravine of Jacob's Creek, where the guns are lowered on ropes. Two men freeze to death on the road.", [-6500, 1200], 5500),
    (D(26, "06:45"), "Birmingham", "At the fork the army divides: Greene's division with Washington by the Pennington Road, Sullivan's by the River Road, each four and a half miles from the town. Sullivan reports his powder wet and is told to use the bayonet.", [-4000, -2800], 5000),
    (D(26, "08:00"), "Eight o'clock", "'Exactly at eight' Greene's van drives in the Pennington Road picket; three minutes later Sullivan strikes the River Road. The jägers and the dragoons bolt over the Assunpink bridge. Forrest's and Hamilton's guns go into battery at the head of King and Queen Streets, firing down both into the storm.", [-200, -6600], 1800),
    (D(26, "08:15"), "Rall forms", "The Rall regiment forms in King Street and marches up it toward the American guns; two Hessian 3-pounders get off six rounds each before half their crews are down and Weedon's Virginians charge and take them. The Lossberg regiment comes up Queen Street and is stopped by Forrest.", [-100, -6900], 1300),
    (D(26, "08:30"), "The orchard at Trenton", "Rall rallies behind St Michael's church and leads his two regiments out of the streets into the orchard east of the town, then back in a counter-attack toward the American guns. Fire from the houses and the batteries breaks it; Rall is hit twice and carried into the church.", [300, -6850], 1300),
    (D(26, "09:25"), "The Knyphausen regiment", "Surrounded in the orchard, the Rall and Lossberg regiments ground their arms. The Knyphausen regiment tries to reach the creek above the bridge, bogs its guns in the mill-pond marsh, and is cut off by St Clair and Stark; it surrenders minutes after the rest. By ten it is over: 22 Hessians dead, about 900 prisoners, six guns, four Americans wounded.", [300, -7200], 1500),
    (D(26, "12:00"), "Back to the river", "Washington's council votes against pushing on. The army marches back nine miles through the storm with its prisoners and recrosses the Delaware that night.", [-3000, -4000], 8000),
    (D(29, "10:00"), "The second crossing", "On the 29th and 30th the army crosses again through heavy ice, two days' work, and camps south of the Assunpink at Trenton. On the last day of the year Washington offers ten dollars to any man who will stay six weeks past his enlistment; most of the Continentals step forward. Mifflin's and Cadwalader's militia march up from Bordentown and Crosswicks.", [-4000, -2500], 9000),
    (D(2, "07:30"), "Cornwallis marches", "Cornwallis leaves Princeton at dawn on 2 January with 5,500 men and 28 guns, Leslie's brigade dropped at Maidenhead. The roads are thawed to mud. Hand's riflemen, a thousand men with two guns, wait at Five Mile Run to slow him.", [5000, 3500], 9000),
    (D(2, "10:30"), "Hand's delaying action", "Hand skirmishes at Five Mile Run, ambushes the van from the wooded bank of Shabakunk Creek and holds the British there searching the woods for half an hour, then stands again at Stockton Hollow. It costs Cornwallis the whole day.", [1500, -2500], 6000),
    (D(2, "16:00"), "Into Trenton", "Hand's men fall back through the town firing from the houses; Hessian grenadiers come in with the bayonet. Washington sits his horse on the bridge while the rear guard files through under the guns on Mill Hill. The British reach the creek just before sunset.", [100, -7200], 2000),
    (D(2, "17:00"), "The bridge", "Three times the British come at the Assunpink: at the lower fords, then the Hessian grenadiers in column on the bridge, then the British in a solid column met with canister and a volley. 'The bridge looked red as blood.' Cornwallis calls it off at dark: 'we'll bag the fox in the morning'.", [85, -7500], 1400),
    (D(2, "20:00"), "The council at the Douglass house", "With the river at his back full of ice, Washington takes his officers' advice to slip away by the Quaker Bridge road and strike Princeton. The gun wheels are wrapped in rags; five hundred men stay to feed the fires and dig within the enemy's hearing.", [200, -7700], 2500),
    (D(3, "01:00"), "The night march", "The wind has gone north-west and the mud is frozen hard enough for the guns. From about one the army files east by Sandtown, through the scrub of the Barrens, over the Quaker Bridge and up the new-cut Sawmill road, twelve miles in the dark on ice.", [4000, -4000], 11000),
    (D(3, "07:20"), "Daylight at Stony Brook", "At first light the column halts by the Quaker meeting house, two miles from Princeton and behind time. Mercer's brigade turns off along the brook to secure the Post Road bridge at Worth's Mill; Sullivan's division wheels right up the Sawmill road toward the town.", [6800, 5100], 3200),
    (D(3, "08:00"), "Mawhood turns back", "Mawhood has marched the 17th and 55th for Maidenhead before dawn. From the hill beyond the bridge he sees Mercer's column in the sun and turns back over Stony Brook; both race for the orchard on William Clarke's rising ground.", [6600, 5300], 2600),
    (D(3, "08:10"), "The orchard", "Mercer's men win the orchard and fire from its upper fence; the British volley goes high. Mawhood orders the bayonet. The line is overrun, both guns lost, Mercer's horse shot and Mercer clubbed and bayoneted by Joseph Clark's barn, Haslet shot through the head, Neil killed at his guns. Cadwalader's militia come up and break after a volley; Moulder's two 4-pounders hold on alone.", [7250, 5300], 1100),
    (D(3, "08:30"), "Washington's rally", "Washington rides between the lines with Hitchcock's New Englanders, Hand's riflemen and the Virginians, halts them thirty yards from the British and gives the word. Hitchcock's volley and charge break Mawhood's line; the 17th cut their way out with the bayonet down the Post Road and over the bridge, chased by the Philadelphia Light Horse. 'It is a fine fox chase, my boys.'", [7400, 5300], 1300),
    (D(3, "09:00"), "Frog Hollow and Nassau Hall", "Sullivan's division drives the 55th and the 40th from the ravine on Stockton's farm through Donop's earthwork and into the town. Two hundred flee north leaving two guns; Hamilton's battery puts a shot into Nassau Hall and 194 men inside surrender.", [8400, 6700], 2200),
    (D(3, "11:00"), "To Kingston", "Washington gives up Brunswick for want of fresh troops and marches north-east as Leslie's advance guard appears at Stony Brook, where Kelly's party is tearing up the bridge. A straggler fires the 32-pounder from the earthwork and holds up Cornwallis for an hour. The British find Princeton empty at one.", [8200, 6500], 5000),
    (D(3, "13:00"), "After", "Ten days: two posts taken, some 1,200 prisoners, Cornwallis's army drawn into the hills. The British give up all New Jersey but Brunswick and Amboy. Mercer dies at the Clarke house on 12 January. Washington goes into winter quarters at Morristown.", [3000, -1000], 20000),
]
# Hold in place through long gaps: without this a unit creeps toward a key hours away and the time-lapse never engages.
# A turn in place takes its last two minutes; a move of more than three hours takes its last fifteen.
def add_holds(units):
    import datetime as _dt
    ts = lambda s: _dt.datetime.strptime(s.replace("T", " ")[:16], "%Y-%m-%d %H:%M").timestamp()
    for u in units:
        ks, out = u["keys"], []
        for a, c in zip(ks, ks[1:] + [None]):
            out.append(a)
            if c is None or a.get("state") == "hidden": continue
            moved = (a["x"], a["y"]) != (c["x"], c["y"]); turned = "h" in c and c["h"] != next((k["h"] for k in reversed(out) if "h" in k), c["h"])
            gap = ts(c["t"]) - ts(a["t"]); lead = 900 if moved else 120
            if (moved and gap > 3 * 3600) or (turned and not moved and gap > 600):
                out.append(dict(t=_dt.datetime.fromtimestamp(ts(c["t"]) - lead).strftime("%Y-%m-%d %H:%M"), x=a["x"], y=a["y"]))
        u["keys"] = out
add_holds(units)
battle = dict(
    id="trenton-princeton", name="Trenton and Princeton", date="1776-12-25", dateText="25 December 1776 to 3 January 1777", place="Trenton and Princeton, New Jersey",
    origin=dict(lat=40.2850, lon=-74.7650), extent=22000, start=D(25, "14:00"), end=D(3, "14:00"), speed=300, lapse=7200, menPerDot=20,
    sunrise="07:20", sunset="16:40", terrainExaggeration=2, contourInterval=5, trees=dict(density=0.00012, clear=[DELAWARE]),
    wind=dict(x=-0.5, y=-0.6), palette=dict(ground="#aeb08a", high="#d6d0a4", tree="rgba(60,85,45,0.45)", water="#7f9fc0"),
    tints=[dict(color="rgba(225,228,236,0.4)", **{"from": D(25, "23:00"), "until": D(27, "06:00")})],
    sides=dict(american=dict(name="Americans (Washington)", color="#1f55c4", light="#4a83e6", dark="#122c66"),
               british=dict(name="British and Hessians (Rall, Cornwallis)", color="#c02a1f", light="#e2584a", dark="#5e1510")),
    features=features, units=units,
    events=[dict(t=t, title=a, text=b, at=at, view=v, **({"speed": PACE[a]} if a in PACE else {})) for t, a, b, at, v in events],
    outcome={"result": "American victory", "losses": [["american", "Trenton: 4 wounded, 2 dead of cold on the march. Princeton: 25 to 44 killed, Mercer among them, and 40 wounded."], ["british", "Trenton: 22 killed, 83 wounded, 896 captured. Princeton: by Howe's return 18 killed, 58 wounded and about 200 missing."]], "note": "Washington claimed over 100 British killed and 300 taken at Princeton; the counts have never been reconciled."},
    sources=[
        "William S. Stryker, <i>The Battles of Trenton and Princeton</i> (1898): the Hessian quarters and picket posts, the regimental strengths and losses, the night march order, the Stony Brook bridge, Mawhood's sighting from the hill by Cochran's, the orchard fight, Nassau Hall and the 32-pounder.",
        "Washington to Hancock, 27 December 1776 ('exactly at eight o'clock', 'three minutes after') and 5 January 1777; Knox's and Greene's letters; the Hessian court-martial testimony on Rall; Wiederhold's and Piel's diaries.",
        "David Hackett Fischer, <i>Washington's Crossing</i> (2004): the storm 'about eleven', the orders of battle, the councils at the Douglass house, the freeze on the night of 2 January, Mawhood's brigade.",
        "Richard M. Ketchum, <i>The Winter Soldiers</i>; the Trenton Historical Society's street plan and battle scripts (King Street is Warren, Queen Street is Broad); the Princeton Battlefield Society and the 2010 Milner <i>Battle of Princeton Mapping Project</i> for the Sawmill road and Maxwell's Field.",
        "<a href='https://www.battlefields.org/learn/revolutionary-war/battles/trenton' target='_blank'>American Battlefield Trust</a> (Trenton and Princeton); Washington Crossing Historic Park and State Park; the Old Barracks Museum.",
        "Terrain: USGS 3DEP elevation at 73 m over a 22 km square. The Delaware and the creeks are traced from the grid, not surveyed; the 1776 roads follow their modern successors (Bear Tavern Road, Pennington Avenue, River Road, Route 206, Quaker Bridge and Mercer Roads).",
        "What is reconstructed: the times inside the Trenton fight between 'exactly eight' and 'over by ten'; the hours of Hand's stands on 2 January; the start of the night march (sources say midnight to two); the hours at Princeton, anchored only by 'daylight', 'about eight' and 'two hours in the town'; brigade strengths on 3 January; and the places of the orchard, the Quaker Bridge and Cochran's hill, taken off the modern road net.",
    ],
)
json.dump(battle, open("battles/trenton-princeton/battle.json", "w"), indent=1)
print(len(units), "units,", len(events), "events,", len(features), "features; river polygon", len(DELAWARE), "points")
