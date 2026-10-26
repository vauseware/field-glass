# Builds battles/belleau-wood/battle.json. Run from the repo root: python3 battles/belleau-wood/make.py
# Local metres from 49.0700N 3.2800E (x east, y north). The 7 km square holds Belleau Wood, Lucy-le-Bocage, Bouresches
# and its station, Belleau, Torcy, Bussiares, Champillon, Les Mares Farm, Hill 142 and the railway east of the wood; the
# Paris road, Vaux, Hill 204 and the brigade's rear are off its south and east edges. Anchors are OpenStreetMap points;
# the hills are read from the Copernicus surface model or placed from the sources' text, and every one placed to 200 m
# or worse is labelled "about here". The woods are OpenStreetMap's (ODbL), the wood itself the memorial park's outline.
# Clock times are French summer time, GMT+1, as the American records wrote them; German times are an hour earlier than
# Otto's, which are central European.
import json, math, re, datetime as dt
HERE = "battles/belleau-wood/"
LAT0, LON0 = 49.0700, 3.2800
KX, KY = 111320 * math.cos(math.radians(LAT0)), 111320  # tools/fetch_terrain.py's metres per degree
def M(lat, lon): return (round((lon - LON0) * KX), round((lat - LAT0) * KY))
HALF_EXTENT = 3500

# ---- terrain: chalk plateau and the Clignon's valley, no water; the page reads a zero as a gap in the survey ----
T = json.load(open(HERE + "terrain.json"))
COLS, SP = T["cols"], T["spacing"]; HALF = COLS * SP / 2
assert HALF == HALF_EXTENT, "terrain.json is not the battle's extent"
Z = [round(max(v, 0.1), 2) for v in T["z"]]
if Z != T["z"]: T["z"] = Z; json.dump(T, open(HERE + "terrain.json", "w"), separators=(",", ":"))
def z(x, y):
    c, r = int((x + HALF) / SP), int((HALF - y) / SP)
    return T["z"][r * COLS + c] if 0 <= c < COLS and 0 <= r < COLS else None
def on_land(p): return z(*p) is not None and z(*p) > 0

# ---- places ----
PLACES = {  # OpenStreetMap, and the hills the note reads from the surface model
    'lucy': (49.05731, 3.27900), 'belleau': (49.08175, 3.29349), 'mairie': (49.08554, 3.29092), 'bouresches': (49.06240, 3.30889),
    'torcy': (49.08759, 3.27973), 'champillon': (49.06680, 3.25148), 'mares': (49.07098, 3.23917), 'bussiares': (49.09161, 3.25799),
    'givry': (49.08743, 3.29796), 'licy': (49.09989, 3.27453), 'cense': (49.04787, 3.30481), 'voie': (49.05432, 3.24265),
    'flagpole': (49.07834, 3.29215), 'german_cemetery': (49.08236, 3.28319), 'h142': (49.07921, 3.26958), 'slobe': (49.06383, 3.29182),
    'waist': (49.06977, 3.28913), 'knoll_w': (49.07882, 3.26277), 'station': (49.06642, 3.30942),
}
ABOUT = {  # placed from the text, to 200 m or worse
    'brusses': (49.08804, 3.30214), 'h176': (49.07515, 3.27016), 'h126': (49.08461, 3.27164), 'h133': (49.08259, 3.28317),
    'h169': (49.07065, 3.28141), 'h181': (49.06391, 3.27908), 'pavilion': (49.07531, 3.29058), 'triangle': (49.05042, 3.29624),
}
P = {k: M(*v) for k, v in {**PLACES, **ABOUT}.items()}

# ---- lines (lat, lon) ----
ROADS_LL = {  # OpenStreetMap, simplified to 25 m
    'lucy_torcy': [(49.0569, 3.27984), (49.05834, 3.27885), (49.06094, 3.27977), (49.06502, 3.28166), (49.06769, 3.28015), (49.06948, 3.28215), (49.07116, 3.28175), (49.07178, 3.2806), (49.07607, 3.27805), (49.08139, 3.27775)],
    'lucy_bouresches': [(49.05677, 3.27986), (49.05557, 3.28232), (49.05596, 3.2845), (49.05839, 3.28971), (49.06616, 3.30976), (49.0624, 3.30854)],
    'bouresches_belleau': [(49.0624, 3.30854), (49.06616, 3.30976), (49.06733, 3.31105), (49.06999, 3.31111), (49.07418, 3.31315), (49.07665, 3.2952), (49.07734, 3.29707)],
    'torcy_belleau': [(49.08615, 3.27915), (49.08404, 3.27849), (49.08139, 3.27775), (49.08177, 3.29261)],
    'belleau_givry': [(49.08177, 3.29261), (49.08031, 3.29762), (49.07715, 3.30473), (49.07508, 3.30618), (49.07396, 3.30935), (49.07414, 3.31013), (49.07562, 3.31161), (49.0751, 3.31297), (49.07396, 3.31347), (49.0736, 3.31742), (49.07417, 3.32029), (49.0752, 3.32281), (49.07461, 3.33015)],
    'bouresches_vaux': [(49.06055, 3.31276), (49.05467, 3.3195)],
    'lucy_marigny': [(49.05715, 3.27937), (49.05705, 3.27833), (49.05786, 3.2753), (49.05789, 3.2724)],
    'champillon_torcy': [(49.0682, 3.25096), (49.07474, 3.25244), (49.07664, 3.25378), (49.08173, 3.2531), (49.08525, 3.25419)],
    'torcy_bussiares': [(49.08404, 3.27849), (49.08523, 3.27111), (49.0865, 3.26722), (49.08715, 3.26651), (49.08919, 3.26639), (49.08979, 3.26552), (49.0908, 3.26348), (49.09057, 3.26059), (49.09141, 3.25491)],
    'bussiares_licy': [(49.08957, 3.26594), (49.09239, 3.26765), (49.09666, 3.27516)],
    'torcy_licy': [(49.08973, 3.27853), (49.09542, 3.27791), (49.09717, 3.27402), (49.09876, 3.27329)],
    'lucy_south': [(49.0569, 3.27984), (49.05509, 3.27945), (49.05382, 3.27847), (49.05312, 3.27889)],
}
RAIL_LL = [(49.05399, 3.32962), (49.0549, 3.32071), (49.05608, 3.31818), (49.05718, 3.31702), (49.06104, 3.31682), (49.0643, 3.31403),  # razed, south-east of Bouresches
           (49.06527, 3.31232), (49.06616, 3.30976), (49.0669, 3.30893),  # the station
           (49.07371, 3.31), (49.07633, 3.30748), (49.07815, 3.3073),  # east of the wood
           (49.07926, 3.30694), (49.08327, 3.30324), (49.08519, 3.30406), (49.08624, 3.30355), (49.08652, 3.30183), (49.08563, 3.298), (49.08582, 3.29414), (49.08803, 3.28876), (49.08992, 3.28256), (49.09399, 3.28033), (49.09569, 3.27869)]
