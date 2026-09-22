from __future__ import annotations

import logging
import os
import sys

# Configura caminhos
_HERE = os.path.dirname(os.path.abspath(__file__))

logger = logging.getLogger("qgis_bridge.project_generator")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

try:
    from qgis.core import (
        QgsApplication,
        QgsProject,
        QgsVectorLayer,
        QgsRasterLayer,
        QgsCoordinateReferenceSystem,
    )
    HAS_QGIS = True
except ImportError:
    HAS_QGIS = False
    logger.warning(
        "Bindings do QGIS (qgis.core) não encontrados localmente. "
        "O script project_generator.py rodará em modo simulação/stub. "
        "A execução real deve ocorrer dentro do contêiner Docker."
    )


def setup_qgis_server_project(
    project_path: str,
    gpkg_path: str,
    table_name: str,
    basemap_path: str | None = None,
    crs_str: str = "EPSG:4326",
) -> bool:
    """
    Carrega ou cria um projeto .qgz de forma headless, registra a camada do GeoPackage (.gpkg)
    e adiciona o basemap caso necessário.
    """
    if not HAS_QGIS:
        logger.info(
            "[SIMULAÇÃO] Registrando no projeto '%s' a camada do GeoPackage '%s' | Tabela: '%s'",
            os.path.basename(project_path),
            os.path.basename(gpkg_path),
            table_name,
        )
        return True

    # Inicializa o ambiente do QGIS de forma Headless (GUI desativada)
    qgs = QgsApplication([], False)
    qgs.initQgis()

    try:
        project = QgsProject.instance()

        if os.path.exists(project_path):
            ok = project.read(project_path)
            if not ok:
                logger.error("Falha ao ler o projeto QGIS existente em: %s", project_path)
                return False
            logger.info("Projeto QGIS carregado com sucesso: %s", project_path)
        else:
            logger.info("Criando novo projeto QGIS em: %s", project_path)
            project.setCrs(QgsCoordinateReferenceSystem(crs_str))
            project.setFileName(project_path)

        # ── 1. Adição do Basemap ─────────────────────────────────────────────
        if basemap_path and os.path.exists(basemap_path):
            basemap_layers = project.mapLayersByName("Basemap")
            if not basemap_layers:
                raster_layer = QgsRasterLayer(basemap_path, "Basemap")
                if raster_layer.isValid():
                    raster_layer.setCrs(QgsCoordinateReferenceSystem(crs_str))
                    project.addMapLayer(raster_layer)
                    logger.info("Camada raster de Basemap carregada com sucesso.")
                else:
                    logger.warning("Basemap fornecido em %s é inválido.", basemap_path)
            else:
                logger.info("Basemap já registrado no projeto.")

        # ── 2. Registro da Camada do GeoPackage ──────────────────────────────
        uri = f"{gpkg_path}|layername={table_name}"

        # Remove camadas anteriores com o mesmo nome para forçar o recarregamento do schema
        for layer in project.mapLayersByName(table_name):
            project.removeMapLayer(layer.id())

        vector_layer = QgsVectorLayer(uri, table_name, "ogr")
        if vector_layer.isValid():
            vector_layer.setCrs(QgsCoordinateReferenceSystem(crs_str))
            project.addMapLayer(vector_layer)
            logger.info("Camada do GeoPackage '%s' adicionada/recarregada.", table_name)
        else:
            logger.error("Falha ao criar camada vetorial do GeoPackage com a URI: %s", uri)
            return False

        # Salva o projeto (.qgz)
        ok = project.write()
        logger.info("Projeto QGIS gravado no disco: %s", "Sucesso" if ok else "ERRO")
        return ok

    except Exception as e:
        logger.error("Erro inesperado no pipeline de geração do projeto: %s", e)
        return False

    finally:
        qgs.exitQgis()


if __name__ == "__main__":
    # Permite execução direta via linha de comando para automação em lote no contêiner
    import argparse

    parser = argparse.ArgumentParser(description="Gerador Headless de Projetos QGIS Server")
    parser.add_argument("--project", required=True, help="Caminho do arquivo de projeto (.qgz)")
    parser.add_argument("--gpkg", required=True, help="Caminho do arquivo GeoPackage (.gpkg)")
    parser.add_argument("--table", required=True, help="Nome da tabela espacial no GeoPackage")
    parser.add_argument("--basemap", help="Caminho opcional do arquivo GeoTIFF de basemap")
    parser.add_argument("--crs", default="EPSG:4326", help="CRS padrão (ex: EPSG:4326)")

    args = parser.parse_args()

    success = setup_qgis_server_project(
        project_path=args.project,
        gpkg_path=args.gpkg,
        table_name=args.table,
        basemap_path=args.basemap,
        crs_str=args.crs,
    )
    sys.exit(0 if success else 1)
