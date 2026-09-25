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
# Ítems aplicables por capítulo — válidos contra el ANEXO 1 oficial.
# ---------------------------------------------------------------------------
# Corrección de los hallazgos 5.1 y 5.2 de CONSTITUTION.md (resueltos con la
# fuente oficial): la Resolución 0312/2019 NO tiene tablas de ponderación propias
# por capítulo. Existe UNA sola Tabla de Valores de 60 ítems (Art. 27, Anexo 1) que
# se usa para todos los capítulos. Los conjuntos aplicables por capítulo salen de
# los ARTÍCULOS 3 (Cap. I: 7 estándares), 9 (Cap. II: 21 estándares) y 16 (Cap. III:
# 60 estándares), mapeados 1:1 a los numerales de la Tabla de Valores. Los ítems no
# aplicables de una empresa de menos de 50 trabajadores con riesgo I, II o III se
# OTORGAN automáticamente con el porcentaje máximo en la columna "No Aplica"
# (Art. 27, parágrafo 2).
_CAPITULO_I_ITEMS: frozenset[str] = frozenset(
    {
        # Art. 3, Res. 0312/2019 (empresas de 10 o menos trabajadores, riesgo I-II-III):
        # persona que diseñe el SG-SST, afiliación SS, capacitación, plan anual,
        # evaluaciones médicas ocupacionales, identificación de peligros y medidas de control.
        "1.1.1", "1.1.4", "1.2.1", "2.4.1", "3.1.4", "4.1.1", "4.2.1"
    }
)

_CAPITULO_II_ITEMS: frozenset[str] = frozenset(
    {
        # Art. 9, Res. 0312/2019 (empresas de 11 a 50 trabajadores, riesgo I-II-III):
        # 21 estándares mínimos, verificados numeral por numeral contra la Tabla de
        # Valores oficial (Anexo 1). Resuelve la discrepancia 5.2: el checklist
        # documental traía 22 por usar numeración propia, no los numerales oficiales.
        # 1. Asignación de persona que diseñe el SG-SST
        "1.1.1",
        # 2. Asignación de recursos
        "1.1.3",
        # 3. Afiliación al Sistema de Seguridad Social Integral
        "1.1.4",
        # 4. COPASST
        "1.1.6",
        # 5. Comité de Convivencia Laboral
        "1.1.8",
        # 6. Programa de capacitación
        "1.2.1",
        # 7. Política de SST
        "2.1.1",
        # 8. Plan Anual de Trabajo
        "2.4.1",
        # 9. Archivo o retención documental
        "2.5.1",
        # 10. Descripción sociodemográfica y diagnóstico de condiciones de salud
        "3.1.1",
        # 11. Actividades de Medicina del Trabajo y de Prevención y Promoción de la Salud
        "3.1.2",
        # 12. Evaluaciones médicas ocupacionales
        "3.1.4",
        # 13. Restricciones y recomendaciones médico-laborales
        "3.1.6",
        # 14. Reporte de accidentes de trabajo y enfermedades laborales
        "3.2.1",
        # 15. Investigación de incidentes, accidentes y enfermedades diagnosticadas como laborales
        "3.2.2",
        # 16. Identificación de peligros, evaluación y valoración de riesgos
        "4.1.1",
        # 17. Mantenimiento periódico de instalaciones, equipos, máquinas y herramientas
        "4.2.5",
        # 18. Entrega de EPP y capacitación en su uso adecuado
        "4.2.6",
        # 19. Plan de Prevención, Preparación y Respuesta ante emergencias
        "5.1.1",
        # 20. Brigada de prevención, preparación y respuesta ante emergencias
        "5.1.2",
        # 21. Revisión por la alta dirección
        "6.1.3",
    }
)
CAPITULO_II_CONTEO_ESPERADO_SEGUN_NORMA = 21
# Con la fuente oficial cargada (Anexo 1 + Art. 9), el conteo de Capítulo II queda
# conciliado: 21 ítems. La discrepancia del checklist (22) quedó documentada como
# error de numeración propia y se resolvió a favor de la norma.
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
