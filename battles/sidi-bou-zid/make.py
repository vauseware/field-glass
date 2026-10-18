# Builds battles/sidi-bou-zid/battle.json. Run from the repo root: python3 battles/sidi-bou-zid/make.py
# Local metres from 35.0500N 9.5000E (x east, y north), the plain north-east of Sidi Bou Zid. The 36 km square holds Faid Pass
# (15674,1670), Djebel Lessouda (2779,9574), Djebel Ksaira (11072,-7458), Garet Hadid (1504,-9240) and Kern's Crossroads
# (-12485,10798). Places come from OpenStreetMap, the Copernicus DEM summits and the 1943 grid references fitted to them
# (good to about a kilometre); see the research notes for issue #4. The 2nd Battalion, 17th Field Artillery is drawn in its
# recorded area astride the Aïn Rebaou road (35.010N 9.600E, +-1.5 km); its battery positions are not recorded.
import json, math, datetime as dt
LAT0, LON0 = 35.05, 9.5
def ll(lat, lon): return (round((lon - LON0) * 111320 * math.cos(math.radians(LAT0))), round((lat - LAT0) * 111320))

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
units = []
def unit(id, short, side, name, commander, type, strength, keys, **extra):
    units.append(dict(id=id, side=side, name=name, short=short, commander=commander, type=type, strength=strength, keys=keys, **extra))
us = lambda *a, **k: unit(a[0], a[1], "american", *a[2:], **k)
de = lambda *a, **k: unit(a[0], a[1], "german", *a[2:], **k)

SBZ, LESS, POSTE, KSAIRA = ll(35.0382, 9.4865), ll(35.136, 9.5305), ll(35.100, 9.5345), ll(34.983, 9.6215)
GARET, FAID_V, FAID_P, REBAOU = ll(34.967, 9.5165), ll(35.057, 9.6527), ll(35.065, 9.672), ll(34.993, 9.696)
SALEM, SADAGUIA, KERN, HAMRA, KEBAR = ll(35.0944, 9.4669), ll(35.0841, 9.4256), ll(35.147, 9.363), ll(35.112, 9.341), ll(34.936, 9.393)
CP168, GUNS, CAPTURE = ll(35.020, 9.516), ll(35.010, 9.600), ll(35.00, 9.44)
R1, R2, R3 = ll(35.017, 9.555), ll(35.008, 9.615), ll(35.000, 9.648)  # the modern road to Aïn Rebaou along Ksaira's northern foothills
BIRHAFEY = ll(34.932, 9.196)
def edge(p, q, lim=17900):  # where the road from p toward q (off the map) leaves the square
    f = min((lim - abs(p[0])) / abs(q[0] - p[0]) if abs(q[0]) > lim else 1, (lim - abs(p[1])) / abs(q[1] - p[1]) if abs(q[1]) > lim else 1)
    return (round(p[0] + (q[0] - p[0]) * f), round(p[1] + (q[1] - p[1]) * f))
BIR_EDGE = edge(SBZ, BIRHAFEY)
WEST_EDGE = edge(KERN, (KERN[0] + 2 * (KERN[0] - POSTE[0]), KERN[1] + 2 * (KERN[1] - POSTE[1])))  # the Sbeïtla road leaves the map
EAST = (17900, 2100)  # the far side of the Eastern Dorsal, behind Faid Pass
MAIZ_EDGE = (6000, -17900)  # the road north from Maizila Pass, 27 km south, enters the map [inferred line]
DEFILE = (6300, -9300)
FAID_RD = [EAST, FAID_P, FAID_V, POSTE, KERN, WEST_EDGE]
REBAOU_RD = [SBZ, R1, R2, R3, REBAOU]
BIR_RD = [SBZ, BIR_EDGE]
SW = lambda km: (round(SBZ[0] + (BIR_EDGE[0] - SBZ[0]) * km * 1000 / math.dist(SBZ, BIR_EDGE)), round(SBZ[1] + (BIR_EDGE[1] - SBZ[1]) * km * 1000 / math.dist(SBZ, BIR_EDGE)))
RALLY = (-12800, 5600)  # CCA rallies near Djebel Hamra at dusk
ASM = (-11500, 9300)    # CCC's assembly area north-east of Djebel Hamra, 15 February
GH = (2500, -8300)      # Drake's position on Garet Hadid, between its two summits
KS_CAP, GH_CAP = off(CAPTURE, 700, 300), off(CAPTURE, -600, -500)  # where the two columns were caught on 17 February

T0 = D(14, "04:00")
# ---- Lessouda Force: Waters on Djebel Lessouda ----
def lessouda(id, short, name, cmd, type, n, p, h, keys, **x): us(id, short, name, cmd, type, n, [K(T0, p, h=h, state="line")] + keys, **x)
def breakout(p, dest, n, t1=D(16, "05:00")):  # the night of 15-16 February: off the hill and across the plain to the west
    return [K(D(15, "22:30"), p, state="column", h=hd(p, (-7000, 8300))), K(fmt((sec(D(15, "22:30")) + sec(t1)) / 2), (-7000, 8300), strength=n),
            K(t1, dest, state="line", h=90), K(D(16, "09:00"), dest), K(D(16, "09:01"), dest, state="hidden")]
lessouda("f168", "F/168", "Company F, 2nd Battalion, 168th Infantry, on Djebel Lessouda", "Maj. Robert R. Moore (2nd Bn)", "infantry", 200, (2300, 9300), 120,
         [K(D(14, "08:45"), (2300, 9300), state="firing", h=230), K(D(14, "09:30"), (2300, 9300), state="line", strength=195)] + breakout((2300, 9300), HAMRA, 115), loose=True)
lessouda("g168", "G/168", "Company G, 2nd Battalion, 168th Infantry, on Djebel Lessouda", "Maj. Robert R. Moore (2nd Bn)", "infantry", 200, (3300, 9800), 90,
         [K(D(14, "08:15"), (3300, 9800), state="firing", h=20), K(D(14, "09:00"), (3300, 9800), state="line", strength=195)] + breakout((3300, 9800), off(HAMRA, 300, 300), 116), loose=True)
lessouda("h168", "H/168", "Company H and the headquarters of the 2nd Battalion, 168th Infantry, with Lessouda Force's command post", "Lt. Col. John K. Waters (captured 16 Feb)", "infantry", 200, (2800, 8900), 160,
         [K(D(14, "06:20"), (2800, 8900), state="line", strength=195)] + breakout((2800, 8900), KERN, 70), loose=True)
lessouda("recon1ar", "Recon/1 AR", "Reconnaissance Company, 1st Armored Regiment, with Lessouda Force", "", "infantry", 120, (3900, 7600), 120,
         [K(D(14, "06:40"), (3900, 7600), state="skirmish"), K(D(14, "07:10"), (3900, 7600), state="retreat", h=330, strength=110), K(D(14, "07:40"), (3300, 8500), state="line", h=120)] + breakout((3300, 8500), off(KERN, 400, -300), 60), loose=True)
