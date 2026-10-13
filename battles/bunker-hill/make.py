# Builds battles/bunker-hill/battle.json. Run from the repo root: python3 battles/bunker-hill/make.py
# Local metres from 42.3765N 71.0610W (x east, y north), 25 m north-west of the Bunker Hill Monument, which stands on
# the site of the redoubt (19,-17). The modern ground is landfill all round the peninsula, so the 1775 shoreline is
# drawn as water polygons: the Mill Pond and Charles bank along Main Street, the Mystic bank, the Navy Yard flats and
# the Boston North End shore. Works, fence and ship positions follow Frothingham's distances and bearings (1849).
import json, math
D = lambda hm, day=17: f"1775-06-{day:02d} {hm}"
def K(t, p, **kw): return dict(t=t, x=p[0], y=p[1], **kw)
units = []
def unit(id, short, side, name, commander, type, strength, keys, **extra):
    units.append(dict(id=id, side=side, name=name, short=short, commander=commander, type=type, strength=strength, keys=keys, **extra))
us = lambda *a, **k: unit(a[0], a[1], "american", *a[2:], **k)
br = lambda *a, **k: unit(a[0], a[1], "british", *a[2:], **k)
def rsq(cx, cy, s, rot):
    c, sn = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return [(round(cx + c * dx - sn * dy), round(cy + sn * dx + c * dy)) for dx, dy in [(-s / 2, -s / 2), (s / 2, -s / 2), (s / 2, s / 2), (-s / 2, s / 2)]]
def ship(cx, cy, L=48, W=14, rot=0):
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return [(round(cx + c * dx - s * dy), round(cy + s * dx + c * dy)) for dx, dy in [(-L / 2, -W / 2), (L / 2 - 6, -W / 2), (L / 2, 0), (L / 2 - 6, W / 2), (-L / 2, W / 2)]]

REDOUBT, FENCE_SW, FENCE_NE, WALL = (19, -17), (-16, 178), (263, 423), (304, 445)
BUNKER, NECK, OFF, MOULTON, MORTON = (-453, 527), (-1030, 906), (-1420, 1230), (452, 100), (400, -40)
IN = [K(D("21:00", 16), OFF, h=135, state="column"), K(D("22:00", 16), NECK), K(D("22:30", 16), BUNKER), K(D("23:30", 16), (-100, 120))]
def out(t0, frm, t1, t2, t3):  # the retreat: north-west over the saddle to Bunker Hill, the Neck and off the map
    return [K(t0, frm, h=315, state="retreat"), K(t1, (-200, 260)), K(t2, BUNKER, state="column"), K(t3, NECK), K("1775-06-17 17:35", OFF), K("1775-06-17 17:36", OFF, state="hidden")]

# The night detachment: Prescott's own regiment in the redoubt, Bridge's and Frye's men at the breastwork, Gridley's guns.
us("prescott", "Prescott", "Col. Prescott's Massachusetts regiment, in the redoubt", "Col. William Prescott", "infantry", 300,
   IN + [K(D("00:00"), REDOUBT, h=65, state="line"), K(D("15:30"), REDOUBT, state="firing"), K(D("15:50"), REDOUBT, state="line", strength=290), K(D("16:00"), REDOUBT, state="firing"),
         K(D("16:22"), REDOUBT, state="line", strength=275), K(D("16:32"), REDOUBT, state="firing"), K(D("16:40"), REDOUBT, state="line", strength=245)] + out(D("16:41"), (0, 20), D("16:50"), D("17:00"), D("17:15")), ranks=4)
us("bridge", "Bridge", "Lt. Col. Bridge's detachment, 300 of Bridge's regiment, at the breastwork", "Lt. Col. Ebenezer Bridge (wounded)", "infantry", 150,
   IN + [K(D("00:00"), (48, 30), h=70, state="line"), K(D("09:30"), (54, 42), h=115), K(D("15:30"), (54, 42), state="firing"), K(D("15:50"), (54, 42), state="line", strength=140), K(D("16:00"), (54, 42), state="firing"),
         K(D("16:22"), (54, 42), state="line", strength=125), K(D("16:32"), (54, 42), state="firing"), K(D("16:40"), (54, 42), state="line", strength=108)] + out(D("16:41"), (30, 60), D("16:49"), D("16:59"), D("17:14")), ranks=3)
us("frye", "Frye", "Frye's detachment, 300 of Frye's regiment, at the north end of the breastwork", "Lt. Col. James Brickett (wounded); Col. Frye", "infantry", 150,
   IN + [K(D("00:00"), (62, 70), h=70, state="line"), K(D("09:30"), (68, 80), h=115), K(D("15:30"), (68, 80), state="firing"), K(D("15:50"), (68, 80), state="line", strength=138), K(D("16:00"), (68, 80), state="firing"),
         K(D("16:22"), (68, 80), state="line", strength=122), K(D("16:32"), (68, 80), state="firing"), K(D("16:40"), (68, 80), state="line", strength=104)] + out(D("16:41"), (40, 100), D("16:49"), D("16:58"), D("17:13")), ranks=3)
