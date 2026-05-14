from __future__ import annotations

import logging
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from dataclasses import dataclass, field

logger = logging.getLogger("qgis_bridge.models")

_KEY_ALIASES: dict[str, str] = {
    "lat":          "latitude",
    "lat_grau":     "latitude",
    "coord_y":      "latitude",
    "geo_lat":      "latitude",
    "y":            "latitude",
    "lon":          "longitude",
    "long":         "longitude",
    "lng":          "longitude",
    "lon_grau":     "longitude",
    "coord_x":      "longitude",
    "geo_lon":      "longitude",
    "x":            "longitude",
    "device":       "device_id",
    "sensor_id":    "device_id",
    "sensor":       "device_id",
    "id_sensor":    "device_id",
    "temp":         "temperatura",
    "temperature":  "temperatura",
    "temp_c":       "temperatura",
    "temperatura_c":"temperatura",
    "hum":          "humidade",
    "humidity":     "humidade",
    "umidade":      "humidade",
    "pressure":     "pressao",
    "pressao_hpa":  "pressao",
    "pressure_hpa": "pressao",
    "estado":       "status",
    "state":        "status",
    "ativo":        "status",
    "active":       "status",
}

def normalize_keys(raw: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in raw.items():
        canonical = _KEY_ALIASES.get(key.lower(), key.lower())
        normalized[canonical] = value
    return normalized

class SensorReading(BaseModel):
    latitude:   float = Field(..., ge=-90,  le=90)
    longitude:  float = Field(..., ge=-180, le=180)
    device_id:  str = Field(default="desconhecido")
    row_id:     int = Field(default=0)
    created_at: str = Field(default="")
    temperatura: Optional[float] = Field(default=None)
    humidade:    Optional[float] = Field(default=None, ge=0, le=100)
    pressao:     Optional[float] = Field(default=None, gt=0)
    status:      Optional[str]   = Field(default=None)
    extra: dict[str, Any] = Field(default_factory=dict)

    @field_validator("temperatura", "humidade", "pressao", mode="before")
    @classmethod
    def coerce_to_float(cls, v: Any) -> Optional[float]:
        if v is None:
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    @field_validator("status", mode="before")
    @classmethod
    def coerce_status(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        return str(v)

    @model_validator(mode="before")
    @classmethod
    def collect_extra_fields(cls, values: dict[str, Any]) -> dict[str, Any]:
        known = {
            "latitude", "longitude", "device_id",
            "row_id", "created_at",
            "temperatura", "humidade", "pressao", "status", "extra",
        }
        extra: dict[str, Any] = {}
        clean: dict[str, Any] = {}
        for k, v in values.items():
            if k in known:
                clean[k] = v
            else:
                extra[k] = v
        clean["extra"] = extra
        return clean

    def to_properties(self) -> dict[str, Any]:
        base = {
            "id":          self.row_id,
            "created_at":  self.created_at,
            "device_id":   self.device_id,
            "latitude":    self.latitude,
            "longitude":   self.longitude,
            "temperatura": self.temperatura,
            "humidade":    self.humidade,
            "pressao":     self.pressao,
            "status":      self.status,
        }
        base.update({k: v for k, v in self.extra.items() if k not in base})
        return base

@dataclass
class ProcessingResult:
    table_name:   str
    total_rows:   int                = 0
    valid_rows:   int                = 0
    skipped_rows: int                = 0
    errors:       list[str]          = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total_rows == 0:
            return 0.0
        return self.valid_rows / self.total_rows

    def log_summary(self) -> None:
        logger.info(
            "[%s] total=%d  válidas=%d  descartadas=%d  (%.0f%%)",
            self.table_name,
            self.total_rows,
            self.valid_rows,
            self.skipped_rows,
            self.success_rate * 100,
        )
        for err in self.errors:
            logger.warning("  ↳ %s", err)

@dataclass
class RowData:
    row_id:     int
    created_at: str
    values:     dict[str, Any]

@dataclass
class TableData:
    name:         str
    column_names: list[str]
    column_types: dict[str, str]
    rows:         list[RowData]
    lat_col:      Optional[str] = None
    lon_col:      Optional[str] = None
