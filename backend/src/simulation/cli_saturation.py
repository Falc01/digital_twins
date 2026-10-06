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

    response = sim.evaluate(
        N_bruto=args.input,
        current_time_hours=args.time,
        step_minutes=args.step_minutes,
        noise_method=args.method,
        persist_telemetry=args.persist,
    )

    if args.json:
        print(response.model_dump_json(indent=2))
        return

    # Apresentação formatada para terminal humano
    t_h = response.current_time_hours
    hh = int(t_h)
    mm = int((t_h - hh) * 60)

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
