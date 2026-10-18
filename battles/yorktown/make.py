# Builds battles/yorktown/battle.json. Run from the repo root: python3 battles/yorktown/make.py
# Local metres from 37.2290N 76.5050W (x east, y north), 450 m south of the Victory Monument (2,491). The British
# inner line, Redoubts 9 and 10, the Grand French Battery, the second parallel and the roads are traced from the
# NPS reconstructions as mapped in OpenStreetMap; the allied works are 1930s rebuilds on sites fixed by archaeology
# and the 1781-82 plans (Bauman, Hills, Fage, Gouvion). Camps follow Johnston (1881) and Ewald's plan. Hours are
# the diarists' (Washington, Gallatin, Deux-Ponts, Cornwallis, Thacher). Strengths are Johnston's regimental
# figures and the surrender return; casualties are Despard's return and Washington's diary.
import json, math
def D(day, hm): return f"1781-{9 if day >= 28 else 10:02d}-{day:02d} {hm}"
def M(day, h, m): return D(day, f"{h + m // 60:02d}:{m % 60:02d}")  # hour plus minutes that may pass 59
def K(t, p, **kw): return dict(t=t, x=p[0], y=p[1], **kw)
units = []
def unit(id, short, side, name, commander, type, strength, keys, **extra):
    units.append(dict(id=id, side=side, name=name, short=short, commander=commander, type=type, strength=strength, keys=keys, **extra))
us = lambda *a, **k: unit(a[0], a[1], "american", *a[2:], **k)
fr = lambda *a, **k: unit(a[0], a[1], "french", *a[2:], **k)
br = lambda *a, **k: unit(a[0], a[1], "british", *a[2:], **k)
GATE = (-110, 20)            # the Hampton road through the Hornwork
FIELD = (-35, -2150)         # Surrender Field
CEASE = D(17, "16:00")       # the second flag stops the firing

