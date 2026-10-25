"""Moves a battle's research note between a local file and its GitHub issue.

  python3 .claude/skills/battle-pipeline/note.py post <issue> <note.md>   post the note as comments on the issue
  python3 .claude/skills/battle-pipeline/note.py pull <issue> <note.md>   write the newest posted note to the file

A note goes up in parts, each under GitHub's 65,536-character comment limit, every part headed
`<!-- research-note <digest> <i>/<n> -->`. Posting again adds a new set; pull reads the newest complete set, so a
rerun never needs to delete anything.
"""
import hashlib, json, re, subprocess, sys

LIMIT = 60000
MARK = re.compile(r"^<!-- research-note ([0-9a-f]{8}) (\d+)/(\d+) -->\n")


def gh(*args, stdin=None):
    return subprocess.run(["gh", *args], input=stdin, capture_output=True, text=True, check=True).stdout


def parts(text):
    out, cur = [], ""
    for line in text.splitlines(keepends=True):
        if len(cur) + len(line) > LIMIT and cur:
            out.append(cur); cur = ""
        cur += line
    return out + [cur] if cur else out


def post(issue, path):
    text = open(path, encoding="utf-8").read()
    digest, chunks = hashlib.sha256(text.encode()).hexdigest()[:8], parts(text)
    for i, chunk in enumerate(chunks, 1):
        gh("issue", "comment", issue, "--body-file", "-", stdin=f"<!-- research-note {digest} {i}/{len(chunks)} -->\n{chunk}")
    print(f"posted {len(chunks)} part(s) of note {digest} to #{issue}")


def pull(issue, path):
    comments = json.loads(gh("issue", "view", issue, "--json", "comments"))["comments"]
    sets = {}
    for c in comments:
        m = MARK.match(c["body"])
        if m: sets.setdefault(m[1], {"n": int(m[3]), "at": c["createdAt"], "parts": {}})["parts"][int(m[2])] = c["body"][m.end():]
    done = [s for s in sets.values() if len(s["parts"]) == s["n"]]
    if not done: sys.exit(f"#{issue} has no complete research note")
    newest = max(done, key=lambda s: s["at"])
    open(path, "w", encoding="utf-8").write("".join(newest["parts"][i] for i in range(1, newest["n"] + 1)))
    print(f"wrote {path} from #{issue} ({newest['n']} part(s))")


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] not in ("post", "pull"): sys.exit(__doc__)
    (post if sys.argv[1] == "post" else pull)(sys.argv[2], sys.argv[3])
