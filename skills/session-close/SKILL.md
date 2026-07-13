---
name: session-close
description: Evidence-first conversation wrap-up. Writes what the session established into RESEARCH_STATE.md (evidence with run ids and strength stamps, hypothesis changes, uncertainties, next experiments), resolves EXPERIMENTS.json entries, chains the memory skill (write mode) for durable non-scientific facts. Digest logs and skill audits are optional on user request. Triggers on end-of-conversation signals (user says goodbye/done, or a long session with substantial work completed).
---

# session-close

**Trigger**: Conversation is ending (user says goodbye/done, or long session
with substantial work completed).

**Principle**: never rely on conversation history as memory. Anything worth
keeping must land in the file that owns it (see `CLAUDE.md § State`).

**Process**:
1. **RESEARCH_STATE.md** — for each thing this session established, append or
   amend the owning section:
   - `## Established evidence`: one line per resolved experiment/finding —
     `[date] {exp/run id}: SUPPORTS/CONTRADICTS — {question} | {criterion
     detail} | strength: {stamp}`. Record contradicting evidence with the
     same care as supporting evidence.
   - `## Active hypotheses`: add/retire/annotate (cite the evidence line).
   - `## Unresolved uncertainties`: new unknowns, crashed runs (crash ≠
     negative evidence), noise caveats.
   - `## Next recommended experiments`: keep it a short, ordered list.
2. **EXPERIMENTS.json** — set status/run/verdict for anything resolved;
   enqueue experiments the session designed (each needs a config with a
   contract before it can run).
3. **Checklists** — mark deliverable items completed this session
   (`checklist` update mode; recount caches while there), if any.
4. **memory (write mode)** — only durable non-scientific facts (user
   preferences, environment quirks, procedures). Scientific findings do NOT
   go to memory.
5. Ask once: "Save narrative digest log? [y/N]" — only on yes, write
   `logs/digest/YYYY-MM-DD.yaml` (legacy format). Default no.
6. Ask once: "Run skill audit? [y/N]" — only on yes, chain `evolve-suggest`.

**Inputs**: session outcomes, RESEARCH_STATE.md, EXPERIMENTS.json
**Outputs**: updated state files (+ optional digest)
**Token**: ~1-3K
**Composition**: chains `checklist` (update mode), `memory` (write mode);
optional `evolve-suggest`; terminal.
