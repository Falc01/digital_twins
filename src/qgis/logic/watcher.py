"""
qgis_bridge/watcher.py
======================
Monitora arquivos de dados e dispara callbacks ao detectar mudanças.

Duas classes principais
-----------------------
FileWatcher   — monitora qualquer arquivo (CSV, GeoJSON, etc.)
               Substitui o CSVWatcher original com suporte ampliado.

DyndbWatcher  — monitora o .dyndb diretamente.
               Ao detectar mudança: chama TableExporter.refresh()
               (gera CSV e GeoJSON) e depois notifica o QGIS para
               recarregar a camada. O QGIS lê sempre dados frescos.

MultiTableWatcher — coordena vários DyndbWatcher em paralelo.

CSVWatcher = FileWatcher  (alias para compatibilidade com código antigo)
"""

from __future__ import annotations

import os
from qgis.PyQt.QtCore import QFileSystemWatcher, QTimer


# ─────────────────────────────────────────────
#  FileWatcher
# ─────────────────────────────────────────────

class FileWatcher:
    """
    Monitora um único arquivo com debounce configurável.

    Parâmetros
    ----------
    path        : caminho do arquivo a monitorar
    callback    : função chamada após debounce (sem argumentos)
    debounce_ms : janela de debounce em ms (padrão 400)
    label       : nome legível para logs (padrão: basename do arquivo)
    """

    def __init__(
        self,
        path: str,
        callback,
        debounce_ms: int = 400,
        label: str | None = None,
    ) -> None:
        self._path     = path
        self._callback = callback
        self._label    = label or os.path.basename(path)
        self._watcher  = QFileSystemWatcher()
        self._timer    = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(debounce_ms)
        self._timer.timeout.connect(self._do_reload)
        self._watcher.fileChanged.connect(self._on_file_changed)

    def start(self) -> None:
        if os.path.exists(self._path):
            self._watcher.addPath(self._path)
            print(f"[watcher] Monitorando: {self._label}")
        else:
            print(f"[watcher] Aguardando criação de: {self._label}")

    def stop(self) -> None:
        self._timer.stop()
        if self._path in self._watcher.files():
            self._watcher.removePath(self._path)
        print(f"[watcher] Monitoramento encerrado: {self._label}")

    def _on_file_changed(self, path: str) -> None:
        # Alguns escritores deletam + recriam o arquivo — reativa se voltou
        if path not in self._watcher.files() and os.path.exists(path):
            self._watcher.addPath(path)
        self._timer.start()

    def _do_reload(self) -> None:
        print(f"[watcher] Mudança em '{self._label}' — disparando callback...")
        try:
            self._callback()
        except Exception as exc:
            print(f"[watcher] Erro no callback de '{self._label}': {exc}")


# ─────────────────────────────────────────────
#  DyndbWatcher — monitora .dyndb → exporta → notifica QGIS
# ─────────────────────────────────────────────

class DyndbWatcher:
    """
    Monitora o .dyndb de uma tabela e encadeia: exportar → recarregar.

    Fluxo ao detectar mudança no arquivo .dyndb:
      1. exporter.refresh()           → gera/atualiza CSV e GeoJSON
      2. layer_reload_callback()      → QGIS recarrega a camada

    Qualquer processo que salve a tabela (Streamlit, MQTT, script)
    aciona automaticamente a atualização no QGIS sem intermediário.

    Parâmetros
    ----------
    dyndb_path            : caminho do .dyndb
    exporter              : instância de TableExporter
    layer_reload_callback : função sem args chamada após export
    debounce_ms           : janela de debounce em ms (padrão 400)
    """

    def __init__(
        self,
        dyndb_path: str,
        exporter,
        layer_reload_callback,
        debounce_ms: int = 400,
    ) -> None:
        self._dyndb_path          = dyndb_path
        self._exporter            = exporter
        self._layer_reload_callback = layer_reload_callback
        self._label               = os.path.basename(dyndb_path)
        self._watcher             = QFileSystemWatcher()
        self._timer               = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(debounce_ms)
        self._timer.timeout.connect(self._do_reload)
        self._watcher.fileChanged.connect(self._on_file_changed)

    def start(self) -> None:
        if os.path.exists(self._dyndb_path):
            self._watcher.addPath(self._dyndb_path)
            print(f"[watcher] Monitorando matriz: {self._label}")
        else:
            print(f"[watcher] .dyndb não encontrado, aguardando: {self._dyndb_path}")

    def stop(self) -> None:
        self._timer.stop()
        if self._dyndb_path in self._watcher.files():
            self._watcher.removePath(self._dyndb_path)
        print(f"[watcher] Monitoramento encerrado: {self._label}")

    def _on_file_changed(self, path: str) -> None:
        if path not in self._watcher.files() and os.path.exists(path):
            self._watcher.addPath(path)
        self._timer.start()

    def _do_reload(self) -> None:
        print(f"[watcher] Mudança em '{self._label}' — exportando e recarregando...")
        try:
            ok = self._exporter.refresh()
            if ok:
                self._layer_reload_callback()
            else:
                print(f"[watcher] Exportação falhou para '{self._label}', reload cancelado.")
        except Exception as exc:
            print(f"[watcher] Erro no pipeline dyndb→export→reload: {exc}")


# ─────────────────────────────────────────────
#  MultiTableWatcher
# ─────────────────────────────────────────────

class MultiTableWatcher:
    """
    Coordena vários DyndbWatcher (um por tabela/camada).

    Exemplo:
        mw = MultiTableWatcher()
        mw.add(dyndb_path_1, exporter_1, layer_mgr_1.reload)
        mw.add(dyndb_path_2, exporter_2, layer_mgr_2.reload)
        mw.start_all()
    """

    def __init__(self) -> None:
        self._watchers: dict[str, DyndbWatcher] = {}

    def add(
        self,
        dyndb_path: str,
        exporter,
        layer_reload_callback,
        debounce_ms: int = 400,
    ) -> "MultiTableWatcher":
        name = os.path.basename(dyndb_path)
        self._watchers[name] = DyndbWatcher(
            dyndb_path=dyndb_path,
            exporter=exporter,
            layer_reload_callback=layer_reload_callback,
            debounce_ms=debounce_ms,
        )
        return self

    def start_all(self) -> None:
        for w in self._watchers.values():
            w.start()
        print(f"[watcher] {len(self._watchers)} tabela(s) monitorada(s).")

    def stop_all(self) -> None:
        for w in self._watchers.values():
            w.stop()

    def __len__(self) -> int:
        return len(self._watchers)


# ─────────────────────────────────────────────
#  Alias de compatibilidade
# ─────────────────────────────────────────────

CSVWatcher = FileWatcher
