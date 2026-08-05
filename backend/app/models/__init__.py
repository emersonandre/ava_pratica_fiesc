"""Modelos de dados (camada Model).

Importar este pacote registra todas as tabelas no `Base.metadata` -- e o que
permite ao `init_db` criar o schema completo com uma chamada.
"""

from app.database.base import Base
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.fault_coverage import FaultCoverage
from app.models.index_metadata import IndexMetadata
from app.models.sensor_event import SensorEvent

__all__ = [
    "Base",
    "Document",
    "DocumentChunk",
    "FaultCoverage",
    "IndexMetadata",
    "SensorEvent",
]