CLIGNON_LL = [(49.09693, 3.27606), (49.0959, 3.27931), (49.0901, 3.28029), (49.0889, 3.28175), (49.08656, 3.29085), (49.08593, 3.29137), (49.08548, 3.29254), (49.0856, 3.29517), (49.08557, 3.29602), (49.08546, 3.29818), (49.08631, 3.30198)]
CORNU_LL = [(49.08661, 3.30391), (49.0875, 3.30412), (49.08977, 3.3117), (49.08889, 3.31972), (49.08945, 3.32253), (49.08935, 3.32415)]
WOODS_LL = {  # OpenStreetMap ways (ODbL), simplified to 15 m
    'rochette': [(49.05879, 3.3209), (49.05931, 3.31948), (49.0588, 3.31867), (49.05712, 3.31811), (49.05652, 3.31722), (49.05694, 3.31665), (49.05721, 3.31691), (49.0606, 3.31706), (49.06002, 3.3175), (49.05963, 3.31899), (49.06044, 3.31968), (49.06107, 3.31961), (49.06051, 3.31775), (49.06117, 3.31697), (49.06128, 3.31755), (49.06209, 3.31681), (49.06278, 3.31938), (49.06345, 3.31914), (49.06466, 3.31794), (49.06541, 3.31784), (49.06566, 3.31951), (49.06636, 3.3195), (49.06617, 3.31888), (49.06741, 3.31846), (49.0674, 3.31902), (49.06812, 3.31901), (49.06824, 3.31991), (49.06885, 3.31978), (49.06878, 3.31867), (49.06997, 3.31842), (49.06994, 3.31912), (49.06948, 3.32035), (49.06954, 3.32104), (49.07038, 3.32189), (49.07108, 3.32359), (49.07237, 3.32514), (49.07211, 3.32572), (49.07138, 3.32538), (49.0712, 3.32672), (49.06856, 3.32545), (49.06859, 3.32735), (49.0691, 3.32968), (49.06475, 3.32912), (49.06389, 3.32848), (49.06343, 3.32983), (49.06166, 3.32845), (49.06083, 3.32812), (49.06056, 3.32847), (49.05805, 3.32511), (49.05832, 3.32422), (49.05889, 3.32376), (49.05767, 3.32295)],  # way 42228177
    'lucy_se': [(49.0588, 3.31134), (49.0586, 3.31177), (49.05771, 3.31175), (49.05691, 3.30664), (49.05632, 3.30554), (49.05593, 3.30562), (49.05436, 3.30456), (49.05455, 3.3032), (49.05364, 3.30206), (49.05392, 3.30208), (49.0537, 3.30153), (49.05383, 3.30128), (49.05443, 3.30183), (49.05416, 3.30211), (49.05502, 3.30278), (49.05544, 3.30287), (49.05585, 3.30234), (49.05516, 3.30153), (49.05498, 3.30045), (49.05511, 3.29932), (49.05355, 3.29934), (49.05321, 3.30004), (49.05305, 3.2999), (49.05317, 3.2985), (49.05355, 3.29848), (49.05383, 3.29776), (49.05592, 3.29844), (49.05605, 3.29807), (49.05561, 3.29764), (49.05576, 3.29708), (49.05502, 3.29616), (49.05557, 3.2952), (49.05499, 3.29423), (49.05533, 3.29353), (49.05435, 3.29218), (49.05475, 3.29032), (49.0551, 3.28966), (49.05427, 3.28906), (49.05467, 3.28759), (49.05404, 3.28715), (49.05277, 3.287), (49.0528, 3.28666), (49.05336, 3.28681), (49.055, 3.28583), (49.0565, 3.28655), (49.05665, 3.28607), (49.0568, 3.28624), (49.05664, 3.28685), (49.05732, 3.28742), (49.05713, 3.28765), (49.05689, 3.28743), (49.05653, 3.28816), (49.05705, 3.28989), (49.05668, 3.29009), (49.05666, 3.29155), (49.05688, 3.29182), (49.05613, 3.29319), (49.05629, 3.29353), (49.05663, 3.29344), (49.05671, 3.29385), (49.05629, 3.29468), (49.05678, 3.29593), (49.05749, 3.29546), (49.05794, 3.29674), (49.05733, 3.297), (49.05752, 3.29812), (49.05821, 3.29769), (49.05866, 3.29928), (49.05785, 3.29953), (49.05746, 3.29914), (49.05743, 3.29829), (49.05655, 3.29856), (49.05592, 3.29985), (49.05615, 3.29965), (49.05659, 3.30002), (49.05661, 3.30055), (49.05755, 3.30066), (49.05711, 3.30205), (49.05638, 3.30325), (49.05677, 3.30415), (49.05734, 3.30448), (49.05904, 3.30716), (49.05884, 3.30743), (49.05806, 3.30589), (49.05776, 3.30586), (49.05766, 3.30635), (49.05844, 3.30873), (49.05794, 3.30897), (49.05816, 3.3106), (49.05875, 3.31073)],  # way 58681209
    'belleau': [(49.05717, 3.28475), (49.05777, 3.28498), (49.05759, 3.28519), (49.05789, 3.28624), (49.05822, 3.28649), (49.05807, 3.2856), (49.05853, 3.2851), (49.05925, 3.28613), (49.0595, 3.28604), (49.05982, 3.28677), (49.06019, 3.28638), (49.06095, 3.28638), (49.06014, 3.28759), (49.05919, 3.28809), (49.05897, 3.28741), (49.05855, 3.28786), (49.05879, 3.28915), (49.06048, 3.28773), (49.06083, 3.28704), (49.06101, 3.28706), (49.06105, 3.28907), (49.06066, 3.28977), (49.06095, 3.29053), (49.06318, 3.28877), (49.06472, 3.29282), (49.06685, 3.29574), (49.06914, 3.29379), (49.0678, 3.29129), (49.06884, 3.28964), (49.06948, 3.2891), (49.06919, 3.28819), (49.06999, 3.28591), (49.07037, 3.28564), (49.07115, 3.28606), (49.07127, 3.28435), (49.07221, 3.28465), (49.07258, 3.2843), (49.07339, 3.28442), (49.07389, 3.2848), (49.07392, 3.28539), (49.077, 3.28717), (49.07687, 3.28813), (49.07783, 3.28927), (49.07819, 3.29136), (49.07754, 3.29124), (49.07748, 3.29196), (49.07808, 3.29211), (49.07727, 3.29422), (49.07743, 3.29502), (49.07494, 3.29823), (49.07355, 3.29952), (49.07314, 3.29959), (49.07306, 3.30008), (49.07354, 3.30087), (49.07241, 3.30199), (49.07133, 3.29979), (49.07088, 3.30002), (49.07065, 3.29908), (49.06743, 3.30028), (49.06742, 3.30055), (49.06631, 3.30088), (49.06608, 3.30161), (49.06563, 3.30163), (49.06556, 3.30243), (49.06578, 3.30251), (49.06554, 3.30418), (49.06511, 3.30428), (49.06485, 3.3056), (49.06461, 3.30556), (49.06452, 3.30515), (49.06454, 3.30325), (49.06398, 3.30347), (49.06385, 3.3041), (49.06409, 3.30549), (49.06381, 3.30574), (49.06331, 3.30411), (49.06381, 3.30379), (49.06405, 3.30315), (49.06383, 3.30266), (49.06348, 3.30285), (49.06247, 3.30106), (49.06231, 3.2996), (49.06169, 3.29941), (49.0616, 3.29879), (49.06122, 3.29842), (49.05967, 3.29176), (49.05863, 3.28943), (49.05866, 3.28827), (49.0577, 3.28706), (49.05776, 3.28663), (49.05726, 3.28527), (49.05679, 3.28578), (49.05657, 3.28543), (49.05684, 3.28539)],  # way 58681212
    'triangle_wood': [(49.05458, 3.29556), (49.05442, 3.29572), (49.05403, 3.29521), (49.05389, 3.29543), (49.0536, 3.29519), (49.05306, 3.29712), (49.0525, 3.29761), (49.05196, 3.29724), (49.05151, 3.29738), (49.05197, 3.29826), (49.05209, 3.29908), (49.05173, 3.29978), (49.05128, 3.29989), (49.05176, 3.29913), (49.05124, 3.29778), (49.05111, 3.29566), (49.052, 3.29649), (49.05229, 3.29642), (49.05266, 3.29537), (49.05318, 3.2956), (49.05376, 3.29454)],  # way 1014467394
    'clerembauts2': [(49.05926, 3.31303), (49.05928, 3.31422), (49.05967, 3.31405), (49.05979, 3.315), (49.05949, 3.31543), (49.05859, 3.31565), (49.05853, 3.3153), (49.05824, 3.31562), (49.05769, 3.31428), (49.05866, 3.31472), (49.05862, 3.31375), (49.05845, 3.31334), (49.05793, 3.31346), (49.05788, 3.31284), (49.05871, 3.31273), (49.05877, 3.31321)],  # way 1014467395
    'square': [(49.08115, 3.26942), (49.08107, 3.27037), (49.08075, 3.27085), (49.07809, 3.26922), (49.07862, 3.26805), (49.07955, 3.26831), (49.07983, 3.26881)],  # way 1015466717
    'champillon': [(49.08324, 3.26137), (49.08293, 3.25913), (49.08316, 3.25884), (49.08247, 3.25784), (49.08249, 3.2574), (49.0811, 3.2575), (49.08106, 3.25773), (49.0793, 3.25732), (49.0787, 3.25686), (49.07783, 3.25717), (49.0765, 3.25628), (49.07594, 3.2551), (49.07554, 3.25497), (49.07524, 3.25609), (49.07665, 3.25697), (49.0766, 3.25744), (49.07692, 3.25762), (49.07818, 3.25801), (49.07983, 3.25801), (49.08032, 3.25857), (49.0811, 3.25816), (49.08215, 3.25843), (49.08287, 3.26009), (49.083, 3.26141)],  # way 1015466719
    'givry': [(49.09491, 3.27854), (49.09255, 3.27923), (49.09207, 3.2791), (49.09216, 3.27846), (49.09037, 3.27828), (49.09035, 3.27882), (49.09094, 3.27902), (49.09088, 3.27995), (49.08987, 3.27969), (49.0894, 3.27898), (49.08898, 3.27906), (49.08874, 3.27984), (49.08905, 3.28068), (49.08848, 3.28202), (49.08777, 3.28159), (49.08744, 3.28258), (49.08686, 3.28244), (49.08464, 3.28973), (49.08478, 3.28992), (49.08552, 3.28934), (49.08615, 3.28765), (49.0871, 3.28745), (49.08624, 3.28979), (49.08687, 3.29003), (49.08852, 3.28425), (49.08922, 3.2847), (49.08722, 3.29092), (49.0877, 3.29109), (49.08919, 3.28898), (49.08851, 3.28814), (49.0893, 3.28557), (49.08959, 3.2857), (49.08981, 3.28518), (49.09032, 3.28527), (49.0908, 3.28366), (49.09248, 3.28404), (49.09328, 3.28373), (49.09388, 3.28401), (49.09459, 3.28336), (49.09542, 3.28351)],  # way 1015466720
    'bussiares': [(49.08631, 3.24327), (49.08598, 3.24627), (49.08611, 3.24762), (49.08484, 3.2475), (49.08337, 3.24523), (49.08176, 3.24383), (49.08164, 3.24301), (49.08097, 3.24171), (49.08102, 3.24117), (49.08153, 3.24081), (49.08201, 3.24128), (49.08239, 3.24247), (49.08502, 3.24228), (49.08545, 3.24311), (49.08598, 3.2428)],  # way 1015466727
    'clerembauts': [(49.0632, 3.315), (49.06313, 3.31541), (49.06353, 3.31553), (49.06376, 3.31627), (49.06356, 3.31726), (49.06325, 3.31766), (49.06249, 3.31632), (49.06229, 3.31633)],  # way 1244869497
    'bussiares_e': [(49.08361, 3.25093), (49.08348, 3.25169), (49.08319, 3.25203), (49.08273, 3.25192), (49.08261, 3.25254), (49.08214, 3.25255), (49.08134, 3.25155), (49.08124, 3.25059), (49.08086, 3.25028), (49.08233, 3.25134), (49.08328, 3.2508)],  # way 1267972375
    'bussiares_e2': [(49.08481, 3.25106), (49.08445, 3.25267), (49.08366, 3.25214), (49.0837, 3.25167), (49.08442, 3.25153), (49.0846, 3.25091)],  # way 1267972376
}
WOODS = {k: [M(*p) for p in v] for k, v in WOODS_LL.items()}
WOODS['nw_lucy'] = [(-700, -620), (-560, -560), (-360, -600), (-300, -720), (-380, -820), (-560, -840), (-690, -760)]  # the brigade reserve's wood, about here
ROADS = {k: [M(*p) for p in v] for k, v in ROADS_LL.items()}
RAIL, CLIGNON, CORNU = [M(*p) for p in RAIL_LL], [M(*p) for p in CLIGNON_LL], [M(*p) for p in CORNU_LL]
def inside(x, y, poly):
    c = False
    for i in range(len(poly)):
        (xa, ya), (xb, yb) = poly[i], poly[i - 1]
        if (ya > y) != (yb > y) and x < xa + (xb - xa) * (y - ya) / (yb - ya): c = not c
    return c
