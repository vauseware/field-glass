# Builds battles/kings-mountain/battle.json. Run from the repo root: python3 battles/kings-mountain/make.py
# Local metres from 35.1423N 81.3811W (x east, y north). The ridge runs N51E from the Centennial Monument
# (-218,-185; the south-west summit) to the Chronicle markers at the north-east foot (214,174). Other anchors:
# U.S. Monument (44,26), Ferguson death marker (157,84), Ferguson grave (179,45), Hambright tablet (178,125),
# headquarters ~(128,122), Hoover monument at the north-west foot (-411,-110), visitor centre (354,-117).
# Column order follows Draper (1881) and the NPS map; strengths are Draper's 910; Loyalist militia regiments
# are apportioned along the crest because no source records their postings.
import json, math
AX = 51                                   # ridge axis bearing; s = metres from the south-west summit along it
A = (math.sin(math.radians(AX)), math.cos(math.radians(AX)))
P = (A[1], -A[0])                         # unit vector to the south-east, perpendicular to the ridge
S0 = (-218, -185)
CREST = [(-60, -45), (0, -40), (50, -20), (100, 0), (350, 0), (400, 25), (450, 40), (600, 40)]  # crest offset from the axis, from the DEM
def dc(s):
    for (s1, d1), (s2, d2) in zip(CREST, CREST[1:]):
        if s <= s2: return d1 + (d2 - d1) * max(0, s - s1) / (s2 - s1)
    return CREST[-1][1]
def R(s, d):                              # point s metres along the ridge, d metres south-east of the crest line
    off = d + dc(s)
    return (round(S0[0] + s * A[0] + off * P[0]), round(S0[1] + s * A[1] + off * P[1]))
def K(t, p, **kw): return dict(t=t, x=p[0], y=p[1], **kw)
SE, NW, NE, SW = 321, 141, 51, 231        # facings: toward the crest from the south-east side, from the north-west side, along the ridge
F0 = (-650, 180)                          # where the columns dismounted, 550 yards from the summit with the camp in view
units = []
def unit(id, short, side, name, commander, type, strength, keys, **extra):
    units.append(dict(id=id, side=side, name=name, short=short, commander=commander, type=type, strength=strength, keys=keys, **extra))

# ---------------- Patriots: nine columns, open order, the two centre columns open the attack ----------------
def patriot(id, short, name, cmd, n, path, **extra):
    unit(id, short, "patriot", name, cmd, "riflemen", n, [K("14:50", (-900, 230), h=120, state="column"), K("14:58", F0)] + path, loose=True, **extra)
END = lambda p, n: [K("16:05", p, strength=n), K("16:06", p, state="line"), K("16:15", p)]
patriot("campbell", "Campbell", "Washington County, Virginia, militia", "Col. William Campbell", 200, [
    K("15:00", F0, state="column"), K("15:04", (-330, -230), state="firing"), K("15:06", R(80, 100), strength=196), K("15:08", R(80, 100), h=141, state="retreat", strength=192),
    K("15:11", R(80, 190)), K("15:13", R(80, 190), h=SE, state="skirmish"), K("15:17", R(80, 100), state="firing", strength=186), K("15:30", R(80, 100), h=141, state="rout", strength=180),
    K("15:33", R(70, 200), strength=176), K("15:35", R(70, 200), h=SE, state="skirmish"), K("15:40", R(80, 100), state="firing", strength=175), K("15:46", R(80, 100), state="charge"),
    K("15:50", R(40, 15), state="firing", strength=172)] + END(R(40, 15), 170))
patriot("shelby", "Shelby", "Sullivan County militia", "Col. Isaac Shelby", 120, [
    K("15:00", F0, state="column"), K("15:04", (-330, -60), state="firing"), K("15:06", R(60, -100), strength=118), K("15:18", R(60, -100), h=321, state="retreat", strength=115),
    K("15:21", R(60, -190)), K("15:23", R(60, -190), h=NW, state="skirmish"), K("15:27", R(60, -100), state="firing", strength=112), K("15:46", R(60, -100), state="charge"),
    K("15:50", R(50, -15), state="firing", strength=110)] + END(R(50, -15), 108))
