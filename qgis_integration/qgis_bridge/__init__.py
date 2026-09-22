"""
qgis_bridge
===========
Integração headless entre a matriz DynTable e o QGIS Server.

Módulos que rodam sem dependência de interface gráfica:
  - gpkg_sync         (gravação de GeoPackage via sqlite3)
  - project_generator (geração headless de projetos .qgz via qgis.core)
"""

from .gpkg_sync import (
    sync_table_to_gpkg,
    detect_coordinate_columns,
    make_point_gpkg_wkb,
)
from .project_generator import setup_qgis_server_project
