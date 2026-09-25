"""
Motor de ponderación y cálculo de diagnóstico — Resolución 0312 de 2019.

Corrige el hallazgo 5.3 de CONSTITUTION.md (Sección 5): antes, `diagnostico.py`
solo maquetaba un esqueleto visual sin calcular ningún puntaje. Este módulo es el
motor determinista de cálculo real.

Modelo oficial implementado (confirmado contra el Anexo 1 — Tabla de Valores):
- Existe UNA sola Tabla de Valores de 60 ítems (Art. 27) que se usa para TODOS
  los capítulos (cargan desde `src/domain/data/estandares_0312_capitulo_iii.json`).
- El conjunto de ítems APLICABLE por capítulo sale de los Artículos 3 (Cap. I: 7),
  9 (Cap. II: 21) y 16 (Cap. III: 60), ver `clasificacion.get_applicable_items`.
- Para empresas de menos de 50 trabajadores con riesgo I, II o III (Cap. I y II),
  los ítems NO aplicables se otorgan AUTOMÁTICAMENTE con el porcentaje máximo en
  la columna "No Aplica" (Art. 27, parágrafo 2). El motor reproduce esa regla sin
  requerir respuesta manual del evaluador.
- Capítulo III exige evaluar explícitamente los 60 ítems.

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

from agente_sgsst.domain.clasificacion import get_applicable_items

_DATA_DIR = Path(__file__).parent / "data"
_ARCHIVO_CAPITULO_III = _DATA_DIR / "estandares_0312_capitulo_iii.json"

_CAPITULOS_SOPORTADOS = ("Capítulo I", "Capítulo II", "Capítulo III")


class CriterioCalificacion(str, Enum):
    """Criterios de calificación oficiales del FT-SST-001."""

    CUMPLE = "C"
    NO_CUMPLE = "NC"
    NO_APLICA = "NA"


@dataclass(frozen=True)
class ItemPonderado:
    """Ítem/criterio del estándar mínimo, con su ponderación oficial (Anexo 1)."""

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
    # True cuando el ítem fue otorgado como "No Aplica" AUTOMÁTICAMENTE por la
    # regla del Art. 27 (no aplicable para el capítulo de la empresa). No es una
    # omisión del evaluador, por lo que no debe marcarse como hallazgo a revisar.
    automatico: bool = False


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

    @property
    def aplicables(self) -> int:
        """Ítems que debía evaluar manualmente el evaluador (los no automáticos)."""
        return sum(1 for item in self.items if not item.automatico)


def cargar_estandares_capitulo_iii() -> dict[str, ItemPonderado]:
    """Carga la Tabla de Valores de 60 ítems (Art. 27) desde el JSON estructurado.

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