patriot("sevier", "Sevier", "Washington County, North Carolina, militia", "Lt. Col. John Sevier", 120, [
    K("15:00", F0, state="column"), K("15:05", (-420, -230)), K("15:09", (-150, -340)), K("15:14", R(300, 100), h=SE, state="firing"), K("15:46", R(300, 100), state="charge", strength=115),
    K("15:52", R(220, 15), state="firing", strength=113)] + END(R(220, 15), 112))
patriot("mcdowell", "McDowell", "Burke County militia", "Maj. Joseph McDowell", 90, [
    K("15:00", F0, state="column"), K("15:06", (-420, -250)), K("15:10", (-100, -390)), K("15:16", R(430, 100), h=SE, state="firing"), K("15:48", R(430, 100), state="charge", strength=87),
    K("15:54", R(360, 20), state="firing", strength=86)] + END(R(360, 20), 85))
unit("winston", "Winston", "patriot", "Surry County militia (part of Cleveland's regiment), sent round to the enemy's right", "Maj. Joseph Winston", "riflemen", 60, [
    K("14:50", (-900, -450), h=100, state="column"), K("15:05", (-200, -620)), K("15:14", (280, -380)), K("15:22", R(520, 60), h=300, state="firing"), K("15:50", R(520, 60), state="charge", strength=59),
    K("15:56", R(470, 30), state="firing")] + END(R(470, 30), 58), loose=True)
patriot("williams", "Williams", "Little River District, South Carolina, with Brandon's, Hammond's and Candler's men", "Col. James Williams", 60, [
    K("15:00", F0, state="column"), K("15:04", (-330, 40)), K("15:08", R(190, -100), h=NW, state="firing"), K("15:46", R(190, -100), state="charge", strength=58),
    K("15:52", R(150, -15), state="firing", strength=57), K("16:00", R(150, -15), strength=56)] + END(R(150, -15), 56))
patriot("lacey", "Lacey", "Sumter's brigade: New Acquisition and Turkey Creek regiments (Lacey, Hawthorn, Steen)", "Col. Edward Lacey", 100, [
    K("15:00", F0, state="column"), K("15:05", (-300, 100)), K("15:11", R(320, -100), h=NW, state="firing"), K("15:48", R(320, -100), state="charge", strength=97),
    K("15:54", R(300, -20), state="firing", strength=96)] + END(R(300, -20), 96))
patriot("cleveland", "Cleveland", "Wilkes County militia", "Col. Benjamin Cleveland", 110, [
    K("15:00", F0, state="column"), K("15:06", (-250, 200)), K("15:14", (-100, 240)), K("15:20", R(460, -100), h=NW, state="firing"), K("15:50", R(460, -100), state="charge", strength=106),
    K("15:56", R(440, -30), state="firing", strength=105)] + END(R(440, -30), 104))
patriot("hambright", "Hambright & Chronicle", "Lincoln County 'South Fork' men", "Lt. Col. Frederick Hambright and Maj. William Chronicle", 50, [
    K("15:00", F0, state="column"), K("15:07", (-200, 290)), K("15:14", (100, 310)), K("15:20", R(580, -20), h=SW, state="firing"), K("15:25", R(580, -20), strength=46),
    K("15:52", R(580, -20), state="charge"), K("15:57", R(520, 0), state="firing")] + END(R(520, 0), 46))

# ---------------- Loyalists: Provincials and militia along the bare crest, compressed to the north-east end ----------------
def loyal(id, short, name, cmd, type, n, keys, **extra): unit(id, short, "loyalist", name, cmd, type, n, keys, **extra)
loyal("picket", "Main guard", "Loyalist main guard, halfway up the south-west spur", "", "militia", 20, [
    K("14:50", R(-40, 0), h=SW, state="skirmish"), K("15:00", R(-40, 0), state="firing"), K("15:03", R(-40, 0), h=NE, state="retreat", strength=14), K("15:06", R(60, 0), state="hidden")])
