"""
qgis_bridge/launcher.py
========================
Abre o QGIS via subprocess com o projeto e o startup_script.

IMPORTANTE: Este é o ÚNICO módulo do qgis_bridge que roda no
ambiente Python normal (Streamlit). Não importa nada do QGIS.

Responsabilidades:
  - Localizar o executável do QGIS automaticamente no Windows
  - Montar o comando com --code e --project
  - Abrir o QGIS como processo independente (não bloqueia o Streamlit)

Uso pelo app.py:
    from qgis_bridge.launcher import launch_qgis, find_qgis_exe
    launch_qgis()
"""

import os
import glob
import subprocess


def find_qgis_exe() -> str | None:
    """
    Tenta localizar o qgis-bin.exe automaticamente no Windows.

    Procura em:
      1. C:\\Program Files\\QGIS*\\bin\\qgis-bin.exe
      2. C:\\OSGeo4W\\bin\\qgis-bin.exe
      3. C:\\OSGeo4W64\\bin\\qgis-bin.exe

    Retorna o caminho do mais recente encontrado, ou None se não achar.
    """
    candidates = []

    # Padrão de instalação oficial do QGIS no Windows
    candidates += glob.glob(
        r"C:\Program Files\QGIS*\bin\qgis-bin.exe"
    )

    # OSGeo4W (instalação alternativa)
    for osgeo_path in [
        r"C:\OSGeo4W\bin\qgis-bin.exe",
        r"C:\OSGeo4W64\bin\qgis-bin.exe",
    ]:
        if os.path.exists(osgeo_path):
            candidates.append(osgeo_path)

    if not candidates:
        return None

    # Ordena para pegar a versão mais recente (ex: QGIS 3.34 > 3.28)
    candidates.sort(reverse=True)
    return candidates[0]


def launch_qgis(
    qgis_exe:    str | None = None,
    project_path: str | None = None,
) -> subprocess.Popen | None:
    """
    Abre o QGIS com o startup_script.py injetado via --code.

    Parâmetros:
        qgis_exe     → caminho do executável. Se None, detecta automaticamente.
        project_path → caminho do .qgz. Se None, lê do config.py.

    Retorna o objeto Popen (processo não bloqueante), ou None em caso de erro.

    O QGIS abrirá com:
      - O projeto .qgz (se existir)
      - O startup_script.py já executado (watcher ativo)
    """
    # ── 1. Resolve o executável ──────────────────────────────
    if qgis_exe is None:
        # Tenta a config primeiro
        try:
            from config import QGIS_EXE_PATH
            qgis_exe = QGIS_EXE_PATH
        except ImportError:
            pass

    if not qgis_exe:
        qgis_exe = find_qgis_exe()

    if not qgis_exe or not os.path.exists(qgis_exe):
        raise FileNotFoundError(
            "Executável do QGIS não encontrado.\n"
            "Edite QGIS_EXE_PATH em config.py com o caminho correto.\n"
            f"Tentativa: {qgis_exe}"
        )

    # ── 2. Resolve o projeto ─────────────────────────────────
    if project_path is None:
        try:
            from config import QGIS_PROJECT_PATH
            project_path = QGIS_PROJECT_PATH
        except ImportError:
            project_path = None

    # ── 3. Resolve o startup_script ─────────────────────────
    # Sobe um nível de qgis_bridge/ para a raiz do projeto
    startup_script = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "startup_script.py"
    )

    if not os.path.exists(startup_script):
        raise FileNotFoundError(
            f"startup_script.py não encontrado: {startup_script}"
        )

    # ── 4. Monta o comando ───────────────────────────────────
    cmd = [qgis_exe, "--code", startup_script]

    # Adiciona o projeto somente se o arquivo já existir
    # (na primeira execução, o startup_script cria o .qgz)
    if project_path and os.path.exists(project_path):
        cmd += ["--project", project_path]

    print(f"[qgis_bridge] Iniciando QGIS: {' '.join(cmd)}")

    # ── 5. Abre como processo independente ───────────────────
    # Popen não bloqueia — o Streamlit continua rodando normalmente
    # enquanto o QGIS abre em paralelo.
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return process
