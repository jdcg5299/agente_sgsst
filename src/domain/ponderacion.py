"""
Motor de ponderación y cálculo de diagnóstico para Capítulo III — Resolución 0312 de 2019.

Corrige el hallazgo 5.3 de CONSTITUTION.md (Sección 5): antes, `diagnostico.py`
solo maquetaba un esqueleto visual sin calcular ningún puntaje. Este módulo es el
motor determinista de cálculo real.

Solo soporta Capítulo III (60 ítems), cuya tabla de ponderación oficial está
cargada en `src/domain/data/estandares_0312_capitulo_iii.json`. Capítulos I y II
se rechazan explícitamente (`NotImplementedError`): la normativa vigente tiene
anexos de ponderación propios para esos capítulos que aún no están cargados al
proyecto, y el motor NO inventa porcentajes (Principio X y XI de CONSTITUTION.md).

Reglas de dominio aplicadas (ver `docs/explicacion_del_negocio.md` sección 3):
- Criterios: "Cumple totalmente" (C), "No cumple" (NC), "No aplica" (NA).
- Un ítem "No aplica" OTORGA el puntaje completo del ítem, siempre con justificación.
- El puntaje total = sumatoria de puntos por cumplimiento + puntos otorgados por NA.
- Ningún valor por defecto silencioso: entradas inválidas o incompletas lanzan excepción.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

_DATA_DIR = Path(__file__).parent / "data"
_ARCHIVO_CAPITULO_III = _DATA_DIR / "estandares_0312_capitulo_iii.json"


class CriterioCalificacion(str, Enum):
    """Criterios de calificación oficiales del FT-SST-001."""

    CUMPLE = "C"
    NO_CUMPLE = "NC"
    NO_APLICA = "NA"


@dataclass(frozen=True)
class ItemPonderado:
    """Ítem/criterio del estándar mínimo de Capítulo III, con su ponderación oficial."""

    numeral: str
    descripcion: str
    valor_item: float
    numeral_grupo: str
    valor_numeral_grupo: float
    estandar_num: int
    estandar_nombre: str
    valor_estandar: float
    ciclo: str


@dataclass(frozen=True)
class RespuestaItem:
    """Respuesta de la empresa para un ítem del diagnóstico."""

    criterio: CriterioCalificacion
    justificacion: str


@dataclass
class ResultadoItem:
    """Ítem ya evaluado dentro de un diagnóstico calculado."""

    numeral: str
    descripcion: str
    valor_item: float
    criterio: CriterioCalificacion
    justificacion: str
    puntos_obtenidos: float


@dataclass
class ResumenEstandar:
    estandar_num: int
    estandar_nombre: str
    valor_maximo: float
    valor_obtenido: float

    @property
    def porcentaje(self) -> float:
        return self.valor_obtenido / self.valor_maximo if self.valor_maximo else 0.0


@dataclass
class ResultadoDiagnosticoCapituloIII:
    capitulo: str = "Capítulo III"
    total_obtenido: float = 0.0
    total_posible: float = 1.0
    porcentaje: float = 0.0
    items: list[ResultadoItem] = field(default_factory=list)
    por_estandar: list[ResumenEstandar] = field(default_factory=list)


def cargar_estandares_capitulo_iii() -> dict[str, ItemPonderado]:
    """Carga la tabla de 60 ítems de Capítulo III desde el JSON estructurado.

    Es la fuente única de verdad (DRY): también la usa `clasificacion.py` vía
    `get_applicable_items` para no duplicar la lista de numerales.
    """
    with _ARCHIVO_CAPITULO_III.open("r", encoding="utf-8") as f:
        datos = json.load(f)

    items: dict[str, ItemPonderado] = {}
    for raw in datos["items"]:
        item = ItemPonderado(
            numeral=raw["numeral"],
            descripcion=raw["descripcion"],
            valor_item=float(raw["valor_item"]),
            numeral_grupo=raw["numeral_grupo"],
            valor_numeral_grupo=float(raw["valor_numeral_grupo"]),
            estandar_num=int(raw["estandar_num"]),
            estandar_nombre=raw["estandar_nombre"],
            valor_estandar=float(raw["valor_estandar"]),
            ciclo=raw["ciclo"],
        )
        items[item.numeral] = item

    return items


_ITEMS_CAPITULO_III: dict[str, ItemPonderado] = cargar_estandares_capitulo_iii()


def _validar_integridad_tabla() -> None:
    """Verifica que la suma de los 60 ítems sea 1.0 (100%) — falla explícito si no.

    Un error de carga silencioso produciría porcentajes incorrectos en todos los
    documentos generados, por eso la validación es obligatoria al importar.
    """
    total_items = sum(item.valor_item for item in _ITEMS_CAPITULO_III.values())
    total_estandar = sum(
        {item.estandar_num: item.valor_estandar for item in _ITEMS_CAPITULO_III.values()}.values()
    )
    if len(_ITEMS_CAPITULO_III) != 60:
        raise ValueError(
            f"Integridad de tabla Capítulo III comprometida: se cargaron "
            f"{len(_ITEMS_CAPITULO_III)} ítems, se esperaban 60."
        )
    if abs(total_items - 1.0) > 1e-9:
        raise ValueError(
            f"Integridad de tabla Capítulo III comprometida: la suma de los "
            f"valor_item es {total_items:.6f}, debe ser 1.0 (100%)."
        )
    if abs(total_estandar - 1.0) > 1e-9:
        raise ValueError(
            f"Integridad de tabla Capítulo III comprometida: la suma de los "
            f"valor_estandar es {total_estandar:.6f}, debe ser 1.0 (100%)."
        )


_validar_integridad_tabla()


def _parsear_respuesta(numeral: str, respuesta: RespuestaItem | tuple | CriterioCalificacion) -> RespuestaItem:
    if isinstance(respuesta, RespuestaItem):
        return respuesta
    if isinstance(respuesta, CriterioCalificacion):
        return RespuestaItem(criterio=respuesta, justificacion="")
    if isinstance(respuesta, str):
        texto = respuesta.strip().upper()
        try:
            criterio = CriterioCalificacion(texto)
        except ValueError:
            raise ValueError(
                f"Criterio inválido para {numeral}: {respuesta!r}. Debe ser "
                "'C', 'NC' o 'NA' (Cumple, No cumple, No aplica)."
            ) from None
        return RespuestaItem(criterio=criterio, justificacion="")
    if isinstance(respuesta, (tuple, list)):
        if len(respuesta) != 2:
            raise ValueError(
                f"Respuesta inválida para {numeral}: {respuesta!r}. "
                "Debe ser (criterio, justificacion) o un CriterioCalificacion."
            )
        criterio, justificacion = respuesta
        if not isinstance(criterio, CriterioCalificacion):
            texto = str(criterio).strip().upper()
            try:
                criterio = CriterioCalificacion(texto)
            except ValueError:
                raise ValueError(
                    f"Criterio inválido para {numeral}: {criterio!r}. Debe ser "
                    "'C', 'NC' o 'NA'."
                ) from None
        return RespuestaItem(criterio=criterio, justificacion=str(justificacion or ""))
    raise ValueError(
        f"Respuesta inválida para {numeral}: {respuesta!r}. Debe ser un "
        "RespuestaItem, un CriterioCalificacion o (criterio, justificacion)."
    )


def calcular_diagnostico_capitulo_iii(
    respuestas: dict[str, RespuestaItem | tuple | CriterioCalificacion],
) -> ResultadoDiagnosticoCapituloIII:
    """Calcula el diagnóstico ponderado de Capítulo III a partir de las respuestas.

    `respuestas` mapea numeral (ej. "4.2.3") a un valor que puede ser:
    - `RespuestaItem(criterio, justificacion)`, o
    - `(criterio, justificacion)` (tupla), o
    - `CriterioCalificacion` directo (sin justificación, solo válido para C/NC).

    Reglas estrictas (Principio XI de CONSTITUTION.md — sin valores por defecto
    silenciosos):
    - Se deben responder TODOS los 60 ítems; falta cualquier numeral -> ValueError.
    - Un numeral desconocido (fuera de los 60) -> ValueError.
    - Un ítem "No aplica" SIN justificación -> ValueError.
    """
    if not isinstance(respuestas, dict):
        raise ValueError(
            f"respuestas debe ser un dict numeral->(criterio, justificacion), "
            f"recibido: {type(respuestas)!r}"
        )

    numerales_tabla = set(_ITEMS_CAPITULO_III.keys())
    numerales_respuesta = set(respuestas.keys())

    faltantes = numerales_tabla - numerales_respuesta
    if faltantes:
        faltantes_ordenadas = ", ".join(sorted(faltantes))
        raise ValueError(
            f"Respuestas incompletas para Capítulo III: faltan {len(faltantes)} ítems "
            f"({faltantes_ordenadas}). El diagnóstico exige evaluar los 60 ítems."
        )

    desconocidos = numerales_respuesta - numerales_tabla
    if desconocidos:
        desconocidos_ordenados = ", ".join(sorted(desconocidos))
        raise ValueError(
            f"Numerales desconocidos: {desconocidos_ordenados}. No pertenecen a la "
            "tabla de 60 ítems de Capítulo III."
        )

    resultados: list[ResultadoItem] = []
    por_estandar: dict[int, dict[str, float]] = {}

    for numeral in sorted(numerales_tabla):
        item = _ITEMS_CAPITULO_III[numeral]
        respuesta = _parsear_respuesta(numeral, respuestas[numeral])

        if item.estandar_num not in por_estandar:
            por_estandar[item.estandar_num] = {"maximo": 0.0, "obtenido": 0.0}
        por_estandar[item.estandar_num]["maximo"] += item.valor_item

        if respuesta.criterio is CriterioCalificacion.CUMPLE:
            puntos = item.valor_item
        elif respuesta.criterio is CriterioCalificacion.NO_CUMPLE:
            puntos = 0.0
        elif respuesta.criterio is CriterioCalificacion.NO_APLICA:
            if not respuesta.justificacion.strip():
                raise ValueError(
                    f"Ítem {numeral} calificado como 'No aplica' sin justificación. "
                    "La regla de exclusión exige siempre una justificación normativa "
                    "(Principio I de CONSTITUTION.md)."
                )
            puntos = item.valor_item  # No aplica otorga el puntaje completo del ítem
        else:  # cubierto por _parsear_respuesta, por defensa:
            raise ValueError(f"Criterio inválido para {numeral}: {respuesta.criterio!r}")

        por_estandar[item.estandar_num]["obtenido"] += puntos
        resultados.append(
            ResultadoItem(
                numeral=numeral,
                descripcion=item.descripcion,
                valor_item=item.valor_item,
                criterio=respuesta.criterio,
                justificacion=respuesta.justificacion,
                puntos_obtenidos=puntos,
            )
        )

    total_obtenido = sum(r.puntos_obtenidos for r in resultados)
    total_posible = sum(item.valor_item for item in _ITEMS_CAPITULO_III.values())
    porcentaje = total_obtenido / total_posible if total_posible else 0.0

    resumen_estandar = [
        ResumenEstandar(
            estandar_num=num,
            estandar_nombre=_ITEMS_CAPITULO_III[
                next(n for n in _ITEMS_CAPITULO_III if _ITEMS_CAPITULO_III[n].estandar_num == num)
            ].estandar_nombre,
            valor_maximo=valor["maximo"],
            valor_obtenido=valor["obtenido"],
        )
        for num, valor in sorted(por_estandar.items())
    ]

    return ResultadoDiagnosticoCapituloIII(
        capitulo="Capítulo III",
        total_obtenido=round(total_obtenido, 6),
        total_posible=round(total_posible, 6),
        porcentaje=round(porcentaje, 6),
        items=resultados,
        por_estandar=resumen_estandar,
    )


def calcular_diagnostico(capitulo: str, respuestas: dict) -> ResultadoDiagnosticoCapituloIII:
    """Punto de entrada genérico que rechaza explícitamente Capítulos I y II."""
    if capitulo != "Capítulo III":
        raise NotImplementedError(
            f"No existe motor de ponderación para {capitulo}: la Resolución 0312/2019 "
            "tiene anexos de ponderación propios para Capítulos I y II que aún no están "
            "cargados al proyecto. No se inventan porcentajes (ver CONSTITUTION.md "
            "Sección 3 y hallazgo 5.3)."
        )
    return calcular_diagnostico_capitulo_iii(respuestas)