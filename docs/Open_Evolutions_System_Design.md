This is the **Master Synthesis** of the **Open Evolutions** Design Document. It integrates the agentic "autoresearch" loop (see https://github.com/karpathy/autoresearch), the distributed "Folding@Home" compute model, the "Library of Lineages" branching strategy, and the tiered knowledge system for both humans and AI.  
---

# **Design Doc: Open Evolutions (v1.2)**

**Objective:** A decentralized, open-source research engine that evolves solutions to complex, non-linear problems (e.g., drug discovery, mathematical proofs). It leverages autonomous agent-led experimentation and distributed community compute to explore vast search spaces.

---

## **1\. System Architecture: The "Three-Layer" Model**

The framework moves the human from "doing" to "curating," providing a standardized environment where agents can conduct science.

### **A. The Core (Fixed Environment)**

* **task\_definition.md**: The "North Star." Natural language instructions, goals, and conceptual constraints for the AI agent.  
* **metrics.py**: The "Fitness Evaluator." Deterministic Python code that returns numerical/vector scores (e.g., toxicity, binding affinity, logical consistency).  
* **prepare.py**: A setup script that standardizes data, dependencies, and hardware checks across all distributed forks.  
* **execution.py**: The sandboxed "Evolution Chamber" where the LLM’s proposed code mutations are executed and measured.

### **B. The Lineage Library (Phylogenetic Management)**

Instead of a single "Master" branch, the project manages a **Forest of Lineages** to maintain diverse search paths.

* **Phylogenetic Mapping**: Every fork identifies its "Parent Lineage." Contributors can choose to optimize an existing approach or start a radical new one.  
* **Minimal Fitness Floor**: A PR must meet a baseline "survival" score before being considered for a branch, preventing the tree from being cluttered by noise.  
* **Survival of the Interesting**: PRs are merged if they are either **Superior** (higher fitness within a lineage) or **Significantly Novel** (introducing a "Predictive Surprise" or unique architectural shift).  
* **Selective Pruning**: Stagnant lineages are "frozen" and moved to /archives to keep the active search tree lean and focused.

### **C. Tiered Knowledge Architecture (The "Collective Memory")**

Knowledge is distilled through three layers to ensure scalability and prevent "context rot" for AI agents.

1. **Level 1: Raw Contribution Logs**: Every PR includes a contribution\_log.json (formerly "Shadow-Log"). These provide an immutable record of every local attempt and result.  
2. **Level 3: Lineage Wisdom**: Approach-specific JSON heuristics stored in /lineages/\[name\]/lineage\_learnings.json. This helps agents specializing in one approach avoid repeating lineage-specific mistakes.  
3. **Level 3: The Master Knowledge Base**:  
   * **learnings.json (The Brain)**: A machine-readable "Executive Summary" at the root for agent ingestion. It captures "Global Truths" and "Negative Constraints."  
   * **evolution.md (The Journal)**: The **Human-Readable** narrative of the project. It tracks major milestones, identifies the current "best-in-breed" solutions, and tells the story of how the problem is being solved.

---

## **2\. The Distributed Evolution Loop (Contributor Workflow)**

Contributors provide their own compute and LLM tokens to drive the project forward.

1. **Ingestion**: A contributor forks the repo. Their local agent (e.g., via **Claude Agent SDK**) reads the **Master Distillation** and **Lineage Wisdom** to understand the search space.  
2. **Autonomous Mutation**: The agent generates variations of the solution, running Karpathy-style 5-minute experiment loops on the user's local hardware.  
3. **Automatic Synthesis**: At the end of a session, a local script summarizes the "Shadow-Logs" into a distilled learnings.json specific to that fork.  
4. **Submission**: The user submits a PR containing the code mutation, the raw logs, and the distilled wisdom.

---

## **3\. Intelligent Selection & Merging**

The Project Organizer (assisted by a CI/CD bot) manages the repository using an **Exploration-Exploitation** balance:

* **Verification**: A GitHub Action re-runs the code in a clean environment to verify the claimed metric improvement (**Proof-of-Metric**).  
* **Novelty Check**: Does the PR offer a unique architectural path? If so, it may spawn a new lineage even if its score is initially lower than the global best.  
* **Hybridization (Consolidation)**: If the bot detects that two lineages are using similar logic to reach similar results, it issues a "Challenge" to the community to cross-breed them into a single superior lineage.

---

## **4\. Security & Epistemic Integrity**

* **Sandboxing**: All contributed code executes in restricted containers to protect host systems.  
* **Epistemic Labeling**: The knowledge base marks findings as **Positive Heuristics** (accelerants), **Negative Constraints** (dead ends), or **Unexplored Frontiers** (high-novelty targets).

---

### **Implementation Roadmap**

* **Phase 1**: Develop the **oe-cli** for local mutation and "Shadow-Log" capture.  
* **Phase 2**: Build the **"Grand Synthesizer"** bot to handle PR categorization and tiered distillation (Markdown and JSON).  
* **Phase 3**: Launch the first "Open Evolution" Grand Challenge.

---

