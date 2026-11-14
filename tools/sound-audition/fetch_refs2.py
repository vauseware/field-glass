#!/usr/bin/env python3
"""Find and fetch freely licensed recordings of real WW1 and WW2 equipment.

  python3 -I fetch_refs2.py search [row ...]        run every query in ROWS, cache to candidates2.json
  python3 -I fetch_refs2.py q <fs|commons|archive> "<query>"   one ad-hoc query, printed, not cached
  python3 -I fetch_refs2.py show <row> [regex] [all]  print cached candidates for a row
  python3 -I fetch_refs2.py info <source> <id>      print full text of one candidate
  python3 -I fetch_refs2.py fetch                   download PICKS into refs2/, convert, write manifest
  python3 -I fetch_refs2.py verify                  re-check refs2/ against its manifest

Standard library only. The freesound key is read from ~/.config/freesound/api_key and
sent only as an Authorization header to freesound.org API URLs.
"""
import html
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REFS = os.path.join(HERE, "refs2")
ORIG = os.path.join(REFS, "orig")
CANDIDATES = os.path.join(HERE, "candidates2.json")
PRIOR_MANIFEST = os.path.join(HERE, "refs", "manifest.json")
UA = "sound-ref-fetch/0.2"
FS_API = "https://freesound.org/apiv2"
FS_FIELDS = "id,name,username,license,duration,previews,tags,description,avg_rating,num_downloads,url"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
MAX_BYTES = 120 * 1024 * 1024
MAX_SECONDS = 180
DOWNLOAD_HOSTS = ("freesound.org", "upload.wikimedia.org", "archive.org")

# Accept list. Anything that matches none of these is rejected.
LICENCE_URLS = [
    (re.compile(r"^https?://creativecommons\.org/publicdomain/zero/1\.0/?"), "CC0 1.0"),
    (re.compile(r"^https?://creativecommons\.org/publicdomain/mark/1\.0/?"), "Public domain"),
    (re.compile(r"^https?://creativecommons\.org/licenses/by/(\d\.\d)(/[a-z]+)?/?"), "CC BY %s"),
    (re.compile(r"^https?://creativecommons\.org/licenses/by-sa/(\d\.\d)(/[a-z]+)?/?"), "CC BY-SA %s"),
]
PD_SHORT = re.compile(r"^(public domain|cc0|pd([- ].*)?)$", re.I)

HARD = [
    "scream", "screams", "screaming", "agony", "pain", "wounded", "dying", "death", "moan", "moans",
    "moaning", "groan", "groans", "groaning", "cry", "cries", "crying", "gore", "injured",
    "synth", "synthesized", "synthesised", "synthesizer", "synthesis", "synthetic", "generated",
    "designed", "sound design", "sound-design", "sounddesign", "layered", "layers", "sfx", "game", "games",
    "videogame", "video game", "gamedev", "daw", "vst", "airsoft", "toy", "announcer", "commentary",
    "commentator", "pa system", "tannoy", "loudspeaker", "music", "conversation", "talking", "simulated",
    "simulation", "fake", "remix", "foley", "film dub", "dubbed", "made in", "created in", "created with",
    "fl studio", "ableton", "audacity generated", "ai",
]
SOFT = ["film", "movie", "blank", "blanks", "reenactment", "re-enactment", "airshow", "air show", "crowd",
        "voices", "speech", "processed", "mixed", "edited", "newsreel", "museum", "replica"]


def word_re(words):
    return re.compile(r"(?<![a-z0-9])(" + "|".join(re.escape(w) for w in words) + r")(?![a-z0-9])")


HARD_RE = word_re(HARD)
SOFT_RE = word_re(SOFT)

