"""
qgis_bridge
===========
Ponte entre o DynTable e o QGIS.

Módulos:
  project_manager → cria/carrega o arquivo .qgz
  layer_manager   → cria/recarrega a camada IoT preservando zoom
  watcher         → QFileSystemWatcher com debounce
  launcher        → abre o QGIS via subprocess (roda no Python normal)

IMPORTANTE:
  launcher.py roda no ambiente Python normal (Streamlit).
  Os demais módulos rodam dentro do Python embutido do QGIS.
  Por isso este __init__.py não importa nada automaticamente —
  evita erros de import quando o Streamlit carrega o pacote.
"""

__version__ = "1.0.0"
