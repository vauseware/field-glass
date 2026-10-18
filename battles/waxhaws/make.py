# Builds battles/waxhaws/battle.json. Run from the repo root: python3 battles/waxhaws/make.py
# Local metres from 34.7420N 80.6262W (x east, y north), 35 m north of the 1860 obelisk over the mass grave (-5,-36).
# The 2010-11 SCDOT metal-detector survey (Butler and Brockington) put Buford's line at the grave: running east from
# the Rocky River Road for 120-220 m, facing south, right flank on the road, a rally point 50 m behind; Tarleton's
# rise is 300 yards south on the east side of the road. Numbers are Tarleton's return of 2 June 1780; the six
# company commanders are from Harris's pension study, their order on the line and their 50-man strengths are placeholders.
import json
def K(t, p, **kw): return dict(t=t, x=p[0], y=p[1], **kw)
units = []
def unit(id, short, side, name, commander, type, strength, keys, **extra):
    units.append(dict(id=id, side=side, name=name, short=short, commander=commander, type=type, strength=strength, keys=keys, **extra))
us = lambda *a, **k: unit(a[0], a[1], "american", *a[2:], **k)
br = lambda *a, **k: unit(a[0], a[1], "british", *a[2:], **k)
LINE_Y = -36

# Buford's six companies in a single rank, right flank on the road, left company (east end) breaking first.
companies = [("wallace", "Wallace", "Capt. Adam Wallace (killed)", 30, (140, -760), (50, -380), "15:12", "rally"),
             ("stokes", "Stokes", "Capt. John Stokes (23 wounds, survived)", 66, (110, -640), (38, -250), "15:10", "rally"),
             ("hord", "Hord", "Capt. Thomas Hord", 102, (80, -520), (28, -160), "15:09", "rally"),
             ("marks", "Marks", "Capt. Isaiah Marks (captured)", 138, (51, -410), (22, -120), "15:08", "rally"),
             ("lawson", "Lawson", "Capt. Claiborne Lawson (mortally wounded)", 174, (48, -370), (18, -80), "15:07", "break"),
             ("woodson", "Woodson", "Capt. Hughes Woodson (captured)", 210, (45, -330), (16, -40), "15:06", "break")]
for id, short, cmd, x, p0, p1, t_form, fate in companies:
    line = (x, LINE_Y)
    if fate == "break":
        after = [K("15:32:30", line, h=0, state="rout", strength=42), K("15:33:30", (x - 10, 10), strength=36), K("15:35", (x - 10, 10), state="surrender", strength=32)]
    else:
        after = [K("15:32:30", line, h=0, state="retreat", strength=42), K("15:33:30", (x, 14), h=180, state="line", strength=38), K("15:34:30", (x, 14), state="rout", strength=34), K("15:35:30", (x, 14), state="surrender", strength=32)]
    end = (after[-1]["x"], after[-1]["y"])
    us(id, short, f"{short}'s company, 3rd Virginia Detachment", cmd, "infantry", 50, [
        K("14:45", p0, h=350, state="column"), K("15:00", p1), K("15:02", p1, state="line"), K(t_form, line, h=180), K("15:31:45", line, state="firing"), K("15:32:15", line, state="line")] + after +
        [K("15:38", end, strength=28), K("15:45", end, strength=18), K("15:50", end, strength=15), K("16:10", end)], ranks=1)
us("reserve", "Colours and reserve", "The colours and a small reserve behind the centre", "Col. Abraham Buford; Lt. Col. Samuel Hawes", "infantry", 30, [
    K("14:45", (60, -450), h=350, state="column"), K("15:00", (32, -200)), K("15:02", (32, -200), state="line"), K("15:11", (120, 14), h=180), K("15:33", (120, 14), state="firing"),
    K("15:34", (120, 14), state="rout", strength=24), K("15:36", (120, 14), state="surrender", strength=18), K("15:45", (120, 14), strength=12), K("15:50", (120, 14), strength=10), K("16:10", (120, 14))])
us("cav", "Virginia dragoons", "Virginia light dragoons with remnants of Washington's 3rd Continental Light Dragoons", "", "cavalry", 40, [
    K("14:45", (170, -870), h=350, state="column"), K("15:00", (62, -440)), K("15:03", (62, -440), state="line"), K("15:13", (150, 30), h=180), K("15:32:30", (150, 30), h=0, state="retreat", strength=36),
    K("15:36", (25, 600), strength=34), K("15:42", (20, 1000)), K("15:43", (20, 1000), state="hidden")])
