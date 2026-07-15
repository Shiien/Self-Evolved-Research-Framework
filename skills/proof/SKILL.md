---
name: proof
description: All proof-side work in one mode-based skill — WRITE (theorem statement → first-draft proof with strategy selection and per-step justification), CRITIQUE (audit a draft for fatal/major/minor issues → Sound / Fixable / Fundamentally flawed), FIX (rewrite flagged steps and re-check downstream), FORMALIZE (validated proof → publication LaTeX), VERIFY (spot-check a formula or algebraic step symbolically/numerically/dimensionally → CONFIRMED / REFUTED / INCONCLUSIVE). Absorbs the former proof-write / proof-critique / proof-fix / proof-formalize / proof-verify skills — those names now refer to modes here. Triggers on "prove that…", "证明", "is this proof correct?", "fix this step", "make this publication-ready", "check this formula".
---

# proof

Statement-level work (formalizing, decomposing, counterexamples) is the
`theory` skill. The canonical chain: WRITE → CRITIQUE → FIX → FORMALIZE, with
VERIFY as a spot-check anywhere.

## Mode: WRITE — "prove that …", no existing draft

1. **Analyze the proposition.** Rewrite it in standard quantifier form and
   read it back if any ambiguity exists ("'sufficiently large n' — fixed n₀
   or n → ∞?"). Classify the statement — it drives strategy:
   universal → direct/induction/contrapositive · existential → construction
   or non-constructive · equivalence → both directions separately ·
   bound → direct or induction on structure · uniqueness → existence + two-
   witnesses-equal · non-existence → contradiction/diagonal.
   List the available toolkit (premises, cited lemmas, in-scope definitions).
   If the user cites "Lemma 3.2" without giving it — ask, don't invent.
2. **Select the strategy** and state in one sentence why it fits (so the
   user can course-correct early). If two look viable, pick the shorter;
   prefer direct over contradiction — contradictions are harder to audit.
3. **Build step-by-step.** Every step carries exactly one justification:
   "by assumption {which}" / "by Lemma {ref}" / "by definition of {term}" /
   "by step {n}" / "by algebra (trivial only)" / "by induction hypothesis".
   Rules: introduce variables before use ("Let x ∈ X be arbitrary"); dispatch
   edge cases up front (n=0, empty set, degenerate configs, ≤1 line each);
   never use the conclusion in a step; promote any step needing its own
   sub-argument to a Lemma; induction = base case, hypothesis, step as three
   separate blocks; case analysis = numbered cases + one-line exhaustivity
   argument.
4. **Self-audit** before handoff: variable scoping, circularity, edge cases
   dispatched, final line literally states the theorem's conclusion, no
   naked "clearly/obviously". (Catches ~60-70% cheaply; not a substitute
   for CRITIQUE.)
5. **Emit LaTeX** (`\begin{theorem}…\begin{proof}`; promoted lemmas get their
   own environments) and save to `paper/proofs/{name}.tex` if that directory
   exists, else `outputs/{topic}/proofs/{name}.tex` — `\input`-able, no
   preamble.

Pitfalls to check: accidentally proving a stronger statement (implicit
premises); wrong base-case index; reused variable names across nested
quantifiers; ε-dependence of "there exists N"; citing unproved lemmas ("by a
standard result" is not a proof); proving only one direction of an iff;
non-exhaustive cases (x>0 / x<0 omits 0); LaTeX syntax errors that make the
critique trip on syntax instead of logic.

## Mode: CRITIQUE — "is this proof correct?"

1. Track each logical step. Classify issues:
   **Fatal** (gaps, circularity, unjustified claims, reversed implication) ·
   **Major** (missing edge cases, unstated assumptions, unclear notation) ·
   **Minor** (style, redundancy).
2. Per issue: quote the exact step, explain the defect, suggest the fix.
3. Verdict: **Sound / Fixable / Fundamentally flawed** (+ note strengths if
   sound).
→ fatal/major: FIX · clean: FORMALIZE.

## Mode: FIX — after CRITIQUE or "how do I fix this step?"

Rewrite only the flagged steps with correct reasoning, explain why the
original failed, verify downstream steps still hold, present the corrected
segment in context. → re-CRITIQUE if the fix was structural, else FORMALIZE.

## Mode: FORMALIZE — "make this publication-ready"

Validated proofs only. Proper theorem/lemma/proof environments, notation
aligned with paper conventions, every step justified, standard results cited
properly. Save to `outputs/{topic}/proofs/{theorem_name}.tex` (or
`paper/proofs/`). → feeds `writing` (draft mode).

## Mode: VERIFY — "check this formula", "does this simplify to…"

Symbolic manipulation, numeric probing (multiple random inputs), and
dimensional/type checks — run Python/SymPy when it helps. Report
**CONFIRMED** (show the verification) / **REFUTED** (minimal counterexample +
suggested correction → FIX) / **INCONCLUSIVE** (why + what would decide it).

**Inputs**: theorem statements, proof drafts, expressions
**Outputs**: `paper/proofs/` or `outputs/{topic}/proofs/` artifacts; critiques inline
**Token**: WRITE 3-12K · CRITIQUE 3-10K · FIX 3-8K · FORMALIZE 3-10K · VERIFY 2-5K
**Composition**: statement needs decomposition first → `theory` (decompose);
surprising theorem → `theory` (counterexample) before WRITE.
