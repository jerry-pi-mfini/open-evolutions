import Lake
open Lake DSL

package OpenEvolutions where
  leanOptions := #[
    ⟨`autoImplicit, false⟩
  ]

@[default_target]
lean_lib OpenEvolutions where
  srcDir := "lineages/shared"

lean_lib AnalyticContinuation where
  srcDir := "lineages/analytic-continuation"
  roots := #[`Main]

lean_lib ComputationalBounds where
  srcDir := "lineages/computational-bounds"
  roots := #[`Main]

lean_lib OperatorTheory where
  srcDir := "lineages/operator-theory"
  roots := #[`Main]

require mathlib from git
  "https://github.com/leanprover-community/mathlib4" @ "master"