us("rearguard", "Rear guard", "Rear guard: a sergeant and four light dragoons", "Lt. Thomas Pearson", "cavalry", 5, [
    K("14:45", (200, -980), h=350, state="column"), K("15:00", (90, -560), state="line"), K("15:01", (90, -560), h=0, state="rout", strength=2), K("15:03", (90, -560), state="hidden")])
us("guns", "Buford's guns", "Two brass 6-pounders and two royals, ordered to keep marching", "Capt. John Champe Carter", "artillery", 30, [
    K("14:45", (40, -230), h=350, state="column"), K("15:00", (16, 10)), K("15:30", (18, 60)), K("15:35", (18, 60), state="surrender", strength=22), K("16:10", (18, 60))], guns=2)
us("catlett", "Catlett", "Capt-Lt Catlett's company, guarding the guns; every officer killed", "Capt-Lt Thomas Catlett (killed)", "infantry", 50, [
    K("14:45", (42, -190), h=350, state="column"), K("15:00", (18, 50)), K("15:30", (19, 100)), K("15:33", (40, 100), h=180, state="firing"), K("15:34", (40, 100), state="rout", strength=40),
    K("15:36", (40, 100), state="surrender", strength=30), K("15:45", (40, 100), strength=15), K("15:50", (40, 100), strength=12), K("16:10", (40, 100))])
us("train", "Wagon train", "Thirty wagons of stores, ammunition and a forge cart", "Obed Britt, wagon master", "infantry", 60, [
    K("14:45", (44, -150), h=350, state="column"), K("15:00", (20, 160)), K("15:30", (20, 210)), K("15:38", (20, 210), state="surrender", strength=50), K("16:10", (20, 210))])
us("bowen", "Advance guard", "Advance guard with two dozen Loyalist prisoners", "Lt. John Bowen", "infantry", 20, [
    K("14:45", (46, -110), h=350, state="column"), K("15:00", (24, 330)), K("15:30", (22, 420)), K("15:33", (40, 420), h=180, state="line"), K("15:36", (40, 420), h=0, state="rout"), K("15:42", (25, 900)), K("15:44", (25, 900), state="hidden")])

# Tarleton's 270: column up the road from the south, three prongs formed on the rise 300 yards from Buford's line.
def brit(id, short, name, cmd, type, n, t_in, t_slot, slot, h_slot, keys, **extra):
    br(id, short, name, cmd, type, n, [K(t_in, (206, -1000), h=345, state="column"), K(t_slot, slot, h=h_slot, state="line")] + keys, **extra)
brit("cochrane", "Cochrane's dragoons", "British Legion cavalry, right wing: sixty dragoons", "Maj. Charles Cochrane", "cavalry", 60, "14:45", "15:20", (230, -280), 0, [
    K("15:00", (110, -620), state="charge"), K("15:02", (90, -560)), K("15:04", (90, -560), state="line"), K("15:20", (230, -280)),
    K("15:31", (230, -280), state="charge"), K("15:32", (235, -55), strength=58), K("15:37", (200, -20)), K("15:42", (150, 10)), K("15:48", (240, 20)), K("15:52", (200, -60), h=0, state="line"), K("16:10", (200, -60))])
brit("cochraneinf", "Legion infantry", "British Legion infantry, dismounted to gall the American left", "Maj. Charles Cochrane", "light_infantry", 50, "14:55", "15:22", (265, -250), 0, [
    K("15:22", (265, -250), state="skirmish"), K("15:31", (265, -250), state="charge"), K("15:33", (255, -45), strength=48), K("15:36", (230, -20)), K("15:44", (190, 10)), K("15:52", (260, -40), h=0, state="line"), K("16:10", (260, -40))], loose=True)
brit("ld17", "17th Light Dragoons", "17th Light Dragoons detachment, the centre", "Capt. Erasmus Corbet", "cavalry", 40, "14:47", "15:18", (140, -300), 0, [
    K("15:31", (140, -300), state="charge"), K("15:32", (140, -52), strength=38), K("15:37", (120, 0)), K("15:42", (80, 30)), K("15:50", (140, -20), h=0, state="line"), K("16:10", (140, -20))])
brit("kinlock", "Kinlock's dragoons", "British Legion cavalry, the centre with the 17th", "Capt. David Kinlock", "cavalry", 40, "14:49", "15:20", (95, -300), 0, [
    K("15:31", (95, -300), state="charge"), K("15:32", (95, -52), strength=39), K("15:37", (60, -10)), K("15:43", (110, 30)), K("15:50", (90, -40), h=0, state="line"), K("16:10", (90, -40))])
