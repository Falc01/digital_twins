"""
qgis_bridge/layer_manager.py
============================
Gerencia camadas vetoriais IoT no QGIS.

Suporta dois formatos de fonte
------------------------------
- GeoJSON  (provider "ogr")       — PREFERIDO: robusto, tipagem nativa
- CSV      (provider "delimitedtext") — fallback, requer lat_col/lon_col

A escolha é automática: se o arquivo .geojson existir, usa GeoJSON;
caso contrário, cai para CSV.

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
        # opção 1: paths explícitos (compatibilidade legada)
        geojson_path: str | None = None,
        csv_path: str | None = None,
        gpkg_path: str | None = None,   # novo — suporte a .gpkg
        # opção 2: data_dir + table_name (novo, para startup_script)
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

        # resolve paths automaticamente se data_dir+table_name fornecidos
        if data_dir and table_name:
            self._geojson_path = os.path.join(data_dir, f"{table_name}.geojson")
            self._csv_path     = os.path.join(data_dir, f"{table_name}.csv")
            self._gpkg_path    = os.path.join(data_dir, f"{table_name}.gpkg")
        else:
            self._geojson_path = geojson_path
            self._csv_path     = csv_path
            self._gpkg_path    = gpkg_path

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
            return self._gpkg_path    # prioridade 1
        if self._geojson_path and os.path.exists(self._geojson_path):
            return self._geojson_path  # prioridade 2
        if self._csv_path and os.path.exists(self._csv_path):
            return self._csv_path      # prioridade 3
        return None

    def _build_geojson_layer(self, path: str) -> QgsVectorLayer | None:
        layer = QgsVectorLayer(path, self._layer_name, "ogr")
        if not layer.isValid():
            print(f"[layer_manager] GeoJSON inválido: {path}")
            return None
        return layer

    def _build_csv_layer(self, path: str) -> QgsVectorLayer | None:
        uri_path = path.replace("\\", "/")
        uri = (
            f"file:///{uri_path}?delimiter=,"
            f"&xField={self._lon_col}&yField={self._lat_col}"
            f"&crs={self._crs_str}&decimalPoint=.&trimFields=yes"
        )
        layer = QgsVectorLayer(uri, self._layer_name, "delimitedtext")
        if not layer.isValid():
            print(f"[layer_manager] CSV inválido. URI: {uri}")
            return None
        return layer

    def _build_gpkg_layer(self, path):
        # o provider do QGIS para .gpkg é "ogr", igual ao GeoJSON
        # mas precisa especificar qual tabela dentro do arquivo
        uri = f"{path}|layername={self._layer_name}"
        layer = QgsVectorLayer(uri, self._layer_name, "ogr")
        if not layer.isValid():
            # fallback sem layername (caso o nome da camada interna seja diferente)
            layer = QgsVectorLayer(path, self._layer_name, "ogr")
        if not layer.isValid():
            print(f"[layer_manager] GeoPackage inválido: {path}")
            return None
        return layer

    def _build_layer(self, data_path):
        ext = os.path.splitext(data_path)[1].lower()
        if ext == ".gpkg":    return self._build_gpkg_layer(data_path)
        if ext == ".geojson": return self._build_geojson_layer(data_path)
        if ext == ".csv":     return self._build_csv_layer(data_path)
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
        src = self._geojson_path or self._csv_path or "?"
        return f"LayerManager('{self._layer_name}', src={os.path.basename(src)!r})"
