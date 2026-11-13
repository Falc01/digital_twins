/-
  Pelourinho Urban Digital Twin — Formal Verification
  Module: EventDamping.lean
  Scientific Backing: John Fruin (1971), Dirk Helbing (Nature 2000), Ulrich Weidmann (1993)
  Document Ref: docs/explanation/dados_sinteticos/02_injecao_eventos.md
-/

namespace Pelourinho.EventDamping

/--
  Função de Amortecimento Logístico Coletivo de Eventos (Doc 02).
  E: volume bruto agregado de pedestres atraídos por eventos no nó j.
  N_max: capacidade nominal máxima do nó j.
  D: fator de tolerância / escala de saturação (D = 1.5 padrão, D = 1.2 no Carnaval).
-/
def collectiveDampingRat (E N_max D : Rat) : Rat :=
  E / (1 + E / (D * N_max))

/--
  Teorema 1: Preservação de Zero.
  Na ausência de eventos (E = 0), o fluxo injetado é estritamente zero.
-/
theorem damping_zero (N_max D : Rat) :
    collectiveDampingRat 0 N_max D = 0 := by
  unfold collectiveDampingRat
  rw [Rat.div_def, Rat.zero_mul]

/--
  Teorema 2: Forma Fatorada Canônica de Produto.
  O amortecimento expressa-se como o produto do fluxo bruto pelo fator de atenuação inverso.
-/
theorem damping_product_form (E N_max D : Rat) :
    collectiveDampingRat E N_max D = E * Rat.inv (1 + E / (D * N_max)) := by
  unfold collectiveDampingRat
  exact Rat.div_def E (1 + E / (D * N_max))

end Pelourinho.EventDamping
