"""Generador del Diagnóstico FT-SST-001 en Excel (.xlsx), formato oficial Res. 0312/2019.

Replica la estructura del instrumento oficial que se entrega como
`docs/Diagnostico Resolucion 0312 de 2019 - 2026.xls` (hoja "Diagnostico inicial"):
cabecera de formato, jerarquía estándar → grupo → ítems del ciclo PHVA, y la
matriz de estándares con las 11 columnas del instrumento:

    Ciclo | Numeral | Item | Criterio | Modo de verificación |
    Valor del item del estandar | Peso porcentual |
    Puntaje Posible (Cumple totalmente / No cumple / No aplica) |
    Calificación de la empresa o contratante

Se replica además el cierre del instrumento: "PORCENTAJE TOTAL DEL ESTANDAR" por
grupo, "SUMA TOTAL" acumulado por estándar, "SUMA TOTAL DE LOS ESTANDRES MINIMOS"
y "SUMA TOTAL DE LOS AVANCES MÍNIMOS DEL SG-SST", más la calificación con su nivel
(Art. 27).

Las marcas de "Cumple/No cumple/No aplica" se registran con el VALOR del ítem en la
columna correspondiente (igual que el instrumento oficial). La fila "No aplica"
manual —que exige justificación del evaluador— se resalta en amarillo; el "No
aplica" automático de la norma (Art. 27, parágrafo 2) no se resalta.
"""

from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from agente_sgsst.domain.clasificacion import clasificar_nivel
from agente_sgsst.domain.ponderacion import (
    Totales,
    evaluacion_por_estandar,
    total_minimos_estandares,
)

# Anchos del instrumento oficial (A..K).
_ANCHO = {
    "A": 10,
    "B": 10,
    "C": 46,
    "D": 52,
    "E": 46,
    "F": 12,
    "G": 11,
    "H": 11,
    "I": 11,
    "J": 11,
    "K": 15,
}

NCOLUMNAS = 11
FILA_ENCABEZADO = 7

# Índices 0-based de las columnas del instrumento.
COL_CICLO = 0
COL_NUMERAL = 1
COL_ITEM = 2
COL_CRITERIO = 3
COL_MODO = 4
COL_VALOR = 5
COL_PESO = 6
COL_CUMPLE = 7
COL_NOCUMPLE = 8
COL_NOAPLICA = 9
COL_CALIFICA = 10

# Excel interpreta como fórmula cualquier celda que empiece por =, +, - o @. Los
# datos de la empresa vienen de un formulario de Streamlit, así que un nombre como
# "=1+1" o "=HYPERLINK(...)" se ejecutaría al abrir el archivo. El apóstrofo es el
# prefijo de texto que Excel reconoce y no muestra.
_INICIO_FORMULA = ("=", "+", "-", "@")


def _texto_seguro(valor) -> str:
    """Neutraliza texto de usuario que Excel leería como fórmula."""
    texto = str(valor or "")
    if texto.startswith(_INICIO_FORMULA):
        return f"'{texto}"
    return texto


def _fecha_de_hoy() -> str:
    """Fecha de generación. Se calcula en cada llamada, no al importar el módulo."""
    return datetime.now().strftime("%d/%m/%Y")


_NEGRITA = Font(bold=True)
_NEGRITA_TITULO = Font(bold=True, size=13)
_NEGRITA_BLOQUE = Font(bold=True, size=11)
_NEGRITA_GRUPO = Font(bold=True, size=10)
_CENTRO = Alignment(horizontal="center", vertical="center", wrap_text=True)
_IZQUIERDA = Alignment(horizontal="left", vertical="center", wrap_text=True)
_ARRIBA = Alignment(horizontal="left", vertical="top", wrap_text=True)
_GRIS = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
_AMARILLO = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
_MARCO = Border(*[Side(style="thin")])


def _estilo_borde(ws, fila: int) -> None:
    for col in range(1, NCOLUMNAS + 1):
        ws.cell(row=fila, column=col).border = _MARCO


def _fusionar(ws, fila: int, desde: int, hasta: int) -> None:
    ws.merge_cells(start_row=fila, start_column=desde, end_row=fila, end_column=hasta)


def _pct(ws, fila: int, desde: int, hasta: int) -> None:
    for col in range(desde, hasta + 1):
        ws.cell(row=fila, column=col).number_format = "0.00%"


