#!/usr/bin/env python3
"""Find and fetch freely licensed freesound.org reference recordings.

  python3 -I fetch_refs.py search          query the API, write candidates.json beside this script
  python3 -I fetch_refs.py show <prefix>   print surviving candidates for one sound
  python3 -I fetch_refs.py fetch           download PICKS into refs/, write manifest.json and README.md

Standard library only. The API key is read from ~/.config/freesound/api_key and
sent only as an Authorization header to freesound.org API URLs.
"""
import html
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REFS = os.path.join(HERE, "refs")
CANDIDATES = os.path.join(HERE, "candidates.json")
API = "https://freesound.org/apiv2"
UA = "sound-ref-fetch/0.1"
FIELDS = "id,name,username,license,duration,previews,tags,description,avg_rating,num_ratings,num_downloads,url"
MAX_BYTES = 8 * 1024 * 1024

LICENCES = [
    (re.compile(r"^https?://creativecommons\.org/publicdomain/zero/1\.0/?$"), "CC0-1.0"),
    (re.compile(r"^https?://creativecommons\.org/licenses/by/3\.0/?$"), "CC-BY-3.0"),
    (re.compile(r"^https?://creativecommons\.org/licenses/by/4\.0/?$"), "CC-BY-4.0"),
]

BANNED = [
    "scream", "screams", "screaming", "agony", "pain", "painful", "wounded", "wound", "dying", "die",
    "death", "dead", "moan", "moans", "moaning", "groan", "groans", "groaning", "cry", "cries", "crying",
    "gore", "gory", "blood", "injured", "injury", "distress", "distressed", "whinny", "whinnying",
    "traffic", "cars", "highway", "motorway", "pa", "announcer", "announcement", "loudspeaker", "tannoy",
    "crowd", "chatter", "talking", "speech", "voices", "applause", "music", "musical", "song",
    "game", "games", "videogame", "gamedev", "synth", "synthesized", "synthesised", "synthesizer",
    "synthesis", "synthetic", "generated", "designed", "sound-design", "sounddesign", "daw", "vst",
    "plugin", "foley", "processed", "layered", "layers", "remix", "edited-together", "fake", "imitation",
    "cinematic", "trailer", "whoosh", "sfxr", "ai", "simulated", "simulation", "simulate", "simulates",
    "simulating", "artificial", "cartoon", "resynthesized", "coconut", "coconuts", "mixed", "mixing",
    "timestretched", "mangled", "8-bit", "laser", "plugins", "soundbank", "movie", "film",
]
BANNED_PHRASES = ["sound design", "sfx design", "video game", "music bed", "made in", "created in", "created with"]
BANNED_RE = re.compile(
    r"(?<![a-z0-9])(" + "|".join(re.escape(w) for w in BANNED + BANNED_PHRASES) + r")(?![a-z0-9])"
)

# prefix: (max seconds, queries)
SOUNDS = {
    "wind": (30, ["wind", "windy field", "wind gusts", "wind in trees", "strong wind", "wind leaves", "wind grass", "wind moor", "wind open field", "wind trees field recording"]),
    "rumble": (30, ["distant artillery", "artillery distant fire", "distant shot rumble", "distant gunfire", "military exercise distant", "cannonade", "bombardment distant", "howitzer distant", "shooting range distant", "distant thunder rumble", "distant explosions"]),
    "whistle": (20, ["referee whistle", "police whistle", "pea whistle", "whistle blast", "sports whistle", "coach whistle", "metal whistle blow", "trench whistle", "acme whistle", "football whistle"]),
    "cannon": (20, ["cannon", "cannon fire", "cannon blast", "civil war cannon", "cannon reenactment", "black powder cannon", "artillery salute", "cannon salute", "howitzer", "user:richardemoore cannon", "user:nofeedbak cannon", "user:daveincamas cannon"]),
    "shell": (20, ["distant explosion", "artillery explosion", "naval gun", "howitzer firing", "quarry blast", "blasting explosion distant", "artillery shell impact", "mortar explosion", "detonation field recording"]),
    "volley": (20, ["musket volley", "muskets", "reenactment", "re-enactment", "civil war reenactment", "napoleonic", "battle reenactment", "volley fire", "gun salute", "rifle salute", "black powder", "user:richardemoore civil war", "user:richardemoore"]),
    "scatter": (20, ["musket shot", "musket", "flintlock", "black powder rifle", "muzzleloader", "black powder shot", "skirmish"]),
    "mg": (20, ["machine gun burst", "vickers", "maxim machine gun", "mg42", "mg34", "machine gun distant", "browning machine gun", "machine gun range", "bren gun", "lewis gun"]),
    "transport": (30, ["dc-3", "dc3", "c-47", "c47 aircraft", "dakota", "douglas", "radial engine", "b-25", "beech 18", "propeller plane flyover", "propeller airplane flyby", "piston aircraft flyby", "vintage aircraft flyover", "prop plane overhead", "twin engine plane"]),
    "stuka": (30, ["stuka", "dive bomber", "warbird", "spitfire", "mustang p-51", "p51", "corsair", "airshow flyby", "plane dive", "user:Fight2FlyPhoto"]),
    "hooves": (20, ["horses galloping", "horse gallop", "horses gallop", "horses running", "horse race", "racehorses", "polo horses", "cavalry", "horses stampede", "herd of horses", "horses hooves"]),
}