us("gridley", "Gridley's guns", "Capt. Samuel Gridley's artillery company: two field pieces in the redoubt, both lost", "Capt. Samuel Gridley", "artillery", 49,
   [K(D("21:00", 16), (-1440, 1250), h=135, state="column"), K(D("22:05", 16), NECK), K(D("22:35", 16), BUNKER), K(D("23:40", 16), (-80, 110)), K(D("00:10"), (28, -30), h=65, state="line"),
    K(D("15:30"), (28, -30), state="firing", fire=0.4), K(D("15:50"), (28, -30), state="line"), K(D("16:00"), (28, -30), state="firing", fire=0.4), K(D("16:22"), (28, -30), state="line"),
    K(D("16:40"), (28, -30), state="surrender", strength=45), K(D("17:45"), (28, -30))], guns=2)
us("callender", "Callender's guns", "Capt. Callender's two field pieces: taken out of action in the early afternoon, brought back to the rail fence by Capt. Trevett, one saved", "Capt. John Callender; Capt. Samuel Trevett", "artillery", 40,
   [K(D("21:00", 16), (-1460, 1260), h=135, state="column"), K(D("22:10", 16), NECK), K(D("22:40", 16), BUNKER), K(D("23:45", 16), (-90, 100)), K(D("00:15"), (-5, 25), h=65, state="line"),
    K(D("13:30"), (-5, 25), h=315, state="column"), K(D("14:00"), (-350, 430)), K(D("15:05"), (-350, 430)), K(D("15:30"), (40, 240), h=139, state="line"), K(D("15:32"), (40, 240), state="firing", fire=0.4),
    K(D("15:50"), (40, 240), state="line"), K(D("16:00"), (40, 240), state="firing", fire=0.4), K(D("16:22"), (40, 240), state="line"), K(D("16:34"), (40, 240), state="firing", fire=0.4),
    K(D("16:52"), (40, 240), state="column", h=315), K(D("17:05"), BUNKER, strength=34), K(D("17:20"), NECK), K(D("17:38"), OFF), K(D("17:39"), OFF, state="hidden")], guns=2)
# The rail fence, built from one o'clock: Knowlton's Connecticut men, then Reed's and Stark's New Hampshire regiments.
us("knowlton", "Knowlton", "Capt. Knowlton's 200 Connecticut men of Putnam's regiment: the fatigue party that built the hay-stuffed rail fence", "Capt. Thomas Knowlton", "infantry", 200,
   IN + [K(D("00:00"), (-40, 40), h=65, state="line"), K(D("13:00"), (-40, 40), state="column", h=45), K(D("13:12"), (60, 245), h=139, state="line"), K(D("15:30"), (60, 245), state="firing"),
         K(D("15:50"), (60, 245), state="line", strength=190), K(D("16:00"), (60, 245), state="firing"), K(D("16:22"), (60, 245), state="line", strength=178), K(D("16:32"), (60, 245), state="firing"),
         K(D("16:50"), (60, 245), state="line", strength=168)] + out(D("16:52"), (60, 245), D("17:00"), D("17:08"), D("17:22")))
us("reed", "Reed (3rd NH)", "Col. Reed's 3rd New Hampshire Regiment, at the rail fence", "Col. James Reed", "infantry", 300,
   [K(D("13:40"), OFF, h=135, state="column"), K(D("14:20"), NECK), K(D("14:40"), BUNKER), K(D("15:00"), (130, 300), h=139, state="line"), K(D("15:30"), (130, 300), state="firing"), K(D("15:50"), (130, 300), state="line", strength=288),
    K(D("16:00"), (130, 300), state="firing"), K(D("16:22"), (130, 300), state="line", strength=280), K(D("16:32"), (130, 300), state="firing"), K(D("16:50"), (130, 300), state="line", strength=274)] + out(D("16:53"), (130, 300), D("17:02"), D("17:10"), D("17:24")))
us("stark", "Stark (1st NH)", "Col. Stark's 1st New Hampshire Regiment: the left of the rail fence and the stone wall on the Mystic beach", "Col. John Stark; Maj. Andrew McClary (killed on the Neck)", "infantry", 400,
   [K(D("14:00"), OFF, h=135, state="column"), K(D("14:35"), NECK), K(D("14:50"), BUNKER), K(D("15:00"), BUNKER), K(D("15:15"), (215, 375), h=139, state="line"), K(D("15:30"), (215, 375), state="firing"),
    K(D("15:50"), (215, 375), state="line", strength=385), K(D("16:00"), (215, 375), state="firing"), K(D("16:22"), (215, 375), state="line", strength=372), K(D("16:32"), (215, 375), state="firing"),
    K(D("16:50"), (215, 375), state="line", strength=362)] + out(D("16:54"), (215, 375), D("17:03"), D("17:12"), D("17:25")) + [], ranks=3)