# row: (era, nation, family, freesound queries, commons queries)
ROWS = {
    "A1": ("ww2", "US", "transport-aircraft",
           ["dc-3", "dc3", "c-47", "c47", "dakota aircraft", "douglas dakota", "skytrain", "li-2", "r-1830",
            "twin wasp", "radial engine start", "dc-3 flyover", "radial engine flyby", "beech 18", "twin radial"],
           ["C-47", "DC-3", "Dakota aircraft", "Douglas Skytrain", "Lisunov", "radial engine", "Twin Wasp"]),
    "A2": ("ww2", "DE", "dive-bomber",
           ["stuka", "ju 87", "ju87", "jericho trumpet", "dive siren", "air raid siren", "mechanical siren",
            "hand crank siren", "jumo", "dive bomber", "wind siren"],
           ["Stuka", "Ju 87", "Jericho", "Sturzkampfflugzeug", "Sirene", "air raid siren", "Jumo 211", "dive bomber"]),
    "A3": ("ww2", "US", "fighter-bomber",
           ["p-47", "p47", "thunderbolt", "r-2800", "double wasp", "corsair flyby", "hellcat", "f4u", "f6f",
            "p-51 flyby", "warbird flyby", "bearcat"],
           ["P-47", "Thunderbolt aircraft", "R-2800", "Corsair F4U", "Hellcat", "P-51", "warbird"]),
    "A4": ("ww2", "UK", "heavy-bomber",
           ["lancaster", "avro lancaster", "halifax bomber", "stirling bomber", "merlin engine", "lancaster flypast",
            "four engine bomber", "b-17", "bristol hercules"],
           ["Lancaster", "Halifax bomber", "Short Stirling", "Merlin engine", "B-17", "Bristol Hercules"]),
    "US1": ("ww2", "US", "rifle", ["garand", "m1 garand", "garand ping", "30-06", "m1 rifle"], ["Garand", "M1 rifle"]),
    "US2": ("ww2", "US", "mg", ["m1919", "browning .30", "browning machine gun", "m2 browning", ".50 cal", "50 cal machine gun",
                                "ma deuce", "50 caliber", "m2hb"], ["M1919", "M2 Browning", "Browning machine gun", ".50 caliber"]),
    "US3": ("ww2", "US", "tank-engine", ["sherman", "sherman tank", "m4 sherman", "tank tracks", "tank driving", "tank engine",
                                         "stuart tank", "m3 stuart", "m18 hellcat", "tank pass", "tracked vehicle"],
            ["Sherman tank", "M4 Sherman", "tank engine", "Stuart tank", "tank tracks"]),
    "US4": ("ww2", "US", "tank-gun", ["tank gun", "tank firing", "tank shot", "75mm", "76mm", "tank cannon", "anti-tank gun",
                                      "abrams firing", "tank main gun"], ["tank gun firing", "tank fire", "anti-tank gun"]),
    "US5": ("ww2", "US", "howitzer", ["105mm", "105 mm howitzer", "howitzer", "m101", "m119", "howitzer firing", "artillery firing",
                                      "artillery fire", "field artillery"], ["howitzer", "105 mm", "artillery fire", "M101", "M119"]),
    "US6": ("ww2", "US", "vehicle", ["willys", "willys jeep", "jeep mb", "ww2 jeep", "gmc cckw", "cckw", "half-track", "halftrack",
                                     "m3 halftrack", "deuce and a half", "army truck", "military truck", "dodge wc", "ford gpw"],
            ["Willys", "Jeep MB", "GMC CCKW", "half-track", "military truck"]),
    "US7": ("ww2", "US", "naval-gun", ["naval gun", "naval gunfire", "battleship", "5 inch gun", "destroyer gun", "ship gun",
                                       "16 inch gun", "naval artillery", "warship firing"],
            ["naval gun", "battleship firing", "5-inch gun", "naval gunfire"]),
    "UK1": ("both", "UK", "rifle", ["lee-enfield", "lee enfield", "enfield rifle", "smle", "303", ".303", "no4 mk1", "enfield"],
            ["Lee-Enfield", "SMLE", ".303"]),
    "UK2": ("ww2", "UK", "mg", ["bren", "bren gun", "bren lmg", "zb26", "zb-26"], ["Bren"]),
    "UK3": ("ww2", "UK", "field-gun", ["25 pounder", "25-pounder", "25pdr", "field gun", "gun salute", "royal artillery",
                                       "pack howitzer", "l118", "light gun", "artillery salute"],
            ["25-pounder", "25 pounder", "field gun", "gun salute", "L118"]),
    "DE1": ("both", "DE", "rifle", ["k98", "kar98", "kar98k", "mauser", "karabiner", "mauser rifle", "8mm mauser", "gewehr 98",
                                    "bolt action rifle"], ["Karabiner 98", "Mauser", "Gewehr 98", "K98"]),
    "DE2": ("ww2", "DE", "mg", ["mg42", "mg 42", "mg34", "mg 34", "mg3", "mg 3", "buzz saw", "german machine gun", "m53", "mg-42"],
            ["MG 42", "MG 34", "MG3", "Maschinengewehr"]),
    "DE3": ("ww2", "DE", "tank-engine", ["panzer", "panther tank", "tiger tank", "stug", "maybach", "panzer iv", "german tank",
                                         "hetzer", "tiger 131", "kettenkrad", "sdkfz", "sd.kfz"],
            ["Panzer", "Panther tank", "Tiger tank", "Maybach", "Sd.Kfz", "Kettenkrad", "StuG"]),
    "DE4": ("ww2", "DE", "tank-gun", ["88mm", "flak 88", "8.8 cm", "flak", "pak 40", "anti aircraft gun", "pak", "flak gun"],
            ["Flak", "8.8 cm", "Pak 40", "88 mm"]),
    "DE5": ("ww2", "DE", "rocket", ["nebelwerfer", "rocket launcher", "katyusha", "mlrs", "rocket artillery", "multiple rocket",
                                    "bm-21", "grad rocket"], ["Nebelwerfer", "rocket artillery", "Katyusha", "MLRS", "BM-21"]),
    "W2": ("great-war", "UK", "mg", ["vickers", "vickers machine gun", "vickers gun", "vickers mg"], ["Vickers machine gun", "Vickers gun"]),
    "W3": ("great-war", "UK", "mg", ["lewis gun", "lewis machine gun", "lewis lmg"], ["Lewis gun"]),
    "W4": ("great-war", "UK", "field-gun", ["18 pounder", "13 pounder", "king's troop", "kings troop", "royal horse artillery",
                                            "royal gun salute", "41 gun salute", "21 gun salute", "hyde park salute"],
           ["18-pounder", "13-pounder", "King's Troop", "gun salute"]),
    "W5": ("great-war", "FR", "field-gun", ["french 75", "canon de 75", "75mm field gun", "75 mm", "soixante-quinze", "canon 75"],
           ["Canon de 75", "French 75", "canon 75"]),
    "W6": ("great-war", "US", "rifle", ["springfield", "m1903", "1903 springfield", "springfield rifle", "03-a3", "1903a3"],
           ["Springfield M1903", "M1903"]),
    "W7": ("great-war", "FR", "mg", ["chauchat", "hotchkiss", "hotchkiss machine gun", "hotchkiss m1914", "lebel", "berthier"],
           ["Chauchat", "Hotchkiss", "Lebel"]),
    "W9": ("great-war", "DE", "mg", ["mg08", "mg 08", "maxim", "maxim gun", "maxim machine gun", "spandau", "pm1910", "pm m1910"],
           ["MG 08", "Maxim gun", "Maxim machine gun"]),
    "W10": ("great-war", "DE", "field-gun", ["7.7 cm", "feldkanone", "ww1 field gun", "ww1 artillery", "field gun firing",
                                             "old cannon firing", "first world war gun", "great war artillery", "krupp"],
            ["Feldkanone", "7.7 cm", "field gun firing", "World War I artillery"]),
    "W11": ("great-war", "UK", "tank-engine", ["mark iv tank", "mark v tank", "ww1 tank", "renault ft", "ft-17", "ft17", "schneider ca1",
                                               "first world war tank", "daimler sleeve valve", "vintage tractor engine", "old tank"],
            ["Mark IV tank", "Mark V tank", "Renault FT", "Schneider CA1", "World War I tank"]),
    "W12": ("great-war", "any", "shell", ["shell burst", "artillery impact", "artillery shell", "shell explosion", "shell whistle",
                                          "incoming artillery", "155mm", "155 mm", "heavy artillery", "heavy howitzer", "m777", "m198",
                                          "shell impact", "artillery explosion", "mortar impact", "incoming shell", "8 inch howitzer"],
            ["shell explosion", "artillery impact", "155 mm", "heavy howitzer", "gas shell bombardment", "bombardment"]),
}

