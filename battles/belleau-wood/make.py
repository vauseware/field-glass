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
    rd('bouresches_belleau', "road from Bouresches to Belleau", [2400, 0], 80), rd('torcy_belleau', "road from Torcy to Belleau", [650, 1320], 2),
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
    label("Hill 133 (about here)", P['h133'], dx=-120, dy=110), label("Hill 169 (about here)", P['h169'], dx=-120, dy=30), label("Hill 181 (about here)", P['h181'], dx=-250),
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
M1 = dict(ranks=1)  # companies, 3/5 and the 84th and 97th went forward in waves of single lines, a company about 175 m across
OOB = [
    ("m5_17", "american", "17th Co.", f"17th Company, {T15}", "Capt. Winans", "infantry", 244, M1),
    ("m5_49", "american", "49th Co.", f"49th Company, {T15}", "Capt. Hamilton", "infantry", 244, M1),
    ("m5_66", "american", "66th Co.", f"66th Company, {T15}", "", "infantry", 244, M1),
    ("m5_67", "american", "67th Co.", f"67th Company, {T15}", "Capt. Crowther", "infantry", 243, M1),
    ("m5_2", "american", "2/5th Marines", "2nd Battalion, 5th Marines: the 18th, 43rd and 55th Companies", "Lt. Col. Frederic M. Wise", "infantry", 750, {}),
    ("m5_51", "american", "51st Co.", "51st Company, 2nd Battalion, 5th Marines", "Capt. Lloyd Williams (mortally wounded 11 June)", "infantry", 250, M1),
    ("m5_3", "american", "3/5th Marines", "3rd Battalion, 5th Marines: the 16th, 20th and 47th Companies", "Maj. Benjamin S. Berry (wounded 6 June), then Maj. Maurice E. Shearer", "infantry", 750, M1),
    ("m5_45", "american", "45th Co.", "45th Company, 3rd Battalion, 5th Marines", "", "infantry", 250, M1),
    ("m6_1", "american", "1/6th Marines", "1st Battalion, 6th Marines: the 74th, 75th, 76th and 95th Companies", "Maj. Maurice Shearer, then Maj. John A. Hughes", "infantry", 1000, {}),
    ("m6_2", "american", "2/6th Marines", "2nd Battalion, 6th Marines: the 78th, 79th and 80th Companies", "Maj. Thomas Holcomb", "infantry", 750, {}),
    ("m6_96", "american", "96th Co.", "96th Company, 2nd Battalion, 6th Marines", "Capt. Duncan (killed 6 June), then Lt. Robertson and Lt. Clifton Cates", "infantry", 250, M1),
    ("m6_82", "american", "82nd Co.", f"82nd Company, {T36}", "", "infantry", 250, M1),
    ("m6_83", "american", "83rd Co.", f"83rd Company, {T36}", "", "infantry", 250, M1),
    ("m6_8497", "american", "84th, 97th Cos.", f"84th and 97th Companies, {T36}", "", "infantry", 500, M1),
    ("eng_a", "american", "Co. A, 2nd Eng.", "Company A, 2nd Engineers (about 200)", "", "infantry", 200, {}),
    ("eng_b", "american", "Co. B, 2nd Eng.", "Company B, 2nd Engineers (about 200)", "", "infantry", 200, {}),
    ("eng_c", "american", "Co. C, 2nd Eng.", "Company C, 2nd Engineers (about 200)", "", "infantry", 200, {}),
    ("eng_d", "american", "Co. D, 2nd Eng.", "Company D, 2nd Engineers (about 200)", "", "infantry", 200, {}),
    ("eng_f", "american", "Co. F, 2nd Eng.", "Company F, 2nd Engineers (about 200)", "", "infantry", 200, {}),
    ("inf23", "american", "23rd Inf.", "A battalion of the 23rd Infantry, 3rd Brigade (about 1,000)", "Col. Paul B. Malone (regiment)", "infantry", 1000, {}),
    ("inf7_1", "american", "1/7th Inf.", "1st Battalion, 7th Infantry, 3rd Division, attached (about 1,000)", "Lt. Col. Adams", "infantry", 1000, {}),
    ("inf7_2", "american", "2/7th Inf.", "2nd Battalion, 7th Infantry, 3rd Division, attached (about 1,000)", "", "infantry", 1000, {}),
    ("inf7_3", "american", "3/7th Inf.", "3rd Battalion, 7th Infantry, 3rd Division, attached (about 1,000)", "", "infantry", 1000, {}),
    ("fr43", "french", "French 43rd Div.", "Rearguards of the French 43rd Division, falling back through the Marines (strength not recorded)", "Gen. Michel", "infantry", 500, {}),
    ("fr45", "french", "French 45th Div.", "The left of the French 45th Division, in line until the 2nd Division relieved it on 4 June (strength not recorded)", "", "infantry", 500, {}),
    ("fr167", "french", "French 167th Div.", "The French 167th Division (116th, 409th and 147th Infantry) on the left, drawn as one battalion (strength not recorded)", "", "infantry", 800, {}),
    ("fr174", "french", "1/174th Inf.", "1st Battalion, French 174th Infantry (strength not recorded)", "", "infantry", 800, {}),
    ("g462", "german", "462nd I.R.", "462nd Infantry Regiment, 237th Division", "Maj. Mors (died of wounds)", "infantry", 822, {}),
    ("g462_10", "german", "10th Coy, 462", "10th Company, 462nd Infantry, on Hill 142", "", "infantry", 120, {}),
    ("g460_9", "german", "9th Coy, 460", "9th Company, 460th Infantry, in the first woods south of Hill 142", "", "infantry", 120, {}),
    ("g460_1011", "german", "10th, 11th Coys, 460", "10th and 11th Companies, 460th Infantry, in the square woods", "", "infantry", 240, {}),
    ("g460_12", "german", "12th Coy, 460", "12th Company, 460th Infantry, in reserve behind Hill 142", "", "infantry", 120, {}),
    ("g460_2", "german", "II/460", "2nd Battalion, 460th Infantry, 237th Division", "Lt. Col. Friedrich Tismer (regiment)", "infantry", 570, {}),
    ("g461_1", "german", "I/461", "1st Battalion, 461st Infantry, the west half of the wood", "Maj. Hartlieb", "infantry", 585, {}),
    ("g461_2", "german", "II/461", "2nd Battalion, 461st Infantry, the east half of the wood", "Maj. Hans Bischoff (regiment)", "infantry", 584, {}),
    ("g273", "german", "273rd I.R.", "273rd Infantry Regiment, 197th Division (about 1,000)", "", "infantry", 1000, {}),
    ("g_jager", "german", "Saxon Jäger", "A Saxon Jäger battalion, 197th Division (about 500)", "", "infantry", 500, {}),
    ("g20", "german", "20th I.R.", "20th Infantry Regiment, 5th Guard Division, drawn as a battalion (about 600)", "", "infantry", 600, {}),
    ("g398_3", "german", "III/398", "3rd Battalion, 398th Infantry, 10th Division (about 400)", "", "infantry", 400, {}),
    ("g398_out", "german", "7th, 8th Coys, 398", "7th and 8th Companies, 398th Infantry, the outpost in Bouresches", "", "infantry", 250, dict(loose=True)),
    ("g398_1", "german", "I/398", "1st Battalion, 398th Infantry, the left wing east of the railway (about 400)", "", "infantry", 400, {}),
    ("g47_1", "german", "I/47", "1st Battalion, 47th Infantry, 10th Division (about 400)", "Capt. Rickert", "infantry", 400, {}),
    ("g6g_2", "german", "II/6 Gren.", "2nd Battalion, 6th Grenadiers, 10th Division", "", "infantry", 200, {}),
    ("g6g_3", "german", "III/6 Gren.", "3rd Battalion, 6th Grenadiers, 10th Division", "", "infantry", 200, {}),
    ("g40_2", "german", "II/40 Fus.", "2nd Battalion, 40th Fusiliers, 28th (Baden) Division (about 600)", "", "infantry", 600, {}),
    ("g40_1", "german", "I/40 Fus.", "1st Battalion, 40th Fusiliers, 28th (Baden) Division (about 600)", "", "infantry", 600, {}),
    ("g110_2", "german", "II/110 Gren.", "2nd Battalion, 110th Grenadiers, 28th (Baden) Division (about 600)", "Mencke", "infantry", 600, {}),
    ("g109", "german", "109th Gren.", "A battalion of the 109th Grenadiers, 28th (Baden) Division (about 700)", "", "infantry", 700, {}),
    ("g_rav", "german", "German battalion", "A German battalion that formed in the ravine north of Bouresches on 11 June (unit and strength not recorded)", "", "infantry", 500, {}),
    ("g345", "german", "345th I.R.", "345th Infantry, 87th Division, about Torcy, drawn as a battalion (about 500)", "", "infantry", 500, {}),
    ("g347_1", "german", "I/347", "Five companies of the 1st and 2nd Battalions, 347th Infantry, 87th Division, in the north of the wood", "Capt. Kaulbars", "infantry", 600, {}),
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
LUCY, BOURESCHES, BELLEAU = P['lucy'], P['bouresches'], P['belleau']
L_T = ROADS['lucy_torcy']; TORCY_RD = [(121, -554), (11, -257), (157, -58), (128, 129), (44, 198), (-142, 676)]  # its vertices north of Lucy
def smoke(at, t0, t1, rate=10, spread=500): features.append(dict(type="smoke", at=list(at), rate=rate, spread=spread, **{"from": t0, "until": t1}))

# ---- 1 June: into the line ----
move("m6_1", START, [(-100, -2400), (-60, -1700), (-12, -1458), (50, -1050)], h=30)
move("m6_2", START, [(900, -2500), (500, -1900)], h=20)
move("m6_82", START, [(-2250, -1500)], h=30); move("m6_83", START, [(-2150, -1600)], h=30); move("m6_8497", START, [(-2400, -1650)], h=30)
hide("fr43", plus(move("fr43", D(1, "14:10"), [(-250, -500), (-150, -1200), (-60, -1700), SOUTH(-100)], state="retreat", moving="retreat", kmh=3), 1))

# ---- 2 June: the 5th Marines on the left; the Germans take Bouresches, Cote 126 and the wood ----
for id, p0, p1, h, t in (("m5_2", (-3450, -450), (-2900, 250), 15, "01:15"), ("m5_51", (-3450, -400), (-2600, 300), 15, "01:15"),
                         ("m5_17", (-3450, -350), (-3200, 200), 0, "01:20"), ("m5_66", (-3450, -300), (-2750, 450), 15, "01:20"),
                         ("m5_3", SOUTH(-400), (250, -1250), 10, "01:00"), ("m5_45", SOUTH(-500), (100, -1400), 0, "01:00")):
    appear(id, D(2, t), p0, h=heading(p0, p1), state="column"); move(id, plus(D(2, t), 1), [(p0[0], -1500), p1] if p0[1] < -3000 else [p1], h=h)
appear("g398_3", D(2, "01:37"), (3450, 0), 240, state="column"); go("g398_3", D(2, "01:37"), D(2, "02:00"), [(2150, -750)], h=240, moving="charge")
appear("g398_out", D(2, "01:37"), (3450, -200), 240, state="column"); go("g398_out", D(2, "01:37"), D(2, "02:00"), [(2000, -900)], h=240, moving="charge")
appear("g462", D(2, "19:30"), (300, 2700), 220, state="column"); go("g462", D(2, "19:30"), D(2, "20:00"), [(-350, 1900)])
go("g462", D(2, "20:00"), D(2, "20:10"), [P['h126']], state="firing", moving="charge")
go("g462", D(2, "20:45"), D(2, "21:15"), [(-350, 1150)], h=200, moving="charge")
go("fr45", D(2, "20:45"), D(2, "21:10"), [(-600, 600)], h=0, moving="retreat")
appear("g461_1", D(2, "19:45"), (900, 2500), 200, state="column"); go("g461_1", D(2, "19:45"), D(2, "20:45"), [(800, 1400), (600, 750)], h=210)
appear("g461_2", D(2, "19:45"), (1300, 2400), 200, state="column"); go("g461_2", D(2, "19:45"), D(2, "20:55"), [(1300, 1300), (1100, 450)], h=200)
appear("g273", D(2, "20:00"), (-1700, 3450), 180, state="column"); go("g273", D(2, "20:00"), D(2, "20:50"), [(-1600, 2450)], h=180)
appear("g_jager", D(2, "21:00"), (-1300, 3450), 180, state="column"); go("g_jager", D(2, "21:00"), D(2, "21:45"), [(-1450, 2550)], h=190)

# ---- 3 June: the 237th Division's attack; Les Mares Farm ----
appear("g398_1", D(3, "06:00"), (3450, -900), 260, state="column"); go("g398_1", D(3, "06:00"), D(3, "06:20"), [(2700, -1000)], h=250)
go("g461_1", D(3, "11:30"), D(3, "12:10"), [(520, 250)], h=250, moving="charge")
go("g461_2", D(3, "11:30"), D(3, "12:30"), [(850, -800)], h=210, moving="charge")
go("g462", D(3, "11:30"), D(3, "12:00"), [(-650, 920)], h=220, state="firing", moving="charge"); at("g462", D(3, "12:40"), state="line")
fire("fr45", D(3, "11:40"), D(3, "12:30"))
move("m6_82", D(3, "11:20"), [(-1000, 580)], h=0)
fire("g461_1", D(3, "14:00"), D(3, "14:20"))
go("g273", D(3, "15:00"), D(3, "15:50"), [(-2650, 1300)], h=200)
go("g273", D(3, "16:00"), D(3, "16:12"), [(-2900, 360)], h=195, state="rout", moving="charge")
go("g273", D(3, "16:13"), D(3, "16:45"), [(-2500, 1600)], h=200, moving="rout")
fire("m5_2", D(3, "15:58"), D(3, "16:15")); fire("m5_51", D(3, "16:00"), D(3, "16:15")); fire("m5_17", D(3, "16:00"), D(3, "16:12")); fire("m5_66", D(3, "16:00"), D(3, "16:15"))
move("m6_83", D(3, "20:40"), [(-400, 620)], h=10)

# ---- night 3/4 and 4 June: the 460th relieves the 462nd; the railway becomes the German line; the French 45th goes ----
go("g462", D(4, "00:30"), D(4, "01:30"), [(-300, 1500), (-50, 2150)], h=180)
for id, p0, p1, t1 in (("g460_9", (-700, 2000), (-820, 830), "01:15"), ("g460_1011", (-600, 2050), (-770, 1100), "01:10"), ("g460_12", (-500, 2050), (-700, 1450), "01:00"),
                       ("g462_10", (-400, 2050), (-600, 1000), "01:20"), ("g460_2", (-1300, 2600), (-1300, 1800), "01:00")):
    appear(id, D(4, "00:30"), p0, 180, state="column"); go(id, D(4, "00:30"), D(4, t1), [p1], h=180)
go("g398_3", D(4, "00:30"), D(4, "00:45"), [(2350, -450)], h=220)
leave("fr45", D(4, "08:00"), [(-700, -200), SOUTH(-900)])
smoke(P['cense'], D(4, "08:00"), D(4, "11:00"), rate=6, spread=300)
go("g273", D(4, "22:00"), D(4, "22:40"), [P['knoll_w']], h=120)

# ---- night 5/6: 1/5 relieves 3/6 west of the wood; a battalion of the 23rd takes over 2/6's line ----
appear("inf23", D(6, "02:20"), SOUTH(1200), 0, state="column"); go("inf23", D(6, "02:20"), D(6, "03:00"), [(1100, -2200)], h=40)
move("m6_2", D(6, "03:05"), [(300, -2250)], h=30)
appear("m6_96", D(6, "03:00"), SOUTH(1300), 0, state="column"); move("m6_96", D(6, "03:01"), [(1350, -1800)], h=20)
J49, J67 = (-550, 580), (-1000, 560)  # the jump-off on Hill 176
appear("m5_49", D(6, "01:54"), (-3450, -300), 85, state="column"); move("m5_49", D(6, "01:54"), [(-2100, -200), J49], h=0)
appear("m5_67", D(6, "03:04"), (-3450, -300), 85, state="column"); move("m5_67", D(6, "03:04"), [(-2100, -200), J67], h=0)
move("m6_82", D(6, "02:45"), [(-800, -300), (-400, -1650)], h=30)
move("m6_83", D(6, "03:00"), [(-300, -300), (-300, -1700)], h=30)

# ---- 6 June, 3.45 a.m.: Hill 142 ----
smoke((-800, 1100), D(6, "03:15"), D(6, "03:45"), rate=14, spread=600); smoke(P['knoll_w'], D(6, "03:15"), D(6, "03:45"), rate=8, spread=400)
go("m5_49", D(6, "03:45"), D(6, "03:53"), [(-560, 900)], h=0, state="firing", moving="charge")
go("m5_49", D(6, "03:58"), D(6, "04:05"), [(-600, 980)], h=350, state="firing", moving="charge"); at("m5_49", D(6, "04:40"), state="line")
go("m5_67", D(6, "03:45"), D(6, "03:55"), [(-1000, 880)], h=330, state="firing", moving="charge"); at("m5_67", D(6, "04:40"), state="line")
fire("g460_9", D(6, "03:46"), D(6, "03:55"), state="rout"); go("g460_9", D(6, "03:56"), D(6, "04:05"), [(-900, 1000)], moving="rout", state="rout"); hide("g460_9", D(6, "04:06"))
fire("g462_10", D(6, "03:50"), D(6, "04:03"), state="surrender"); hide("g462_10", D(6, "04:20"))
fire("g460_1011", D(6, "03:50"), D(6, "04:40")); fire("g273", D(6, "03:55"), D(6, "04:30"))
move("m5_66", D(6, "04:40"), [(-850, 760)], h=0)
move("m5_17", D(6, "04:50"), [(-1500, 450), (-250, 950)], h=0)
appear("eng_d", D(6, "05:00"), P['champillon'], 40, state="column"); go("eng_d", D(6, "05:00"), D(6, "05:30"), [(-700, 800)], h=0)
move("m5_51", D(6, "06:00"), [P['champillon'], (-1500, 400), (-1150, 650)], h=290)
smoke((-650, 950), D(6, "06:10"), D(6, "18:00"), rate=3, spread=600)
go("g273", D(6, "07:30"), D(6, "08:15"), [(-1900, 2000)], h=30, moving="retreat")
# Hamilton runs on through the square woods toward the Bussiares road, then brings the 49th back to the nose of the hill.
go("m5_49", D(6, "07:00"), D(6, "07:25"), [(-600, 1250), (-750, 1650)], state="firing", moving="charge")
go("m5_49", D(6, "08:00"), D(6, "08:40"), [(-600, 1250), (-520, 1080)], h=0, moving="retreat")
fire("g460_1011", D(6, "07:10"), D(6, "07:30"))
appear("fr167", D(6, "07:00"), (-3450, 1900), 80, state="column"); go("fr167", D(6, "07:00"), D(6, "07:40"), [(-2600, 2100)], h=80)
go("fr167", D(6, "07:40"), D(6, "08:10"), [(-1750, 2380)], state="firing", moving="charge"); at("fr167", D(6, "08:45"), state="retreat")
go("fr167", D(6, "08:46"), D(6, "09:15"), [(-2600, 2000)], h=90, moving="retreat")
fire("g_jager", D(6, "08:10"), D(6, "08:30")); go("g_jager", D(6, "08:30"), D(6, "08:45"), [(-1700, 2380)], state="firing", moving="charge")
go("g_jager", D(6, "08:50"), D(6, "09:40"), [(-1000, 1550)], h=170)
go("fr167", D(6, "12:30"), D(6, "13:10"), [(-1800, 1300)], h=30)
# Five counter-attacks on the hill between nine and six, by the 12th Company of the 460th and the Jäger.
G12 = (-700, 1450)
for t in ("09:30", "12:30", "15:30"):
    go("g460_12", D(6, t), plus(D(6, t), 10), [(-650, 1150)], state="firing", moving="charge")
    go("g460_12", plus(D(6, t), 20), plus(D(6, t), 35), [G12], h=180, moving="retreat"); fire("m5_49", plus(D(6, t), 5), plus(D(6, t), 25))
for t in ("11:00", "14:30"):
    go("g_jager", D(6, t), plus(D(6, t), 12), [(-850, 1180)], state="firing", moving="charge")
    go("g_jager", plus(D(6, t), 20), plus(D(6, t), 40), [(-1000, 1550)], h=160, moving="retreat"); fire("m5_17", plus(D(6, t), 5), plus(D(6, t), 25)); fire("m5_67", plus(D(6, t), 5), plus(D(6, t), 25))
go("g460_1011", D(6, "21:30"), D(6, "22:00"), [(-400, 1650)], h=180); go("g460_12", D(6, "22:00"), D(6, "22:20"), [(-150, 1700)], h=180)

# ---- 6 June, 5 p.m.: into the wood and Bouresches ----
move("m5_2", D(6, "14:30"), [(-500, -700)], h=30)
move("m5_3", D(6, "16:20"), [(-80, 380)], h=80)
move("m6_8497", D(6, "16:10"), [(480, -1700)], h=30); move("m6_82", D(6, "16:30"), [(150, -1620)], h=40); move("m6_83", D(6, "16:35"), [(250, -1800)], h=40)
move("m6_96", D(6, "16:10"), [(1720, -1230)], h=40)
appear("eng_c", D(6, "16:00"), SOUTH(1500), 0, state="column"); move("eng_c", D(6, "16:01"), [(1600, -1450)], h=40)
go("m5_3", D(6, "17:00"), D(6, "17:15"), [(170, 360)], h=80, state="firing", moving="charge")
go("m5_3", D(6, "17:40"), D(6, "18:10"), [(330, 340)], h=80, state="firing", moving="charge"); at("m5_3", D(6, "18:40"), state="line")
fire("g461_1", D(6, "17:05"), D(6, "18:40"))
go("m6_82", D(6, "17:00"), D(6, "17:08"), [(380, -1440)], state="charge", moving="charge")
go("m6_82", D(6, "17:08"), D(6, "18:30"), [(500, -1250), (650, -1000)], state="firing", moving="charge"); at("m6_82", D(6, "20:30"), state="line")
go("m6_83", D(6, "17:00"), D(6, "17:40"), [(700, -1300)], state="charge", moving="charge")
go("m6_83", D(6, "17:40"), D(6, "19:20"), [(1300, -900), (1900, -600), (2140, -420)], state="firing", moving="charge")
go("m6_83", D(6, "19:50"), D(6, "20:30"), [(1900, -650)], h=30, moving="retreat")
go("m6_8497", D(6, "17:00"), D(6, "17:20"), [(900, -1350)], state="charge", moving="charge")
go("m6_8497", D(6, "17:20"), D(6, "18:30"), [(1400, -1000)], h=60, moving="charge")
go("m6_8497", D(6, "23:00"), D(6, "23:40"), [(2250, -680)], h=30)
fire("g461_2", D(6, "17:15"), D(6, "20:30"))
go("m6_96", D(6, "17:00"), D(6, "17:30"), [(1850, -1080)], state="firing", moving="charge")
go("m6_96", D(6, "19:00"), D(6, "19:30"), [(2080, -870)], state="firing", moving="charge"); at("m6_96", D(6, "20:00"), state="line")
fire("g398_out", D(6, "17:30"), D(6, "19:30"), state="retreat"); go("g398_out", D(6, "19:31"), D(6, "19:50"), [(2380, -520)], h=220, moving="retreat")
go("eng_c", D(6, "19:45"), D(6, "20:15"), [(2350, -1050)]); go("eng_c", D(6, "21:30"), D(6, "22:00"), [(2300, -1350)], h=60)
move("m6_2", D(6, "23:00"), [(1200, -1700), (1880, -1080)], h=30)
move("m5_2", D(6, "21:45"), TORCY_RD + [(-150, 750)], h=0)
move("m5_45", D(6, "20:00"), TORCY_RD + [(-350, 650)], h=0)  # its way up is not recorded; its losses fall on it
# The 23rd Infantry toward Hill 192, south-east of Triangle Farm, and the 47th's counter-attack at 8.14.
go("inf23", D(6, "18:30"), D(6, "19:10"), [(2300, -2350)], h=60, moving="charge")
appear("g47_1", D(6, "19:30"), (3450, -1500), 250, state="column"); go("g47_1", D(6, "19:30"), D(6, "20:00"), [(2750, -1600)], h=220)
fire("g47_1", D(6, "20:10"), D(6, "20:14")); go("g47_1", D(6, "20:14"), D(6, "20:22"), [(2400, -2200)], state="firing", moving="charge"); at("g47_1", D(6, "20:40"), state="line")
go("g47_1", D(6, "21:30"), D(6, "22:00"), [(2750, -1600)], h=220)
at("inf23", D(6, "20:22"), state="retreat"); go("inf23", D(6, "20:23"), D(6, "20:55"), [(1500, -2500)], h=40, moving="retreat")
appear("g6g_3", D(6, "22:00"), (3450, 300), 250, state="column"); go("g6g_3", D(6, "22:00"), D(6, "22:15"), [(2750, 150)], h=240)
appear("g6g_2", D(6, "22:00"), (3450, 600), 250, state="column"); go("g6g_2", D(6, "22:00"), D(6, "22:20"), [(2300, 450)], h=220)

# ---- 7 and 8 June: the engineers come up; the night attacks; the rocks of the south lobe ----
appear("eng_a", D(7, "01:20"), LUCY, 90, state="column"); go("eng_a", D(7, "01:20"), D(7, "02:00"), [(708, -1292), (1900, -1150), (2220, -980)], h=30)
appear("eng_b", D(7, "01:50"), LUCY, 90, state="column"); go("eng_b", D(7, "01:50"), D(7, "02:30"), [(380, -1400), (600, -1250)], h=30)
go("m5_45", D(7, "03:40"), D(7, "04:00"), [(-150, 1000)], h=0)
leave("g47_1", D(7, "22:50"), [(3450, -1600)])
move("m6_82", D(7, "22:50"), [(800, -1250), (1200, -1050)], h=340)
go("g6g_2", D(7, "23:30"), D(7, "23:45"), [(2200, -350)], state="firing", moving="charge"); at("g6g_2", D(7, "23:55"), state="rout")
go("g6g_2", D(7, "23:56"), D(8, "00:20"), [(2300, 450)], h=200, moving="rout")
fire("m6_83", D(7, "23:33"), D(7, "23:58")); fire("m6_8497", D(7, "23:35"), D(7, "23:55"))
go("g398_1", D(8, "00:15"), D(8, "00:25"), [(2450, -1350)], state="firing", moving="charge"); at("g398_1", D(8, "00:35"), state="rout")
go("g398_1", D(8, "00:36"), D(8, "01:00"), [(2700, -1000)], h=230, moving="rout")
fire("eng_c", D(8, "00:17"), D(8, "00:37")); fire("inf23", D(8, "00:17"), D(8, "00:37"))
go("g398_3", D(8, "01:25"), D(8, "01:35"), [(2180, -700)], state="firing", moving="charge"); at("g398_3", D(8, "02:00"), state="rout")
go("g398_3", D(8, "02:01"), D(8, "02:20"), [(2350, -450)], h=220, moving="rout")
for id in ("m6_96", "eng_a", "m6_2", "m6_8497"): fire(id, D(8, "01:27"), D(8, "02:00"))
move("m6_83", D(8, "02:45"), [(1300, -1000), (750, -1200)], h=0)
smoke((900, -850), D(8, "03:45"), D(8, "04:00"), rate=12, spread=300)
for id, p in (("m6_82", (1100, -720)), ("m6_83", (760, -880)), ("eng_b", (560, -960))):
    go(id, D(8, "04:00"), D(8, "04:30"), [p], h=0, state="firing", moving="charge"); at(id, D(8, "06:00"), state="line")
fire("g461_2", D(8, "04:05"), D(8, "05:00")); go("g461_2", D(8, "05:00"), D(8, "05:15"), [(980, -860)], state="firing", moving="charge")
go("g461_2", D(8, "05:40"), D(8, "06:00"), [(850, -800)], h=190, moving="retreat")
go("m6_82", D(8, "06:01"), D(8, "06:20"), [(1150, -900)], h=340, moving="retreat")
for id, p in (("m6_82", (1200, -1150)), ("m6_83", (800, -1350)), ("eng_b", (600, -1300))): go(id, D(8, "11:00"), D(8, "11:30"), [p], h=0, moving="retreat")
# The night of the 8th: the wood is left to the guns; 3/6 and the engineers go back to the Bois de Platière. The
# 398th and the 6th Grenadiers give way to the 109th Grenadiers, the 197th Division to the 5th Guard.
leave("m6_82", D(8, "22:00"), [(800, -2000), SOUTH(-800)]); leave("m6_83", D(8, "22:05"), [(500, -2000), SOUTH(-700)])
leave("m6_8497", D(8, "22:10"), [(1200, -1700), (600, -2200), SOUTH(-600)]); leave("eng_b", D(8, "22:15"), [(300, -2000), SOUTH(-500)]); leave("eng_c", D(8, "22:15"), [SOUTH(2000)])
for id, p in (("g398_3", (3450, 200)), ("g398_out", (3450, 0)), ("g398_1", (3450, -800)), ("g6g_2", (3450, 700)), ("g6g_3", (3450, 400))): leave(id, D(8, "23:00"), [p])
leave("g273", D(8, "22:00"), [(-1900, 3450)]); leave("g_jager", D(8, "22:00"), [(-1100, 3450)])
appear("g109", D(8, "23:30"), (3450, 100), 250, state="column"); go("g109", D(8, "23:30"), D(9, "00:10"), [(2400, -300)], h=220)
appear("g20", D(8, "22:30"), (-2600, 3450), 180, state="column"); go("g20", D(8, "22:30"), D(9, "00:00"), [(-2600, 2300), (-2500, 1600)], h=160)

# ---- 9 June: the guns on the wood; the French at Bussiares ----
for p in ((500, 300), (900, 600), (800, -700), (1200, 0), (600, -1100)): smoke(p, D(9, "04:00"), D(10, "04:30"), rate=12, spread=500)
go("fr167", D(9, "03:40"), D(9, "04:10"), [(-2350, 1600)], state="firing", moving="charge"); at("fr167", D(9, "04:40"), state="line")
fire("g20", D(9, "03:45"), D(9, "04:30")); go("g20", D(9, "04:40"), D(9, "05:20"), [(-1750, 2500)], h=200, moving="retreat")
go("fr167", D(9, "07:40"), D(9, "08:30"), [(-1850, 2350)], state="firing", moving="charge")
go("g460_2", D(9, "08:30"), D(9, "08:45"), [(-1650, 2280)], state="firing", moving="charge"); at("g460_2", D(9, "09:00"), state="line")
at("fr167", D(9, "08:50"), state="retreat"); go("fr167", D(9, "08:51"), D(9, "09:10"), [(-2000, 2350)], h=90, state="firing", moving="retreat")
at("fr167", D(9, "09:40"), state="line"); at("fr167", D(9, "15:30"), state="retreat"); go("fr167", D(9, "15:31"), D(9, "16:00"), [(-2350, 1550)], h=60, moving="retreat")
go("g20", D(9, "22:00"), D(9, "23:00"), [(-1600, 3150)], h=180)
# The night of the 9th: two companies of 1/5 relieve 2/6 in Bouresches; the 2/40th takes over the east half of the wood.
move("m5_17", D(9, "21:30"), [(-200, -700), (708, -1292), (1900, -1000), (2100, -800)], h=0)
move("m5_66", D(9, "21:35"), [(-300, -600), (708, -1292), (1900, -1000), (2000, -920)], h=20)
leave("m6_2", D(9, "23:00"), [(1200, -1700), SOUTH(1100)]); leave("m6_96", D(9, "23:05"), [(1300, -1700), SOUTH(1300)])
leave("eng_a", D(10, "01:25"), [(1900, -1000), (708, -1292), LUCY, SOUTH(-100)])
appear("g40_2", D(10, "00:40"), BELLEAU, 160, state="column"); go("g40_2", D(10, "00:40"), D(10, "01:20"), [(1300, 700), (1050, -450)], h=200)
go("g461_2", D(10, "01:20"), D(10, "01:50"), [(850, 350)], h=190)

# ---- 10 June, 4.30 a.m.: 1/6 behind the rolling barrage ----
move("m6_1", D(10, "03:40"), [(420, -1480)], h=40)
A0, A1 = (420, -1480), (900, -800); Lb = math.dist(A0, A1); ub = ((A1[0] - A0[0]) / Lb, (A1[1] - A0[1]) / Lb); d, t = 150, D(10, "04:30")
while d < Lb + 100:
    smoke((round(A0[0] + d * ub[0]), round(A0[1] + d * ub[1])), t, plus(t, 2), rate=14, spread=400); d, t = d + 100, plus(t, 2)
go("m6_1", D(10, "04:30"), D(10, "05:10"), [(780, -950)], h=35, state="firing", moving="charge"); at("m6_1", D(10, "05:40"), state="line")
fire("g40_2", D(10, "04:35"), D(10, "05:20")); fire("g461_1", D(10, "04:40"), D(10, "05:10"))

# ---- 11 June, 4.30 a.m.: Wise across the wood ----
move("m5_2", D(11, "03:30"), [(220, -40)], h=90); move("m5_51", D(11, "03:20"), [(-300, -100), (220, -260)], h=90)
for p in ((600, 200), (1100, 100), (900, -400)): smoke(p, D(11, "03:25"), D(11, "04:30"), rate=10, spread=500)
go("m5_2", D(11, "04:30"), D(11, "04:50"), [(560, 60)], h=80, state="firing", moving="charge")
go("m5_2", D(11, "05:00"), D(11, "06:00"), [(1000, 200), (1450, 330)], h=80, moving="charge")
go("m5_51", D(11, "04:30"), D(11, "05:00"), [(700, -180)], h=95, state="firing", moving="charge")
go("m5_51", D(11, "05:00"), D(11, "05:40"), [(1300, -300)], h=100, state="firing", moving="charge"); at("m5_51", D(11, "06:30"), state="line")
fire("g461_1", D(11, "04:32"), D(11, "04:50"), state="rout"); go("g461_1", D(11, "04:51"), D(11, "05:20"), [(700, 750)], h=200, moving="rout")
fire("g40_2", D(11, "05:05"), D(11, "05:40"), state="rout"); go("g40_2", D(11, "05:41"), D(11, "06:20"), [(1900, 400)], h=60, moving="rout")
go("m6_1", D(11, "05:00"), D(11, "06:00"), [(1150, -700)], h=40, state="firing", moving="charge"); at("m6_1", D(11, "06:30"), state="line")
appear("g_rav", D(11, "05:20"), (2900, 600), 220, state="column"); go("g_rav", D(11, "05:20"), D(11, "05:55"), [(2250, 100)], h=200)
go("g_rav", D(11, "05:55"), D(11, "06:05"), [(2150, -450)], state="firing", moving="charge"); at("g_rav", D(11, "06:08"), state="rout")
go("g_rav", D(11, "06:09"), D(11, "06:40"), [(2900, 550)], h=50, moving="rout"); hide("g_rav", D(11, "06:41"))
smoke((2200, -200), D(11, "05:57"), D(11, "06:15"), rate=20, spread=400)
fire("m5_17", D(11, "05:58"), D(11, "06:15")); fire("m5_66", D(11, "05:58"), D(11, "06:15"))
# Noon: Hartlieb takes back the west half; the 1/40th and 2/110th push the Marines back from the east edge.
move("g462", D(11, "09:00"), [P['brusses']], h=200)
go("g461_1", D(11, "11:30"), D(11, "12:00"), [(520, 250)], state="firing", moving="charge"); at("g461_1", D(11, "12:30"), state="line")
fire("m5_3", D(11, "11:35"), D(11, "12:15"))
appear("g40_1", D(11, "10:30"), (2300, 700), 260, state="column"); go("g40_1", D(11, "10:30"), D(11, "10:40"), [(1900, 650)], h=250)
go("g40_1", D(11, "11:00"), D(11, "11:15"), [(1650, 480)], state="firing", moving="charge"); at("g40_1", D(11, "12:00"), state="line")
fire("m5_2", D(11, "11:02"), D(11, "11:14")); go("m5_2", D(11, "11:15"), D(11, "11:45"), [(1300, 280)], h=80, moving="retreat")
appear("g110_2", D(11, "13:40"), (2300, 500), 260, state="column"); go("g110_2", D(11, "13:40"), D(11, "13:50"), [(1900, 450)], h=250)
go("g110_2", D(11, "14:00"), D(11, "14:20"), [(1550, 380)], state="firing", moving="charge"); at("g110_2", D(11, "14:45"), state="line")
fire("m5_2", D(11, "14:05"), D(11, "14:19")); go("m5_2", D(11, "14:20"), D(11, "14:50"), [(1150, 250)], h=80, moving="retreat")
move("eng_d", D(11, "16:20"), [(-150, 700), (180, 100), (1000, 180)], h=80)
appear("eng_f", D(11, "16:00"), SOUTH(-400), 0, state="column"); move("eng_f", D(11, "16:01"), [(-200, -700), (180, -100), (950, 0)], h=80)
TINTS = [dict(color="rgba(225,228,232,0.35)", **{"from": D(11, "04:00"), "until": D(11, "06:30")})]  # morning mist

# ---- 12 June: the old line retaken, then the north-east of the wood ----
go("g110_2", D(12, "04:30"), D(12, "05:01"), [(1000, 260)], state="firing", moving="charge"); at("g110_2", D(12, "05:30"), state="line")
go("g40_1", D(12, "04:30"), D(12, "05:01"), [(1250, 420)], state="firing", moving="charge"); at("g40_1", D(12, "05:30"), state="line")
go("m5_2", D(12, "04:30"), D(12, "05:00"), [(800, 150)], h=80, moving="retreat"); go("m5_51", D(12, "04:30"), D(12, "05:00"), [(900, -150)], h=80, moving="retreat")
go("eng_d", D(12, "04:30"), D(12, "05:00"), [(780, 60)], h=80, moving="retreat"); go("eng_f", D(12, "04:30"), D(12, "05:00"), [(850, -80)], h=80, moving="retreat")
for p in ((500, 300), (900, 300), (1200, 100), (800, -300)): smoke(p, D(12, "12:30"), D(12, "16:30"), rate=16, spread=500)
smoke(BOURESCHES, D(12, "13:00"), D(13, "08:00"), rate=6, spread=300)
fire("g461_1", D(12, "15:00"), D(12, "15:30")); fire("m5_3", D(12, "15:00"), D(12, "15:30"))
for id, p in (("m5_2", (1350, 450)), ("m5_51", (1450, 200)), ("eng_d", (1100, 400)), ("eng_f", (1250, 100))):
    go(id, D(12, "16:30"), D(12, "17:10"), [p], h=60, state="firing", moving="charge"); at(id, D(12, "17:40"), state="line")
for id, p in (("g110_2", (2250, 400)), ("g40_1", (2200, 250))):
    fire(id, D(12, "16:32"), D(12, "16:50"), state="rout"); go(id, D(12, "16:51"), D(12, "17:20"), [p], h=250, moving="rout")
go("g461_2", D(12, "16:40"), D(12, "17:00"), [P['pavilion']], h=180, moving="retreat")
go("g461_2", D(12, "17:45"), D(12, "18:00"), [(820, 470)], state="firing", moving="charge"); at("g461_2", D(12, "18:30"), state="line")
go("g462", D(12, "16:40"), D(12, "17:30"), [(1100, 1200), (900, 700)], h=190)
go("g462", D(12, "17:45"), D(12, "18:00"), [(950, 520)], state="firing", moving="charge"); at("g462", D(12, "18:30"), state="line")
# Dusk: 3/6 relieves 1/5 north-east of Hill 142.
for id, t, x, p in (("m6_82", "20:40", -700, (-1000, 850)), ("m6_83", "20:45", -600, (-560, 960)), ("m6_8497", "20:50", -500, (-250, 950))):
    appear(id, D(12, t), SOUTH(x), 0, state="column"); move(id, plus(D(12, t), 1), [(x + 100, -700), p], h=0)
leave("m5_49", D(12, "21:50"), [(-500, -700), SOUTH(-600)]); leave("m5_67", D(12, "21:50"), [(-700, -700), SOUTH(-700)])

# ---- 13 June: the Baden division's attack ----
appear("m6_2", D(13, "01:00"), SOUTH(-300), 0, state="column"); move("m6_2", D(13, "01:01"), [(-500, -700)], h=30)
appear("m6_96", D(13, "01:00"), SOUTH(-200), 0, state="column"); move("m6_96", D(13, "01:01"), [(-450, -800)], h=30)
for p in (BOURESCHES, (1300, -400), (800, -900)): smoke(p, D(13, "02:00"), D(13, "02:30"), rate=16, spread=400)
smoke(P['torcy'], D(13, "03:45"), D(13, "04:30"), rate=10, spread=400)
go("g109", D(13, "02:30"), D(13, "02:50"), [(2130, -760)], state="firing", moving="charge"); at("g109", D(13, "04:00"), state="rout")
go("g109", D(13, "04:01"), D(13, "04:30"), [(2450, -250)], h=40, moving="rout")
go("g110_2", D(13, "02:30"), D(13, "02:50"), [(1700, -50)], state="firing", moving="charge"); at("g110_2", D(13, "04:00"), state="rout")
go("g110_2", D(13, "04:01"), D(13, "04:30"), [(2250, 400)], h=60, moving="rout")
go("g40_1", D(13, "02:30"), D(13, "02:50"), [(1800, 100)], state="firing", moving="charge"); at("g40_1", D(13, "04:00"), state="rout")
go("g40_1", D(13, "04:01"), D(13, "04:30"), [(2200, 250)], h=60, moving="rout")
for id in ("m5_17", "m5_66", "m5_2", "m5_51", "m6_1"): fire(id, D(13, "02:50"), D(13, "04:00"))
# A false report that Bouresches had fallen sends the 78th and 96th Companies 2 km in open order to the woods south-east of Lucy.
move("m6_96", D(13, "07:20"), [(1000, -1700)], h=40, moving="charge", kmh=3); move("m6_2", D(13, "07:20"), [(1150, -1650)], h=40, moving="charge", kmh=3)

# ---- 14 June: gas; 2/6 relieves 2/5, then falls back to Hill 181 ----
TINTS.append(dict(color="rgba(214,222,150,0.28)", **{"from": D(13, "23:00"), "until": D(14, "18:00")}))  # mustard gas
move("m6_2", D(14, "01:15"), [(1300, -800), (1350, 400)], h=60); move("m6_96", D(14, "01:15"), [(1200, -800), (1400, 200)], h=80)
move("m5_2", D(14, "02:10"), [(900, -300), (400, -1300), (-500, -700)], h=30); move("m5_51", D(14, "02:15"), [(900, -400), (400, -1300), (-600, -750)], h=30)
leave("eng_d", D(14, "02:30"), [(400, -1300), SOUTH(-100)]); leave("eng_f", D(14, "02:30"), [(450, -1350), SOUTH(0)])
move("m6_2", D(14, "16:50"), [(900, -300), (-50, -650)], h=30); move("m6_96", D(14, "16:50"), [(900, -400), (-150, -720)], h=30)

# ---- 15 to 19 June: the French and the 7th Infantry take over; the 87th Division relieves the 237th ----
appear("fr174", D(15, "21:00"), (-3450, 300), 80, state="column"); move("fr174", D(15, "21:01"), [(-2000, 300), (-560, 980)], h=0)
leave("m6_82", D(15, "22:00"), [(-700, -700), SOUTH(-800)]); leave("m6_83", D(15, "22:05"), [(-500, -700), SOUTH(-700)]); leave("m6_8497", D(15, "22:10"), [(-300, -700), SOUTH(-600)])
appear("inf7_1", D(15, "21:00"), SOUTH(-200), 0, state="column"); move("inf7_1", D(15, "21:01"), [(-60, -1700), (121, -554), (157, -58), (330, 340)], h=80)
leave("m5_3", D(15, "22:10"), [(157, -58), (121, -554), (-60, -1700), SOUTH(-150)]); leave("m5_45", D(15, "22:00"), [(-100, -600), SOUTH(-250)])
for id, p in (("g461_1", [(400, 1300), (300, 3450)]), ("g461_2", [(900, 1300), (800, 3450)]), ("g462", [(1100, 1300), (1200, 3450)]),
              ("g460_2", [(-1600, 3450)]), ("g460_1011", [(-450, 3450)]), ("g460_12", [(-100, 3450)])): leave(id, D(16, "22:00"), p)
appear("g347_1", D(16, "22:00"), (1100, 3450), 180, state="column"); go("g347_1", D(16, "22:00"), D(16, "23:30"), [(1050, 1300), (850, 760)], h=190)
appear("g347_3", D(16, "22:00"), (600, 3450), 180, state="column"); go("g347_3", D(16, "22:00"), D(16, "23:30"), [(500, 1300), (600, 650)], h=200)
appear("g345", D(16, "22:00"), (-400, 3450), 180, state="column"); go("g345", D(16, "22:00"), D(16, "23:00"), [(-300, 1650)], h=190)
for id, p in (("g40_1", (3450, 400)), ("g110_2", (3450, 550)), ("g109", (3450, 0)), ("g40_2", (3450, 300))): leave(id, D(16, "23:00"), [p])
appear("inf7_2", D(16, "21:30"), SOUTH(0), 0, state="column"); move("inf7_2", D(16, "21:31"), [(-60, -1700), (-60, -700)], h=30)
leave("m6_2", D(16, "22:20"), [(-150, -1700), SOUTH(-50)]); leave("m6_96", D(16, "22:25"), [(-250, -1700), SOUTH(-150)])
appear("inf7_3", D(16, "21:30"), SOUTH(1300), 0, state="column"); move("inf7_3", D(16, "21:31"), [(1300, -1700), (2050, -850)], h=20)
leave("m5_17", D(16, "22:30"), [(1300, -1700), SOUTH(1200)]); leave("m5_66", D(16, "22:35"), [(1250, -1700), SOUTH(1100)])
leave("m5_2", D(16, "22:00"), [SOUTH(-500)]); leave("m5_51", D(16, "22:00"), [SOUTH(-600)])
move("inf7_2", D(18, "22:00"), [(400, -1450), (1050, -750)], h=30); leave("m6_1", D(18, "22:40"), [(400, -1450), SOUTH(300)])

# ---- 20 and 21 June: the 7th Infantry against the north end ----
go("inf7_1", D(20, "03:50"), D(20, "04:10"), [(560, 540)], h=40, state="firing", moving="charge"); at("inf7_1", D(20, "04:30"), state="retreat")
go("inf7_1", D(20, "04:31"), D(20, "05:00"), [(330, 340)], h=40, moving="retreat"); fire("g347_3", D(20, "03:52"), D(20, "04:30"))
smoke((650, 650), D(21, "03:00"), D(21, "03:15"), rate=12, spread=400)
go("inf7_1", D(21, "03:15"), D(21, "03:35"), [(560, 540)], h=40, state="firing", moving="charge"); at("inf7_1", D(21, "04:00"), state="retreat")
go("inf7_1", D(21, "04:01"), D(21, "04:20"), [(330, 340)], h=40, moving="retreat"); fire("g347_3", D(21, "03:20"), D(21, "04:00"))
go("g347_3", D(22, "21:00"), D(22, "21:30"), [(700, 1150)], h=180)

# ---- 22 and 23 June: the Marines come back; Shearer's first attack ----
for id, t, x, p in (("m6_82", "21:00", 800, (1150, -700)), ("m6_83", "21:05", 900, (1300, -500)), ("m6_8497", "21:10", 700, (1000, -900))):
    appear(id, D(22, t), SOUTH(x), 0, state="column"); move(id, plus(D(22, t), 1), [(x + 100, -1700), p], h=20)
leave("inf7_2", D(22, "22:00"), [(700, -1700), SOUTH(600)])
appear("m5_3", D(22, "21:00"), SOUTH(-200), 0, state="column"); move("m5_3", D(22, "21:01"), [(-60, -1700), (121, -554), (157, -58), (330, 340)], h=80)
leave("inf7_1", D(22, "22:10"), [(157, -58), (121, -554), (-60, -1700), SOUTH(-300)])
appear("m5_45", D(22, "21:00"), SOUTH(-400), 0, state="column"); move("m5_45", D(22, "21:01"), [(-400, -1500), (-300, 1050)], h=0)
leave("inf7_3", D(22, "23:00"), [(1300, -1700), SOUTH(1300)])
for id, x, p in (("m6_2", -400, (-500, -700)), ("m6_96", -300, (-400, -800)), ("m6_1", -600, (-700, -500))):
    appear(id, D(23, "01:00"), SOUTH(x), 0, state="column"); move(id, D(23, "01:01"), [p], h=30)
move("m5_3", D(23, "17:30"), [(600, 420)], h=10)
smoke((650, 700), D(23, "18:50"), D(23, "19:00"), rate=12, spread=400)
go("m5_3", D(23, "19:00"), D(23, "20:15"), [(640, 600)], h=10, state="firing", moving="charge"); at("m5_3", D(23, "20:45"), state="line")
fire("g347_1", D(23, "19:00"), D(23, "20:45"))
go("g345", D(23, "21:00"), D(23, "21:12"), [(-300, 1180)], state="firing", moving="charge"); at("g345", D(23, "21:20"), state="rout")
go("g345", D(23, "21:21"), D(23, "21:45"), [(-300, 1650)], h=180, moving="rout"); fire("m5_45", D(23, "21:02"), D(23, "21:20"))

# ---- 25 June: fourteen hours of fire, then the north end ----
for p in ((700, 750), (1000, 750), (850, 880)): smoke(p, D(25, "03:00"), D(25, "17:00"), rate=18, spread=400)
move("m6_83", D(25, "15:00"), [(1300, 450)], h=0)
go("m5_3", D(25, "17:00"), D(25, "17:30"), [(780, 760)], h=30, state="firing", moving="charge")
go("m5_3", D(25, "18:30"), D(25, "19:00"), [(850, 830)], h=30, state="firing", moving="charge")
go("m5_3", D(25, "19:30"), D(25, "20:00"), [(880, 880)], h=20, state="firing", moving="charge"); at("m5_3", D(25, "20:30"), state="line")
go("m6_83", D(25, "17:00"), D(25, "17:30"), [(1250, 700)], h=330, state="firing", moving="charge")
go("m6_83", D(25, "19:30"), D(25, "20:00"), [(1150, 820)], h=330, state="firing", moving="charge"); at("m6_83", D(25, "20:30"), state="line")
fire("g347_1", D(25, "17:02"), D(25, "17:30"), state="retreat"); go("g347_1", D(25, "17:31"), D(25, "17:50"), [(950, 950)], state="firing", moving="retreat")
go("g347_1", D(25, "18:12"), D(25, "18:40"), [(900, 850)], h=190, state="firing", moving="charge"); at("g347_1", D(25, "19:38"), state="rout")
go("g347_1", D(25, "19:40"), D(25, "21:15"), [(700, 1270)], h=180, moving="rout")
appear("g347_pow", D(25, "19:45"), (880, 850), 200, state="surrender")
hide("g347_pow", plus(move("g347_pow", D(25, "19:46"), [(400, 300), (157, -58), (11, -257), (121, -554), (-17, -1009), (-60, -1380)], state="surrender", moving="surrender", kmh=3), 1))
go("g347_3", D(25, "20:50"), D(25, "21:00"), [(700, 950)], state="firing", moving="charge"); at("g347_3", D(25, "21:05"), state="retreat")
go("g347_3", D(25, "21:06"), D(25, "21:25"), [(700, 1150)], h=180, moving="retreat"); fire("m5_3", D(25, "20:52"), D(25, "21:05"))
appear("g3e", D(25, "20:30"), (1250, 2300), 200, state="column"); go("g3e", D(25, "20:30"), D(25, "21:15"), [(950, 1200)], h=180)
TINTS.append(dict(color="rgba(225,228,232,0.35)", **{"from": D(25, "17:30"), "until": D(25, "19:00")}))  # the heavy mist

# ---- losses: (from, until, men) per unit, falling evenly through each span ----
# Recorded: the brigade's 31 officers and 1,056 men on 6 June, 1/5's 14 officers and 318, the 51st Company's 46, 3/6's
# nearly 400 by 8 June, 700 gas cases on 13/14 June, 3/5's 130 on 23 June and about 250 on 25/26 June, the 1/7th's 63 and
# over 200, Company D's 11 and 40 to 50 gassed; the German divisions' daily losses from Otto. How they are shared among
# the units of a division, and every loss not in that list (the 197th's at Les Mares Farm and on Hill 142, 2/5's and 1/6's
# from 10 to 12 June, the ravine battalion's), is inferred.
def S(day, a, b, n, day2=None): return (D(day, a), D(day2 or day, b), n)
LOSS = {
    "m5_49": [S(6, "03:47", "10:00", 120)], "m5_67": [S(6, "03:47", "07:00", 110)], "m5_66": [S(6, "05:10", "17:00", 52), S(14, "00:00", "12:00", 25)],
    "m5_17": [S(6, "05:36", "17:00", 50), S(14, "00:00", "12:00", 25)], "m5_51": [S(6, "06:40", "18:00", 46), S(11, "04:30", "05:40", 50), S(12, "16:30", "17:10", 30), S(14, "00:00", "12:00", 30)],
    "m5_45": [S(6, "20:00", "21:30", 73)],
    "m5_3": [S(6, "17:02", "18:40", 250), S(23, "19:00", "20:45", 130), S(25, "17:00", "21:00", 250)],
    "m6_82": [S(6, "17:00", "20:30", 90), S(8, "04:00", "06:20", 80)], "m6_83": [S(6, "17:10", "20:30", 60), S(8, "04:00", "06:00", 70), S(25, "17:00", "20:00", 20)],
    "m6_8497": [S(6, "17:05", "18:30", 66), S(7, "23:30", "02:00", 34, 8)],
    "m6_96": [S(6, "17:00", "19:40", 160), S(14, "02:30", "16:00", 60)], "m6_2": [S(14, "02:30", "16:00", 240)],
    "m5_2": [S(11, "04:30", "07:00", 200), S(12, "16:30", "17:40", 100), S(14, "00:00", "12:00", 120)],
    "m6_1": [S(10, "04:30", "05:40", 60), S(11, "05:00", "06:30", 90), S(14, "00:00", "18:00", 200)],
    "eng_d": [S(6, "06:00", "18:00", 11, 12), S(13, "23:00", "02:00", 45, 14)],
    "inf7_1": [S(20, "03:52", "04:30", 63), S(21, "03:20", "04:20", 210)],
    "g460_9": [S(6, "03:47", "04:05", 120)], "g462_10": [S(6, "03:50", "04:03", 90), S(6, "04:18", "04:19", 30)],
    "g460_12": [S(6, "09:30", "17:00", 40), S(10, "04:30", "10:00", 38)], "g460_1011": [S(6, "03:50", "21:30", 30), S(8, "04:00", "12:00", 39)],
    "g460_2": [S(7, "06:00", "20:00", 30), S(9, "08:30", "10:00", 69), S(11, "06:00", "18:00", 41), S(13, "02:30", "12:00", 47)],
    "g461_1": [S(6, "17:05", "18:40", 50), S(7, "06:00", "20:00", 30), S(8, "04:00", "09:00", 40), S(9, "06:00", "20:00", 60), S(10, "04:30", "06:00", 40),
               S(11, "04:32", "05:20", 100), S(12, "15:00", "23:20", 12), S(13, "02:30", "06:00", 20), S(15, "06:00", "20:00", 30)],
    "g461_2": [S(6, "17:15", "20:30", 41), S(7, "06:00", "20:00", 25), S(8, "04:00", "06:00", 110), S(9, "06:00", "20:00", 60), S(10, "04:30", "05:20", 40),
               S(11, "05:00", "07:00", 20), S(12, "16:30", "18:30", 50), S(13, "02:30", "06:00", 30), S(15, "06:00", "20:00", 25)],
    "g462": [S(9, "06:00", "20:00", 80), S(10, "06:00", "20:00", 60), S(11, "12:00", "18:00", 70), S(12, "17:45", "18:30", 63), S(13, "02:30", "06:00", 57), S(15, "06:00", "20:00", 20)],
    "g109": [S(9, "06:00", "20:00", 54), S(10, "06:00", "20:00", 184), S(11, "05:55", "07:00", 49), S(12, "13:00", "20:00", 56), S(13, "02:30", "05:00", 250)],
    "g40_2": [S(10, "01:20", "05:20", 250), S(11, "05:05", "05:40", 280)],
    "g40_1": [S(11, "11:00", "12:00", 120), S(12, "04:30", "05:01", 75), S(12, "16:32", "16:50", 75), S(13, "02:30", "04:30", 47)],
    "g110_2": [S(11, "14:00", "14:45", 120), S(12, "04:30", "05:01", 75), S(12, "16:32", "16:50", 75), S(13, "02:30", "05:00", 120)],
    "g398_out": [S(6, "17:30", "19:50", 60), S(7, "06:00", "20:00", 27)], "g398_3": [S(6, "17:00", "23:00", 30), S(7, "06:00", "20:00", 30)],
    "g398_1": [S(6, "17:00", "23:00", 21)], "g47_1": [S(6, "20:14", "20:40", 40)], "g6g_2": [S(7, "23:30", "23:59", 40)],
    "g273": [S(3, "16:00", "16:40", 300), S(6, "03:55", "08:15", 418)], "g_jager": [S(6, "11:00", "15:00", 150)], "g20": [S(9, "03:45", "04:30", 89)],
    "g_rav": [S(11, "06:00", "06:30", 250)], "g347_1": [S(25, "17:30", "19:45", 440)],
}
def lost(ids, day): return sum(n for id in ids for t0, _, n in LOSS.get(id, []) if t0.startswith(D(day, "")))
MARINES = [r[0] for r in OOB if r[0].startswith("m")]
assert lost(MARINES, 6) + 10 == 1087, "the brigade's 31 officers and 1,056 men on 6 June: the 8th MG Company's 10 are not drawn"
assert lost(["m5_17", "m5_49", "m5_66", "m5_67"], 6) == 332, "1/5's 14 officers and 318 men"
assert lost(["m6_82", "m6_83", "m6_8497"], 6) + lost(["m6_82", "m6_83", "m6_8497"], 7) + lost(["m6_82", "m6_83", "m6_8497"], 8) == 400, "3/6, nearly 400 by 8 June"
assert lost(MARINES, 14) == 700, "700 gas cases in 24 hours"
G237 = ["g460_9", "g460_1011", "g460_12", "g460_2", "g461_1", "g461_2", "g462", "g462_10"]
for day, n in ((6, 401), (7, 85), (8, 189), (9, 269), (10, 178), (11, 231), (12, 125), (13, 154), (15, 75)): assert lost(G237, day) == n, ("the 237th Division", day)
for day, n in ((9, 54), (10, 434), (11, 569), (12, 356), (13, 417)): assert lost(["g40_1", "g40_2", "g110_2", "g109"], day) == n, ("the 28th Division", day)
for day, n in ((6, 151), (7, 97)): assert lost(["g398_out", "g398_3", "g398_1", "g47_1", "g6g_2", "g6g_3"], day) == n, ("the 10th Division", day)
def pose(id, t):  # where a unit is at time t between its keys
    ks = KEYS[id]; a = max((k for k in ks if sec(k["t"]) <= sec(t)), key=lambda k: sec(k["t"])); b = next((k for k in ks if sec(k["t"]) > sec(t)), None)
    if b is None: return (a["x"], a["y"])
    f = (sec(t) - sec(a["t"])) / (sec(b["t"]) - sec(a["t"])); return (a["x"] + f * (b["x"] - a["x"]), a["y"] + f * (b["y"] - a["y"]))
def state_at(id, t): return next((k["state"] for k in reversed(KEYS[id]) if sec(k["t"]) <= sec(t) and "state" in k), None)
def curve(pts, base):  # strength at a time, falling linearly through each span of losses
    def f(s):
        if s <= pts[0][0]: return base
        for (s0, v0), (s1, v1) in zip(pts, pts[1:]):
            if s0 <= s <= s1: return v1 if s1 == s0 else round(v0 + (s - s0) / (s1 - s0) * (v1 - v0))
        return pts[-1][1]
    return f
for id, spans in LOSS.items():
    cur, pts = BASE[id][6], []
    for t0, t1, n in spans:
        assert state_at(id, t0) not in (None, "hidden") and state_at(id, t1) not in (None, "hidden"), (id, t0, t1, "losses while off the map")
        pts += [(sec(t0), cur), (sec(t1), cur - n)]; cur -= n
    assert cur >= 0, (id, cur)
    s_at = curve(pts, BASE[id][6])
    have = {k["t"] for k in KEYS[id]}
    for s, _ in pts:
        t = fmt(s)
        if t not in have: KEYS[id].append(K(t, pose(id, t))); have.add(t)
    KEYS[id].sort(key=lambda k: sec(k["t"]))
    for k in KEYS[id]: k["strength"] = s_at(sec(k["t"]))
def strength(ids, t): return sum(next(k["strength"] for k in reversed(KEYS[id]) if sec(k["t"]) <= sec(t)) for id in ids)
T13 = D(13, "12:00")
assert strength(["g460_9", "g460_1011", "g460_12", "g460_2"], T13) == 596, "the 460th's 21 officers and 575 men on 13 June"
assert strength(["g461_1", "g461_2"], T13) == 441, "the 461st's 12 officers and 429 men"
assert strength(["g462", "g462_10"], T13) == 492, "the 462nd's 14 officers and 478 men"
assert strength(["m5_17", "m5_49", "m5_66", "m5_67"], D(6, "03:00")) == 975, "1/5's 22 officers and 953 men"

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

# ---- chapters: (time, title, text, camera centre, metres across, playback speed, when) ----
# `when` holds a clock time the sources record; without one the card gives the nearest hour. Where the American and
# German clocks disagree the caption gives the American records' time.
CHAPTERS = [
    (D(1, "14:00"), "Into the line", "On 31 May the 2nd Division, Major General Omar Bundy, embussed north-west of Paris; its orders changed four times, and the Marines unloaded along the Paris-Metz road at night. On 1 June the columns march at 4.30, and that afternoon the 6th Marines go into line along the Paris road under the French 43rd Division, deploying through the fields: 1/6 north-east of Lucy-le-Bocage, 2/6 from Triangle Farm to Lucy, 3/6 in reserve by La Voie du Châtel. Brigadier General James Harbord, commanding the 4th Brigade of Marines, reports to the French at Lucy, 'a fairly noisy town'. Château-Thierry falls that day.", [-300, -1900], 4600, 300, None),
    (D(2, "19:45"), "Cote 126", "In the night the 5th Marines came into line on the left, 2/5 at Les Mares Farm with two companies of 1/5, and the German 10th Division took Bouresches. At 8.10 on the evening of 2 June Germans come out of the woods between Licy and Torcy and take Cote 126; at 8.45 they cross south of the Belleau-Torcy road and push the French back. 'Bussiares, Torcy and the wood of Belleau have been taken from us during the evening,' the French report.", [-100, 1300], 4400, 120, "8.10 p.m."),
    (D(3, "11:30"), "The 237th Division", "At 11.30 on 3 June the German 237th Division attacks. Its 462nd Infantry comes on toward Hill 142 and Champillon and is stopped a kilometre south of Torcy. The 461st, under Major Hans Bischoff, 'a veteran in African bush and forest fighting', completes the occupation of the wood to its west edge, repulses a counter-attack at two and clears the south-west corner. At noon the 82nd Company of 3/6 goes into the line north-east of Champillon and loses four killed.", [-400, 600], 3600, 120, "11.30 a.m."),
    (D(3, "15:50"), "Retreat, hell", "In the afternoon Germans of the 197th Division come through the wheat toward Les Mares Farm. 2/5 holds its fire until they are within 100 yards, then stops them; the Marines' rifle fire reaches out to 800 yards. Captain Lloyd Williams of the 51st Company: 'Retreat, hell. We just got here.' At dark the 83rd Company of 3/6 joins the 82nd south of Torcy, 'in the same woods' as the Germans and about fifty yards from them.", [-2600, 900], 2800, 120, "in the afternoon"),
    (D(4, "08:00"), "Field Order No. 1", "At eight on 4 June the 2nd Division relieves the French 45th Division on the Champillon front. On the 5th General Degoutte ordered the French 167th Division to attack next morning, and the Americans to support it 'by the capture of the slopes of Champillon'; 'the Infantry will attack by infiltration rather than by waves.' The brigade's Field Order No. 1 sends 1/5, Major Julius Turrill, with two machine-gun companies, to seize Hill 142 at 3.45 on an 800 m front. The French relieve the Marine left only at three, 'instead of 9 o'clock last night'. The 49th Company reaches the jump-off on Hill 176 at 2.40, the 67th at 3.45. A battalion of the 23rd Infantry takes over 2/6's line at three.", [-1600, 100], 4400, 600, "8 a.m."),
    (D(6, "03:45"), "Hill 142", "At 3.15 the American guns open on the German positions. At 3.45 the 49th Company, Captain Hamilton, and the 67th, Captain Crowther, 11 officers and 475 men in four waves each, step off north from Hill 176 across 300 m of wheat. They are fired on after 18 m. The 9th Company of the 460th is overrun and fires a red rocket; the 67th is hit by the machine guns in the Champillon ravine; the 49th overruns the 10th Company of the 462nd and takes fire from the square woods. The 15th Machine Gun Company's ten guns at Champillon fire over their heads.", [-800, 850], 1900, 60, "3.45 a.m."),
    (D(6, "05:15"), "The rest of the battalion", "Gilfillan's platoon of the 66th Company arrives at 4.30 and goes forward, and the German 273rd Infantry reports both its flanks giving ground. The rest of the 66th, the 8th Machine Gun Company and Company D of the 2nd Engineers come up by 5.30, and the 17th Company, Captain Winans, goes in on the 49th's right at 5.37. At six Lieutenant Colonel Logan Feland asks for the open left flank to be covered, and the 51st Company of 2/5 is sent to Champillon and up the ravine at a right angle to the 67th. At 6.10 the German guns fall on Hill 142.", [-1300, 600], 3200, 120, "5.15 a.m."),
    (D(6, "07:00"), "Past the objective", "'Reached our objectives. We are throwing out strong points and are consolidating,' 1/5 reports at seven. Hamilton's 49th has run on past the objective through the square woods toward the road short of Bussiares, and three men get into Torcy; he brings the company back to the nose of Hill 142. At 7.30 an aviator reports that 'it is uncertain who holds Bois de Belleau'. On the left the French enter Bussiares at 8.10 and are thrown out at 8.45 by a Saxon Jäger battalion.", [-1300, 1600], 3400, 120, "7 a.m."),
    (D(6, "09:30"), "So far have held the hill", "At 9.50 Hamilton writes from 'the nose of Hill 142 and about 400 yds N.E. of square woods ... counter-attacked several times but so far have held the hill. Our casualties are very heavy.' Between nine and six the 12th Company of the 460th and the Jäger counter-attack five times. Janson (Hoffman) bayonets two of twelve Germans with five light machine guns 18 m from the line. The French come up on the left at 1.10. The 10th and 11th Companies of the 460th hold the square woods all day and slip away after dark without losing a gun. 1/5 loses 14 officers and 318 men; the 273rd Infantry 13 officers and 405.", [-800, 1250], 2600, 120, "9.50 a.m."),
    (D(6, "14:05"), "Field Order No. 2", "At 2.05 Harbord orders the wood taken in two phases: first the wood itself at five, 3/5 on the left and 3/6 on the right under Colonel Albertus Catlin of the 6th Marines, 2/6 conforming on the right; then the railway station, Bouresches, the brook crossing and Hills 126 and 133. 2/5 waits in reserve in the woods north-west of Lucy. There is to be no artillery preparation: the wood is thought to be lightly held. Catlin gets the order at 3.45 from Harbord's aide by motorcycle, and his company commanders are shown the map and led to the line.", [300, -800], 4400, 120, "2.05 p.m."),
    (D(6, "17:00"), "Through the wheat", "At five 3/5, Major Benjamin Berry, crosses 400 yards of wheat from the Lucy-Torcy road toward the west face of the wood in waves. 'Halfway across the wheat field, German machine guns and rifles opened up on the long, straight lines and mowed them down.' Berry is wounded. On the right 3/6 steps off from the ravine east of Lucy, the 82nd Company left and the 84th right, the 83rd and 97th behind, 200 yards from the southern tip of the wood. The 96th Company of 2/6 starts across 600 yards toward Bouresches; Captain Duncan is killed by a shell as it goes. First Sergeant Dan Daly: 'Do you want to live forever?' At 5.30 Catlin is shot through the chest watching 3/6 reach the wood, and Lieutenant Colonel Harry Lee takes the regiment.", [950, -650], 2600, 60, "5 p.m."),
    (D(6, "19:15"), "Bouresches", "At 7.15 an aviator sees 'advance elements about 400 meters southwest of Bouresches ... still fighting in the Bois de Belleau ... in the northern part of the attack I see absolutely nothing'. At 7.20 the 83rd Company is reported at the railway station, a claim doubted that night. At 7.30 the 96th enters Bouresches, 'making good use of the bed of a brook', and clears the 7th and 8th Companies of the 398th out house by house; the outpost falls back to the railway. Lieutenants Robertson and Clifton Cates hold the village with about 24 men. South-east of Triangle Farm the 23rd Infantry, attacking toward Hill 192, is driven back at 8.14 by the 1st Battalion of the 47th.", [1900, -1200], 2400, 120, "7.15 p.m."),
    (D(6, "21:40"), "Held up", "At 8.45 Major Berton Sibley reports 'Unable to advance infantry further ... Losses already heavy.' 3/6 has halted at the far edge of the wood near Bouresches, its 82nd Company held by machine-gun nests in the rocks. At 9.40 the division hears that the attack on the north edge is 'held up by machine gun nest', and Wise's three reserve companies go north on the Torcy road into the gap between Turrill and Berry. Major Thomas Holcomb asks for reinforcements for Bouresches; the 84th and 97th Companies march in from the field at 11.40 without resistance, and Lieutenant Moore and Sergeant Major Quick drive an ammunition truck into the village under flares. The 4th Brigade has lost 31 officers and 1,056 men in the day, 10 of them in the 8th Machine Gun Company.", [900, -300], 4200, 300, "9.40 p.m."),
    (D(7, "23:30"), "The night attack", "7 June is comparatively quiet; at four that morning the 45th Company came up on 1/5's right on Hill 142. At 11.30 that night the Germans attack 3/6 and, from the north, Bouresches, after heavy artillery and machine-gun fire; the 83rd Company on the east edge shoots the attack down with automatic rifles and captured guns. At 12.15 an attack on the 23rd Infantry's front is repulsed, and at 1.25 another on Bouresches, where 110 men of Company A, 2nd Engineers, are in the line.", [2150, -800], 2800, 120, "11.30 p.m."),
    (D(8, "04:00"), "The rocks", "At four on 8 June, after a Stokes-mortar bombardment, 3/6 attacks north through the south lobe, the 82nd Company on the right at the south-east corner and the 83rd on the left, with Company B of the engineers on a flank. The machine-gun nests are 'well fortified in the rocks ... one flanked the other'. Four guns are taken; the fighting goes on to 8.30, and by 11.30 the battalion is back under cover. The 461st's 6th and 8th Companies and the 365th Engineer Company throw back a break-in from the Bouresches side and take 40 prisoners. At 1.55 Sibley reports that 'officers and men are too much exhausted for further attack'. 3/6 has lost nearly 400 men.", [950, -950], 1800, 120, "4 a.m."),
    (D(8, "22:00"), "The guns", "That night 3/6 and the engineers are taken out and the wood is left to the artillery; they reach the Bois de Platière by daylight and get their first hot food since 31 May. The German 398th gives way to the 109th Grenadiers of the 28th (Baden) Division, and the 197th Division to the 5th Guard. On 9 June the American and French guns fire 28,000 75 mm and 6,000 155 mm shells into the wood. On the left the French 116th Infantry attacks Bussiares at 3.40, takes 4 officers and 85 men of the 20th Regiment in the triangular wood south-west of it and gets into the village at 8.30, but is thrown out by two companies of the 460th and holds the west houses only until 3.30.", [-1000, 900], 5600, 600, None),
    (D(10, "04:30"), "The rolling barrage", "In the night 1/5 relieved 2/6 in Bouresches, and the 2nd Battalion of the 40th Fusiliers took over the east half of the wood. At 4.30 on 10 June 1/6, Major John Hughes, attacks the south lobe behind the brigade's first rolling barrage, lifting every two minutes, two companies up and two in support, while twelve machine guns massed in Bouresches fire up the east flank. 'Objective reached by 5:10 and being consolidated ... two large Minenwerfers captured. Our losses slight.' Hughes has in fact got no further than 3/6's high-water mark of the 8th. Major Edward Cole of the 6th Machine Gun Battalion is mortally wounded.", [750, -950], 1800, 120, "4.30 a.m."),
    (D(11, "04:30"), "Wise across the wood", "At 3.25 on 11 June the American guns open up. At 4.30, in morning mist, 2/5, Lieutenant Colonel Frederic Wise, attacks from the west edge, east across the wood instead of north-east, while 1/6 renews the attack in the south. It breaks through the right of the 2/40th by the brook bed and takes its 5th, 7th and 8th Companies from flank and rear: 'Wo ist das Regiment 40?' The 1st and 4th Companies of the 461st are cut off, 3 officers and 80 men taken, and the rest fight their way north to Major Hartlieb. 1/6 clears the south half; Captains Burns and Fuller are killed. Captain Lloyd Williams is mortally wounded.", [800, 0], 2400, 120, "4.30 a.m."),
    (D(11, "05:55"), "The ravine north of Bouresches", "At 5.55 a German battalion forms in the ravine north of Bouresches and attacks 'en masse'. The first volley of the 2nd Battalion, 12th Field Artillery lands among it and the 155s finish it: 'great slaughter of fleeing Germans as they left the Bois de Belleau by our machine guns from a flank'. At seven: 'The northern half of the Bois de Belleau belongs to 5th Marines. 20 prisoners sent back.' By 10.40 the division has 3 officers and 169 men.", [1900, -100], 2600, 120, "5.55 a.m."),
    (D(11, "11:30"), "Hartlieb", "About noon Hartlieb's counter-attack regains the 461st's old position in the west half of the wood, and the 1st Battalion of the 462nd goes into the woods at Les Brusses. The German brigade orders the old line retaken 'at any cost'. On the east edge the 1st Battalion of the 40th counter-attacks 200 m, and the 2nd Battalion of the 110th Grenadiers, Mencke, another 200 m; they are exhausted by seven, and the Marine line has been pulled back a little. Companies D and F of the 2nd Engineers go to Wise, a platoon to each Marine company.", [1300, 450], 2200, 120, "about noon"),
    (D(12, "03:15"), "The old line", "At 3.15 on 12 June the 2/110th and part of the 1/40th renew the attack and reach 'the old line' at 5.01. In the afternoon the German guns put 'more than 80,000 shells in less than four hours' on the wood, and at one Bouresches is on fire.", [1100, 250], 2200, 120, "3.15 a.m."),
    (D(12, "16:30"), "Without artillery preparation", "Between four and five 2/5 attacks again, without artillery preparation. The 8th Company of the 461st is cut off, the 7th attacked from the rear and the north-east corner broken into; Bischoff pulls his 2nd Battalion back to the Pavilion hill, counter-attacks with its 5th and 7th Companies and two companies of the 462nd, and holds south of the Pavilion. On the Baden division's front the Americans, 'advancing in part in columns', break through at 4.30 and drive the 2/110th and 1/40th out of the wood to the Bouresches-Belleau road.", [1100, 450], 2600, 120, "4.30 p.m."),
    (D(12, "20:45"), "Relief at dusk", "At dusk 3/6, back from the Bois de Platière, relieves 1/5 north-east of Hill 142. At 11.20 that night an officer and 56 men of the 461st come in, 'some surrendered under a flag of truce', and say a fresh division attacks tonight. At 1.30 2/6 is ordered up to the woods north-west of Lucy as brigade reserve; a dying German officer tells them the attack will come at dawn.", [-500, 0], 4400, 600, "at dusk"),
    (D(13, "02:30"), "The Baden division", "At 2.30 on 13 June, after an intense barrage with gas, the 28th Division attacks Bouresches and the wood. At 4.30 Wise reports 'line appears to be holding ... Loss (German) must be very heavy'; at 5.05 Hughes: 'Everything O.K. now, Men digging in. Trenches badly ruined by shell fire. Casualties under 20%.' By 5.30 the attack is 'thoroughly broken with very severe losses'. The 1st Company of the 109th gets into Bouresches and leaves 'only dead and prisoners'. Later a false report that Bouresches has fallen sends the 78th and 96th Companies 2 km in open order to the woods south-east of Lucy.", [1800, -400], 2800, 120, "2.30 a.m."),
    (D(14, "02:00"), "Mustard gas", "In the night mustard gas falls on the south of the wood, Bouresches and Lucy. At two 2/6 relieves 2/5 in the wood and is gassed; by the next afternoon practically all of the 78th and 96th Companies have been evacuated, and there are 700 gas cases in 24 hours. At 4.50 that afternoon, with German troops coming into Torcy and Belleau in motor trucks and the wood 'heavily shelled with mustard gas', Harbord pulls the battalion back to Hill 181 and holds the east edge with 'a very thin line of machine guns'.", [600, -300], 3800, 300, "2 a.m."),
    (D(15, "21:00"), "The 7th Infantry", "On 15 June three battalions of the 7th Infantry, 3rd Division, are attached for seven days 'for the purpose of relieving battalions of the 4th Brigade which have been continually in front line positions for the last fourteen days'. In the next nights they relieve 3/5, 2/6 and 1/6 ('it was a mad house', in Cates's words), and the 1st Battalion of the French 174th Infantry relieves 3/6 north-east of Hill 142. Across the wood the German 87th Division, newly arrived, takes over from the 237th.", [100, 0], 5200, 600, None),
    (D(20, "03:50"), "The 7th Infantry attacks", "At 3.50 on 20 June the 1st Battalion of the 7th attacks the north end of the wood in strong lines of skirmishers, without special artillery support. It fails, with 63 casualties; the 3rd Battalion of the 347th finds 60 to 70 American dead. At 3.15 next morning, after a short barrage, Lieutenant Colonel Adams's battalion tries again. Two companies lose touch, the German counter-barrage and hidden machine guns catch it, and it is back in its positions by 7.30 with over 200 casualties.", [500, 500], 1800, 120, "3.50 a.m."),
    (D(22, "21:00"), "The Marines come back", "On 21 and 22 June the Marines come back into the line: 3/6 into the south-east corner of the wood in place of the 2nd Battalion of the 7th, and 3/5 into the north in place of the 1st, while wire is strung across the whole front. 2/6 and 1/6 go to the woods north-west of Lucy, and Company B of the 4th Machine Gun Battalion comes into the wood.", [300, -800], 5000, 600, None),
    (D(23, "19:00"), "Shearer's first attack", "At seven on the 23rd 3/5, now under Major Maurice Shearer, attacks the north end after a small barrage, with sharpshooter pairs, extra grenades and Company B of the 4th Machine Gun Battalion. It gains 200 yards against machine-gun nests that cover one another, loses 130 men in three hours, and stops at 11.20. At nine a German attack out of Torcy hits the Marine company south of the Torcy-Belleau road and is driven back.", [300, 900], 2600, 120, "7 p.m."),
    (D(25, "03:00"), "Fourteen hours", "From three in the morning of 25 June the 75s and 155s fire on the north-west corner of the wood for fourteen hours, and the German nests are 'knocked out or disorganized'. Otto has medium and heavy mine throwers falling on the 347th's part of the wood from four in the afternoon; its 3rd and 4th Companies, near the edge, suffer most, 'since the mines burst for the most part in the trees'.", [900, 800], 1800, 300, "3 a.m."),
    (D(25, "17:00"), "The assault", "At five 3/5 attacks, two platoons of the 83rd Company of 3/6 on its right, with two companies of the 4th Machine Gun Battalion and the 15th Company of the 6th. At 5.30 a heavy mist comes down over the area. The 1st Battalion of the 347th gives ground; at six Captain Kaulbars calls for his 3rd Battalion by radio and feeds his shock company into the line, and at 6.12 his battalion is 'again advancing on the woods'. At seven Shearer reports two companies on their objectives and about 150 prisoners: 'more prisoners are coming in now too fast to be counted'.", [950, 800], 1600, 120, "5 p.m."),
    (D(25, "19:30"), "Rolled up", "At 7.30 the Marines break in between the 347th's 3rd Company and what is left of its 4th, and roll both up against the 2nd and 5th; the captains of the 3rd and 4th are killed. 'Things are going O.K.,' Harbord reports at 8.15. At 8.50 a small counter-attack is repulsed. By 9.15 'only remnants of the five companies' are back along the Torcy-Belleau road, and two companies of the 3rd Ersatz Regiment go into Belleau. Prisoners say 'the reserves are in caves by the Chateau where the artillery can't reach them'.", [600, 400], 3200, 120, "7.30 p.m."),
    (D(26, "07:00"), "Woods now U.S. Marine Corps entirely", "'Woods now U.S. Marine Corps entirely,' Shearer reports at seven on 26 June. The division counts 7 officers and 302 men taken; the 347th's five companies lost 7 officers and 433 men, and 3/5 about 250. On 30 June Degoutte renames the wood the Bois de la Brigade de Marine. 'They have added the Bois de Belleau, Hill 142 and Bouresches to Mexico, China, Santo Domingo, Tripoli,' Harbord wrote of his Marines, and von Conta reported on 17 August: 'The 2nd American may be described as a very good division ... Our fire did not affect their morale.'", [700, 0], 4400, 60, "7 a.m."),
]
events = [dict(t=t, title=a, text=b, at=at_, view=v, speed=s, **({"when": w} if w else {})) for t, a, b, at_, v, s, w in CHAPTERS]
for e in events:  # without `when` the card speaks the nearest hour (app.js chapterWhen), so it must be near the frame's clock
    s = sec(e["t"]) % 86400; hh = [n % 12 or 12 for n in (int(s // 3600), int(s // 3600) + 1)]; num = re.search(r"\d+", e.get("when", ""))
    assert not num or int(num[0]) in hh, (e["t"], e["when"], "the card's hour is not the frame's")
    assert "when" in e or abs(s - math.floor(s / 3600 + 0.5) * 3600) <= 15 * 60, (e["t"], e["title"], "give it a when")
    assert e["speed"] in (1, 2, 5, 10, 20, 30, 60, 120, 300, 600, 1800, 3600, 7200), (e["title"], e["speed"], "not a speed the menu offers (sim.js SPEEDS)")
assert [sec(e["t"]) for e in events] == sorted(sec(e["t"]) for e in events)

OUTCOME = {"result": "American victory: the 4th Brigade took Hill 142, Bouresches and the whole of the wood, which the French renamed the Bois de la Brigade de Marine", "losses": [
    ["american", "The 4th Brigade lost 112 officers and 4,598 men in June, over 1,000 of them killed; 31 officers and 1,056 men fell on 6 June alone. Harbord counted some 3,400 killed and wounded by 2 July. The 2nd Division, with Vaux, lost 1,811 battle deaths and 7,252 other casualties from 31 May to 9 July. The 7th Infantry lost 63 men on 20 June and over 200 on the 21st. The map draws only the losses the sources give for the units on it."],
    ["german", "No total survives in the sources read. Otto gives the divisions' daily losses: the 237th 401 on 6 June alone, the 28th (Baden) 70 officers and 2,100 men from 27 May to 15 June, the 197th about 2,000 from 4 to 6 June; five companies of the 347th lost 7 officers and 433 men on 25 June. The brigade took more than 500 prisoners from 2 to 13 June. Estimates of over 10,000 German casualties are only estimates."]],
    "note": "The German records run an hour ahead of the American clock and are converted to it here. The hills, Triangle Farm and positions inside the wood day by day are placed from the text, not from a map of 1918; the strengths of the French and of most German battalions are not recorded and are drawn at battalion size."}
SOURCES = [
    "Lt. Col. Ernst Otto (Reichsarchiv), <a href='https://www.usni.org/magazines/proceedings/1928/november/battles-possession-belleau-woods-june-1918' target='_blank'>\"The Battles for the Possession of Belleau Woods, June, 1918\"</a>, <i>U.S. Naval Institute Proceedings</i> 54/11 (November 1928), from the war diaries of the German 237th, 10th, 28th and 87th Divisions; and Capt. John W. Thomason Jr.'s discussion of it in the same issue.",
    "<a href='https://archive.org/details/recordsofsecondd04unit' target='_blank'><i>Records of the Second Division (Regular)</i></a> (Army War College, 1928): the division's field messages and telephone logs, with their clock times.",
    "<a href='https://archive.org/details/historyofthirdba00hillrich' target='_blank'><i>History of the Third Battalion, Sixth Regiment, U.S. Marines</i></a> (1919), with Brigade Field Order No. 2; and <a href='https://archive.org/details/historyofsixthre00tien' target='_blank'><i>History of the Sixth Regiment, United States Marines</i></a> (Tientsin, 1928).",
    "James G. Harbord, <a href='https://archive.org/details/leavesfromwardia00jame' target='_blank'><i>Leaves from a War Diary</i></a> (1925); Edwin N. McClellan, <a href='https://archive.org/details/unitedstatesmari00unit' target='_blank'><i>The United States Marine Corps in the World War</i></a> (1920); <a href='https://archive.org/details/officialhistoryo00uni' target='_blank'><i>The Official History of the Second Regiment of Engineers</i></a> (1920).",
    "Gary W. Cozzens, \"How Will the Americans Behave in a Pitched Battle?\", <i>Marine Corps History</i> 4/2 (Winter 2018): Hill 142 minute by minute; J. Wayne Hill, <i>A Regiment Like No Other: The 6th Marine Regiment at Belleau Wood</i> (MMAS thesis, 2012); Mark R. Folse, \"Keystone Battle Brief: The Battle of Belleau Wood\" (Marine Corps History Division, 2019).",
    "American Battle Monuments Commission, <a href='https://archive.org/details/americanarmiesba00wash' target='_blank'><i>American Armies and Battlefields in Europe</i></a> (1938); War Department, <a href='https://archive.org/details/historiesoftwohu00unit' target='_blank'><i>Histories of Two Hundred and Fifty-One Divisions of the German Army</i></a> (1920); Wikipedia, <a href='https://en.wikipedia.org/wiki/Battle_of_Belleau_Wood' target='_blank'>Battle of Belleau Wood</a> (read 25 October 2026), for the casualty estimates.",
    "Woods, roads, the railway and places from OpenStreetMap (ODbL); the wood is the memorial park's outline. Hills 126, 133, 142, 169, 176 and 181, the Pavilion and Triangle Farm are placed from the sources' text and the surface model, within 150 to 400 m. Sunrise and sunset computed for the place and date, French summer time.",
    "Placed by inference, not from the sources: the Germans in the wheat at Les Mares Farm on 3 June as the 197th Division, which held Hill 164 by the farm that morning; the 45th Company's way up to Hill 142 on the evening of 6 June, where its 73 casualties are drawn; the 7th Infantry's battalions, 1st at the west edge, 2nd at Hill 181 and then the south-east corner, 3rd in Bouresches, so that 3/5 relieves the 1st in the north; the 28th Division leaving the map on the night of 16 June, when the 87th relieves the 237th. To keep the replay moving, the 12 June attack is drawn going forward from 4.30, the 13 June attack breaking at four, the 7th Infantry's second attack lasting an hour, and the Baden battalions of 11 June coming in from east of the railway.",
    "Terrain: " + T["source"] + ", 30 m, sampled to 17.5 m. A surface model: the wood and the villages stand 10 to 25 m above the ground.",
]

battle = dict(
    id="belleau-wood", name="Battle of Belleau Wood", date="1918-06-01", dateText="1 to 26 June 1918", place="Belleau Wood, near Château-Thierry, Aisne, France",
    origin=dict(lat=LAT0, lon=LON0), extent=2 * HALF_EXTENT, start=START, end=END, sunrise="04:44", sunset="20:50", speed=60, lapse=43200, menPerDot=10,
    terrainExaggeration=2, contourInterval=10, trees=dict(density=0.008), fields=FIELDS, wind=dict(x=0.5, y=0.3), view=dict(x=0, y=0, width=7000),
    sides=dict(american=dict(name="Americans (2nd Division, Bundy; 4th Marine Brigade, Harbord)", color="#2a55a0", light="#7090c8", dark="#15305e"),
               french=dict(name="French (XXI Corps, Degoutte)", color="#6d8fb5", light="#a9c0dc", dark="#36506e"),
               german=dict(name="Germans (IV Reserve Corps, von Conta)", color="#4a4a42", light="#8c8c80", dark="#22221e")),
    features=features, units=units, events=events, tints=TINTS,
    outcome=OUTCOME, sources=SOURCES,
)
json.dump(battle, open(HERE + "battle.json", "w"), indent=1)
print(len(units), "units,", len(events), "events,", len(features), "features,", len(FIELDS), "fields")
# Which units each chapter's frame holds at its moment, so a caption never names a unit the camera leaves out.
def where(u, t):
    ks = [k for k in u["keys"] if sec(k["t"]) <= sec(t)]
    if not ks or next((k["state"] for k in reversed(ks) if "state" in k), None) == "hidden": return None
    k = ks[-1]; nxt = [k2 for k2 in u["keys"] if sec(k2["t"]) > sec(t)]
    if nxt and (k["x"], k["y"]) != (nxt[0]["x"], nxt[0]["y"]):
        f = (sec(t) - sec(k["t"])) / (sec(nxt[0]["t"]) - sec(k["t"])); return (k["x"] + f * (nxt[0]["x"] - k["x"]), k["y"] + f * (nxt[0]["y"] - k["y"]))
    return (k["x"], k["y"])
for e in events:
    r = e["view"] / 2; inside = [u["id"] for u in units if (p := where(u, e["t"])) and abs(p[0] - e["at"][0]) <= r and abs(p[1] - e["at"][1]) <= r]
    print(f"{e['t']} {e['title']}: {' '.join(inside)}")