# (prefix, n, freesound id, note)
PICKS = [
    ("wind", 1, 593817, "Wind through tall grass, open country. Phone-grade m4a source, so expect some mic wind noise."),
    ("wind", 2, 482254, "Strong wind in a tree, summer field recording. One bird, per the title."),
    ("wind", 3, 544853, "Strong wind in forest trees. Cut by the uploader to loop; trees, not open field."),
    ("rumble", 1, 184275, "Tank guns on a training range, heard from a distance. Audio lifted from a US government video, so it may be camera-mic quality."),
    ("rumble", 2, 581123, "Real distant rolling thunder, not gunfire. Uploader says crackly, low quality, one frog call; rain is tagged."),
    ("whistle", 1, 815647, "Pea whistle blown at a distance. Short single blast. USB mic, room or outdoors not stated."),
    ("whistle", 2, 324539, "Old army whistle of the WW1 kind. 16 s, so likely several blasts; perspective not stated."),
    ("whistle", 3, 451464, "Police whistle, nearby, with natural echo. Recorded in India; street background not described."),
    ("cannon", 1, 162626, "Single cannon at a US Civil War re-enactment, about a football field away. Lightly edited to isolate."),
    ("cannon", 2, 351963, "Several firings of an 18th-century cannon at Alamance Battleground. Distance not stated."),
    ("cannon", 3, 125348, "Cannon at a Civil War re-enactment. Two-word description; distance and background unknown."),
    ("shell", 1, 82682, "Quarry blast in granite recorded from about 800 m. Real distant explosion with rock fall, not ordnance."),
    ("shell", 2, 184365, "K-55 self-propelled howitzers firing. Audio lifted from a US government video. Gun reports, not shell bursts."),
    ("shell", 3, 108640, "Explosion from far away, muffled. Uploader gives no detail on what exploded or how it was recorded."),
    ("volley", 1, 675623, "Musket volley from a vintage film sound-effects library (35 mm mag transfer). Real firing, but era fidelity and staging unknown."),
    ("volley", 2, 125346, "Battle noise at a Civil War re-enactment. Tagged rebel yell, so expect men's voices over the fire."),
    ("scatter", 1, 538795, "Old musket fired outside with natural mountain reverb. Mics next to the musket, so close perspective."),
    ("scatter", 2, 347647, "Ignition and report of a single musket. Close perspective, setting not stated."),
    ("scatter", 3, 675622, "Musket shots from a vintage film sound-effects library (35 mm mag transfer). Setting unknown."),
    ("mg", 1, 160773, "Russian Maxim, WW2 era, recorded about 40 m from the gun."),
    ("mg", 2, 160772, "Same Maxim at 1 to 10 m. Close perspective; spent cases audible on pavement."),
    ("mg", 3, 675596, "Machine gun bursts with outdoor echo, vintage film sound-effects library. Gun type not named."),
    ("transport", 1, 143557, "Not a C-47. Grumman F7F Tigercat, twin radial, flying by on take-off from an airport."),
    ("transport", 2, 329616, "Not a C-47. B-25 bomber, twin radial, taking off at an air show. Take-off roll, not an overhead pass; show background possible."),
    ("transport", 3, 110737, "Not a C-47. Lockheed Super Constellation low pass, four radials. A little wind noise."),
    ("stuka", 1, 143558, "Not a Stuka and no siren. Bf 109E fast flyby at an aviation event, inverted V12."),
    ("stuka", 2, 143562, "Not a Stuka and no siren. Fw 190 high-speed low pass at an air show, BMW radial."),
    ("stuka", 3, 96210, "Not a Stuka and no siren. Aircraft diving, cleaned from Iwo Jima footage on archive.org. Wartime film audio was often dubbed, so it may not be a live recording."),
    ("hooves", 1, 479738, "Group of horses galloping on hard ground, medium distance. A man urges them on at the start; birds behind."),
    ("hooves", 2, 479736, "Small herd of horses running in from a distance and past the mic. Vintage film library transfer."),
    ("hooves", 3, 194982, "Wild horses running on grass. No recording details given."),
]