lessouda("b91", "B/91 AFA", "Battery B, 91st Armored Field Artillery Battalion (105 mm, self-propelled), with Lessouda Force; what became of its guns is not recorded", "", "artillery", 100, (2000, 8100), 110,
         [K(D(14, "06:40"), (2000, 8100), state="firing", fire=0.5), K(D(14, "09:00"), (2000, 8100), state="line", strength=90), K(D(15, "22:30"), (2000, 8100), state="hidden")], guns=6)
lessouda("g1ar", "G/1 AR", "Company G, 1st Armored Regiment, ten tanks east of Lessouda; Maj. Norman Parsons's tank is knocked out first", "Maj. Norman Parsons", "armor", 10, (5300, 8100), 100,
         [K(D(14, "06:30"), (5300, 8100), state="firing"), K(D(14, "06:40"), (5300, 8100), strength=9), K(D(14, "07:40"), (5300, 8100), state="retreat", h=290, strength=5), K(D(14, "08:10"), (3700, 8700), state="line", h=120, strength=3),
          K(D(14, "10:00"), (3700, 8700), strength=2), K(D(15, "22:30"), (3700, 8700), state="hidden")])

# ---- Hightower's tank battalion, the tank destroyers and the 91st's guns ----
def hightower(id, short, name, n, end, dx, **x):
    p0 = (-2700 + dx, -3000)
    keys = [K(T0, p0, h=30, state="line"), K(D(14, "07:30"), p0, state="column")] + march(D(14, "07:30"), D(14, "08:45"), [p0, off(SBZ, dx, 0), (600 + dx, 2400)])[1:] + [
        K(D(14, "08:50"), (600 + dx, 2400), state="firing", h=45), K(D(14, "10:50"), (600 + dx, 2400), state="line", strength=round(n * 0.6)),
        K(D(14, "11:00"), (600 + dx, 2400), state="retreat", h=225), K(D(14, "12:00"), (-3000 + dx, -2400), state="line", h=40),
        K(D(14, "14:00"), (-3600 + dx, -1400), state="firing", h=60), K(D(14, "16:20"), (-3600 + dx, -1400), state="line", strength=end + 1),
        K(D(14, "16:30"), (-3600 + dx, -1400), state="retreat", h=290), K(D(14, "17:20"), (-9000 + dx, -600)), K(D(14, "18:30"), off(RALLY, dx, 0), state="line", h=120, strength=end),
        K(D(16, "06:00"), off(RALLY, dx, 0)), K(D(16, "06:01"), off(RALLY, dx, 0), state="hidden")]
    us(id, short, name, "Lt. Col. Louis V. Hightower (3rd Bn)", x.pop("type", "armor"), n, keys, **x)
hightower("h1ar", "H/1 AR", "Company H, 3rd Battalion, 1st Armored Regiment, the mobile reserve south-west of the village (Howe gives the battalion about forty tanks)", 20, 2, 0)
hightower("i1ar", "I/1 AR", "Company I, 3rd Battalion, 1st Armored Regiment, with Hightower", 20, 2, 700)
hightower("a701", "A/701 TD", "Company A (less a platoon), 701st Tank Destroyer Battalion (75 mm, self-propelled); it lost all but two of its guns", 8, 2, -700)

def gunline_91(id, short, name, p, h, leave):  # Drake stops the 8 AM withdrawal; the guns go around noon with the CCA command post
    keys = [K(T0, p, h=h, state="line"), K(D(14, "07:00"), p, state="firing", fire=0.4), K(D(14, "07:55"), p, state="line"), K(D(14, "08:00"), p, state="column", h=250),
            K(D(14, "08:12"), off(p, -500, -150)), K(D(14, "08:25"), p, state="line", h=h), K(D(14, "08:30"), p, state="firing", fire=0.4), K(fmt(sec(leave) - 900), p, state="line")]
    path = ([p] + [q for q in [R1, SBZ] if q[0] < p[0]]) + [SW(3), (-6500, -5200), (-10500, 1000), off(RALLY, 0, -700)]
    keys += march(leave, fmt(sec(leave) + 5.5 * 3600), path)[1:]
    keys[-1].update(state="line", h=120, strength=60)
    keys += [K(D(16, "06:00"), off(RALLY, 0, -700)), K(D(16, "06:01"), off(RALLY, 0, -700), state="hidden")]
    us(id, short, name, "Lt. Col. Charles P. Summerall Jr.", "artillery", 100, keys, guns=6)
gunline_91("a91", "A/91 AFA", "Battery A, 91st Armored Field Artillery Battalion (105 mm, self-propelled), near the CCA command post; the battalion lost nine guns on 14 Feb", off(SBZ, 600, 300), 60, D(14, "12:00"))
gunline_91("c91", "91st AFA", "The 91st Armored Field Artillery's other battery with CCA, 'to the left of Dj. Ksaira five miles along the road to Faid Pass' in Drake's order of 8 Feb", (6300, -3700), 50, D(14, "12:30"))

# ---- The 2nd Battalion, 17th Field Artillery: three batteries of 155 mm howitzers astride the Aïn Rebaou road ----
# Recorded: in action at the foot of Ksaira; shelled at 08:00; part left at 11:00, all gone by 13:00 (Drake) or 15:00 (Hoffman);
# moved back by batteries toward an area south-west of the village, dive-bombed repeatedly, destroyed. Inferred: which battery left
# when, where each was caught, and the order in the column.
FA17 = "Probably the 2nd Battalion, 17th Field Artillery Regiment (Howe; the 1st Armored Division's report says 1st), 155 mm howitzers, towed. One of its batteries: the letter and the place within the battalion are not recorded"
def battery(id, p, leave, legs):  # legs: (time, place, state, strength) after leaving; the last is where the battery is lost sight of
    keys = [K(T0, p, h=50, state="line"), K(D(14, "07:00"), p, state="firing", fire=0.4), K(D(14, "07:55"), p, state="line", strength=106),
            K(D(14, "08:00"), p, state="column", h=275), K(D(14, "08:12"), off(p, -500, 80)), K(D(14, "08:25"), p, state="line", h=50),
            K(D(14, "08:30"), p, state="firing", fire=0.4), K(fmt(sec(leave) - 900), p, state="line"), K(leave, p, state="column", h=hd(p, R1))]
    prev = p
    for t, q, st, n in legs:
        keys.append(K(t, q, state=st, **({"h": hd(prev, q)} if q != prev else {}), **({"strength": n} if n else {}))); prev = q
    keys.append(K(fmt(sec(legs[-1][0]) + 60), prev, state="hidden"))
    us(id, "17th FA", FA17 + ".", "battalion commander not recorded (perhaps Lt. Col. Henry P. Ward)", "artillery", 110, keys, guns=4)
