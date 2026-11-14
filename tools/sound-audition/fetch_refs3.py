#!/usr/bin/env python3
"""Find and fetch freely licensed recordings of real WW1 and WW2 equipment.

  python3 -I fetch_refs3.py search [row ...]        run every query in ROWS, cache to candidates3.json
  python3 -I fetch_refs3.py q <fs|commons|archive> "<query>"   one ad-hoc query, printed, not cached
  python3 -I fetch_refs3.py show <row> [regex] [all]  print cached candidates for a row
  python3 -I fetch_refs3.py info <source> <id>      print full text of one candidate
  python3 -I fetch_refs3.py fetch                   download PICKS into refs3/, convert, write manifest
  python3 -I fetch_refs3.py verify                  re-check refs3/ against its manifest

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
REFS = os.path.join(HERE, "refs3")
ORIG = os.path.join(REFS, "orig")
CANDIDATES = os.path.join(HERE, "candidates3.json")
PRIOR_MANIFEST = os.path.join(HERE, "refs", "manifest.json")
PRIOR_MANIFEST2 = os.path.join(HERE, "refs2", "manifest.json")
SOURCES = os.path.join(REFS, "sources.json")
UA = "sound-ref-fetch/0.3"
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
    "deaths", "dead", "kill", "killed", "killing", "screamed", "yelling", "shout", "shouts", "pa", "narrator", "narration",
    "created from", "created by", "mixed together", "mixed in", "slowed", "pitch shifted", "pitched down", "amplified using",
    "processed in", "with enough effects", "funny noises", "reverb added", "added reverb", "chatter", "commands", "command voices",
]
# The observer is never in the fight: nothing that arrives at, passes or hits near the listener.
INCOMING = [
    "incoming", "whine", "whines", "whining", "whiz", "whizz", "whizzing", "whizzes", "ricochet", "ricochets", "ricocheting",
    "supersonic", "receiving end", "under fire", "hit nearby", "hits nearby", "fall nearby", "falls nearby", "whistle",
    "whistles", "whistling", "bullets passing", "bullet passing", "bullets fly", "bullet fly", "bullets flying", "bullet flyby",
    "bullet fly-by", "bullet fly by", "fly over", "flies over", "files over", "zoom past", "zooms past", "shells zoom", "bullet flybys", "shell flyby", "shell fly-by", "shells fly", "shell flies", "flies overhead",
    "fly overhead", "shells overhead", "shell overhead", "shell in flight", "crack overhead", "bullet crack", "bullet impacts",
    "bullet impact", "bullet hits", "near miss", "near misses", "fly by and explode",
]
SOFT = ["film", "movie", "blank", "blanks", "reenactment", "re-enactment", "airshow", "air show", "crowd",
        "voices", "speech", "processed", "mixed", "edited", "newsreel", "museum", "replica"]


def word_re(words):
    return re.compile(r"(?<![a-z0-9])(" + "|".join(re.escape(w) for w in words) + r")(?![a-z0-9])")


HARD_RE = word_re(HARD + INCOMING)
SOFT_RE = word_re(SOFT)

DISTANT_RE = re.compile(r"(?<![a-z])(distant|distance|far|far away|faraway|far-off|far off|afar|from (a|the) distance|across (the|a) "
                        r"(valley|range|field|lake|bay|water)|heard from shore|from shore|from the shore|"
                        r"\d{3,}\s?(m|metres|meters|yards|yds|km)|\d+\s?(km|kilometres|kilometers|miles))(?![a-z])")
MEDIUM_RE = re.compile(r"(?<![a-z])(medium|mid[- ]distance|not close|some distance|echo|echoes|echoing|natural reverb|reverb|"
                       r"valley|range|\d{2}\s?(m|metres|meters|yards))(?![a-z])")
CLOSE_RE = re.compile(r"(?<![a-z])(close|close-up|closeup|close up|near|up close|onboard|on board|interior|inside|indoors|"
                      r"\d\s?(m|metres|meters))(?![a-z])")


def distance_of(text):
    """Perspective from the description only: distant, medium, close or unknown."""
    t = (text or "").lower()
    if DISTANT_RE.search(t):
        return "distant"
    if re.search(r"(?<![a-z])(indoor|indoors|inside|interior)(?![a-z])", t):
        return "close"
    if MEDIUM_RE.search(t):
        return "medium"
    if CLOSE_RE.search(t):
        return "close"
    return "unknown"

# row: (era, nation, family, freesound queries, commons queries)
ROWS = {
    "US1": ("ww2", "US", "rifle",
            ["garand", "m1 garand", "garand firing", "garand shots", "m1 garand range", "30-06 rifle", "30-06 shots", "m1 rifle",
             "garand distant", "rifle volley", "firing squad", "rifle salute", "three volley salute", "21 gun salute rifle",
             "honor guard volley", "user:craigsmith rifle", "user:YleArkisto kivääri", "user:YleArkisto rifle"],
            ["Garand", "M1 rifle", "rifle volley", "three-volley salute", "firing party salute"]),
    "US2": ("ww2", "US", "mg",
            ["m1919", "browning m1919", "browning .30", "30 cal machine gun", "m2 browning", ".50 cal", "50 cal", "50 caliber",
             "m2hb", "heavy machine gun distant", "machine gun distant", "machine gun range", "machine gun far",
             "user:craigsmith machine gun", "user:craigsmith browning"],
            ["M1919", "M2 Browning", "Browning machine gun", ".50 caliber machine gun", "heavy machine gun firing"]),
    "US3": ("ww2", "US", "tank-engine",
            ["sherman", "m4 sherman", "sherman tank", "m4a4", "m4a1", "m4a3", "stuart tank", "m5 stuart", "m24 chaffee", "chaffee",
             "m10 wolverine", "m36 jackson", "m18 hellcat", "continental r975", "tank pass distant", "tank approaching",
             "tank passing", "tank tracks distant", "tracked vehicle distant", "user:craigsmith tank", "user:YleArkisto panssarivaunu"],
            ["Sherman tank", "M4 Sherman", "Stuart tank", "Chaffee tank", "tank driving", "Beeld en Geluid tank", "tank rijden"]),
    "US5": ("ww2", "US", "howitzer",
            ["105mm howitzer", "105 mm", "m101 howitzer", "m2a1 howitzer", "pack howitzer", "75mm pack howitzer", "155mm",
             "howitzer distant", "artillery distant", "distant artillery", "artillery far", "artillery range", "cannon distant",
             "distant cannon", "distant gunfire", "gun salute distant", "salute battery", "user:craigsmith artillery",
             "user:craigsmith cannon", "user:craigsmith howitzer", "user:YleArkisto tykki", "user:YleArkisto artillery"],
            ["howitzer firing", "105 mm howitzer", "M101 howitzer", "artillery firing", "gun salute", "salute battery"]),
    "US7": ("ww2", "US", "naval-gun",
            ["naval gun", "naval gunfire", "battleship", "battleship guns", "uss iowa", "uss new jersey", "16 inch", "5 inch",
             "5 inch gun", "destroyer", "destroyer gun", "cruiser", "warship", "ship cannon", "naval salute", "ship salute",
             "naval bombardment", "naval artillery", "coastal artillery", "user:craigsmith navy", "user:craigsmith naval",
             "user:craigsmith ship gun", "user:YleArkisto rannikkotykki"],
            ["naval gun firing", "battleship firing", "5-inch gun", "naval gunfire", "16-inch gun", "warship salute",
             "coastal artillery firing"]),
    "UK1": ("both", "UK", "rifle",
            ["lee-enfield", "lee enfield", "enfield rifle", "smle", ".303", "303 rifle", "no4 mk1", "no 4 rifle", "enfield shots",
             "enfield firing", "mad minute", "british rifle", "rifle range distant"],
            ["Lee-Enfield", "SMLE", ".303 rifle", "Lee Enfield firing"]),
    "UK3": ("ww2", "UK", "field-gun",
            ["25 pounder", "25-pounder", "25pdr", "25 pdr", "ordnance qf", "sexton", "field gun", "field gun firing",
             "royal artillery", "artillery salute", "gun salute", "royal salute", "l118", "light gun", "tankfest gun",
             "artillery demonstration"],
            ["25-pounder", "25 pounder", "Ordnance QF 25", "Sexton", "field gun firing", "gun salute", "L118", "Royal Artillery"]),
    "DE1": ("both", "DE", "rifle",
            ["k98", "kar98", "kar98k", "kar 98", "karabiner 98", "mauser", "mauser rifle", "mauser m96", "swedish mauser",
             "m96 mauser", "8mm mauser", "7.92", "gewehr 98", "gew 98", "mauser 98", "mosin", "mosin nagant", "bolt action rifle",
             "bolt action shots", "user:YleArkisto kivääri"],
            ["Karabiner 98", "Mauser", "Gewehr 98", "K98", "Mauser rifle firing", "bolt-action rifle"]),
    "W5": ("great-war", "FR", "field-gun",
           ["french 75", "canon de 75", "75mm field gun", "75 mm gun", "75mm gun", "soixante-quinze", "canon 75", "m1897",
            "m1897 75mm", "schneider", "canon", "tir canon", "artillerie", "user:craigsmith 75mm"],
           ["Canon de 75", "French 75", "canon 75", "M1897 gun", "artillerie tir", "canon de campagne"]),
    "W6": ("great-war", "US", "rifle",
           ["springfield", "m1903", "1903 springfield", "springfield rifle", "springfield 1903", "03-a3", "1903a3", "springfield shots",
            "30-06 bolt", "krag", "krag jorgensen"],
           ["Springfield M1903", "M1903", "Springfield rifle"]),
    "W9": ("great-war", "DE", "mg",
           ["mg08", "mg 08", "maxim", "maxim gun", "maxim machine gun", "pm1910", "pm m1910", "m/09-09", "m/32-33", "maxim m32",
            "konekivääri", "water cooled machine gun", "spandau", "user:YleArkisto konekivääri", "user:YleArkisto maxim",
            "user:poissonmort maxim"],
           ["MG 08", "Maxim gun", "Maxim machine gun", "Maxim firing", "konekivääri"]),
    "W10": ("great-war", "DE", "field-gun",
            ["7.7 cm", "feldkanone", "fk 96", "18 pounder", "13 pounder", "77mm", "76 mm", "76mm", "ww1 field gun", "ww1 artillery",
             "field gun firing", "first world war gun", "great war artillery", "old cannon firing", "antique cannon", "cannon fire distant",
             "user:YleArkisto tykki", "user:YleArkisto kenttätykki", "user:YleArkisto 76"],
            ["Feldkanone", "7.7 cm", "field gun firing", "World War I artillery", "76 mm divisional gun", "kenttätykki"]),
    "DE2": ("ww2", "DE", "mg",
            ["mg42", "mg 42", "mg-42", "mg34", "mg 34", "mg-34", "mg3", "mg 3", "mg-3", "mg3 machine gun", "rheinmetall mg3",
             "m53 machine gun", "zastava m53", "buzz saw machine gun", "hitler saw", "german machine gun", "bundeswehr mg",
             "maschinengewehr", "mg 74", "user:YleArkisto konekivääri"],
            ["MG 42", "MG 34", "MG3", "Maschinengewehr", "MG3 Bundeswehr", "Rheinmetall MG 3", "Zastava M53"]),
    "DE3": ("ww2", "DE", "tank-engine",
            ["panzer", "panther tank", "tiger tank", "tiger 131", "stug", "stug iii", "stug 3", "maybach", "panzer iv", "panzer iii",
             "hetzer", "jagdpanzer 38", "g13 hetzer", "sdkfz", "sd.kfz", "sd kfz 251", "halftrack german", "hanomag", "kettenkrad",
             "german tank", "wehrmacht tank", "user:YleArkisto stug", "user:YleArkisto rynnäkkötykki"],
            ["Panzer", "Panther tank", "Tiger tank", "Maybach", "Sd.Kfz. 251", "Kettenkrad", "StuG III", "Hetzer", "Sturmgeschütz",
             "Hanomag halftrack"]),
    "DE4": ("ww2", "DE", "field-gun",
            ["88mm", "flak 88", "flak 18", "flak 36", "8.8 cm", "pak 40", "pak 38", "7.5 cm", "lefh 18", "10.5 cm", "flak 38",
             "20mm flak", "german cannon", "german artillery", "german gun", "wehrmacht gun", "flak gun", "anti aircraft gun ww2",
             "bofors 40mm", "user:YleArkisto ilmatorjunta", "user:YleArkisto ilmatorjuntatykki"],
            ["Flak", "8.8 cm Flak", "Pak 40", "88 mm gun", "leFH 18", "Flak 38", "German artillery firing"]),
    "DE5": ("ww2", "DE", "rocket",
            ["nebelwerfer", "wurfrahmen", "screaming mimi", "katyusha", "bm-13", "bm13", "stalin organ", "stalinorgel",
             "rocket artillery", "rocket launch distant", "rockets salvo", "rocket salvo", "multiple rocket launcher",
             "user:YleArkisto raketinheitin"],
            ["Nebelwerfer", "Katyusha", "BM-13", "rocket artillery", "Stalinorgel"]),
    "W2": ("great-war", "UK", "mg",
           ["vickers", "vickers machine gun", "vickers gun", "vickers mg", "vickers mk1", "vickers .303", "vickers firing",
            "water cooled machine gun", "browning 1917", "m1917 browning", "colt 1895"],
           ["Vickers machine gun", "Vickers gun", "Vickers firing", "M1917 Browning"]),
    "W3": ("great-war", "UK", "mg",
           ["lewis gun", "lewis machine gun", "lewis lmg", "lewis gun firing", "lewis .303", "lewis gun ww1"],
           ["Lewis gun", "Lewis gun firing", "Lewis machine gun"]),
    "W7": ("great-war", "FR", "mg",
           ["chauchat", "hotchkiss", "hotchkiss machine gun", "hotchkiss m1914", "hotchkiss mle 1914", "st etienne mle 1907",
            "mitrailleuse", "mitrailleuse hotchkiss", "fusil mitrailleur", "lebel", "berthier", "user:YleArkisto pikakivääri"],
           ["Chauchat", "Hotchkiss machine gun", "Hotchkiss M1914", "mitrailleuse", "Lebel rifle"]),
    "W4": ("great-war", "UK", "field-gun",
           ["18 pounder", "18-pounder", "13 pounder", "13-pounder", "king's troop", "kings troop", "royal horse artillery",
            "royal gun salute", "41 gun salute", "62 gun salute", "21 gun salute", "hyde park salute", "green park salute",
            "gun salute london", "royal salute"],
           ["18-pounder", "13-pounder", "King's Troop", "King's Troop Royal Horse Artillery", "gun salute", "Royal salute Hyde Park",
            "Ordnance QF 13-pounder"]),
    "W11": ("great-war", "UK", "tank-engine",
            ["mark iv tank", "mark v tank", "ww1 tank", "renault ft", "ft-17", "ft17", "renault ft-17", "schneider ca1", "whippet",
             "medium mark a", "first world war tank", "great war tank", "daimler engine", "ricardo engine", "tank museum",
             "bovington", "tankfest", "steam traction engine", "vintage tractor", "old tractor engine", "hart parr", "holt tractor"],
            ["Mark IV tank", "Mark V tank", "Renault FT", "Schneider CA1", "World War I tank", "Whippet tank", "Holt tractor"]),
}

# archive.org full-text search returns mostly music and talk, so it is limited to the USC film
# sound-effects collection (CC0), whose item descriptions list every file name.
ARCHIVE_COLLECTION = "usc-sound-effect-archive"
# Items in that collection whose file names name weapons or armour. Each row lists files of these items
# whose name matches its pattern. Item listing came from the collection's advancedsearch on 2026-11-14.
ARCHIVE_GUN_ITEMS = ["Red_Library_Guns_Artillery", "Red_Library_Guns_Machine", "Red_Library_Guns_Misc", "GOLD_TAPE_33_Explosions_and_War",
                     "GOLD_TAPE_35_Gun_Shots", "SSE_Library_GUNS", "SSE_Library_AMBIENCE", "Red_Library_Ambience_1",
                     "Red_Library_Ambience_2", "Red_Library_Ambience_3", "SSE_Library_BOATS"]
ARCHIVE_VEHICLE_ITEMS = ["GOLD_TAPE_15_Tanks_Bulldozers", "SSE_Library_VEHICLES"]
ARCHIVE_ROWS = {
    "US1": (ARCHIVE_GUN_ITEMS, r"rifle"), "UK1": (ARCHIVE_GUN_ITEMS, r"rifle|british"), "DE1": (ARCHIVE_GUN_ITEMS, r"rifle"),
    "W6": (ARCHIVE_GUN_ITEMS, r"rifle"),
    "US2": (ARCHIVE_GUN_ITEMS, r"machine gun|browning|50 cal"), "W9": (ARCHIVE_GUN_ITEMS, r"machine gun"),
    "DE2": (ARCHIVE_GUN_ITEMS, r"machine gun|rapid"), "W2": (ARCHIVE_GUN_ITEMS, r"machine gun"), "W3": (ARCHIVE_GUN_ITEMS, r"machine gun"),
    "W7": (ARCHIVE_GUN_ITEMS, r"machine gun"),
    "US5": (ARCHIVE_GUN_ITEMS, r"howitzer|artillery|cannon|large gun|75mm|105mm|barrage|bombardment"),
    "UK3": (ARCHIVE_GUN_ITEMS, r"artillery|cannon|large gun|75mm|105mm"), "W4": (ARCHIVE_GUN_ITEMS, r"artillery|cannon|75mm"),
    "W5": (ARCHIVE_GUN_ITEMS, r"75mm|artillery|cannon"), "W10": (ARCHIVE_GUN_ITEMS, r"artillery|cannon|75mm|large gun"),
    "DE4": (ARCHIVE_GUN_ITEMS, r"artillery|cannon|anti tank|anti-tank|large gun|automatic artillery"),
    "DE5": (ARCHIVE_GUN_ITEMS, r"rocket|bazooka"),
    "US7": (ARCHIVE_GUN_ITEMS, r"nav|ship|5 inch|destroyer|cannon|large gun"),
    "US3": (ARCHIVE_VEHICLE_ITEMS, r"tank|m-4"), "DE3": (ARCHIVE_VEHICLE_ITEMS, r"tank"), "W11": (ARCHIVE_VEHICLE_ITEMS, r"tank"),
}

CROSS_REFS = {
    "W1": "Same weapon family as UK1 (Lee-Enfield). Use the UK1 files.",
    "W8": "Same Mauser 98 action and 7.92 mm cartridge as DE1. Use the DE1 files.",
    "W5": "refs2/US4-1-freesound486031.mp3 (USC '75mm gun fires three times') is the best French 75 stand-in already on disk: "
          "the US 75 mm M1897 was the French Canon de 75 mle 1897 built under licence. Not re-downloaded.",
    "refs2-incoming": "Under the new observer rule these earlier picks describe incoming fire and should be dropped or trimmed: "
                      "refs2/W5-1 (486023, 'shell flies through air, explodes'), refs2/US7-1 (675606, 'with shell whines'), "
                      "refs2/W12-3 (674897, 'Incoming shells').",
}

USC_NOTE = ("USC Cinema / Sunset Editorial film sound-effects library (optical/35 mm mag transfers, likely 1940s-60s), "
            "original WAV from archive.org. Library card text from the freesound copy (craigsmith %s). Recording date and place unknown.")

# archive.org USC file -> the same clip on freesound (craigsmith), whose description carries the library card text.
ARCHIVE_DESC = {
    "GOLD_TAPE_15_Tanks_Bulldozers/G15-25-M-4 Tank Slow Drive By.wav": "438121",
    "GOLD_TAPE_15_Tanks_Bulldozers/G15-21-Light Tank.wav": "438117",
    "GOLD_TAPE_35_Gun_Shots/G35-06-Low Rifle Shots.wav": "438570",
    "SSE_Library_GUNS/AUTOMATIC/GUNAuto_Machine gun fire; not close; dull_CS_USC.wav": "675598",
    "SSE_Library_GUNS/AUTOMATIC/GUNAuto_Various groups of machine guns; medium distance_CS_USC.wav": "675604",
    "SSE_Library_GUNS/CANNON/GUNCano_Distant cannon fire_CS_USC.wav": "675613",
    "SSE_Library_BOATS/SUBMARINE/BOATSub_Destroyer horn blasts warning for 5 inch_CS_USC.wav": "675788",
    "Red_Library_Guns_Artillery/R12-07-Artillery Single Shots.wav": "486019",
}

BG = "Netherlands Institute for Sound and Vision (Beeld en Geluid) effects archive via Commons; date not given."
YLE = "Finnish Broadcasting Company (Yle) sound-effects archive."

# (row, n, source, id, equipment, exact, distance or None to derive from text, best_span, note)
PICKS = [
    ("US1", 1, "archive", "GOLD_TAPE_35_Gun_Shots/G35-06-Low Rifle Shots.wav", "Rifle, type not named, low muffled shots in the distance",
     False, "distant", None, USC_NOTE % "438570" + " Rifle model unknown; a period US film library, so a Springfield or Garand is plausible but not stated."),
    ("US1", 2, "commons", "File:3 Volley Salute - US Army Funeral.ogg", "US Army rifle party, three-volley salute",
     False, None, None, "US Army recording (public domain). Rifle not named; honour guards use M1 Garands or M14s. A squad firing together, "
     "three times. Funeral setting, so taps or speech may follow the volleys."),
    ("US1", 3, "freesound", "854204", "Rifle volley on a target range, US military training video",
     False, "unknown", None, "Audio lifted by qubodup from a US military video (public domain). Modern service rifles, not Garands."),
    ("US1", 4, "freesound", "385785", "M1 Garand single shot",
     True, None, None, "Uploader gives no recording details. 3 s, one shot."),
    ("US2", 1, "freesound", "160355", ".50 calibre Browning, Avenger air-defence system, bursts with echo",
     True, "medium", None, "Audio lifted by qubodup from a US Army training video (public domain). M3P, a Browning M2 derivative; modern."),
    ("US2", 2, "archive", "SSE_Library_GUNS/AUTOMATIC/GUNAuto_Machine gun fire; not close; dull_CS_USC.wav", "Machine gun fire, not close, dull",
     False, "medium", None, USC_NOTE % "675598" + " Gun type not named."),
    ("US2", 3, "archive", "SSE_Library_GUNS/AUTOMATIC/GUNAuto_Various groups of machine guns; medium distance_CS_USC.wav",
     "Several groups of machine guns at medium distance", False, "medium", None, USC_NOTE % "675604" + " Gun types not named."),
    ("US3", 1, "commons", "File:Sherman tank, met grote snelheid rijden - SoundCloud - Beeld en Geluid.ogg",
     "M4 Sherman approaching at speed from a great distance and passing, concrete road", True, "distant", None,
     BG + " Same session as the long approach Dave kept (refs2 US3-1). Description: 'van grote afstand met grote snelheid aankomen en voorbijrijden'."),
    ("US3", 2, "commons", "File:Sherman tank, rijden, stationair en stoppen - SoundCloud - Beeld en Geluid.ogg",
     "M4 Sherman approaching from a great distance, stopping in front, idling, driving off", True, "distant", None,
     BG + " Order per description: long approach, stop, about 1:20 of idle, drive away. No timestamps given, so no best span."),
    ("US3", 3, "commons", "File:Het rijden van een colonne Sherman tanks - SoundCloud - Beeld en Geluid.ogg",
     "Column of M4 Shermans driving past on a concrete road", True, None, None, BG + " Several tanks, so a denser din. Distance not stated."),
    ("US3", 4, "archive", "GOLD_TAPE_15_Tanks_Bulldozers/G15-25-M-4 Tank Slow Drive By.wav",
     "M4 medium tank: very long approach with sputtering engine, to close up", True, "distant", None,
     USC_NOTE % "438121" + " Ends close up; the approach is the useful part."),
    ("US3", 5, "archive", "GOLD_TAPE_15_Tanks_Bulldozers/G15-21-Light Tank.wav", "US light tank idling in the distance, then driving by slowly",
     False, "distant", None, USC_NOTE % "438117" + " Model not named (M3/M5 Stuart likely, assumed). Library notes some squeaks."),
    ("US5", 1, "freesound", "95129", "Salute battery, '70mm' salute cannons, about half a mile away in a river valley",
     False, "distant", None, "Hudson River valley; the uploader says 70mm. Possibly the West Point salute battery (assumed, not stated). "
     "Salute charges, not service rounds."),
    ("US5", 2, "archive", "SSE_Library_GUNS/CANNON/GUNCano_Distant cannon fire_CS_USC.wav", "Distant cannon fire, gun not named",
     False, "distant", None, USC_NOTE % "675613"),
    ("US5", 3, "freesound", "332934", "155 mm field gun, two shots with a long heavy echo",
     False, "medium", None, YLE + " Nagra tape, Rovajärvi range, Finland, 1957. Model not stated (KT 155 mm). Heavier than a 105."),
    ("US7", 1, "archive", "SSE_Library_BOATS/SUBMARINE/BOATSub_Destroyer horn blasts warning for 5 inch_CS_USC.wav",
     "Destroyer: horn blasts warning that the 5-inch guns are about to fire", True, None, None,
     USC_NOTE % "675788" + " Least sure pick: the card names the warning horn, and the gunfire itself may not be on the clip."),
    ("UK1", 1, "freesound", "450851", "Lee-Enfield .303 shot, loud", True, None, None, "Same uploader and session as the two UK1 clips Dave has. Mark not stated."),
    ("UK1", 2, "freesound", "450854", "Lee-Enfield .303 shot", True, None, None, "Same uploader and session as the two UK1 clips Dave has. Mark not stated."),
    ("DE1", 1, "freesound", "338240", "Mosin and Mauser rifles exchanging fire in a forest, WW2 re-enactment",
     False, "unknown", None, "Recorded near Lviv for a documentary; blanks assumed. Mauser and Mosin mixed, several shots."),
    ("DE1", 2, "freesound", "255265", "Mosin-Nagant 7.62x54R, echoing solid single shots outdoors",
     False, "medium", None, YLE + " Nagra tape, Vihti, Finland, 12 Oct 1988. Mosin, not Mauser: a bolt-action stand-in."),
    ("DE1", 3, "freesound", "255264", "Rifle, sometimes two, firing further away with echo (Mosin-Nagant)",
     False, "distant", None, YLE + " Archive compilation of analogue tapes ('kooste'), edited by the archive. 'ammutaan kauempana' = fired further away."),
    ("W5", 1, "archive", "Red_Library_Guns_Artillery/R12-07-Artillery Single Shots.wav", "Single artillery shots, gun not named",
     False, None, None, USC_NOTE % "486019" + " Weak stand-in; see the W5 cross-reference for a named 75 mm."),
    ("W6", 1, "freesound", "399067", "Sako .30-06 bolt-action rifle shot, outdoors",
     False, "unknown", None, "Same .30-06 cartridge as the Springfield. 'Shot at 100 meters' is the target distance, not the microphone's (assumed)."),
    ("W9", 1, "freesound", "255269", "Russian Maxim, sustained fire with echo; last bursts further away",
     False, "medium", None, YLE + " Nagra tape, Hameenlinna, 1 Nov 1984; same session as the refs2 W9 clips. Not the MG 08."),
    ("W10", 1, "freesound", "634629", "ZiS-3 76 mm divisional guns firing a salute, 1.2 km away",
     False, "distant", None, "Victory Day 2022 salute, ORTF pair. WW2 Soviet 76 mm, standing in for a WW1 field gun. Fireworks may also be "
     "audible (Moscow salutes pair them); not stated."),
    ("W10", 2, "freesound", "258205", "Artillery firing at the front, continuous gunfire with echo",
     False, "medium", None, YLE + " Archive compilation ('kooste') of analogue tapes, edited by the archive; guns not named."),
]

# Per-row notes for the README: what the search turned up when nothing was kept, or why picks are stand-ins.
SEARCH_NOTES = {
    "US7": "Rejected: qubodup 162365 battleship soundscape (radio chatter and command voices), USC 8-inch with shell whines "
           "(already refs2 US7-1), USC '8\" gun; cannon' (675607; ship not stated). Commons had no naval gunfire audio.",
    "UK3": "No 25-pounder firing beyond refs2 UK3-1 (Sexton at Fort Nelson). Commons 'Sexton artillery moving' is the vehicle, not the gun.",
    "W4": "No 13- or 18-pounder recording. King's Troop salutes appear only as video on Commons; no audio file. "
          "freesound 43783 (US Veterans Day 21-gun salute) skipped: parade noise and gun type unknown.",
    "DE2": "Only MG 42 hits were layered or game audio (freesound 338242 'real MG 42 + few additional layers', 387508). "
           "Every 'mg3' hit was a Morphagene reel or guitar amp. freesound 338241 (heavy machine guns at a WW2 re-enactment) skipped: type not named.",
    "DE3": "No German tank or halftrack. Commons 'Panther' hits are Rilke readings. freesound 329800 is a Soviet T-26, not German.",
    "DE4": "No German gun. 'flak' hits were game voice lines and synthetic noise.",
    "DE5": "No Nebelwerfer or Katyusha. Only modern HIMARS launches (qubodup 854469-854476), which the row excludes.",
    "W2": "'Vickers' only matched a recordist's surname and an airliner. No Vickers gun or M1917 audio on freesound or Commons.",
    "W3": "No Lewis gun audio on freesound or Commons.",
    "W7": "No Chauchat or Hotchkiss audio on freesound or Commons.",
    "W11": "No WW1 tank. Beeld en Geluid has Centurion and Sherman only.",
    "W6": "No Springfield shots beyond refs2 W6-1. 'springfield' hits were places and M1911 pistols.",
}


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
            if (e.code >= 500 or e.code == 429) and attempt < 2:
                time.sleep(15 * (attempt + 1))
                continue
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
    if not meta.get("files"):
        sys.exit("archive.org returned no file list for " + identifier)
    md = meta.get("metadata") or {}
    lic = licence_of(md.get("licenseurl") if isinstance(md.get("licenseurl"), str) else "")
    if not lic:
        return []
    text = "collection: " + str(md.get("collection")) + " || uploader: " + str(md.get("uploader"))
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


ARCHIVE_CACHE = {}


def archive_row(row):
    items, pattern = ARCHIVE_ROWS.get(row, ([], None))
    out = []
    for ident in items:
        if ident not in ARCHIVE_CACHE:
            ARCHIVE_CACHE[ident] = archive_item(ident)
        out += [c for c in ARCHIVE_CACHE[ident] if re.search(pattern, c["id"].split("/", 1)[1], re.I)]
    return out


def prior_ids():
    """Keys (source:id) already downloaded into refs/ or refs2/."""
    keys = set()
    try:
        with open(PRIOR_MANIFEST, encoding="utf-8") as f:
            keys |= {"freesound:%s" % e["freesound_id"] for e in json.load(f)}
    except FileNotFoundError:
        pass
    try:
        with open(PRIOR_MANIFEST2, encoding="utf-8") as f:
            for e in json.load(f)["files"]:
                if e["source"] == "freesound":
                    keys.add("freesound:" + re.search(r"/s/(\d+)/", e["page"]).group(1))
                else:
                    keys.add(e["source"] + ":" + e["title"])
    except FileNotFoundError:
        pass
    return keys


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
        aq = [row] if row in ARCHIVE_ROWS else []
        if only and row not in only:
            continue
        found = {}
        n = {"freesound": 0, "commons": 0, "archive": 0}
        for src, queries, fn in (("freesound", fsq, lambda q: fs_search(q, key)), ("commons", cq, commons_search), ("archive", aq, archive_row)):
            for q in queries:
                for c in fn(q):
                    k = c["source"] + ":" + c["id"]
                    if k in skip:
                        continue
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
        if identifier not in ARCHIVE_CACHE:
            ARCHIVE_CACHE[identifier] = archive_item(identifier)
        for c in ARCHIVE_CACHE[identifier]:
            if c["id"] == cid:
                return c
    return None


def download(url, dest):
    p = urllib.parse.urlparse(url)
    host = p.hostname or ""
    if p.scheme != "https" or not any(host == h or host.endswith("." + h) for h in DOWNLOAD_HOSTS):
        sys.exit("refusing download host: %s" % host)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                final = urllib.parse.urlparse(r.geturl()).hostname or ""
                if not any(final == h or final.endswith("." + h) for h in DOWNLOAD_HOSTS):
                    sys.exit("redirected to refused host: %s" % final)
                data = r.read(MAX_BYTES + 1)
            break
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if attempt == 3:
                sys.exit("download failed %s: %s" % (url, e))
            time.sleep(10 * (attempt + 1))
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


DISTANCE_RANK = {"distant": 0, "medium": 1, "unknown": 2, "close": 3}


def cmd_fetch():
    key = read_key()
    os.makedirs(ORIG, exist_ok=True)
    skip = prior_ids()
    entries, sources = [], {}
    for row, n, source, cid, equipment, exact, distance, best_span, note in PICKS:
        era, nation, family = ROWS[row][:3]
        if source + ":" + cid in skip:
            sys.exit("already downloaded in refs/ or refs2/: %s %s" % (source, cid))
        c = lookup(source, cid, key)
        if not c:
            sys.exit("licence not accepted or not found: %s %s" % (source, cid))
        if source == "archive":
            # archive.org file names are terse; the same USC clip on freesound (craigsmith) carries the library card text.
            mirror = ARCHIVE_DESC.get(cid)
            if not mirror:
                sys.exit("archive pick has no freesound description mirror: " + cid)
            if "freesound:" + mirror in skip:
                sys.exit("archive pick is the same clip as freesound %s, already downloaded" % mirror)
            m = lookup("freesound", mirror, key)
            stem = os.path.splitext(cid.split("/")[-1])[0].replace("_CS_USC", "").lower()
            if not m or not (m["title"].lower().startswith(stem[:12]) or stem[:12] in m["title"].lower()
                             or re.sub(r"^[a-z]+_", "", stem.split("/")[-1])[:20] in m["title"].lower()):
                sys.exit("mirror %s does not match %s (%s)" % (mirror, cid, m and m["title"]))
            c["text"] += " || freesound mirror %s: %s || %s" % (mirror, m["title"], m["text"])
            c["hard"], c["soft"] = flags(c["title"] + " " + c["text"])
        if c["hard"]:
            sys.exit("content or incoming rule words in %s %s: %s" % (source, cid, c["hard"]))
        if c.get("duration") and c["duration"] > MAX_SECONDS:
            sys.exit("longer than %d s: %s %s" % (MAX_SECONDS, source, cid))
        distance = distance or distance_of(c["title"] + " " + c["text"])
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
        if pr["duration"] > MAX_SECONDS + 1:
            sys.exit("converted file longer than %d s: %s" % (MAX_SECONDS, name))
        entries.append({
            "row": row, "era": era, "nation": nation, "family": family, "equipment": equipment, "exact": exact, "source": source,
            "page": c["page"], "title": c["title"], "author": c["author"], "licence": c["licence"], "licence_url": c["licence_url"],
            "duration_s": round(pr["duration"], 2), "bytes": os.path.getsize(dest), "file": name, "best_span": best_span, "note": note,
            "distance": distance,
        })
        sources[name] = c["title"] + " || " + c["text"]
        print("ok %s %.1fs %s %s" % (name, pr["duration"], c["licence"], distance))
    with open(os.path.join(REFS, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with open(SOURCES, "w", encoding="utf-8") as f:
        json.dump(sources, f, indent=1, ensure_ascii=False)
        f.write("\n")
    write_readme(entries)
    cmd_verify()


def write_readme(entries):
    cell = lambda s: str(s).replace("|", "/")
    entries = sorted(entries, key=lambda e: (list(ROWS).index(e["row"]), DISTANCE_RANK[e["distance"]], e["file"]))
    lines = [
        "# Audition recordings, third pass: thin and empty World War rows",
        "",
        "New candidates for rows where Dave kept one clip or none. Nobody has listened to them yet;",
        "they were chosen from titles, tags and descriptions only.",
        "",
        "The observer hears the battle from above and far off, so distant recordings rank first within each row.",
        "`distance` comes from the description (distant, medium, close, unknown); it is not a measurement.",
        "Anything describing incoming fire (shell whistle or whine, bullets passing, ricochet) was rejected in code.",
        "",
        "Freesound files are HQ MP3 previews re-encoded. Commons and archive.org files are originals (archive.org: 24-bit 48 kHz mono WAV",
        "from the USC Cinema / Sunset Editorial sound-effects library, CC0) converted to MP3 (libmp3lame -q:a 2).",
        "Originals as downloaded are in `orig/`. `exact` is yes when the recording is the equipment the row names.",
        "",
        "| File | Row | Distance | Equipment | Exact | Licence | Seconds | Author | Page | Best span | Note |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for e in entries:
        lic = "[%s](%s)" % (e["licence"], e["licence_url"])
        lines.append("| %s | %s | %s | %s | %s | %s | %.1f | %s | %s | %s | %s |" % (
            e["file"], e["row"], e["distance"], cell(e["equipment"]), "yes" if e["exact"] else "no", lic, e["duration_s"],
            cell(e["author"]), e["page"], cell(e["best_span"] or ""), cell(e["note"])))
    lines += ["", "## Cross-references", ""] + ["- %s: %s" % kv for kv in CROSS_REFS.items()]
    lines += ["", "## Searched, per row", "",
              "Every row ran its freesound and Commons queries below. Rows with an archive.org pattern also scanned the",
              "USC library items: " + ", ".join(ARCHIVE_GUN_ITEMS + ARCHIVE_VEHICLE_ITEMS) + ".", ""]
    for row, (era, nation, family, fsq, cq) in ROWS.items():
        got = sum(1 for e in entries if e["row"] == row)
        lines.append("### %s (%s %s %s): %d new" % (row, era, nation, family, got))
        lines.append("")
        if row in SEARCH_NOTES:
            lines.append(SEARCH_NOTES[row])
            lines.append("")
        lines.append("- freesound: " + "; ".join(fsq))
        lines.append("- Commons: " + "; ".join(cq))
        if row in ARCHIVE_ROWS:
            lines.append("- archive.org file-name pattern: `%s`" % ARCHIVE_ROWS[row][1])
        lines.append("")
    with open(os.path.join(REFS, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def cmd_verify():
    with open(os.path.join(REFS, "manifest.json"), encoding="utf-8") as f:
        entries = json.load(f)
    with open(SOURCES, encoding="utf-8") as f:
        sources = json.load(f)
    skip = prior_ids()
    bad = 0
    for e in entries:
        path = os.path.join(REFS, e["file"])
        pr = probe(path) if os.path.exists(path) and os.path.getsize(path) > 0 else None
        lic = licence_of(e["licence_url"], e["licence"]) or (PD_SHORT.match(e["licence"]) and "commons.wikimedia.org" in e["licence_url"])
        hard, _ = flags(e["title"] + " " + e["note"] + " " + e["equipment"] + " " + sources.get(e["file"], ""))
        key_id = re.search(r"/s/(\d+)/", e["page"]).group(1) if e["source"] == "freesound" else (
            e["title"] if e["source"] == "commons" else None)
        dup = key_id is not None and (e["source"] + ":" + key_id) in skip
        ok = bool(pr and pr["codec"] == "mp3" and "mp3" in pr["format"] and abs(pr["duration"] - e["duration_s"]) < 0.05
                  and os.path.getsize(path) == e["bytes"] and lic and not hard and e["file"] in sources and not dup
                  and e["distance"] in DISTANCE_RANK and e["duration_s"] <= MAX_SECONDS + 1)
        if not ok:
            bad += 1
            print("FAIL", e["file"], pr, bool(lic), hard, "dup" if dup else "")
    key = read_key()
    leaked = []
    for root, _, files in os.walk(HERE):
        for fn in files:
            p = os.path.join(root, fn)
            if os.path.getsize(p) < 5 * 1024 * 1024 and not p.endswith((".mp3", ".png", ".wav")):
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
        fn = {"fs": lambda q: fs_search(q, read_key()), "commons": commons_search, "archive": archive_row}[a[1]]
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