# archive.org full-text search returns mostly music and talk, so it is limited to the USC film
# sound-effects collection (CC0), whose item descriptions list every file name.
ARCHIVE_COLLECTION = "usc-sound-effect-archive"
ARCHIVE_Q = {
    "A2": ["stuka OR siren"], "A3": ["P-47 OR fighter"], "A4": ["B-17 OR bomber"], "US1": ["rifle"], "US2": ["machine gun"],
    "US3": ["tank"], "US4": ["anti-tank OR cannon"], "US5": ["howitzer OR artillery"], "US6": ["jeep OR army truck"],
    "US7": ["naval OR battleship"], "W12": ["shell OR bombardment"],
}

# Cross-references that need no file of their own.
CROSS_REFS = {
    "W1": "Same weapon family as UK1 (Lee-Enfield). Use the UK1 files.",
    "W8": "Same Mauser 98 action and 7.92 mm cartridge as DE1. Use the DE1 files.",
    "W9-prior": "Earlier pass already holds two Russian Maxim clips by poissonmort: freesound 160772 and 160773 (refs/mg-2-160772.mp3, refs/mg-1-160773.mp3). Not re-downloaded.",
}

# (row, n, source, id, equipment, exact, best_span, note)
PICKS = [
    ('A1', 1, 'freesound', '437839', 'Douglas C-47, slow pass overhead with long fly-away', True, None, 'USC film sound-effects library (optical/35 mm mag transfer, likely 1940s-60s). Studio library label is the only provenance; recording date and place unknown. Pass comes first, then a long fly-away.'),
    ('A1', 2, 'freesound', '437841', 'Douglas C-47 take-off', True, None, 'USC film sound-effects library (optical/35 mm mag transfer, likely 1940s-60s). Studio library label is the only provenance; recording date and place unknown. Ground perspective assumed.'),
    ('A1', 3, 'freesound', '437833', 'Douglas C-47 engine start, idle, stop', True, None, 'USC film sound-effects library (optical/35 mm mag transfer, likely 1940s-60s). Studio library label is the only provenance; recording date and place unknown. Order is start, idle, stop; no times given.'),
    ('A1', 4, 'freesound', '256049', 'Douglas DC-3 (Dakota) taxi to runway end, take-off, climb away', True, None, 'Finnish Broadcasting Company archive, Nagra tape, Utti airfield, 4 April 1978. Best-documented C-47 family clip here.'),
    ('A2', 1, 'freesound', '437771', 'Junkers Ju 87 Stuka, steady engine drone, no siren', False, None, 'USC film sound-effects library (optical/35 mm mag transfer, likely 1940s-60s). Studio library label is the only provenance; recording date and place unknown. Labelled Stuka by the library; that cannot be checked. No dive and no siren.'),
    ('A2', 2, 'freesound', '437780', 'Unnamed WW2 fighter diving with whine', False, None, 'USC film sound-effects library (optical/35 mm mag transfer, likely 1940s-60s). Studio library label is the only provenance; recording date and place unknown. Not a Stuka. The whine may be airframe or prop, not a siren. Could be a studio-built effect.'),
    ('A2', 3, 'freesound', '675690', 'Hand-cranked mechanical siren', False, None, "USC film sound-effects library (optical/35 mm mag transfer, likely 1940s-60s). Studio library label is the only provenance; recording date and place unknown. Real rotor siren, the same sound-making principle as the Stuka's wind-driven siren, but not on an aircraft."),
    ('A2', 4, 'freesound', '438696', 'Air raid siren, winds up and down', False, None, 'USC film sound-effects library (optical/35 mm mag transfer, likely 1940s-60s). Studio library label is the only provenance; recording date and place unknown. Civil-defence siren, several tones at once. Stand-in for siren character only.'),
    ('A3', 1, 'freesound', '143560', 'Republic P-47D Thunderbolt low pass overhead', True, None, 'Tagged Airshow, so show noise is possible; the description says nothing more about the setting. 12 s, single pass.'),
    ('A3', 2, 'freesound', '437795', 'Republic P-47 fighters, several varied passes overhead', True, None, 'USC film sound-effects library (optical/35 mm mag transfer, likely 1940s-60s). Studio library label is the only provenance; recording date and place unknown. More than one aircraft. 105 s; passes are spread through the clip, no times given.'),
    ('A3', 3, 'freesound', '142900', 'Republic P-47D Thunderbolt cold engine start (R-2800)', True, None, 'Start-up on the ground, not a pass.'),
    ('A4', 1, 'freesound', '325563', 'Avro Lancaster fly-by over Toronto', False, None, 'Lancaster stands in for Stirling/Halifax (Merlins, not Hercules). Uploader calls it a clean fly-by; Tascam DR100 with Neumann pair. 110 s, pass position not stated.'),
    ('A4', 2, 'freesound', '103439', 'Avro Lancaster fly-past', False, None, 'Recorded at Santa Pod, a drag-racing venue, so event noise is possible. 11 s.'),
    ('A4', 3, 'freesound', '195412', 'Avro Lancaster with Hurricane and Spitfire, low fly-past', False, None, 'Three aircraft together (BBMF-style formation), so not a lone bomber. Mono, unprocessed.'),
    ('US1', 1, 'freesound', '460851', 'M1 Garand single shot', True, None, 'Fired in a small indoor range, so room reverb, not open air.'),
    ('US1', 2, 'freesound', '725398', 'M1 Garand en-bloc clip ejecting with ping', True, None, 'Ping only, about 1 s. Uploader does not say how it was recorded.'),
    ('US1', 3, 'freesound', '460848', 'M1 Garand clip eject, handling', True, None, 'Mechanism sound, no shot. Indoor range.'),
    ('US2', 1, 'freesound', '675588', 'Browning .50 calibre machine gun firing', True, None, 'USC film sound-effects library (optical/35 mm mag transfer, likely 1940s-60s). Studio library label is the only provenance; recording date and place unknown. 15 s.'),
    ('US2', 2, 'freesound', '249146', 'Browning .50 calibre machine gun, two runs, exterior, medium distance', True, None, 'Modern recording; the M2 is the same gun still in service. Model not named beyond 50 cal.'),
    ('US2', 3, 'freesound', '183656', 'Vehicle-mounted .50 calibre machine gun, various bursts', True, None, 'Audio lifted from a US government video by the uploader; camera-mic quality likely.'),
    ('US3', 1, 'commons', 'File:Sherman tank, rijden - SoundCloud - Beeld en Geluid.ogg', 'M4 Sherman approaching from far off and driving past on a concrete road', True, None, 'Netherlands Institute for Sound and Vision effects archive. 102 s; approach is long, pass position not stated.'),
    ('US3', 2, 'commons', 'File:Sherman tank, starten en rijden - SoundCloud - Beeld en Geluid.ogg', 'M4 Sherman starting and driving away on a concrete road', True, None, 'Netherlands Institute for Sound and Vision effects archive. Engine variant not stated.'),
    ('US3', 3, 'freesound', '438118', 'M4 medium tank pass-by, squeaky tracks', True, None, 'USC film sound-effects library (optical/35 mm mag transfer, likely 1940s-60s). Studio library label is the only provenance; recording date and place unknown. Medium to slow speed.'),
    ('US4', 1, 'freesound', '486031', '75 mm gun firing three times', False, None, 'USC film sound-effects library (optical/35 mm mag transfer, likely 1940s-60s). Studio library label is the only provenance; recording date and place unknown. Library says only 75mm gun: could be a tank gun, field gun or pack howitzer.'),
    ('US4', 2, 'freesound', '675587', 'Squad firing 37 mm anti-tank guns', False, None, "USC film sound-effects library (optical/35 mm mag transfer, likely 1940s-60s). Studio library label is the only provenance; recording date and place unknown. US 37 mm M3 class, smaller than the row's 75/76 mm. Several guns."),
    ('US5', 1, 'freesound', '486029', '105 mm howitzer firing twice', True, None, 'USC film sound-effects library (optical/35 mm mag transfer, likely 1940s-60s). Studio library label is the only provenance; recording date and place unknown. Described as inside a larger battle scene, so other fire is audible and it may be a film mix.'),
    ('US5', 2, 'freesound', '182822', 'US Army artillery shots, type not stated', False, None, 'Audio lifted from four US government videos by the uploader. Tagged howitzer; calibre unknown; modern guns.'),
    ('US6', 1, 'freesound', '438109', 'Army jeep approaching from a distance, idling, stopping', True, None, 'USC film sound-effects library (optical/35 mm mag transfer, likely 1940s-60s). Studio library label is the only provenance; recording date and place unknown. Jeep model not named.'),
    ('US6', 2, 'commons', 'File:Jeep Willys - engine and exhaust sound (YouTube U- wTDXrO6U).opus', 'Willys Jeep start-up, revving or acceleration', True, None, 'Audio track of a CC BY YouTube video. Close exhaust perspective; Willys variant and year not stated, may be a post-war CJ.'),
    ('US6', 3, 'freesound', '438098', 'Army truck driving on a rough road', False, None, 'USC film sound-effects library (optical/35 mm mag transfer, likely 1940s-60s). Studio library label is the only provenance; recording date and place unknown. Truck type not named. Microphone may be riding with the vehicle.'),
    ('US7', 1, 'freesound', '675606', '8-inch naval gun firing, with shell whines', False, None, 'USC film sound-effects library (optical/35 mm mag transfer, likely 1940s-60s). Studio library label is the only provenance; recording date and place unknown. Cruiser-size gun, not destroyer 5-inch or battleship main battery. Shell whine may be added.'),
    ('US7', 2, 'freesound', '675605', '6-inch naval gun fired close up', False, None, 'USC film sound-effects library (optical/35 mm mag transfer, likely 1940s-60s). Studio library label is the only provenance; recording date and place unknown. Light-cruiser-size gun. 6 s.'),
    ('UK1', 1, 'freesound', '450850', 'Lee-Enfield .303 shots with bolt and case ejection', True, None, 'Mark not stated (SMLE or No. 4). Also serves W1.'),
    ('UK1', 2, 'freesound', '450853', 'Lee-Enfield .303 single clean shot', True, None, 'Mark not stated. Also serves W1.'),
    ('UK2', 1, 'freesound', '675590', 'Bren gun firing, canyon echo', True, None, 'USC film sound-effects library (optical/35 mm mag transfer, likely 1940s-60s). Studio library label is the only provenance; recording date and place unknown. 6 s.'),
    ('UK2', 2, 'freesound', '675591', 'Bren gun firing, distant', True, None, 'USC film sound-effects library (optical/35 mm mag transfer, likely 1940s-60s). Studio library label is the only provenance; recording date and place unknown. 21 s.'),
    ('UK3', 1, 'commons', 'File:Sexton artillery firing.oga', 'Ordnance QF 25-pounder firing, mounted on a Sexton self-propelled gun', True, None, 'Public demonstration at Fort Nelson, Hampshire, so likely a blank charge and spectators nearby. Same gun as the towed 25-pounder.'),
    ('UK3', 2, 'freesound', '702455', 'Ordnance QF 6-pounder anti-tank gun firing', False, None, 'Recorded at Tankfest (Bovington), so likely a blank charge; show PA or spectators possible though not mentioned.'),
    ('DE1', 1, 'freesound', '802675', 'Mauser Karabiner 98k firing', True, None, 'Blank cartridge at a historical re-enactment, so a lighter report than ball ammunition. 2 s. Also serves W8.'),
    ('DE1', 2, 'freesound', '802673', 'Mauser Karabiner 98k bolt action cycling', True, None, 'Mechanism only, no shot. Also serves W8.'),
    ('W5', 1, 'freesound', '486023', '75 mm gun: fires, shell in flight, burst', False, None, 'USC film sound-effects library (optical/35 mm mag transfer, likely 1940s-60s). Studio library label is the only provenance; recording date and place unknown. Calibre matches the French 75 (the US M1897 was the same gun) but the library does not name the model. Flight and burst may be assembled.'),
    ('W6', 1, 'freesound', '169261', 'Springfield M1903 .30-06 single shot', True, None, 'Fired inside a 535-seat theatre (presumably a blank); uploader applied noise reduction. 4 s.'),
    ('W9', 1, 'freesound', '255270', 'Russian Maxim machine gun, heavy sustained fire, close, with echo', False, None, 'Finnish Broadcasting Company archive, Nagra tape, Hameenlinna, 1 Nov 1984. Russian Maxim, not the German MG 08; same Maxim action and similar rate. 108 s of bursts.'),
    ('W9', 2, 'freesound', '255271', 'Russian Maxim machine gun, sustained fire at varying distances', False, None, 'Finnish Broadcasting Company archive, same 1984 session. Russian Maxim, not MG 08.'),
    ('W9', 3, 'freesound', '160771', 'Russian Maxim machine gun at about 200 m', False, None, 'Third perspective from the poissonmort session whose 1-10 m and 40 m clips are in the earlier refs/ folder.'),
    ('W10', 1, 'freesound', '332935', '76 mm field gun, single shots', False, None, "Finnish Broadcasting Company archive, Niinisalo, 1958. Model not stated; Finland's 76 mm field guns were mostly WW1-era Russian pieces, but that is an inference."),
    ('W12', 1, 'freesound', '258203', 'Obukhov 305 mm gun, 1911-1915 model, two echoing shots at a distance', True, None, 'Finnish Broadcasting Company, DAT, Kuivasaari coastal battery, 6 Dec 1997. A real WW1-era heavy gun; salute charge likely. Gun report, not a shell burst.'),
    ('W12', 2, 'freesound', '486030', '155 mm howitzer firing several times, shells bursting in the background', True, None, 'USC film sound-effects library (optical/35 mm mag transfer, likely 1940s-60s). Studio library label is the only provenance; recording date and place unknown. Gun and distant bursts together.'),
    ('W12', 3, 'freesound', '674897', 'Incoming shells and explosions', True, None, 'USC film sound-effects library (optical/35 mm mag transfer, likely 1940s-60s). Studio library label is the only provenance; recording date and place unknown. Library files it under REAL explosions, but the incoming whistle may be assembled. Least certain of the three.'),
]


