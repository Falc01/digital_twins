"""
qgis_bridge/layer_manager.py
============================
Gerencia camadas vetoriais IoT no QGIS.

Suporta apenas o formato GeoPackage (provider "ogr").

Uso
---
Instancie LayerManager para cada tabela/camada que quiser manter no QGIS.
Chame reload() sempre que os dados mudarem (normalmente via DyndbWatcher).
"""

from __future__ import annotations

import os
from qgis.core import QgsProject, QgsVectorLayer, QgsCoordinateReferenceSystem
from qgis.utils import iface


class LayerManager:
    def __init__(
        self,
        layer_name: str,
        project_path: str,
        gpkg_path: str | None = None,
        data_dir: str | None = None,
        table_name: str | None = None,
        lat_col: str = "latitude",
        lon_col: str = "longitude",
        crs_str: str = "EPSG:4326",
    ) -> None:
        self._layer_name   = layer_name
        self._project_path = project_path
        self._lat_col      = lat_col
        self._lon_col      = lon_col
        self._crs_str      = crs_str

        if data_dir and table_name:
            self._gpkg_path = os.path.join(data_dir, f"{table_name}.gpkg")
        else:
            self._gpkg_path = gpkg_path

    # ─────────────────────────────────────────
    #  API pública
    # ─────────────────────────────────────────

    def reload(self) -> None:
        """
        Remove a camada atual e carrega a versão atualizada.
        Preserva extent (zoom) do canvas se já estava definido.
        """
        data_path = self._pick_data_source()
        if data_path is None:
            print(
                f"[layer_manager] Nenhum dado disponível para '{self._layer_name}'. "
                "Execute uma exportação primeiro."
            )
            return

        canvas       = iface.mapCanvas()
        saved_extent = canvas.extent()
        has_extent   = not saved_extent.isEmpty()

        self._remove_existing_layer()

        layer = self._build_layer(data_path)
        if layer is None:
            return

        QgsProject.instance().addMapLayer(layer)
        print(
            f"[layer_manager] '{self._layer_name}' recarregada "
            f"({layer.featureCount()} feature(s)) "
            f"[{os.path.basename(data_path)}]"
        )

        if has_extent:
            canvas.setExtent(saved_extent)
        else:
            canvas.zoomToFullExtent()

        canvas.refresh()
        self._save_project()

    def get_layer(self) -> QgsVectorLayer | None:
        """Retorna a camada ativa no projeto, ou None se não existir."""
        layers = QgsProject.instance().mapLayersByName(self._layer_name)
        return layers[0] if layers else None

    def feature_count(self) -> int:
        """Retorna o número de features na camada ativa (0 se não existir)."""
        layer = self.get_layer()
        return layer.featureCount() if layer else 0
    
    def load_if_missing(self) -> None:
        if self.get_layer() is None:
            print(f"[layer_manager] '{self._layer_name}' ausente, carregando...")
            self.reload()
        else:
            print(f"[layer_manager] '{self._layer_name}' já presente no projeto, mantendo.")

    # ─────────────────────────────────────────
    #  Internos
    # ─────────────────────────────────────────
    
    def _pick_data_source(self):
        if self._gpkg_path and os.path.exists(self._gpkg_path):
            return self._gpkg_path
        return None

    def _build_gpkg_layer(self, path):
        uri = f"{path}|layername={self._layer_name}"
        layer = QgsVectorLayer(uri, self._layer_name, "ogr")
        if not layer.isValid():
            layer = QgsVectorLayer(path, self._layer_name, "ogr")
        if not layer.isValid():
            print(f"[layer_manager] GeoPackage inválido: {path}")
            return None
            
        # Atribuir explicitamente o CRS à camada
        crs = QgsCoordinateReferenceSystem(self._crs_str)
        layer.setCrs(crs)
        
        return layer

    def _build_layer(self, data_path):
        ext = os.path.splitext(data_path)[1].lower()
        if ext == ".gpkg":    return self._build_gpkg_layer(data_path)
        print(f"[layer_manager] Formato não suportado: {ext}")
        return None

    def _remove_existing_layer(self) -> None:
        project = QgsProject.instance()
        for layer in project.mapLayersByName(self._layer_name):
            project.removeMapLayer(layer.id())

    def _save_project(self) -> None:
        project = QgsProject.instance()
        if project.fileName():
            project.write()

    def __repr__(self) -> str:
        return f"LayerManager('{self._layer_name}', src={os.path.basename(self._gpkg_path or '?')!r})"
