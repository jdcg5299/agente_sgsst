"""
Diagnóstico inicial FT-SST-001 — hallazgos 5.3 y 5.4 de CONSTITUTION.md, y modelo oficial.

Antes: este archivo solo maquetaba una tabla HTML con columnas C/NC/NA vacías,
parseando `docs/tabla_ponderacion_resolucion_0312.md` línea por línea en runtime
(hallazgos 5.4) y sin calcular NINGÚN puntaje (hallazgo 5.3). Para Capítulos I y II,
ni siquiera había descripciones oficiales (solo numerales y "(pendiente tabla oficial)").

Ahora:
- La fuente de datos es el motor de dominio `src/domain/ponderacion.py` (JSON
  estructurado con la Tabla de Valores oficial — Art. 27 y Anexo 1).
- Se usa la MISMA tabla de 60 ítems para los tres capítulos. En Cap. I y II los
  ítems no aplicables (Arts. 3 y 9) se otorgan automáticamente como "No Aplica"
  con puntaje máximo (Art. 27 parágrafo 2) y se muestran SIN resaltado amarillo.
- Si el contexto trae respuestas guardadas, se CALCULA el puntaje real
  (sumatoria por cumplimiento + "No aplica" que otorga puntaje completo).
- No se inventan resultados: sin respuestas completas, el informe queda
  explícitamente "pendiente de evaluación" (Principio XI).
"""

import os
from datetime import datetime
from html import escape

from agente_sgsst.domain.clasificacion import clasificar_empresa, get_applicable_items
from agente_sgsst.domain.ponderacion import (
    Totales,
    calcular_diagnostico,
    evaluacion_por_estandar,
    total_minimos_estandares,
)
from agente_sgsst.rendering.excel_diagnostico import generar_excel_diagnostico
from agente_sgsst.rendering.maquetador import get_header_ft_sst_002

# Las 11 columnas del instrumento oficial. "Puntaje Posible" abarca tres sub-columnas.
_NCOLUMNAS = 11
_ESTILO_AMARILLO = ' style="background-color: yellow;"'
_ENCABEZADOS = (
    "Ciclo",
    "Numeral",
    "Item",
    "Criterio",
    "Modo de verificación",
    "Valor del item del estandar",
    "Peso porcentual",
    "Cumple totalmente",
    "No cumple",
    "No aplica",
    "Calificacion de la empresa o contratante",
)


def _pct(value: float | None) -> str:
    """Formatea un porcentaje del diagnóstico.

    Sin resultado todavía (empresa nueva, sin respuestas guardadas) los valores
    dependientes de la evaluación son `None`: se representan vacíos en vez de
    romper la generación (Principio XI). Los pesos normativos del instrumento
    sí se muestran siempre: pertenecen al formato oficial, no al avance de la
    evaluación, y el .xlsx los escribe igual en estado pendiente.
    """
    if value is None:
        return ""
    return f"{value * 100:.2f}%"


def _celda(texto, *, estilo: str = "") -> str:
    """Celda de la tabla, con el contenido escapado.

    Los textos de la tabla vienen del JSON del instrumento y de lo que responde el
    evaluador; se escapan para que un `<script>` no termine ejecutándose al abrir
    la vista previa. Los valores ya formateados (porcentajes) no contienen
    caracteres problemáticos, pero se escapan igual por uniformidad.
    """
    return f"<td{estilo}>{escape(str(texto))}</td>"


def _fila_encabezado_completa(texto: str) -> str:
    return f'<tr><td colspan="{_NCOLUMNAS}" style="text-align: left;"><strong>{texto}</strong></td></tr>'


def _fila_totales(etiqueta: str, *, valor, cumples, nocumples, noaplicas, calificacion) -> str:
    """Fila de totales: la etiqueta ocupa Ítem..Modo y los valores caen en sus columnas."""
    return (
        f"<tr>{_celda('')}{_celda('')}"
        f'<td colspan="3" style="text-align: left;"><em>{etiqueta}</em></td>'
        f"{_celda(valor)}{_celda('')}"
        f"{_celda(cumples)}{_celda(nocumples)}{_celda(noaplicas)}{_celda(calificacion)}</tr>"
    )


def _valores_de_totales(totales: Totales, hay_resultado: bool) -> dict[str, str]:
    """Traduce un `Totales` del dominio a las celdas de las cuatro columnas."""
    if not hay_resultado:
        return {"cumples": "", "nocumples": "", "noaplicas": "", "calificacion": ""}
    return {
        "cumples": _pct(totales.cumples),
        "nocumples": _pct(totales.no_cumples),
        "noaplicas": _pct(totales.no_aplica),
        "calificacion": _pct(totales.calificacion),
    }


