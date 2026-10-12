# Builds battles/cowpens/battle.json. Run from the repo root: python3 battles/cowpens/make.py
# Figures follow Babits (1998) and the sources listed at the bottom. Local metres from 35.1344N 81.8140W (x east, y north).
# Anchors: Washington Light Infantry monument (-15,-39) on Howard's line; NPS waysides Continental (24,26),
# skirmish (165,-82), cavalry (-61,113), British line / sword clash (364,-167); visitor centre (-373,251).
import json, math
AH, BH = 125, 305                      # Americans face SE down the slope; British advance NW up the Green River Road
def dv(h): r = math.radians(h); return (math.sin(r), math.cos(r))
def rv(h): r = math.radians(h); return (math.cos(r), -math.sin(r))
def slot(c, h, u, back=0):            # u metres along the right-hand vector of a unit facing h; back metres to its rear
    dx, dy = dv(h); rx, ry = rv(h)
    return (round(c[0] + u * rx - back * dx), round(c[1] + u * ry - back * dy))
ROAD = [(-900, 640), (-480, 420), (-250, 280), (-61, 113), (24, 26), (165, -82), (364, -167), (600, -210), (1000, -270)]
def road_se(s):                        # point s metres along the road south-east of the sword-clash wayside
    pts = ROAD[6:]
    for a, b in zip(pts, pts[1:]):
        L = math.dist(a, b)
        if s <= L: return (round(a[0] + (b[0] - a[0]) * s / L), round(a[1] + (b[1] - a[1]) * s / L))
        s -= L
    return pts[-1]
def K(t, p, **kw): return dict(t=t, x=p[0], y=p[1], **kw)

C0 = (45, 10)                          # main line centre, on the road
C1 = slot(C0, AH, 0, -137)             # militia line, 150 yd ahead
C2 = slot(C0, AH, 0, -247)             # skirmish line, 120 yd ahead of the militia
CL = slot(C0, AH, 0, -197)             # British halt 60 m short of the militia line
CM = slot(C0, AH, 0, -70)              # British firing line, ~75 yd from Howard
CS = slot(C0, AH, 0, 63)               # where the British mob met the about-face volley, 30 yd from the new American line
CB = (494, -191)                       # British deployment astride the road, ~300 yd from the skirmishers
BHB = 300                              # British facing at deployment, where the road bends
units = []
SHORT = {}
def unit(id, short, side, name, commander, type, strength, keys, **extra):
    units.append(dict(id=id, side=side, name=name, short=short, commander=commander, type=type, strength=strength, keys=keys, **extra))

# ---------------- Americans ----------------
def main_line(id, short, name, cmd, type, n, u, hits, tail):
    p0, p1, p2 = slot(C0, AH, u), slot(C0, AH, u, 90), slot(C0, AH, u, -55)
    unit(id, short, "american", name, cmd, type, n, [
        K("06:40", p0, h=AH, state="line"), K("07:28", p0, state="firing"), K("07:41", p0, h=BH, state="retreat", strength=n - hits),
        K("07:45", p1), K("07:46", p1, h=AH, state="firing"), K("07:48", p1, state="charge"), K("07:51", p2)] + tail(p2))
main_line("triplett", "Triplett", "Virginia militia, left wing (Triplett, Tate, Gilmore)", "Maj. Francis Triplett", "riflemen", 120, -55, 6,
          lambda p: [K("07:53", p, state="line"), K("08:10", p)])
main_line("howard", "Howard", "Continental light infantry (Maryland, Delaware, Virginia companies)", "Lt. Col. John Eager Howard", "light_infantry", 300, 25, 12,
          lambda p: [K("07:53", p, state="line"), K("08:10", p)])
main_line("varight", "Virginians", "Virginia militia, right wing (Buchanan, Campbell, Lawson)", "Capt. Patrick Buchanan", "militia", 165, 111, 7,
          lambda p: [K("07:52", p, state="charge"), K("07:54", (40, -120), h=230, state="firing"), K("07:57", (40, -120), state="line"), K("08:10", (40, -120))])
