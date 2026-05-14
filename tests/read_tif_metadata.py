import sys
import os

# Adiciona o diretório bin do QGIS ao PATH para encontrar as DLLs do GDAL
qgis_bin = r"C:\Program Files\QGIS 3.44.4\bin"
if os.path.exists(qgis_bin):
    os.environ['PATH'] = qgis_bin + os.pathsep + os.environ['PATH']

from osgeo import gdal, osr

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tif_path = os.path.join(project_root, 'dados', 'pelourinho_recortado.tif')
    
    if not os.path.exists(tif_path):
        print(f"Arquivo não encontrado: {tif_path}")
        return
        
    # Suprime os avisos do GDAL
    gdal.UseExceptions()
    
    try:
        # Abre o arquivo com GDAL
        dataset = gdal.Open(tif_path)
        if not dataset:
            print("Falha ao abrir o TIF com GDAL.")
            return
            
        # Obtém o CRS
        proj_wkt = dataset.GetProjection()
        srs = osr.SpatialReference()
        srs.ImportFromWkt(proj_wkt)
        
        # Tenta obter o código EPSG
        srs.AutoIdentifyEPSG()
        epsg_code = srs.GetAuthorityCode(None)
        crs_name = f"EPSG:{epsg_code}" if epsg_code else "Desconhecido"
        
        # Obtém as coordenadas originais do Bounding Box
        gt = dataset.GetGeoTransform()
        width = dataset.RasterXSize
        height = dataset.RasterYSize
        
        min_x = gt[0]
        max_y = gt[3]
        max_x = min_x + width * gt[1] + height * gt[2]
        min_y = max_y + width * gt[4] + height * gt[5]
        
        # Prepara a transformação para Lat/Lon (EPSG:4326) para mostrar no terminal
        target_srs = osr.SpatialReference()
        target_srs.ImportFromEPSG(4326)
        
        # Garante a ordem correta dos eixos (Lon, Lat) para o GDAL 3.x
        if hasattr(target_srs, 'SetAxisMappingStrategy'):
            target_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        if hasattr(srs, 'SetAxisMappingStrategy'):
            srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
            
        transform = osr.CoordinateTransformation(srs, target_srs)
        
        # Transforma os cantos
        lon_min, lat_min, _ = transform.TransformPoint(min_x, min_y)
        lon_max, lat_max, _ = transform.TransformPoint(max_x, max_y)
        
        # Garante a extração do valor mínimo e máximo absolutos
        final_lat_min = min(lat_min, lat_max)
        final_lat_max = max(lat_min, lat_max)
        final_lon_min = min(lon_min, lon_max)
        final_lon_max = max(lon_min, lon_max)
        
        print("=" * 60)
        print("METADADOS DO ARQUIVO TIF (pelourinho_recortado.tif)")
        print("=" * 60)
        print(f"Caminho:   {tif_path}")
        print(f"Dimensões: {width} x {height} pixels")
        print(f"CRS (Ref): {crs_name}")
        print("-" * 60)
        print("Bounding Box (Lat/Lon - WGS84):")
        print(f"  -> Latitude Mínima:  {final_lat_min:.6f}")
        print(f"  -> Latitude Máxima:  {final_lat_max:.6f}")
        print(f"  -> Longitude Mínima: {final_lon_min:.6f}")
        print(f"  -> Longitude Máxima: {final_lon_max:.6f}")
        print("=" * 60)
        
    except Exception as e:
        print(f"Erro ao processar o arquivo TIF: {e}")

if __name__ == '__main__':
    main()