def read_key():
    with open(os.path.expanduser("~/.config/freesound/api_key"), encoding="utf-8") as f:
        return f.read().strip()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, "redirect refused: " + newurl, headers, fp)


FS_OPENER = urllib.request.build_opener(NoRedirect)


REFUSED = set()


def get_json(url, params, headers=None, opener=None):
    full = url + "?" + urllib.parse.urlencode(params)
    h = {"User-Agent": UA}
    h.update(headers or {})
    req = urllib.request.Request(full, headers=h)
    for attempt in range(3):
        try:
            with (opener or urllib.request.build_opener()).open(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            body = e.read(600).decode("utf-8", "replace")
            if e.code == 429 and "wikimedia" in url:
                if attempt < 2:
                    time.sleep(90)
                    continue
                print("commons keeps refusing (429); skipping it for the rest of this run")
                REFUSED.add("commons")
                return {}
            sys.exit("HTTP %s on %s\n%s" % (e.code, url, body))
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt == 2:
                sys.exit("network failure on %s: %s" % (url, e))
            time.sleep(5)


def clean(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(s or ""))).strip()


def licence_of(url, short=""):
    """Return (short name, url) for an accepted licence, else None."""
    url = (url or "").strip()
    short = clean(short)
    if re.search(r"(?<![a-z])(nc|nd)(?![a-z])|sampling|gfdl|fair use", (url + " " + short).lower()):
        return None
    for rx, name in LICENCE_URLS:
        m = rx.match(url)
        if m:
            return ((name % m.group(1)) if "%s" in name else name, url)
    if not url and PD_SHORT.match(short):
        return (short, "")
    return None