main_line("connelly", "Connelly", "North Carolina State Troops company", "Capt. Henry Connelly", "infantry", 20, 149, 1,
          lambda p: [K("07:52", p, state="charge"), K("07:54", (70, -95), h=230, state="firing"), K("07:57", (70, -95), state="line"), K("08:10", (70, -95))])

def militia(id, short, name, cmd, n, u, path):
    p0 = slot(C1, AH, u)
    unit(id, short, "american", name, cmd, "militia", n, [K("06:40", p0, h=AH, state="line"), K("07:20", p0, state="firing"), K("07:23", p0, state="retreat", strength=n - 4)] + path)
# left wing withdraws round the American left (north-east), re-forms behind the second crest, returns on the British right
militia("brandon", "Brandon", "Fair Forest Regiment, 7 companies", "Col. Thomas Brandon", 250, -90,
        [K("07:27", (230, 120)), K("07:31", (120, 210)), K("07:36", (60, 230), h=AH, state="line"), K("07:46", (60, 230), state="charge"), K("07:51", (110, 160), h=235, state="firing"), K("07:56", (110, 160), state="line"), K("08:10", (110, 160))])
militia("hayes", "Hayes", "Little River Regiment, 5 companies", "Lt. Col. Joseph Hayes", 200, 0,
        [K("07:27", (200, 60)), K("07:31", (130, 180)), K("07:36", (20, 215), h=AH, state="line"), K("07:46", (20, 215), state="charge"), K("07:51", (150, 100), h=275, state="firing"), K("07:56", (150, 100), state="line"), K("08:10", (150, 100))])
# right wing withdraws by the right (south-west), re-forms, and comes back onto the 71st from behind
militia("roebuck", "Roebuck", "Spartan Regiment detachment, 3 companies", "Lt. Col. Benjamin Roebuck", 120, 60,
        [K("07:27", (-20, -200)), K("07:31", (-120, -150)), K("07:36", (-150, -60), h=AH, state="line"), K("07:44", (-150, -60), state="charge"), K("07:50", (-80, -230), h=60, state="firing"), K("07:56", (-80, -230), state="line"), K("08:10", (-80, -230))])
militia("thomas", "Thomas", "Spartan Regiment, 4 companies", "Col. John Thomas Jr.", 160, 112,
        [K("07:27", (-60, -240)), K("07:31", (-170, -190)), K("07:36", (-200, -100), h=AH, state="line"), K("07:44", (-200, -100), state="charge"), K("07:50", (-20, -290), h=350, state="firing"), K("07:56", (-20, -290), state="line"), K("08:10", (-20, -290))])
militia("ncmil", "NC militia", "North Carolina militia battalion (Burke and Rutherford counties)", "Maj. Joseph McDowell", 130, 165,
        [K("07:27", (-100, -280)), K("07:31", (-220, -230)), K("07:36", (-250, -140), h=AH, state="line"), K("07:44", (-250, -140), state="charge"), K("07:50", (50, -275), h=320, state="firing"), K("07:56", (50, -275), state="line"), K("08:10", (50, -275))])

def skirmish(id, short, name, cmd, n, u, u_mil, path):
    p0, p1 = slot(C2, AH, u), slot(C1, AH, u_mil)
    unit(id, short, "american", name, cmd, "riflemen", n, [K("06:40", p0, h=AH, state="skirmish"), K("06:56", p0, state="firing"), K("07:00", p0, state="skirmish"),
         K("07:13", p0, state="retreat"), K("07:17", p1, state="firing"), K("07:23", p1, state="retreat", strength=n - 2)] + path)
skirmish("mcdowell", "McDowell", "North Carolina riflemen, skirmish line right", "Maj. Joseph McDowell", 140, 160, 210,
         [K("07:27", (-140, -320)), K("07:31", (-260, -270)), K("07:36", (-290, -170), h=AH, state="line"), K("07:44", (-290, -170), state="charge"), K("07:50", (-130, -190), h=80, state="firing"), K("07:56", (-130, -190), state="line"), K("08:10", (-130, -190))])
