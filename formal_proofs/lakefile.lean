import Lake
open Lake DSL

package "formal_proofs" where
  version := v!"0.1.0"
  keywords := #["math", "urban-mobility", "markov", "pedestrian-simulation"]

@[default_target]
lean_lib «PelourinhoProofs» where
  -- Library configuration
