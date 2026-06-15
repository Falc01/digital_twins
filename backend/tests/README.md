# Testes

Os testes serão migrados da suíte existente em `../digital_twins/tests/` na Fase 1.

Testes importantes já validados historicamente:
- test_exporter.py
- test_layer_manager_gpkg.py
- test_coordinates_qgis.py
- diag_pydantic.py
- check_sensors.py

Mantenha foco em:
- Pureza do core dyntable
- Fidelidade de exportação para GeoPackage
- Correção de CRS (EPSG:31984 ↔ 4326)
- Comportamento do pipeline de atualização