# Justificación oficial que se registra en los ítems otorgados automáticamente como
# "No Aplica" para empresas de menos de 50 trabajadores con riesgo I/II/III (Art. 27
# parágrafo 2). Es parte de la regla de la norma, no una decisión del evaluador.
_JUSTIFICACION_NA_AUTO = {
    "Capítulo I": (
        "Ítem no aplicable para empresas de 10 o menos trabajadores con riesgo I, II o III "
        "(Art. 3 y Art. 27, Res. 0312 de 2019) — se otorga el porcentaje máximo en la "
        "columna 'No Aplica'."
    ),
    "Capítulo II": (
        "Ítem no aplicable para empresas de menos de 50 trabajadores con riesgo I, II o III "
        "(Art. 9 y Art. 27, Res. 0312 de 2019) — se otorga el porcentaje máximo en la "
        "columna 'No Aplica'."
    ),
}


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
            f"Integridad de tabla comprometida: se cargaron "
            f"{len(_ITEMS_CAPITULO_III)} ítems, se esperaban 60."
        )
    if abs(total_items - 1.0) > 1e-9:
        raise ValueError(
            f"Integridad de tabla comprometida: la suma de los "
            f"valor_item es {total_items:.6f}, debe ser 1.0 (100%)."
        )
    if abs(total_estandar - 1.0) > 1e-9:
        raise ValueError(
            f"Integridad de tabla comprometida: la suma de los "
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


def _calcular_diagnostico(
    capitulo: str,
    respuestas: dict[str, RespuestaItem | tuple | CriterioCalificacion],
) -> ResultadoDiagnosticoCapituloIII:
    """Núcleo del cálculo ponderado para cualquier capítulo de la Resolución 0312.

    Reglas estrictas (Principio XI de CONSTITUTION.md — sin valores por defecto
    silenciosos):
    - Se deben responder TODOS los ítems APLICABLES del capítulo (7 para Cap. I,
      21 para Cap. II, 60 para Cap. III); falta cualquier numeral aplicable -> ValueError.
    - Los numerales NO aplicables para empresas de <50 trabajadores con riesgo
      I/II/III (Cap. I y II) se otorgan automáticamente como "No Aplica" con el
      puntaje máximo y su justificación normativa (Art. 27, parágrafo 2).
    - Un numeral desconocido (fuera de los 60) -> ValueError.
    - Un numeral de la tabla que NO aplica al capítulo no puede responderse
      manualmente -> ValueError (no contradice la regla de "No Aplica" automático).
    - Un ítem "No aplica" SIN justificación -> ValueError.
    """
    if capitulo not in _CAPITULOS_SOPORTADOS:
        raise ValueError(
            f"Capítulo no soportado: {capitulo!r}. Debe ser 'Capítulo I', "
            "'Capítulo II' o 'Capítulo III'."
        )

    if not isinstance(respuestas, dict):
        raise ValueError(
            f"respuestas debe ser un dict numeral->(criterio, justificacion), "
            f"recibido: {type(respuestas)!r}"
        )

    numerales_tabla = set(_ITEMS_CAPITULO_III.keys())
    numerales_respuesta = set(respuestas.keys())
    aplicables = set(get_applicable_items(capitulo))
    no_aplicables = numerales_tabla - aplicables

    desconocidos = numerales_respuesta - numerales_tabla
    if desconocidos:
        desconocidos_ordenados = ", ".join(sorted(desconocidos))
        raise ValueError(
            f"Numerales desconocidos: {desconocidos_ordenados}. No pertenecen a la "
            "tabla de 60 ítems de la Resolución 0312 de 2019."
        )

    no_aplicables_respondidos = numerales_respuesta & no_aplicables
    if no_aplicables_respondidos:
        ordenados = ", ".join(sorted(no_aplicables_respondidos))
        raise ValueError(
            f"Ítems no aplicables al {capitulo} no pueden responderse manualmente: "
            f"{ordenados}. Se otorgan automáticamente como 'No Aplica' con el "
            "porcentaje máximo (Art. 27, parágrafo 2, Res. 0312 de 2019)."
        )

    faltantes = aplicables - numerales_respuesta
    if faltantes:
        faltantes_ordenadas = ", ".join(sorted(faltantes))
        raise ValueError(
            f"Respuestas incompletas para {capitulo}: faltan {len(faltantes)} ítems "
            f"({faltantes_ordenadas}). El diagnóstico exige evaluar los {len(aplicables)} "
            "ítems aplicables del capítulo."
        )

    resultados: list[ResultadoItem] = []
    por_estandar: dict[int, dict[str, float]] = {}

    for numeral in sorted(numerales_tabla):
        item = _ITEMS_CAPITULO_III[numeral]
        automatico = numeral in no_aplicables

        if automatico:
            respuesta = RespuestaItem(
                criterio=CriterioCalificacion.NO_APLICA,
                justificacion=_JUSTIFICACION_NA_AUTO[capitulo],
            )
        else:
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
                automatico=automatico,
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
        capitulo=capitulo,
        total_obtenido=round(total_obtenido, 6),
        total_posible=round(total_posible, 6),
        porcentaje=round(porcentaje, 6),
        items=resultados,
        por_estandar=resumen_estandar,
    )


def calcular_diagnostico_capitulo_iii(
    respuestas: dict[str, RespuestaItem | tuple | CriterioCalificacion],
) -> ResultadoDiagnosticoCapituloIII:
    """Calcula el diagnóstico ponderado de Capítulo III (los 60 ítems).

    Mantiene su firma por compatibilidad; delega en el motor generalizado.

    `respuestas` mapea numeral (ej. "4.2.3") a un valor que puede ser:
    - `RespuestaItem(criterio, justificacion)`, o
    - `(criterio, justificacion)` (tupla), o
    - `CriterioCalificacion` directo (sin justificación, solo válido para C/NC).
    """
    return _calcular_diagnostico("Capítulo III", respuestas)


def calcular_diagnostico(capitulo: str, respuestas: dict) -> ResultadoDiagnosticoCapituloIII:
    """Punto de entrada genérico: calcula el diagnóstico para cualquier capítulo.

    Capítulos I y II usan la misma Tabla de Valores (Art. 27) que Capítulo III; la
    diferencia es el conjunto de ítems aplicables (Arts. 3 y 9) y la regla de
    "No Aplica" automático para los ítems no exigibles (Art. 27, parágrafo 2).
    """
    return _calcular_diagnostico(capitulo, respuestas)