us("beach", "Stark's beach party", "Stark's men behind the stone wall thrown up across the Mystic beach at low water", "Col. John Stark", "infantry", 120,
   [K(D("15:05"), BUNKER, h=135, state="column"), K(D("15:20"), (322, 462), h=139, state="line"), K(D("15:30"), (322, 462), state="firing"), K(D("15:50"), (322, 462), state="line", strength=118),
    K(D("16:00"), (322, 462), state="firing"), K(D("16:22"), (322, 462), state="line", strength=115), K(D("16:32"), (322, 462), state="firing"), K(D("16:50"), (322, 462), state="line", strength=112),
    K(D("16:55"), (322, 462), h=315, state="retreat"), K(D("17:04"), (-150, 420)), K(D("17:14"), NECK, state="column"), K(D("17:33"), OFF), K(D("17:34"), OFF, state="hidden")], ranks=3)
# Massachusetts regiments that came over the Neck in the afternoon, to the flèches and the gap behind the breastwork.
def mass(id, short, name, cmd, n, t_in, t_at, at, h, keys, **extra):
    us(id, short, name, cmd, "infantry", n, [K(t_in, OFF, h=135, state="column"), K(f"1775-06-17 {t_in[11:13]}:{int(t_in[14:16]) + 30:02d}" if int(t_in[14:16]) < 30 else t_at, NECK), K(t_at, at, h=h, state="line")] + keys, **extra)
mass("brewer", "Brewer", "Col. Brewer's Massachusetts regiment, at the flèches between breastwork and fence", "Col. Jonathan Brewer (wounded)", 300, D("14:10"), D("15:10"), (40, 125), 135,
     [K(D("15:30"), (40, 125), state="firing"), K(D("15:50"), (40, 125), state="line", strength=294), K(D("16:00"), (40, 125), state="firing"), K(D("16:22"), (40, 125), state="line", strength=288),
      K(D("16:32"), (40, 125), state="firing"), K(D("16:44"), (40, 125), state="line", strength=282)] + out(D("16:45"), (40, 125), D("16:52"), D("17:02"), D("17:17")))
mass("nixon", "Nixon", "Col. Nixon's Massachusetts regiment, at the flèches", "Col. John Nixon (wounded)", 300, D("14:15"), D("15:12"), (10, 160), 135,
     [K(D("15:30"), (10, 160), state="firing"), K(D("15:50"), (10, 160), state="line", strength=296), K(D("16:00"), (10, 160), state="firing"), K(D("16:22"), (10, 160), state="line", strength=290),
      K(D("16:32"), (10, 160), state="firing"), K(D("16:46"), (10, 160), state="line", strength=287)] + out(D("16:47"), (10, 160), D("16:53"), D("17:03"), D("17:18")))
mass("little", "Little", "Col. Little's Massachusetts regiment, behind the breastwork", "Col. Moses Little", 300, D("14:30"), D("15:20"), (-20, 70), 115,
     [K(D("15:30"), (-20, 70), state="firing"), K(D("15:50"), (-20, 70), state="line", strength=290), K(D("16:00"), (-20, 70), state="firing"), K(D("16:22"), (-20, 70), state="line", strength=280),
      K(D("16:32"), (-20, 70), state="firing"), K(D("16:42"), (-20, 70), state="line", strength=270)] + out(D("16:43"), (-20, 70), D("16:50"), D("17:00"), D("17:16")))
mass("doolittle", "Doolittle", "Seven companies of Doolittle's regiment, at the south end of the rail fence", "Maj. Willard Moore (mortally wounded)", 200, D("14:40"), D("15:25"), (-10, 200), 139,
     [K(D("15:30"), (-10, 200), state="firing"), K(D("15:50"), (-10, 200), state="line", strength=197), K(D("16:00"), (-10, 200), state="firing"), K(D("16:22"), (-10, 200), state="line", strength=191),
      K(D("16:32"), (-10, 200), state="firing"), K(D("16:50"), (-10, 200), state="line", strength=188)] + out(D("16:52"), (-10, 200), D("16:59"), D("17:07"), D("17:21")))
mass("chester", "Chester, Clark, Coit", "Connecticut companies of Chester, Clark and Coit, and Lt. Col. Ward: the last to leave the fence", "Capt. John Chester", 250, D("15:00"), D("15:45"), (-50, 160), 139,
     [K(D("15:50"), (-50, 160), state="firing"), K(D("16:22"), (-50, 160), state="line", strength=238), K(D("16:32"), (-50, 160), state="firing"), K(D("16:54"), (-50, 160), state="line", strength=228)] + out(D("16:56"), (-50, 160), D("17:04"), D("17:12"), D("17:26")))
us("jackson", "Ward's companies", "Companies of Ward's regiment under Maj. Jackson, with Febiger's party of Gerrish's: a line between the hills to cover the retreat", "Maj. Michael Jackson", "infantry", 150,
   [K(D("16:00"), OFF, h=135, state="column"), K(D("16:25"), NECK), K(D("16:40"), (-180, 260), h=135, state="line"), K(D("16:44"), (-180, 260), state="firing"), K(D("17:02"), (-180, 260), state="line", strength=143),
    K(D("17:03"), (-180, 260), h=315, state="retreat"), K(D("17:10"), BUNKER, state="column"), K(D("17:18"), NECK), K(D("17:35"), OFF), K(D("17:36"), OFF, state="hidden")])