battery("fa17a", (8400, -4250), D(14, "11:00"), [(D(14, "11:25"), R1, "column", 0), (D(14, "11:45"), R1, "column", 85), (D(14, "12:15"), SBZ, "column", 0),
                                                  (D(14, "12:30"), SW(2.5), "rout", 60), (D(14, "13:30"), SW(4), "rout", 45)])  # bombed at the road bend, again south-west of the village
battery("fa17b", (9100, -4430), D(14, "13:00"), [(D(14, "13:25"), R1, "column", 0), (D(14, "13:50"), (1900, -2500), "column", 0), (D(14, "14:10"), (1900, -2500), "rout", 70),
                                                  (D(14, "15:30"), SW(3.5), "rout", 40)])
battery("fa17c", (9800, -4570), D(14, "15:00"), [(D(14, "15:30"), R1, "column", 0), (D(14, "16:00"), (2400, -2700), "column", 0), (D(14, "16:20"), (2400, -2700), "rout", 60),
                                                  (D(14, "17:30"), (2000, -4300), "rout", 45)])

# ---- The 168th Infantry ----
def ksaira(id, short, name, n, p, h, back, cap, cap_n, **x):  # 3rd Bn on Ksaira: into the hills at 19:00, attacked on the 16th, off the hill at 23:40, caught on the plain
    keys = [K(T0, p, h=h, state="line"), K(D(14, "19:00"), back, state="line", h=h), K(D(16, "08:00"), back, state="firing"), K(D(16, "16:30"), back, state="line", strength=n - 15)]
    keys += march(D(16, "23:40"), D(17, "07:00"), [back, (6000, -7700), (500, -7000), cap])
    keys += [K(D(17, "07:05"), cap, state="firing", h=30), K(D(17, "08:30"), cap, state="surrender", strength=cap_n)]
    us(id, short, name, "Lt. Col. John H. Van Vliet Jr. (3rd Bn, captured 17 Feb)", "infantry", n, keys, loose=True, **x)
ksaira("i168", "I/168", "Company I, 3rd Battalion, 168th Infantry, on the summit of Djebel Ksaira", 210, (11000, -7300), 10, (11000, -7300), off(KS_CAP, 0, 300), 195)
ksaira("l168", "L/168", "Company L, 3rd Battalion, 168th Infantry, the centre of the Ksaira horseshoe", 210, (10300, -6600), 10, (10400, -6800), off(KS_CAP, -300, 0), 195)
ksaira("k168", "K/168", "Company K, 3rd Battalion, 168th Infantry, in the foothills; its 1st Platoon on the left by the guns", 210, (9300, -5300), 30, (10200, -6300), off(KS_CAP, 300, 0), 190)
ksaira("at168", "AT/168", "Antitank Company, 168th Infantry, with the 3rd Battalion on Ksaira", 170, (10000, -5900), 20, (10700, -6900), off(KS_CAP, 0, -300), 160)
units[-2]["keys"][1:1] = [K(D(14, "11:00"), (9300, -5300), state="retreat", h=270), K(D(14, "11:30"), (8600, -4900), state="line", h=40, strength=195), K(D(14, "12:00"), (9300, -5300), h=40)]

def garet(id, short, name, cmd, n, keys, cap, cap_n, **x):  # Drake's group: Garet Hadid, the march of 16-17 February and the fight on the plain
    gp = (keys[-1]["x"], keys[-1]["y"])
    keys += [K(D(16, "08:00"), gp, state="firing"), K(D(16, "16:00"), gp, state="line")]
    keys += march(D(16, "21:50"), D(17, "06:45"), [gp, (-1500, -7600), cap])
    keys += [K(D(17, "07:20"), cap, state="firing", h=60), K(D(17, "11:00"), cap, state="surrender", strength=cap_n)]
    us(id, short, name, cmd, "infantry", n, keys, loose=True, **x)
garet("hq168", "168th HQ", "The 168th Infantry's headquarters company, band and the Cannon Company of the 39th Infantry, from the command post in the olive grove to Garet Hadid", "Col. Thomas D. Drake (captured 17 Feb)", 300,
      [K(T0, CP168, h=60, state="line")] + march(D(14, "13:00"), D(14, "17:00"), [CP168, (2200, -6000), GH]) + [K(D(14, "17:05"), GH, state="line", h=60)], off(GH_CAP, 0, 0), 200)
garet("e168", "E/168", "Company E, 168th Infantry, guarding the artillery 'on the left side of [the] Sidi Bou Zid, Rebuou Road in the cactus patch'", "Capt. Donald L. Wilkinson", 190,
      [K(T0, (8900, -4000), h=50, state="line"), K(D(14, "15:00"), (8900, -4000), state="column", h=240)] + march(D(14, "15:00"), D(14, "18:00"), [(8900, -4000), (6300, -6500), off(GH, 600, 200)])[1:] + [K(D(14, "18:05"), off(GH, 600, 200), state="line", h=90)], off(GH_CAP, 300, -300), 130)
garet("eng16", "C/16 Engr", "Company C, 16th Armored Engineer Battalion, covering the minefield between Ksaira and Garet Hadid", "Capt. William R. A. Kleysteuber", 150,
      [K(T0, DEFILE, h=180, state="line"), K(D(14, "12:00"), DEFILE, state="firing"), K(D(14, "17:00"), DEFILE, state="line", strength=120)] + march(D(14, "18:00"), D(14, "19:30"), [DEFILE, off(GH, 700, -500)])[1:] + [K(D(14, "19:35"), off(GH, 700, -500), state="line", h=120)], off(GH_CAP, -300, 0), 100)
garet("strag", "Stragglers", "About 300 unarmed men from the tanks, reconnaissance units, tank destroyers and artillery, who joined Drake on Garet Hadid", "", 300,
      march(D(14, "16:30"), D(14, "18:30"), [(1800, -3300), (2000, -6000), off(GH, -600, 200)]) + [K(D(14, "18:35"), off(GH, -600, 200), state="line", h=60)], off(GH_CAP, 0, -400), 170)

us("kern", "Kern", "Kern's force: the 1st Battalion, 6th Armored Infantry, with a light tank company, sent forward from division reserve to Kern's Crossroads", "Col. Kern", "infantry", 700,
   march(D(14, "15:00"), D(14, "17:00"), [WEST_EDGE, KERN]) + [K(D(14, "17:05"), KERN, state="line", h=120), K(D(16, "20:00"), KERN), K(D(16, "20:01"), KERN, state="hidden")], loose=True)