# ---------- British and German garrison: blocks just inside their sectors of the line, facing out ----------
def garrison(id, short, name, cmd, n, post, h, i, type="infantry", **extra):
    """In the works from the start, thinned by fire and sickness, marched out to Surrender Field on the 19th in a
    column that leaves the Hornwork gate six minutes per corps, grounds arms, and returns."""
    fld = (FIELD[0] + (i % 4) * 90 - 135, FIELD[1] - (i // 4) * 60)
    br(id, short, name, cmd, type, n, [
        K(D(28, "12:30"), post, h=h, state="line"), K(D(13, "12:00"), post, strength=round(n * 0.96)), K(D(17, "16:00"), post, strength=round(n * 0.92)),
        K(M(19, 13, 55 + i * 2), post), K(M(19, 14, i * 2), GATE, h=180, state="column"), K(M(19, 14, 30 + i * 2), fld, h=180, state="line"),
        K(M(19, 15, i), fld, state="surrender"), K(M(19, 15, 30 + i * 2), fld, h=0, state="column"),
        K(M(19, 16, i * 2), GATE), K(M(19, 16, 15 + i * 2), post, h=h, state="line")], ranks=4, **extra)
garrison("guards", "Guards", "Brigade of Foot Guards, in reserve in the town", "Brig. Gen. Charles O'Hara", 527, (-120, 420), 180, 0)
garrison("lightinf", "Light infantry", "Light Infantry Brigade, holding the Hornwork", "Lt. Col. Robert Abercrombie", 671, (-100, 140), 180, 1, type="light_infantry")
garrison("r17", "17th Foot", "17th Regiment of Foot, Yorke's brigade, the right", "Lt. Col. John Yorke", 245, (-380, 470), 280, 2)
garrison("r23", "23rd Fusiliers", "23rd Royal Welch Fusiliers, less the company in the Fusiliers' Redoubt", "", 200, (-330, 410), 260, 3)
garrison("r33", "33rd Foot", "33rd Regiment of Foot, in the works facing the river", "", 260, (-250, 600), 330, 4)
garrison("r71", "71st Highlanders", "2nd Battalion, 71st (Fraser's Highlanders), less the redoubt garrisons", "", 200, (-200, 290), 250, 5)
garrison("erbprinz", "Erbprinz", "Hessian Regiment Erbprinz (Prince Hereditary)", "Lt. Col. von Fuchs", 484, (-170, 190), 200, 6)
garrison("ansbach1", "Ansbach", "1st Ansbach-Bayreuth Regiment, the centre", "Col. von Voigt", 540, (0, 115), 180, 7)
garrison("ansbach2", "Bayreuth", "2nd Ansbach-Bayreuth Regiment, the centre", "Col. von Seybothen", 537, (150, 135), 170, 8)
garrison("bose", "von Bose", "Hessian Regiment von Bose, in the works facing the river", "", 349, (150, 520), 10, 9)
garrison("r43", "43rd Foot", "43rd Regiment of Foot, Dundas's brigade, the left", "Lt. Col. Thomas Dundas", 359, (280, 175), 150, 10)
garrison("r76", "76th Foot", "76th Regiment of Foot (Macdonald's Highlanders), the left", "", 715, (330, 260), 120, 11)
garrison("r80", "80th Foot", "80th Regiment of Foot, the part at York", "", 300, (300, 340), 80, 12)
garrison("sailors", "Seamen", "Seamen and marines from the Charon, Guadeloupe and transports, serving the water batteries", "Capt. Thomas Symonds RN", 800, (-120, 620), 0, 13)
# Artillery in the works. Sporadic fire from 30 Sept (300 shots a day), nearly silenced after 10 Oct.
def bbat(id, short, name, pos, h, guns):
    br(id, short, name, "Capt. George Rochfort RA", "artillery", guns * 12, [
        K(D(28, "12:30"), pos, h=h, state="line"), K(D(30, "08:00"), pos, state="firing", fire=0.5), K(D(10, "08:00"), pos, state="firing", fire=0.15),
        K(CEASE, pos, state="line"), K(D(19, "12:00"), pos, state="surrender")], guns=guns)
bbat("bat4", "Battery 4", "Battery No. 4: five 18-pounders over the Williamsburg road", (-250, 300), 230, 5)
bbat("horn", "Hornwork guns", "The Hornwork (Battery No. 5), astride the Hampton road", (-100, 65), 180, 4)
bbat("bat67", "Battery 6", "Batteries 6 and 7 beside Redoubt 6", (80, 60), 180, 6)
bbat("bat8", "Battery 8", "Battery No. 8 by Redoubt 7, bearing on the American approaches", (300, 110), 150, 6)
bbat("wb1", "Water battery 1", "Water battery No. 1: twenty-six iron 12-pounders from the ships, on the bluff", (-180, 690), 0, 6)
bbat("wb2", "Water battery 2", "Water battery No. 2, where the Victory Monument stands", (10, 560), 10, 6)
# Outer works, held until the night of 29 Sept, then the advanced posts.
br("pickets", "Pigeon Hill pickets", "Ansbach pickets in the Pigeon Quarter redoubts and the Hampton road field work", "", "infantry", 300, [
    K(D(28, "12:30"), (-690, -680), h=240, state="line"), K(D(29, "10:00"), (-690, -680), state="skirmish"), K(D(29, "10:45"), (-690, -680), state="line", strength=297),
    K(D(29, "22:55"), (-690, -680)), K(D(29, "23:00"), (-690, -680), h=40, state="column"), K(D(29, "23:40"), (-250, 200)), K(D(29, "23:41"), (-250, 200), state="hidden")], ranks=2)
br("fusiliers", "Fusiliers' Redoubt", "Fusiliers' Redoubt: about 120 of the 23rd and marines, on the bluff beyond Yorktown Creek", "Capt. Apthorpe", "infantry", 120, [
    K(D(28, "12:30"), (-1100, 985), h=250, state="line"), K(D(30, "09:20"), (-1100, 985), state="firing"), K(D(30, "10:00"), (-1100, 985), state="line", strength=117),
    K(D(9, "15:00"), (-1100, 985), strength=110), K(D(17, "16:00"), (-1100, 985), strength=100), K(D(19, "12:00"), (-1100, 985), state="surrender")], ranks=2)
br("r9", "McPherson", "Redoubt No. 9: about 120 British and Hessians", "Lt. Col. Duncan McPherson, 71st", "infantry", 120, [
    K(D(28, "12:30"), (513, -158), h=200, state="line"), K(D(13, "12:00"), (513, -158), strength=112), K(D(14, "20:05"), (513, -158), state="firing"),
    K(D(14, "20:22"), (513, -158), state="surrender", strength=42), K(D(15, "07:00"), (513, -158), state="hidden")], ranks=2)
br("r10", "Campbell", "Redoubt No. 10: about 70 British and Germans, by the river", "Maj. James Campbell, 71st", "infantry", 70, [
    K(D(28, "12:30"), (670, 27), h=200, state="line"), K(D(13, "12:00"), (670, 27), strength=66), K(D(14, "20:03"), (670, 27), state="firing"),
    K(D(14, "20:12"), (670, 27), state="surrender", strength=17), K(D(15, "07:00"), (670, 27), state="hidden")], ranks=2)
br("tarleton", "Tarleton", "British Legion and 17th Light Dragoons, then the Gloucester cavalry", "Lt. Col. Banastre Tarleton", "cavalry", 280, [
    K(D(28, "12:30"), (1550, -820), h=200, state="line"), K(D(28, "13:15"), (1550, -820), state="skirmish"), K(D(28, "13:45"), (1550, -820), state="line"),
    K(D(28, "15:40"), (1550, -820)), K(D(28, "15:45"), (1550, -820), h=300, state="column"), K(D(28, "16:15"), (900, -500)), K(D(28, "16:45"), GATE), K(D(28, "17:00"), (230, 420), h=90, state="line"),
    K(D(2, "22:00"), (230, 420), state="column"), K(D(2, "22:20"), (-60, 650)), K(D(2, "22:30"), (-60, 650), state="hidden"), K(D(3, "00:30"), (300, 1650), h=0, state="line"),
    K(D(3, "00:50"), (420, 2420)), K(D(3, "09:00"), (420, 2420), state="column"), K(D(3, "09:15"), (420, 2900)), K(D(3, "09:16"), (420, 2900), state="hidden"),
    K(D(3, "14:30"), (420, 2900), state="column"), K(D(3, "14:45"), (420, 2420), h=0, state="line", strength=268), K(D(19, "15:00"), (420, 2420), state="surrender")])
br("gloucester", "Gloucester garrison", "Gloucester Point: Queen's Rangers, the Legion infantry, part of the 80th, Ewald's jägers and seamen", "Lt. Col. Thomas Dundas; Lt. Col. John Graves Simcoe", "infantry", 620, [
    K(D(28, "12:30"), (700, 2400), h=0, state="line"), K(D(3, "06:00"), (700, 2400), state="column"), K(D(3, "06:15"), (700, 2900)), K(D(3, "06:16"), (700, 2900), state="hidden"),
    K(D(3, "13:30"), (700, 2900), state="column"), K(D(3, "13:45"), (700, 2400), h=0, state="line", strength=600), K(D(19, "15:00"), (700, 2400), state="surrender")], ranks=4)

# ---------- The allied armies: the march in on 28 Sept, camps, the trenches, the lines of the 19th ----------
AM_IN, FR_IN, MIL_IN = (-2650, -1500), (-2650, 560), (900, -2990)
def camp(side, id, short, name, cmd, n, pos, h, enter, t_in, t_camp, extra_keys=(), lineY=None, **extra):
    """March in on the 28th, camp, and on the 19th stand along the Hampton road: Americans east of it, French west."""
    hd = math.degrees(math.atan2(pos[0] - enter[0], pos[1] - enter[1])) % 360  # a unit is hidden before its first key
    keys = [K(t_in, enter, h=hd, state="column"), K(t_camp, pos, h=h, state="line")] + list(extra_keys)
    if lineY is not None:
        side_x, side_h = ((-55, 270) if side is us else (-185, 90))
        last = (keys[-1]["x"], keys[-1]["y"])  # the 19th starts from wherever the unit last stood
        keys += [K(D(19, "11:30"), last, state="column"), K(D(19, "12:15"), (side_x, lineY), h=side_h, state="line"), K(D(19, "16:00"), (side_x, lineY), state="column"), K(D(19, "16:45"), last, h=h, state="line")]
    side(id, short, name, cmd, "infantry", n, keys, ranks=8, **extra)
# Americans: Lafayette's light division on the right east of the Hampton road, Lincoln's toward Wormley Creek,
# Steuben's on the left by Beaverdam Creek, militia behind.
camp(us, "muhlenberg", "Muhlenberg", "Muhlenberg's brigade of light infantry: Vose's, Gimat's and Barber's battalions", "Brig. Gen. Peter Muhlenberg", 600, (600, -1550), 0, AM_IN, D(28, "13:00"), D(28, "13:50"),
     [K(D(30, "08:30"), (600, -1550), state="column"), K(D(30, "09:00"), (200, -560), h=0, state="line"), K(D(1, "18:00"), (200, -560), state="column"), K(D(1, "18:40"), (600, -1550), h=0, state="line")], -1000)
camp(us, "hazen", "Hazen", "Hazen's brigade of light infantry: Hamilton's and Laurens's battalions and the 2nd Canadian Regiment", "Brig. Gen. Moses Hazen", 800, (870, -1620), 0, AM_IN, D(28, "13:10"), D(28, "14:00"), lineY=-1180)
camp(us, "clinton", "Clinton", "Clinton's brigade: 1st and 2nd New York", "Brig. Gen. James Clinton", 675, (-750, -1250), 0, AM_IN, D(28, "13:20"), D(28, "13:50"),
     [K(D(29, "14:30"), (-750, -1250), state="column"), K(D(29, "15:00"), (1150, -1250), h=0, state="line")], -1360)
camp(us, "dayton", "Dayton", "Dayton's brigade: 1st and 2nd New Jersey, 1st Rhode Island", "Col. Elias Dayton", 1050, (-750, -1650), 0, AM_IN, D(28, "13:30"), D(28, "14:00"),
     [K(D(29, "14:40"), (-750, -1650), state="column"), K(D(29, "15:10"), (1380, -1380), h=0, state="line")], -1540)
camp(us, "wayne", "Wayne", "Wayne's brigade: 1st and 2nd Pennsylvania, Gaskins's Virginians", "Brig. Gen. Anthony Wayne", 900, (-380, -1420), 0, AM_IN, D(28, "13:40"), D(28, "14:10"), lineY=-1720)
camp(us, "gist", "Gist", "Gist's brigade: 3rd and 4th Maryland, the Delaware recruits", "Brig. Gen. Mordecai Gist", 1060, (120, -1500), 0, AM_IN, D(28, "13:50"), D(28, "14:30"), lineY=-1900)
camp(us, "lawson", "Lawson's militia", "Lawson's brigade of Virginia militia", "Brig. Gen. Robert Lawson", 750, (900, -2020), 0, MIL_IN, D(28, "14:00"), D(28, "14:40"), lineY=-2080)
camp(us, "stevens", "Stevens's militia", "Stevens's brigade of Virginia militia", "Brig. Gen. Edward Stevens", 750, (1180, -2080), 0, MIL_IN, D(28, "14:15"), D(28, "14:55"))
us("riflemen", "Riflemen", "Lewis's Virginia riflemen and Parr's Pennsylvania riflemen, the van", "Col. Lewis; Maj. James Parr", "riflemen", 200, [
    K(D(28, "12:35"), AM_IN, h=90, state="column"), K(D(28, "13:15"), (-600, -900), h=20, state="skirmish"), K(D(28, "14:30"), (-600, -900), state="line"),
    K(D(29, "09:30"), (-600, -900)), K(D(29, "10:00"), (-450, -620), state="skirmish"), K(D(29, "10:45"), (-450, -620), state="line", strength=197), K(D(30, "08:30"), (-450, -620), state="column"),
    K(D(30, "08:50"), (-150, -480), h=0, state="line"), K(D(6, "19:00"), (-150, -480), state="column"), K(D(6, "19:30"), (450, -1850), h=0, state="line")], loose=True)
us("moylan", "Moylan", "Moylan's 4th Continental Light Dragoons and Armand's Legion", "Col. Stephen Moylan", "cavalry", 150, [
    K(D(28, "12:35"), AM_IN, h=90, state="column"), K(D(28, "13:20"), (300, -1250), h=0, state="line"), K(D(28, "14:30"), (300, -1950))])
us("sappers", "Sappers and miners", "The corps of sappers and miners, about fifty", "Capt. James Gilliland", "light_infantry", 50, [
    K(D(28, "13:30"), AM_IN, h=90, state="column"), K(D(28, "14:20"), (750, -1780), h=0, state="line")])
# The division on duty in the trenches: relieved every twenty-four hours, so one block stands for whichever
# division's turn it is. 1,500 Americans and two French regiments dug the first parallel on the night of 6 Oct.
us("amtrench", "American trench guard", "The American division on duty in the trenches (relieved every 24 hours: Lincoln, Lafayette, Steuben in turn)", "Maj. Gen. Benjamin Lincoln, then by rotation", "infantry", 1500, [
    K(D(6, "19:30"), (600, -1000), h=0, state="hidden"), K(D(6, "20:00"), (600, -1000), state="column"), K(D(6, "20:40"), (560, -708), h=0, state="line"),
    K(D(11, "20:00"), (560, -708), state="column"), K(D(11, "20:40"), (240, -405), h=0, state="line", strength=1480), K(D(14, "22:00"), (240, -405), strength=1470),
    K(D(19, "11:30"), (240, -405)), K(D(19, "12:00"), (240, -405), state="column"), K(D(19, "12:20"), (300, 100), h=180, state="line")], ranks=3)
us("how10", "Howitzers", "Two howitzers in Redoubt 10, opened the afternoon of the 15th; two 18-pounders joined them on the 17th", "", "artillery", 24, [
    K(D(15, "16:00"), (690, 40), h=220, state="hidden"), K(D(15, "16:01"), (690, 40), state="line"), K(D(15, "17:00"), (690, 40), state="firing"), K(CEASE, (690, 40), state="line")], guns=2)
us("amgrand", "Grand American Battery", "The Grand American Battery: six 18- and 24-pounders, two howitzers, four 10-inch mortars. Washington fired the first gun.", "Brig. Gen. Henry Knox; Col. John Lamb", "artillery", 72, [
    K(D(8, "06:00"), (900, -540), h=340, state="hidden"), K(D(8, "06:01"), (900, -540), state="line"), K(D(9, "17:00"), (900, -540), state="firing"), K(CEASE, (900, -540), state="line")], guns=6)
us("machin", "Machin's battery", "Machin's battery: four 18-pounders and two mortars, with four more 10-inch mortars beside it", "Capt. Thomas Machin", "artillery", 48, [
    K(D(9, "06:00"), (450, -705), h=350, state="hidden"), K(D(9, "06:01"), (450, -705), state="line"), K(D(10, "06:30"), (450, -705), state="firing"), K(CEASE, (450, -705), state="line")], guns=4)
us("am2nd", "American Battery 2", "American Battery No. 2 beside Redoubt 9: four 18-pounders opened on the 17th; the rest of its thirty-two pieces were still mounting at the capitulation", "Col. John Lamb", "artillery", 60, [
    K(D(15, "06:00"), (465, -245), h=0, state="hidden"), K(D(15, "06:01"), (465, -245), state="line"), K(D(17, "07:00"), (465, -245), state="firing"), K(CEASE, (465, -245), state="line")], guns=5)
us("hamilton", "Hamilton", "The storming party for Redoubt 10: Gimat's and Hamilton's battalions, Mansfield's forlorn hope, the sappers", "Lt. Col. Alexander Hamilton", "light_infantry", 320, [
    K(D(14, "19:50"), (560, -250), h=30, state="column"), K(D(14, "20:00"), (580, -200), state="charge"), K(D(14, "20:08"), (660, 5)),
    K(D(14, "20:10"), (665, 15), h=200, state="line", strength=290), K(D(19, "11:00"), (665, 15))])
us("laurens", "Laurens", "Laurens's eighty men, round the back of Redoubt 10 to cut off the garrison", "Lt. Col. John Laurens", "light_infantry", 80, [
    K(D(14, "19:50"), (520, -230), h=30, state="column"), K(D(14, "20:00"), (540, -200), state="charge"), K(D(14, "20:09"), (640, 110)),
    K(D(14, "20:12"), (650, 95), h=180, state="line", strength=72), K(D(15, "06:30"), (650, 95)), K(D(15, "07:00"), (620, 60)), K(D(19, "11:00"), (620, 60))], loose=True)
# French: Saint-Simon's division on the left reaching the river, Rochambeau's brigades between them and Beaverdam Creek.
camp(fr, "saintonge", "Saintonge", "Régiment de Saintonge, Soissonnais brigade", "Col. Comte de Custine", 900, (-1950, -1450), 45, FR_IN, D(28, "13:00"), D(28, "13:40"), lineY=-1000)
camp(fr, "soissonnais", "Soissonnais", "Régiment de Soissonnais, Soissonnais brigade", "Col. Comte de Saint-Maisme", 900, (-1950, -1100), 45, FR_IN, D(28, "13:10"), D(28, "13:45"), lineY=-1180)
camp(fr, "bourbonnais", "Bourbonnais", "Régiment de Bourbonnais, Bourbonnais brigade; its grenadiers took the Pigeon Quarter redoubts on the 30th", "Col. Marquis de Laval", 900, (-1800, -650), 60, FR_IN, D(28, "13:20"), D(28, "13:50"),
     [K(D(30, "08:30"), (-1800, -650), state="column"), K(D(30, "09:00"), (-1050, -620), h=60, state="line")], -1360)
camp(fr, "deuxponts", "Royal Deux-Ponts", "Régiment Royal Deux-Ponts, Bourbonnais brigade", "Col. Comte Christian de Deux-Ponts", 900, (-1800, -250), 60, FR_IN, D(28, "13:30"), D(28, "13:55"), lineY=-1540)
camp(fr, "agenais", "Agenais", "Régiment d'Agenais, Saint-Simon's division", "Col. Comte d'Autichamp", 900, (-1950, 150), 60, FR_IN, D(28, "13:40"), D(28, "14:00"), lineY=-1720)
camp(fr, "gatinais", "Gâtinais", "Régiment de Gâtinais, Saint-Simon's division", "Col. Marquis de Rostaing", 900, (-2000, 500), 60, FR_IN, D(28, "13:50"), D(28, "14:10"), lineY=-1900)
camp(fr, "touraine", "Touraine", "Régiment de Touraine, Saint-Simon's division; held the river flank opposite the Fusiliers' Redoubt", "Col. Vicomte de Pondeux", 900, (-1900, 850), 60, FR_IN, D(28, "14:00"), D(28, "14:20"),
     [K(D(6, "19:30"), (-1900, 850), state="column"), K(D(6, "20:10"), (-1500, 830), h=60, state="firing"), K(D(6, "22:00"), (-1500, 830), state="line", strength=890)], -2080)
fr("volunteers", "Saint-Simon's volunteers", "The Volunteers of Saint-Simon, chasseurs; drove in the pickets before the Fusiliers' Redoubt on the 30th and were repulsed", "", "light_infantry", 300, [
    K(D(28, "12:35"), FR_IN, h=90, state="column"), K(D(28, "13:30"), (-1700, 950), h=60, state="line"),
    K(D(30, "09:00"), (-1700, 950), state="column"), K(D(30, "09:20"), (-1330, 960), h=70, state="skirmish"), K(D(30, "10:00"), (-1330, 960), state="retreat", strength=290), K(D(30, "10:20"), (-1700, 950), h=60, state="line")], loose=True)
fr("frtrench", "French trench guard", "The two French regiments on duty in the trenches (relieved daily: Bourbonnais and Soissonnais, Agenais and Saintonge, Gâtinais and Deux-Ponts in turn)", "Baron de Viomenil, Chastellux and Saint-Simon in turn", "infantry", 1500, [
    K(D(6, "19:30"), (-100, -950), h=10, state="hidden"), K(D(6, "20:00"), (-100, -950), state="column"), K(D(6, "20:40"), (-80, -595), h=10, state="line"),
    K(D(11, "20:00"), (-80, -595), state="column"), K(D(11, "20:40"), (-130, -330), h=5, state="line", strength=1470), K(D(16, "04:08"), (-130, -330), state="charge"),
    K(D(16, "04:18"), (-40, -400), strength=1460), K(D(16, "04:32"), (-130, -330), h=5, state="line"), K(D(19, "11:30"), (-130, -330)), K(D(19, "12:00"), (-130, -330), state="column"), K(D(19, "12:20"), (380, 230), h=120, state="line")], ranks=3)
def fbat(id, short, name, pos, h, guns, built, opened):
    fr(id, short, name, "Col. François-Marie d'Aboville", "artillery", guns * 12, [K(built, pos, h=h, state="hidden"), K(built[:-5] + "06:01", pos, state="line"), K(opened, pos, state="firing"), K(CEASE, pos, state="line")], guns=guns)
fbat("frleft", "Touraine battery", "The French left battery opposite the Fusiliers' Redoubt: four guns, six mortars and howitzers. The first allied guns to open, at three in the afternoon of the 9th.", (-1400, 830), 60, 4, D(8, "06:00"), D(9, "15:00"))
fbat("gfb", "Grand French Battery", "The Grand French Battery: sixteen 18- and 24-pounders and howitzers astride the Hampton road, with a bomb battery of six 13-inch mortars", (28, -663), 0, 6, D(9, "06:00"), D(10, "06:30"))
fbat("fr34", "French batteries 3 and 4", "Two batteries of three 24-pounders on the left of the parallel", (-200, -520), 10, 6, D(10, "06:00"), D(11, "10:00"))
fbat("fr6", "French battery 6", "Battery No. 6 in front of the second parallel, between the communications: the target of the sortie", (60, -430), 0, 6, D(15, "06:00"), D(16, "12:00"))
fbat("fr2nd", "French second-parallel batteries", "Three batteries of sixteen 18- and 24-pounders in the second parallel, and ten 13-inch mortars", (150, -385), 0, 6, D(15, "06:00"), D(16, "06:30"))
fr("frpark", "French artillery park", "The French artillery park, where the siege train was assembled and carriages repaired", "Col. d'Aboville", "artillery", 72, [
    K(D(28, "15:00"), FR_IN, h=90, state="column"), K(D(28, "16:00"), (-1975, -2325), h=45, state="line")], guns=6)
fr("dpcolumn", "Deux-Ponts's column", "The storming party for Redoubt 9: grenadiers and chasseurs of Gâtinais and Royal Deux-Ponts, about 400", "Lt. Col. Guillaume de Deux-Ponts; Baron de L'Estrade", "light_infantry", 400, [
    K(D(14, "19:50"), (400, -360), h=30, state="column"), K(D(14, "20:00"), (420, -340), state="charge"), K(D(14, "20:05"), (495, -188), state="line"),
    K(D(14, "20:05:30"), (495, -188), state="firing", fire=0.2), K(D(14, "20:12"), (495, -188), state="charge", strength=360), K(D(14, "20:16"), (513, -160)), K(D(14, "20:22"), (513, -160), h=200, state="line", strength=308),
    K(D(19, "11:00"), (513, -160))])
fr("how9", "Howitzers", "Two howitzers in Redoubt 9, opened the afternoon of the 15th", "", "artillery", 24, [
    K(D(15, "16:00"), (535, -140), h=220, state="hidden"), K(D(15, "16:01"), (535, -140), state="line"), K(D(15, "17:00"), (535, -140), state="firing"), K(CEASE, (535, -140), state="line")], guns=2)

# ---------- The crossing to Gloucester, night of 16-17 Oct: a detachment in the boats ----------
br("crossing", "The first embarkation", "The light infantry, most of the Guards and the 23rd in sixteen boats; the first trip reached Gloucester before midnight, the storm scattered the second", "", "light_infantry", 900, [
    K(D(16, "22:00"), (-100, 140), h=0, state="hidden"), K(D(16, "22:01"), (-100, 140), state="column"), K(D(16, "22:40"), (-60, 650)), K(D(16, "23:00"), (-60, 650), state="hidden"),
    K(D(16, "23:50"), (250, 1600), h=0, state="line"), K(D(17, "09:30"), (250, 1600), state="hidden"), K(D(17, "11:00"), (-60, 650), state="column"), K(D(17, "11:40"), (-100, 140)), K(D(17, "11:41"), (-100, 140), state="hidden")])

# Defined last so it draws over the battery it attacks.
br("sortie", "Abercrombie's sortie", "The sortie of 16 Oct: about 350 Guards, grenadiers and light infantry", "Lt. Col. Robert Abercrombie", "light_infantry", 350, [
    K(D(16, "03:40"), GATE, h=180, state="hidden"), K(D(16, "03:45"), GATE, state="column"), K(D(16, "03:55"), (-40, -300), state="charge"), K(D(16, "04:02"), (20, -470)),
    K(D(16, "04:04"), (20, -470), state="firing"), K(D(16, "04:15"), (20, -470), state="retreat", strength=330), K(D(16, "04:25"), GATE), K(D(16, "04:30"), (-100, 140)), K(D(16, "04:31"), (-100, 140), state="hidden")])

# ---------- Ground ----------
BRIT_LINE = [(-436, 509), (-355, 490), (-273, 455), (-209, 399), (-198, 387), (-184, 327), (-150, 325), (-144, 307), (-129, 266), (-121, 242), (-107, 144), (-106, 119),
             (-136, 78), (-62, 57), (-66, 71), (-46, 52), (74, 33), (191, 76), (198, 112), (249, 140), (316, 161), (370, 141), (372, 146), (365, 199), (378, 236), (375, 265), (346, 298)]
FIRST_FR = [(-420, -420), (-280, -480), (-261, -499), (-217, -527), (-172, -528), (-125, -557), (-91, -586), (-44, -614), (46, -661), (110, -685), (137, -718)]
FIRST_AM = [(137, -718), (300, -722), (500, -716), (700, -712), (846, -686), (909, -656), (948, -630), (880, -483), (870, -300)]
SECOND = [(-380, -330), (-107, -295), (97, -373), (129, -390), (164, -376), (199, -394), (253, -401), (295, -412), (359, -377), (405, -330), (409, -324)]
SECOND_EXT = [(409, -324), (472, -246), (482, -236), (513, -158), (546, -151), (600, -80), (670, 27), (700, 70)]
HAMPTON = [(-110, 60), (-130, -300), (-153, -817), (-115, -1400), (-90, -1889), (-35, -2179), (0, -3050)]
WMBG_MAIN = [(-2650, 560), (-2388, 413), (-1856, -32), (-1100, -380), (-501, -590), (-350, -200), (-230, 150), (-150, 470)]
WMBG_RIVER = [(-2650, 1500), (-2000, 1300), (-1500, 1050), (-1100, 985), (-900, 780), (-700, 600), (-436, 509), (-150, 470)]
MOORE_RD = [(-130, -1150), (600, -1150), (1240, -1115), (1400, -900), (1692, -806)]
YT_CREEK = [(-470, -330), (-440, -200), (-520, -100), (-580, 0), (-680, 100), (-800, 230), (-900, 400), (-860, 560), (-880, 700)]
BEAVERDAM = [(-1620, -3050), (-1400, -2300), (-1280, -2100), (-1220, -1900), (-1120, -1700), (-1100, -1300), (-1140, -1100), (-1280, -900), (-1440, -700), (-1500, -400), (-1450, 0), (-1420, 500), (-1400, 1000)]
WORMLEY = [(1000, -1250), (1060, -1000), (1080, -800), (1110, -600), (1120, -320)]
def sq(cx, cy, s=36): return [(cx - s / 2, cy - s / 2), (cx + s / 2, cy - s / 2), (cx + s / 2, cy + s / 2), (cx - s / 2, cy + s / 2)]
def ship(cx, cy, L=48, W=14, rot=0):
    import math; c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return [(cx + c * dx - s * dy, cy + s * dx + c * dy) for dx, dy in [(-L / 2, -W / 2), (L / 2 - 6, -W / 2), (L / 2, 0), (L / 2 - 6, W / 2), (-L / 2, W / 2)]]
features = [
    dict(type="works", name="British inner line", pts=BRIT_LINE),
    dict(type="works", pts=[(-120, 10), (-110, 60), (-62, 57), (-40, 0), (-120, 10)]),
    *[dict(type="redoubt", poly=sq(*p)) for p in [(-487, 746), (-443, 557), (-355, 445), (-292, 334), (-195, 134), (44, 78), (248, 134), (381, 267)]],
    dict(type="redoubt", name="Redoubt 9", poly=sq(513, -158, 40), at=[513, -215]), dict(type="redoubt", name="Redoubt 10", poly=sq(670, 27, 34), at=[670, -30]),
    dict(type="redoubt", name="Fusiliers' Redoubt", poly=[(-1140, 1010), (-1100, 1040), (-1060, 1010), (-1070, 965), (-1130, 965)], at=[-1100, 925]),
    dict(type="redoubt", name="Pigeon Quarter redoubts (abandoned 29 Sept)", poly=sq(-747, -655, 34), at=[-700, -760]), dict(type="redoubt", poly=sq(-620, -720, 30)),
    dict(type="redoubt", name="Hampton road field work", poly=sq(-100, -470, 32), at=[-100, -430], until=D(6, "20:00")),
    dict(type="works", name="Gloucester works", pts=[(-60, 2330), (300, 2320), (700, 2300), (1100, 2290), (1300, 2310)], at=[600, 2250]),
    *[dict(type="redoubt", poly=sq(x, 2310, 30)) for x in (80, 460, 880, 1250)],
    dict(type="trench", name="First parallel, 6-7 Oct", pts=FIRST_FR, from_=D(7, "06:00"), at=[-300, -570], rot=-25),
    dict(type="trench", pts=FIRST_AM, from_=D(7, "06:00")),
    dict(type="trench", name="approach from the American camp", pts=[(750, -1400), (752, -813), (846, -686)], from_=D(7, "06:00"), at=[830, -1100], rot=90),
    dict(type="trench", name="Second parallel, 11-12 Oct", pts=SECOND, from_=D(12, "06:00"), at=[-150, -250]),
    dict(type="trench", pts=[(-130, -700), (-175, -500), (-130, -320)], from_=D(12, "06:00")), dict(type="trench", pts=[(500, -715), (430, -520), (380, -385)], from_=D(12, "06:00")),
    dict(type="trench", name="extended through the redoubts, 15 Oct", pts=SECOND_EXT, from_=D(15, "06:00"), at=[640, -120], rot=-45),
    dict(type="trench", pts=[(880, -483), (864, -450), (812, -311), (798, -267), (762, -163), (715, -158), (593, -142)], from_=D(15, "06:00")),
    dict(type="road", name="York-Hampton road (Surrender Road)", pts=HAMPTON, at=[-200, -1650], rot=85),
    dict(type="road", name="main road from Williamsburg", pts=WMBG_MAIN, at=[-1950, 120], rot=25), dict(type="road", name="river road from Williamsburg", pts=WMBG_RIVER, at=[-1800, 1230], rot=-20),
    dict(type="road", name="to Moore's mill dam and the Moore House", pts=MOORE_RD, at=[600, -1200]),
    dict(type="creek", name="Yorktown Creek", pts=YT_CREEK, at=[-760, 150], rot=-55), dict(type="creek", name="Beaverdam Creek", pts=BEAVERDAM, at=[-1180, -1500], rot=80), dict(type="creek", name="Wormley Creek", pts=WORMLEY, at=[1180, -850], rot=80),
    dict(type="ship", name="Charon, 44 guns", poly=ship(-650, 1080, rot=20), at=[-650, 1140], until=D(10, "22:00")), dict(type="ship", name="Guadeloupe", poly=ship(-480, 1090, L=40, rot=20), at=[-480, 1150], until=D(9, "18:00")),
    *[dict(type="ship", poly=ship(x, y, L=30, W=10, rot=r)) for x, y, r in [(120, 720, 30), (260, 640, 30), (380, 560, 25), (-150, 880, 20)]],
    dict(type="ship", name="sunken transports", poly=ship(500, 420, L=30, W=10, rot=30), at=[560, 470]),
    dict(type="camp", name="American camp", poly=[(-600, -1200), (1500, -1050), (1600, -1600), (1300, -2300), (-400, -2250), (-700, -1600)], at=[500, -2350]),
    dict(type="camp", name="French camp", poly=[(-2300, -2000), (-1600, -2000), (-1500, -700), (-1650, 200), (-1700, 900), (-2300, 1100)], at=[-2000, -2100]),
    dict(name="Yorktown", at=[-100, 480]), dict(name="Victory Monument (1884)", at=[2, 440]), dict(name="Nelson House", at=[-193, 600]), dict(name="the Hornwork", at=[-100, -20]),
    dict(name="Moore House", at=[1692, -850]), dict(name="Surrender Field", at=[-35, -2280]), dict(name="Gloucester Point", at=[250, 1560]),
    dict(name="Tyndall's Point", at=[206, 2360]), dict(name="Choisy's blockade: Lauzun's Legion, Weedon's militia and 800 marines, two miles north", at=[700, 2960]),
    dict(name="Washington's headquarters", at=[-2300, -2900]), dict(name="Knox's headquarters", at=[-1093, -2960]), dict(name="French artillery park", at=[-1975, -2400]), dict(name="French cemetery", at=[-1985, -2640]),
    dict(name="Pigeon Hill", at=[-800, -560]), dict(name="York River", at=[-300, 1500], rot=-30), dict(name="Wormley Creek", at=[1500, -420]), dict(name="to Williamsburg, 13 miles", at=[-2450, 650], rot=25),
    dict(name="to Hampton", at=[80, -2900], rot=85),
]
for f in features:
    if "from_" in f: f["from"] = f.pop("from_")

events = [
    (D(28, "12:30"), "The march from Williamsburg", "At five in the morning of 28 September the allied army, 8,000 Americans and 7,800 French, leaves Williamsburg. The Continentals take the right fork for the Hampton road, the French the left. About noon the van meets British pickets two miles from the works; Tarleton's cavalry trades a few cannon shots on the Moore House side and pulls back at sunset.", [-800, -600], 4500),
    (D(28, "15:30"), "The investment", "By nightfall the army lies on its arms in a half-circle from the York above the town to Wormley Creek below it: Americans on the right, French on the left, Beaverdam Creek between them. Cornwallis holds an outer line on the high ground between the creeks and the inner works around the town. He has 8,000 men, 65 guns in the works, and Clinton's promise of a relief fleet.", [-300, -800], 4500),
    (D(29, "10:00"), "Skirmishing", "The American wing shifts right and camps east of Beaverdam Creek within cannon shot; riflemen trade fire with the Ansbach pickets at Pigeon Hill. That night Cornwallis, trusting Clinton's letter that help will sail about 5 October, abandons his outer works and pulls everything inside the town line except the Fusiliers' Redoubt and Redoubts 9 and 10.", [-500, -500], 2500),
    (D(30, "08:30"), "The outer works taken", "At first light the empty redoubts are found. Bourbonnais grenadiers and Deux-Ponts chasseurs occupy the Pigeon Quarter works, Lafayette's light infantry the field work on the Hampton road. Saint-Simon's volunteers drive in the pickets before the Fusiliers' Redoubt and are thrown back. Colonel Scammell, reconnoitring, is shot after surrendering and dies at Williamsburg.", [-900, -300], 3000),
    (D(1, "08:00"), "Gabions and fascines", "For six days a third of the army cuts stakes and weaves gabions and fascines, 6,000 stakes, 2,000 fascines and 600 gabions, while the siege train comes up by ox team from Trebell's Landing on the James. The British fire three hundred shot a day and kill a man or two. On 3 October at Gloucester, Lauzun's hussars unhorse Tarleton and shut the garrison inside its lines.", [-400, -1200], 4500),
    (D(6, "20:00"), "The first parallel", "On a dark, wet night 1,500 men dig while 2,800 stand to arms. Washington strikes the first pickaxe. The Touraine regiment makes a false attack on the upper river that draws the British fire. By dawn a trench 2,000 yards long, 600 to 800 yards from the works, covers the diggers, and the enemy, Washington writes, were totally ignorant of our labour until daylight.", [100, -650], 2600),
    (D(7, "08:00"), "Batteries", "Two days to finish the parallel, its four redoubts and the batteries, and to drag in the guns. The trenches are relieved every twenty-four hours, the Americans by division, the French by two regiments at a time.", [300, -600], 2600),
    (D(9, "15:00"), "The guns open", "At three in the afternoon of 9 October the French battery on the far left opens on the Fusiliers' Redoubt and the ships. At five Washington puts the match to the first gun of the Grand American Battery on the right. By morning the British have pulled their pieces back from the embrasures.", [-600, 200], 3200),
    (D(10, "06:30"), "Bombardment", "The Grand French Battery and Machin's battery open at daylight: fifty-two allied guns and mortars by the 11th, firing round the clock. The British reply falls to six shots an hour. Cornwallis moves his headquarters from the Nelson house to a cave in the bluff. That night French hot shot sets the 44-gun Charon ablaze with two transports.", [0, -200], 2800),
    (D(11, "20:00"), "The second parallel", "Steuben's division and the Gâtinais and Deux-Ponts regiments open the second parallel 300 yards from the works, 750 yards long by morning. It cannot reach the river: Redoubts 9 and 10 stand in the way and enfilade its right. For three days the guns batter their abatis.", [100, -350], 1800),
    (D(14, "19:50"), "The night of 14 October", "Moonless. Four hundred French under Deux-Ponts form against Redoubt 9, four hundred Americans under Hamilton against Redoubt 10, muskets unloaded, bayonets fixed. Diversions are fired at the Fusiliers' Redoubt and at Gloucester. At eight o'clock six shells rise from the batteries: the signal.", [580, -150], 900),
    (D(14, "20:00"), "Redoubts 9 and 10", "Hamilton's men go through the abatis without waiting for the sappers and are over the parapet in ten minutes; Laurens's party comes round behind and takes Major Campbell. The French halt at the abatis under fire while the carpenters cut, then charge: seven minutes of fighting and the Hessians throw down their arms. Nine Americans and fifteen French are killed; the redoubts cost Cornwallis eighteen dead and seventy-three prisoners.", [590, -70], 700),
    (D(15, "06:00"), "To the river", "Overnight the parallel is dug through both redoubts to the bluff, and by evening howitzers in them fire into the town from 300 yards. Cornwallis writes to Clinton that the safety of the place is so precarious that he cannot recommend the fleet and army should run great risk to save him.", [450, -200], 1400),
    (D(16, "03:45"), "The sortie", "Before dawn on the 16th Abercrombie leads 350 Guards, grenadiers and light infantry out of the Hornwork against the junction of the parallels. They spike four French guns and two American with bayonet points and are driven out by Noailles's grenadiers crying Vive le Roi. The spikes are drilled out and the guns are firing again by noon.", [0, -380], 1200),
    (D(16, "22:00"), "The boats", "Cornwallis's last throw: sixteen boats to carry the fit men over to Gloucester, break through Choisy, and march for New York. The light infantry, most of the Guards and the 23rd cross before midnight. Then the weather changes from moderate and calm to a most violent storm of wind and rain and drives the second trip down the river.", [50, 1000], 2200),
    (D(17, "02:00"), "The storm", "At two in the morning the wind moderates. Cornwallis calls the troops back; the boats return after daybreak under fire from the batteries and the detachment is in the lines again by noon. A hundred allied pieces are now in action, the fraises are falling and breaches have begun.", [50, 800], 2200),
    (D(17, "10:00"), "The drummer", "At ten o'clock on 17 October a drummer in red mounts the Hornwork parapet and beats a parley, and an officer comes out with a flag. Cornwallis asks for twenty-four hours and commissioners to meet at Mr Moore's house. Washington gives him two hours to put his proposals in writing. The guns stop in the afternoon.", [-110, 0], 1000),
    (D(18, "12:00"), "The Moore House", "Dundas and Ross for the British, Noailles and Laurens for the allies, sit all afternoon and into the night at the Moore House. The terms are those Cornwallis's army gave Lincoln at Charleston: the garrison marches out with colours cased and the band may not play an American or French march.", [1692, -806], 1200),
    (D(19, "11:30"), "19 October 1781", "The articles are signed in the trenches at eleven. At noon two redoubts on the British left are handed over, one to Butler's Americans, one to Laval's French. The allied army forms along the Hampton road for over a mile, Americans on the east side, French on the west.", [-120, -1500], 2600),
    (D(19, "14:00"), "The world turned upside down", "At two o'clock the garrison marches out under O'Hara, Cornwallis pleading illness, drums beating a British march. O'Hara offers his sword to Rochambeau, who points him to Washington, who points him to Lincoln. In the field at the end of the road 7,247 soldiers and 840 seamen ground their arms. At three the Gloucester garrison does the same before Choisy.", [-60, -1700], 2400),
    (D(19, "16:45"), "After", "The prisoners march back into the town and set off for Winchester and Frederick two days later. The siege cost the British 156 killed and 326 wounded, the allies about 88 killed and 300 wounded. Clinton's fleet with 7,000 men sails from New York the same day and turns back at the Chesapeake. The war in America is, in effect, over.", [-100, -400], 4500),
]
PACE = {"The night of 14 October": 30, "Redoubts 9 and 10": 30, "The sortie": 60, "The world turned upside down": 60}  # chapters that play slower
battle = dict(
    id="yorktown", name="Siege of Yorktown", date="1781-09-28", dateText="28 September to 19 October 1781", place="Yorktown, Virginia",
    origin=dict(lat=37.2290, lon=-76.5050), extent=6000, start=D(28, "12:30"), end=D(19, "17:00"), speed=120, lapse=7200, menPerDot=20,
    sunrise="06:15", sunset="17:42", water=0.3, terrainExaggeration=2, contourInterval=3, trees=dict(density=0.0005, clear=[[(-700, 900), (900, 700), (900, -800), (-700, -800)]]),
    wind=dict(x=0.4, y=0.3), palette=dict(ground="#a3ac7c", high="#cfcb9a", tree="rgba(55,90,45,0.5)", water="#7f9fc0"),
    fields=[[(-200, -2050), (130, -2050), (130, -2330), (-200, -2330)]],
    view=dict(x=-100, y=-600, width=4500),
    sides=dict(american=dict(name="Americans (Washington)", color="#2a63c4", light="#5a8fe0", dark="#163a7a"),
               french=dict(name="French (Rochambeau)", color="#ece6d2", light="#f6f2e6", dark="#5a5340"),
               british=dict(name="British and Germans (Cornwallis)", color="#c9332e", light="#e06a5a", dark="#6e1b18")),
    features=features, units=units,
    events=[dict(t=t, title=a, text=b, at=at, view=v, **({'speed': PACE[a]} if a in PACE else {})) for t, a, b, at, v in events],
    outcome={"result": "Allied victory: Cornwallis surrenders", "losses": [[["american", "french"], "About 88 killed and 300 wounded."], ["british", "156 killed, 326 wounded; 7,247 soldiers and 840 seamen surrendered."]], "note": "The Gloucester garrison surrendered to Choisy the same afternoon."},
    sources=[
        "Earl Cornwallis to Sir Henry Clinton, York Town, 20 October 1781: the outer works, the sortie, the boats and the storm, the parley.",
        "George Washington's diary, 28 September to 19 October 1781 (Founders Online): the first parallel, the hours the batteries opened, the storming of the redoubts, the howitzers of the 15th.",
        "Journal of the Siege of York-town by the French General Staff (Gallatin), William and Mary 1931: the French trench rotation, battery by battery, with the daily French losses.",
        "Guillaume de Deux-Ponts, <i>My Campaigns in America</i> (1868): the assault on Redoubt 9 in his own words, and Viomenil's report.",
        "Banastre Tarleton, <i>History of the Campaigns of 1780 and 1781</i> (1787), with Despard's return of 156 killed, 326 wounded and 70 missing.",
        "Sebastian Bauman, <i>Plan of the Investment of York and Gloucester</i> (surveyed 22-28 October 1781, published 1782): the legend naming every battery and the day it opened.",
        "Henry P. Johnston, <i>The Yorktown Campaign and the Surrender of Cornwallis</i> (1881): camps, regimental strengths, the sectors of the British line, the trench rotation.",
        "Charles E. Hatch, <i>Yorktown and the Siege of 1781</i> (NPS Historical Handbook 14, 1957); NPS Historic Resource Study <i>Yorktown's Main Street</i> (the British works lot by lot).",
        "James Thacher, <i>Military Journal</i>; Ebenezer Denny, <i>Military Journal</i>; Stephan Popp's journal (Bayreuth regiment); Joseph Plumb Martin, <i>A Narrative</i>.",
        "National Park Service, Yorktown Battlefield: the reconstructed British line, Redoubts 9 and 10, the Grand French Battery and the second parallel, as mapped in OpenStreetMap. Terrain: USGS 3DEP, 10 m, with the river at sea level.",
        "What is reconstructed: the allied earthworks are 1930s rebuilds on sites fixed by archaeology; the visible British line is the 1862 Confederate rebuild over the 1781 one; Redoubts 1 to 8 are placed within about fifty metres; the French camp order by regiment is inferred from Ewald's plan; the trench guard is shown as one standing block for whichever division was on duty; the hours of the sortie (midnight to five) and the length of the fight for Redoubt 9 (seven minutes to half an hour) are given differently by every diarist.",
    ],
)
WHEN = {'The guns open': '3:00 PM', 'The storm': '2:00 AM', 'The drummer': '10:00 AM', 'The world turned upside down': '2:00 PM'}  # chapter times the sources record; the story gives the others to the nearest hour
for e in battle["events"]:
    if e["title"] in WHEN: e["when"] = WHEN[e["title"]]
json.dump(battle, open("battles/yorktown/battle.json", "w"), indent=1)
print(len(units), "units,", len(events), "events,", len(features), "features")
