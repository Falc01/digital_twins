/-
  Pelourinho Urban Digital Twin — Formal Verification
  Module: MacroFlow.lean
  Domain: Circadian Macro-Flow, Multi-modal Peaks, Gate Partition and Climate Multiplier
  Document Ref: docs/explanation/dados_sinteticos/01_modulo_de_entrada.md
-/

namespace Pelourinho.MacroFlow

/--
  Teorema 1: Conservação Estrita da Partição de Influxo por Portão (Doc 01).
  Dado o influxo diferencial ΔN ≥ 0 e pesos de portão normalizados ∑ w_g = 1:
    ∑ Φ_in,g = ΔN
-/
theorem gate_influx_partition_conserved
    (delta_N w1 w2 w3 : Rat)
    (h_weights : w1 + w2 + w3 = 1) :
    (w1 * delta_N) + (w2 * delta_N) + (w3 * delta_N) = delta_N := by
  have h1 : w1 * delta_N + w2 * delta_N = (w1 + w2) * delta_N := (Rat.add_mul w1 w2 delta_N).symm
  rw [h1]
  have h2 : (w1 + w2) * delta_N + w3 * delta_N = (w1 + w2 + w3) * delta_N := (Rat.add_mul (w1 + w2) w3 delta_N).symm
  rw [h2, h_weights, Rat.one_mul]

/--
  Teorema 2: Decomposição Associativa do Multiplicador Sazonal Efetivo (Doc 01-B).
  A ordem de agregação de estações climáticas, intempéries e ajuste manual do gestor
  é rigorosamente associativa sobre o corpo dos racionais:
    γ_efetivo = (γ_manual * γ_estação) * ω_clima = γ_manual * (γ_estação * ω_clima)
-/
theorem effective_gamma_associative
    (gamma_manual gamma_season omega_weather : Rat) :
    (gamma_manual * gamma_season) * omega_weather = gamma_manual * (gamma_season * omega_weather) := by
  exact Rat.mul_assoc gamma_manual gamma_season omega_weather

/--
  Teorema 3: Preservação de Escala Linear sob Neutralidade Climática.
  Sob condições basais (γ_estação = 1, ω_clima = 1), o multiplicador efetivo
  coincide exatamente com o controle manual do gestor.
-/
theorem effective_gamma_neutral
    (gamma_manual : Rat) :
    (gamma_manual * 1) * 1 = gamma_manual := by
  rw [Rat.mul_one, Rat.mul_one]

end Pelourinho.MacroFlow
