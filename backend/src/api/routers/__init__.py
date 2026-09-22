"""Routers do backend FastAPI (ingest, tables, status)."""

from . import ingest, tables, status

__all__ = ["ingest", "tables", "status"]
