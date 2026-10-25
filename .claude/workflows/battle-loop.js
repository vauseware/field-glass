// Cursor: prefer /poteto-mode with .claude/skills/battle-pipeline/SKILL.md (Orchestrate or Feature per issue).
// This workflow is the Claude Code fleet path and is expensive; keep it off Cursor.
export const meta = {
  name: 'battle-loop',
  description: 'Claude Code fleet: research and build Field Glass battles from GitHub issues (Fable research/review, Opus build/fix). Prefer poteto-mode on Cursor.',
  whenToUse: 'Claude Code only. Run the next loop from the pinned Battle queue issue. args: { issues: [<issue numbers>] }, one battle per war per loop. On Cursor use /poteto-mode + battle-pipeline instead.',
  phases: [
    { title: 'Research', detail: 'one Fable agent per issue posts the note and verdict', model: 'fable' },
    { title: 'Build', detail: 'one Opus agent per fitting battle opens a PR', model: 'opus' },
    { title: 'Review', detail: 'a Fable agent checks the PR against the note', model: 'fable' },
    { title: 'Fix', detail: 'an Opus agent fixes wrong and unsupported findings', model: 'opus' },
  ],
}

const SKILL = '.claude/skills/battle-pipeline/SKILL.md'
const POTETO = '/Users/claw/.claude/plugins/cache/cursor-plugins/pstack/0.15.25/skills/poteto-mode/SKILL.md'
const AGENT = 'pstack:poteto-agent'
const issues = args?.issues ?? []
if (!issues.length) throw new Error('battle-loop needs args.issues, the issue numbers to run')

const VERDICT = {
  type: 'object',
  properties: {
    id: { type: 'string' },
    verdict: { type: 'string', enum: ['fits', 'fits with engine work', 'does not fit'] },
    summary: { type: 'string' },
  },
  required: ['id', 'verdict', 'summary'],
}
const BUILT = {
  type: 'object',
  properties: {
    pr: { type: 'string', description: 'the PR URL, or empty if none was opened' },
    branch: { type: 'string' },
    shots: { type: 'array', items: { type: 'string' } },
    gaps: { type: 'array', items: { type: 'string' } },
  },
  required: ['pr', 'branch', 'shots', 'gaps'],
}
const FINDINGS = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: { where: { type: 'string' }, claim: { type: 'string' }, note: { type: 'string' }, severity: { type: 'string', enum: ['wrong', 'unsupported', 'nit'] } },
        required: ['where', 'claim', 'note', 'severity'],
      },
    },
  },
  required: ['findings'],
}

const brief = role => `Read ${POTETO} and the "${role}" section of ${SKILL} in full, and follow them. Work from the repo root.`

const results = await pipeline(
  issues,
  n => agent(`${brief('Research')} Your issue is #${n}. Return the battle id, the verdict you posted, and a two-sentence summary.`,
    { label: `research #${n}`, phase: 'Research', model: 'fable', agentType: AGENT, schema: VERDICT }),
  (r, n) => {
    if (r.verdict !== 'fits') { log(`#${n} ${r.id}: ${r.verdict}, left for Dave`); return { n, ...r } }
    return agent(`${brief('Build')} Your issue is #${n}, battle id \`${r.id}\`. Return the PR URL, the branch, the absolute paths of the shots to show Dave, and the open gaps.`,
      { label: `build ${r.id}`, phase: 'Build', model: 'opus', agentType: AGENT, isolation: 'worktree', schema: BUILT })
      .then(b => ({ n, ...r, ...b }))
  },
  b => {
    if (!b.pr) return b
    return agent(`${brief('Review')} The PR is ${b.pr}, for issue #${b.n}, battle id \`${b.id}\`. Return your findings.`,
      { label: `review ${b.id}`, phase: 'Review', model: 'fable', agentType: AGENT, schema: FINDINGS })
      .then(v => ({ ...b, findings: v.findings }))
  },
  b => {
    const real = (b.findings ?? []).filter(f => f.severity !== 'nit')
    if (!real.length) return b
    return agent(`${brief('Fix')} The PR is ${b.pr} on branch \`${b.branch}\`, issue #${b.n}. Check out that branch first. The findings:\n${JSON.stringify(real, null, 1)}\nReturn the PR URL, the branch, the shots you retook, and the gaps still open.`,
      { label: `fix ${b.id}`, phase: 'Fix', model: 'opus', agentType: AGENT, isolation: 'worktree', schema: BUILT })
      .then(f => ({ ...b, fixed: f }))
  },
)

return results.map((r, i) => r ?? { n: issues[i], failed: true })
