#!/usr/bin/env python3
"""Export Dave's audition picks into Field Glass's sound library.

Reads a pools file (a dated pools-*.txt, or the page's summary text pasted on stdin with "-"),
the refs*/manifest.json files, and the CUES, WWROWS, RENAMED and DROPPED tables in index.html.
Writes sounds/<era>/<cue>-<n>.m4a and sounds/<era>/manifest.json in the shape of
docs/specs/battle-sound.md, then prints a battle.json "sound.kit" block for each World War battle.

    python3 -I export_pools.py pools-2026-11-13.txt            # writes ../../sounds
    python3 -I export_pools.py pools-2026-11-13.txt --dry-run  # report only, writes nothing
    python3 -I export_pools.py - < summary.txt                 # the page's summary text

Each take is prepared as the spec says: silence trimmed off both ends, cut to the length limit,
mono, levelled to -18 LUFS, 50 ms fades, AAC 96 kbit/s at 48 kHz. Needs ffmpeg and ffprobe.
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
REF_DIRS = ['refs', 'refs2', 'refs3']

TARGET_LUFS = -18.0
PEAK_CEILING = -1.0       # dBTP after gain; the gain is lowered rather than limiting the take
SILENCE_DB = -50          # trim threshold for the ends
FADE = 0.05
LONG_CUES = {'air', 'transport'}   # spec: these may run to 30 s, the rest to 10 s

# The first pass (refs/) has no era or kit. Dave accepted this mapping on 2026-11-14.
# Each value: list of (era, kit) for the recordings, list of eras for the synth.
BP = ['flintlock', 'percussion']
WW = ['great-war', 'ww2']
REFS_ERAS = {
    'wind':      {'files': [('common', None)], 'synth': ['common']},
    'rumble':    {'files': [('great-war', None), ('ww2', None)], 'synth': BP},
    'whistle':   {'files': [('great-war', None)], 'synth': []},
    'cannon':    {'files': [(e, None) for e in BP], 'synth': BP},
    'shell':     {'files': [('great-war', None), ('ww2', None)], 'synth': BP},
    'volley':    {'files': [(e, None) for e in BP], 'synth': BP},
    'scatter':   {'files': [(e, None) for e in BP], 'synth': BP},
    'mg':        {'files': [], 'synth': []},
    'transport': {'files': [('ww2', None)], 'synth': []},
    'stuka':     {'files': [('ww2', 'de')], 'synth': []},
    'hooves':    {'files': [('common', None)], 'synth': ['common']},
}
# refs/ clips that land in a World War era need equipment, a kit override, and the stand-in flag.
REFS_WW = {
    'rumble-1-184275.mp3': ('Tank guns on a range, distant', None, True),
    'rumble-2-581123.mp3': ('Distant thunder, for far guns', None, True),
    'whistle-2a-324539.mp3': ('Army whistle, old', None, False),
    'whistle-2b-324539.mp3': ('Army whistle, old', None, False),
    'shell-1-82682.mp3': ('Quarry blast at 800 m, for a shell burst', None, True),
    'shell-3-108640.mp3': ('Distant explosion, source not named', None, True),
    'transport-1-143557.mp3': ('Grumman F7F Tigercat, for the C-47', None, True),
    'transport-3-110737.mp3': ('Lockheed Super Constellation, for a four-engine tug', None, True),
    'stuka-1-143558.mp3': ('Messerschmitt Bf 109E, for the Ju 87', 'de', True),
    'stuka-2-143562.mp3': ('Focke-Wulf Fw 190, for the Ju 87', 'de', True),
    'stuka-3-96210.mp3': ('US aircraft diving, Iwo Jima film', 'us', True),
}
# Side names in battle.json that map to one kit without a judgment call.
SIDE_KITS = {'american': 'us', 'us': 'us', 'british': 'uk', 'german': 'de', 'french': 'fr'}
WAR_ERA = {'World War I': 'great-war', 'World War II': 'ww2'}


def die(msg):
    sys.exit('export_pools: ' + msg)


def read_page():
    """Pull the pool tables out of index.html so this script never drifts from the page."""
    html = open(os.path.join(HERE, 'index.html'), encoding='utf-8').read()
    cues = dict(re.findall(r"\{ id: '([\w-]+)', cue: '([\w-]+)'", html))
    m = re.search(r'const WWROWS = \[(.*?)\]\.map', html, re.S)
    rows = re.findall(r"\['(\w+)', '(\w+)', '[^']*', '([^']*)'\]", m.group(1)) if m else []
    wwrows = {}
    for rid, cue, where in rows:
        eras_part, _, kits_part = where.partition(' · ')
        eras = WW if eras_part == 'both wars' else [eras_part]
        kits = [k.strip() for k in kits_part.split(',')] if kits_part else [None]
        wwrows[rid] = (cue, eras, kits)
    m = re.search(r'const DROPPED = new Set\((\[.*?\])\)', html)
    dropped = set(json.loads(m.group(1))) if m else set()
    m = re.search(r'const RENAMED = (\{.*?\});', html)
    renamed = json.loads(m.group(1)) if m else {}
    if not cues or not wwrows:
        die('could not read CUES or WWROWS from index.html')
    return cues, wwrows, dropped, renamed


def read_refs():
    clips = {}
    for d in REF_DIRS:
        path = os.path.join(HERE, d, 'manifest.json')
        if not os.path.exists(path):
            continue
        for e in json.load(open(path, encoding='utf-8')):
            clips[e['file']] = dict(e, dir=d)
    return clips


def read_pools(path):
    text = sys.stdin.read() if path == '-' else open(path, encoding='utf-8').read()
    pools = {}
    for line in text.splitlines():
        m = re.match(r'^(\w+)\s+(.+?)(\s+\(blind .*\))?\s*$', line)
        if not m or line.startswith('Notes'):
            continue
        members = [] if m.group(2) == 'undecided' else [x.strip() for x in m.group(2).split('+')]
        pools[m.group(1)] = members
    if not pools:
        die('no pool lines in ' + path)
    return pools


def licence(raw):
    s = raw.strip().replace('CC-BY', 'CC BY').replace('CC0-1.0', 'CC0 1.0')
    if s == 'Public domain':
        return 'PD'
    m = re.fullmatch(r'CC0 1\.0', s)
    if m:
        return 'CC0-1.0'
    m = re.fullmatch(r'CC BY(-SA)?[ -](\d\.\d)', s)
    if m:
        return 'CC-BY%s-%s' % (m.group(1) or '', m.group(2))
    die('licence %r is not on the allowed list' % raw)


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        die('%s failed:\n%s' % (cmd[0], p.stderr[-2000:]))
    return p


def duration(path):
    out = run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path]).stdout
    return float(out.strip())


def find_trim(src, cue):
    """Return (start, end) in the source: silence cut off both ends, then the length limit."""
    total = duration(src)
    err = run(['ffmpeg', '-hide_banner', '-nostats', '-i', src, '-af',
               'silencedetect=noise=%ddB:d=0.25' % SILENCE_DB, '-f', 'null', '-']).stderr
    starts = [float(x) for x in re.findall(r'silence_start: (-?[\d.]+)', err)]
    ends = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', err)]
    a, b = 0.0, total
    if starts and starts[0] <= 0.01 and ends:
        a = max(0.0, ends[0] - FADE)
    if len(starts) > len(ends) or (starts and ends and starts[-1] > ends[-1]):
        b = min(total, starts[-1] + FADE)
    limit = 30.0 if cue in LONG_CUES else 10.0
    cut = b - a > limit
    if cut:
        b = a + limit
    return round(a, 2), round(b, 2), cut


def measure(src, a, b):
    err = run(['ffmpeg', '-hide_banner', '-nostats', '-ss', str(a), '-to', str(b), '-i', src,
               '-ac', '1', '-af', 'loudnorm=I=%g:TP=%g:print_format=json' % (TARGET_LUFS, PEAK_CEILING),
               '-f', 'null', '-']).stderr
    stats = json.loads(err[err.rindex('{'):err.rindex('}') + 1])
    return float(stats['input_i']), float(stats['input_tp'])


def prepare(src, dst, cue):
    a, b, cut = find_trim(src, cue)
    lufs, tp = measure(src, a, b)
    gain = TARGET_LUFS - lufs
    capped = tp + gain > PEAK_CEILING
    if capped:
        gain = PEAK_CEILING - tp
    gain = round(gain, 1)
    seconds = round(b - a, 2)
    af = 'volume=%.1fdB,afade=t=in:d=%g,afade=t=out:st=%g:d=%g' % (gain, FADE, max(0, seconds - FADE), FADE)
    run(['ffmpeg', '-hide_banner', '-v', 'error', '-y', '-ss', str(a), '-to', str(b), '-i', src,
         '-ac', '1', '-ar', '48000', '-af', af, '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', dst])
    notes = []
    if cut:
        notes.append('cut to %g s' % seconds)
    if capped:
        notes.append('peak-capped: %.1f LUFS, not %g' % (lufs + gain, TARGET_LUFS))
    return {'seconds': seconds, 'trim': [a, b], 'gainDb': gain}, notes


def plan(pools, cues, wwrows, dropped, renamed, clips):
    """Turn pools into per-era lists of takes. Returns (takes, synths, skipped)."""
    takes, synths, skipped = [], [], []
    for pid, members in pools.items():
        if not members:
            skipped.append(pid)
            continue
        if pid in cues:
            cue, eras = cues[pid], REFS_ERAS.get(pid)
            if eras is None:
                die('pool %s has no era mapping in REFS_ERAS' % pid)
        elif pid in wwrows:
            cue = wwrows[pid][0]
        else:
            die('pool %s is neither a CUES id nor a WWROWS id in index.html' % pid)
        for m in members:
            if m == 'synth':
                for era in (REFS_ERAS[pid]['synth'] if pid in cues else []):
                    if era in WW and pid != 'wind':
                        die('synth %s may not go in %s' % (pid, era))
                    synths.append({'era': era, 'cue': cue, 'synth': pid})
                if pid in cues and not REFS_ERAS[pid]['synth']:
                    die('pool %s ticks synth but has no synth era' % pid)
                continue
            f = m + '.mp3'
            f = renamed.get(f, f)
            if f in dropped:
                skipped.append('%s: %s (dropped)' % (pid, f))
                continue
            clip = clips.get(f)
            if not clip:
                die('pool %s names %s, which no refs*/manifest.json lists' % (pid, f))
            src = os.path.join(HERE, clip['dir'], f)
            if not os.path.exists(src):
                die('%s is in %s/manifest.json but not on disk' % (f, clip['dir']))
            base = {
                'cue': cue,
                'source': clip.get('url') or clip.get('page'),
                'title': clip.get('name') or clip.get('title'),
                'author': clip.get('username') or clip.get('author'),
                'licence': licence(clip['licence']),
                'battles': None,
            }
            if base['author'] in (None, 'None'):
                base['author'] = 'USC sound library (archive.org)'
            if pid in cues:
                for era, kit in REFS_ERAS[pid]['files']:
                    t = dict(base, era=era, src=src, pool=pid, file0=f)
                    if era in WW:
                        equip, kit_over, stand = REFS_WW.get(f) or die('%s needs a REFS_WW entry for %s' % (f, era))
                        k = kit_over or kit
                        if k:
                            t['kit'] = k
                        t['equipment'] = equip
                        if stand:
                            t['standIn'] = True
                    takes.append(t)
            else:
                _, eras, kits = wwrows[pid]
                for era in eras:
                    for kit in kits:
                        t = dict(base, era=era, src=src, pool=pid, file0=f, equipment=clip['equipment'])
                        if kit:
                            t['kit'] = kit
                        if not clip.get('exact'):
                            t['standIn'] = True
                        takes.append(t)
    return takes, synths, skipped


def kit_blocks():
    """battle.json sound.kit for each World War battle, from side names that need no judgment."""
    out = []
    for e in json.load(open(os.path.join(REPO, 'battles', 'index.json'), encoding='utf-8')):
        era = WAR_ERA.get(e.get('war'))
        if not era:
            continue
        b = json.load(open(os.path.join(REPO, 'battles', e['id'], 'battle.json'), encoding='utf-8'))
        kit = {s: SIDE_KITS[s] for s in b['sides'] if s in SIDE_KITS}
        unmapped = [s for s in b['sides'] if s not in SIDE_KITS]
        out.append((e['id'], era, kit, unmapped))
    return out


ORDER = ['id', 'file', 'cue', 'synth', 'kit', 'equipment', 'standIn', 'seconds', 'source', 'title',
         'author', 'licence', 'trim', 'gainDb', 'battles']


def ordered(entry):
    return {k: entry[k] for k in ORDER if k in entry}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('pools', help="a pools-*.txt file, or - to read the page's summary on stdin")
    ap.add_argument('--out', default=os.path.join(REPO, 'sounds'), help='library root (default: <repo>/sounds)')
    ap.add_argument('--dry-run', action='store_true', help='report the plan, write nothing')
    args = ap.parse_args()

    cues, wwrows, dropped, renamed = read_page()
    takes, synths, skipped = plan(read_pools(args.pools), cues, wwrows, dropped, renamed, read_refs())

    eras = sorted({t['era'] for t in takes} | {s['era'] for s in synths})
    if not args.dry_run:
        for era in eras:
            if os.path.exists(os.path.join(args.out, era, 'manifest.json')):
                die('%s/%s/manifest.json exists. This script builds a library from scratch; move the '
                    'old folder aside first.' % (args.out, era))

    for era in eras:
        mine = sorted((t for t in takes if t['era'] == era), key=lambda t: (t['cue'], t.get('kit') or ''))
        count, entries = {}, []
        print('\n== %s ==' % era)
        for t in mine:
            count[t['cue']] = count.get(t['cue'], 0) + 1
            name = '%s-%d.m4a' % (t['cue'], count[t['cue']])
            entry = {k: v for k, v in t.items() if k not in ('era', 'src', 'pool', 'file0')}
            entry['file'] = name
            notes = []
            if not args.dry_run:
                os.makedirs(os.path.join(args.out, era), exist_ok=True)
                dst = os.path.join(args.out, era, name)
                prep, notes = prepare(t['src'], dst, t['cue'])
                entry.update(prep)
                entry['_bytes'] = os.path.getsize(dst)
            entries.append(entry)
            print('  %-14s %-4s %-24s %s%s' % (
                name, entry.get('kit', ''), t['file0'],
                '' if args.dry_run else '%5.2f s %+5.1f dB %3d KB' % (entry['seconds'], entry['gainDb'], entry['_bytes'] // 1024),
                ('  [' + '; '.join(notes) + ']') if notes else ''))
        for s in synths:
            if s['era'] == era:
                entries.append({'cue': s['cue'], 'synth': s['synth']})
                print('  %-14s      synth %s' % (s['cue'], s['synth']))
        entries.sort(key=lambda e: (e['cue'], 'synth' in e, e.get('file', '')))
        if not args.dry_run:
            with open(os.path.join(args.out, era, 'manifest.json'), 'w', encoding='utf-8') as fh:
                json.dump([ordered(e) for e in entries], fh, indent=1, ensure_ascii=False)
                fh.write('\n')

    print('\n== skipped ==')
    for s in skipped:
        print('  ' + s + ('' if ':' in s else ': undecided'))

    print('\n== kit coverage (volley, mg, gun) ==')
    for era in WW:
        kits = sorted({t['kit'] for t in takes if t['era'] == era and t.get('kit')})
        for k in kits:
            have = {t['cue'] for t in takes if t['era'] == era and t.get('kit') == k}
            missing = [c for c in ('volley', 'mg', 'gun') if c not in have]
            print('  %-9s %-3s %s' % (era, k, 'complete' if not missing else 'missing ' + ', '.join(missing)))

    print('\n== battle.json "sound" for World War battles ==')
    for bid, era, kit, unmapped in kit_blocks():
        print('  %-13s %s' % (bid, json.dumps({'sound': {'kit': kit}})) +
              ('   needs Dave: ' + ', '.join(unmapped) if unmapped else ''))


if __name__ == '__main__':
    main()