skirmish("cunningham", "Cunningham", "Georgia refugee riflemen, three companies", "Maj. John Cunningham", 55, -96, -150,
         [K("07:27", (260, 90)), K("07:31", (170, 230)), K("07:36", (100, 250), h=AH, state="line"), K("07:46", (100, 250), state="charge"), K("07:51", (170, 150), h=253, state="firing"), K("07:56", (170, 150), state="line"), K("08:10", (170, 150))])
skirmish("hammond", "Hammond", "South Carolina State Troops (Hammond; Capt. Joseph Pickens' company)", "Maj. Samuel Hammond", 60, 0, -190,
         [K("07:27", (290, 110)), K("07:31", (200, 250)), K("07:36", (140, 270), h=AH, state="line"), K("07:46", (140, 270), state="charge"), K("07:51", (200, 120), h=266, state="firing"), K("07:56", (200, 120), state="line"), K("08:10", (200, 120))])

unit("washington", "Washington", "american", "3rd Continental Light Dragoons", "Lt. Col. William Washington", "cavalry", 82, [
    K("06:40", (40, 100), h=AH, state="line"), K("07:08", (40, 100), state="retreat"), K("07:10", (-10, 125), h=AH, state="line"),  # a 3-pdr round finds the first position; they move into the trees
    K("07:24", (-10, 125), state="charge"), K("07:28", (190, 130), strength=80), K("07:32", (150, 110), h=AH, state="line"),
    K("07:47", (150, 110), h=230, state="charge"), K("07:50", (80, 150)), K("07:53", (20, 110)), K("07:56", (-40, 60)), K("08:00", (60, -50), h=125),
    K("08:01", (60, -50), state="charge"), K("08:05", (330, -150), strength=79), K("08:10", (600, -215))])
unit("mccall", "McCall & Jolly", "american", "South Carolina State dragoons and mounted militia (McCall, Jolly, NC and VA state dragoons)", "Maj. James McCall", "cavalry", 100, [
    K("06:40", (30, 170), h=AH, state="line"), K("07:25", (30, 170), state="charge"), K("07:29", (220, 170)), K("07:34", (180, 150), h=AH, state="line"),
    K("07:40", (180, 150), h=250, state="retreat"), K("07:45", (-230, -110)), K("07:49", (-230, -110), h=330, state="charge"), K("07:52", (-70, -260)), K("07:56", (10, -240), h=330, state="line"), K("08:10", (10, -240))])

# ---------------- British ----------------
def brit(id, short, name, cmd, type, n, s_col, u, back, keys, **extra):
    base = [K("06:40", road_se(s_col), h=BH, state="column"), K("07:00", road_se(max(0, s_col - 250))), K("07:12", slot(CB, BHB, u, back), h=BHB, state="line")]
    unit(id, short, "british", name, cmd, type, n, base + keys, **extra)
def line_unit(id, short, name, cmd, type, n, s_col, u, hits):   # the three infantry units and both guns follow this script
    a, b, c, d = hits
    return brit(id, short, name, cmd, type, n, s_col, u, 0, [
        K("07:14", slot(CB, BHB, u)), K("07:21", slot(CL, BH, u), h=BH, strength=n - a), K("07:24", slot(CL, BH, u), strength=n - a - b),
        K("07:29", slot(CM, BH, u), state="firing"), K("07:41", slot(CM, BH, u), state="charge", strength=n - a - b - c),
        K("07:46", slot(CS, BH, u), state="rout", strength=n - a - b - c - d), K("07:50", slot(CS, BH, u, 25), state="surrender"), K("08:10", slot(CS, BH, u, 25))])
