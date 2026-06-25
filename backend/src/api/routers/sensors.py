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

def load_metadata() -> Dict[str, Dict[str, Any]]:
    if METADATA_FILE.exists():
        try:
            data = json.loads(METADATA_FILE.read_text(encoding="utf-8"))
            # Normaliza dados legados
            normalized = {}
            for k, v in data.items():
                if isinstance(v, str):
                    normalized[k] = {"name": v, "lat": None, "lng": None}
                elif isinstance(v, dict):
                    normalized[k] = {
                        "name": v.get("name", f"Sensor {k}"),
                        "lat": v.get("lat"),
                        "lng": v.get("lng"),
                    }
                else:
                    normalized[k] = {"name": f"Sensor {k}", "lat": None, "lng": None}
            return normalized
        except Exception:
            pass
    return {}

def save_metadata(metadata: Dict[str, Dict[str, Any]]) -> None:
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
    
    metadata = load_metadata()
    sensors = []
    
    if lat_col and lon_col:
        # Group rows by coordinates (representing unique sensors)
        sensor_rows = {}
        for idx, row in enumerate(table):
            lat_val = row[lat_col]
            lon_val = row[lon_col]
            if lat_val is None or lon_val is None:
                continue
            try:
                lat = float(str(lat_val).replace(",", "."))
                lon = float(str(lon_val).replace(",", "."))
            except (ValueError, TypeError):
                continue
            try:
                # Use rounded coords as key to handle slight precision differences
                key = (round(lat, 5), round(lon, 5))
                sensor_rows[key] = row
            except (ValueError, TypeError):
                continue
                
        # Sort coordinate keys for deterministic output
        sorted_keys = sorted(sensor_rows.keys())
        
        for i, key in enumerate(sorted_keys, 1):
            row = sensor_rows[key]
            lat, lon = key
            sensor_id = f"SNS-{i:03d}"
            
            # Recover metadata
            sensor_meta = metadata.get(sensor_id, {})
            sensor_name = sensor_meta.get("name", f"Sensor {i}")
            
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
    else:
        # Table does not have coordinates, cyclically assign to 5 sensors SNS-001 to SNS-005
        sensor_rows = {}
        for idx, row in enumerate(table):
            sensor_idx = (idx % 5) + 1
            sensor_id = f"SNS-{sensor_idx:03d}"
            sensor_rows[sensor_id] = row
            
        for i in range(1, 6):
            sensor_id = f"SNS-{i:03d}"
            row = sensor_rows.get(sensor_id)
            if not row:
                continue
                
            sensor_meta = metadata.get(sensor_id, {})
            sensor_name = sensor_meta.get("name", f"Sensor {i}")
            lat = sensor_meta.get("lat")
            lon = sensor_meta.get("lng")
            
            data_dict = {}
            for col in table.column_names:
                if col in ("id", "created_at", "data", "hora_utc"):
                    continue
                val = row[col]
                if val is not None:
                    try:
                        if isinstance(val, str) and "," in val:
                            val = val.replace(",", ".")
                        data_dict[col] = float(val)
                    except (ValueError, TypeError):
                        data_dict[col] = val
                        
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
def patch_sensor(id: str, payload: dict = Body(...), mgr: TableManagerDep = None):
    # Retrieve current sensors to make sure ID is valid
    sensors = get_sensors_list(mgr)
    sensor_exists = any(s["id"] == id for s in sensors)
    if not sensor_exists:
        raise HTTPException(status_code=404, detail=f"Sensor {id} não encontrado")
        
    metadata = load_metadata()
    if id not in metadata:
        metadata[id] = {"name": f"Sensor {id}", "lat": None, "lng": None}
        
    if "name" in payload:
        metadata[id]["name"] = payload["name"]
    if "lat" in payload:
        try:
            metadata[id]["lat"] = float(payload["lat"]) if payload["lat"] is not None else None
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Latitude inválida")
    if "lng" in payload:
        try:
            metadata[id]["lng"] = float(payload["lng"]) if payload["lng"] is not None else None
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Longitude inválida")
            
    save_metadata(metadata)
    
    # Trigger GPKG export immediately to update QGIS Server
    try:
        from qgis_bridge.exporter import export_gpkg
        table_name = get_active_table_name(mgr)
        if table_name:
            table = mgr.get(table_name)
            export_gpkg(table, mgr.folder)
    except Exception as e:
        print(f"[backend] Erro ao sincronizar GPKG pós PATCH: {e}")
        
    return {
        "id": id,
        "name": metadata[id]["name"],
        "lat": metadata[id]["lat"],
        "lng": metadata[id]["lng"]
    }
