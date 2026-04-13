import time
from dyntable import DynTable, DynType


def main():
    readings = DynTable("sensor_readings")

    readings.add_column("device_id",  DynType.STRING, nullable=False)
    readings.add_column("timestamp",  DynType.TIMESTAMP)
    readings.add_column("temperature_c")
    readings.add_column("pressure_hpa", DynType.FLOAT)
    readings.add_column("humidity_pct", DynType.FLOAT)
    readings.add_column("porta_aberta", DynType.BOOL)

    r1 = readings.new_row(device_id="sensor-T01", timestamp=time.time())
    r1["temperature_c"] = 23.7

    r2 = readings.new_row(device_id="sensor-P01", timestamp=time.time(), pressure_hpa=1013.25)
    r3 = readings.new_row(device_id="sensor-TP01", timestamp=time.time(),
                          temperature_c=21.3, pressure_hpa=1011.50)
    readings.new_row(device_id="sensor-H01", timestamp=time.time(), humidity_pct=68.2)
    readings.new_row(device_id="sensor-D01", timestamp=time.time(), porta_aberta=True)

    print(f"Temp TP01:    {readings[r3.id]['temperature_c']} °C")
    print(f"Pressão P01:  {readings.get(r2.id, 'pressure_hpa')} hPa\n")

    print(readings)

    print(f"Matriz: {readings._store.row_count}×{readings._store.col_count}\n")

    quentes = readings.filter(temperature_c=lambda v: v is not None and v > 22)
    print("Sensores > 22 °C:")
    for row in quentes:
        print(f"  {row['device_id']}: {row['temperature_c']} °C")

    print(f"\nStats temperature_c: {readings.column_stats('temperature_c')}")

    readings.save("dados")
    print("\n✅ Salvo em dados/sensor_readings.dyndb (sem JSON, sem CSV separado)")

    t2 = DynTable.load("dados", "sensor_readings")
    print(f"Recarregado: {t2}")


if __name__ == "__main__":
    main()