# ---- Combat Command C, 15 February ----
def ccc(id, short, name, cmd, type, n, dx, dy, fight, end, **x):
    a, f = off(ASM, dx, dy), off(fight, dx, dy)
    keys = march(D(15, "07:00"), D(15, "09:45"), [off(WEST_EDGE, 0, -1500 + dy), a]) + [K(D(15, "09:50"), a, state="line", h=120)]
    keys += [K(D(15, "12:40"), a, state="line", h=hd(a, f)), K(D(15, "15:50"), f, state="firing"), K(D(15, "17:30"), f, state="line", strength=end)]
    keys += [K(D(15, "17:40"), f, state="retreat", h=hd(f, a)), K(D(15, "21:00"), off(a, 0, -600), state="line", h=120), K(D(16, "06:00"), off(a, 0, -600)), K(D(16, "06:01"), off(a, 0, -600), state="hidden")]
    us(id, short, name, cmd, type, n, keys, **x)
ALGER = "Lt. Col. James D. Alger (2nd Bn, captured)"
ccc("d21", "2/1 AR", "A tank company of the 2nd Battalion, 1st Armored Regiment, Combat Command C (52 tanks went in)", ALGER, "armor", 17, -500, 700, (-3800, 5100), 1)
ccc("e21", "2/1 AR", "A tank company of the 2nd Battalion, 1st Armored Regiment", ALGER, "armor", 17, 0, 0, (-3800, 5100), 2)
ccc("f21", "2/1 AR", "A tank company of the 2nd Battalion, 1st Armored Regiment", ALGER, "armor", 18, 500, -700, (-3800, 5100), 3)
ccc("i6ai", "3/6 AI", "The 3rd Battalion, 6th Armored Infantry, in half-tracks behind the tanks; clear of the fight by 5:40", "Col. Robert I. Stack (CCC)", "infantry", 700, -1500, -400, (-5600, 5400), 640, loose=True)
units[-1]["keys"][-5]["t"] = D(15, "17:15"); units[-1]["keys"][-4]["t"] = D(15, "17:20")
us("f68", "68th AFA", "The 68th Armored Field Artillery Battalion (less Battery A), firing for Combat Command C", "", "artillery", 200,
   march(D(15, "07:30"), D(15, "11:00"), [off(WEST_EDGE, 0, -2500), (-9000, 7400)]) + [K(D(15, "11:05"), (-9000, 7400), state="line", h=120), K(D(15, "13:00"), (-9000, 7400), state="firing", fire=0.5),
    K(D(15, "17:45"), (-9000, 7400), state="line"), K(D(15, "18:00"), (-9000, 7400), state="column", h=300), K(D(15, "20:00"), off(ASM, -300, -1200), state="line"), K(D(16, "06:00"), off(ASM, -300, -1200)), K(D(16, "06:01"), off(ASM, -300, -1200), state="hidden")], guns=12)

# ---- Gruppe Ziegler: the 10th Panzer Division through Faid Pass ----
de("garty", "German guns", "Most of the artillery of both panzer divisions, firing from the hills east of Faid", "", "artillery", 400,
   [K(T0, (16300, 700), h=290, state="line"), K(D(14, "06:00"), (16300, 700), state="firing", fire=0.6, h=290), K(D(14, "08:00"), (16300, 700), h=235), K(D(14, "10:30"), (16300, 700), state="line"),
    K(D(16, "08:00"), (16300, 700), state="firing", fire=0.4, h=240), K(D(16, "16:30"), (16300, 700), state="line")], guns=24)
de("g7pz", "Gerhardt", "Kampfgruppe Gerhardt: the 7th Panzer Regiment less a battalion, round the north of Djebel Lessouda", "Gerhardt", "armor", 50,
   [K(T0, (17600, 2700), h=270, state="column")] + march(D(14, "06:20"), D(14, "08:50"), [FAID_P, (12000, 8200), (6200, 13300), (600, 12300), (-1000, 9000), (-1200, 6300)])[1:] +
   [K(D(14, "08:55"), (-1200, 6300), state="line", h=160), K(D(14, "09:30"), (-1200, 6300), state="firing", h=140), K(D(14, "11:00"), (-1200, 6300), state="line", strength=46),
    K(D(14, "11:30"), (-1200, 6300), state="column", h=200), K(D(14, "13:00"), (-3300, 1200), state="line", h=180), K(D(14, "14:00"), (-3300, 1200), state="firing", h=190), K(D(14, "16:20"), (-3300, 1200), state="line", strength=40),
    K(D(14, "16:30"), (-3300, 1200), state="column", h=200), K(D(14, "17:05"), (-4700, -1300), state="line", h=270),
    K(D(15, "15:00"), (-4700, -1300), state="column", h=340), K(D(15, "15:45"), (-6300, 3300), state="firing", h=30), K(D(15, "17:45"), (-6300, 3300), state="line", strength=36), K(D(15, "19:00"), (-3000, 1500), h=300)])
de("pg69", "69th PzGr", "A battalion of the 69th Panzergrenadier Regiment with Gerhardt, closing the ring round Lessouda", "", "infantry", 600,
   [K(T0, (17400, 2300), h=270, state="column")] + march(D(14, "06:30"), D(14, "09:15"), [FAID_P, (12000, 8000), (6200, 12800), (1200, 11800)])[1:] +
   [K(D(14, "09:20"), (1200, 11800), state="firing", h=150), K(D(14, "10:30"), (1200, 11800), state="line", strength=585), K(D(14, "12:00"), (0, 8600), h=90),
    K(D(15, "23:00"), (0, 8600), state="firing", h=90), K(D(16, "01:00"), (0, 8600), state="line", strength=575), K(D(16, "08:00"), (2500, 9300), h=270)], loose=True)
de("pg86", "86th PzGr", "Kampfgruppe Reimann: the 86th Panzergrenadier Regiment less a battalion, with infantry, engineers, artillery and a platoon of 88 mm guns, down the Faid road and south-west on Sidi Bou Zid", "Reimann", "infantry", 800,
   [K(T0, (17200, 1400), h=270, state="column")] + march(D(14, "06:40"), D(14, "08:30"), [FAID_P, FAID_V, (5600, 6400)])[1:] +
   [K(D(14, "08:35"), (5600, 6400), state="line", h=250), K(D(14, "09:15"), (5600, 6400), state="column", h=225), K(D(14, "10:30"), (2400, 3000), state="firing", h=225), K(D(14, "11:15"), (2400, 3000), state="line", strength=780),
    K(D(14, "13:00"), (300, 500), state="line", h=225), K(D(14, "16:10"), (300, 500), state="column"), K(D(14, "16:40"), off(SBZ, 1000, 0), state="line", h=270),
    K(D(15, "15:30"), off(SBZ, 1000, 0), state="column", h=320), K(D(15, "16:10"), (-1000, 2600), state="firing", h=300), K(D(15, "17:45"), (-1000, 2600), state="line", strength=760)], loose=True)
