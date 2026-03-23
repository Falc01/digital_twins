import os
from qgis.PyQt.QtCore import QFileSystemWatcher, QTimer


class CSVWatcher:
    def __init__(self, csv_path: str, callback, debounce_ms: int = 300):
        self._path     = csv_path
        self._callback = callback
        self._watcher  = QFileSystemWatcher()
        self._timer    = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(debounce_ms)
        self._timer.timeout.connect(self._do_reload)
        self._watcher.fileChanged.connect(self._on_file_changed)

    def start(self) -> None:
        if os.path.exists(self._path):
            self._watcher.addPath(self._path)
            print(f"[qgis_bridge] Monitorando: {os.path.basename(self._path)}")
        else:
            print(f"[qgis_bridge] Aguardando arquivo: {self._path}")

    def stop(self) -> None:
        self._timer.stop()
        if self._path in self._watcher.files():
            self._watcher.removePath(self._path)

    def _on_file_changed(self, path: str) -> None:
        if path not in self._watcher.files() and os.path.exists(path):
            self._watcher.addPath(path)
        self._timer.start()

    def _do_reload(self) -> None:
        print("[qgis_bridge] Mudança detectada — recarregando...")
        try:
            self._callback()
        except Exception as e:
            print(f"[qgis_bridge] Erro no reload: {e}")