def in_wood(p): return any(inside(*p, w) for w in WOODS.values())

# ---- fields: all the open ground, in farm-sized parcels that each take their own furrows (after Cantigny) ----
def hashf(i, j, s=0): return ((i * 73856093 ^ j * 19349663 ^ s * 83492791) & 0xffff) / 0xffff
CELL, PARCEL, NP = 50, 800, 5
SEEDS = {(i, j): (i * PARCEL + (hashf(i, j, 1) - 0.5) * PARCEL * 0.8, j * PARCEL + (hashf(i, j, 2) - 0.5) * PARCEL * 0.8) for i in range(-NP, NP + 1) for j in range(-NP, NP + 1)}
def parcel(x, y): return min(SEEDS, key=lambda k: math.hypot(SEEDS[k][0] - x, SEEDS[k][1] - y))
BOX = {k: (min(x for x, _ in w), max(x for x, _ in w), min(y for _, y in w), max(y for _, y in w)) for k, w in WOODS.items()}
N = 2 * HALF_EXTENT // CELL
cells = {}
for j in range(N):
    for i in range(N):
        x, y = -HALF_EXTENT + (i + 0.5) * CELL, -HALF_EXTENT + (j + 0.5) * CELL
        if not any(b[0] <= x <= b[1] and b[2] <= y <= b[3] and inside(x, y, WOODS[k]) for k, b in BOX.items()): cells.setdefault(parcel(x, y), set()).add((i, j))