de("tigers", "Tigers", "The company of Tigers (Mark VI) with Kampfgruppe Reimann: eleven or twelve tanks", "", "armor", 11,
   [K(T0, (17600, 1700), h=270, state="column")] + march(D(14, "06:30"), D(14, "07:20"), [FAID_P, FAID_V, (8200, 6200)])[1:] +
   [K(D(14, "07:25"), (8200, 6200), state="firing", h=290), K(D(14, "08:20"), (8200, 6200), state="line"), K(D(14, "08:30"), (8200, 6200), state="column", h=280)] +
   march(D(14, "08:30"), D(14, "10:00"), [(8200, 6200), (4200, 5300), (1800, 3200)])[1:] + [K(D(14, "10:05"), (1800, 3200), state="firing", h=225), K(D(14, "11:15"), (1800, 3200), state="line"),
    K(D(14, "13:00"), (-200, 900), h=225), K(D(14, "14:00"), (-200, 900), state="firing"), K(D(14, "16:00"), (-200, 900), state="line"),
    K(D(15, "15:20"), (-200, 900), state="column", h=330), K(D(15, "16:00"), (-1300, 3700), state="firing", h=290), K(D(15, "17:45"), (-1300, 3700), state="line")])
de("hudel", "Hudel", "Maj. Hudel's tank battalion of the 7th Panzer Regiment, mostly Mark IIIs with 50 mm guns: off at 4 AM in a sandstorm, it took the cactus grove north of the village", "Maj. Hudel", "armor", 27,
   [K(T0, (17700, 1000), h=270, state="column")] + march(D(14, "05:00"), D(14, "08:30"), [(17700, 1000), FAID_P, FAID_V, (4000, 5100)])[1:] +
   [K(D(14, "08:35"), (4000, 5100), state="line", h=230), K(D(14, "09:00"), (4000, 5100), state="firing", h=220), K(D(14, "10:45"), (4000, 5100), state="line", strength=25),
    K(D(14, "11:00"), (4000, 5100), state="column", h=225), K(D(14, "12:15"), (-900, 1300), state="line", h=210), K(D(14, "14:00"), (-900, 1300), state="firing", h=230), K(D(14, "15:40"), (-900, 1300), state="line", strength=24),
    K(D(14, "15:45"), (-900, 1300), state="column", h=200), K(D(14, "16:00"), off(SBZ, 300, 800), state="line", h=240),
    K(D(15, "15:30"), off(SBZ, 300, 800), state="column", h=320), K(D(15, "16:10"), (-2700, 2300), state="firing", h=320), K(D(15, "17:45"), (-2700, 2300), state="line", strength=21)])
de("lang", "Lang", "Kampfgruppe Lang, the reserve: the 10th Motorcycle Battalion, armoured engineers, an antitank platoon and two 88 mm detachments", "Lang", "infantry", 500,
   [K(T0, (17300, 2900), h=270, state="column")] + march(D(14, "07:00"), D(14, "08:00"), [FAID_P, off(FAID_V, -800, 800)])[1:] + [K(D(14, "08:05"), off(FAID_V, -800, 800), state="line", h=270)], loose=True)

# ---- The 21st Panzer Division from the south ----
de("sch_pz", "Schuette", "Kampfgruppe Schuette's tank battalion, through Maizila Pass from 6 AM and north between Garet Hadid and Ksaira", "Schuette (HQ 104th Panzergrenadier Regt)", "armor", 30,
   march(D(14, "10:15"), D(14, "12:00"), [MAIZ_EDGE, off(DEFILE, 0, -1500)]) + [K(D(14, "12:00"), off(DEFILE, 0, -1500), state="firing", h=0), K(D(14, "17:00"), off(DEFILE, 0, -1500), state="line", strength=28),
    K(D(16, "07:00"), off(DEFILE, 0, -1500), state="column", h=330), K(D(16, "08:00"), (4300, -8400), state="firing", h=280), K(D(16, "16:00"), (4300, -8400), state="line", strength=27),
    K(D(17, "05:30"), (4300, -8400), state="column", h=280), K(D(17, "07:00"), off(CAPTURE, 2600, -400), state="firing", h=270), K(D(17, "11:00"), off(CAPTURE, 2600, -400), state="line")])
de("sch_pg", "Schuette PzGr", "Kampfgruppe Schuette's armoured infantry, artillery and flak", "", "infantry", 600,
   march(D(14, "10:45"), D(14, "12:45"), [MAIZ_EDGE, off(DEFILE, -400, -2800)]) + [K(D(14, "12:50"), off(DEFILE, -400, -2800), state="line", h=0), K(D(14, "13:30"), off(DEFILE, -400, -2800), state="firing"), K(D(14, "17:00"), off(DEFILE, -400, -2800), state="line", strength=585),
    K(D(16, "07:00"), off(DEFILE, -400, -2800), state="column", h=300), K(D(16, "08:30"), (3700, -9600), state="firing", h=300), K(D(16, "16:00"), (3700, -9600), state="line", strength=570),
    K(D(17, "05:30"), (3700, -9600), state="column", h=290), K(D(17, "07:10"), off(CAPTURE, 0, -2400), state="firing", h=0), K(D(17, "11:00"), off(CAPTURE, 0, -2400), state="line")], loose=True)
def stenk(id, short, name, cmd, type, n, t_in, lag_km, meet, **x):
    keys = march(t_in, D(14, "17:05"), [BIR_EDGE, meet]) + [K(fmt(sec(D(14, "17:05")) + 300), meet, state="line", h=45)]
    keys += [K(D(15, "15:00"), meet, state="column", h=0), K(D(15, "16:00"), off(meet, -800, 4200 - lag_km * 300), state="firing", h=20), K(D(15, "17:45"), off(meet, -800, 4200 - lag_km * 300), state="line", strength=n - 3)]
    keys += march(D(16, "13:00"), D(16, "18:00"), [off(meet, -800, 4200 - lag_km * 300), SADAGUIA, off(KERN, 0, -400 * lag_km), WEST_EDGE]) + [K(D(16, "18:01"), WEST_EDGE, state="hidden")]
    de(id, short, name, cmd, type, n, keys, **x)
stenk("stk1", "Stenkhoff", "Kampfgruppe Stenkhoff (headquarters of the 5th Panzer Regiment): one of its two tank battalions, round by Bir el Hafey and up the road from 1:45", "Col. Stenkhoff", "armor", 30, D(14, "14:50"), 0, SW(3.6))
stenk("stk2", "Stenkhoff", "Kampfgruppe Stenkhoff: the second tank battalion", "Col. Stenkhoff", "armor", 30, D(14, "15:00"), 1, SW(5))
stenk("stk_pg", "Stenkhoff PzGr", "Kampfgruppe Stenkhoff's armoured infantry, artillery and flak", "", "infantry", 600, D(14, "15:10"), 2, SW(6.5), loose=True)
de("rec580", "580th Recon", "The 580th Reconnaissance Battalion (reinforced), flank guard south and west of Stenkhoff", "", "light_infantry", 500,
   march(D(14, "14:40"), D(14, "17:30"), [(-17900, -12500), (-9500, -5600)]) + [K(D(14, "17:35"), (-9500, -5600), state="line", h=45),
    K(D(17, "06:00"), (-9500, -5600), state="column", h=70), K(D(17, "07:10"), off(CAPTURE, -2600, -900), state="firing", h=70), K(D(17, "11:00"), off(CAPTURE, -2600, -900), state="line")], loose=True)
