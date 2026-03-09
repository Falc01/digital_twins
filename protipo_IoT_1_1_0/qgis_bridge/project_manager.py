"""
qgis_bridge/project_manager.py
===============================
Gerencia o arquivo de projeto QGIS (.qgz).

Responsabilidades:
  - Criar o projeto na primeira execução (se .qgz não existir)
  - Carregar o projeto em execuções seguintes
  - Adicionar o basemap como camada raster na criação

IMPORTANTE: Este módulo roda DENTRO do Python do QGIS.
Não importe ele no ambiente Streamlit/Python normal.

Uso pelo startup_script.py:
    from qgis_bridge.project_manager import setup_project
    setup_project()
"""

import os
import sys

from qgis.core import (
    QgsProject,
    QgsRasterLayer,
    QgsCoordinateReferenceSystem,
)
from qgis.utils import iface


def _add_basemap(basemap_path: str, crs_str: str) -> None:
    """
    Adiciona a imagem local como camada raster de base.
    Chamado apenas na criação do projeto — não duplica na recarga.
    """
    if not os.path.exists(basemap_path):
        print(f"[qgis_bridge] Basemap não encontrado: {basemap_path}")
        print("[qgis_bridge] O projeto será criado sem basemap.")
        print("[qgis_bridge] Coloque o arquivo em dados/basemap.tif e recrie o projeto.")
        return

    layer = QgsRasterLayer(basemap_path, "Basemap")

    if not layer.isValid():
        print(f"[qgis_bridge] Basemap inválido: {basemap_path}")
        return

    # Define o CRS da camada
    crs = QgsCoordinateReferenceSystem(crs_str)
    layer.setCrs(crs)

    QgsProject.instance().addMapLayer(layer)
    print(f"[qgis_bridge] Basemap carregado: {os.path.basename(basemap_path)}")


def setup_project(project_path: str, basemap_path: str, crs_str: str) -> bool:
    """
    Cria o projeto .qgz se não existir, ou carrega se já existir.

    Parâmetros:
        project_path  → caminho completo do .qgz
        basemap_path  → caminho da imagem local de base
        crs_str       → CRS do projeto (ex: "EPSG:4326")

    Retorna True se o projeto estava carregado/criado com sucesso.

    Lógica:
        .qgz existe  → QGIS já o abriu via --project, apenas confirma
        .qgz não existe → cria pasta, define CRS, adiciona basemap, salva
    """
    project = QgsProject.instance()

    if os.path.exists(project_path):
        # O QGIS pode ter aberto o projeto via --project já.
        # Se não, carrega agora.
        if project.fileName() != project_path:
            ok = project.read(project_path)
            if not ok:
                print(f"[qgis_bridge] Falha ao carregar projeto: {project_path}")
                return False
        print(f"[qgis_bridge] Projeto carregado: {os.path.basename(project_path)}")
        return True

    # ── Primeira execução: cria o projeto ───────────────────
    print("[qgis_bridge] Projeto não encontrado. Criando novo...")

    # Garante que a pasta existe
    os.makedirs(os.path.dirname(project_path), exist_ok=True)

    # Define CRS do projeto
    crs = QgsCoordinateReferenceSystem(crs_str)
    project.setCrs(crs)

    # Adiciona basemap
    _add_basemap(basemap_path, crs_str)

    # Salva o projeto
    project.setFileName(project_path)
    ok = project.write()

    if ok:
        print(f"[qgis_bridge] Projeto criado e salvo: {project_path}")
    else:
        print(f"[qgis_bridge] Erro ao salvar projeto: {project_path}")

    return ok
