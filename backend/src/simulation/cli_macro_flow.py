"""
Interface CLI para Simulação do Macro-Fluxo de Pedestres do Pelourinho (Doc 01).

Permite avaliar e visualizar rapidamente o volume urbano basal e alocação por portão.

Uso:
  python cli_macro_flow.py --time 16.5 --gamma 1.0
  python cli_macro_flow.py --curve --step 0.5
"""

import argparse
import json
import sys
import os

# Adiciona backend/ ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.simulation.macro_flow import MacroFlowSimulator


def main():
    parser = argparse.ArgumentParser(
        description="Gêmeo Digital IoT Pelourinho — Avaliador de Macro-Fluxo Circadiano (Doc 01)"
    )
    parser.add_argument(
        "--time",
        type=float,
        default=None,
        help="Horário contínuo em horas (ex: 16.5 para 16h30). Se omitido, usa o horário atual do sistema.",
    )
    parser.add_argument(
        "--gamma",
        type=float,
        default=1.0,
        help="Fator sazonal multiplicador (1.0 = dia útil, 1.5 = alta estação/verão, 3.5 = carnaval).",
    )
    parser.add_argument(
        "--curve",
        action="store_true",
        help="Exibe a série temporal completa de 24 horas no terminal.",
    )
    parser.add_argument(
        "--step",
        type=float,
        default=1.0,
        help="Passo em horas para a curva (padrão: 1.0 hora).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Exporta a saída em formato JSON estruturado.",
    )

    args = parser.parse_args()
    sim = MacroFlowSimulator()

    if args.curve:
        curve = sim.generate_24h_curve(step_hours=args.step, gamma=args.gamma)
        if args.json:
            print(json.dumps(curve, indent=2, ensure_ascii=False))
        else:
            print(f"\n📈 Curva Circadiana de 24 Horas do Pelourinho (Gamma = {args.gamma}):")
            print("=" * 60)
            print(f"{'Horário':<10} | {'Hora (dec)':<12} | {'Volume Total (Pedestres)':<25}")
            print("-" * 60)
            for pt in curve:
                bar = "█" * int(pt["total_bairro_volume"] / 10)
                print(f"{pt['hour_formatted']:<10} | {pt['hour']:<12.2f} | {pt['total_bairro_volume']:>6.1f}  {bar}")
            print("=" * 60)
        return

    result = sim.evaluate(t_hours=args.time, gamma=args.gamma)

    if args.json:
        data = result.to_response()
        dump_fn = getattr(data, "model_dump", None) or (lambda: data.__dict__)
        print(json.dumps(dump_fn(), indent=2, ensure_ascii=False, default=str))
    else:
        print("\n🌐 Gêmeo Digital IoT Pelourinho — Simulação de Macro-Fluxo (Doc 01)")
        print("=" * 65)
        print(f" Timestamp ISO        : {result.timestamp_iso}")
        print(f" Hora Contínua t      : {result.t_hours:.2f}h")
        print(f" Hora Circadiana h(t) : {result.circadian_h:.2f}h")
        print(f" Fator Sazonal (γ)    : {result.gamma:.2f}")
        print(f" Volume Total Bairro  : {result.N_bairro:.2f} indivíduos")
        print("-" * 65)
        print(" Alocação nos Portões de Entrada (w_j):")
        for alloc in result.allocations:
            pct = alloc.gate_weight * 100
            print(f"  • {alloc.nome_local:<30} ({pct:>5.1f}%): {alloc.count_pedestrians:>6.1f} pessoas")
        print("=" * 65)
        print(f" Vetor N_rotina(t) para o Barramento : {result.vector_N_rotina}\n")


if __name__ == "__main__":
    main()
