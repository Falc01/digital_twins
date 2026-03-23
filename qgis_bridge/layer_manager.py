import os
from qgis.core import QgsProject, QgsVectorLayer, QgsCoordinateReferenceSystem
from qgis.utils import iface


class LayerManager:
    def __init__(self, csv_path, lat_col, lon_col, crs_str, layer_name, project_path):
        self._csv_path     = csv_path
        self._lat_col      = lat_col
        self._lon_col      = lon_col
        self._crs_str      = crs_str
        self._layer_name   = layer_name
        self._project_path = project_path

    def reload(self) -> None:
        if not os.path.exists(self._csv_path):
            print(f"[qgis_bridge] CSV não encontrado: {self._csv_path}")
            return
        canvas       = iface.mapCanvas()
        saved_extent = canvas.extent()
        has_extent   = not saved_extent.isEmpty()

        self._remove_existing_layer()
        layer = self._build_layer()
        if layer is None:
            return

        QgsProject.instance().addMapLayer(layer)
        print(f"[qgis_bridge] '{self._layer_name}' recarregada ({layer.featureCount()} pontos)")

        if has_extent:
            canvas.setExtent(saved_extent)
        else:
            canvas.zoomToFullExtent()
        canvas.refresh()
        self._save_project()

    def _build_layer(self) -> QgsVectorLayer | None:
        uri_path = self._csv_path.replace("\\", "/")
        uri = (
            f"file:///{uri_path}?delimiter=,"
            f"&xField={self._lon_col}&yField={self._lat_col}"
            f"&crs={self._crs_str}&decimalPoint=.&trimFields=yes"
        )
        layer = QgsVectorLayer(uri, self._layer_name, "delimitedtext")
        if not layer.isValid():
            print(f"[qgis_bridge] Camada inválida. URI: {uri}")
            return None
        return layer

    def _remove_existing_layer(self) -> None:
        project = QgsProject.instance()
        for layer in project.mapLayersByName(self._layer_name):
            project.removeMapLayer(layer.id())

    def _save_project(self) -> None:
        project = QgsProject.instance()
        if project.fileName():
            project.write()