av = R(80, 0)
loyal("volunteers", "American Volunteers", "American Volunteers: Provincials of the King's American Regiment, New Jersey Volunteers and others", "Maj. Patrick Ferguson; Capt. Abraham DePeyster", "infantry", 100, [
    K("14:50", av, h=SW, state="line"), K("15:03", av, state="firing"), K("15:06", av, h=141, state="charge"), K("15:09", R(70, 75), strength=96), K("15:10", R(70, 75), h=321, state="retreat"),
    K("15:13", av, h=SW, state="firing"), K("15:16", av, h=321, state="charge"), K("15:19", R(60, -75), strength=92), K("15:20", R(60, -75), h=141, state="retreat"), K("15:23", av, h=SW, state="firing"),
    K("15:28", av, h=141, state="charge", strength=88), K("15:31", R(60, 85), strength=84), K("15:32", R(60, 85), h=321, state="retreat"), K("15:36", R(90, 0), h=SW, state="firing", strength=80),
    K("15:40", R(90, 0), h=NE, state="retreat", strength=75), K("15:50", R(380, 0), h=SW, state="firing", strength=60), K("16:00", R(380, 0), state="surrender", strength=55), K("16:05", R(380, 0), strength=50), K("16:15", R(380, 0))])
def militia(id, short, name, cmd, n, s, h, t_fire, t_back, pocket, losses):
    a, b, c = losses
    loyal(id, short, name, cmd, "militia", n, [K("14:50", R(s, 0), h=h, state="line"), K(t_fire, R(s, 0), state="firing"), K(t_back, R(s, 0), h=NE, state="retreat", strength=n - a),
          K(pocket[0], R(*pocket[1]), h=h, state="line"), K("16:00", R(*pocket[1]), state="surrender", strength=n - a - b), K("16:05", R(*pocket[1]), strength=n - a - b - c), K("16:15", R(*pocket[1]))])
militia("mills", "Mills", "Tryon County Loyalist militia, North Carolina", "Col. Ambrose Mills", 250, 180, SE, "15:05", "15:40", ("15:48", (400, 10)), (40, 30, 10))
militia("husbands", "Husbands", "Burke County Loyalist militia, North Carolina", "Col. Vezey Husbands", 100, 260, NW, "15:08", "15:44", ("15:50", (400, -15)), (20, 10, 5))
militia("green", "Green", "Rutherford County Loyalist militia, North Carolina", "Maj. William Green", 100, 320, SE, "15:16", "15:48", ("15:54", (415, 0)), (15, 10, 5))
militia("plummer", "Plummer", "Fair Forest Loyalist militia, South Carolina", "Maj. Daniel Plummer", 150, 390, NW, "15:20", "15:52", ("15:56", (430, 12)), (25, 15, 10))
militia("spartan", "Spartan Loyalists", "Spartan District Loyalist militia, South Carolina", "", 100, 440, SE, "15:22", "15:54", ("15:57", (430, -12)), (15, 10, 5))
militia("ninetysix", "Ninety Six Loyalists", "Ninety Six District Loyalist militia (Little River, Long Cane, Stevens Creek, Dutch Fork)", "", 100, 480, NE, "15:22", "15:55", ("15:58", (445, 0)), (15, 5, 5))
loyal("wagons", "Wagons", "Seventeen baggage wagons and their drivers, drawn across the north-east end", "", "infantry", 10, [
    K("14:50", R(500, -25), h=NE, state="column"), K("16:00", R(500, -25), state="surrender"), K("16:15", R(500, -25))])
loyal("ferguson", "Ferguson", "Ferguson with two Loyalist colonels and his mounted men, trying to cut through", "Maj. Patrick Ferguson", "cavalry", 10, [
    K("15:49", R(380, 0), h=NE, state="hidden"), K("15:50", R(380, 0), state="charge"), K("15:52", (157, 84), state="rout", strength=3), K("15:54", (157, 84), state="hidden")])

