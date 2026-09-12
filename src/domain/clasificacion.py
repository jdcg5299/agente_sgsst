"""
Motor de clasificación de capítulo y de ítems aplicables — Resolución 0312 de 2019.

CORRIGE los hallazgos 5.1, 5.2, 5.13 y 5.14 de CONSTITUTION.md (Sección 5, auditoría).
Mantiene las mismas firmas públicas que el `clasificacion.py` original
(`clasificar_empresa`, `get_applicable_items`) para que `diagnostico.py` y
`generador.py` puedan seguir importándolas sin cambios adicionales.

Este módulo es determinista: no importa nada de `generation/` ni `rendering/`
(Principio III de CONSTITUTION.md).
"""
from __future__ import annotations

import json
from enum import Enum
from pathlib import Path

_DATA_DIR = Path(__file__).parent / "data"
_ARCHIVO_CAPITULO_III = _DATA_DIR / "estandares_0312_capitulo_iii.json"


class RiesgoARL(str, Enum):
    """Clase de riesgo ARL, en la notación oficial (numerales romanos)."""

    I = "I"
    II = "II"
    III = "III"
    IV = "IV"
    V = "V"

    @property
    def es_riesgo_alto(self) -> bool:
        return self in (RiesgoARL.IV, RiesgoARL.V)


_MAPA_NUMERICO_A_ROMANO = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}


def _normalizar_riesgo(clase_riesgo_arl) -> RiesgoARL:
    """Acepta el formato oficial ('I'..'V') o el numérico (1..5) que usa `ingesta.py`
    hoy (hallazgo 5.13). Ambos son válidos de entrada; el tipo canónico interno
    siempre es `RiesgoARL` (numeral romano), que es el que se debe usar al construir
    los prompts para el LLM y los documentos generados.
    """
    if isinstance(clase_riesgo_arl, RiesgoARL):
        return clase_riesgo_arl

    texto = str(clase_riesgo_arl).strip().upper()

    if texto in RiesgoARL.__members__:
        return RiesgoARL[texto]

    if texto in _MAPA_NUMERICO_A_ROMANO:
        return RiesgoARL(_MAPA_NUMERICO_A_ROMANO[texto])

    raise ValueError(
        f"Clase de riesgo ARL inválida: {clase_riesgo_arl!r}. "
        "Debe ser 'I'..'V' (formato oficial) o 1..5 (compatibilidad). "
        "Ver hallazgo 5.13 de CONSTITUTION.md."
    )


def normalizar_riesgo_arl(clase_riesgo_arl) -> RiesgoARL:
    """API pública para el borde de entrada (ingesta.py, main.py, validaciones).

    Devuelve el RiesgoARL canónico (numeral romano I..V), o lanza ValueError.
    Corrige el hallazgo 5.13: el dato canónico en todo el sistema es el romano,
    NO el entero 1..5 que hacía divergir los prompts del LLM.
    """
    return _normalizar_riesgo(clase_riesgo_arl)


def clasificar_empresa(total_trabajadores: int, clase_riesgo_arl) -> str:
    """Determina el capítulo aplicable de la Resolución 0312 de 2019.

    Corrige el hallazgo 5.14: ya NO acepta silenciosamente total_trabajadores <= 0
    (antes se clasificaba como "Capítulo I" sin avisar). Ahora lanza ValueError.
    """
    if not isinstance(total_trabajadores, int) or total_trabajadores <= 0:
        raise ValueError(
            f"total_trabajadores debe ser un entero positivo, recibido: "
            f"{total_trabajadores!r}. Ver hallazgo 5.14 de CONSTITUTION.md — "
            "una empresa con 0 o menos trabajadores no es un caso de negocio válido."
        )

    riesgo = _normalizar_riesgo(clase_riesgo_arl)

    # Excepción obligatoria: riesgo alto siempre es Capítulo III, sin importar el tamaño.
    if riesgo.es_riesgo_alto:
        return "Capítulo III"

    if total_trabajadores > 50:
        return "Capítulo III"

    if total_trabajadores <= 10:
        return "Capítulo I"

    return "Capítulo II"  # 11 a 50 trabajadores, riesgo I/II/III


# ---------------------------------------------------------------------------
# Ítems aplicables por capítulo
# ---------------------------------------------------------------------------

_CAPITULO_I_ITEMS: frozenset[str] = frozenset(
    {"1.1.1", "1.1.4", "1.2.1", "2.1.1", "2.2.1", "2.4.1", "2.5.1"}
)

# ADVERTENCIA — hallazgo 5.2 de CONSTITUTION.md:
# checklist_documental_resolucion_0312.md lista 22 numerales para Capítulo II,
# pese a que su propio encabezado declara "21 Estándares Mínimos". No ha sido
# posible conciliar esto contra el anexo oficial de la Resolución 0312/2019
# (no está entre las fuentes cargadas al proyecto). Se conserva el set tal como
# aparece en la fuente para no inventar cuál ítem "sobra", pero se expone
# `CAPITULO_II_CONTEO_VERIFICADO = False` para que cualquier capa superior
# (UI, reportes, logs) pueda advertir visiblemente la discrepancia en vez de
# ocultarla — ver Principio I y XI de CONSTITUTION.md.
_CAPITULO_II_ITEMS: frozenset[str] = frozenset(
    {
        "1.1.1", "1.1.2", "1.1.4", "1.1.6", "1.1.8", "1.2.1",
        "2.1.1", "2.2.1", "2.3.1", "2.4.1", "2.5.1", "2.6.1", "2.7.1", "2.8.1", "2.11.1",
        "3.1.1", "3.1.2", "3.2.1", "3.2.2", "3.3.1", "4.1.1", "4.2.1",
    }
)
CAPITULO_II_CONTEO_ESPERADO_SEGUN_NORMA = 21
CAPITULO_II_CONTEO_VERIFICADO = len(_CAPITULO_II_ITEMS) == CAPITULO_II_CONTEO_ESPERADO_SEGUN_NORMA


def _cargar_numerales_capitulo_iii() -> frozenset[str]:
    """Fuente única de verdad: los mismos 60 numerales reales usados por el motor
    de ponderación (`estandares_0312_capitulo_iii.json`). Antes (hallazgo 5.1),
    esta función generaba `{"1", "2", ..., "60"}` — enteros como texto que nunca
    coinciden con los numerales reales tipo "1.1.1", causando que TODO ítem se
    marcara como "No aplica" en el diagnóstico de Capítulo III.
    """
    with _ARCHIVO_CAPITULO_III.open("r", encoding="utf-8") as f:
        datos = json.load(f)
    return frozenset(item["numeral"] for item in datos["items"])


def get_applicable_items(capitulo: str) -> frozenset[str]:
    """Retorna el conjunto de numerales aplicables según el capítulo.

    Corrige el hallazgo 5.1: Capítulo III ahora retorna los 60 numerales reales
    (p.ej. "1.1.1", "4.2.3"), no índices enteros de relleno.
    """
    if capitulo == "Capítulo I":
        return _CAPITULO_I_ITEMS
    if capitulo == "Capítulo II":
        return _CAPITULO_II_ITEMS
    if capitulo == "Capítulo III":
        return _cargar_numerales_capitulo_iii()

    raise ValueError(
        f"Capítulo desconocido: {capitulo!r}. Debe ser 'Capítulo I', 'Capítulo II' "
        "o 'Capítulo III'."
    )
