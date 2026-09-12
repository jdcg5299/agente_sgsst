"""Compatibilidad hacia atrás para imports directos desde src/clasificacion.py."""
from src.domain.clasificacion import (
    RiesgoARL,
    clasificar_empresa,
    get_applicable_items,
    normalizar_riesgo_arl,
    CAPITULO_II_CONTEO_VERIFICADO,
    CAPITULO_II_CONTEO_ESPERADO_SEGUN_NORMA,
)

__all__ = [
    "RiesgoARL",
    "clasificar_empresa",
    "get_applicable_items",
    "normalizar_riesgo_arl",
    "CAPITULO_II_CONTEO_VERIFICADO",
    "CAPITULO_II_CONTEO_ESPERADO_SEGUN_NORMA",
]
