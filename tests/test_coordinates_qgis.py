import sys
import os
import struct

# Adiciona o diretório raiz ao path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from table_manager import TableManager
from qgis_bridge.exporter import detect_coordinate_columns

def main():
    data_dir = os.path.join(project_root, 'dados')
    manager = TableManager(data_dir)
    
    if not manager.exists('sensor_readings'):
        print("Erro: Tabela 'sensor_readings' não encontrada.")
        return
        
    table = manager.get('sensor_readings')
    lat_col, lon_col = detect_coordinate_columns(table)
    
    print("=" * 60)
    print("VERIFICAÇÃO DE PASSAGEM DE COORDENADAS PARA O QGIS")
    print("=" * 60)
    print(f"Colunas detectadas pelo pipeline: Lat='{lat_col}', Lon='{lon_col}'\n")
    
    # Bounding Box do TIF extraído no script anterior
    TIF_LAT_MIN = -12.975504
    TIF_LAT_MAX = -12.971626
    TIF_LON_MIN = -38.513750
    TIF_LON_MAX = -38.506777
    
    for row in table:
        try:
            lat = float(row[lat_col])
            lon = float(row[lon_col])
        except (TypeError, ValueError):
            print(f"[{row.id}] ERRO: Coordenadas inválidas.")
            continue
            
        print(f"--- Sensor ID: {row.id} ---")
        print(f"Valores originais (float): Latitude (Y) = {lat}, Longitude (X) = {lon}")
        
        # 1. Checagem de Bounding Box
        lat_in_bounds = TIF_LAT_MIN <= lat <= TIF_LAT_MAX
        lon_in_bounds = TIF_LON_MIN <= lon <= TIF_LON_MAX
        
        if lat_in_bounds and lon_in_bounds:
            print("  [✓] Ponto está DENTRO do Bounding Box do raster.")
        else:
            print("  [x] Ponto está FORA do Bounding Box do raster!")
            if not lat_in_bounds:
                if lat > TIF_LAT_MAX:
                    print(f"      -> Latitude {lat} é mais ao Norte que o topo do mapa ({TIF_LAT_MAX}).")
                else:
                    print(f"      -> Latitude {lat} é mais ao Sul que o fundo do mapa ({TIF_LAT_MIN}).")
            if not lon_in_bounds:
                print("      -> Longitude fora dos limites.")

        # 2. Simulação da passagem para o CSV (QGIS provider 'delimitedtext')
        print(f"  [CSV]  xField={lon_col} (X={lon}), yField={lat_col} (Y={lat})")
        
        # 3. Simulação da passagem para o GeoPackage (QGIS provider 'ogr')
        # WKB Point packing: little-endian (1), PointType (1), X (lon), Y (lat)
        wkb = struct.pack("<bIdd", 1, 1, lon, lat)
        unpacked = struct.unpack("<bIdd", wkb)
        print(f"  [GPKG] Unpack do WKB Binário simulado: Ordem=(X={unpacked[2]}, Y={unpacked[3]})")
        
        if unpacked[2] != lon or unpacked[3] != lat:
            print("  [!] ALERTA: A ordem no binário WKB foi invertida!")
        else:
            print("  [✓] A ordem no WKB está correta (X=Longitude, Y=Latitude).")
        print("")

if __name__ == '__main__':
    main()