def _filas_tabla(capitulo, respuestas):
    """Construye las filas de la Tabla de Valores con las 11 columnas del instrumento.

    Estructura espejo del Excel oficial: encabezado de estándar por fase PHVA,
    encabezado de bloque solo para los grupos que el instrumento desglosa
    (1.1, 3.2, 4.1…), los 60 ítems, y el cierre de cada bloque con
    "PORCENTAJE TOTAL DEL ESTANDAR". El recorrido y los totales salen de
    `evaluacion_por_estandar`, igual que el .xlsx, para que ambos no divergan.

    Retorna (filas, resultado) donde resultado es None cuando aún no hay respuestas.
    """
    resultado = calcular_diagnostico(capitulo, respuestas) if respuestas else None
    evaluado = {r.numeral: r for r in resultado.items} if resultado else {}
    hay_resultado = resultado is not None

    filas = []
    for estandar in evaluacion_por_estandar(resultado):
        filas.append(
            _fila_encabezado_completa(
                f"{estandar.ciclo} — {estandar.estandar_nombre_oficial} ({estandar.valor * 100:.0f}%)"
            )
        )
        for resumen in estandar.bloques:
            bloque = resumen.bloque
            if bloque.desglosado:
                filas.append(
                    _fila_encabezado_completa(f"{bloque.clave} {bloque.nombre} ({bloque.valor * 100:.0f}%)")
                )
            for indice, item in enumerate(bloque.items):
                primero = indice == 0
                r_item = evaluado.get(item.numeral)
                celdas = {"cumples": "", "nocumples": "", "noaplicas": "", "calificacion": ""}
                estilo = ""
                if r_item is not None:
                    totales_item = Totales.de_item(r_item)
                    celdas = _valores_de_totales(totales_item, hay_resultado=True)
                    # Amarillo solo para el "No Aplica" manual (requiere
                    # justificación del evaluador), NO para el automático de la norma.
                    if totales_item.no_aplica and not r_item.automatico:
                        estilo = _ESTILO_AMARILLO
                filas.append(
                    f"  <tr{estilo}>"
                    f"{_celda(estandar.ciclo if primero else '')}"
                    f"{_celda(item.numeral)}"
                    f"{_celda(item.descripcion)}"
                    f"{_celda(item.criterio)}"
                    f"{_celda(item.modo_verificacion)}"
                    f"{_celda(_pct(item.valor_item))}"
                    f"{_celda(_pct(bloque.valor) if primero else '')}"
                    f"{_celda(celdas['cumples'])}{_celda(celdas['nocumples'])}"
                    f"{_celda(celdas['noaplicas'])}{_celda(celdas['calificacion'])}"
                    "</tr>"
                )
            if hay_resultado:
                filas.append(
                    _fila_totales(
                        "PORCENTAJE TOTAL DEL ESTANDAR",
                        valor=_pct(bloque.valor),
                        **_valores_de_totales(resumen.totales, hay_resultado),
                    )
                )
            else:
                filas.append(
                    _fila_totales(
                        "PORCENTAJE TOTAL DEL ESTANDAR - pendiente de evaluación",
                        valor=_pct(bloque.valor),
                        **{
                            "cumples": "",
                            "nocumples": "",
                            "noaplicas": "",
                            "calificacion": "",
                        },
                    )
                )

        if hay_resultado:
            filas.append(
                _fila_totales(
                    "SUMA TOTAL",
                    valor=_pct(estandar.valor_acumulado),
                    **_valores_de_totales(estandar.totales, hay_resultado),
                )
            )
        else:
            filas.append(
                _fila_totales(
                    "SUMA TOTAL - pendiente de evaluación",
                    valor=_pct(estandar.valor_acumulado),
                    **{"cumples": "", "nocumples": "", "noaplicas": "", "calificacion": ""},
                )
            )

    # Cierre: los mismos rótulos y el mismo orden que el .xlsx oficial, para que la
    # vista previa narre exactamente lo mismo que el archivo que se entrega.
    if resultado is None:
        for etiqueta in (
            "SUMA TOTAL DE LOS ESTANDRES MINIMOS",
            "SUMA TOTAL DE LOS AVANCES MÍNIMOS DEL SG-SST",
        ):
            filas.append(
                _fila_totales(
                    f"{etiqueta} - pendiente de evaluación",
                    valor=_pct(total_minimos_estandares()),
                    **{"cumples": "", "nocumples": "", "noaplicas": "", "calificacion": ""},
                )
            )
    else:
        totales = resultado.totales
        filas.append(
            _fila_totales(
                "SUMA TOTAL DE LOS ESTANDRES MINIMOS",
                valor=_pct(total_minimos_estandares()),
                cumples=_pct(totales.cumples),
                nocumples=_pct(totales.no_cumples),
                noaplicas=_pct(totales.no_aplica),
                calificacion="",
            )
        )
        filas.append(
            _fila_totales(
                "SUMA TOTAL DE LOS AVANCES MÍNIMOS DEL SG-SST",
                valor="",
                **_valores_de_totales(totales, hay_resultado),
            )
        )
    return filas, resultado