de("rebaou", "21st Pz at Rebaou", "Non-motorised units of the 21st Panzer Division at Aïn Rebaou, east of Ksaira", "", "infantry", 600,
   [K(T0, off(REBAOU, -400, 0), h=260, state="line"), K(D(16, "06:00"), off(REBAOU, -400, 0), state="column", h=260), K(D(16, "07:30"), (13600, -6900), state="firing", h=270), K(D(16, "17:00"), (13600, -6900), state="line", strength=570),
    K(D(17, "06:00"), (13600, -6900), state="column", h=270), K(D(17, "07:30"), off(KSAIRA, 300, 300), state="line")], loose=True)

# Stukas: cosmetic, never moving a unit. Recorded: Sidi Bou Zid 10:00-11:00; the CCA guns and command post around noon; the 17th FA
# repeatedly in the afternoon (times and places inferred); on CCC at 13:40, about 14:40 (on the village) and 16:30 on the 15th.
def stuka(name, at, t0, t1, spread=700, h=255): return dict(type="airstrike", name=name, at=list(at), spread=spread, h=h, **{"from": t0, "until": t1})
features = [
    stuka("Stukas on Sidi Bou Zid", SBZ, D(14, "10:00"), D(14, "11:00"), 1000),
    stuka("Stukas on the 17th FA", R1, D(14, "11:25"), D(14, "11:45")),
    stuka("Stukas on the guns and the CCA command post", SW(2.5), D(14, "12:15"), D(14, "12:40"), 900),
    stuka("Stukas on the 17th FA", (1900, -2500), D(14, "13:50"), D(14, "14:10")),
    stuka("Stukas on the 17th FA", (2400, -2700), D(14, "16:00"), D(14, "16:20")),
    stuka("Stukas on Combat Command C", (-8000, 8000), D(15, "13:40"), D(15, "14:00"), 900),
    stuka("Stukas on Sidi Bou Zid", SBZ, D(15, "14:40"), D(15, "15:00"), 900),
    stuka("Stukas on Combat Command C", (-4400, 5300), D(15, "16:30"), D(15, "16:50"), 900),
    dict(type="road", name="Faïd–Sbeïtla road", pts=FAID_RD, at=[-7000, 8900], rot=-18), dict(type="road", name="road to Aïn Rebaou", pts=REBAOU_RD, at=[7600, -3700], rot=10),
    dict(type="road", name="road to Bir el Hafey", pts=BIR_RD, at=[-11000, -5300], rot=24), dict(type="road", pts=[SBZ, POSTE]), dict(type="road", name="road from Maizila Pass", pts=[MAIZ_EDGE, DEFILE, R1], at=[6900, -14000], rot=-88),
    dict(name="Sidi Bou Zid", at=[SBZ[0] - 1400, SBZ[1] + 300]), dict(name="Faïd Pass", at=[FAID_P[0], FAID_P[1] + 700]), dict(name="Faïd", at=[FAID_V[0] - 300, FAID_V[1] - 600]),
    dict(name="Djebel Lessouda", at=[LESS[0], LESS[1] + 900]), dict(name="Poste de Lessouda", at=[POSTE[0] - 300, POSTE[1] + 800]), dict(name="Djebel Ksaïra", at=[KSAIRA[0], KSAIRA[1] - 900]),
    dict(name="Djebel Garet Hadid", at=[GARET[0], GARET[1] - 900]), dict(name="Aïn Rebaou", at=[REBAOU[0] - 900, REBAOU[1] - 700]), dict(name="Sidi Salem", at=[SALEM[0], SALEM[1] + 500]),
    dict(name="Sadaguia", at=[SADAGUIA[0], SADAGUIA[1] + 500]), dict(name="Kern's Crossroads", at=[KERN[0], KERN[1] + 700]), dict(name="Djebel Hamra (about here)", at=[HAMRA[0], HAMRA[1] + 900]),
    dict(name="Djebel el Kebar", at=[KEBAR[0], KEBAR[1] - 800]), dict(name="Eastern Dorsal", at=[16600, -2500], rot=-80), dict(name="to Maizila Pass, 27 km", at=[MAIZ_EDGE[0] + 2200, -17300]),
    dict(name="to Bir el Hafey", at=[BIR_EDGE[0] + 2000, BIR_EDGE[1] - 700], rot=24), dict(name="to Sbeïtla", at=[WEST_EDGE[0] + 1600, WEST_EDGE[1] + 700], rot=-18),
    dict(name="CCA command post", at=[SBZ[0] + 300, SBZ[1] - 700], **{"until": D(14, "12:00")}), dict(name="168th Infantry CP", at=[CP168[0], CP168[1] - 600], **{"until": D(14, "17:00")}),
    dict(name="the defile", at=[DEFILE[0] + 1300, DEFILE[1]]), dict(name="the cactus grove", at=[-2100, 1100]),
    dict(name="the columns caught, 17 Feb (grid square T-6050)", at=[CAPTURE[0], CAPTURE[1] - 1500], **{"from": D(17, "07:00")}),
]
PACE = {"Out of Faïd Pass": 120, "The guns are shelled": 60, "The guns pull out": 120, "Caught on the road": 120, "The pincers meet": 120, "Still pretty busy": 120, "Caught on the plain": 120}
events = [
    (D(14, "04:00"), "Frühlingswind", "Combat Command A of the US 1st Armored Division, under Brig. Gen. Raymond McQuillin, holds the plain round Sidi Bou Zid below the Eastern Dorsal: Lt. Col. John Waters's force on Djebel Lessouda to the north, the 3rd Battalion, 168th Infantry on Djebel Ksaïra to the south-east, Hightower's tank battalion in reserve by the village, and the guns by the village and along the road to Aïn Rebaou. Operation Frühlingswind sends two panzer divisions under General Heinz Ziegler against it: the 10th through Faïd Pass, the 21st round the south by Maizila Pass. At four in the morning, in a sandstorm, Maj. Hudel's tank battalion moves off from the olive grove east of Faïd.", [5000, 1500], 34000),
    (D(14, "06:30"), "Out of Faïd Pass", "German guns have shelled the Lessouda road junction since six. At 6:30 the Germans come out of Faïd Pass onto a misty plain, the light 'not yet sufficient'. Kampfgruppe Gerhardt swings round the north of Djebel Lessouda; Kampfgruppe Reimann, with a company of Tigers, comes down the Faïd–Sbeïtla road. Company G, 1st Armored Regiment, ten tanks east of Lessouda, is hit at once and Maj. Norman Parsons's tank knocked out. Col. Peter Hains in Sidi Bou Zid hears the gunfire at '06:35 hours, by my watch'.", [9000, 6500], 15000),
    (D(14, "07:30"), "Hightower goes forward", "About 7:30 Lt. Col. Louis Hightower is ordered to 'clear up the situation' with two tank companies of the 3rd Battalion, 1st Armored Regiment and the tank destroyers of Company A, 701st. Howe gives the battalion about forty tanks. The 2nd Battalion, 168th Infantry on Lessouda reports itself surrounded from this hour.", [1000, 2500], 15000),
    (D(14, "08:00"), "The guns are shelled", "At eight German guns shell the 17th Field Artillery heavily. Its 155 mm howitzers stand astride the Sidi Bou Zid–Aïn Rebaou road at the foot of Djebel Ksaïra. Col. Thomas Drake of the 168th Infantry sees 'the armored artillery followed by the 17th Field Artillery' leave their positions, telephones McQuillin, is told to 'take command and stop it', and stops it. Howe names the battalion as the 2nd; the 1st Armored Division's own report says the 1st. It was probably the 2nd. Where its batteries stood is not recorded: the map spaces three along the road by guesswork.", list(GUNS), 5000),
    (D(14, "08:30"), "Lessouda cut off", "By 8:30 more than forty German tanks have encircled Djebel Lessouda and are on the Faïd–Sbeïtla road heading south; at nine 39 Mark IVs and some Tigers are reported west of the hill. About 900 men of Waters's force are cut off on it.", [2000, 8000], 14000),
    (D(14, "10:00"), "Dive bombers", "Between ten and eleven dive bombers and fighter-bombers hit the Sidi Bou Zid area. In the last hour of the morning Hightower pulls his tanks back south-west. About eleven McQuillin's line to Drake is cut after 'No more over the phone, we are leaving', and the CCA headquarters starts for Zaafria.", [0, 0], 11000),
    (D(14, "11:00"), "The guns pull out", "At eleven 'part of the 17th Field Artillery left positions', taking some of K Company's 1st Platoon with it, and Lt. Harry Hoffman orders his infantry back. The battalion moves back by batteries toward an area south-west of the village. Drake reports all the artillery gone at one; Hoffman writes that the 17th left at three. Both may be right for different batteries. The replay shows one battery leaving at eleven, one at one and one at three; that split is a reconstruction.", [6500, -4000], 8000),
    (D(14, "12:00"), "The southern pincer", "At noon the 21st Panzer Division arrives from the south. Kampfgruppe Schuette's advance guard, about thirty vehicles, enters the gap between Garet Hadid and Ksaïra, where Company C, 16th Armored Engineers covers a minefield, and fights there all afternoon. Kampfgruppe Stenkhoff, two tank battalions, has swung wide to Bir el Hafey. McQuillin moves his guns and command post out under dive-bomber attack; at 12:08 he signals 'Enemy right on top of us.' At one the 168th's headquarters starts for Garet Hadid.", [0, -5500], 26000),
    (D(14, "15:00"), "Caught on the road", "'The 17th Field Artillery left their positions at 1500 hours.' Moving back by batteries, the battalion is dive-bombed again and again and, in Howe's words, 'destroyed as a fighting unit'; a 1st Armored officer writes of German tanks 'moving up from the south'. All its 155 mm howitzers are lost. Where and when each battery was hit is not recorded, and the bomb strikes on the map are placed by inference. Some of its men reached Drake on Garet Hadid. Cpl James E. Vause of the 17th Field Artillery was among those reported captured on 14 February; his record names the regiment, not his battalion or battery.", [3500, -3300], 10000),
    (D(14, "17:05"), "The pincers meet", "At 3:30 Ziegler judges his first mission done. About four a company of Hudel's battalion enters Sidi Bou Zid and finds it empty. At 5:05 Stenkhoff, coming up the road from Bir el Hafey since 1:45, meets the 10th Panzer west of the village. Combat Command A has lost 44 tanks, all but two of its tank destroyers, nine of the 91st's guns and all the 155s. It rallies at dusk near Djebel Hamra.", [-4500, -800], 15000),
    (D(14, "19:00"), "Night on the hills", "At seven the 3rd Battalion, 168th Infantry pulls back into the Ksaïra hills. Drake holds Garet Hadid with about 950 men, some 300 of them unarmed men from the tanks, reconnaissance units, tank destroyers and artillery. Waters's force is still on Lessouda. All three are cut off.", [5000, -2000], 30000),
    (D(15, "12:40"), "The counterattack", "Combat Command C under Col. Robert Stack, with Lt. Col. James Alger's 2nd Battalion, 1st Armored Regiment, reaches its assembly area north-east of Djebel Hamra by 9:45 and attacks toward Sidi Bou Zid at 12:40. Dive bombers hit it at 1:40, about 2:40 and 4:30.", [-7500, 6500], 16000),
    (D(15, "16:00"), "Still pretty busy", "From about four the tanks are fighting near Sidi Salem and the village. Just after 4:45 comes Alger's last message: 'Still pretty busy. Situation in hand.' The armored infantry is clear by 5:40 and withdrawal is ordered at six. Of 52 tanks that went in, 46 are lost; Howe says only four came out. The 2nd Battalion reports 15 officers and 298 men missing, Alger among them. The Germans claim 39 tanks.", [-3500, 4300], 9000),
    (D(15, "22:30"), "Out of Lessouda", "About 10:30 the infantry on Lessouda breaks out across the plain. About a third of its 900 men get out: 231 reach Djebel Hamra before dawn and others reach Kern's Crossroads at five. Waters is captured on the 16th.", [-4500, 8500], 24000),
    (D(16, "14:30"), "The decision is yours", "All day on the 16th Ksaïra and Garet Hadid are under attack. At 2:30 Maj. Gen. Orlando Ward, commanding the 1st Armored Division, radios Drake: 'We can do no more for you. The decision is yours.' Late in the afternoon a withdrawal message is dropped on Ksaïra, about five by Drake's account and 4:30 by Line's.", [7000, -7500], 16000),
    (D(16, "22:00"), "Off the hills", "The Garet Hadid column moves off between 9:50 and ten. The 3rd Battalion follows from Ksaïra about 11:40, once the code word comes through. Both march for Djebel Hamra, 22 to 26 miles by Drake's reckoning, under a moon Hoffman calls full, breaking through cloud.", [3000, -7000], 22000),
    (D(17, "07:00"), "Caught on the plain", "About seven both columns are caught in the open by German motorised troops and tanks. Drake's group fights for about three and a half hours; Lt. William Rogers of the 91st and twelve volunteers are killed holding a knoll. Howe counts about 800 prisoners in the first group and 600, Drake among them, in the second; Van Vliet is taken too. The accounts put the place a few miles short of Djebel Hamra, but a grid reference in Line's report puts it about 6 km south-west of Sidi Bou Zid, which is where the map shows it. Which German units made the capture is not recorded here; the map's are a guess.", list(off(CAPTURE, 0, -300)), 7000),
    (D(17, "11:00"), "After", "The 14th and 15th cost the 1st Armored Division 98 tanks, 57 half-tracks and 29 guns, and the 168th Infantry lost about 2,200 men of its 2nd and 3rd Battalions. The 21st Panzer Division claimed 2,546 Allied prisoners for 14–17 February: a German count of men taken, not of the dead. That day the 21st Panzer takes Sbeïtla and the 1st Armored falls back through Kasserine. Drake's men are marched back toward Lessouda, then trucked to Sfax and sent on by Tunis to Italy and the camps in Germany and Poland.", [1000, 0], 34000),
]
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
CREDIT = json.load(open("battles/sidi-bou-zid/terrain.json"))["source"]
battle = dict(
    id="sidi-bou-zid", name="Sidi Bou Zid", date="1943-02-14", dateText="14 to 17 February 1943", place="Sidi Bou Zid, Tunisia",
    origin=dict(lat=LAT0, lon=LON0), extent=36000, start=D(14, "04:00"), end=D(17, "11:30"), speed=300, lapse=7200, menPerDot=20,
    sunrise="07:10", sunset="18:02", terrainExaggeration=2, contourInterval=10,
    sides=dict(american=dict(name="Americans (1st Armored Division, 168th Infantry)", color="#1f55c4", light="#4a83e6", dark="#122c66"),
               german=dict(name="Germans (10th and 21st Panzer Divisions)", color="#b8322a", light="#de5d50", dark="#5c1712")),
    features=features, units=units,
    events=[dict(t=t, title=a, text=b, at=at, view=v, **({"speed": PACE[a]} if a in PACE else {})) for t, a, b, at, v in events],
    outcome={"result": "German victory",
             "losses": [["american", "14 Feb, Combat Command A (Howe's final count): 6 killed, 22 wounded, 134 missing (Blumenson: 32 wounded); 44 tanks, all but two tank destroyers, nine of the 91st's 105s and all the 155s of the 17th FA; Blumenson adds 59 half-tracks and 26 guns. The first estimate on the 16th was 62 officers and 1,536 men killed, wounded or missing. 15 Feb, Combat Command C: 46 of 52 tanks; 15 officers and 298 men of the 2nd Battalion, 1st Armored Regiment missing. 168th Infantry: about 2,200 men of its 2nd and 3rd Battalions; some 1,400 taken on 17 Feb (Anderson; Howe counts about 800 and 600)."],
                        ["german", "No German count found. The US estimate for 15 Feb alone was 13 Mark IVs, five 88 mm and ten other guns, and about 50 killed."]],
             "note": "German claims of Allied losses: the 10th Panzer, 71 prisoners and 40 tanks on 14 Feb; the 21st Panzer, 2,546 prisoners, 103 tanks, 280 vehicles and 18 field guns for 14–17 Feb. Some accounts print the 2,546 as Americans killed; it is a German claim of prisoners taken. How many howitzers the 17th FA lost is uncertain: Atkinson says eighteen, a 2024 newspaper account twelve."},
    sources=[
        "George F. Howe, <i>Northwest Africa: Seizing the Initiative in the West</i> (US Army Center of Military History, 1957), chapters XXI and XXII and Map 11: the plan of Frühlingswind, the kampfgruppen and their axes, the clock times, the 17th FA's position and destruction (citing Lt. Col. Henry P. Ward to Col. Charles E. Hart, 16 Feb 1943, in the 17th FA regimental history), Combat Command C, the prisoners and the losses.",
        "US Army Center of Military History, <i>Kasserine Pass Battles: Readings</i>, Vol. I, Part 1 (staff ride volume): the 1st Armored Division's report of operations; Hudel and Robinett, 'The Tank Battle at Sidi Bou Zid'; the 168th Infantry reports of Maj. Robert Moore, 1st Lt. Harry Hoffman (Co K), Lt. Col. Gerald Line and Col. Thomas Drake; the Lessouda Force history.",
        "Martin Blumenson, 'Kasserine Pass, 30 January–22 February 1943', in <i>America's First Battles</i> (1986): the losses.",
        "Rick Atkinson, <i>An Army at Dawn</i> (2002), chapter 9; Charles R. Anderson, <i>Tunisia</i> (CMH, 1993).",
        "NARA, WWII Prisoners of War Data File (RG 389): Cpl James E. Vause, 17th Field Artillery Regiment, reported captured 14 February 1943.",
        "Terrain: " + CREDIT + ". GLO-30 sampled at 100 m over a 36 km square; it is a surface model, so the modern town of Sidi Bouzid and its irrigated farms show. Places from OpenStreetMap and the 1943 grid references; the roads are drawn straight between them, not traced.",
        "Clock: the times as recorded, read as a GMT+1 clock, which fits 'light not yet sufficient' at 6:30; sunrise 7:10 and sunset 18:02 are computed for 14 February on that assumption.",
        "What is reconstructed: every unit strength except the tank counts Howe and the reports give (German tank counts split Howe's divisional totals across the kampfgruppen); the three batteries of four howitzers each, their places along the road, which left when, and where each was caught; the times and places of the Stukas over the 17th FA; the routes between recorded places; how tank losses fell between companies; the German units at the capture on 17 February; and the hours of the fighting on 16 February.",
    ],
)
WHEN = {"Frühlingswind": "4:00 AM", "Out of Faïd Pass": "6:30 AM", "Hightower goes forward": "about 7:30 AM", "The guns are shelled": "8:00 AM", "Lessouda cut off": "8:30 AM",
        "Dive bombers": "10–11 AM", "The guns pull out": "11:00 AM", "The southern pincer": "noon", "Caught on the road": "3:00 PM", "The pincers meet": "5:05 PM",
        "Night on the hills": "7:00 PM", "The counterattack": "12:40 PM", "Still pretty busy": "about 4:00 PM", "Out of Lessouda": "about 10:30 PM",
        "The decision is yours": "2:30 PM", "Off the hills": "about 10 PM", "Caught on the plain": "about 7:00 AM"}  # chapter times the sources record; the story gives the others to the nearest hour
for e in battle["events"]:
    if e["title"] in WHEN: e["when"] = WHEN[e["title"]]
json.dump(battle, open("battles/sidi-bou-zid/battle.json", "w"), indent=1, ensure_ascii=False)
print(len(units), "units (", sum(u["side"] == "american" for u in units), "US,", sum(u["side"] == "german" for u in units), "German ),", len(events), "events,", len(features), "features")
