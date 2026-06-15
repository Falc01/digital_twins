import sys
import os
from table_manager import TableManager
from qgis_bridge.exporter import detect_coordinate_columns
from qgis_bridge.middleware import normalize_keys

def check_sensors():
    data_dir = os.path.join(os.path.dirname(__file__), 'dados')
    manager = TableManager(data_dir)
    
    if not manager.exists('sensor_readings'):
        print("Tabela 'sensor_readings' não encontrada.")
        return
        
    table = manager.get('sensor_readings')
    lat_col, lon_col = detect_coordinate_columns(table)
    print(f"Total de linhas: {table.row_count}")
    print(f"Colunas originais: {table.column_names}")
    print(f"Colunas de coordenadas detectadas: lat={lat_col}, lon={lon_col}")
    print("-" * 50)
    
    issues_found = 0
    for row in table:
        raw_dict = {col: row[col] for col in table.column_names}
        norm_dict = normalize_keys(raw_dict)
        
        # Try finding device ID or similar
        device_id = norm_dict.get('device_id', 'Desconhecido')
        
        lat = row[lat_col] if lat_col else norm_dict.get('latitude')
        lon = row[lon_col] if lon_col else norm_dict.get('longitude')
        
        if lat is None or lon is None or lat == '' or lon == '':
            print(f"AVISO: Linha ID={row.id} possui coordenadas faltantes!")
            print(f"  -> Dispositivo (device_id): {device_id}")
            print(f"  -> lat_lida: {lat}, lon_lida: {lon}")
            print(f"  -> Dados brutos da linha: {raw_dict}")
            issues_found += 1
            
    if issues_found == 0:
        print("Tudo certo! Todas as linhas possuem latitude e longitude.")
    else:
        print(f"\nEncontrados {issues_found} registros com problemas de coordenadas.")

if __name__ == '__main__':
    check_sensors()
