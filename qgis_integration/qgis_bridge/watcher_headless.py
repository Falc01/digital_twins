import os
import time
import subprocess
import json
from pathlib import Path

# Pasta de dados compartilhada no container do QGIS
DATA_DIR = Path("/infra/dados")
STATUS_FILE = DATA_DIR / "status.json"
QGIS_PROJECT = DATA_DIR / "projeto_iot.qgz"

# Mantém registro do último timestamp processado
last_timestamp = None

print("[qgis_watcher] Daemon de automação headless do QGIS iniciado.", flush=True)

# Loop de monitoramento de status
while True:
    try:
        if STATUS_FILE.exists():
            try:
                data = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
            except Exception:
                time.sleep(1)
                continue
                
            current_timestamp = data.get("ultima_atualizacao")
            active_table = data.get("tabela")
            
            if current_timestamp != last_timestamp and active_table:
                print(f"[qgis_watcher] Nova sincronização detectada: {current_timestamp}. Processando tabela: {active_table}...", flush=True)
                
                # Executa o gerador de projeto headless do QGIS para registrar a nova camada no projeto
                gpkg_file = DATA_DIR / f"{active_table}.gpkg"
                if not gpkg_file.exists():
                    gpkg_file = DATA_DIR / "sensor_readings_demo.gpkg"
                    
                if gpkg_file.exists():
                    print(f"[qgis_watcher] Atualizando projeto {QGIS_PROJECT} com a camada vetorial {active_table}...", flush=True)
                    
                    # 1. Executa o project_generator.py headless usando as bindings locais do QGIS no contêiner
                    # O PYTHONPATH=/usr/share/qgis/python garante acesso ao qgis.core
                    env = os.environ.copy()
                    env["PYTHONPATH"] = "/usr/share/qgis/python"
                    env["QT_QPA_PLATFORM"] = "offscreen"
                    
                    res = subprocess.run([
                        "python3", 
                        "/qgis_integration/qgis_bridge/project_generator.py",
                        "--project", str(QGIS_PROJECT),
                        "--gpkg", str(gpkg_file),
                        "--table", active_table
                    ], env=env, capture_output=True, text=True)
                    
                    if res.returncode == 0:
                        print("[qgis_watcher] Camada registrada com sucesso no projeto QGIS.", flush=True)
                    else:
                        print(f"[qgis_watcher] ERRO ao registrar camada: {res.stderr}", flush=True)
                        
                    # 2. Executa o enable_wfs.py em seguida para habilitar o WFS OGC para a nova camada
                    res_wfs = subprocess.run([
                        "python3", 
                        "/qgis_integration/qgis_bridge/enable_wfs.py",
                        "--project", str(QGIS_PROJECT)
                    ], capture_output=True, text=True)
                    
                    if res_wfs.returncode == 0:
                        print("[qgis_watcher] WFS habilitado com sucesso para todas as camadas vetoriais.", flush=True)
                    else:
                        print(f"[qgis_watcher] ERRO ao habilitar WFS: {res_wfs.stderr}", flush=True)
                
                last_timestamp = current_timestamp
    except Exception as e:
        print(f"[qgis_watcher] Erro no loop do daemon: {e}", flush=True)
        
    time.sleep(2)
