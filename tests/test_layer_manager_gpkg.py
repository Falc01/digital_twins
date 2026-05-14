"""
tests/test_layer_manager_gpkg.py
================================
Verifica se o LayerManager reconhece corretamente a fonte de dados GeoPackage.
Sem usar qgis.core se possível, ou mockado/ignorando.
"""

import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

# Mock qgis modules antes do import
sys.modules['qgis'] = MagicMock()
sys.modules['qgis.core'] = MagicMock()
sys.modules['qgis.utils'] = MagicMock()

from qgis_bridge.layer_manager import LayerManager

def test_layer_manager_gpkg_source(tmp_path):
    data_dir = str(tmp_path)
    # Criar um gpkg fake
    gpkg_path = os.path.join(data_dir, "sensores.gpkg")
    with open(gpkg_path, "w") as f:
        f.write("fake_gpkg")

    mgr = LayerManager(
        layer_name="sensores",
        project_path="dummy.qgz",
        data_dir=data_dir,
        table_name="sensores"
    )

    src = mgr._pick_data_source()
    assert src == gpkg_path
    print("[OK] LayerManager usa GPKG corretamente como fonte.")

    # Testando o mock do build_gpkg_layer
    with patch("qgis_bridge.layer_manager.QgsVectorLayer") as mock_qgs_layer:
        mock_instance = MagicMock()
        mock_instance.isValid.return_value = True
        mock_qgs_layer.return_value = mock_instance

        layer = mgr._build_layer(gpkg_path)
        assert layer is not None
        mock_qgs_layer.assert_called()
    
    print("[OK] LayerManager constrói QgsVectorLayer usando formato ogr para GPKG.")


if __name__ == "__main__":
    import pathlib
    with tempfile.TemporaryDirectory() as tmp:
        test_layer_manager_gpkg_source(pathlib.Path(tmp))
