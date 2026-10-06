"""
Interface CLI para o Subsistema de Saturação de Richards, Ruído Instrumental IoT & Telemetria (Doc 04).

Permite avaliar a saturação não-linear de Richards, a injeção dos três métodos de ruído instrumental
(Uniforme, Gaussiano, Ornstein-Uhlenbeck) e inspecionar os payloads de telemetria IoT.

Uso:
  python cli_saturation.py --time 16.5
  python cli_saturation.py --method GAUSSIAN --time 17.0
  python cli_saturation.py --method OU --step-minutes 5.0 --json
  python cli_saturation.py --input 60 90 130 240 220
"""

import argparse
import json
import os
import sys

# Garante path de importação
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.simulation.sensor_saturation import (
    SensorSaturationSimulator,
    RichardsSaturationConfig,
    SensorNoiseConfig,
    SensorNoiseType,
    SensorSaturationConfig,
)


def main():
    parser = argparse.ArgumentParser(
        description="Gêmeo Digital IoT Pelourinho — Saturação de Richards, Ruído Instrumental & Telemetria (Doc 04)"
    )
    parser.add_argument(
        "--time",
        type=float,
        default=None,
        help="Horário contínuo em horas (ex: 16.5 para 16h30). Se omitido, usa o relógio atual.",
    )
    parser.add_argument(
        "--method",
        type=str,
        default="ORNSTEIN_UHLENBECK",
        choices=["NONE", "UNIFORM", "GAUSSIAN", "ORNSTEIN_UHLENBECK", "OU"],
        help="Método de ruído instrumental (NONE, UNIFORM, GAUSSIAN, ORNSTEIN_UHLENBECK).",
    )
    parser.add_argument(
        "--step-minutes",
        "--dt",
        type=float,
        default=5.0,
        help="Passo temporal Delta t em minutos para a difusão de Ornstein-Uhlenbeck.",
    )
    parser.add_argument(
        "--input",
        type=float,
        nargs="+",
        default=None,
        help="Vetor customizado de fluxo bruto N_bruto(t) por sensor.",
    )
    parser.add_argument(
        "--unanchored",
        action="store_true",
        help="Desativa a ancoragem em zero da curva logística de Richards.",
    )
    parser.add_argument(
        "--persist",
        action="store_true",
        help="Persiste as leituras na tabela telemetria_sensores do GeoPackage / Datalake.",
    )
    parser.add_argument(
        "--day",
        "--full-day",
        action="store_true",
        help="Executa a simulação contínua do dia inteiro (24 horas) exibindo o panorama temporal.",
    )
    parser.add_argument(
        "--step-hours",
        type=float,
        default=2.0,
        help="Intervalo em horas entre amostras ao simular o dia inteiro com --day (padrão: 2.0 h).",
    )
    parser.add_argument(
        "--matrix",
        action="store_true",
        help="Exibe a Matriz Estocástica de Transição de Markov P(t) e os campos atratores.",
    )
    parser.add_argument(
        "--weekday",
        "--day-of-week",
        type=int,
        default=None,
        choices=[0, 1, 2, 3, 4, 5, 6],
        help="Dia da semana para eventos culturais (0=Segunda, 1=Terça, ..., 6=Domingo).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Exibe a saída em formato JSON estrito para integração de scripts.",
    )

    args = parser.parse_args()

    # Monta configuração
    richards_cfg = RichardsSaturationConfig(
        zero_anchored=not args.unanchored,
    )
    noise_cfg = SensorNoiseConfig(
        method=SensorNoiseType(args.method.upper() if args.method.upper() != "OU" else "ORNSTEIN_UHLENBECK"),
    )
    cfg = SensorSaturationConfig(
        richards=richards_cfg,
        noise=noise_cfg,
        step_minutes=args.step_minutes,
    )

    sim = SensorSaturationSimulator(config=cfg)

    # ==========================================================================
    # MODO 1: Panorama Completo de 24 Horas (--day / --full-day)
    # ==========================================================================
    if args.day:
        step_h = max(0.5, args.step_hours)
        hours_timeline = []
        curr = 0.0
        while curr < 24.0:
            hours_timeline.append(curr)
            curr += step_h

        # Garante inclusão dos pontos críticos do Pelourinho (pico 16h30 e shows 20h00)
        for critical_h in (16.5, 20.0):
            if not any(abs(h - critical_h) < 0.25 for h in hours_timeline):
                hours_timeline.append(critical_h)
        hours_timeline = sorted(set(hours_timeline))

        timeline_results = []
        for t in hours_timeline:
            resp = sim.evaluate(
                current_time_hours=t,
                step_minutes=args.step_minutes,
                noise_method=args.method,
                persist_telemetry=args.persist,
                day_of_week=args.weekday,
            )
            timeline_results.append(resp)

        if args.json:
            print(json.dumps([r.model_dump() for r in timeline_results], indent=2))
            return

        print("\n" + "=" * 105)
        print("📡 GÊMEO DIGITAL IOT PELOURINHO — PANORAMA TEMPORAL DE 24 HORAS (DOCS 01 A 04)")
        print("=" * 105)
        print(f"Método de Ruído : {args.method.upper()} | Granularidade Física: {args.step_minutes:.1f} min | Total de Pontos: {len(timeline_results)}")
        print("-" * 105)
        print(f"{'HORÁRIO':<7} | {'LACERDA (150)':<13} | {'PRAÇA SÉ (120)':<14} | {'CARMO (80)':<10} | {'LARGO (250)':<11} | {'TERREIRO (200)':<14} | {'TOTAL':<6} | {'STATUS GERAL'}")
        print("-" * 105)

        for resp in timeline_results:
            t = resp.current_time_hours
            hh = int(t)
            mm = int((t - hh) * 60)
            h_str = f"{hh:02d}h{mm:02d}"

            counts = resp.vector_N_sensor
            total_bairro = sum(counts)
            
            # Identifica status mais severo no instante
            statuses = [s.status for s in resp.sensors]
            if "CRITICO" in statuses:
                stat_general = "CRÍTICO (Superlotação)"
            elif "ATENCAO" in statuses:
                stat_general = "ATENÇÃO (Fluxo Intenso)"
            else:
                stat_general = "NORMAL (Fluxo Livre)"

            c0 = f"{counts[0]:>3d} ({resp.sensors[0].occupancy_pct:>4.0f}%)" if len(counts) > 0 else "-"
            c1 = f"{counts[1]:>3d} ({resp.sensors[1].occupancy_pct:>4.0f}%)" if len(counts) > 1 else "-"
            c2 = f"{counts[2]:>3d} ({resp.sensors[2].occupancy_pct:>4.0f}%)" if len(counts) > 2 else "-"
            c3 = f"{counts[3]:>3d} ({resp.sensors[3].occupancy_pct:>4.0f}%)" if len(counts) > 3 else "-"
            c4 = f"{counts[4]:>3d} ({resp.sensors[4].occupancy_pct:>4.0f}%)" if len(counts) > 4 else "-"

            print(
                f"{h_str:<7} | "
                f"{c0:<13} | "
                f"{c1:<14} | "
                f"{c2:<10} | "
                f"{c3:<11} | "
                f"{c4:<14} | "
                f"{total_bairro:>5d}  | "
                f"{stat_general}"
            )

        print("=" * 105)
        print("💡 Legenda: Contagem inteira emitida do sensor acompanhada da taxa percentual de ocupação (%).")
        print("=" * 105 + "\n")
        return

    # ==========================================================================
    # MODO 2: Instante Específico (--time)
    # ==========================================================================
    response = sim.evaluate(
        N_bruto=args.input,
        current_time_hours=args.time,
        step_minutes=args.step_minutes,
        noise_method=args.method,
        persist_telemetry=args.persist,
        day_of_week=args.weekday,
    )

    if args.json:
        print(response.model_dump_json(indent=2))
        return

    # Apresentação formatada para terminal humano
    t_h = response.current_time_hours
    hh = int(t_h)
    mm = int((t_h - hh) * 60)

    if args.matrix:
        from src.simulation.markov_circulation import MarkovCirculationSimulator
        m_sim = MarkovCirculationSimulator()
        p_mat, alphas = m_sim.evaluate_transition_matrix(t_hours=t_h)
        print("\n🎲 MATRIZ ESTOCÁSTICA DE TRANSIÇÃO DE MARKOV P(t):")
        print("=" * 82)
        print(f"Horário Virtual: {hh:02d}h{mm:02d} ({t_h:.2f} h) | Decaimento Espacial λ_d: {m_sim.config.lambda_decay} m^-1")
        print("-" * 82)
        header = f"{'Origem \\ Destino':<22} | " + " | ".join(f"{name[:10]:<10}" for name in m_sim.node_names) + " | Total"
        print(header)
        print("-" * len(header))
        for i, row in enumerate(p_mat):
            row_str = " | ".join(f"{val*100:>9.1f}%" for val in row)
            print(f"{m_sim.node_names[i][:22]:<22} | {row_str} | {sum(row)*100:>5.1f}%")
        print("=" * len(header))
        print("Atratividades Instantâneas α_j(t):")
        for i, name in enumerate(m_sim.node_names):
            print(f"  • {name:<22}: α = {alphas[i]:.2f}")
        print("-" * len(header))

    print("\n" + "=" * 82)
    print(f"📡 GÊMEO DIGITAL IOT PELOURINHO — TELEMETRIA DE SENSORES (DOC 04)")
    print("=" * 82)
    print(f"Timestamp ISO   : {response.timestamp_iso}")
    print(f"Horário Virtual : {hh:02d}h{mm:02d} ({t_h:.2f} h) | Passo Temporal: {response.step_minutes:.1f} min")
    print(f"Método de Ruído : {response.noise_method} | Persistência Datalake: {response.persisted_rows} linha(s)")
    print("-" * 82)
    print(f"{'SENSOR / POI':<24} | {'BRUTO':<6} | {'SAT':<6} | {'RUÍDO':<6} | {'LEITURA':<7} | {'CAP':<5} | {'OCUP %':<7} | {'STATUS':<7}")
    print("-" * 82)

    for item in response.sensors:
        status_marker = item.status
        if status_marker == "CRITICO":
            status_marker = f"\033[91m{status_marker}\033[0m" if sys.platform != "win32" else status_marker
        elif status_marker == "ATENCAO":
            status_marker = f"\033[93m{status_marker}\033[0m" if sys.platform != "win32" else status_marker

        raw_str = f"{item.raw_input:.1f}" if item.raw_input is not None else "-"
        sat_str = f"{item.saturated_val:.1f}" if item.saturated_val is not None else "-"
        noi_str = f"{item.noise_val:+.2f}" if item.noise_val is not None else "-"

        print(
            f"{item.nome_local[:24]:<24} | "
            f"{raw_str:>6} | "
            f"{sat_str:>6} | "
            f"{noi_str:>6} | "
            f"{item.count:>7} | "
            f"{item.max_capacity:>5} | "
            f"{item.occupancy_pct:>6.1f}% | "
            f"{status_marker}"
        )

    print("=" * 82)
    print(f"Vetor Final N_sensor: {response.vector_N_sensor}")
    print("=" * 82 + "\n")


if __name__ == "__main__":
    main()