brit("tarleton", "Tarleton", "Thirty chosen horse under Tarleton himself, the left, against the road and the wagons", "Lt. Col. Banastre Tarleton", "cavalry", 30, "14:51", "15:24", (15, -300), 0, [
    K("15:31", (15, -300), state="charge"), K("15:32", (20, -52), strength=29), K("15:32:10", (20, -52), state="line"), K("15:34", (20, -52), state="charge"), K("15:36", (25, 120)), K("15:40", (40, 200)),
    K("15:50", (30, 60), h=0, state="line"), K("16:10", (30, 60))])
brit("leftinf", "Legion infantry (left)", "Legion infantry with the left wing", "", "light_infantry", 20, "14:53", "15:26", (0, -330), 0, [
    K("15:31", (0, -330), state="charge"), K("15:33", (5, -60)), K("15:36", (15, 40)), K("15:44", (30, 110)), K("15:52", (10, -10), h=0, state="line"), K("16:10", (10, -10))], loose=True)
brit("gun", "3-pounder", "The 3-pounder and the stragglers, in reserve on the rise; the gun never fired", "", "artillery", 30, "15:05", "15:28", (110, -330), 0, [
    K("15:40", (110, -330)), K("15:46", (60, -150)), K("16:10", (60, -150))], guns=1)
br("flag", "Kinlock's flag", "Capt. Kinlock with the flag of truce and Tarleton's summons", "Capt. David Kinlock", "cavalry", 2, [
    K("14:46", (120, -700), h=350, state="hidden"), K("14:47", (120, -700), state="line"), K("14:50", (60, -440)), K("14:56", (60, -440), h=165, state="retreat"), K("15:00", (130, -760)), K("15:01", (130, -760), state="hidden")])