def area(r): return sum(r[i][0] * r[(i + 1) % len(r)][1] - r[(i + 1) % len(r)][0] * r[i][1] for i in range(len(r))) / 2
def dp(pts, tol):
    if len(pts) < 3: return pts
    (x0, y0), (x1, y1) = pts[0], pts[-1]; Ln = math.hypot(x1 - x0, y1 - y0) or 1
    dist = [abs((x1 - x0) * (y0 - y) - (x0 - x) * (y1 - y0)) / Ln for x, y in pts]
    k = max(range(len(pts)), key=dist.__getitem__)
    return [pts[0], pts[-1]] if dist[k] <= tol else dp(pts[:k + 1], tol)[:-1] + dp(pts[k:], tol)
def rings(S):  # boundary edges with the open cell on the left, linked into loops: outer rings run anticlockwise, holes clockwise
    E = {}
    for i, j in S:
        for (di, dj), e0, e1 in (((0, -1), (i, j), (i + 1, j)), ((1, 0), (i + 1, j), (i + 1, j + 1)), ((0, 1), (i + 1, j + 1), (i, j + 1)), ((-1, 0), (i, j + 1), (i, j))):
            if (i + di, j + dj) not in S: E.setdefault(e0, []).append(e1)
    out = []
    while E:
        s = next(iter(E)); ring = [s]; p = s
        while True:
            q = E[p].pop()
            if not E[p]: del E[p]
            if q == s: break
            ring.append(q); p = q
        r = [(-HALF_EXTENT + u * CELL, -HALF_EXTENT + v * CELL) for u, v in ring]
        k = max(range(len(r)), key=lambda n: math.hypot(r[n][0] - r[0][0], r[n][1] - r[0][1]))
        out.append(dp(r[:k + 1], 30)[:-1] + dp(r[k:] + [r[0]], 30)[:-1])
    return out
