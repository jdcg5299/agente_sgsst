"""Compatibilidad hacia atrás para imports directos desde src/ingesta.py."""
from agente_sgsst.cli.ingesta import (
    solicitar_datos_usuario,
    _capturar_riesgo_arl,
)

__all__ = [
    "solicitar_datos_usuario",
    "_capturar_riesgo_arl",
]