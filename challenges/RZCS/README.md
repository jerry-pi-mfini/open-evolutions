# Challenge #001: Riemann-Zeta Critical Strip (RZCS)

## Overview

The Riemann Hypothesis is one of the most important unsolved problems in
mathematics. It asserts that all non-trivial zeros of the Riemann Zeta function
lie on the critical line Re(s) = 1/2. For over 160 years, this conjecture has
resisted proof by individual researchers.

Open Evolutions takes a different approach: instead of waiting for a single
breakthrough, we evolve a **global proof-search tree** through distributed,
agent-driven formal verification. Every contribution that proves a new lemma or
eliminates a dead-end approach is merged into a collective intelligence that makes
the next attempt more likely to succeed.

All work is done in Lean 4, a formal verification language that guarantees
mathematical correctness. If a proof compiles, it is correct.

---

## Phase 1 Goal: The Narrowing Lemma

The immediate target is to prove the **Narrowing Lemma**: establish that for a
specific subset of s, no zeros of the Riemann Zeta function can exist at a
distance epsilon from the lines Re(s)=0 and Re(s)=1.

This is a stepping stone, not the full hypothesis. By narrowing the strip where
zeros can exist, we incrementally push toward the critical line.

### Constraints

- All submissions must be written in **Lean 4**.
- No `sorry` tags (Lean's placeholder for unproven assumptions) are allowed in
  final PRs.
- Agents should prioritize **symmetry arguments** and **contour integration**
  strategies.

### Success criteria

A submission is considered successful if:
- The Lean 4 code compiles without errors (sorry-free).
- It builds upon existing project lemmas or Mathlib foundations.
- It advances the proof state toward the Narrowing Lemma.

---

## Seed Lineages

Three starting lineages provide different angles of attack. Each represents a
distinct mathematical strategy.

### analytic-continuation

**Directory:** `lineages/analytic-continuation/`

Focuses on the functional equation and traditional complex analysis. This is the
most classical approach. The functional equation relates zeta(s) to
zeta(1-s), and this symmetry is a powerful tool for reasoning about the critical
strip.

**Known heuristic:** Transforming the zeta function into the Xi function
simplifies symmetry arguments significantly (estimated 40% reduction in proof
complexity).

**Known dead end:** Basic induction on the critical strip fails at the boundary.

### computational-bounds

**Directory:** `lineages/computational-bounds/`

Focuses on establishing zero-free regions through high-precision interval
arithmetic. Rather than proving structural properties of zeta, this lineage works
by computationally bounding where zeros can and cannot exist, then formalizing
those bounds in Lean.

### operator-theory

**Directory:** `lineages/operator-theory/`

A high-risk, high-reward approach that treats the zeros of the zeta function as
eigenvalues of operators. This connects to the Hilbert-Polya conjecture and
random matrix theory. No lineage has fully explored this direction yet.

---

## Current Knowledge Base Status

The master knowledge base (`knowledge/learnings.json`) contains the following
findings from early runs:

### Negative constraints (dead ends to avoid)

- Attempting to use basic induction on the critical strip consistently fails at
  the boundary. (Source: `induction_tests.lean`, confidence: high)

### Positive heuristics (strategies that help)

- Transforming the zeta function into the Xi function simplifies symmetry proofs
  by an estimated 40%. (Confidence: medium)

### Unexplored frontiers (high-novelty targets)

- **Topological methods** applied to the critical strip -- no lineage has
  attempted topological arguments yet.
- **Probabilistic models** of zero distribution -- random matrix theory
  connections remain unexplored in formal verification.

The human-readable evolution journal is at `knowledge/evolution.md`. No major
milestones have been recorded yet. This is the ground floor.

---

## Getting Started

### 1. Install and initialize

```bash
pip install -e .
export ANTHROPIC_API_KEY=sk-ant-...
oe-cli init --challenge RZCS
```

### 2. Choose your approach

Pick a lineage to work on, or let the agent decide:

```bash
# Work on a specific lineage
oe-cli start --challenge RZCS --lineage analytic-continuation

# Let the agent choose
oe-cli start --challenge RZCS
```

### 3. Run the evolution loop

The agent will read the knowledge base, propose Lean 4 mutations, compile them,
and record results. A default session runs 10 cycles of 5 minutes each:

```bash
oe-cli start --challenge RZCS --cycles 10 --cycle-minutes 5
```

For sandboxed execution:

```bash
oe-cli start --challenge RZCS --docker
```

### 4. Review and submit

After the session completes, check `contribution_log.json` for results. If you
have at least one successful compilation, submit:

```bash
oe-cli submit --lineage analytic-continuation
git push origin submission/analytic-continuation/<timestamp>
```

Then open a pull request on GitHub.

### 5. Read the docs

- [System design](../docs/Open_Evolutions_System_Design.md) -- full architecture
  overview.
- [Contributing guide](../CONTRIBUTING.md) -- detailed workflow and submission
  rules.
- [Agent configuration](../docs/agent_configuration.md) -- API keys, Docker
  setup, troubleshooting.

---

## Fitness Metrics

Submissions to the RZCS challenge are scored on three axes:

| Metric | Symbol | Type | Description |
|---|---|---|---|
| Verification | V | Binary (0/1) | Does the Lean 4 code compile without errors? |
| Lemma Depth | D | Integer | How many axioms and lemmas does the proof build on? |
| Interestingness | I | Float (0.0-1.0) | Does the proof use novel Mathlib modules? |

A PR must achieve V=1 (compiles successfully) to pass the minimum fitness floor.
Higher D and I scores increase the likelihood of the PR being merged and may
trigger the creation of a new lineage.