def flags(text):
    t = text.lower()
    return sorted(set(HARD_RE.findall(t))), sorted(set(SOFT_RE.findall(t)))


def cand(source, cid, title, author, lic, duration, page, download, text, size=None):
    hard, soft = flags(title + " " + text)
    return {"source": source, "id": str(cid), "title": title, "author": author, "licence": lic[0], "licence_url": lic[1],
            "duration": duration, "page": page, "download": download, "text": text, "hard": hard, "soft": soft, "size": size}


def fs_to_cand(s):
    lic = licence_of(s.get("license"))
    if not lic:
        return None
    text = " ".join(s.get("tags") or []) + " || " + clean(s.get("description"))
    return cand("freesound", s["id"], s["name"], s["username"], lic, s.get("duration"),
                "https://freesound.org/s/%s/" % s["id"], s["previews"]["preview-hq-mp3"], text)


def fs_search(q, key):
    flt = 'duration:[1 TO %d] license:("Creative Commons 0" OR "Attribution")' % MAX_SECONDS
    m = re.match(r"user:(\S+)\s*(.*)", q)
    if m:
        flt += " username:" + m.group(1)
        q = m.group(2)
    data = get_json(FS_API + "/search/text/", {"query": q, "filter": flt, "fields": FS_FIELDS, "page_size": 50, "sort": "score"},
                    {"Authorization": "Token " + key}, FS_OPENER)
    time.sleep(1.1)
    return [c for c in (fs_to_cand(s) for s in data.get("results", [])) if c]


