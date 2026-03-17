# Contributing to Open Evolutions

Thank you for contributing compute, ideas, and proofs to the Open Evolutions
project. This guide walks you through everything you need to get started and
submit high-quality contributions.

---

## Prerequisites

- **Python 3.11+** -- required to run `oe-cli` and the synthesizer tooling.
- **Lean 4** -- the formal verification language used for all proof submissions.
  Install via [elan](https://github.com/leanprover/elan):
  ```bash
  curl -sSf https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | sh
  ```
  Restart your shell after installation so that `lean` and `lake` are on your PATH.
- **Docker** (optional but recommended) -- enables sandboxed execution of
  mutations, which isolates untrusted code from your host system. Install from
  [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/).
- **An Anthropic API key** -- the evolution loop uses the Anthropic API to drive
  the AI agent. Obtain one at [https://console.anthropic.com/](https://console.anthropic.com/).

---

## Setup

### 1. Fork and clone

Fork the repository on GitHub, then clone your fork:

```bash
git clone https://github.com/<your-username>/open-evolutions.git
cd open-evolutions
```

### 2. Install the CLI

Create a virtual environment and install the project in editable mode:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Or, if you use [uv](https://github.com/astral-sh/uv):

```bash
uv venv && source .venv/bin/activate && uv pip install -e .
```

### 3. Set your API key

Export your Anthropic API key so the agent can call the LLM:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Alternatively, create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=sk-ant-...
```

The CLI loads `.env` automatically on startup.

### 4. Initialize the environment

Run the init command to verify your toolchain and fetch dependencies:

```bash
oe-cli init --challenge RZCS
```

This will:
- Check that `lean` and `lake` are installed.
- Check that Docker is available (warns if not).
- Initialize the knowledge base (`knowledge/learnings.json`, `knowledge/evolution.md`).
- Set up the three seed lineages.
- Run `lake update` to fetch Mathlib (this can take several minutes on first run).

---

## The Evolution Workflow

### How `oe-cli start` works

When you run the evolution loop, the following happens in each cycle:

1. **Ingestion** -- The agent reads the master knowledge base
   (`knowledge/learnings.json`) and the task definition (`core/task_definition.md`).
   If you selected a lineage, it also reads that lineage's
   `lineage_learnings.json` to understand approach-specific heuristics and dead
   ends.

2. **Mutation proposal** -- The agent constructs a prompt from all accumulated
   knowledge (including results from previous cycles in the current session) and
   calls the LLM. The LLM returns a Lean 4 code block representing a proposed
   proof step.

3. **Execution** -- The proposed code is written to a temporary file and compiled
   using `lake` (or inside a Docker container if `--docker` is set). The fitness
   evaluator (`core/metrics.py`) scores the result on three axes: Verification
   (V), Lemma Depth (D), and Interestingness (I).

4. **Recording** -- The result (pass/fail, fitness scores, duration, errors) is
   appended to `contribution_log.json`.

5. **Lint and retry** -- Before compilation, a lint pass auto-fixes known bad
   patterns (e.g., `Complex.abs` is replaced with norm notation). If compilation
   fails, the error is fed back to the agent for up to 3 retry attempts within
   the same cycle.

6. **Iteration** -- The agent incorporates the result into its context and begins
   the next cycle. Failed attempts inform future proposals by narrowing the
   search space.

After all cycles complete, a session synthesis is saved to
`session_synthesis.json` summarizing the run's outcomes.

### Command reference

```bash
# Run 10 cycles (default), agent chooses lineage
oe-cli start --challenge RZCS

# Run 20 cycles on a specific lineage, 3 minutes per cycle
oe-cli start --challenge RZCS --lineage analytic-continuation --cycles 20 --cycle-minutes 3

# Run in Docker sandbox
oe-cli start --challenge RZCS --docker

# Check current environment status
oe-cli status
```

---

## Submission Guidelines

When your evolution session produces at least one successful compilation, you can
package the results into a PR.

### What a PR must contain

1. **Lean 4 code** -- Any new or modified `.lean` files in your lineage
   directory (`lineages/<name>/`). The code must compile without errors and must
   not contain any `sorry` placeholders.

2. **contribution_log.json** -- The raw log of every mutation attempted during
   your session. This is the immutable record that feeds the knowledge base.

3. **Distilled learnings** -- A `contribution_distilled.json` file summarizing
   your session's findings (generated automatically by `oe-cli submit`). This
   includes success rates, best scores, and recurring error patterns.

### How to submit

```bash
oe-cli submit --lineage analytic-continuation --message "Proved Xi-symmetry lemma"
```

This command will:
- Validate that you have a contribution log with at least one successful mutation.
- Distill your session logs into `contribution_distilled.json`.
- Create a Git branch named `submission/<lineage>/<timestamp>`.
- Stage and commit all required files.

Then push and open a PR:

```bash
git push origin submission/<lineage>/<timestamp>
```

### What happens after submission

A GitHub Actions pipeline will:
- Re-run your Lean code in a clean CI environment (Proof-of-Metric verification).
- Check that the fitness score meets the minimum survival floor.
- Classify the PR as either superior within its lineage or novel enough to spawn
  a new lineage.

---

## How Lineages Work

### Choosing a lineage

Each lineage represents a distinct proof strategy. The current seed lineages are:

| Lineage | Approach |
|---|---|
| `analytic-continuation` | Functional equation, traditional complex analysis |
| `computational-bounds` | Zero-free regions, high-precision interval arithmetic |
| `operator-theory` | Zeros as eigenvalues of operators (high-risk, high-reward) |

To work on a specific lineage, pass `--lineage <name>` to `oe-cli start`. If you
omit this flag, the agent will choose based on the current knowledge base.

### Spawning a new lineage

If your work introduces a fundamentally different approach not represented by any
existing lineage, the synthesizer bot may create a new lineage branch from your
PR. New lineages must demonstrate sufficient novelty (a high Interestingness
score) to justify the additional search branch. Lineages that stagnate over time
are frozen and moved to `/archives/`.

---

## Fitness Metrics

Every submission is evaluated on three axes:

### V -- Verification

Binary score (0 or 1). Does the Lean 4 code compile without errors? This is the
minimum survival floor: a submission that does not compile cannot be merged.

### D -- Lemma Depth

An integer count of how many foundational axioms, Mathlib theorems, and project
lemmas the submission builds upon. Higher depth indicates that the proof is
connecting to established mathematical foundations.

### I -- Interestingness

A float from 0.0 to 1.0 measuring novelty. This is computed by comparing the
Mathlib modules imported by the submission against those already known to the
existing lineages. A submission that uses entirely new modules scores higher. This
metric drives exploration of the search space.

---

## Code of Conduct

- **Be constructive.** Every failed proof path is valuable data. Report your dead
  ends honestly so others can avoid them.
- **Respect compute donations.** Contributors donate their own hardware and API
  tokens. Do not submit frivolous PRs that waste CI resources.
- **Credit your lineage.** When building on another contributor's work, reference
  the parent submission in your PR description.
- **Keep the knowledge base honest.** Do not fabricate results or tamper with
  contribution logs. The Proof-of-Metric CI pipeline will catch discrepancies.
- **Be patient with Lean.** Mathlib builds are slow. First-time `lake update`
  runs can take 10-30 minutes.
