# Cross-Model Review Contract (Codex Track, ADD mode)

Shared context for skills whose **codex variants** extend the upstream,
Claude-only review path by adding a Codex reviewer as an **extra participant**
— not as a replacement. Skills that reference this document today:

- `writing-review` (Track B only) — adds a 3rd peer reviewer (Codex) on top of
  Claude主 + Claude subagent.
- `idea-verify` (Track B only) — adds a 4th evidence source (Codex) on top of
  DBLP + arXiv + Claude subagent.

This document is installed **only on the codex track** by
`scripts/install-skills.sh --codex-track codex`. The claude track never
references it.

---

## §1 — MCP invocation contract

**Tool**: `mcp__codex__codex` (direct MCP call, distinct from `/codex:rescue`
or `/codex:review` which are code-only helpers).

Codex is **stateless per MCP call** — do not rely on prior-call context. Each
call must bundle:

1. A **clear role** (e.g. "rigorous peer reviewer for {venue}", "research
   novelty checker") at the top of the prompt.
2. **All artifact content** necessary for the review (draft section text,
   idea description, etc.). Do not assume shared state.
3. **Project context** limited to what the role needs — brief methodology /
   goals — to keep token budget tight.
4. **Explicit output schema** so the calling skill can parse the result
   without ambiguity (e.g. numbered sections, fixed field names).

Follow `codex:gpt-5-4-prompting` for phrasing style. Keep prompts under ~3k
tokens where possible; Codex/GPT-5.5 performs better on focused briefs than
long dumps.

---

## §2 — ADD mode synthesize patterns

### §2.1 — 3-way synthesize (writing-review)

Three independent reviews exist per round: Claude内部, Claude subagent, Codex.
Classify each finding into:

| Agreement | Meaning | Action |
|-----------|---------|--------|
| All 3 agree | Highest-confidence finding | Include in auto-fix list |
| 2-vs-1 (majority Claude, dissent Codex) | Likely in-family bias | Note in "Codex-only concern" — usually worth addressing |
| 2-vs-1 (majority Claude subagent + Codex, dissent Claude主) | Claude主 blind spot | Strongly include — external consensus trumps internal |
| 2-vs-1 (majority Claude主 + Codex, dissent Claude subagent) | Noise from subagent | Include in fix list, note subagent dissent |
| All 3 disagree | Subjective call | Flag for user, do not auto-fix |

**Score aggregation**: external score is `min(claude_subagent_score, codex_score)` —
stopping requires BOTH external reviewers to reach Accept, not just one.

### §2.2 — 4-source synthesize (idea-verify)

Four signals exist per verification: DBLP (hard), arXiv (hard), Claude
subagent (soft, in-family), Codex (soft, out-of-family).

Decision procedure:

1. **If either hard source (a/b) returns a direct match** → verdict is
   `already exists` or `incremental`. Soft sources (c/d) only refine the
   "closest work" citation list.
2. **If hard sources find nothing but both soft sources agree on
   "already exists / incremental"** → verdict is `incremental` with
   confidence = Medium. Surface which papers each soft source cited.
3. **If hard sources find nothing, soft sources disagree** → verdict =
   `somewhat novel` with confidence = Low. Flag for human with both
   soft-source opinions.
4. **If all four find nothing** → verdict = `highly novel` with
   confidence = High. Note that Codex (GPT-5.5 training cutoff is later
   than Claude's) is the more recent knowledge check.

Merge the "closest existing work" list across sources by deduplication on
(title, year). Preserve attribution — each paper in the merged list is
tagged with which source cited it.

---

## §3 — Codex unavailable fallback

Codex may fail per-call due to: MCP server down, rate limit, auth expiry,
network, or user revoked the Codex service mid-session.

Fallback rules:

1. **Detect on call**: wrap the `mcp__codex__codex` invocation with error
   handling. If the call fails or times out (>60s for a single review
   request), treat Codex as unavailable for this invocation.
2. **Degrade to Track A behavior**: proceed with the upstream review flow
   (Claude subagent only for writing-review; subagent + APIs for idea-verify).
   Do not abort the skill.
3. **Annotate the output report**: add a top-line note

   > **Cross-model review: partial** — Codex reviewer was unavailable for
   > this run. Review reflects Claude-only perspective; consider retry for
   > true cross-model signal.

4. **Do not retry automatically** within a single skill invocation. The
   user can re-invoke the skill manually once Codex is back.
5. **Loop skills (writing-review auto-fix)**: if Codex fails on Round N,
   log the fail and continue subsequent rounds with Claude subagent only.
   Do not alternate between Codex-and-not mid-loop — pick one regime
   after the first Codex failure of the run.

---

## §4 — Output conventions

Reports produced on Track B that consume this contract should:

- Save to the same location as Track A (do not introduce new paths just
  because Codex participated): `paper/reviews/{section}-cross-review.md`
  for writing-review; `methodology/ideas/{date}-discovery.md` append for
  idea-verify.
- Prefix the report with a small YAML header:
  ```yaml
  ---
  cross_model: true
  claude_subagent: {ok | failed}
  codex: {ok | failed | unavailable}
  synthesize_mode: {3-way | 4-source}
  ---
  ```
- Attribute each finding to its source(s): e.g. "(Claude subagent + Codex)",
  "(Codex only — possible Claude blind spot)". This attribution is the
  value of ADD mode — do not collapse into anonymous consensus bullets.

---

## §5 — Budget and rounds

Track B skills that loop (writing-review) must tighten loop bounds because
each round now fans out to TWO external reviewers instead of one:

| Skill | Track A max rounds | Track B max rounds |
|-------|-------------------:|-------------------:|
| writing-review | 4 | **3** |

Track B also changes TD-NL tracking metrics: record `codex_agreement_rate`
and `codex_availability` alongside the upstream `agreement_rate`. These let
future sessions decide whether the extra Codex call is pulling its weight
for a given artifact type.

Non-loop skills (idea-verify) incur only a single extra MCP call per
invocation — no budget change needed.
