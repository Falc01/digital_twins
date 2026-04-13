import os
from qgis.core import QgsProject, QgsRasterLayer, QgsCoordinateReferenceSystem
from qgis.utils import iface


def _add_basemap(basemap_path: str, crs_str: str) -> None:
    if not os.path.exists(basemap_path):
        print(f"[qgis_bridge] Basemap não encontrado: {basemap_path}")
        return
    layer = QgsRasterLayer(basemap_path, "Basemap")
    if not layer.isValid():
        print(f"[qgis_bridge] Basemap inválido: {basemap_path}")
        return
    layer.setCrs(QgsCoordinateReferenceSystem(crs_str))
    QgsProject.instance().addMapLayer(layer)
    print(f"[qgis_bridge] Basemap carregado: {os.path.basename(basemap_path)}")


def setup_project(project_path: str, basemap_path: str, crs_str: str) -> bool:
    project = QgsProject.instance()
    if os.path.exists(project_path):
        if project.fileName() != project_path:
            ok = project.read(project_path)
            if not ok:
                print(f"[qgis_bridge] Falha ao carregar: {project_path}")
                return False
        print(f"[qgis_bridge] Projeto carregado: {os.path.basename(project_path)}")
        return True

    print("[qgis_bridge] Criando novo projeto...")
    os.makedirs(os.path.dirname(project_path), exist_ok=True)
    project.setCrs(QgsCoordinateReferenceSystem(crs_str))
    _add_basemap(basemap_path, crs_str)
    project.setFileName(project_path)
    ok = project.write()
    print(f"[qgis_bridge] Projeto {'criado' if ok else 'ERRO'}: {project_path}")
    return ok
