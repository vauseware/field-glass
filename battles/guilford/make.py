# Builds battles/guilford/battle.json. Run from the repo root: python3 battles/guilford/make.py
# Local metres from 36.1320N 79.8450W (x east, y north). Anchors (NPS points of interest): Hoskins House (-671,-232),
# Forbis monument on the first line (-281,-235), Tour Stop 1 marker on the road (-187,-53), Greene monument (49,27),
# Hunting Creek at the road trace (483,260), Cavalry monument (492,137), courthouse site (863,260), Stop 6 (863,230).
# The third line follows Babits and Howard (2009): on the courthouse rise with the vale in front, not at the 1890s monuments.
# Strengths: Cornwallis's return of 15 March for the British; Hatch's brigade totals split per regiment for the Continentals.
import json, math
def dv(h): r = math.radians(h); return (math.sin(r), math.cos(r))
def rv(h): r = math.radians(h); return (math.cos(r), -math.sin(r))
def slot(c, h, u, back=0):            # u metres along the right-hand vector of a unit facing h; back metres to its rear
    dx, dy = dv(h); rx, ry = rv(h)
    return (round(c[0] + u * rx - back * dx), round(c[1] + u * ry - back * dy))
def K(t, p, **kw): return dict(t=t, x=p[0], y=p[1], **kw)
AH, BH = 262, 70                      # Americans face west-south-west down the Salisbury road; the British advance up it
C1, C2, C3 = (-190, -50), (139, 70), (860, 255)   # the three lines where they cross the road
CB = (-756, -205)                     # British deployment, 100 yards west of the Hoskins farmstead
def road_w(s):                        # point s metres down the road west-south-west of the US-220 junction, where the creek is
    return (round(-931 - 0.956 * s), round(-255 - 0.292 * s))
units = []
def unit(id, short, side, name, commander, type, strength, keys, **extra):
    units.append(dict(id=id, side=side, name=name, short=short, commander=commander, type=type, strength=strength, keys=keys, **extra))
us = lambda *a, **k: unit(*a[:1], a[1], "american", *a[2:], **k)
br = lambda *a, **k: unit(*a[:1], a[1], "british", *a[2:], **k)
GONE_N = lambda t0, p1, p2: [K(t0, p1, h=10, state="column"), K("16:10", p2), K("16:11", p2, state="hidden")]

# ---------------- Americans: first line ----------------
for id, short, name, cmd, u, path in [
    ("eaton", "Eaton", "Eaton's brigade, North Carolina militia", "Brig. Gen. Thomas Eaton", 115, [(100, 250), (600, 350), (900, 420)]),
    ("butler", "Butler", "Butler's brigade, North Carolina militia", "Brig. Gen. John Butler", -115, [(80, -230), (500, -300), (900, -400)])]:
    p = slot(C1, AH, u)
    us(id, short, name, cmd, "militia", 550, [K("12:30", p, h=AH, state="line"), K("14:00", p, state="firing"), K("14:05", p, h=70, state="rout", strength=530),
       K("14:12", path[0]), K("14:25", path[1], strength=520), K("14:40", path[2]), K("14:41", path[2], state="hidden")])
us("nccont", "NC Continentals", "North Carolina Continental detachment guarding the guns", "", "infantry", 40, [
    K("12:30", slot(C1, AH, 0, 15), h=AH, state="line"), K("13:50", slot(C1, AH, 0, 15), state="retreat"), K("14:05", (840, 258), state="line"), K("15:00", (840, 258), state="firing"),
    K("15:04", (840, 258), h=70, state="rout", strength=30), K("15:12", (930, 300)), K("15:30", (930, 300), h=10, state="retreat"), K("15:50", (960, 700)), K("16:00", (960, 700), state="hidden")])
us("singleton", "Singleton's guns", "Singleton's section, 1st Continental Artillery, two 6-pounders", "Capt. Anthony Singleton", "artillery", 30, [
    K("12:30", slot(C1, AH, 0, -15), h=AH, state="line"), K("13:30", slot(C1, AH, 0, -15), state="firing"), K("13:50", slot(C1, AH, 0, -15), state="retreat"), K("14:05", (850, 258), state="line"),
    K("15:00", (850, 258), state="firing"), K("15:05", (850, 258), state="surrender", strength=22), K("15:10", (850, 258), state="line"), K("15:32", (850, 258), state="surrender"), K("16:15", (850, 258))], guns=2)