us("gardner", "Gardner", "Col. Gardner's Massachusetts regiment, come up late to the slope of Bunker Hill", "Col. Thomas Gardner (mortally wounded)", "infantry", 300,
   [K(D("16:10"), OFF, h=135, state="column"), K(D("16:35"), NECK), K(D("16:48"), (-300, 380), h=135, state="line"), K(D("16:50"), (-300, 380), state="firing"), K(D("17:05"), (-300, 380), state="line", strength=287),
    K(D("17:06"), (-300, 380), h=315, state="retreat"), K(D("17:12"), BUNKER, state="column"), K(D("17:20"), NECK), K(D("17:37"), OFF), K(D("17:38"), OFF, state="hidden")])
us("gerrish", "Gerrish", "Col. Gerrish's regiment, which stayed on Bunker Hill all afternoon; Gerrish was cashiered for it", "Col. Samuel Gerrish", "infantry", 300,
   [K(D("14:20"), OFF, h=135, state="column"), K(D("14:50"), NECK), K(D("15:10"), (-480, 540), h=135, state="line"), K(D("16:58"), (-480, 540), h=315, state="retreat", strength=295), K(D("17:06"), NECK, state="column"), K(D("17:25"), OFF), K(D("17:26"), OFF, state="hidden")])

# Howe's force: the first wave formed in three lines on Morton's Hill at one o'clock, the second landed at three.
def wave(id, short, name, cmd, type, n, land, t_land, slot, h, keys, **extra):
    br(id, short, name, cmd, type, n, [K(t_land, land, h=h, state="column"), K(f"1775-06-17 {t_land[11:13]}:{int(t_land[14:16]) + 15:02d}", slot, state="line")] + keys, **extra)
def assault(slot, fwd, hf, t0, t1, t2, t3, s1, s2):  # advance in line, fire, fall back to the start line
    return [K(t0, slot, state="line"), K(t1, fwd, h=hf, state="firing"), K(t2, fwd, state="retreat", strength=s1), K(t3, slot, h=hf, state="line", strength=s2)]
wave("li", "Light infantry", "The light infantry battalion: eleven flank companies, sent in column along the Mystic beach against the stone wall", "", "light_infantry", 350, (470, 60), D("12:50"), (420, 140), 300,
     [K(D("15:30"), (420, 140), state="column", h=330), K(D("15:38"), (430, 260)), K(D("15:43"), (350, 400), state="charge"), K(D("15:46"), (350, 400), state="rout", strength=240), K(D("15:52"), (440, 210), h=320, state="line"),
      K(D("16:00"), (440, 210), state="column", h=330), K(D("16:10"), (300, 360), state="charge"), K(D("16:16"), (300, 360), state="rout", strength=190), K(D("16:24"), (440, 210), h=320, state="line"),
      K(D("16:32"), (380, 330), state="firing"), K(D("16:48"), (380, 330), state="line", strength=175), K(D("16:55"), (200, 400), h=300, state="column"), K(D("17:08"), (-250, 480), state="line"), K(D("17:45"), (-250, 480))])
wave("gren", "Grenadiers", "The grenadier battalion: eleven flank companies, four deep, against the rail fence", "Lt. Col. James Abercrombie (mortally wounded)", "infantry", 350, (470, 30), D("12:52"), (385, 40), 300,
     assault((385, 40), (175, 260), 319, D("15:30"), D("15:42"), D("15:48"), D("15:57"), 260, 250) + assault((385, 40), (110, 230), 319, D("16:00"), D("16:12"), D("16:20"), D("16:28"), 200, 190) +
     [K(D("16:32"), (385, 40), state="column", h=300), K(D("16:38"), (120, 90), state="charge"), K(D("16:43"), (70, 65), state="line", strength=180), K(D("16:52"), (-50, 200), h=300, state="column"), K(D("17:06"), (-300, 440), state="line"), K(D("17:45"), (-300, 440))], ranks=4)
wave("r5", "5th Foot", "The 5th Foot, in support of the grenadiers", "", "infantry", 200, (470, 0), D("12:55"), (385, -60), 300,
     assault((385, -60), (220, 190), 319, D("15:31"), D("15:43"), D("15:48"), D("15:58"), 160, 150) + assault((385, -60), (160, 170), 319, D("16:01"), D("16:13"), D("16:20"), D("16:29"), 125, 120) +
     [K(D("16:33"), (385, -60), state="column", h=300), K(D("16:40"), (150, 110), state="line", h=300), K(D("16:55"), (0, 300), state="column"), K(D("17:10"), (-380, 420), state="line"), K(D("17:45"), (-380, 420))])
