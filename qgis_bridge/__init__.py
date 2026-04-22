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

from .middleware import (
    ExportPipeline,
    build_default_pipeline,
    GpkgWriter,
    GeoJsonWriter,
    CsvWriter,
    DyndbReader,
)

# watcher, layer_manager e project_manager NÃO são importados aqui
# porque dependem de qgis.core / qgis.PyQt — disponíveis só dentro do QGIS.
# Importe-os diretamente quando precisar:
#   from qgis_bridge.watcher import FileWatcher, DyndbWatcher, MultiTableWatcher
#   from qgis_bridge.layer_manager import LayerManager
#   from qgis_bridge.project_manager import setup_project
