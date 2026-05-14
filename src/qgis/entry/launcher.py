import os
import glob
import subprocess


def find_qgis_exe() -> str | None:
    candidates = []
    candidates += glob.glob(r"C:\Program Files\QGIS*\bin\qgis-bin.exe")
    for p in [r"C:\OSGeo4W\bin\qgis-bin.exe", r"C:\OSGeo4W64\bin\qgis-bin.exe"]:
        if os.path.exists(p):
            candidates.append(p)
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0]


def launch_qgis(
    qgis_exe:     str | None = None,
    project_path: str | None = None,
) -> subprocess.Popen | None:
    if qgis_exe is None:
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
            "Edite QGIS_EXE_PATH em config.py com o caminho correto."
        )

    if project_path is None:
        try:
            from config import QGIS_PROJECT_PATH
            project_path = QGIS_PROJECT_PATH
        except ImportError:
            project_path = None

    startup_script = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "startup_script.py"
    )
    if not os.path.exists(startup_script):
        raise FileNotFoundError(f"startup_script.py não encontrado: {startup_script}")

    cmd = [qgis_exe, "--code", startup_script]
    if project_path and os.path.exists(project_path):
        cmd += ["--project", project_path]

    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
