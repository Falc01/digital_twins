"""
exemplo_iot.py
==============
Demonstração da API Pythônica do DynTable.
Compare com a versão C-style para ver as diferenças.
"""
import time
from dyntable import DynTable, DynType


def main():

    # ── 1. Cria tabela ──────────────────────────────────────────
    readings = DynTable("sensor_readings")

    # ── 2. Colunas que já conhecemos ────────────────────────────
    readings.add_column("device_id", DynType.STRING, nullable=False)
    readings.add_column("timestamp", DynType.TIMESTAMP)

    # ── 3. Sensor de temperatura — coluna nova em runtime! ───────
    r1 = readings.new_row(device_id="sensor-T01", timestamp=time.time())

    readings.add_column("temperature_c")   # tipo AUTO — será inferido
    r1["temperature_c"] = 23.7             # infere FLOAT, trava a coluna

    # ── 4. Sensor de pressão ────────────────────────────────────
    readings.add_column("pressure_hpa", DynType.FLOAT)
    r2 = readings.new_row(
        device_id="sensor-P01",
        timestamp=time.time(),
        pressure_hpa=1013.25
    )

    # ── 5. Sensor misto ─────────────────────────────────────────
    r3 = readings.new_row(
        device_id="sensor-TP01",
        timestamp=time.time(),
        temperature_c=21.3,
        pressure_hpa=1011.50
    )

    # ── 6. Umidade e bool ───────────────────────────────────────
    readings.add_column("humidity_pct", DynType.FLOAT)
    readings.add_column("door_open", DynType.BOOL)

    readings.new_row(device_id="sensor-H01", timestamp=time.time(), humidity_pct=68.2)
    readings.new_row(device_id="sensor-D01", timestamp=time.time(), door_open=True)

    # ── 7. Acesso direto ────────────────────────────────────────
    print(f"Temp sensor-TP01: {readings[r3.id]['temperature_c']} °C")

    # Ou pelo método get:
    print(f"Pressão P01:      {readings.get(r2.id, 'pressure_hpa')} hPa\n")

    # ── 8. Tabela formatada ─────────────────────────────────────
    print(readings)

    # ── 9. Iteração Pythônica ───────────────────────────────────
    print("Sensores com temperatura registrada:")
    for row in readings:
        temp = row["temperature_c"]
        if temp is not None:
            print(f"  {row['device_id']:15} → {temp:.1f} °C")

    # ── 10. Filtro ──────────────────────────────────────────────
    print("\nSensores com temperatura > 22 °C:")
    quentes = readings.filter(
        temperature_c=lambda v: v is not None and v > 22
    )
    for row in quentes:
        print(f"  {row['device_id']}: {row['temperature_c']} °C")

    # ── 11. Estatísticas ────────────────────────────────────────
    stats = readings.column_stats("temperature_c")
    print(f"\nEstatísticas de temperature_c: {stats}")

    # ── 12. Encadeamento de operações ───────────────────────────
    (readings
        .add_column("signal_db", DynType.INT)
        .rename_column("door_open", "porta_aberta")
        .remove_column("signal_db"))

    # ── 13. CSV ─────────────────────────────────────────────────
    readings.export_csv("iot_readings.csv")
    print("\nCSV exportado.")

    # ── 14. to_dicts() → integração com pandas ──────────────────
    dicts = readings.to_dicts()
    print(f"\nPrimeiro registro como dict:")
    print(dicts[0])

    # ── 15. Nenhum destroy() necessário ─────────────────────────
    # GC cuida de tudo quando `readings` sai de escopo.


if __name__ == "__main__":
    main()
