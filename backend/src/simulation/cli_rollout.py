"""
Interface de Linha de Comando (CLI) para Simulação Contínua (Rollout 24h) dos Pedestres do Pelourinho.

Modos de Execução:
1. Batch (Lote Direto):
   Calcula e imprime instantaneamente o dia inteiro (24 horas) com balanço consolidado de portões.
   Uso:
     python cli_rollout.py --mode batch --step-minutes 30
     python cli_rollout.py --batch --step-minutes 60

2. Live (Tempo Real / Ticker Streaming):
   Avança o relógio da cidade passo a passo (ex: 30 min simulados a cada 5 segundos reais),
   exibindo as entradas, saídas (egress) e lotação viva em cada rua/praça.
   Uso:
     python cli_rollout.py --mode live --step-minutes 30 --delay 5
     python cli_rollout.py --live --step-minutes 60 --delay 10
"""

import argparse
import json
import os
import sys
import time

# Adiciona backend/ e backend/src ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.simulation.rollout import RolloutSimulationEngine, RolloutStep, RolloutSummary
from src.simulation.schemas import MacroFlowConfig


def render_step_row(step: RolloutStep, max_pop: float = 350.0):
    """Renderiza uma linha tabular detalhada de um ciclo de simulação."""
    bar_len = int((step.total_population / max_pop) * 20) if max_pop > 0 else 0
    bar = "█" * max(1, bar_len)
    
    # Detalhe dos portões
    gates_summary = []
    for g_name, in_val in step.inflow_by_gate.items():
        eg_val = step.egress_by_gate.get(g_name, 0.0)
        short_name = g_name.replace("Elevador Lacerda", "Elevador").replace("Praça da Sé", "Sé").replace("Ladeira do Carmo", "Carmo")
        gates_summary.append(f"{short_name}: +{in_val:.1f}/-{eg_val:.1f}")
    
    gates_str = " | ".join(gates_summary)

    print(
        f"{step.hour_formatted:<7} | "
        f"{step.total_population:>6.1f}p {bar:<20} | "
        f"In: +{step.total_inflow:>4.1f} | "
        f"Out: -{step.total_egress:>4.1f} | "
        f"ΔLíq: {step.net_flux:>+5.1f} | "
        f"{gates_str}"
    )


def print_banner(mode: str, step_min: float, delay: float, regime: str, gamma: float):
    print("\n" + "=" * 115)
    print("🌐 GÊMEO DIGITAL IOT — CENTRO HISTÓRICO DO PELOURINHO (UNIFACS)")
    print("🏙️  SIMULAÇÃO CONTÍNUA DE TRÁFEGO DE PEDESTRES (DOCS 01 + 02 + 03)")
    print("=" * 115)
    print(f" • Modo de Execução : {mode.upper()} ({'Instantâneo' if mode == 'batch' else f'Ticker Live: 1 passo a cada {delay}s reais'})")
    print(f" • Ciclo Simulado   : Passos de {step_min:.0f} minutos (Δt)")
    print(f" • Regime de Entrada: {regime.upper()} (Doc 01 v2.0 - Salvador)")
    print(f" • Sazonalidade (γ) : {gamma:.2f} (1.0 = dia útil, 1.5 = verão, 3.5 = carnaval)")
    print("=" * 115)


def run_batch_cli(engine: RolloutSimulationEngine, args: argparse.Namespace):
    start_t = time.perf_counter()
    summary = engine.run_batch(
        start_hour=args.start_hour,
        end_hour=args.end_hour,
        step_minutes=args.step_minutes,
    )
    elapsed_ms = (time.perf_counter() - start_t) * 1000

    if args.json:
        print(json.dumps(summary.to_dict(), indent=2, ensure_ascii=False))
        return

    print_banner("batch", args.step_minutes, 0.0, args.regime, args.gamma)
    print(f"{'Horário':<7} | {'Lotação Total':<28} | {'Entrada':<10} | {'Saída':<10} | {'Saldo':<8} | Balanço por Portão (+In/-Out)")
    print("-" * 115)

    for step in summary.steps:
        render_step_row(step, max_pop=max(summary.peak_population, 300.0))

    print("=" * 115)
    print("📊 RESUMO CONSOLIDADO DO DIA SIMULADO (24H):")
    print(f" • Tempo de Cálculo Computacional: {elapsed_ms:.2f} ms ({summary.total_steps} ciclos executados)")
    print(f" • Total Acumulado de Ingressos  : +{summary.cumulative_inflow:.1f} pessoas que entraram no Pelourinho")
    print(f" • Total Acumulado de Saídas     : -{summary.cumulative_egress:.1f} pessoas que foram embora da cidade")
    print(f" • Saldo Líquido do Centro       : {summary.net_city_balance:+.1f} pessoas")
    print(f" • Pico Máximo de Lotação        : {summary.peak_population:.1f} pessoas simultâneas às {summary.peak_time_formatted}")
    print(f" • População ao Fechar o Ciclo   : {summary.final_population:.1f} pessoas")
    print("=" * 115 + "\n")