us("lynch", "Lynch", "Lynch's Virginia riflemen (Bedford County)", "Col. Charles Lynch", "riflemen", 200, [
    K("12:30", slot(C1, AH, 330, -30), h=AH, state="skirmish"), K("13:55", slot(C1, AH, 330, -30), state="firing"), K("14:08", slot(C1, AH, 330, -30), strength=190), K("14:15", slot(C1, AH, 330, -30), h=70, state="retreat"),
    K("14:30", (350, 560)), K("14:45", (1050, 850), h=AH, state="line", strength=185), K("15:20", (1050, 850), state="firing"), K("15:28", (1050, 850), strength=180)] + GONE_N("15:35", (1050, 850), (1000, 1150)), loose=True)
us("kirkwood", "Kirkwood", "Kirkwood's Delaware company with Huffman's and Wallace's Virginia light companies", "Capt. Robert Kirkwood", "light_infantry", 110, [
    K("12:30", slot(C1, AH, 255, -10), h=AH, state="line"), K("13:55", slot(C1, AH, 255, -10), state="firing"), K("14:08", slot(C1, AH, 255, -10), strength=104), K("14:15", slot(C1, AH, 255, -10), h=70, state="retreat"),
    K("14:30", (330, 470)), K("14:45", (1020, 780), h=AH, state="line", strength=100), K("15:20", (1020, 780), state="firing"), K("15:28", (1020, 780), strength=96)] + GONE_N("15:35", (1020, 780), (980, 1100)))
us("washington", "Washington", "Washington's light dragoons (1st and 3rd Continental Light Dragoons)", "Lt. Col. William Washington", "cavalry", 86, [
    K("12:30", (950, 100), h=AH, state="line"), K("15:05", (950, 100), h=250, state="charge"), K("15:08", (830, 170)), K("15:12", (780, 190), strength=80), K("15:18", (900, 190), h=AH, state="line")] + GONE_N("15:35", (900, 190), (990, 900)))
# the left flank: the separate fight drifts half a mile south to the knoll in today's Country Park
us("campbell", "Campbell", "Campbell's Virginia riflemen", "Col. William Campbell", "riflemen", 200, [
    K("12:30", slot(C1, AH, -330), h=250, state="skirmish"), K("13:55", slot(C1, AH, -330), state="firing"), K("14:06", slot(C1, AH, -330), h=120, state="retreat", strength=194), K("14:15", (50, -520), h=280, state="firing"),
    K("14:30", (280, -720), h=300, strength=185), K("14:50", (470, -880)), K("15:15", (560, -980), strength=178), K("15:22", (560, -980), h=130, state="rout", strength=175), K("15:40", (880, -1300), state="retreat"), K("15:45", (880, -1300), state="hidden")], loose=True)
us("winston", "Winston", "Winston's Surry County riflemen", "Maj. Joseph Winston", "riflemen", 50, [
    K("12:30", slot(C1, AH, -255), h=250, state="skirmish"), K("13:55", slot(C1, AH, -255), state="firing"), K("14:06", slot(C1, AH, -255), h=120, state="retreat"), K("14:15", (0, -470), h=280, state="firing"),
    K("14:30", (230, -660), h=300), K("14:50", (400, -840)), K("15:15", (500, -930), strength=47), K("15:22", (500, -930), h=130, state="rout", strength=46), K("15:40", (820, -1250), state="retreat"), K("15:45", (820, -1250), state="hidden")], loose=True)
us("leefoot", "Lee's infantry", "Lee's Legion infantry", "Lt. Col. Henry Lee", "light_infantry", 82, [
    K("12:30", slot(C1, AH, -400), h=250, state="line"), K("13:55", slot(C1, AH, -400), state="firing"), K("14:06", slot(C1, AH, -400), h=120, state="retreat"), K("14:15", (80, -600), h=290, state="firing"),
    K("14:30", (320, -800), h=300, strength=76), K("14:50", (540, -960)), K("15:15", (650, -1030), strength=72), K("15:25", (650, -1030), h=120, state="retreat"), K("15:40", (1050, -1300)), K("15:45", (1050, -1300), state="hidden")])
