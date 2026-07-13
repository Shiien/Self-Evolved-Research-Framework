---
name: theory
description: All theory-side mathematical work in one mode-based skill — FORMALIZE (informal claim → precise LaTeX statement with assumptions and strategy candidates), DECOMPOSE (hard theorem → sub-lemma dependency graph with critical path), SEARCH (stuck on a step → cross-domain known results and techniques), COUNTEREXAMPLE (stress-test a conjecture with degenerate/boundary/pathological cases), GENERALIZE (proven result → generalization axes and which proof steps break). Absorbs the former theory-formalize / theory-decompose / theory-search / theory-counterexample / theory-generalize skills — those names now refer to modes here. Triggers on "I conjecture that…", "make this rigorous", "how do I prove this?", "is there a known result for…", "is this true?", "can we generalize?".
---

# theory

For producing/reviewing actual proofs use the `proof` skill; this skill works
on the *statements* — formalizing, decomposing, hunting techniques,
stress-testing, generalizing.

## Mode: FORMALIZE — "I conjecture…", "make this rigorous"

1. Parse the informal statement; identify assumptions, variables, domains,
   claim type (existence / uniqueness / bound / equivalence).
2. Output a precise LaTeX statement + required definitions and notation.
3. List candidate proof strategies (direct, contradiction, induction,
   construction) with one-line fit rationale.
4. Save to `outputs/{topic}/theory/` on confirmation.
→ complex claim: DECOMPOSE; existing draft: `proof` (critique mode);
surprising claim: COUNTEREXAMPLE first.

## Mode: DECOMPOSE — "how do I prove this?", multi-step goals

1. Split the main claim into precisely-stated sub-lemmas.
2. Classify each: difficulty (routine / moderate / hard / open) + suggested
   technique.
3. Draw the text-based dependency graph; identify the critical path (the
   hardest blocking sub-lemma).
4. Save substantial roadmaps to `outputs/{topic}/roadmaps/`.
→ hard sub-lemma: SEARCH; user supplies an attempt: `proof` (critique mode).

## Mode: SEARCH — "is there a known result for…", stuck on a step

1. Identify the mathematical structure of the obstacle.
2. Sweep candidate domains: spectral graph theory, functional analysis,
   optimization, information geometry, statistical learning theory,
   topology/algebra where relevant.
3. Per candidate result: statement with reference, applicability (direct /
   needs adaptation / inspirational), application sketch.
4. Rank by relevance × feasibility.
→ applicable theorem found: FORMALIZE the adapted statement.

## Mode: COUNTEREXAMPLE — "is this true?", pre-proof stress test

1. Attack the claim: degenerate cases (n=1, empty set, identity), boundary
   cases (parameter extremes), known pathologies of the domain.
2. Found → present the *minimal* counterexample, name the violated
   assumption, propose the strengthened statement.
3. Not found → state confidence + which case families were checked; this
   supports (never proves) the claim.
4. Save significant counterexamples to `outputs/{topic}/counterexamples/`.
→ corrected statement: FORMALIZE; claim survives: `proof` (write mode).

## Mode: GENERALIZE — "does this extend to…", after a special case lands

1. Identify exactly which assumptions the existing proof uses.
2. Propose generalization axes: weaker assumptions (convex → quasi-convex),
   higher dimensions/spaces, different norms/metrics, stochastic/approximate
   versions.
3. Per axis: generalized claim, feasibility (likely true / unclear / likely
   false), and *which proof steps break*.
4. Recommend the most promising axis.
→ promising axis: DECOMPOSE the generalized proof.

**Inputs**: claims / goals / proven results (natural language or LaTeX)
**Outputs**: inline analyses; artifacts under `outputs/{topic}/` when substantial
**Token**: ~2-8K per mode
**Composition**: feeds the `proof` skill; surprising conjectures should pass
COUNTEREXAMPLE before anyone invests in a proof.
