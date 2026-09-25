"""
Interface CLI para Simulação da Circulação de Rede via Cadeias de Markov (Doc 03).

Permite inspecionar a matriz de transição estocástica P(t), atratividades de POIs alpha_j(t)
e simular a redistribuição de pedestres pela malha urbana do Pelourinho.

Uso:
  python cli_markov.py --time 16.5 --matrix
  python cli_markov.py --time 17.0 --steps 3
  python cli_markov.py --time 18.0 --json
"""

import argparse
import json
import os
import sys

# Adiciona backend/ e backend/src ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.simulation.markov_circulation import MarkovCirculationSimulator


def main():
    parser = argparse.ArgumentParser(
        description="Gêmeo Digital IoT Pelourinho — Circulação de Markov & Gravidade de POIs (Doc 03)"
    )
    parser.add_argument(
        "--time",
        type=float,
        default=None,
        help="Horário contínuo em horas (ex: 16.5 para 16h30). Se omitido, usa hora atual.",
    )
    parser.add_argument(
        "--gamma",
        type=float,
        default=1.0,
        help="Fator sazonal multiplicador da época.",
    )
    parser.add_argument(
        "--matrix",
        action="store_true",
        help="Exibe a Matriz Estocástica de Transição P(t) formatada em porcentagens.",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=1,
        help="Número de passos/ciclos sequenciais de propagação de Markov a simular.",
    )
    parser.add_argument(
        "--initial",
        type=str,
        default=None,
        help="Vetor inicial de pedestres N(0) separado por vírgula (ex: '100,80,50,150,90').",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Exporta a saída em formato JSON estruturado.",
    )

    args = parser.parse_args()
    sim = MarkovCirculationSimulator()

    # Parse do vetor inicial opcional
    init_vec = None
    if args.initial:
        try:
            init_vec = [float(x.strip()) for x in args.initial.split(",")]
        except Exception:
            print("Erro ao interpretar vetor inicial. Use formato: 100,50,30,80,40")
            sys.exit(1)

    # Exibição apenas da matriz de transição
    if args.matrix and args.steps <= 1 and not args.json:
        p_mat, alphas = sim.evaluate_transition_matrix(t_hours=args.time)
        print("\n🎲 Matriz Estocástica de Transição de Markov P(t) — Centro Histórico:")
        print("=" * 80)
        time_display = f"{args.time:.2f}h" if args.time is not None else "Hora do Sistema"
        print(f"Horário de Avaliação: {time_display} | Taxa de Decaimento (λ_d): {sim.config.lambda_decay} m⁻¹")
        print("-" * 80)
        header = f"{'Origem \\ Destino':<22} | " + " | ".join(f"{name[:10]:<10}" for name in sim.node_names) + " | Total Linha"
        print(header)
        print("-" * 80)
        for i, name in enumerate(sim.node_names):
            row_vals = " | ".join(f"{p_mat[i, j] * 100:>9.1f}%" for j in range(len(sim.node_names)))
            row_sum = sum(p_mat[i, :])
            print(f"{name[:22]:<22} | {row_vals} | {row_sum * 100:>10.1f}%")
        print("=" * 80)
        print("Campos Atratores de Destino α_j(t):")
        for name, a, p_type in zip(sim.node_names, alphas, sim.poi_types):
            print(f"  • {name:<25} ({p_type:<6}): α = {a:.2f}")
        print()
        return

    # Execução de 1 ou mais passos de propagação
    state = init_vec
    last_res = None
    all_steps = []

    current_t = args.time if args.time is not None else 16.5
    for step in range(1, args.steps + 1):
        step_t = current_t + (step - 1) * (5.0 / 60.0)  # passo temporal padrão de 5 minutos
        res = sim.propagate(
            current_state_N=state,
            t_hours=step_t,
            gamma=args.gamma,
        )
        last_res = res
        state = res.vector_N_propagado
        all_steps.append({
            "step": step,
            "time_hours": round(step_t, 2),
            "state_propagated": res.vector_N_propagado,
        })

    if args.json:
        dump_fn = getattr(last_res, "model_dump", None) or (lambda: last_res.__dict__)
        out_dict = dump_fn()
        if args.steps > 1:
            out_dict["all_steps"] = all_steps
        print(json.dumps(out_dict, indent=2, ensure_ascii=False, default=str))
        return

    # Saída formatada em ASCII
    print("\n🌐 Gêmeo Digital IoT Pelourinho — Circulação de Markov (Doc 03)")
    print("=" * 75)
    print(f" Timestamp ISO             : {last_res.timestamp_iso}")
    print(f" Hora Contínua t           : {last_res.current_time_hours:.2f}h")
    print(f" Total Inicial de Pessoas  : {last_res.total_initial_pedestrians:.1f} pessoas")
    print(f" Total Propagado de Pessoas: {last_res.total_propagated_pedestrians:.1f} pessoas (Erro = {last_res.conservation_error:.6f})")
    print("-" * 75)
    print(" Balanço de Fluxos por Nó Monitorado:")
    print(f"{'Local':<22} | {'Inicial':<9} | {'Ficaram':<9} | {'Entraram':<9} | {'Saíram':<9} | {'Final':<9}")
    print("-" * 75)
    for flow in last_res.node_flows:
        print(
            f"{flow.nome_local[:22]:<22} | "
            f"{flow.initial_pedestrians:>7.1f}p | "
            f"{flow.retained_pedestrians:>7.1f}p | "
            f"{flow.inflow_pedestrians:>7.1f}p | "
            f"{flow.outflow_pedestrians:>7.1f}p | "
            f"{flow.final_propagated_pedestrians:>7.1f}p"
        )
    print("=" * 75)
    print(f" Vetor N_propagado(t+1) para o Barramento: {last_res.vector_N_propagado}\n")


if __name__ == "__main__":
    main()