us("leehorse", "Lee's horse", "Lee's Legion cavalry", "Lt. Col. Henry Lee", "cavalry", 75, [
    K("12:30", slot(C1, AH, -460, 20), h=250, state="line"), K("14:06", slot(C1, AH, -460, 20), h=120, state="retreat"), K("14:15", (120, -660), h=300, state="line"), K("14:30", (380, -860)),
    K("14:50", (600, -1000)), K("15:15", (700, -1060), strength=70), K("15:25", (700, -1060), h=120, state="retreat"), K("15:40", (1150, -1350)), K("15:45", (1150, -1350), state="hidden")])
# ---------------- second line ----------------
us("lawson", "Lawson", "Lawson's brigade, Virginia militia (Randolph, Holcombe)", "Brig. Gen. Robert Lawson", "militia", 600, [
    K("12:30", slot(C2, AH, 130), h=AH, state="line"), K("14:10", slot(C2, AH, 130), state="firing"), K("14:30", slot(C2, AH, 130), h=60, state="retreat", strength=560), K("14:45", (450, 520)),
    K("15:00", (760, 880), h=AH, state="line", strength=540)] + GONE_N("15:35", (760, 880), (900, 1200)))
us("stevensn", "Stevens", "Stevens's brigade, Virginia militia, right wing (Perkins, Cocke)", "Brig. Gen. Edward Stevens", "militia", 350, [
    K("12:30", slot(C2, AH, -100), h=AH, state="line"), K("14:10", slot(C2, AH, -100), state="firing"), K("14:35", slot(C2, AH, -100), h=70, state="retreat", strength=315), K("14:50", (600, 150)),
    K("15:05", (900, 80), h=AH, state="line", strength=310)] + GONE_N("15:30", (900, 80), (980, 600)))
us("stevenss", "Stuart's Virginians", "Stevens's brigade, left wing under Maj. Alexander Stuart (Moffett, McDowell)", "Maj. Alexander Stuart", "militia", 250, [
    K("12:30", slot(C2, AH, -260), h=AH, state="line"), K("14:12", slot(C2, AH, -260), state="firing"), K("14:22", slot(C2, AH, -260), h=170, state="charge", strength=240), K("14:30", (260, -560), h=160, state="firing"),
    K("14:42", (260, -560), h=60, state="retreat", strength=225), K("15:00", (700, -100), h=AH, state="line")] + GONE_N("15:30", (700, -100), (950, 400)))
# ---------------- third line, on the courthouse rise ----------------
us("md1", "1st Maryland", "1st Maryland Regiment", "Col. John Gunby; Lt. Col. John Eager Howard", "infantry", 350, [
    K("12:30", (787, 353), h=AH, state="line"), K("14:42", (787, 353), state="firing"), K("14:48", (787, 353), state="charge", strength=335), K("14:52", (700, 420)), K("14:55", (787, 353), state="line"),
    K("15:03", (787, 353), h=180, state="charge"), K("15:06", (820, 290), h=190, state="firing"), K("15:08", (820, 290), state="charge", strength=320), K("15:12", (850, 235)),
    K("15:15", (850, 235), h=AH, state="retreat"), K("15:25", (900, 330), state="line", strength=300)] + GONE_N("15:32", (900, 330), (1000, 1000)))
us("md2", "2nd Maryland", "2nd Maryland Regiment, mostly new recruits", "Lt. Col. Benjamin Ford", "infantry", 280, [
    K("12:30", (868, 196), h=AH, state="line"), K("15:00", (868, 196), state="firing"), K("15:03", (868, 196), h=70, state="rout", strength=240), K("15:10", (980, 120)), K("15:20", (1000, 130), h=AH, state="line", strength=230)] + GONE_N("15:30", (1000, 130), (1050, 1000)))
us("hawes", "Hawes", "2nd Virginia Regiment (Hawes's)", "Lt. Col. Samuel Hawes", "infantry", 390, [
    K("12:30", (880, 470), h=320, state="line"), K("14:42", (880, 470), state="firing"), K("14:48", (880, 470), state="line", strength=375), K("15:20", (880, 470), state="firing"), K("15:28", (880, 470), strength=362)] + GONE_N("15:32", (880, 470), (1000, 1100)))
us("green", "Green", "1st Virginia Regiment (Green's)", "Col. John Green", "infantry", 388, [
    K("12:30", (1000, 720), h=280, state="line"), K("15:26", (1000, 720), state="firing"), K("15:34", (1000, 720), strength=378)] + GONE_N("15:38", (1000, 720), (1050, 1300)))
