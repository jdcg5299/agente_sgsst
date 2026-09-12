"""Compatibilidad hacia atrás para imports directos desde src/diagnostico.py."""
from agente_sgsst.rendering.diagnostico import (
    generar_diagnostico_base,
    _filas_capitulo_iii,
    _filas_genericas,
)

__all__ = [
    "generar_diagnostico_base",
    "_filas_capitulo_iii",
    "_filas_genericas",
]