def generar_diagnostico_base(contexto):
    empresa = contexto["empresa"]
    capitulo = clasificar_empresa(empresa["total_trabajadores"], empresa["clase_riesgo_arl"])
    aplicables = get_applicable_items(capitulo)

    respuestas = contexto.get("estado_sistema", {}).get("diagnostico", {}).get("respuestas") or None

    filas, resultado = _filas_tabla(capitulo, respuestas)

    informe_path = "sistema_gestion/99_INFORMES_EJECUTIVOS/Diagnostico_Inicial_Resolucion_0312.md"
    header_table = get_header_ft_sst_002(
        "DIAGNÓSTICO INICIAL SG-SST",
        "FT-SST-001",
        "E2.3.1",
        empresa["razon_social"],
        fecha=datetime.now().strftime("%d/%m/%Y"),
    )

    matriz_html = "<table>\n  <tr>" + "".join(f"<th>{h}</th>" for h in _ENCABEZADOS) + "</tr>\n"
    matriz_html += "\n".join(filas)
    matriz_html += "\n</table>"

    nombres_articulo = {
        "Capítulo I": "Artículo 3",
        "Capítulo II": "Artículo 9",
        "Capítulo III": "Artículo 16",
    }
    n_aplicables = len(aplicables)

    if resultado is not None:
        n_manuales = resultado.aplicables
        n_auto_na = len(resultado.items) - n_manuales
        totales = resultado.totales
        resumen = (
            f"### Resultado del diagnóstico ({capitulo})\n\n"
            f"- Calificación de la empresa: **{totales.calificacion * 100:.2f}%** — Nivel "
            f"**{resultado.nivel}** (Art. 27: <60% Crítico, 60–85% Moderado, >85% Aceptable).\n"
            f"- Avance por cumplimiento: **{totales.cumples * 100:.2f}%** cumplido, "
            f"**{totales.no_cumples * 100:.2f}%** pendiente, "
            f"**{totales.no_aplica * 100:.2f}%** no aplica.\n"
        )
        if capitulo == "Capítulo III":
            resumen += f"- Ítems evaluados: {len(resultado.items)} / 60\n"
        else:
            resumen += (
                f"- Ítems evaluados: {n_manuales} / {n_aplicables} aplicables "
                f"({nombres_articulo[capitulo]}); {n_auto_na} ítems no aplicables "
                "otorgados automáticamente con puntaje máximo (Art. 27, parágrafo 2).\n"
            )
        nota_estado = ""
    else:
        if capitulo == "Capítulo III":
            resumen = (
                "### Evaluación pendiente\n\n"
                "_El diagnóstico de Capítulo III requiere las respuestas C/NC/NA de los 60 ítems "
                "para calcular el puntaje. Sin ellas no se calcula (Principio XI de CONSTITUTION.md)._"
            )
        else:
            resumen = (
                "### Evaluación pendiente\n\n"
                f"_El diagnóstico de {capitulo} requiere marcar C/NC/NA en los {n_aplicables} ítems "
                f"aplicables ({nombres_articulo[capitulo]}). Los {60 - n_aplicables} ítems no aplicables "
                "se otorgarán automáticamente con puntaje máximo (Art. 27, parágrafo 2) al calcular._"
            )
        nota_estado = "Pendiente de evaluación"

    contexto.setdefault("estado_sistema", {})
    contexto["estado_sistema"]["capitulo_aplicable"] = capitulo
    if "diagnostico" not in contexto["estado_sistema"]:
        contexto["estado_sistema"]["diagnostico"] = {}
    contexto["estado_sistema"]["diagnostico"].update(
        {
            "capitulo": capitulo,
            "estado": nota_estado or "Calculado",
            "porcentaje": resultado.porcentaje if resultado else None,
        }
    )

    contenido = f"""# Diagnóstico Inicial SG-SST

{header_table.strip()}

## Capítulo Aplicable: {capitulo}

{matriz_html}

{resumen}
"""

    os.makedirs(os.path.dirname(informe_path), exist_ok=True)
    with open(informe_path, "w", encoding="utf-8") as f:
        f.write("\n".join([line.rstrip() for line in contenido.split("\n")]))

    # El formato oficial de entrega del diagnóstico 0312 es Excel (.xlsx),
    # replicando el instrumento de docs/ (el .md solo se usa como vista previa web).
    generar_excel_diagnostico(capitulo, resultado, empresa, informe_path.replace(".md", ".xlsx"))

    return contexto