FIELDS = []
for key in sorted(cells):
    rs = rings(cells[key]); outer = [r for r in rs if area(r) > 20000]
    for o in outer:
        for hole in (r for r in rs if area(r) < -10000 and inside(*r[0], o)):  # bridged in, so even-odd and non-zero fills both leave it out
            k = min(range(len(o)), key=lambda n: math.hypot(o[n][0] - hole[0][0], o[n][1] - hole[0][1]))
            o[:] = o[:k + 1] + hole + [hole[0]] + o[k:]
        FIELDS.append([(round(x), round(y)) for x, y in o])

# ---- the clock: 1 to 26 June 1918, French summer time ----
UTC = dt.timezone.utc
T0 = dt.datetime(1918, 6, 1, tzinfo=UTC)
def D(day, hm): return f"1918-06-{day:02d} {hm}"
def sec(t): return (dt.datetime.strptime(t, "%Y-%m-%d %H:%M:%S" if t.count(":") == 2 else "%Y-%m-%d %H:%M").replace(tzinfo=UTC) - T0).total_seconds()
def fmt(s): s = round(s); return (T0 + dt.timedelta(seconds=s)).strftime("%Y-%m-%d %H:%M" + (":%S" if s % 60 else ""))
def plus(t, mins): return fmt(sec(t) + mins * 60)
START, END = D(1, "14:00"), D(26, "08:00")

# ---- ground ----
def label(name, p, dy=0, dx=0, **kw): return dict(name=name, at=[p[0] + dx, p[1] + dy], **kw)
def rd(key, name, at, rot): return dict(type="road", name=name, pts=ROADS[key], at=at, rot=rot)
MARINE_LINE = [(-2050, 100), (-1400, 450), (-800, 560), (-350, 300), (-200, -300), (0, -900), (150, -1300), (300, -1720), (800, -1950), P['triangle']]
HILL142_LINE = [(-1150, 880), (-1000, 940), (-560, 1060), (-250, 1000), (-120, 980)]
RAIL_LINE = RAIL[3:16]  # the railway from south-east of Bouresches to Belleau, the German main line from 3/4 June
PPR = [(450, -1500), P['triangle'], (2000, -1900), (2750, -1600)]
features = [
    rd('lucy_torcy', "road from Lucy to Torcy", [-80, -250], -70), rd('lucy_bouresches', "road from Lucy to Bouresches", [1500, -880], 31),
    rd('bouresches_belleau', "road from Bouresches to Belleau", [2400, 0], 80), rd('torcy_belleau', "road from Torcy to Belleau", [400, 1340], 2),
    rd('belleau_givry', "road to Givry and Étrépilly", [3000, 440], -5), rd('bouresches_vaux', "road to Vaux", [2700, -1500], -53),
    rd('lucy_marigny', "road to Marigny", [-400, -1300], 0), rd('champillon_torcy', "road from Champillon to Torcy", [-2120, 400], -82),
    rd('torcy_bussiares', "road from Torcy to Bussiares", [-1250, 2230], 15), dict(type="road", name="", pts=ROADS['bussiares_licy']), rd('torcy_licy', "road to Licy", [-200, 2650], 85),
    rd('lucy_south', "road to the Paris road", [-180, -2400], 80),
    dict(type="road", name="the railway, Château-Thierry to La Ferté-Milon", pts=RAIL, at=[2350, -50], rot=-80),
    dict(type="creek", name="the Clignon", pts=CLIGNON, at=[400, 2060], rot=-20), dict(type="creek", name="", pts=CORNU),
    dict(type="trench", name="the Marine line of 2 to 5 June (about here)", pts=MARINE_LINE, **{"until": D(6, "17:00")}),
    dict(type="trench", name="Hill 142, dug in on 6 June", pts=HILL142_LINE, **{"from": D(6, "07:10")}),
    dict(type="trench", name="the German line on the railway", pts=RAIL_LINE, **{"from": D(4, "01:00")}),
    dict(type="trench", name="", pts=PPR, **{"from": D(8, "00:00")}),
    label("Lucy-le-Bocage", P['lucy'], dx=-300, dy=-120), label("Bouresches", P['bouresches'], dx=280, dy=-100), label("Belleau", P['belleau'], dx=60, dy=120),
    label("Torcy", P['torcy'], dx=-200, dy=90), label("Champillon", P['champillon'], dy=-130), label("Les Mares Farm", P['mares'], dy=-130),
    label("Bussiares", P['bussiares'], dy=150), label("Givry", P['givry'], dy=140), label("Licy-Clignon", P['licy'], dx=250, dy=-40),
    label("La Cense", P['cense'], dy=-110), label("La Voie du Châtel", P['voie'], dy=-120), label("Triangle Farm (about here)", P['triangle'], dy=-130),
    label("Hill 142", P['h142'], dx=-250, dy=40), label("Hill 176 (about here)", P['h176'], dx=-150, dy=-110), label("Hill 126 (about here)", P['h126'], dx=-200, dy=0),
    label("Hill 133 (about here)", P['h133'], dy=-60), label("Hill 169 (about here)", P['h169'], dx=-120, dy=30), label("Hill 181 (about here)", P['h181'], dx=-250),
    label("the Pavilion (about here)", P['pavilion'], dy=60), label("Bouresches station", P['station'], dx=300, dy=60),
    label("Bois de Belleau", (1150, -150)), label("Bois de la Rochette", (3150, -600)), label("Les Brusses (about here)", P['brusses'], dx=150, dy=-120),
    label("the square woods", (-770, 1180), dx=-150),
    label("woods north-west of Lucy (about here)", (-500, -700), dy=-200),
]
for f in features:
    if "at" in f: assert on_land(f["at"]) and max(map(abs, f["at"])) < HALF_EXTENT - 100, (f.get("name"), f["at"], "a label off the map")

