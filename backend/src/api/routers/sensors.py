import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Body

from src.api.dependencies import TableManagerDep
from shared.config import DATA_DIR
from qgis_bridge.exporter import detect_coordinate_columns

router = APIRouter(prefix="/sensors", tags=["sensors"])

METADATA_FILE = Path(DATA_DIR) / "sensors_metadata.json"

def load_metadata() -> Dict[str, str]:
    if METADATA_FILE.exists():
        try:
            return json.loads(METADATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def save_metadata(metadata: Dict[str, str]) -> None:
    METADATA_FILE.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

def get_active_table_name(mgr) -> Optional[str]:
    """Retorna a tabela ativa, priorizando:
    1. A tabela marcada em status.json (campo 'tabela').
    2. A primeira tabela com colunas de coordenadas detectáveis.
    3. A primeira tabela disponível (last resort).
    """
    status_path = Path(DATA_DIR) / "status.json"
    if status_path.exists():
        try:
            data = json.loads(status_path.read_text(encoding="utf-8"))
            table_name = data.get("tabela")
            if table_name and mgr.exists(table_name):
                return table_name
        except Exception:
            pass

    # Fallback: busca a primeira tabela com colunas de coordenadas
    for name in mgr.list_tables():
        try:
            t = mgr.get(name)
            lat_col, lon_col = detect_coordinate_columns(t)
            if lat_col and lon_col:
                return name
        except Exception:
            continue

    # Último recurso: qualquer tabela
    tables = mgr.list_tables()
    return tables[0] if tables else None

def get_sensors_list(mgr) -> List[Dict[str, Any]]:
    table_name = get_active_table_name(mgr)
    if not table_name:
        return []
        
    table = mgr.get(table_name)
    lat_col, lon_col = detect_coordinate_columns(table)
    
    # Coordenadas fixas dos 5 sensores do Pelourinho para Fallback Espacial
    PELOURINHO_COORDS = [
        (-12.9745, -38.5120),  # Sensor 1
        (-12.9745, -38.5085),  # Sensor 2
        (-12.9735, -38.5102),  # Sensor 3
        (-12.9725, -38.5120),  # Sensor 4
        (-12.9725, -38.5085),  # Sensor 5
    ]
        
    # Group rows by coordinates (representing unique sensors)
    sensor_rows = {}
    for idx, row in enumerate(table):
        if lat_col and lon_col:
            lat_val = row[lat_col]
            lon_val = row[lon_col]
            if lat_val is None or lon_val is None:
                continue
            try:
                lat = float(str(lat_val).replace(",", "."))
                lon = float(str(lon_val).replace(",", "."))
            except (ValueError, TypeError):
                continue
        else:
            # Injeta coordenadas do Pelourinho de forma cíclica
            lat, lon = PELOURINHO_COORDS[idx % len(PELOURINHO_COORDS)]
            
        try:
            # Use rounded coords as key to handle slight precision differences
            key = (round(lat, 5), round(lon, 5))
            # Keep the latest row (assuming chronological order)
            sensor_rows[key] = row
        except (ValueError, TypeError):
            continue
            
    metadata = load_metadata()
    sensors = []
    
    # Sort coordinate keys for deterministic output
    sorted_keys = sorted(sensor_rows.keys())
    
    for i, key in enumerate(sorted_keys, 1):
        row = sensor_rows[key]
        lat, lon = key
        sensor_id = f"SNS-{i:03d}"
        
        # Recover custom name if exists
        sensor_name = metadata.get(sensor_id, f"Sensor {i}")
        
        # Build readings dictionary
        data_dict = {}
        for col in table.column_names:
            if col in (lat_col, lon_col, "id", "created_at", "data", "hora_utc"):
                continue
            val = row[col]
            if val is not None:
                try:
                    if isinstance(val, str) and "," in val:
                        val = val.replace(",", ".")
                    data_dict[col] = float(val)
                except (ValueError, TypeError):
                    data_dict[col] = val
                    
        # Provide compatible keys for frontend
        if "humidade" in data_dict and "umidade" not in data_dict:
            data_dict["umidade"] = data_dict["humidade"]
        if "umidade_relativa_do_ar__horaria____" in data_dict and "umidade" not in data_dict:
            data_dict["umidade"] = data_dict["umidade_relativa_do_ar__horaria____"]
        if "temperatura_do_ar___bulbo_seco__horaria___c_" in data_dict and "temperatura" not in data_dict:
            data_dict["temperatura"] = data_dict["temperatura_do_ar___bulbo_seco__horaria___c_"]
            
        sensors.append({
            "id": sensor_id,
            "name": sensor_name,
            "blk": "Pelourinho",
            "lat": lat,
            "lng": lon,
            "data": data_dict,
            "st": "online",
            "ts": str(row["hora_utc"]) if "hora_utc" in table.column_names else (str(row["created_at"]) if "created_at" in table.column_names else "20:00")
        })
        
    return sensors

@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def list_sensors(mgr: TableManagerDep) -> List[Dict[str, Any]]:
    return get_sensors_list(mgr)

@router.get("/{id}", response_model=Dict[str, Any])
def get_sensor(id: str, mgr: TableManagerDep) -> Dict[str, Any]:
    sensors = get_sensors_list(mgr)
    for s in sensors:
        if s["id"] == id:
            return s
    raise HTTPException(status_code=404, detail=f"Sensor {id} não encontrado")

@router.patch("/{id}")
def rename_sensor(id: str, payload: dict = Body(...), mgr: TableManagerDep = None):
    new_name = payload.get("name")
    if not new_name:
        raise HTTPException(status_code=400, detail="Campo 'name' é obrigatório")
        
    sensors = get_sensors_list(mgr)
    sensor_exists = any(s["id"] == id for s in sensors)
    if not sensor_exists:
        raise HTTPException(status_code=404, detail=f"Sensor {id} não encontrado")
        
    metadata = load_metadata()
    metadata[id] = new_name
    save_metadata(metadata)
    return {"id": id, "name": new_name}