def _encabezado_documento(ws, empresa, capitulo, porcentaje, nivel) -> None:
    """Cabecera de formato del instrumento (filas 1 a 5)."""
    _fusionar(ws, 1, 1, NCOLUMNAS)
    ws.cell(row=1, column=1, value="SISTEMA DE GESTIÓN DE LA SEGURIDAD Y SALUD EN EL TRABAJO")
    ws.cell(row=1, column=1).font = _NEGRITA_TITULO
    ws.cell(row=1, column=1).alignment = _CENTRO
    _estilo_borde(ws, 1)

    _fusionar(ws, 2, 1, NCOLUMNAS)
    ws.cell(row=2, column=1, value="DIAGNOSTICO INICIAL SG-SST - FORMATO FT-SST-001 / ESTANDAR E2.3.1")
    ws.cell(row=2, column=1).font = _NEGRITA
    ws.cell(row=2, column=1).alignment = _CENTRO
    _estilo_borde(ws, 2)

    _fusionar(ws, 3, 1, 7)
    ws.cell(
        row=3,
        column=1,
        value=(f"EMPRESA: {_texto_seguro(empresa['razon_social'])}  (NIT {_texto_seguro(empresa['nit'])})"),
    )
    _fusionar(ws, 3, 8, NCOLUMNAS)
    ws.cell(row=3, column=8, value=f"FECHA: {_fecha_de_hoy()}")
    _estilo_borde(ws, 3)
    ws.cell(row=3, column=1).alignment = _IZQUIERDA
    ws.cell(row=3, column=8).alignment = _IZQUIERDA

    _fusionar(ws, 4, 1, NCOLUMNAS)
    pct_texto = f"{porcentaje * 100:.2f}%" if porcentaje is not None else "—"
    ws.cell(
        row=4,
        column=1,
        value=f"CAPITULO APLICABLE: {capitulo}  |  Calificación: {pct_texto}  |  Nivel (Art. 27): {nivel}",
    )
    ws.cell(row=4, column=1).font = _NEGRITA
    ws.cell(row=4, column=1).alignment = _CENTRO
    _estilo_borde(ws, 4)

    _fusionar(ws, 5, 1, NCOLUMNAS)
    ws.cell(
        row=5,
        column=1,
        value="RESOLUCION 0312 DE 2019 - ESTANDARES MINIMOS DEL SISTEMA DE GESTION DE SEGURIDAD "
        "Y SALUD EN EL TRABAJO - ANEXO TECNICO (TABLA DE VALORES)",
    )
    ws.cell(row=5, column=1).font = _NEGRITA
    ws.cell(row=5, column=1).fill = _GRIS
    ws.cell(row=5, column=1).alignment = _CENTRO
    _estilo_borde(ws, 5)


def _encabezado_tabla(ws) -> None:
    """Los rótulos de las 11 columnas, con "Puntaje Posible" sobre sus tres sub-columnas."""
    titulos = {
        COL_CICLO: "Ciclo",
        COL_NUMERAL: "Numeral",
        COL_ITEM: "Item",
        COL_CRITERIO: "Criterio",
        COL_MODO: "Modo de verificación",
        COL_VALOR: "Valor del item del estandar",
        COL_PESO: "Peso porcentual",
        COL_CUMPLE: "Puntaje Posible",
        COL_CALIFICA: "Calificacion de la empresa o contratante",
    }
    for col, titulo in titulos.items():
        ws.cell(row=FILA_ENCABEZADO, column=col + 1, value=titulo)
    _fusionar(ws, FILA_ENCABEZADO, COL_CUMPLE + 1, COL_NOAPLICA + 1)
    for col in range(1, NCOLUMNAS + 1):
        celda = ws.cell(row=FILA_ENCABEZADO, column=col)
        celda.font = _NEGRITA
        celda.fill = _GRIS
        celda.alignment = _CENTRO
    _estilo_borde(ws, FILA_ENCABEZADO)

    subtitulos = {COL_CUMPLE: "Cumple totalmente", COL_NOCUMPLE: "No cumple", COL_NOAPLICA: "No aplica"}
    for col, titulo in subtitulos.items():
        celda = ws.cell(row=FILA_ENCABEZADO + 1, column=col + 1, value=titulo)
        celda.font = _NEGRITA
        celda.fill = _GRIS
        celda.alignment = _CENTRO
    _estilo_borde(ws, FILA_ENCABEZADO + 1)


def _encabezado_bloque(ws, fila: int, texto: str, *, grupo: bool = False) -> int:
    _fusionar(ws, fila, 1, NCOLUMNAS)
    celda = ws.cell(row=fila, column=1, value=texto)
    celda.font = _NEGRITA_GRUPO if grupo else _NEGRITA_BLOQUE
    celda.fill = _GRIS
    celda.alignment = _IZQUIERDA
    _estilo_borde(ws, fila)
    return fila + 1


