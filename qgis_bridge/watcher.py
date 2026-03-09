"""
qgis_bridge/watcher.py
=======================
Monitora o CSV e dispara o reload da camada quando ele muda.

Problemas que este módulo resolve:
  1. Sinais múltiplos: o OS pode emitir vários fileChanged para
     uma única escrita. O debounce com QTimer cancela as chamadas
     intermediárias e executa apenas a última.

  2. Perda do watch no Windows: quando o arquivo é reescrito
     completamente (que é o que DynTable.save() faz), o Windows
     considera que o arquivo antigo "sumiu" e o watcher para de
     monitorar. A correção é re-adicionar o path dentro do callback.

IMPORTANTE: Este módulo roda DENTRO do Python do QGIS.
Não importe ele no ambiente Streamlit/Python normal.

Uso pelo startup_script.py:
    from qgis_bridge.watcher import CSVWatcher
    watcher = CSVWatcher(csv_path, callback=layer_manager.reload)
    watcher.start()
"""

import os

from qgis.PyQt.QtCore import QFileSystemWatcher, QTimer


class CSVWatcher:
    """
    Observador de arquivo CSV com debounce.

    Parâmetros:
        csv_path  → caminho do arquivo CSV a monitorar
        callback  → função chamada quando o arquivo muda
                    (normalmente LayerManager.reload)
        debounce_ms → janela de debounce em milissegundos (padrão 300)
    """

    def __init__(self, csv_path: str, callback, debounce_ms: int = 300):
        self._path       = csv_path
        self._callback   = callback
        self._debounce   = debounce_ms

        # ── QFileSystemWatcher ───────────────────────────────
        # Monitora o arquivo a nível de OS.
        # No Windows, para de monitorar após reescrita completa
        # (tratado no _on_file_changed abaixo).
        self._watcher = QFileSystemWatcher()

        # ── QTimer para debounce ─────────────────────────────
        # setSingleShot(True): o timer dispara apenas uma vez.
        # Cada chamada a _on_file_changed reinicia o timer — se
        # vários sinais chegarem em menos de debounce_ms, apenas
        # o último dispara o callback.
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(self._debounce)
        self._timer.timeout.connect(self._do_reload)

        # Conecta o sinal do watcher ao handler
        self._watcher.fileChanged.connect(self._on_file_changed)

    # ─────────────────────────────────────────────────────────
    #  API pública
    # ─────────────────────────────────────────────────────────

    def start(self) -> None:
        """
        Inicia o monitoramento do arquivo.
        Seguro chamar mesmo se o arquivo ainda não existir —
        o watcher tentará novamente quando o arquivo aparecer.
        """
        if os.path.exists(self._path):
            self._watcher.addPath(self._path)
            print(f"[qgis_bridge] Monitorando: {os.path.basename(self._path)}")
        else:
            print(f"[qgis_bridge] Arquivo ainda não existe, aguardando: "
                  f"{self._path}")

    def stop(self) -> None:
        """Para o monitoramento e cancela qualquer timer pendente."""
        self._timer.stop()
        if self._path in self._watcher.files():
            self._watcher.removePath(self._path)
        print("[qgis_bridge] Watcher parado.")

    # ─────────────────────────────────────────────────────────
    #  Handlers internos
    # ─────────────────────────────────────────────────────────

    def _on_file_changed(self, path: str) -> None:
        """
        Chamado pelo QFileSystemWatcher quando o arquivo muda.

        Faz duas coisas antes de iniciar o debounce:
          1. Re-adiciona o path ao watcher (fix Windows)
          2. Reinicia o timer de debounce
        """
        # Fix Windows: após reescrita completa, o watcher perde o arquivo.
        # Se o path sumiu da lista de arquivos monitorados, re-adiciona.
        if path not in self._watcher.files():
            if os.path.exists(path):
                self._watcher.addPath(path)

        # Reinicia o timer — cancela qualquer disparo anterior pendente.
        # Se mais sinais chegarem antes de debounce_ms, o timer é resetado
        # e a execução real é adiada novamente.
        self._timer.start()

    def _do_reload(self) -> None:
        """
        Executado após o debounce: chama o callback real.
        Neste ponto, o arquivo parou de mudar por pelo menos debounce_ms.
        """
        print("[qgis_bridge] Mudança detectada — recarregando camada...")
        try:
            self._callback()
        except Exception as e:
            print(f"[qgis_bridge] Erro no reload: {e}")