ROAD = [(306, -1387), (54, -410), (40, -200), (15, -36), (20, 215), (25, 265), (20, 1000)]
events = [
    ("14:45", "The road to Salisbury", "Buford's 350 Virginians, the last Continentals in South Carolina after the fall of Charleston, march north toward Salisbury with thirty wagons and two six-pounders. Tarleton has ridden 105 miles in 54 hours to catch them.", [60, -250], 1200),
    ("14:52", "The blood be upon your head", "Kinlock brings Tarleton's summons: surrender on the Charleston terms within the hour, or 'the blood be upon your head'. Buford keeps the flag waiting while his column marches on, then answers that he will defend himself to the last extremity. The hour of this exchange is not recorded.", [50, -450], 900),
    ("15:00", "The rear guard", "Tarleton's advance guard rides down Lieutenant Pearson's sergeant and four dragoons at the tail of the column. Pearson is cut across the face as he lies on his back.", [90, -560], 600),
    ("15:05", "Buford forms", "Buford halts in open wood east of the road and forms a single line, his right on the road, colours in the centre, a small reserve fifty yards behind. He orders the guns and wagons to keep marching. His men are to hold their fire until the cavalry is within ten yards.", [120, -40], 600),
    ("15:16", "Tarleton forms", "Three hundred yards south, on a low rise east of the road, Tarleton forms in full view and without a shot fired at him: Cochrane with sixty dragoons and the dismounted infantry on the right, Corbet and Kinlock with the 17th and the Legion in the centre, Tarleton himself with thirty chosen horse on the left, against the road and the wagons.", [120, -300], 700),
    ("15:31", "The charge", "All three prongs go in together. The Virginians hold their fire until the horses are ten yards away and fire one volley. Tarleton's horse goes down and pins him.", [120, -150], 500),
    ("15:33", "Three minutes", "The line is ridden through before a second round can be loaded. The left gives way first; part of the line rallies fifty yards back and is overrun. A flag is sent and cut down. Buford and the mounted men break away north.", [120, -30], 450),
    ("15:37", "Tarleton's quarter", "With Tarleton pinned and reported dead, his men go over the field with sabre and bayonet for a quarter of an hour. Captain Stokes takes twenty-three wounds and lives. Whether the killing after surrender was ordered is still argued; that it happened, the survivors' wounds prove.", [100, 0], 450),
    ("15:52", "The field", "113 Virginians dead, 150 too badly hurt to move, 53 prisoners, three colours, both guns and thirty wagons taken. Tarleton loses five killed and twelve wounded. 'Tarleton's quarter' becomes a Patriot war cry, repaid at Kings Mountain and Cowpens.", [60, 50], 800),
    ("16:05", "Afterward", "Neighbours bury 84 men in one pit beside the road that afternoon and 25 more the next day. The wounded go twelve miles west by wagon to the Waxhaw meeting house, where Elizabeth Jackson and her thirteen-year-old son Andrew help nurse them. The obelisk stands over the grave today.", [-5, -36], 1000),
]
battle = dict(
    id="waxhaws", name="Battle of the Waxhaws", date="1780-05-29", dateText="29 May 1780", place="Buford's Battleground, Lancaster County, South Carolina",
    origin=dict(lat=34.7420, lon=-80.6262), extent=2000, start="14:45", end="16:10", speed=5, menPerDot=2,
    terrainExaggeration=3, contourInterval=2, trees=dict(density=0.0035), wind=dict(x=0.3, y=0.6),
    palette=dict(ground="#9fb07a", high="#cbd09a", tree="rgba(50,95,45,0.5)"),
    sides=dict(american=dict(name="Virginians (Buford)", color="#1f55c4", light="#4a83e6", dark="#122c66"),
               british=dict(name="British Legion (Tarleton)", color="#c02a1f", light="#e2584a", dark="#5e1510")),
    features=[dict(type="road", name="Rocky River Road", pts=ROAD), dict(type="creek", name="drainage", pts=[(-159, -45), (-192, -97), (-260, -200), (-350, -350), (-450, -550)]),
              dict(name="Rocky River Road: the Camden to Salisbury road", at=[-150, -700], rot=75), dict(name="to Camden, 34 miles", at=[330, -960], rot=75), dict(name="to the Waxhaws and Charlotte", at=[90, 900], rot=88),
              dict(name="mass grave and 1860 obelisk", at=[-5, -62]), dict(name="Tarleton's rise", at=[160, -340]), dict(name="SC 9 junction", at=[90, 270]),
              dict(name="Waxhaw meeting house, 12 miles west", at=[-760, 60])],
    units=units,
    events=[dict(t=t, title=a, text=b, at=at, view=v) for t, a, b, at, v in events],
    outcome={"result": "British victory", "losses": [["american", "113 killed, 150 wounded too badly to move, 53 prisoners."], ["british", "5 killed, 12 wounded."]], "note": "Both guns, three colours and thirty wagons taken. Figures are Tarleton's return of 2 June 1780."},
    sources=[
        "Banastre Tarleton, <i>A History of the Campaigns of 1780 and 1781</i> (1787), and his return from Camden of 2 June 1780: 270 men, three o'clock, the three prongs, 113 killed, 150 wounded and 53 prisoners, five British killed and twelve wounded.",
        "Col. Abraham Buford's report to the Virginia Assembly, 2 June 1780 ('at half past three o'clock we was attacked in rear by the horse'; the rally within fifty yards).",
        "Dr Robert Brownfield's account (c. 1821): Pearson's rear guard, Ensign Cruit's flag, fifteen minutes of bayoneting, Captain Stokes's twenty-three wounds.",
        "SCDOT battlefield survey by Scott Butler and Brockington and Associates (2011): metal-detector evidence placing the line at the mass grave, the rally point and Tarleton's rise.",
        "C. Leon Harris, pension-file studies of the 3rd Virginia Detachment (2016, 2024): the company commanders, and the statistical analysis of survivors' wounds.",
        "Jim Piecuch, <i>The Blood Be Upon Your Head: Tarleton and the Myth of Buford's Massacre</i> (2010); Wayne Lynch, <i>Journal of the American Revolution</i> (2013); and the 2025 JAR reassessment: the debate over what happened after the volley.",
        "National Register nomination, Buford's Massacre Site (1989); Lancaster County's Liberty Trail waysides; <a href='https://www.battlefields.org/learn/revolutionary-war/battles/waxhaws' target='_blank'>American Battlefield Trust</a>.",
        "Terrain: USGS 3DEP elevation, 10 m. The obelisk, the junction and the road from the Historical Marker Database and OpenStreetMap.",
        "What is reconstructed: the order of the six companies on the line and their equal strengths; the hour of the summons; where the rear guard was caught; the duration of the killing after surrender (Tarleton 'a few minutes', Brownfield fifteen); and every position between the recorded moments.",
    ],
)
json.dump(battle, open("battles/waxhaws/battle.json", "w"), indent=1)
print(len(units), "units,", len(events), "events")