us("finley", "Finley's guns", "Finley's section, 1st Continental Artillery, two 6-pounders", "Capt. Lt. Ebenezer Finley", "artillery", 29, [
    K("12:30", (960, 600), h=300, state="line"), K("14:42", (960, 600), state="firing"), K("14:50", (960, 600), state="line"), K("15:20", (960, 600), state="firing"), K("15:30", (960, 600), state="line"),
    K("15:34", (960, 600), state="surrender", strength=20), K("16:15", (960, 600))], guns=2)
us("malmedy", "Malmedy", "Malmedy's mounted militia and the Guilford light horse, in reserve", "Col. Francois de Malmedy", "cavalry", 100, [
    K("12:30", (1000, 450), h=AH, state="line")] + GONE_N("15:35", (1000, 450), (1030, 900)))

# ---------------- British ----------------
def brit(id, short, name, cmd, type, n, s, u, back, keys, **extra):
    br(id, short, name, cmd, type, n, [K("12:30", road_w(s), h=70, state="column"), K("13:15", road_w(max(0, s - 330))), K("13:35", slot(CB, BH, u, back), state="line")] + keys, **extra)
brit("ra", "Macleod's guns", "Royal Artillery detachment, three light guns", "Lt. John Macleod", "artillery", 50, 50, 0, -30, [
    K("13:36", slot(CB, BH, 0, -30), state="firing"), K("13:50", slot(CB, BH, 0, -30), state="line"), K("13:55", slot(CB, BH, 0, -30)), K("14:10", (-190, -50)), K("14:40", (200, 120)),
    K("15:00", (770, 265), state="firing"), K("15:20", (770, 265), state="line"), K("16:15", (770, 265))], guns=3)
brit("r23", "23rd Foot", "23rd Regiment of Foot (Royal Welch Fusiliers)", "Capt. Thomas Peter", "infantry", 238, 120, -60, 0, [
    K("13:52", slot(CB, BH, -60)), K("14:00", (-380, -20), state="firing"), K("14:03", (-380, -20), state="charge", strength=230), K("14:06", (-230, -30), strength=222), K("14:12", (65, 178), state="firing", strength=215),
    K("14:35", (65, 178), state="charge", strength=200), K("14:50", (450, 260)), K("15:15", (780, 300), state="firing", strength=190), K("15:30", (780, 300), state="line", strength=170), K("16:15", (780, 300))])
brit("r71", "71st Highlanders", "2nd Battalion, 71st Regiment (Fraser's Highlanders)", "Capt. Robert Hutcheson", "infantry", 244, 190, 60, 0, [
    K("13:52", slot(CB, BH, 60)), K("14:00", (-370, -110), state="firing"), K("14:03", (-370, -110), state="charge", strength=236), K("14:06", (-215, -120)), K("14:12", (97, -50), state="firing", strength=228),
    K("14:35", (97, -50), state="charge", strength=210), K("14:55", (500, 50)), K("15:15", (760, 130), state="firing", strength=195), K("15:30", (760, 130), state="line", strength=181), K("16:15", (760, 130))])
brit("r33", "33rd Foot", "33rd Regiment of Foot (Webster's)", "Lt. Col. James Webster", "infantry", 234, 340, -170, 0, [
    K("13:52", slot(CB, BH, -170)), K("14:00", (-440, 160)), K("14:08", (-292, 257), state="firing", strength=228), K("14:15", (-292, 257), state="charge"), K("14:25", (150, 380)), K("14:35", (400, 450)),
    K("14:42", (720, 480), state="firing", strength=205), K("14:48", (720, 480), h=250, state="rout", strength=185), K("14:55", (560, 440), state="retreat"), K("15:00", (560, 440), h=70, state="line", strength=180),
    K("15:15", (560, 440), state="charge"), K("15:25", (760, 520), state="firing"), K("15:30", (760, 520), state="line", strength=160), K("16:15", (760, 520))])
