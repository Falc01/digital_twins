"""
Pacote do backend (FastAPI) do Gêmeo Digital IoT.

Fornece API funcional para:
- Ingestão de dados (Excel → tabelas dinâmicas)
- Consulta de tabelas e linhas
- Status/telemetria

Ver docs/guides/backend.md para instruções de execução e integração com frontend externo.
"""

from .main import app

__all__ = ["app"]