# ---- order of battle: (id, side, short, name, commander, type, strength, extra) ----
# Marine companies are about 250 [HILL]; 1/5 went in on 6 June with 22 officers and 953 men [COZ]. German companies are
# about 100 to 150, and the 237th Division's regiments are set so that their losses reach Otto's rifle strengths of 13
# June. Strengths the sources do not give (the French, the 23rd and 7th Infantry battalions, most German battalions) are
# battalion-sized and said so in the unit's name.
T15 = "1st Battalion, 5th Marines (Maj. Julius S. Turrill)"; T36 = "3rd Battalion, 6th Marines (Maj. Berton W. Sibley)"
OOB = [
    ("m5_17", "american", "17th Co.", f"17th Company, {T15}", "Capt. Winans", "infantry", 244, {}),
    ("m5_49", "american", "49th Co.", f"49th Company, {T15}", "Capt. Hamilton", "infantry", 244, {}),
    ("m5_66", "american", "66th Co.", f"66th Company, {T15}", "", "infantry", 244, {}),
    ("m5_67", "american", "67th Co.", f"67th Company, {T15}", "Capt. Crowther", "infantry", 243, {}),
    ("m5_2", "american", "2/5th Marines", "2nd Battalion, 5th Marines: the 18th, 43rd and 55th Companies", "Lt. Col. Frederic M. Wise", "infantry", 750, {}),
    ("m5_51", "american", "51st Co.", "51st Company, 2nd Battalion, 5th Marines", "Capt. Lloyd Williams (mortally wounded 11 June)", "infantry", 250, {}),
    ("m5_3", "american", "3/5th Marines", "3rd Battalion, 5th Marines: the 16th, 20th and 47th Companies", "Maj. Benjamin S. Berry (wounded 6 June), then Maj. Maurice E. Shearer", "infantry", 750, {}),
    ("m5_45", "american", "45th Co.", "45th Company, 3rd Battalion, 5th Marines", "", "infantry", 250, {}),
    ("m6_1", "american", "1/6th Marines", "1st Battalion, 6th Marines: the 74th, 75th, 76th and 95th Companies", "Maj. Maurice Shearer, then Maj. John A. Hughes", "infantry", 1000, {}),
    ("m6_2", "american", "2/6th Marines", "2nd Battalion, 6th Marines: the 78th, 79th and 80th Companies", "Maj. Thomas Holcomb", "infantry", 750, {}),
    ("m6_96", "american", "96th Co.", "96th Company, 2nd Battalion, 6th Marines", "Capt. Duncan (killed 6 June), then Lt. Robertson and Lt. Clifton Cates", "infantry", 250, {}),
    ("m6_82", "american", "82nd Co.", f"82nd Company, {T36}", "", "infantry", 250, {}),
    ("m6_83", "american", "83rd Co.", f"83rd Company, {T36}", "", "infantry", 250, {}),
    ("m6_8497", "american", "84th, 97th Cos.", f"84th and 97th Companies, {T36}", "", "infantry", 500, {}),
    ("eng_a", "american", "Co. A, 2nd Eng.", "Company A, 2nd Engineers (about 200)", "", "infantry", 200, {}),
    ("eng_b", "american", "Co. B, 2nd Eng.", "Company B, 2nd Engineers (about 200)", "", "infantry", 200, {}),
    ("eng_c", "american", "Co. C, 2nd Eng.", "Company C, 2nd Engineers (about 200)", "", "infantry", 200, {}),
    ("eng_d", "american", "Co. D, 2nd Eng.", "Company D, 2nd Engineers (about 200)", "", "infantry", 200, {}),
    ("eng_f", "american", "Co. F, 2nd Eng.", "Company F, 2nd Engineers (about 200)", "", "infantry", 200, {}),
    ("inf23", "american", "23rd Inf.", "A battalion of the 23rd Infantry, 3rd Brigade (about 1,000)", "Col. Paul B. Malone (regiment)", "infantry", 1000, {}),
    ("inf7_1", "american", "1/7th Inf.", "1st Battalion, 7th Infantry, 3rd Division, attached (about 1,000)", "Lt. Col. Adams", "infantry", 1000, {}),
    ("inf7_2", "american", "2/7th Inf.", "2nd Battalion, 7th Infantry, 3rd Division, attached (about 1,000)", "", "infantry", 1000, {}),
    ("inf7_3", "american", "3/7th Inf.", "3rd Battalion, 7th Infantry, 3rd Division, attached (about 1,000)", "", "infantry", 1000, {}),
    ("fr43", "french", "French 43rd Div.", "Rearguards of the French 43rd Division, falling back through the Marines (strength not recorded)", "Gen. Michel", "infantry", 500, dict(loose=True)),
    ("fr45", "french", "French 45th Div.", "The left of the French 45th Division, in line until the 2nd Division relieved it on 4 June (strength not recorded)", "", "infantry", 500, dict(loose=True)),
    ("fr167", "french", "French 167th Div.", "The French 167th Division (116th, 409th and 147th Infantry) on the left, drawn as one battalion (strength not recorded)", "", "infantry", 800, {}),
    ("fr174", "french", "1/174th Inf.", "1st Battalion, French 174th Infantry (strength not recorded)", "", "infantry", 800, {}),
    ("g462", "german", "462nd I.R.", "462nd Infantry Regiment, 237th Division", "Maj. Mors (died of wounds)", "infantry", 822, {}),
    ("g462_10", "german", "10th Coy, 462", "10th Company, 462nd Infantry, on Hill 142", "", "infantry", 120, {}),
    ("g460_9", "german", "9th Coy, 460", "9th Company, 460th Infantry, in the first woods south of Hill 142", "", "infantry", 120, {}),
    ("g460_1011", "german", "10th, 11th Coys, 460", "10th and 11th Companies, 460th Infantry, in the square woods", "", "infantry", 240, {}),
    ("g460_12", "german", "12th Coy, 460", "12th Company, 460th Infantry, in reserve behind Hill 142", "", "infantry", 120, {}),
    ("g460_2", "german", "II/460", "2nd Battalion, 460th Infantry, 237th Division", "Lt. Col. Friedrich Tismer (regiment)", "infantry", 570, {}),
    ("g461_1", "german", "I/461", "1st Battalion, 461st Infantry, the west half of the wood", "Maj. Hartlieb", "infantry", 585, dict(loose=True)),
    ("g461_2", "german", "II/461", "2nd Battalion, 461st Infantry, the east half of the wood", "Maj. Hans Bischoff (regiment)", "infantry", 584, dict(loose=True)),
    ("g273", "german", "273rd I.R.", "273rd Infantry Regiment, 197th Division (about 1,000)", "", "infantry", 1000, {}),
    ("g_jager", "german", "Saxon Jäger", "A Saxon Jäger battalion, 197th Division (about 500)", "", "infantry", 500, {}),
    ("g20", "german", "20th I.R.", "20th Infantry Regiment, 5th Guard Division, drawn as a battalion (about 600)", "", "infantry", 600, {}),
    ("g398_3", "german", "III/398", "3rd Battalion, 398th Infantry, 10th Division (about 400)", "", "infantry", 400, {}),
    ("g398_out", "german", "7th, 8th Coys, 398", "7th and 8th Companies, 398th Infantry, the outpost in Bouresches", "", "infantry", 250, dict(loose=True)),
    ("g398_1", "german", "I/398", "1st Battalion, 398th Infantry, the left wing east of the railway (about 400)", "", "infantry", 400, {}),
    ("g47_1", "german", "I/47", "1st Battalion, 47th Infantry, 10th Division (about 400)", "Capt. Rickert", "infantry", 400, {}),
    ("g6g_2", "german", "II/6 Gren.", "2nd Battalion, 6th Grenadiers, 10th Division", "", "infantry", 200, {}),
    ("g6g_3", "german", "III/6 Gren.", "3rd Battalion, 6th Grenadiers, 10th Division", "", "infantry", 200, {}),
    ("g40_2", "german", "II/40 Fus.", "2nd Battalion, 40th Fusiliers, 28th (Baden) Division (about 600)", "", "infantry", 600, dict(loose=True)),
    ("g40_1", "german", "I/40 Fus.", "1st Battalion, 40th Fusiliers, 28th (Baden) Division (about 600)", "", "infantry", 600, {}),
    ("g110_2", "german", "II/110 Gren.", "2nd Battalion, 110th Grenadiers, 28th (Baden) Division (about 600)", "Mencke", "infantry", 600, {}),
    ("g109", "german", "109th Gren.", "A battalion of the 109th Grenadiers, 28th (Baden) Division (about 700)", "", "infantry", 700, {}),
    ("g_rav", "german", "German battalion", "A German battalion that formed in the ravine north of Bouresches on 11 June (unit and strength not recorded)", "", "infantry", 500, {}),
    ("g345", "german", "345th I.R.", "345th Infantry, 87th Division, about Torcy, drawn as a battalion (about 500)", "", "infantry", 500, {}),
    ("g347_1", "german", "I/347", "Five companies of the 1st and 2nd Battalions, 347th Infantry, 87th Division, in the north of the wood", "Capt. Kaulbars", "infantry", 600, dict(loose=True)),
    ("g347_3", "german", "III/347", "3rd Battalion, 347th Infantry, 87th Division (about 400)", "", "infantry", 400, {}),
    ("g347_pow", "german", "prisoners", "Prisoners of the 347th, marched back through Lucy", "", "infantry", 300, {}),
    ("g3e", "german", "3rd Ersatz", "Two companies of the 3rd Ersatz Regiment, sent to Belleau", "", "infantry", 250, {}),
]
BASE = {row[0]: row for row in OOB}

