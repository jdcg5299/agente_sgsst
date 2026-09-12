"""Compatibilidad hacia atrás para imports directos desde src/converter.py."""
from agente_sgsst.rendering.converter import (
    convertir_markdown_a_docx,
    REFERENCE_DOC_DEFAULT,
    _celdas_de_fila,
    _es_fila_separadora,
    _parsear_tabla,
    _convertir_con_python_docx,
)

__all__ = [
    "convertir_markdown_a_docx",
    "REFERENCE_DOC_DEFAULT",
    "_celdas_de_fila",
    "_es_fila_separadora",
    "_parsear_tabla",
    "_convertir_con_python_docx",
]