def run_live_cli(engine: RolloutSimulationEngine, args: argparse.Namespace):
    print_banner("live", args.step_minutes, args.delay, args.regime, args.gamma)
    print("🔴 INICIANDO RELÓGIO VIVO DA CIDADE (Pressione Ctrl+C para encerrar)...")
    print(f"{'Horário':<7} | {'Lotação Total':<28} | {'Entrada':<10} | {'Saída':<10} | {'Saldo':<8} | Balanço por Portão (+In/-Out)")
    print("-" * 115)

    try:
        gen = engine.run_live_generator(
            start_hour=args.start_hour,
            end_hour=args.end_hour,
            step_minutes=args.step_minutes,
            delay_seconds=args.delay,
        )
        for step in gen:
            render_step_row(step, max_pop=300.0)
        print("=" * 115)
        print("✅ CICLO DE 24 HORAS CONCLUÍDO COM SUCESSO!\n")
    except KeyboardInterrupt:
        print("\n" + "=" * 115)
        print("🛑 Simulação em tempo real interrompida pelo usuário.")
        print("=" * 115 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Gêmeo Digital IoT Pelourinho — Simulação Contínua / Rollout de Tráfego de Pedestres"
    )
    parser.add_argument(
        "--mode",
        choices=["batch", "live"],
        default="batch",
        help="Modo de execução: 'batch' (calcula o dia inteiro instantaneamente) ou 'live' (entrega passo a passo simulado no tempo real).",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Atalho para --mode batch.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Atalho para --mode live.",
    )
    parser.add_argument(
        "--step-minutes",
        "--dt",
        dest="step_minutes",
        type=float,
        default=30.0,
        help="Duração de cada ciclo simulado em minutos (ex: 30 para meia em meia hora, 60 para hora em hora). Padrão: 30.0 min.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=3.0,
        help="Tempo de espera em segundos na vida real entre cada ciclo no modo live (ex: 5 ou 10). Padrão: 3.0s.",
    )
    parser.add_argument(
        "--regime",
        choices=["trimodal", "unimodal", "fourier"],
        default="trimodal",
        help="Regime do modelo circadiano de entrada (Doc 01 v2.0). Padrão: 'trimodal'.",
    )
    parser.add_argument(
        "--gamma",
        type=float,
        default=1.0,
        help="Fator sazonal multiplicador da época (1.0 = normal, 1.5 = verão, 3.5 = carnaval).",
    )
    parser.add_argument(
        "--start-hour",
        type=float,
        default=6.0,
        help="Hora inicial da simulação contínua (ex: 6.0 para começar às 06h00). Padrão: 6.0.",
    )
    parser.add_argument(
        "--end-hour",
        type=float,
        default=24.0,
        help="Hora final da simulação contínua (ex: 24.0 para fechar à meia-noite). Padrão: 24.0.",
    )
    parser.add_argument(
        "--events",
        action="store_true",
        help="Ativa a injeção dinâmica de eventos culturais (Doc 02) durante o rollout.",
    )
    parser.add_argument(
        "--n-max",
        type=int,
        default=300,
        help="Capacidade máxima de pedestres no Pelourinho (padrão: 300).",
    )
    parser.add_argument(
        "--n-min",
        type=int,
        default=15,
        help="Piso mínimo de pedestres na madrugada (padrão: 15).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Exporta o resultado em formato JSON.",
    )

    args = parser.parse_args()

    # Atalhos de flags
    if args.live:
        args.mode = "live"
    elif args.batch:
        args.mode = "batch"

    macro_cfg = MacroFlowConfig(
        N_max=args.n_max,
        N_min=args.n_min,
        gamma_seasonality=args.gamma,
        regime=args.regime,
    )

    engine = RolloutSimulationEngine(
        macro_config=macro_cfg,
        regime=args.regime,
        gamma=args.gamma,
        enable_events=args.events,
    )

    if args.mode == "batch":
        run_batch_cli(engine, args)
    else:
        run_live_cli(engine, args)


if __name__ == "__main__":
    main()