# ---- movement ----
KEYS = {}
def K(t, p, **kw): return dict(t=t, x=round(p[0]), y=round(p[1]), **kw)
def carried(id, f): return next((k[f] for k in reversed(KEYS.get(id, [])) if f in k), {"state": "line", "strength": BASE[id][6]}.get(f))
def keys(id, ks):  # every leg starts where the unit stands, unless it is coming out of hiding
    have = KEYS.setdefault(id, [])
    if have and ks:
        a, b = have[-1], ks[0]
        assert sec(b["t"]) >= sec(a["t"]), (id, a["t"], b["t"], "a key before the last one: the unit is still on its way")
        assert carried(id, "state") == "hidden" or (a["x"], a["y"]) == (b["x"], b["y"]), (id, a["t"], b["t"], "a leg must start where the unit stands")
        if a["t"] == b["t"]: a.update({k: v for k, v in b.items() if k != "t"}); ks = ks[1:]
    have += ks
def last(id): k = KEYS[id][-1]; return (k["x"], k["y"])
def heading(a, b): return round(math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) % 360)
def hold_until(id, t0):  # stand until the minute before t0, then turn and go
    if sec(t0) - sec(KEYS[id][-1]["t"]) > 120: at(id, plus(t0, -1))
def at(id, t, **kw): keys(id, [K(t, last(id), **kw)])  # a change in place
def turn(id, t, h, **kw): hold_until(id, t); at(id, t, h=h, **kw)
def appear(id, t, p, h, state="line", **kw): keys(id, [K(t, p, h=h, state=state, **kw)])
def hide(id, t): at(id, t, state="hidden")
PACE = 4  # km/h, a column of foot on the road
def walk(t0, pts, state="column", kmh=PACE):  # keys along a path at a marching pace
    pts = [p for i, p in enumerate(pts) if i == 0 or math.dist(p, pts[i - 1]) > 5]
    t, out = sec(t0), []
    for i, p in enumerate(pts):
        if i: t += math.dist(pts[i - 1], p) / (kmh / 3.6)
        out.append(K(fmt(t), p, h=heading(p, pts[i + 1]) if i + 1 < len(pts) else heading(pts[i - 1], p), **(dict(state=state) if i == 0 else {})))
    return out