def fs_one(sid, key):
    s = get_json(FS_API + "/sounds/%s/" % sid, {"fields": FS_FIELDS}, {"Authorization": "Token " + key}, FS_OPENER)
    time.sleep(1.1)
    return fs_to_cand(s)


def commons_info(titles):
    out = []
    if "commons" in REFUSED:
        return out
    for i in range(0, len(titles), 40):
        data = get_json(COMMONS_API, {"action": "query", "format": "json", "formatversion": "2", "titles": "|".join(titles[i:i + 40]),
                                      "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime"})
        time.sleep(4.0)
        for p in data.get("query", {}).get("pages", []):
            ii = (p.get("imageinfo") or [None])[0]
            if not ii or not (ii.get("mime", "").startswith("audio/") or ii.get("mime") == "application/ogg"):
                continue
            em = ii.get("extmetadata") or {}
            v = lambda k: (em.get(k) or {}).get("value", "")
            lic = licence_of(v("LicenseUrl"), v("LicenseShortName"))
            if not lic:
                continue
            if not lic[1]:
                lic = (lic[0], ii.get("descriptionurl", ""))
            text = clean(v("ImageDescription")) + " || cats: " + clean(v("Categories")) + " || credit: " + clean(v("Credit")) \
                + " || date: " + clean(v("DateTimeOriginal"))
            if re.search(r"pronunciation|lingua libre|spoken wikipedia|wiktionary|wikiwoordenboek", text + p["title"], re.I):
                continue
            out.append(cand("commons", p["title"], p["title"], clean(v("Artist")), lic, ii.get("duration"),
                            ii.get("descriptionurl"), ii.get("url"), text, ii.get("size")))
    return out


def commons_search(q):
    if "commons" in REFUSED:
        return []
    data = get_json(COMMONS_API, {"action": "query", "format": "json", "formatversion": "2", "list": "search", "srnamespace": "6",
                                  "srsearch": q + " filetype:audio", "srlimit": "40"})
    time.sleep(4.0)
    titles = [r["title"] for r in data.get("query", {}).get("search", [])]
    return commons_info(titles) if titles else []


def archive_item(identifier):
    """Candidates for every audio original in one archive.org item whose metadata carries an accepted licence URL."""
    meta = get_json("https://archive.org/metadata/" + urllib.parse.quote(identifier), {})
    time.sleep(1.0)
    md = meta.get("metadata") or {}
    lic = licence_of(md.get("licenseurl") if isinstance(md.get("licenseurl"), str) else "")
    if not lic:
        return []
    text = "collection: " + str(md.get("collection"))
    out = []
    for f in meta.get("files", []):
        if f.get("source") != "original" or not re.search(r"\.(mp3|wav|flac|ogg|m4a|aiff?)$", f.get("name", ""), re.I):
            continue
        try:
            dur = float(f.get("length")) if ":" not in str(f.get("length")) else None
        except (TypeError, ValueError):
            dur = None
        out.append(cand("archive", identifier + "/" + f["name"], clean(str(md.get("title"))) + " / " + f["name"],
                        clean(str(md.get("creator"))), lic, dur, "https://archive.org/details/" + identifier,
                        "https://archive.org/download/%s/%s" % (urllib.parse.quote(identifier), urllib.parse.quote(f["name"])),
                        text, int(f["size"]) if str(f.get("size", "")).isdigit() else None))
    return out