def read_key():
    with open(os.path.expanduser("~/.config/freesound/api_key"), encoding="utf-8") as f:
        return f.read().strip()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, "redirect refused: " + newurl, headers, fp)


API_OPENER = urllib.request.build_opener(NoRedirect)


def api_get(path, params, key):
    url = API + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": "Token " + key, "User-Agent": UA})
    try:
        with API_OPENER.open(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read(2000).decode("utf-8", "replace")
        sys.exit("HTTP %s on %s\n%s" % (e.code, path, body))


def licence_short(url):
    for rx, short in LICENCES:
        if rx.match(url or ""):
            return short
    return None


def text_of(s):
    desc = re.sub(r"<[^>]+>", " ", html.unescape(s.get("description") or ""))
    return " ".join([s.get("name") or "", " ".join(s.get("tags") or []), desc])


def banned_hits(s):
    return sorted(set(BANNED_RE.findall(text_of(s).lower())))


def score(s):
    return (s.get("avg_rating") or 0) * math.log10(1 + (s.get("num_downloads") or 0))


def cmd_search():
    key = read_key()
    seen_licences = {}
    first = True
    only = sys.argv[2:]
    try:
        with open(CANDIDATES, encoding="utf-8") as f:
            prev = json.load(f)
    except FileNotFoundError:
        prev = {}
    out = dict(prev)
    for prefix, (max_s, queries) in SOUNDS.items():
        if only and prefix not in only:
            continue
        old_ids = {c["id"] for c in prev.get(prefix, [])}
        found = {}
        stats = {"raw": 0, "licence": 0, "banned": 0}
        for q in queries:
            flt = 'duration:[2 TO %d] license:("Creative Commons 0" OR "Attribution")' % max_s
            m = re.match(r"user:(\S+)\s*(.*)", q)
            if m:
                flt += " username:" + m.group(1)
            data = api_get("/search/text/", {
                "query": m.group(2) if m else q,
                "filter": flt,
                "fields": FIELDS,
                "page_size": 40,
                "sort": "score",
            }, key)
            if first:
                print("first call ok: count=%s keys=%s" % (data.get("count"), sorted(data.keys())))
                if data.get("results"):
                    print("first result keys:", sorted(data["results"][0].keys()))
                first = False
            for s in data.get("results", []):
                stats["raw"] += 1
                seen_licences[s.get("license")] = seen_licences.get(s.get("license"), 0) + 1
                short = licence_short(s.get("license"))
                if not short:
                    stats["licence"] += 1
                    continue
                hits = banned_hits(s)
                if hits:
                    stats["banned"] += 1
                    continue
                s["licence_short"] = short
                s.setdefault("queries", [])
                if s["id"] in found:
                    found[s["id"]]["queries"].append(q)
                else:
                    s["queries"].append(q)
                    found[s["id"]] = s
            time.sleep(1.1)
        for c in found.values():
            c["new"] = c["id"] not in old_ids
        out[prefix] = sorted(found.values(), key=score, reverse=True)
        print("%-10s raw=%d rejected_licence=%d rejected_banned=%d kept=%d" % (
            prefix, stats["raw"], stats["licence"], stats["banned"], len(found)))
    with open(CANDIDATES, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print("licence strings returned:", json.dumps(seen_licences, indent=1))


def cmd_show(prefix, limit=14, offset=0, pattern=None):
    with open(CANDIDATES, encoding="utf-8") as f:
        cands = json.load(f)[prefix]
    new = [c for c in cands if c.get("new")]
    if pattern:
        new = [c for c in new if re.search(pattern, text_of(c), re.I)]
    print("%s: %d candidates, %d new shown from %d" % (prefix, len(cands), len(new), offset))
    for s in new[offset:offset + limit]:
        desc = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(s.get("description") or "")))
        print("- %d | %s | %.1fs | r%.1f n%d d%d | %s | by %s\n  tags: %s\n  %s" % (
            s["id"], s["licence_short"], s["duration"], s.get("avg_rating") or 0, s.get("num_ratings") or 0,
            s.get("num_downloads") or 0, s["name"], s["username"], ",".join((s.get("tags") or [])[:14]),
            desc[:200]))