def _fila_totales(ws, fila: int, etiqueta: str, valores: dict[int, float | None]) -> int:
    """Fila de totales: la etiqueta ocupa Ítem..Modo y los valores van en sus columnas."""
    _fusionar(ws, fila, COL_ITEM + 1, COL_MODO + 1)
    celda = ws.cell(row=fila, column=COL_ITEM + 1, value=etiqueta)
    celda.font = _NEGRITA
    celda.alignment = _IZQUIERDA
    for col, valor in valores.items():
        ws.cell(row=fila, column=col + 1, value=valor)
        ws.cell(row=fila, column=col + 1).alignment = _CENTRO
    _pct(ws, fila, COL_VALOR + 1, NCOLUMNAS)
    _estilo_borde(ws, fila)
    return fila + 1


# Orden de los totales en las cuatro columnas de Puntaje Posible / Calificación.
_COLUMNAS_DE_TOTALES = (COL_CUMPLE, COL_NOCUMPLE, COL_NOAPLICA, COL_CALIFICA)


def _valores_de_totales(totales: Totales) -> dict[int, float]:
    """Traduce un `Totales` del dominio a las columnas del instrumento."""
    return dict(
        zip(
            _COLUMNAS_DE_TOTALES,
            (totales.cumples, totales.no_cumples, totales.no_aplica, totales.calificacion),
        )
    )


def _fila_item(ws, fila, item, ciclo, peso_grupo, r_item) -> int:
    ws.cell(row=fila, column=COL_CICLO + 1, value=ciclo)
    ws.cell(row=fila, column=COL_NUMERAL + 1, value=item.numeral)
    ws.cell(row=fila, column=COL_ITEM + 1, value=item.descripcion)
    ws.cell(row=fila, column=COL_CRITERIO + 1, value=item.criterio)
    ws.cell(row=fila, column=COL_MODO + 1, value=item.modo_verificacion)
    ws.cell(row=fila, column=COL_VALOR + 1, value=item.valor_item)
    ws.cell(row=fila, column=COL_PESO + 1, value=peso_grupo)

    cumple = nocumple = noaplica = califica = None
    amarillo = False
    if r_item is not None:
        # El reparto por columna lo decide el dominio; aquí solo se pinta.
        totales = Totales.de_item(r_item)
        cumple = totales.cumples or None
        nocumple = totales.no_cumples or None
        noaplica = totales.no_aplica or None
        califica = totales.calificacion or None
        # Amarillo solo para el "No Aplica" manual (requiere justificación del
        # evaluador), NO para el "No Aplica" automático de la norma.
        amarillo = noaplica is not None and not r_item.automatico
    ws.cell(row=fila, column=COL_CUMPLE + 1, value=cumple)
    ws.cell(row=fila, column=COL_NOCUMPLE + 1, value=nocumple)
    ws.cell(row=fila, column=COL_NOAPLICA + 1, value=noaplica)
    ws.cell(row=fila, column=COL_CALIFICA + 1, value=califica)

    for col in (
        COL_CICLO,
        COL_NUMERAL,
        COL_VALOR,
        COL_PESO,
        COL_CUMPLE,
        COL_NOCUMPLE,
        COL_NOAPLICA,
        COL_CALIFICA,
    ):
        ws.cell(row=fila, column=col + 1).alignment = _CENTRO
    ws.cell(row=fila, column=COL_ITEM + 1).alignment = _ARRIBA
    ws.cell(row=fila, column=COL_CRITERIO + 1).alignment = _ARRIBA
    ws.cell(row=fila, column=COL_MODO + 1).alignment = _ARRIBA
    _pct(ws, fila, COL_VALOR + 1, NCOLUMNAS)
    if amarillo:
        for col in range(1, NCOLUMNAS + 1):
            ws.cell(row=fila, column=col).fill = _AMARILLO
    _estilo_borde(ws, fila)
    return fila + 1