line_unit("lightinf", "Light infantry", "Light infantry companies (16th Foot, Prince of Wales's American Regt, and others)", "", "light_infantry", 100, 350, 75, (0, 10, 10, 20))
line_unit("legioninf", "Legion infantry", "British Legion infantry", "Lt. Col. Banastre Tarleton", "infantry", 200, 400, 0, (0, 15, 20, 45))
line_unit("fusiliers", "7th Foot", "7th Regiment of Foot (Royal Fusiliers), mostly recruits", "Maj. Timothy Newmarsh", "infantry", 177, 460, -90, (0, 17, 20, 40))
for gid, s_col, u in (("gun1", 505, 37), ("gun2", 520, -45)):
    brit(gid, "3-pdr", "Royal Artillery, 3-pounder 'grasshopper'", "Royal Artillery detachment", "artillery", 12, s_col, u, 0, [
        K("07:05", slot(CB, BHB, u), state="firing"), K("07:14", slot(CB, BHB, u)), K("07:21", slot(CL, BH, u), h=BH), K("07:29", slot(CM, BH, u)),
        K("07:41", slot(CM, BH, u)), K("07:46", slot(CS, BH, u, 30)), K("07:47", slot(CS, BH, u, 30), state="surrender", strength=4), K("08:10", slot(CS, BH, u, 30))], guns=1)
brit("ld17", "17th Light Dragoons", "17th Light Dragoons, one troop (right flank)", "", "cavalry", 50, 330, 130, 0, [
    K("07:14", slot(CB, BHB, 130)), K("07:21", slot(CL, BH, 130), h=BH), K("07:23", slot(CL, BH, 130), state="charge"), K("07:27", (240, 120)),
    K("07:28", (240, 120), h=120, state="rout", strength=32), K("07:33", (420, 60)), K("07:40", (520, -120), state="retreat"), K("07:50", (520, -150), h=BHB, state="line"), K("07:57", (520, -150), state="hidden")])
brit("ogilvie", "Ogilvie", "British Legion dragoons, Ogilvie's troop (left flank)", "Capt. David Ogilvie", "cavalry", 50, 300, -145, 0, [
    K("06:52", road_se(300), state="charge"), K("06:57", (335, -155)), K("06:59", (335, -155), h=120, state="retreat", strength=42), K("07:03", (520, -230)), K("07:12", slot(CB, BHB, -145), h=BHB, state="line"),
    K("07:14", slot(CB, BHB, -145)), K("07:21", slot(CL, BH, -145), h=BH), K("07:29", slot(CM, BH, -145, 50)), K("07:41", slot(CM, BH, -145, 50)),
    K("07:48", slot(CM, BH, -145, 50), h=120, state="retreat"), K("07:54", (520, -330), state="rout"), K("08:00", (990, -268)), K("08:01", (990, -268), state="hidden")])
brit("highlanders", "71st Highlanders", "1st Battalion, 71st Regiment of Foot (Fraser's Highlanders)", "Maj. Archibald McArthur", "infantry", 334, 560, -110, 137, [
    K("07:14", slot(CB, BHB, -110, 137)), K("07:21", slot(CL, BH, -110, 137), h=BH), K("07:40", slot(CL, BH, -110, 137), state="charge"),
    K("07:45", (-13, -194), state="firing"), K("07:50", (-13, -194), state="rout", strength=320), K("07:55", (-13, -194), state="surrender", strength=290), K("08:10", (-13, -194))])
brit("legioncav", "Legion cavalry", "British Legion dragoons, reserve", "Lt. Col. Banastre Tarleton", "cavalry", 200, 640, 0, 200, [
    K("07:14", slot(CB, BHB, 0, 200)), K("07:21", (392, -172), h=BH), K("07:52", (392, -172), h=120, state="retreat"), K("07:55", (600, -210), state="rout"), K("08:00", (990, -268)), K("08:01", (990, -268), state="hidden")])
unit("tarleton", "Tarleton", "british", "Tarleton's last charge: 14 officers and about 40 dragoons, mostly 17th Light Dragoons", "Lt. Col. Banastre Tarleton", "cavalry", 40, [
    K("07:57", (520, -150), h=BHB, state="hidden"), K("07:58", (520, -150), state="charge"), K("08:01", (60, 20)), K("08:03", (60, 20), h=115, state="retreat"),
    K("08:05", (364, -163)), K("08:09", (990, -268)), K("08:10", (990, -268), state="hidden")])
