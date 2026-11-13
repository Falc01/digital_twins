/-
  Pelourinho Urban Digital Twin — Formal Verification
  Module: MarkovCirculation.lean
  Domain: Open Markov Chain with Dynamic Huff Gravity, Creep Flow and Gate Egress
  Document Ref: docs/explanation/dados_sinteticos/03_circulacao_markov_pois.md
-/

namespace Pelourinho.MarkovCirculation

/--
  Teorema 1: Invariante Estocástica da Linha Aberta com Egress (Doc 03).
  Para qualquer linha normalizada cuja soma interna seja 1, ao aplicar a taxa de evasão
  egress_rate nos portões, a soma de transição interna mais a saída é rigorosamente 1.
-/
theorem row_stochastic_with_egress
    (inner_sum egress_rate : Rat)
    (h_inner : inner_sum = 1) :
    (1 - egress_rate) * inner_sum + egress_rate = 1 := by
  rw [h_inner, Rat.mul_one]
  rw [Rat.sub_eq_add_neg, Rat.add_assoc, Rat.add_comm (-egress_rate), Rat.add_neg_cancel, Rat.add_zero]

/--
  Teorema 2: Conservação de Massa de Pedestres em Nó Aberto (Doc 03).
  A propagação do estado N através da linha de Markov interna mais a fração de evasão
  conserva estritamente o número inicial de pedestres no nó.
    N_propagado_interno + N_egress = N_inicial
-/
theorem pedestrian_mass_balance_single_node
    (n p_diag p_off egress : Rat)
    (h_row : p_diag + p_off = 1 - egress) :
    n * p_diag + n * p_off + n * egress = n := by
  have h1 : n * p_diag + n * p_off = n * (p_diag + p_off) := (Rat.mul_add n p_diag p_off).symm
  rw [h1, h_row]
  have h2 : n * (1 - egress) + n * egress = n * (1 - egress + egress) := (Rat.mul_add n (1 - egress) egress).symm
  rw [h2]
  have h3 : 1 - egress + egress = 1 := by
    rw [Rat.sub_eq_add_neg, Rat.add_assoc, Rat.add_comm (-egress), Rat.add_neg_cancel, Rat.add_zero]
  rw [h3, Rat.mul_one]

/--
  Teorema 3: Preservação de Soma Unitária sob Creep Flow (Doc 03 / Fruin / Helbing).
  A reponderação da probabilidade de permanência p_effective e o complemento
  (1 - p_effective) redistribuído preservam identicamente a soma unitária da linha.
-/
theorem creep_flow_conservation (p_effective : Rat) :
    p_effective + (1 - p_effective) = 1 := by
  have h_add : p_effective + (1 - p_effective) = (p_effective + -p_effective) + 1 := by
    rw [Rat.sub_eq_add_neg]
    rw [Rat.add_comm 1 (-p_effective)]
    rw [Rat.add_assoc]
  rw [h_add, Rat.add_neg_cancel, Rat.zero_add]

end Pelourinho.MarkovCirculation