ROAD = [(-900, 250), (-650, 180), (-400, 260), (-150, 300), (100, 290), (240, 250), (400, 120), (520, -80), (620, -350), (760, -900)]
events = [
    ("14:50", "The Overmountain men arrive", "Nine hundred picked horsemen, in the saddle since eight the night before through steady rain, halt a quarter mile from the ridge. Ferguson's camp on the summit is in full view. They tie their horses and form two lines of two columns each.", [-450, 60], 1400),
    ("15:00", "Here they are, my brave boys", "Loyalist pickets fire on Shelby's column before it is in place. Campbell's Virginians and Shelby's Sullivan men open the attack on the narrow south-west end while the two wings run to circle the mountain.", [-230, -180], 700),
    ("15:06", "The bayonet", "DePeyster's Provincials charge down the south-east slope with fixed bayonets. The riflemen have none. They give way to the foot of the hill, re-form among the trees, and climb again.", [-170, -230], 550),
    ("15:16", "Shelby's turn", "A second charge comes down the north-west face at Shelby's men. They fall back and climb again as soon as the bayonets turn around.", [-240, -100], 550),
    ("15:22", "The noose closes", "Cleveland's men, delayed by a swamp, and Winston's, who lost the columns and rode hard to catch up, reach the north-east end. Chronicle falls at the head of the South Fork men. Fire is general all round the mountain.", [80, 70], 900),
    ("15:28", "The third charge", "The last charge drives the Virginians down the ridge in something close to a rout. Campbell rallies them. Attacks on the north and east slopes pull the Provincials back to the crest.", [-170, -230], 550),
    ("15:40", "Downhill fire", "From the crest the Loyalists overshoot. Musket balls fly over the heads of men climbing from tree to tree, while on the bare summit the close column of Loyalists is a fair mark for rifles. Mills' North Carolinians, out of ammunition, give way first.", [-60, -70], 600),
    ("15:46", "The summit taken", "Campbell and Shelby gain the south-west summit and hold it. The right wing comes over the crest and forces the Loyalists north-east along the ridge, where Cleveland's men stop them.", [-120, -120], 600),
    ("15:51", "Ferguson falls", "Ferguson, in a checked hunting shirt on a white horse, tries to cut through with two Loyalist colonels. He is hit by six or more balls and dragged by a stirrup. He dies within minutes.", [157, 84], 450),
    ("15:56", "Sixty yards by forty", "The Loyalists are crowded into a pocket on the north-east end among their wagons. Ferguson's silver whistle is silent. DePeyster raises his white handkerchief.", [110, 80], 450),
    ("16:00", "Buford's play", "The firing does not stop. Some men have not seen the flag; others remember Tarleton at the Waxhaws. Williams falls mortally wounded. Campbell shouts that it is murder to kill them now. A second flag ends it.", [110, 80], 450),
    ("16:08", "An hour and five minutes", "Ferguson's force is destroyed: 157 killed, 163 wounded, nearly 700 prisoners, and no one escaped. The Patriots lose 28 killed and 62 wounded. Cornwallis's march into North Carolina stops here.", [0, 0], 1100),
]
crest_poly = [R(s, w) for s, w in [(-50, 15), (0, 25), (100, 30), (250, 30), (350, 45), (450, 55), (520, 40), (570, 15)]] + [R(s, -w) for s, w in [(570, 15), (520, 40), (450, 55), (350, 45), (250, 30), (100, 30), (0, 25), (-50, 15)]]
battle = dict(
    id="kings-mountain", name="Battle of Kings Mountain", date="1780-10-07", dateText="7 October 1780", place="Kings Mountain, South Carolina",
    origin=dict(lat=35.1423, lon=-81.3811), extent=2000, start="14:50", end="16:15", speed=10, menPerDot=5,
    terrainExaggeration=1.5, contourInterval=3, trees=dict(density=0.005, clear=[crest_poly]), wind=dict(x=0.6, y=-0.3),
    palette=dict(ground="#a9a67a", high="#d3cc9f", tree="rgba(75,70,40,0.5)"),
    sides=dict(patriot=dict(name="Patriots (Campbell)", color="#1f55c4", light="#4a83e6", dark="#122c66"),
               loyalist=dict(name="Loyalists (Ferguson)", color="#c02a1f", light="#e2584a", dark="#5e1510")),
    features=[dict(type="road", name="Colonial road", pts=ROAD),
              dict(type="creek", name="Buck Hill Branch", pts=[(-189, 96), (-92, 136), (20, 160), (132, 176), (300, 225), (450, 375), (600, 525), (720, 720), (820, 900)]),
              dict(type="creek", name="stream on the south side", pts=[(90, -290), (240, -380), (375, -450), (450, -675), (525, -750), (675, -900)]),
              dict(name="Colonial road to the Ridge Road", at=[-760, 250], rot=-12), dict(name="to Yorkville", at=[720, -800], rot=75),
              dict(name="Hambright's Gap", at=[260, 300]), dict(name="Buck Hill Branch", at=[520, 470], rot=45), dict(name="Centennial Monument (1880)", at=[-250, -230]),
              dict(name="U.S. Monument (1909)", at=[44, 50]), dict(name="Ferguson fell", at=[200, 100]), dict(name="Ferguson's grave", at=[215, 30]),
              dict(name="Chronicle fell", at=[260, 190]), dict(name="Hoover monument", at=[-411, -130]), dict(name="Visitor Center", at=[354, -140]),
              dict(name="horses left here", at=[-650, 150]), dict(name="Ferguson's camp and wagons", at=[118, 126])],
    units=units,
    events=[dict(t=t, title=a, text=b, at=at, view=v) for t, a, b, at, v in events],
    outcome={"result": "Patriot victory", "losses": [["patriot", "28 killed, 62 wounded."], ["loyalist", "157 killed, 163 wounded, nearly 700 prisoners. Ferguson killed; no one escaped."]], "note": "The Patriot colonels' report gave 225 Loyalists killed and 716 prisoners."},
    sources=[
        "Lyman C. Draper, <i>King's Mountain and Its Heroes</i> (1881): column order, regimental strengths (910 men), the three bayonet charges, Ferguson's death.",
        "Official report of Cols. Campbell, Shelby and Cleveland, October 1780: 'an hour and five minutes'; Patriot loss 28 killed and 62 wounded; Loyalist return 225 killed, 163 wounded, 716 prisoners.",
        "Lt. Anthony Allaire's diary and letters (Loyalist adjutant): 70 Provincials and about 800 militia on the field, DePeyster's surrender.",
        "National Park Service, Kings Mountain National Military Park: <a href='https://www.nps.gov/kimo/' target='_blank'>park pages</a>, brochure map and battlefield trail waysides; Cultural Landscape Inventory (2010) for the summit, the slopes and the final pocket.",
        "War Department survey of the battlefield (Landers, 1925 to 1928): ridge axis N 52° E, crest width, heights above the plateau.",
        "<a href='https://allthingsliberty.com' target='_blank'>Journal of the American Revolution</a>: Wayne Lynch on Williams' death; Jim Piecuch (2024) on numbers engaged.",
        "American Battlefield Trust, <a href='https://www.battlefields.org/learn/revolutionary-war/battles/kings-mountain' target='_blank'>Kings Mountain</a>: modern casualty figures (157 killed, 163 wounded, 698 captured).",
        "Terrain: USGS 3DEP elevation, 10 m. Monument and wayside coordinates from OpenStreetMap and the Historical Marker Database; the ridge axis is measured between the Centennial Monument and the Chronicle markers.",
        "What is reconstructed: the postings and strengths of the individual Loyalist militia regiments on the crest, how far each repulse pushed the riflemen back, and every position between the recorded moments. Clock times follow the Patriot accounts ('about three o'clock'); Loyalist accounts say two.",
    ],
)
json.dump(battle, open("battles/kings-mountain/battle.json", "w"), indent=1)
print(len(units), "units,", len(events), "events")