unit("baggage", "Baggage guard", "british", "Baggage guard: 100 men, 35 wagons, left on the road", "", "infantry", 100, [
    K("07:05", (980, -268), h=BH, state="hidden"), K("07:06", (980, -268), state="column"), K("08:10", (980, -268))])

events = [
    ("06:40", "Before dawn", "Morgan's three lines have stood formed since first light on the slope above the Green River Road, the Broad River six miles at their backs. Tarleton's column, on the road since three in the morning, is closing from the south-east.", [300, -150], 1300),
    ("06:52", "First contact", "Tarleton sends Ogilvie's fifty Legion dragoons up the road at the skirmishers. McDowell's and Cunningham's riflemen empty saddles and the horsemen recoil.", [330, -190], 650),
    ("07:03", "Tarleton deploys", "Light infantry on the right, Legion infantry in the centre, the 7th Foot on the left, a three-pounder in each gap and fifty dragoons on each flank. The 71st and two hundred Legion cavalry wait in reserve. The guns open fire.", [470, -230], 800),
    ("07:15", "The advance", "The British line comes up the slope at a trot. Pickens' militia have orders to fire twice at close range and then file off around the left.", [230, -120], 650),
    ("07:21", "Two volleys", "At fifty yards the militia line fires. Two-thirds of the officers in the leading companies go down. The militia withdraw as ordered, most by the left, some by the right.", [160, -70], 550),
    ("07:25", "Dragoons on the left", "The 17th Light Dragoons ride round the American left after the militia and begin cutting them down. Washington's dragoons and the sabre-armed militia horse burst out of the trees and drive them off.", [200, 110], 600),
    ("07:30", "The main line", "Howard's Continentals and the Virginians meet the British line on the forward crest. Both sides stand and fire; British balls are later found thirty feet up in the trees.", [80, -20], 500),
    ("07:40", "The Highlanders", "Tarleton sends the 71st past the marsh to turn the American right. Howard orders Wallace's company to wheel back and refuse the flank. The order is taken as a retreat, and within a minute the whole line is marching to the rear.", [-20, -140], 600),
    ("07:43", "Retreat to Washington's horse", "Morgan rides up and names the new ground, a hundred yards back. The British, sure the day is won, break ranks and rush after them.", [-20, 50], 450),
    ("07:46", "About face", "The Continentals halt, turn and fire at thirty yards. Howard calls for the bayonet. The guns are taken and men surrender where they stand.", [-20, 50], 450),
    ("07:50", "Double envelopment", "Washington's dragoons sweep into the British right and rear. McCall's horse leads Pickens' re-formed militia onto the 71st from behind, while the Virginians go at it from the front.", [0, -60], 700),
    ("07:54", "Collapse", "The 71st, cut off on three sides, lays down its arms. The 7th is broken and loses its colours. The Royal Artillery is lost to a man. Tarleton orders his two hundred reserve dragoons to charge; they ride off instead.", [20, -100], 650),
    ("07:58", "Tarleton's last charge", "With fourteen officers and forty dragoons Tarleton rides for the guns, too late. On the road he meets Washington's troopers: Washington's sword breaks at the hilt, Tarleton's pistols wound Washington's horse, and the British ride off south-east.", [200, -80], 600),
    ("08:06", "After the battle", "In about an hour Tarleton has lost 110 killed, 229 wounded and some 600 captured, with both guns and the 7th's colours. Morgan's loss is two dozen killed and about a hundred wounded. Before noon he is marching for the Broad River fords.", [150, -80], 1200),
]
battle = dict(
    id="cowpens", name="Battle of Cowpens", date="1781-01-17", dateText="17 January 1781", place="Cowpens, South Carolina",
    origin=dict(lat=35.1344, lon=-81.8140), extent=2000, start="06:40", end="08:10", sunrise="07:34", speed=10, menPerDot=5,
    terrainExaggeration=3, contourInterval=2, trees=dict(density=0.003), wind=dict(x=0.5, y=0.4),
    palette=dict(ground="#b7b18a", high="#d9d2aa", tree="rgba(70,85,45,0.45)"),
    sides=dict(american=dict(name="Americans (Morgan)", color="#1f55c4", light="#4a83e6", dark="#122c66"),
               british=dict(name="British (Tarleton)", color="#c02a1f", light="#e2584a", dark="#5e1510")),
    features=[dict(type="road", name="Green River Road", pts=ROAD),
              dict(name="Green River Road", at=[-330, 330], rot=32), dict(name="to Island Ford on the Broad River", at=[-700, 560], rot=28),
              dict(name="to Thicketty Creek and Burr's Mill", at=[800, -300], rot=-8),
              dict(name="Visitor Center and U.S. Monument", at=[-373, 251]), dict(name="W.L.I. Monument (1856)", at=[-40, -62]),
              dict(name="Hannah's Cowpens: open oak and hickory woods, no undergrowth", at=[0, 600]),
              dict(name="head of Suck Creek (boggy)", at=[280, 470]), dict(name="Maple Swamp", at=[-470, -90])],
    units=units,
    events=[dict(t=t, title=a, text=b, at=at, view=v) for t, a, b, at, v in events],
    sources=[
        "Lawrence E. Babits, <i>A Devil of a Whipping: The Battle of Cowpens</i> (UNC Press, 1998). Unit strengths and casualties follow Babits.",
        "Daniel Morgan to Nathanael Greene, 19 January 1781. <a href='https://www.battlefields.org/learn/primary-sources/obtain-compleat-victory-daniel-morgans-letter-after-battle-cowpens' target='_blank'>Transcription at the American Battlefield Trust</a>.",
        "Banastre Tarleton, <i>A History of the Campaigns of 1780 and 1781</i> (London, 1787), ch. IV: the British deployment in Tarleton's own words.",
        "Thomas J. Fleming, <i>Cowpens: 'Downright Fighting'</i> (NPS Handbook 135, 1988). <a href='https://www.gutenberg.org/files/62413/old/62413-h/62413-h.htm' target='_blank'>Project Gutenberg</a>.",
        "National Park Service, Cowpens National Battlefield: <a href='https://www.nps.gov/cowp/learn/historyculture/the-battle-of-cowpens.htm' target='_blank'>The Battle of Cowpens</a>, <a href='https://www.nps.gov/places/the-cavalry-dragoons-at-cowpens.htm' target='_blank'>The Cavalry at Cowpens</a>, <a href='https://home.nps.gov/cowp/learn/historyculture/british-units-at-the-cowpens.htm' target='_blank'>British Units</a>, park brochure and ranger scripts.",
        "American Battlefield Trust, <a href='https://www.battlefields.org/learn/maps/cowpens-january-17-1781' target='_blank'>Cowpens battle maps</a> by Steven Stanley (phases 7:00–7:40, 7:40–7:50, 7:50–8:10).",
        "Wayne Lynch and Jim Piecuch, <a href='https://allthingsliberty.com/2013/07/debating-cowpens-how-could-tarleton-lose/' target='_blank'>Debating Cowpens</a>; <a href='https://allthingsliberty.com/2025/01/morgans-victory-at-the-cowpens-brilliant-tactics-or-fortunate-volley/' target='_blank'>Morgan's Victory at the Cowpens</a>, <i>Journal of the American Revolution</i>.",
        "National Register nomination, Cowpens National Battlefield (1976): terrain, vegetation and the course of the Green River Road.",
        "Terrain: USGS 3DEP elevation, 10 m. Lines are placed on the Washington Light Infantry monument and the NPS trail waysides; the 1856 monument stands on Howard's line.",
        "What is reconstructed: every position between the recorded moments is interpolated, clock times are approximate (Morgan wrote only 'about sunrise'), and strengths follow Babits where older accounts differ.",
    ],
)
json.dump(battle, open("battles/cowpens/battle.json", "w"), indent=1)
print(len(units), "units,", len(events), "events")