def is_mp3(head):
    return head[:3] == b"ID3" or (len(head) > 1 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0)


def download(url, dest):
    p = urllib.parse.urlparse(url)
    if p.scheme != "https" or not (p.hostname or "").endswith("freesound.org"):
        sys.exit("refusing preview URL host: %s" % p.hostname)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        sys.exit("preview too large: %s" % url)
    if not data or not is_mp3(data[:4]):
        sys.exit("not an MP3: %s" % url)
    with open(dest, "wb") as f:
        f.write(data)
    return len(data)


def cmd_fetch():
    key = read_key()
    os.makedirs(REFS, exist_ok=True)
    entries = []
    for prefix, n, sid, note in PICKS:
        s = api_get("/sounds/%d/" % sid, {"fields": FIELDS}, key)
        short = licence_short(s.get("license"))
        if not short:
            sys.exit("licence not allowed for %d: %s" % (sid, s.get("license")))
        hits = banned_hits(s)
        if hits:
            sys.exit("banned words in %d: %s" % (sid, hits))
        name = "%s-%d-%d.mp3" % (prefix, n, sid)
        size = download(s["previews"]["preview-hq-mp3"], os.path.join(REFS, name))
        entries.append({
            "prefix": prefix, "file": name, "freesound_id": sid,
            "url": "https://freesound.org/s/%d/" % sid, "name": s["name"], "username": s["username"],
            "licence": short, "licence_url": s["license"], "duration_s": round(s["duration"], 2),
            "bytes": size, "note": note,
        })
        print("ok", name, size)
        time.sleep(1.1)
    with open(os.path.join(REFS, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
        f.write("\n")
    lines = [
        "# Reference recordings for the synth blind test",
        "",
        "Throwaway A/B material from freesound.org. These are HQ MP3 previews, not originals.",
        "Chosen from titles, tags and descriptions only. Nobody has listened to them yet.",
        "",
        "| File | Sound | Licence | Seconds | Bytes | Name | Author | Page | Note |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for e in entries:
        lines.append("| %s | %s | [%s](%s) | %.1f | %d | %s | %s | %s | %s |" % (
            e["file"], e["prefix"], e["licence"], e["licence_url"], e["duration_s"], e["bytes"],
            e["name"].replace("|", "/"), e["username"], e["url"], e["note"].replace("|", "/")))
    missing = [p for p in SOUNDS if not any(e["prefix"] == p for e in entries)]
    lines += ["", "No acceptable match: %s." % (", ".join(missing) if missing else "none")]
    with open(os.path.join(REFS, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    cmd_verify()


def cmd_verify():
    with open(os.path.join(REFS, "manifest.json"), encoding="utf-8") as f:
        entries = json.load(f)
    bad = 0
    for e in entries:
        path = os.path.join(REFS, e["file"])
        with open(path, "rb") as f:
            head = f.read(4)
        size = os.path.getsize(path)
        ok = size > 0 and size == e["bytes"] and is_mp3(head) and e["licence"] in ("CC0-1.0", "CC-BY-3.0", "CC-BY-4.0") \
            and licence_short(e["licence_url"]) == e["licence"]
        bad += not ok
        if not ok:
            print("FAIL", e["file"])
    counts = {}
    for e in entries:
        counts[e["prefix"]] = counts.get(e["prefix"], 0) + 1
    print("verify: %d files, %d failures, counts=%s" % (len(entries), bad, json.dumps(counts)))
    if bad:
        sys.exit(1)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "fetch"
    if cmd == "search":
        cmd_search()
    elif cmd == "show":
        cmd_show(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 14, int(sys.argv[4]) if len(sys.argv) > 4 else 0,
                 sys.argv[5] if len(sys.argv) > 5 else None)
    elif cmd == "fetch":
        cmd_fetch()
    elif cmd == "verify":
        cmd_verify()
    else:
        sys.exit(__doc__)