wave("r52", "52nd Foot", "The 52nd Foot, against the breastwork, then in the lead at the redoubt", "Maj. Arthur Williams (mortally wounded)", "infantry", 200, (470, -40), D("12:57"), (430, -10), 290,
     assault((430, -10), (190, 60), 290, D("15:31"), D("15:44"), D("15:49"), D("15:58"), 160, 150) + assault((430, -10), (170, 50), 290, D("16:01"), D("16:14"), D("16:21"), D("16:29"), 120, 110) +
     [K(D("16:32"), (430, -10), state="column", h=270), K(D("16:38"), (130, -10), state="charge"), K(D("16:42"), (40, -12), strength=100), K(D("16:44"), (40, -12), state="line", h=315), K(D("17:45"), (40, -12))])
wave("r38", "38th Foot", "The 38th Foot, Pigot's wing, against the redoubt", "Brig. Gen. Robert Pigot", "infantry", 200, (470, -80), D("12:59"), (430, -110), 290,
     assault((430, -110), (160, -80), 290, D("15:32"), D("15:45"), D("15:50"), D("15:59"), 170, 160) + assault((430, -110), (140, -70), 290, D("16:02"), D("16:15"), D("16:21"), D("16:30"), 135, 130) +
     [K(D("16:33"), (430, -110), state="column", h=280), K(D("16:39"), (120, -60), state="charge"), K(D("16:43"), (60, -45), state="line", h=300, strength=122), K(D("17:45"), (60, -45))])
wave("r43", "43rd Foot", "The 43rd Foot, Pigot's wing", "Maj. Roger Spendlove (mortally wounded)", "infantry", 200, (470, -120), D("13:01"), (430, -200), 290,
     assault((430, -200), (160, -150), 290, D("15:32"), D("15:45"), D("15:50"), D("15:59"), 170, 160) + assault((430, -200), (140, -140), 290, D("16:02"), D("16:15"), D("16:21"), D("16:30"), 135, 130) +
     [K(D("16:33"), (430, -200), state="column", h=280), K(D("16:40"), (110, -120), state="charge"), K(D("16:44"), (60, -90), state="line", h=300, strength=124), K(D("17:45"), (60, -90))])
wave("r47", "47th Foot", "The 47th Foot, landed with the second wave nearer the town, against the south face of the redoubt", "", "infantry", 300, (300, -330), D("15:00"), (240, -260), 320,
     [K(D("15:34"), (240, -260), state="line"), K(D("15:46"), (90, -150), h=330, state="firing"), K(D("15:51"), (90, -150), state="retreat", strength=270), K(D("16:00"), (240, -260), h=330, state="line", strength=265),
      K(D("16:03"), (240, -260)), K(D("16:16"), (80, -140), state="firing"), K(D("16:22"), (80, -140), state="retreat", strength=235), K(D("16:30"), (240, -260), h=330, state="line", strength=230),
      K(D("16:33"), (240, -260), state="column", h=320), K(D("16:40"), (60, -120), state="charge"), K(D("16:44"), (30, -60), state="line", h=330, strength=218), K(D("17:00"), (30, -60), state="column", h=250),
      K(D("17:20"), (-400, -40), state="line", h=300), K(D("17:45"), (-400, -40))])
wave("marines1", "1st Marines", "The 1st Battalion of Marines, on Pigot's left under fire from the houses of Charlestown", "Maj. John Pitcairn (killed)", "infantry", 300, (240, -400), D("15:02"), (170, -340), 340,
     [K(D("15:34"), (170, -340), state="line"), K(D("15:47"), (20, -190), h=350, state="firing"), K(D("15:52"), (20, -190), state="retreat", strength=270), K(D("16:00"), (170, -340), h=350, state="line", strength=262),
      K(D("16:03"), (170, -340)), K(D("16:16"), (10, -170), state="firing"), K(D("16:22"), (10, -170), state="retreat", strength=235), K(D("16:30"), (170, -340), h=350, state="line", strength=228),
      K(D("16:33"), (170, -340), state="column", h=350), K(D("16:40"), (10, -110), state="charge"), K(D("16:44"), (5, -50), state="line", h=350, strength=210), K(D("17:45"), (5, -50))])
br("clinton", "Clinton's reinforcement", "The 2nd Marines and the 63rd, brought over by Clinton with a party of walking wounded, landed below the burning town", "Maj. Gen. Henry Clinton; Maj. Small", "infantry", 400,
   [K(D("16:12"), (160, -520), h=330, state="column"), K(D("16:28"), (-10, -270), state="line", h=350), K(D("16:33"), (-10, -270), state="column", h=350), K(D("16:40"), (-20, -120), state="charge"),
    K(D("16:44"), (-25, -55), state="line", h=350, strength=385), K(D("17:00"), (-25, -55), state="column", h=300), K(D("17:12"), (-200, 180), state="line", h=315), K(D("17:45"), (-200, 180))])
br("ra", "Royal Artillery", "Six 6-pounders, sent 12-pounder shot by mistake and bogged in the clay below the breastwork; they enfiladed the breastwork in the last assault", "", "artillery", 60,
   [K(D("13:05"), (480, 20), h=300, state="column"), K(D("13:20"), (400, 90), state="line"), K(D("15:30"), (400, 90), state="column"), K(D("15:45"), (250, 150), state="line", h=290),
    K(D("16:34"), (180, 130), state="firing", fire=0.5), K(D("16:44"), (180, 130), state="line"), K(D("17:45"), (180, 130))], guns=6)
