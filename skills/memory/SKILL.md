---
name: memory
description: All persistent-memory operations in one mode-based skill — WRITE (persist a durable insight/decision to memory/episodes/, importance-gated), RETRIEVE (surface relevant episodes/topics/procedures for the current task), CONSOLIDATE (synthesize 3+ related episodes into topics/procedures, keep MEMORY.md under its 200-line budget), FORGET (prune low-value memories under capacity pressure). Absorbs the former memory-write / memory-retrieve / memory-consolidate / memory-forget skills — those names now refer to modes here. Scope: durable NON-scientific context only; evidence lives in RESEARCH_STATE.md. Triggers on "remember this", "what do we know about X", at session-close, or on capacity thresholds.
---

# memory

**Shared context**: Read `skills/_shared/memory-tiers.md` first (tier
definitions, episode/topic/procedure formats, MEMORY.md index rules).

**Scope note**: memory holds durable **non-scientific** context — user
preferences, environment quirks, procedures, project constraints. Scientific
findings go to `RESEARCH_STATE.md § Established evidence`; if asked to
"remember" a finding, route it there instead.

## Mode: WRITE — "remember this", insight-producing skills, session-close

1. Assess importance 1-10 (novelty to project, decision significance,
   error severity, cross-topic relevance). Importance < 5 → skip silently.
2. Duplicate check against the `memory/MEMORY.md` index — duplicates update
   the existing file rather than creating a new one.
3. Write `memory/episodes/YYYY-MM-DD-NNN.md` (episode format from
   `memory-tiers.md`); prepend to MEMORY.md's Recent Episodes (keep last 10).
4. MEMORY.md > 180 lines → chain CONSOLIDATE.

## Mode: RETRIEVE — before knowledge-dependent work, "what do we know about X"

1. Form the query: what does the current task actually need?
2. Score MEMORY.md index entries: tag overlap, keyword match, recency,
   importance. Read the top ~3 full files only.
3. Surface the relevant content inline. Not by default at session-open — the
   SessionStart hook covers state; retrieve on demand.

## Mode: CONSOLIDATE — session-close check, >180 lines, 15+ loose episodes

1. Cluster unconsolidated episodes (tag overlap → source → temporal
   proximity). 3+ related episodes → synthesize `memory/topics/{slug}.md`;
   2+ describing the same multi-step process → `memory/procedures/{slug}.md`.
2. Mark sources `consolidated: true`; update the index.
3. Still > 200 lines → chain FORGET.

## Mode: FORGET — capacity pressure

Prune: unretrieved episodes with importance < 5, consolidated episodes with
importance < 7, superseded decisions. **Never forget**: architectural
decisions, key findings pointers, active constraints. Update the index.

**Inputs**: insight / query / capacity trigger
**Outputs**: episode/topic/procedure files + MEMORY.md index (WRITE paths);
inline context (RETRIEVE)
**Token**: ~1-3K per operation
**Composition**: WRITE chained from session-close; CONSOLIDATE → FORGET on
overflow.
