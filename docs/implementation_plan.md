# Open Evolutions — Implementation Plan

## Phase 1: Core Environment & `oe-cli` (Foundation) [DONE]

### 1.1 — Repository Scaffold
- Create the canonical directory structure: `/core/`, `/lineages/`, `/archives/`, `/knowledge/`
- Write template files: `task_definition.md`, `metrics.py`, `prepare.py`, `execution.py`
- Set up `learnings.json` (master knowledge base) and `evolution.md` (human journal)

### 1.2 — `oe-cli` Tool
- CLI tool (Python + Typer) that contributors install
- Commands:
  - `oe-cli init` — fork setup, dependency check, Lean 4 toolchain verification
  - `oe-cli start --challenge RZCS` — ingests master `learnings.json` + chosen lineage's `lineage_learnings.json`, launches the agent loop
  - `oe-cli evolve` — runs the autonomous mutation loop (Karpathy-style 5-min experiment cycles) using Claude Agent SDK
  - `oe-cli submit` — packages code mutation + `contribution_log.json` + distilled learnings into a PR-ready branch

### 1.3 — Sandboxed Execution Chamber
- `execution.py` runs Lean 4 compilation in a restricted container (Docker-based)
- `metrics.py` extracts: verification status (V), lemma depth (D), interestingness score (I)
- `prepare.py` handles Lean 4 / Mathlib setup, data standardization

### 1.4 — Agent Loop Integration
- Integrate with Claude Agent SDK for the autonomous mutation cycle
- Agent reads knowledge base → proposes Lean 4 code mutations → executes in sandbox → records results in `contribution_log.json`
- Local synthesis script distills session logs into fork-level `learnings.json`

---

## Phase 2: Grand Synthesizer Bot & CI/CD [DONE]

### 2.1 — GitHub Actions Pipeline
- **Proof-of-Metric**: re-run submitted Lean code in clean CI environment, verify claimed scores
- **Fitness Floor Gate**: reject PRs below minimum survival score
- **Lineage Classification**: auto-detect which lineage a PR belongs to (or if it spawns a new one)

### 2.2 — Grand Synthesizer Bot
- Runs on PR merge events
- **Tiered Distillation**: updates `lineage_learnings.json` and master `learnings.json` with new findings
- **Novelty Check**: detects if a PR introduces a genuinely new approach → creates new lineage branch
- **Hybridization Alerts**: detects converging lineages → issues community challenges to cross-breed
- **Pruning**: flags stagnant lineages for archival

### 2.3 — Knowledge Base Management
- Automated updates to `evolution.md` (the human-readable journal)
- Epistemic labeling: positive heuristics, negative constraints, unexplored frontiers

---

## Phase 3: Inaugural Challenge Launch (RZCS) [DONE]

### 3.1 — Seed Content
- Populate three starter lineages with initial Lean 4 scaffolds:
  - `lineages/analytic-continuation/` — functional equation, complex analysis
  - `lineages/computational-bounds/` — zero-free regions, interval arithmetic
  - `lineages/operator-theory/` — spectral interpretation of zeros
- Pre-populate `learnings.json` with known heuristics and negative constraints

### 3.2 — Documentation & Onboarding
- Contributor guide, challenge README
- Agent configuration guide (how to plug in your LLM API keys)

### 3.3 — Launch
- Open the repo, announce the challenge, accept first community PRs

---

## Tech Stack

| Component | Technology |
|---|---|
| CLI | Python + Typer |
| Agent runtime | Claude Agent SDK |
| Formal verification | Lean 4 + Mathlib |
| Sandboxing | Docker containers |
| CI/CD | GitHub Actions |
| Synthesizer bot | Python service (GitHub App or Action) |
| Knowledge format | JSON (machine) + Markdown (human) |

---

## Key Risks & Mitigations

- **Lean 4 compilation is slow** — cache Mathlib builds, use incremental compilation in `prepare.py`
- **Agent quality variance** — the fitness floor + proof-of-metric CI ensures only verified work merges
- **Lineage explosion** — aggressive pruning policy + minimum novelty threshold for new lineages
- **Security** — all contributed code runs in sandboxed containers; never on bare metal