brit("jaegers", "Jägers", "Ansbach-Bayreuth jäger company", "Capt. Friedrich von Roeder", "light_infantry", 84, 20, -120, 40, [
    K("13:52", slot(CB, BH, -120, 40)), K("14:00", (-480, 120), state="skirmish"), K("14:25", (120, 430)), K("14:42", (700, 540), state="firing", strength=80), K("14:48", (700, 540), h=250, state="rout", strength=76),
    K("14:55", (540, 480), state="retreat"), K("15:00", (540, 480), h=70, state="line"), K("15:15", (540, 480), state="charge"), K("15:25", (740, 580), state="firing"), K("15:30", (740, 580), state="line", strength=74), K("16:15", (740, 580))], loose=True)
brit("guardsli", "Guards light company", "Guards light infantry company", "Capt. William Maynard", "light_infantry", 60, 35, -100, 40, [
    K("13:52", slot(CB, BH, -100, 40)), K("14:00", (-470, 80), state="skirmish"), K("14:25", (100, 400)), K("14:42", (690, 430), state="firing", strength=56), K("14:48", (690, 430), h=250, state="rout", strength=50),
    K("14:55", (530, 420), state="retreat"), K("15:00", (530, 420), h=70, state="line"), K("15:15", (530, 420), state="charge"), K("15:25", (730, 470), state="firing"), K("15:30", (730, 470), state="line", strength=44), K("16:15", (730, 470))], loose=True)
brit("guards2", "2nd Guards", "2nd Battalion, Brigade of Guards, with the grenadier company", "Lt. Col. James Stuart; Brig. Gen. Charles O'Hara", "infantry", 250, 270, 0, 120, [
    K("14:08", slot(CB, BH, 0, 120), state="charge"), K("14:15", (30, 60), state="line"), K("14:18", (30, 60), state="firing"), K("14:35", (30, 60), state="charge", strength=235), K("14:45", (400, 200)),
    K("14:50", (650, 230), strength=225), K("14:55", (650, 230), state="charge"), K("15:00", (815, 210), state="firing", strength=215), K("15:03", (815, 210), state="charge"), K("15:05", (850, 215), strength=200),
    K("15:08", (850, 215), h=250, state="rout", strength=150), K("15:15", (700, 230), state="retreat"), K("15:25", (660, 240), h=70, state="line", strength=120), K("15:40", (660, 240), strength=110), K("16:15", (660, 240))])
brit("guards1", "1st Guards", "1st Battalion, Brigade of Guards", "Lt. Col. Chapple Norton", "infantry", 200, 480, 110, 100, [
    K("14:08", slot(CB, BH, 110, 100), state="charge"), K("14:20", (-60, -520), h=110), K("14:35", (200, -700), state="firing", strength=185), K("14:50", (420, -880), strength=160), K("15:10", (540, -960), strength=140),
    K("15:30", (540, -960), state="line", strength=130), K("15:45", (600, -900)), K("16:15", (600, -900))])
brit("bose", "von Bose", "Hessian Regiment von Bose", "Maj. Johann Christian du Buy", "infantry", 321, 410, 170, 0, [
    K("13:52", slot(CB, BH, 170)), K("14:02", (-380, -430), state="firing", strength=300), K("14:06", (-380, -430), state="charge"), K("14:12", (-144, -377), strength=290), K("14:20", (-144, -377), h=120, state="firing"),
    K("14:35", (150, -640), strength=275), K("14:50", (380, -820), strength=260), K("15:10", (520, -920), strength=245), K("15:30", (520, -920), state="line", strength=241), K("15:45", (560, -860)), K("16:15", (560, -860))])
brit("legion", "Tarleton", "British Legion cavalry with a 17th Light Dragoons detachment", "Lt. Col. Banastre Tarleton", "cavalry", 272, 560, 0, 250, [
    K("13:36", slot(CB, BH, 0, 250), state="column"), K("14:10", (-300, -70)), K("14:40", (0, 20)), K("15:15", (0, 20), h=150, state="charge"), K("15:22", (560, -940), strength=268), K("15:30", (560, -940), state="line"), K("15:45", (600, -860)), K("16:15", (600, -860))])

ROAD = [(-1505, -430), (-931, -255), (-671, -174), (-197, -26), (49, 91), (330, 170), (619, 267), (787, 249), (1132, 245), (1500, 250)]
REEDY = [(870, 262), (900, 600), (940, 1000), (960, 1500)]
fields = [[(-640, -165), (-215, -45), (-250, 210), (-690, 90)], [(-640, -175), (-215, -55), (-200, -200), (-620, -330)], [(-560, -520), (-180, -410), (-150, -560), (-520, -690)],
          [(250, 100), (420, 130), (400, 300), (240, 270)], [(820, 120), (1080, 90), (1120, 430), (840, 460)]]
