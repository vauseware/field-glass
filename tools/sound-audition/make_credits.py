#!/usr/bin/env python3
"""Write a CREDITS file for every recorded clip a pools file uses.

Usage: python3 -I make_credits.py pools-2026-11-13.txt [-o CREDITS-2026-11-13.md]

Reads refs*/manifest.json next to this script. Each pool line is `<cue> <clip> + <clip> ...`,
where a clip is a manifest file name without `.mp3`; `synth` and `undecided` are skipped.
Exits non-zero if a clip is in no manifest, or a licence is not CC0, public domain, CC BY or
CC BY-SA.
"""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
USC = "USC Cinema / Sunset Editorial sound-effects library"
SKIP = {"+", "synth", "undecided"}

# Licence name as written in the manifests -> (short name, deed URL, kind).
LICENCES = {
    "CC0-1.0": ("CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/", "cc0"),
    "CC0 1.0": ("CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/", "cc0"),
    "Public domain": ("Public domain", None, "pd"),
    "CC-BY-3.0": ("CC BY 3.0", "https://creativecommons.org/licenses/by/3.0/", "by"),
    "CC BY 3.0": ("CC BY 3.0", "https://creativecommons.org/licenses/by/3.0/", "by"),
    "CC-BY-4.0": ("CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/", "by"),
    "CC BY 4.0": ("CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/", "by"),
    "CC BY-SA 3.0": ("CC BY-SA 3.0", "https://creativecommons.org/licenses/by-sa/3.0/", "by-sa"),
    "CC BY-SA 4.0": ("CC BY-SA 4.0", "https://creativecommons.org/licenses/by-sa/4.0/", "by-sa"),
}


def load_clips():
    """Map clip stem -> normalised credit record, across every refs*/manifest.json."""
    clips = {}
    for manifest in sorted(HERE.glob("refs*/manifest.json")):
        folder = manifest.parent.name
        for e in json.loads(manifest.read_text()):
            if folder == "refs":
                title, author, source = e["name"], e["username"], e["url"]
            else:
                title, author, source = e["title"], e["author"], e["page"]
                title = title.removeprefix("File:")  # Wikimedia Commons page titles
            if author in (None, "", "None") or author.startswith("USC sound library"):
                author = USC
            if e["licence"] not in LICENCES:
                sys.exit(f"{folder}/{e['file']}: licence {e['licence']!r} is not allowed")
            name, url, kind = LICENCES[e["licence"]]
            if folder == "refs" and e.get("licence_url"):
                url = e["licence_url"].replace("http://", "https://")
            changes = [s.strip() for s in re.split(r"(?<=\.)\s+", e.get("note", ""))
                       if s.startswith(("Trimmed by Claude", "Cut by Claude"))]
            if folder != "refs":
                changes.append("Converted to MP3.")
            clips[e["file"][:-4]] = dict(file=f"{folder}/{e['file']}", title=title, author=author,
                                         source=source, licence=name, licence_url=url, kind=kind,
                                         changes=" ".join(changes))
    return clips


def read_pools(path):
    """Yield (cue, [clip stems]) from a pools-*.txt file."""
    for line in Path(path).read_text().splitlines():
        parts = line.split("(")[0].split()
        if len(parts) < 2 or parts[0].endswith(":"):
            continue
        yield parts[0], [p for p in parts[1:] if p not in SKIP]


def entry(c, cues):
    lic = f"[{c['licence']}]({c['licence_url']})" if c["licence_url"] else c["licence"]
    if c["kind"] == "pd":
        lic += f" (see [source page]({c['source']}))"
    lines = [
        f"### {c['file']}",
        "",
        f"- Title: {c['title']}",
        f"- Author: {c['author']}",
        f"- Licence: {lic}",
        f"- Source: {c['source']}",
        f"- Used in: {', '.join(cues)}",
    ]
    if c["changes"]:
        lines.append(f"- Changes: {c['changes']}")
    if c["kind"] in ("by", "by-sa"):
        mod = " Modified from the original." if c["changes"] else ""
        attr = (f'"{c["title"]}" by {c["author"]} ({c["source"]}), licensed under '
                f'{c["licence"]} ({c["licence_url"]}).{mod}')
        if c["kind"] == "by-sa":
            attr += f" This clip, as changed, is shared under {c['licence']}."
        lines.append(f"- Attribution: {attr}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pools", help="a pools-*.txt file")
    ap.add_argument("-o", "--out", help="output file (default CREDITS-<date>.md next to the pools file)")
    args = ap.parse_args()

    clips = load_clips()
    used = {}  # stem -> cues, in pool order
    missing = []
    for cue, stems in read_pools(args.pools):
        for s in stems:
            if s not in clips:
                missing.append(f"{cue}: {s}")
            used.setdefault(s, []).append(cue)
    if missing:
        sys.exit("Not in any manifest:\n  " + "\n  ".join(missing))

    pools = Path(args.pools)
    date = re.search(r"\d{4}-\d{2}-\d{2}", pools.name)
    out = Path(args.out) if args.out else pools.with_name(f"CREDITS-{date.group(0) if date else 'pools'}.md")

    sections = {"by-sa": [], "by": [], "pd": [], "cc0": []}
    for s, cues in used.items():
        sections[clips[s]["kind"]].append(entry(clips[s], cues))
    heads = {
        "by-sa": "CC BY-SA: credit required, share alike",
        "by": "CC BY: credit required",
        "pd": "Public domain",
        "cc0": "CC0: no credit required, given anyway",
    }
    body = [
        "# Battle sound credits",
        "",
        f"Generated by `make_credits.py` from `{pools.name}`. Do not edit by hand; re-run the script.",
        "",
        f"{len(used)} recorded clips. Ship this file with the sounds wherever Field Glass uses them.",
        "CC BY and CC BY-SA clips must keep the attribution line shown. A CC BY-SA clip, and any",
        "sound made from it, stays under CC BY-SA.",
    ]
    for kind, items in sections.items():
        if items:
            body += ["", f"## {heads[kind]} ({len(items)})", ""]
            body.append("\n\n".join(items))
    out.write_text("\n".join(body) + "\n")
    print(f"Wrote {out.name}: {len(used)} clips "
          + ", ".join(f"{len(v)} {k}" for k, v in sections.items() if v))


if __name__ == "__main__":
    main()
