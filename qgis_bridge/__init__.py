"""
qgis_bridge
===========
Integração entre a matriz DynTable e o QGIS.

Módulos que REQUEREM ambiente QGIS (importar apenas dentro do QGIS):
  - watcher        (QFileSystemWatcher, QTimer)
  - layer_manager  (qgis.core, qgis.utils)
  - project_manager(qgis.core, qgis.utils)

Módulos que rodam FORA do QGIS (seguros para importar em qualquer contexto):
  - exporter       (sem dependências de Qt/QGIS)
  - launcher       (subprocess — abre o QGIS)
"""

# Importações seguras (sem Qt/QGIS)
from .exporter import (
    TableExporter,
    detect_coordinate_columns,
    export_all_tables,
    export_csv,
    export_geojson,
    table_to_csv_string,
    table_to_geojson,
    ExportResult,
)
from .launcher import launch_qgis, find_qgis_exe

# watcher, layer_manager e project_manager NÃO são importados aqui
# porque dependem de qgis.core / qgis.PyQt — disponíveis só dentro do QGIS.
# Importe-os diretamente quando precisar:
#   from qgis_bridge.watcher import FileWatcher, DyndbWatcher, MultiTableWatcher
#   from qgis_bridge.layer_manager import LayerManager
#   from qgis_bridge.project_manager import setup_project