events = [
    ("12:30", "Two armies on the Salisbury road", "At dawn Lee's Legion and Campbell's riflemen met Tarleton at New Garden Meeting House, four miles to the south-west, and fell back fighting. Greene's 4,400 men wait in three lines astride the road. Cornwallis's 1,900 regulars come on without breakfast.", [-500, -150], 1600),
    ("13:20", "The head of the column", "The British come down the hill, across Little Horsepen Creek and up toward the Hoskins farm. Singleton's two six-pounders open on the road. Macleod's guns answer, and for twenty minutes they duel while Cornwallis deploys: Leslie on the right, Webster on the left, the Guards in reserve.", [-760, -210], 1000),
    ("13:52", "Across the fields", "The 23rd and the 71st climb the fence into four hundred yards of wet ploughed ground. Behind the far fence the North Carolina militia have been asked for two volleys and no more.", [-430, -120], 900),
    ("14:02", "The first line", "At forty yards the militia fire. The British volley back and go in with the bayonet. The North Carolinians run, most of them straight through the Virginians toward the courthouse and on home. On the flanks the riflemen stand, and the British line begins to split in three.", [-230, -80], 800),
    ("14:13", "The second line", "Three hundred yards on, in woods thick with underbrush, the Virginia militia fight from tree to tree. The 23rd and the Guards grenadiers press Lawson; the 71st and the 2nd Guards press Stevens. Cornwallis's horse is shot under him.", [120, 60], 800),
    ("14:27", "The separate fight", "On the American left, Lee and Campbell draw the 1st Guards and the Hessians half a mile south into the woods, away from the main battle. Stuart's Virginians strike the Guards in the flank before von Bose comes up to save them.", [250, -650], 1200),
    ("14:41", "Webster goes in alone", "The 33rd, with the jägers and the Guards light company, crosses the vale and climbs at the American right before the rest of the army is up. The 1st Maryland and Hawes's Virginians shatter it with volleys. Webster, shot through the knee, pulls back across the ravine.", [720, 460], 700),
    ("14:55", "The Guards and the 2nd Maryland", "Stuart's 2nd Guards reach the cleared ground by the courthouse and find the 2nd Maryland, raw recruits, trying to wheel to meet them. One volley and a charge break the Marylanders and take Singleton's guns.", [800, 215], 600),
    ("15:04", "Howard wheels the 1st Maryland", "Gunby and Howard swing the 1st Maryland onto the Guards' flank and fire so close that the muzzle flashes meet. Washington's dragoons come in from the rear. Stuart is killed, the guns are retaken, and the Guards are driven back into the field under grape from their own three-pounders.", [810, 250], 500),
    ("15:21", "Greene decides", "The 71st and the 23rd come up into the clearing and Webster drives at Hawes again. With his left broken and the British gaining on his right, Greene orders a retreat. Green's Virginians cover it. The four guns, their horses dead, are left behind.", [820, 320], 900),
    ("15:40", "Another such victory", "The Americans go north by the Reedy Fork road and are followed only three miles. Cornwallis holds the field with 532 men killed or wounded, a quarter of his army, the Guards above half. It rains all night on the wounded. Greene lost 79 killed and 185 wounded; most of the militia went home.", [850, 600], 1400),
]
battle = dict(
    id="guilford", name="Battle of Guilford Courthouse", date="1781-03-15", dateText="15 March 1781", place="Guilford Courthouse, North Carolina",
    origin=dict(lat=36.1320, lon=-79.8450), extent=3000, start="12:30", end="16:15", speed=20, menPerDot=10,
    terrainExaggeration=2, contourInterval=3, trees=dict(density=0.004), fields=fields, wind=dict(x=0.5, y=0.3),
    palette=dict(ground="#b0ab86", high="#d8d2aa", tree="rgba(95,80,55,0.42)", field="rgba(236,222,170,0.55)"),
    sides=dict(american=dict(name="Americans (Greene)", color="#1f55c4", light="#4a83e6", dark="#122c66"),
               british=dict(name="British and Hessians (Cornwallis)", color="#c02a1f", light="#e2584a", dark="#5e1510")),
    features=[dict(type="road", name="New Garden Road", pts=ROAD), dict(type="road", name="Reedy Fork Road", pts=REEDY),
              dict(type="creek", name="Hunting Creek", pts=[(220, -214), (273, -10), (386, 134), (483, 260), (600, 450), (700, 600), (850, 750), (900, 900), (1000, 1100), (1050, 1500)]),
              dict(type="creek", name="Little Horsepen Creek", pts=[(-1150, 1500), (-1100, 800), (-1050, 300), (-980, -150), (-950, -260), (-1050, -500), (-1100, -900), (-1150, -1500)]),
              dict(type="fence", name="first-line fence", pts=[(-210, -420), (-200, -45), (-230, 230)]), dict(type="fence", name="middle fence", pts=[(-400, -470), (-385, -100), (-410, 220)]),
              dict(type="fence", name="west fence", pts=[(-660, -350), (-640, -165), (-690, 90)]),
              dict(name="New Garden Road (the Great Salisbury Road)", at=[-500, -70], rot=17), dict(name="to New Garden Meeting House, 4 miles", at=[-1250, -400], rot=17),
              dict(name="Reedy Fork Road, to Speedwell Ironworks", at=[1000, 1250], rot=85), dict(name="Hoskins farm", at=[-671, -290]), dict(name="Little Horsepen Creek", at=[-1020, 500], rot=80),
              dict(name="Hunting Creek", at=[660, 560], rot=45), dict(name="Guilford Courthouse", at=[863, 295]), dict(name="Greene monument (1915)", at=[49, 2]), dict(name="Visitor Center", at=[-116, -120]),
              dict(name="Cavalry monument", at=[492, 160]), dict(name="the knoll in Country Park: the separate fight ends here", at=[450, -1060])],
    units=units,
    events=[dict(t=t, title=a, text=b, at=at, view=v) for t, a, b, at, v in events],
    sources=[
        "Lawrence E. Babits and Joshua B. Howard, <i>Long, Obstinate, and Bloody: The Battle of Guilford Courthouse</i> (UNC Press, 2009), read through the NPS Historic Resource Study (2017), which cites it page by page: the third line on the courthouse rise, the fences and fields, the sequence at the third line.",
        "Cornwallis to Lord George Germain, 17 March 1781. <a href='https://www.battlefields.org/learn/primary-sources/1781-cleared-ground-about-guilford-court-house' target='_blank'>Transcription at the American Battlefield Trust</a>: the deployment, Leslie right and Webster left, 'about half an hour past one', the Guards driven back by Washington's dragoons.",
        "Nathanael Greene to Samuel Huntington, 16 March 1781, and Otho Williams's return of 16 March: 79 killed, 185 wounded, 1,046 missing.",
        "Charles E. Hatch, <i>The Battle of Guilford Courthouse</i> (NPS, 1971): the British return of 15 March (1,924 all ranks) and losses by regiment; American brigade strengths.",
        "National Park Service, Guilford Courthouse National Military Park: <a href='https://www.nps.gov/guco/self-guided-driving-tour.htm' target='_blank'>driving tour</a>, tour stop pages and monument coordinates; Courtland Reid, NPS Historical Handbook 30 (1959).",
        "Joshua Howard, <a href='https://www.ncpedia.org/history/usrevolution/guilford-courthouse' target='_blank'>Battle of Guilford Courthouse</a>, NCpedia (2009); Ian Saberton on Cornwallis's numbers, <i>Journal of the American Revolution</i> (2017).",
        "American Battlefield Trust, <a href='https://www.battlefields.org/learn/revolutionary-war/battles/guilford-court-house' target='_blank'>Guilford Court House</a>.",
        "Terrain: USGS 3DEP elevation, 10 m. Monument and tour stop coordinates from the NPS points-of-interest service and OpenStreetMap.",
        "What is reconstructed: the exact positions of the three lines (the park draws them but publishes no coordinates), the Continental regiment strengths (split from brigade totals), the course of the separate fight south of the park, and every position between the recorded moments. The clock follows Cornwallis; the NPS handbook starts an hour earlier.",
    ],
)
json.dump(battle, open("battles/guilford/battle.json", "w"), indent=1)
print(len(units), "units,", len(events), "events")