def archive_search(q):
    data = get_json("https://archive.org/advancedsearch.php", [("q", "collection:%s AND (%s)" % (ARCHIVE_COLLECTION, q)),
                                                               ("fl[]", "identifier"), ("fl[]", "title"), ("fl[]", "licenseurl"),
                                                               ("rows", "25"), ("output", "json")])
    time.sleep(1.0)
    out = []
    for d in data.get("response", {}).get("docs", []):
        if licence_of(d.get("licenseurl")):
            out += archive_item(d["identifier"])
    return out


def prior_ids():
    try:
        with open(PRIOR_MANIFEST, encoding="utf-8") as f:
            return {str(e["freesound_id"]) for e in json.load(f)}
    except FileNotFoundError:
        return set()


def line(c):
    mark = "R" if c["hard"] else " "
    dur = "%.0fs" % c["duration"] if c.get("duration") else "?s"
    return "%s %s:%s | %s | %s | %s | by %s%s%s | %s" % (
        mark, c["source"][:2], c["id"], c["licence"], dur, c["title"][:70], (c["author"] or "")[:18],
        (" | HARD " + ",".join(c["hard"])) if c["hard"] else "", (" | soft " + ",".join(c["soft"])) if c["soft"] else "",
        c["text"][:170])


def cmd_search(only):
    key = read_key()
    skip = prior_ids()
    try:
        with open(CANDIDATES, encoding="utf-8") as f:
            out = json.load(f)
    except FileNotFoundError:
        out = {}
    for row, (era, nation, family, fsq, cq) in ROWS.items():
        aq = ARCHIVE_Q.get(row, [])
        if only and row not in only:
            continue
        found = {}
        n = {"freesound": 0, "commons": 0, "archive": 0}
        for src, queries, fn in (("freesound", fsq, lambda q: fs_search(q, key)), ("commons", cq, commons_search), ("archive", aq, archive_search)):
            for q in queries:
                for c in fn(q):
                    if c["source"] == "freesound" and c["id"] in skip:
                        continue
                    k = c["source"] + ":" + c["id"]
                    if k not in found:
                        c["queries"] = [q]
                        found[k] = c
                        n[src] += 1
                    else:
                        found[k]["queries"].append(q)
        out[row] = list(found.values())
        clean_n = sum(1 for c in found.values() if not c["hard"])
        print("%-4s freesound=%d commons=%d archive=%d passing_content=%d" % (row, n["freesound"], n["commons"], n["archive"], clean_n))
        with open(CANDIDATES, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1)


def cmd_show(row, pattern=None, show_all=False):
    with open(CANDIDATES, encoding="utf-8") as f:
        cands = json.load(f)[row]
    shown = [c for c in cands if (show_all or not c["hard"]) and (not pattern or re.search(pattern, c["title"] + " " + c["text"], re.I))]
    print("%s: %d cached, %d shown" % (row, len(cands), len(shown)))
    for c in shown:
        print(line(c))


def lookup(source, cid, key=None):
    if source == "freesound":
        return fs_one(cid, key or read_key())
    if source == "commons":
        r = commons_info([cid])
        return r[0] if r else None
    if source == "archive":
        identifier, name = cid.split("/", 1)
        for c in archive_item(identifier):
            if c["id"] == cid:
                return c
    return None


def download(url, dest):
    p = urllib.parse.urlparse(url)
    host = p.hostname or ""
    if p.scheme != "https" or not any(host == h or host.endswith("." + h) for h in DOWNLOAD_HOSTS):
        sys.exit("refusing download host: %s" % host)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read(MAX_BYTES + 1)
    if not data or len(data) > MAX_BYTES:
        sys.exit("empty or too large: %s" % url)
    with open(dest, "wb") as f:
        f.write(data)


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=format_name,duration:stream=codec_name,codec_type",
                        "-of", "json", path], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return None
    j = json.loads(r.stdout)
    audio = [s for s in j.get("streams", []) if s.get("codec_type") == "audio"]
    return {"format": j.get("format", {}).get("format_name"), "codec": audio[0]["codec_name"] if audio else None,
            "duration": float(j.get("format", {}).get("duration") or 0)}


def slug(source, cid):
    if source == "freesound":
        return cid
    base = cid.split("/")[-1] if source == "archive" else re.sub(r"^File:", "", cid)
    base = re.sub(r"\.[A-Za-z0-9]{2,4}$", "", base)
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")[:40]