br("copps", "Copp's Hill battery", "Six 24-pounders and howitzers on Copp's Hill in Boston; its hot shot helped fire Charlestown", "", "artillery", 40,
   [K(D("21:00", 16), (430, -1000), h=338, state="line"), K(D("04:30"), (430, -1000), state="firing", fire=0.25), K(D("17:00"), (430, -1000), state="line"), K(D("17:45"), (430, -1000))], guns=6)
def hms(id, short, name, cmd, at, h, t_fire, t_stop, guns, fire=0.2):
    br(id, short, name, cmd, "artillery", guns * 5, [K(D("21:00", 16), at, h=h, state="line"), K(t_fire, at, state="firing", fire=fire), K(t_stop, at, state="line"), K(D("17:45"), at)], guns=min(guns // 2, 10))
hms("lively", "Lively", "HMS Lively, 20 guns: the first to see the works at dawn and open fire", "Capt. Thomas Bishop", (370, -557), 330, D("04:00"), D("17:00"), 20, 0.3)
hms("somerset", "Somerset", "HMS Somerset, 68 guns, Admiral Graves's flagship, in the ferry way", "Capt. Edward Le Cras", (123, -779), 345, D("05:30"), D("17:00"), 68, 0.15)
hms("falcon", "Falcon", "HMS Falcon, sloop, covering the landing at Moulton's Point", "Capt. John Linzee", (822, -223), 300, D("12:30"), D("16:30"), 16)
hms("glasgow", "Glasgow", "HMS Glasgow, 24 guns, in the Charles above the Mill Pond, firing across the Neck", "Capt. William Maltby", (-1234, 390), 40, D("09:00"), D("17:40"), 24)
hms("symmetry", "Symmetry", "The transport Symmetry, 20 guns, firing on the Neck with the Glasgow", "", (-1192, 557), 40, D("09:00"), D("17:40"), 20)
hms("floating", "Floating batteries", "Three or four floating batteries brought up on the flood tide to rake the Neck", "", (-1028, 390), 45, D("09:30"), D("17:40"), 8, 0.3)

PENINSULA = [(-1080, 950), (-800, 650), (-600, 380), (-450, 150), (-350, -150), (-250, -400), (-120, -600), (-16, -635), (120, -560), (247, -334), (380, -150), MOULTON, (430, 250), (300, 430), (0, 600), (-400, 720), (-740, 779), (-990, 900)]
WEST = PENINSULA[:12] + [(600, -150), (1500, -300), (1500, -1500), (900, -1500), (850, -1150), (700, -920), (250, -900), (150, -1100), (-200, -1150), (-450, -1300), (-700, -1500), (-1500, -1500), (-1500, 700), (-1300, 850)]
NORTH = [(-1500, 1100), (-1250, 1050)] + PENINSULA[17:11:-1] + [(600, -150), (1500, -300), (1500, 800), (1200, 850), (900, 900), (900, 1500), (-1500, 1500)]
MAIN_ST = [(-97, -504), (-300, -150), (-600, 250), NECK, (-1300, 1100), OFF, (-1500, 1300)]
features = [
    dict(type="water", poly=WEST), dict(type="water", poly=NORTH),
    dict(type="redoubt", name="the redoubt", poly=rsq(19, -17, 40, 15), at=[19, -70]),
    dict(type="works", name="breastwork", pts=[(40, 8), (60, 50), (74, 89)], at=[110, 50]),
    *[dict(type="works", pts=[(x - 10, y - 12), (x + 8, y), (x - 10, y + 12)]) for x, y in [(60, 112), (38, 138), (16, 164)]],
    dict(type="fence", name="rail fence", pts=[FENCE_SW, (120, 300), FENCE_NE], at=[150, 260], rot=41),
    dict(type="works", name="stone wall", pts=[WALL, (345, 480)], at=[360, 430]),
    dict(type="road", name="Main Street", pts=MAIN_ST), dict(type="road", pts=[(-97, -504), (-20, -400), (60, -250), (200, -130), MOULTON]),
    dict(type="road", pts=[(-300, -150), (-150, 0), (-60, 120), (-200, 260), BUNKER]),
    *[dict(type="ship", poly=ship(x, y, L=L, rot=r)) for x, y, L, r in [(370, -557, 36, 30), (123, -779, 60, 15), (822, -223, 30, 60), (-1234, 390, 40, 70), (-1192, 557, 36, 70)]],
    *[dict(type="ship", poly=ship(-1028 + dx, 390 + dy, L=18, W=8, rot=45)) for dx, dy in [(0, 0), (30, -20), (-30, 20)]],
    dict(type="smoke", name="Charlestown burning", at=[-130, -420], rate=5, spread=350, **{"from": D("15:25")}),
    dict(name="Charlestown", at=[-130, -430], rot=0), dict(name="Charlestown burns", at=[-130, -460], **{"from": D("15:25")}),
    dict(name="Breed's Hill", at=[-80, -90]), dict(name="Bunker Hill", at=[-453, 560]), dict(name="Charlestown Neck", at=[-1030, 960]), dict(name="to Cambridge", at=[-1380, 1300], rot=40),
    dict(name="Moulton's Point", at=[500, 130]), dict(name="Morton's Hill", at=[420, -70]), dict(name="Mystic River", at=[-200, 1100], rot=-20), dict(name="Charles River", at=[-900, -300], rot=45),
    dict(name="Mill Pond", at=[-560, 110]), dict(name="Boston: the North End", at=[550, -1200]), dict(name="Copp's Hill", at=[430, -1040]), dict(name="ferry to Boston", at=[-16, -680]),
    dict(name="the slough and brick kilns", at=[190, 190]), dict(name="Warren fell here", at=[-20, 40], **{"from": D("16:45")}),
    dict(name="Winthrop Square", at=[72, -270]),
]
events = [
    (D("21:00", 16), "The march from Cambridge", "At nine on the night of 16 June, after a prayer on Cambridge Common, Colonel Prescott marches about a thousand Massachusetts men with entrenching tools and two field pieces over Charlestown Neck. On Bunker Hill the officers argue for an hour over which hill to fortify. They choose Breed's Hill, the lower one, within cannon shot of Boston.", [-700, 700], 2600),
    (D("00:00"), "Digging on Breed's Hill", "Work begins at midnight: a redoubt eight rods square with walls six feet high, laid out by Colonel Gridley. Prescott twice walks down to the shore to listen to the Somerset's watch calling 'All's well'. The moon is four days past full.", [19, -17], 700),
    (D("04:00"), "The Lively opens fire", "At first light a sentry on the Lively sees the new works. Without orders she springs her cable and opens fire. Copp's Hill and the other ships join in. One man, Asa Pollard, is killed; Prescott walks the parapet to steady the rest.", [200, -250], 1500),
    (D("09:00"), "The breastwork", "Prescott sees the redoubt can be turned on its left and runs a breastwork a hundred yards north to a slough. The flood tide brings floating batteries up to rake the Neck. At nine his officers ask to be relieved; he refuses, and sends Major Brooks to Cambridge for reinforcements on foot, since Putnam has taken the horses.", [60, 60], 900, 20),
    (D("11:30"), "Boston parades", "Gage, Howe, Clinton and Burgoyne decide to land at Moulton's Point and attack the works in front. The light infantry, grenadiers and four regiments parade at half past eleven and embark at Long Wharf and the North Battery in twenty-eight barges.", [420, -500], 1800, 20),
    (D("12:50"), "The landing", "About one o'clock the first wave, fifteen hundred men, lands unopposed at Moulton's Point and forms three lines on Morton's Hill. Howe looks at the works, sends back for more troops, and lets the men eat their dinner.", [420, 0], 1200),
    (D("13:00"), "The rail fence", "Knowlton's two hundred Connecticut men take post six hundred feet behind the redoubt at a rail fence running to the Mystic. They build a second fence beside it and stuff the gap with new-mown hay. Three small flèches are dug across the open ground between the fence and the breastwork.", [100, 250], 900),
    (D("14:20"), "The Neck under fire", "Ward has sent Stark's and Reed's New Hampshire regiments. They cross the Neck under the fire of the Glasgow, the Symmetry and the floating batteries, Stark at a walk: 'one fresh man in action is worth ten fatigued ones'. He puts his left on the Mystic beach behind a stone wall thrown up at low water, and plants a stake a hundred feet in front of the fence.", [-800, 750], 1600, 20),
    (D("15:00"), "The second wave", "It is nearly three when the barges return with the 47th, the 1st Marines and the rest of the flank companies. They land nearer the town. Warren and Pomeroy arrive as volunteers, Warren to the redoubt, Pomeroy to the fence.", [300, -250], 1300),
    (D("15:25"), "Charlestown burns", "Snipers in the houses gall the marines on Pigot's left. Howe asks for the town to be fired: carcasses from Copp's Hill and a landing party from the Somerset set it alight. Four hundred buildings burn; the south-west wind carries the smoke off the field toward Boston.", [-100, -380], 1300),
    (D("15:30"), "The first assault", "About half past three the general battle begins. The light infantry go in column along the beach against the stone wall; the grenadiers, four deep, cross the fences in waist-high grass toward the rail fence; Pigot's regiments advance on the redoubt. The Americans hold their fire until the regulars reach Stark's stake and Prescott's twenty yards, then shatter the lines. The light companies melt away.", [220, 180], 1100, 5),
    (D("16:00"), "The second assault", "Howe forms again and comes on against Knowlton's fence instead of the beach, Pigot straight at the redoubt. For half an hour the lines fire volleys at the works and lose men; the Americans fire from behind rails and earth. Howe's staff are shot down round him. On Bunker Hill Putnam tries to bring down the regiments that have stopped there.", [150, 120], 1100, 5),
    (D("16:12"), "Clinton crosses", "Clinton, watching from Copp's Hill, crosses on his own authority with the 2nd Marines and the 63rd and rallies about two hundred walking wounded on the shore below the burning town. He takes them in on Pigot's left.", [50, -400], 1200),
    (D("16:30"), "Bayonets", "The men drop their knapsacks. Howe's artillery, freed of its wrong-calibre shot, is dragged to the gap and enfilades the breastwork. The light infantry hold the fence under fire while the 52nd, the 47th, the marines and Clinton's men come at the redoubt in column from three sides. Inside, the powder is nearly gone.", [100, 0], 800, 2),
    (D("16:40"), "The redoubt stormed", "The last cartridges are fired and stones thrown. Pigot climbs a corner by one of the trees; Pitcairn is shot at the parapet. With the regulars inside and the dust so thick the sally port can scarcely be seen, Prescott orders the retreat and goes out last, parrying bayonets with his sword. Warren, leaving among the last, is shot in the head.", [19, -17], 600, 2),
    (D("16:50"), "The fence holds", "Stark, Reed, Knowlton and the Connecticut companies keep the rail fence until the men from the redoubt are past, then withdraw in order over Bunker Hill. Burgoyne, watching from Boston: 'no flight; it was even covered with bravery and military skill.' Gardner is mortally wounded on the slope.", [-100, 300], 1300, 5),
    (D("17:00"), "Over the Neck", "The retreat crosses the Neck under the fire of the ships; Major McClary is cut in two by a cannon ball. About five the British take Bunker Hill and halt. Clinton urges a march on Cambridge; Howe, with a third of his force down, declines.", [-800, 700], 2000),
    (D("17:30"), "The cost", "The British lose 226 killed and 828 wounded of some three thousand engaged, a hundred of them officers, the heaviest loss of the war. The Americans lose about 450, with Warren, five of six guns and the tools. Gage: 'the rebels are not the despicable rabble too many have supposed'.", [-100, 150], 2400),
]
battle = dict(
    id="bunker-hill", name="Battle of Bunker Hill", date="1775-06-17", dateText="17 June 1775", place="Charlestown, Massachusetts",
    origin=dict(lat=42.3765, lon=-71.0610), extent=3000, start=D("21:00", 16), end=D("17:45"), speed=10, lapse=1800, menPerDot=5,
    sunrise="04:22", sunset="19:38", water=-0.5, terrainExaggeration=3, contourInterval=3, trees=dict(density=0.0004, clear=[WEST, NORTH]),
    wind=dict(x=0.7, y=0.5), palette=dict(ground="#a3ac7c", high="#d0cb9a", tree="rgba(55,90,45,0.5)", water="#7f9fc0"),
    fields=[PENINSULA],
    sides=dict(american=dict(name="Americans (Prescott, Putnam)", color="#1f55c4", light="#4a83e6", dark="#122c66"),
               british=dict(name="British (Howe, Pigot)", color="#c02a1f", light="#e2584a", dark="#5e1510")),
    features=features, units=units,
    events=[dict(t=e[0], title=e[1], text=e[2], at=e[3], view=e[4], **({"speed": e[5]} if len(e) > 5 else {})) for e in events],
    sources=[
        "Richard Frothingham, <i>History of the Siege of Boston</i> (1849), chapters IV and V: the march, the redoubt 'eight rods square', the breastwork a hundred yards north, the fence six hundred feet behind the redoubt, the landing about one, the battle 'about half past three' to five, the Neck under the fire of the Glasgow, the Symmetry and the floating batteries, and the loss tables by regiment.",
        "Gage's return of 17 June 1775 (226 killed, 828 wounded) and Ward's orderly book (115 killed, 305 wounded, 30 taken); Burgoyne's letter on the retreat; Prescott's letter to John Adams; Stark's return.",
        "Page's <i>Plan of the Action at Bunkers Hill</i> (1775, published 1793) for the shape of the works and the fences.",
        "National Park Service, Boston National Historical Park; the Bunker Hill Monument Association; <a href='https://www.battlefields.org/learn/revolutionary-war/battles/bunker-hill' target='_blank'>American Battlefield Trust</a>; Ketchum, <i>Decisive Day</i> (1974); Philbrick, <i>Bunker Hill</i> (2013).",
        "Weather: David Ludlum's reconstruction from Winthrop's Andover and Holyoke's Salem records (clear, 61 to 80 °F, wind backing south-west). Sun and moon computed for Charlestown in local apparent time.",
        "Terrain: USGS 3DEP elevation, 10 m, which shows the modern filled shoreline. The 1775 water line is drawn from the record (Main Street along the Mill Pond, the Mystic bank below the fence, the flats under the Navy Yard, Boston's North End and Mill Pond) and is approximate to about a hundred metres.",
        "What is reconstructed: the exact trace of the breastwork, the flèches and the rail fence (from Frothingham's distances, not a survey); the ships' anchorages; British regimental strengths, which Gage's return does not give; how the American reinforcements were shared between the fence, the flèches and the breastwork; and the loss of each unit, scaled from the regimental tables.",
    ],
)
json.dump(battle, open("battles/bunker-hill/battle.json", "w"), indent=1)
print(len(units), "units,", len(events), "events,", len(features), "features")