def generar_excel_diagnostico(capitulo, resultado, empresa, ruta) -> None:
    """Escribe el Diagnóstico FT-SST-001 en Excel con la estructura del instrumento oficial.

    `resultado` es el diagnóstico ya calculado por el llamador (`None` cuando aún
    no hay respuestas): el renderizador solo formatea, nunca recalcula, para que
    el .xlsx y el .md no puedan divergir. `ruta` termina en `.xlsx`; el archivo
    se crea en el lugar dado y la función retorna None.
    """
    evaluado = {r.numeral: r for r in resultado.items} if resultado else {}
    estandares = evaluacion_por_estandar(resultado)

    wb = Workbook()
    ws = wb.active
    ws.title = "Diagnostico inicial"
    ws.freeze_panes = f"A{FILA_ENCABEZADO + 2}"
    for letra, ancho in _ANCHO.items():
        ws.column_dimensions[letra].width = ancho

    porcentaje = resultado.porcentaje if resultado else None
    nivel = resultado.nivel if resultado else "Pendiente de evaluación"
    _encabezado_documento(ws, empresa, capitulo, porcentaje, nivel)
    _encabezado_tabla(ws)

    fila = FILA_ENCABEZADO + 2
    for estandar in estandares:
        fila = _encabezado_bloque(
            ws,
            fila,
            f"{estandar.ciclo} — {estandar.estandar_nombre_oficial} ({estandar.valor * 100:.0f}%)",
        )
        for resumen in estandar.bloques:
            bloque = resumen.bloque
            if bloque.desglosado:
                fila = _encabezado_bloque(
                    ws, fila, f"{bloque.clave} {bloque.nombre} ({bloque.valor * 100:.0f}%)", grupo=True
                )
            for indice, item in enumerate(bloque.items):
                primero = indice == 0
                fila = _fila_item(
                    ws,
                    fila,
                    item,
                    estandar.ciclo if primero else None,
                    bloque.valor if primero else None,
                    evaluado.get(item.numeral),
                )
            if resultado is None:
                fila = _fila_totales(
                    ws,
                    fila,
                    "PORCENTAJE TOTAL DEL ESTANDAR - pendiente de evaluación",
                    {COL_VALOR: bloque.valor},
                )
            else:
                fila = _fila_totales(
                    ws,
                    fila,
                    "PORCENTAJE TOTAL DEL ESTANDAR",
                    {COL_VALOR: bloque.valor, **_valores_de_totales(resumen.totales)},
                )
        # "SUMA TOTAL" del estándar: valor acumulado de los estándares ya cerrados,
        # como en el instrumento oficial, con el avance del estándar que se cierra.
        if resultado is None:
            fila = _fila_totales(
                ws,
                fila,
                "SUMA TOTAL - pendiente de evaluación",
                {COL_VALOR: estandar.valor_acumulado},
            )
        else:
            fila = _fila_totales(
                ws,
                fila,
                "SUMA TOTAL",
                {COL_VALOR: estandar.valor_acumulado, **_valores_de_totales(estandar.totales)},
            )

    if resultado is None:
        for etiqueta in (
            "SUMA TOTAL DE LOS ESTANDRES MINIMOS",
            "SUMA TOTAL DE LOS AVANCES MÍNIMOS DEL SG-SST",
        ):
            fila = _fila_totales(
                ws,
                fila,
                f"{etiqueta} - pendiente de evaluación",
                {COL_VALOR: total_minimos_estandares()},
            )
    else:
        totales = resultado.totales
        fila = _fila_totales(
            ws,
            fila,
            "SUMA TOTAL DE LOS ESTANDRES MINIMOS",
            {
                COL_VALOR: total_minimos_estandares(),
                COL_CUMPLE: totales.cumples,
                COL_NOCUMPLE: totales.no_cumples,
                COL_NOAPLICA: totales.no_aplica,
            },
        )
        fila = _fila_totales(
            ws,
            fila,
            "SUMA TOTAL DE LOS AVANCES MÍNIMOS DEL SG-SST",
            {
                COL_CUMPLE: totales.cumples,
                COL_NOCUMPLE: totales.no_cumples,
                COL_NOAPLICA: totales.no_aplica,
                COL_CALIFICA: totales.calificacion,
            },
        )
        _fusionar(ws, fila, 1, NCOLUMNAS)
        ws.cell(
            row=fila,
            column=1,
            value=(
                f"CALIFICACIÓN DE LA EMPRESA: {totales.calificacion * 100:.2f}% - "
                f"NIVEL: {clasificar_nivel(totales.calificacion)} "
                "(Art. 27: <60% Critico, 60-85% Moderado, >85% Aceptable)"
            ),
        )
        ws.cell(row=fila, column=1).font = _NEGRITA
        ws.cell(row=fila, column=1).fill = _GRIS
        ws.cell(row=fila, column=1).alignment = _CENTRO
        _estilo_borde(ws, fila)

    wb.save(ruta)