def cmd_fetch():
    key = read_key()
    os.makedirs(ORIG, exist_ok=True)
    entries = []
    for row, n, source, cid, equipment, exact, best_span, note in PICKS:
        era, nation, family = ROWS[row][:3]
        c = lookup(source, cid, key)
        if not c:
            sys.exit("licence not accepted or not found: %s %s" % (source, cid))
        if c["hard"]:
            sys.exit("content rule words in %s %s: %s" % (source, cid, c["hard"]))
        name = "%s-%d-%s%s.mp3" % (row, n, source, slug(source, cid))
        ext = os.path.splitext(urllib.parse.urlparse(c["download"]).path)[1].lower() or ".bin"
        orig = os.path.join(ORIG, name[:-4] + ext)
        if not (os.path.exists(orig) and os.path.getsize(orig) > 0):
            download(c["download"], orig)
            time.sleep(1.0)
        dest = os.path.join(REFS, name)
        r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", orig, "-vn", "-map", "0:a:0", "-map_metadata", "-1",
                            "-c:a", "libmp3lame", "-q:a", "2", dest], capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            sys.exit("ffmpeg failed on %s: %s" % (orig, r.stderr[-300:]))
        pr = probe(dest)
        entries.append({
            "row": row, "era": era, "nation": nation, "family": family, "equipment": equipment, "exact": exact, "source": source,
            "page": c["page"], "title": c["title"], "author": c["author"], "licence": c["licence"], "licence_url": c["licence_url"],
            "duration_s": round(pr["duration"], 2), "bytes": os.path.getsize(dest), "file": name, "best_span": best_span, "note": note,
        })
        print("ok %s %.1fs %s" % (name, pr["duration"], c["licence"]))
    with open(os.path.join(REFS, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"files": entries, "cross_refs": CROSS_REFS,
                   "empty_rows": [r for r in ROWS if not any(e["row"] == r for e in entries)]}, f, indent=2, ensure_ascii=False)
        f.write("\n")
    write_readme(entries)
    cmd_verify()


def write_readme(entries):
    cell = lambda s: str(s).replace("|", "/")
    lines = [
        "# Audition recordings: WW1 and WW2 equipment",
        "",
        "Real recordings of real equipment for Dave to judge by ear. Not the shipped library.",
        "Chosen from titles, tags and descriptions only. Nobody has listened to them yet.",
        "Freesound files are HQ MP3 previews re-encoded; Commons and archive.org files are originals converted to MP3.",
        "Originals as downloaded are in `orig/`. `exact` is yes when the recording is the equipment the row names.",
        "Author craigsmith is the USC film sound-effects library; uncompressed WAVs of the same clips are on archive.org (collection usc-sound-effect-archive, CC0).",
        "",
        "| File | Row | Nation | Family | Equipment | Exact | Licence | Seconds | Author | Page | Best span | Note |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for e in entries:
        lic = "[%s](%s)" % (e["licence"], e["licence_url"])
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %.1f | %s | %s | %s | %s |" % (
            e["file"], e["row"], e["nation"], e["family"], cell(e["equipment"]), "yes" if e["exact"] else "no", lic, e["duration_s"],
            cell(e["author"]), e["page"], cell(e["best_span"] or ""), cell(e["note"])))
    lines += ["", "## Cross-references", ""] + ["- %s: %s" % kv for kv in CROSS_REFS.items()]
    empty = [r for r in ROWS if not any(e["row"] == r for e in entries)]
    lines += ["", "## Rows with no acceptable recording", "", ", ".join(empty) if empty else "None."]
    with open(os.path.join(REFS, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def cmd_verify():
    with open(os.path.join(REFS, "manifest.json"), encoding="utf-8") as f:
        entries = json.load(f)["files"]
    bad = 0
    for e in entries:
        path = os.path.join(REFS, e["file"])
        pr = probe(path) if os.path.exists(path) and os.path.getsize(path) > 0 else None
        lic = licence_of(e["licence_url"], e["licence"]) or (PD_SHORT.match(e["licence"]) and "commons.wikimedia.org" in e["licence_url"])
        hard, _ = flags(e["title"] + " " + e["note"] + " " + e["equipment"])
        ok = bool(pr and pr["codec"] == "mp3" and "mp3" in pr["format"] and abs(pr["duration"] - e["duration_s"]) < 0.05
                  and os.path.getsize(path) == e["bytes"] and lic and not hard)
        if not ok:
            bad += 1
            print("FAIL", e["file"], pr, bool(lic), hard)
    key = read_key()
    leaked = []
    for root, _, files in os.walk(HERE):
        for fn in files:
            p = os.path.join(root, fn)
            if os.path.getsize(p) < 5 * 1024 * 1024 and not p.endswith((".mp3", ".png")):
                with open(p, "rb") as f:
                    if key.encode() in f.read():
                        leaked.append(p)
    counts = {}
    for e in entries:
        counts[e["row"]] = counts.get(e["row"], 0) + 1
    print("verify: %d files, %d failures, key found in %d files, counts=%s" % (len(entries), bad, len(leaked), json.dumps(counts)))
    for p in leaked:
        print("KEY LEAK", p)
    if bad or leaked:
        sys.exit(1)


if __name__ == "__main__":
    a = sys.argv[1:]
    cmd = a[0] if a else ""
    if cmd == "search":
        cmd_search(a[1:])
    elif cmd == "q":
        fn = {"fs": lambda q: fs_search(q, read_key()), "commons": commons_search, "archive": archive_search}[a[1]]
        for c in fn(a[2]):
            if len(a) > 3 or not c["hard"]:
                print(line(c))
    elif cmd == "show":
        cmd_show(a[1], a[2] if len(a) > 2 and a[2] != "all" else None, a[-1] == "all")
    elif cmd == "info":
        print(json.dumps(lookup(a[1], a[2]), indent=1, ensure_ascii=False))
    elif cmd == "brief":
        key = read_key()
        for cid in a[2:]:
            c = lookup(a[1], cid, key)
            print("%s | %s | %ss | %s | %s | HARD %s soft %s\n   %s" % (cid, c["licence"], c["duration"], c["title"], c["author"],
                                                                     c["hard"], c["soft"], c["text"][:700]) if c else cid + " REJECTED")
    elif cmd == "fetch":
        cmd_fetch()
    elif cmd == "verify":
        cmd_verify()
    else:
        sys.exit(__doc__)
