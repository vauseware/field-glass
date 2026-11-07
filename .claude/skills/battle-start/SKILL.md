---
name: battle-start
description: Start a Field Glass battle loop on Cursor via /poteto-mode and battle-pipeline. Pick the next queued issue, paste the right template, never run Claude battle-loop.js. Use for "start a battle", "next battle", "battle loop", or picking from the Battle queue.
---

# Battle start (Cursor)

Launcher only. The contract is `.claude/skills/battle-pipeline/SKILL.md`. Verify with `.claude/skills/verify-field-glass/SKILL.md`.

**Never** run `.claude/workflows/battle-loop.js` from Cursor. That is the Claude Code fleet path and burns tokens.

## Pick an issue

From the repo root:

```bash
# Ready for an agent (preferred)
gh issue list --label ready-for-agent --label research --limit 20

# One war only (pipeline: one battle per war per loop)
gh issue list --label research --label ww2 --limit 20
# wars: revolutionary-war | war-of-1812 | civil-war | ww1 | ww2

# Already researched, waiting to build
gh issue list --label researched --limit 20

# Order of work
gh issue view 53   # pinned Battle queue
```

Prefer `ready-for-agent` + `research`. If several match, take the next unchecked item on #53 for a war that has no open `building` PR.

## Templates

Start a new Cursor chat. Attach or `@` this skill and `battle-pipeline`. Then paste **one** block (replace `N`).

### A. One issue, research then build (default)

```
/poteto-mode
Follow .claude/skills/battle-pipeline. Issue #N.
Research, then Build only if the verdict is fits.
Verify with verify-field-glass (fg.sh only). Open a draft PR.
Do not run battle-loop.js. Do not start other wars in this chat.
```

### B. Research only (stop at verdict)

```
/poteto-mode
Follow .claude/skills/battle-pipeline Research for issue #N.
Post the note and verdict. Stop. Do not build.
```

### C. Build only (note already on the issue)

```
/poteto-mode
Follow .claude/skills/battle-pipeline Build for issue #N (label researched).
Pull the note with note.py. Verify with verify-field-glass. Draft PR, Closes #N.
```

### D. Review then fix an open PR

```
/poteto-mode
Follow .claude/skills/battle-pipeline Review for PR <url> / issue #N.
Then Bug-fix only wrong and unsupported findings. Same branch. Re-shoot what changed.
```

### E. Next from the queue (still one battle)

```
/poteto-mode
Autopilot-stack, one battle only.
Read Battle queue #53. Take the next ready-for-agent research issue for war <war>.
Run battle-pipeline Research→Build if fits. Draft PR. Stop after that one.
```

Do not use Orchestrate until A feels cheap and reliable.

## After paste

1. Confirm the issue number and war label before spending a long research turn.
2. Keep fences from battle-pipeline (no engine edits; `question` if blocked).
3. Show Dave the `fg.sh` PNGs in chat when Build finishes.
