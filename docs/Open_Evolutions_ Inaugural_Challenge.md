To launch **Open Evolutions**, we’ll frame the inaugural challenge as a search for **"The Zeta-Critical Proofs."** This README will serve as the template for every future "Evolution" launched on your platform.

It needs to be part-manifesto, part-technical-manual.

---

# **Open Evolutions: Inaugural Challenge**

## **Challenge \#001: The Riemann-Zeta Critical Strip (RZCS)**

### **1\. The Vision**

The Riemann Hypothesis is the "Everest" of mathematics. For 160 years, human intuition has scaled its slopes but never reached the peak. **Open Evolutions** aims to solve this not by finding a single genius, but by evolving a **Global Proof-Search Tree**.

Using the Lean 4 formal verification language, we will swarm the critical strip. Every contribution that proves a new lemma or eliminates a dead-end approach is merged into our collective intelligence.

---

### **2\. Task Definition (task\_definition.md)**

**Objective:** Construct a formally verified proof in Lean 4 that establishes specific properties of the Riemann Zeta Function ($\\zeta(s)$) within the critical strip.

**Phase 1 Goal:** Prove the "Narrowing Lemma"—establish that for a specific subset of $s$, no zeros can exist at a distance $\\epsilon$ from the lines $Re(s)=0$ and $Re(s)=1$.

**Constraints:**

* All submissions must be written in **Lean 4**.  
* No "sorry" tags (Lean’s placeholder for unproven assumptions) allowed in final PRs.  
* Agents should prioritize **Symmetry Arguments** and **Contour Integration** lineages.

---

### **3\. The Judge (metrics.py)**

In this evolution, "Fitness" is binary (it either compiles or it doesn't), so we use **"Proof Progress"** as the primary metric.

* **Metric 1: Lean Verification ($V$):** A binary $0$ or $1$. Does the code compile without errors?  
* **Metric 2: Lemma Depth ($D$):** How many foundational axioms or previous project lemmas does this proof successfully build upon?  
* **Metric 3: Interestingness ($I$):** Does the proof use a novel mathematical library or approach (e.g., shifting from Analytic to Topological methods) not yet represented in the lineages/ folder?

---

### **4\. Current Lineages (The Starting Forest)**

To kickstart the evolution, the repository contains three seed lineages:

1. **lineages/analytic-continuation/**: Focuses on the functional equation and traditional complex analysis.  
2. **lineages/computational-bounds/**: Focuses on establishing zero-free regions through high-precision interval arithmetic.  
3. **lineages/operator-theory/**: A high-risk, high-reward approach treating zeros as eigenvalues of operators.

---

### **5\. How to Contribute**

1. **Fork the Repo:** Clone the Open Evolutions structure.  
2. **Initialize the Agent:** Run oe-cli start \--challenge RZCS. This will feed your agent the current learnings.json (the list of all failed proof paths).  
3. **Evolve:** Your local agent will attempt to bridge the gap between "Axiom A" and "Target Lemma B."  
4. **Submit:** If your agent finds a verified path, submit a PR.  
   * **The Reward:** Your name (and your agent's version) will be etched into the evolution.md journal as the discoverer of that milestone.

---

### **6\. The Knowledge Base (learnings.json snippet)**

Current "Global Truths" discovered by early runs:

* **Negative Constraint:** "Attempting to use basic induction on the critical strip consistently fails at the boundary; avoid File: induction\_tests.lean."  
* **Positive Heuristic:** "Transforming the zeta function into the $Xi$ function $(\\xi)$ simplifies the symmetry proofs by 40%."

---

