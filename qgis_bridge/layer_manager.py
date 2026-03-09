"""
qgis_bridge/layer_manager.py
=============================
Gerencia a camada de pontos IoT dentro do QGIS.

Responsabilidades:
  - Criar a camada CSV como pontos na primeira vez
  - Recarregar a camada quando o CSV mudar
  - Preservar o zoom e a posição do mapa a cada recarga

IMPORTANTE: Este módulo roda DENTRO do Python do QGIS.
Não importe ele no ambiente Streamlit/Python normal.

Uso pelo startup_script.py:
    from qgis_bridge.layer_manager import LayerManager
    lm = LayerManager(csv_path, lat_col, lon_col, crs_str, layer_name)
    lm.reload()   # chamado pelo watcher a cada mudança
"""

import os

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsCoordinateReferenceSystem,
)
from qgis.utils import iface


class LayerManager:
    """
    Mantém a camada de pontos IoT sincronizada com o CSV.

    A cada reload():
      1. Salva a extensão atual do mapa (zoom + posição)
      2. Remove a camada antiga (se existir)
      3. Cria nova camada a partir do CSV atualizado
      4. Restaura a extensão salva
      5. Salva o projeto .qgz
    """

    def __init__(
        self,
        csv_path:    str,
        lat_col:     str,
        lon_col:     str,
        crs_str:     str,
        layer_name:  str,
        project_path: str,
    ):
        self._csv_path    = csv_path
        self._lat_col     = lat_col
        self._lon_col     = lon_col
        self._crs_str     = crs_str
        self._layer_name  = layer_name
        self._project_path = project_path

    # ─────────────────────────────────────────────────────────
    #  API pública
    # ─────────────────────────────────────────────────────────

    def reload(self) -> None:
        """
        Recarrega a camada a partir do CSV atual.
        Chamado pelo watcher a cada mudança detectada.
        """
        if not os.path.exists(self._csv_path):
            print(f"[qgis_bridge] CSV não encontrado: {self._csv_path}")
            return

        canvas = iface.mapCanvas()

        # ── 1. Preserva zoom e posição ───────────────────────
        saved_extent = canvas.extent()
        has_extent   = not saved_extent.isEmpty()

        # ── 2. Remove a camada antiga ────────────────────────
        self._remove_existing_layer()

        # ── 3. Cria nova camada ──────────────────────────────
        layer = self._build_layer()
        if layer is None:
            return

        QgsProject.instance().addMapLayer(layer)
        print(f"[qgis_bridge] Camada '{self._layer_name}' recarregada "
              f"({layer.featureCount()} pontos)")

        # ── 4. Restaura zoom e posição ───────────────────────
        if has_extent:
            canvas.setExtent(saved_extent)
        else:
            # Primeira carga: zoom automático para os dados
            canvas.zoomToFullExtent()

        canvas.refresh()

        # ── 5. Salva o projeto ───────────────────────────────
        self._save_project()

    # ─────────────────────────────────────────────────────────
    #  Helpers internos
    # ─────────────────────────────────────────────────────────

    def _build_layer(self) -> QgsVectorLayer | None:
        """
        Constrói a URI do provider delimitedtext e cria a camada.

        Formato da URI do QGIS para CSV com coordenadas:
            file:///caminho/arquivo.csv?delimiter=,&xField=lon&yField=lat&crs=EPSG:4326
        """
        # Normaliza para URI com barras normais (obrigatório no QGIS)
        uri_path = self._csv_path.replace("\\", "/")

        uri = (
            f"file:///{uri_path}"
            f"?delimiter=,"
            f"&xField={self._lon_col}"
            f"&yField={self._lat_col}"
            f"&crs={self._crs_str}"
            f"&decimalPoint=."      # força ponto como separador decimal
            f"&trimFields=yes"      # ignora espaços em branco nos valores
        )

        layer = QgsVectorLayer(uri, self._layer_name, "delimitedtext")

        if not layer.isValid():
            print(f"[qgis_bridge] Camada inválida. Verifique se o CSV tem as "
                  f"colunas '{self._lat_col}' e '{self._lon_col}'.")
            print(f"[qgis_bridge] URI usada: {uri}")
            return None

        return layer

    def _remove_existing_layer(self) -> None:
        """Remove a camada IoT anterior pelo nome, se existir."""
        project = QgsProject.instance()
        layers  = project.mapLayersByName(self._layer_name)
        for layer in layers:
            project.removeMapLayer(layer.id())

    def _save_project(self) -> None:
        """Salva o projeto .qgz para persistir o estado das camadas."""
        project = QgsProject.instance()
        if project.fileName():
            project.write()
