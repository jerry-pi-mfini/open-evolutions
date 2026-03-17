# Open Evolutions

**A decentralized research engine that evolves solutions to complex problems.**

Open Evolutions is an open-source platform where autonomous AI agents and human
contributors collaborate to tackle hard, non-linear research problems. Contributors
donate their own compute and LLM tokens to drive an evolutionary search process:
agents propose mutations, a formal verifier judges them, and the best results are
merged into a shared knowledge base that makes every subsequent attempt smarter.

The project is inspired by [Karpathy's autoresearch](https://github.com/karpathy/autoresearch)
loop and the distributed compute model pioneered by Folding@Home.

---

## Active Challenge

**Challenge #001: Riemann-Zeta Critical Strip (RZCS)**

The inaugural challenge targets the Riemann Hypothesis through formal verification
in Lean 4. The Phase 1 goal is to prove the "Narrowing Lemma" -- establish that
for a specific subset of s, no zeros of the Riemann Zeta function can exist at a
distance epsilon from the lines Re(s)=0 and Re(s)=1.

Three seed lineages are available: analytic-continuation, computational-bounds,
and operator-theory. See [challenges/RZCS/README.md](challenges/RZCS/README.md)
for full details.

---

## Prerequisites

- **Python 3.11+**
- **Lean 4** — required for proof compilation and verification. Install via [elan](https://github.com/leanprover/elan):
  ```bash
  curl -sSf https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | sh
  ```
  Restart your shell after installation so that `lean` and `lake` are on your PATH.
- **Anthropic API key** — needed for the AI agent. Get one at [console.anthropic.com](https://console.anthropic.com/).
- **Docker** (optional) — enables sandboxed execution of mutations.

---

## Quick Start

```bash
# 1. Fork and clone the repository
git clone https://github.com/<your-username>/open-evolutions.git
cd open-evolutions

# 2. Create a virtual environment and install the CLI
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Or, if you use uv (https://github.com/astral-sh/uv):
#   uv venv && source .venv/bin/activate && uv pip install -e .

# 3. Set your Anthropic API key (or add to a .env file in the project root)
export ANTHROPIC_API_KEY=sk-ant-...

# 4. Initialize the environment (checks Lean 4, fetches Mathlib)
oe-cli init --challenge RZCS

# 5. Run the evolution loop
oe-cli start --challenge RZCS --cycles 10

# 6. Submit your results as a PR
oe-cli submit --lineage analytic-continuation
```

---

## How It Works

Open Evolutions uses a **three-layer architecture** to coordinate distributed
research:

### Layer 1 -- The Core (Fixed Environment)

A stable set of files that define the problem and judge solutions:

- `core/task_definition.md` -- the natural-language description of the goal.
- `core/metrics.py` -- the fitness evaluator that scores submissions on
  Verification (V), Lemma Depth (D), and Interestingness (I).
- `core/execution.py` -- the sandboxed "evolution chamber" where proposed
  mutations are compiled and measured.
- `core/prepare.py` -- environment setup (Lean 4, Mathlib, Docker checks).

### Layer 2 -- The Lineage Library (Phylogenetic Management)

Instead of one master branch of work, the project maintains a **forest of
lineages** -- diverse proof strategies that evolve in parallel. Contributors
choose an existing lineage to extend or spawn a new one. Stagnant lineages are
pruned to keep the search tree focused.

### Layer 3 -- Tiered Knowledge Architecture (Collective Memory)

Knowledge flows upward through three tiers:

1. **Raw Contribution Logs** -- immutable records of every local experiment
   (`contribution_log.json`).
2. **Lineage Wisdom** -- approach-specific heuristics stored in each lineage's
   `lineage_learnings.json`.
3. **Master Knowledge Base** -- `knowledge/learnings.json` (machine-readable
   global truths and dead ends) and `knowledge/evolution.md` (the human-readable
   narrative journal).

---

## Architecture Overview

See [docs/Open_Evolutions_System_Design.md](docs/Open_Evolutions_System_Design.md)
for the full system design document, and
[docs/implementation_plan.md](docs/implementation_plan.md) for the phased
implementation roadmap.

---

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, the evolution
workflow, submission guidelines, and how lineages and fitness metrics work.

---

## License

This project is released under the [MIT License](LICENSE).