def move(id, t0, pts, h=None, state="line", moving="column", kmh=PACE):  # from where it stands along pts at a pace; returns the arrival time
    hold_until(id, t0)
    ks = walk(t0, [last(id)] + pts, moving, kmh); ks[-1]["state"] = state
    if h is not None: ks[-1]["h"] = h
    keys(id, ks); return ks[-1]["t"]
def go(id, t0, t1, pts, h=None, state="line", moving="column"):  # from where it stands along pts, arriving at t1
    hold_until(id, t0)
    pts = [last(id)] + pts; pts = [p for i, p in enumerate(pts) if i == 0 or math.dist(p, pts[i - 1]) > 5]; d = [0]
    if len(pts) == 1: return at(id, t1, state=state, **({"h": h} if h is not None else {}))
    for a, b in zip(pts, pts[1:]): d.append(d[-1] + math.dist(a, b))
    ks = [K(fmt(sec(t0) + (sec(t1) - sec(t0)) * d[i] / d[-1]), p, h=heading(p, pts[i + 1]) if i + 1 < len(pts) else heading(pts[i - 1], p)) for i, p in enumerate(pts)]
    ks[0]["state"] = moving; ks[-1]["state"] = state
    if h is not None: ks[-1]["h"] = h
    keys(id, ks)
def fire(id, t0, t1, state="line"): hold_until(id, t0); at(id, t0, state="firing"); at(id, t1, state=state)
def leave(id, t0, pts, kmh=PACE):  # march off the map and out of the replay
    hide(id, plus(move(id, t0, pts, moving="column", state="column", kmh=kmh), 1))
SOUTH = lambda x: (x, -3450)

# 1 June, 2 p.m.: the 6th Marines come up from the Paris road; the French 43rd's rearguards fall back through them.
for id in BASE: appear(id, START, (0, 0), 0, state="hidden")
for id, x in (("m6_1", -100), ("m6_2", 900), ("m6_82", -2250), ("m6_83", -2350), ("m6_8497", -2450)): appear(id, START, SOUTH(x), 0, state="column")
appear("fr43", START, (-300, 200), 20, state="line")
appear("fr45", START, (-550, 950), 0, state="line")

assert set(KEYS) == set(BASE), set(KEYS) ^ set(BASE)
for id in KEYS:
    if carried(id, "state") != "hidden" and sec(KEYS[id][-1]["t"]) < sec(END): at(id, END)

# ---- assemble and check ----
units = []
TOP = {"infantry": 6}  # km/h, the fastest any leg may go
for id, side, short, name, commander, type, strength, extra in OOB:
    ks, state, h = KEYS[id], None, None
    for a, b in zip(ks, ks[1:]):
        state, h = a.get("state", state), a.get("h", h)
        assert sec(b["t"]) > sec(a["t"]), (id, a["t"], b["t"])
        if state == "hidden": continue
        moved = (a["x"], a["y"]) != (b["x"], b["y"])
        assert moved or b.get("h", h) == h or "strength" in b or sec(b["t"]) - sec(a["t"]) <= 600, (id, a["t"], b["t"], "a slow turn in place holds the time-lapse")
        assert not (moved and sec(b["t"]) - sec(a["t"]) > 3 * 3600), (id, a["t"], b["t"], "a march leg over three hours")
        kmh = math.dist((a["x"], a["y"]), (b["x"], b["y"])) / (sec(b["t"]) - sec(a["t"])) * 3.6
        assert kmh <= TOP[type], (id, a["t"], b["t"], f"{kmh:.1f} km/h")
    state = None
    for k in ks:
        state = k.get("state", state)
        assert state == "hidden" or (on_land((k["x"], k["y"])) and max(abs(k["x"]), abs(k["y"])) < HALF_EXTENT), (id, k["t"], (k["x"], k["y"]), "off the map")
    units.append(dict(id=id, side=side, name=name, short=short, commander=commander, type=type, strength=strength, keys=ks, **extra))

events, TINTS = [], []
SOURCES = ["Woods, roads and places from OpenStreetMap (ODbL).", "Terrain: " + T["source"] + ", 30 m, sampled to 17.5 m."]

battle = dict(
    id="belleau-wood", name="Battle of Belleau Wood", date="1918-06-01", dateText="1 to 26 June 1918", place="Belleau Wood, near Château-Thierry, Aisne, France",
    origin=dict(lat=LAT0, lon=LON0), extent=2 * HALF_EXTENT, start=START, end=END, sunrise="04:44", sunset="20:50", speed=60, lapse=7200, menPerDot=10,
    terrainExaggeration=2, contourInterval=10, trees=dict(density=0.008), fields=FIELDS, wind=dict(x=0.5, y=0.3), view=dict(x=0, y=0, width=7000),
    sides=dict(american=dict(name="Americans (2nd Division, Bundy; 4th Marine Brigade, Harbord)", color="#2a55a0", light="#7090c8", dark="#15305e"),
               french=dict(name="French (XXI Corps, Degoutte)", color="#6d8fb5", light="#a9c0dc", dark="#36506e"),
               german=dict(name="Germans (IV Reserve Corps, von Conta)", color="#4a4a42", light="#8c8c80", dark="#22221e")),
    features=features, units=units, events=events, tints=TINTS,
    sources=SOURCES,
)
json.dump(battle, open(HERE + "battle.json", "w"), indent=1)
print(len(units), "units,", len(events), "events,", len(features), "features,", len(FIELDS), "fields")
