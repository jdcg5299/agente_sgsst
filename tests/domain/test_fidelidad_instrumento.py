"""
Fidelidad del diagnóstico contra el instrumento oficial de la Resolución 0312/2019.

Estos tests no comparan la salida contra otras pruebas: leen el `.xls` que se
entrega al usuario (`docs/Diagnostico Resolucion 0312 de 2019 - 2026.xls`, hoja
"Diagnostico inicial") y lo contrastan contra el modelo de dominio. Si alguien
edita el JSON maestro, o el generador, y el resultado deja de coincidir con el
instrumento que la empresa va a firmar, estos tests fallan.

Conocido y aceptado a propósito: el instrumento usa saltos de línea dentro de las
celdas de texto solo para maquetar ("Conformación y funcionamiento\\ndel
COPASST"); el modelo los colapsa a un espacio porque el texto es el mismo.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import xlrd

from agente_sgsst.domain.ponderacion import (
    bloques_evaluacion,
    cargar_estandares_capitulo_iii,
    total_minimos_estandares,
)

INSTRUMENTO = Path(__file__).resolve().parents[2] / "docs" / "Diagnostico Resolucion 0312 de 2019 - 2026.xls"
HOJA = "Diagnostico inicial"

_RE_NUMERAL = re.compile(r"\d+\.\d+\.\d+")
_RE_PORCENTAJE = re.compile(r"^(?P<nombre>.+?)\s*\((?P<pct>\d+(?:[.,]\d+)?)\s*%\)\s*$")
_ESPACIOS = re.compile(r"\s+")


@pytest.fixture(scope="module")
def hoja_oficial():
    """La hoja "Diagnostico inicial" del `.xls` oficial."""
    if not INSTRUMENTO.exists():
        pytest.skip(f"El instrumento oficial no está disponible: {INSTRUMENTO}")
    libro = xlrd.open_workbook(str(INSTRUMENTO))
    if HOJA not in libro.sheet_names():
        pytest.fail(f"El instrumento oficial no tiene la hoja {HOJA!r}: {libro.sheet_names()}")
    return libro.sheet_by_name(HOJA)


# Columnas del instrumento: Numeral | Item | Criterio | Modo | Valor del item
COL_NUMERAL, COL_ITEM, COL_CRITERIO, COL_MODO, COL_VALOR = 1, 2, 3, 4, 5


def _normalizar(texto) -> str:
    return _ESPACIOS.sub(" ", str(texto).strip())


@pytest.fixture(scope="module")
def filas_oficiales() -> dict[str, tuple[str, str, str, float]]:
    """Numeral -> (Ítem, Criterio, Modo de verificación, Valor) leídos del .xls oficial."""
    if not INSTRUMENTO.exists():
        pytest.skip(f"El instrumento oficial no está disponible: {INSTRUMENTO}")
    libro = xlrd.open_workbook(str(INSTRUMENTO))
    if HOJA not in libro.sheet_names():
        pytest.fail(f"El instrumento oficial no tiene la hoja {HOJA!r}: {libro.sheet_names()}")
    hoja = libro.sheet_by_name(HOJA)

    filas: dict[str, tuple[str, str, str, float]] = {}
    for indice in range(hoja.nrows):
        numeral = _normalizar(hoja.cell_value(indice, COL_NUMERAL))
        if not _RE_NUMERAL.fullmatch(numeral):
            continue
        try:
            valor = float(hoja.cell_value(indice, COL_VALOR))
        except (TypeError, ValueError):
            valor = 0.0
        filas[numeral] = (
            _normalizar(hoja.cell_value(indice, COL_ITEM)),
            _normalizar(hoja.cell_value(indice, COL_CRITERIO)),
            _normalizar(hoja.cell_value(indice, COL_MODO)),
            valor,
        )
    return filas


class TestTablaDeValoresContraficheroOficial:
    def test_el_oficial_tiene_los_60_items(self, filas_oficiales):
        assert len(filas_oficiales) == 60

    def test_el_modelo_tiene_exactamente_los_mismos_numerales(self, filas_oficiales):
        assert set(cargar_estandares_capitulo_iii()) == set(filas_oficiales)

    def test_los_60_items_son_los_mismos(self, filas_oficiales):
        for numeral, item in cargar_estandares_capitulo_iii().items():
            oficial_item, oficial_criterio, oficial_modo, oficial_valor = filas_oficiales[numeral]
            assert _normalizar(item.descripcion) == oficial_item, f"Ítem {numeral}"
            assert _normalizar(item.criterio) == oficial_criterio, f"Criterio {numeral}"
            assert _normalizar(item.modo_verificacion) == oficial_modo, f"Modo de verificación {numeral}"
            assert item.valor_item == pytest.approx(oficial_valor), f"Valor {numeral}"

    def test_los_pesos_de_los_items_suman_el_100_por_ciento(self, filas_oficiales):
        total = sum(valor for _, _, _, valor in filas_oficiales.values())
        assert total == pytest.approx(1.0)

    def test_el_encabezado_del_oficial_tiene_las_11_columnas_del_instrumento(self, filas_oficiales):
        libro = xlrd.open_workbook(str(INSTRUMENTO))
        hoja = libro.sheet_by_name(HOJA)
        assert hoja.ncols == 11


class TestJerarquiaContraficheroOficial:
    def test_los_bloques_cubren_los_60_items_sin_repetir(self):
        bloques = bloques_evaluacion()
        numerales = [item.numeral for bloque in bloques for item in bloque.items]
        assert len(numerales) == 60
        assert len(set(numerales)) == 60

    def test_los_7_estandares_del_instrumento_estan_cubiertos(self):
        estandares = {bloque.estandar_num for bloque in bloques_evaluacion()}
        assert estandares == {1, 2, 3, 4, 5, 6, 7}

    def test_los_pesos_de_los_estandares_suman_el_100_por_ciento(self):
        estandares = {b.estandar_num: b.valor_estandar for b in bloques_evaluacion()}
        assert len(estandares) == 7
        assert sum(estandares.values()) == pytest.approx(1.0)

    def test_cada_bloque_declara_exactamente_lo_que_suman_sus_items(self):
        for bloque in bloques_evaluacion():
            assert sum(item.valor_item for item in bloque.items) == pytest.approx(bloque.valor), bloque.clave

    def test_el_instrumento_no_desglosa_los_estandares_2_5_6_y_7(self):
        """El oficial no pone encabezado de grupo en esos estándares: no lo inventamos."""
        sin_desglose = {bloque.estandar_num for bloque in bloques_evaluacion() if not bloque.desglosado}
        assert sin_desglose == {2, 5, 6, 7}

    def test_solo_los_grupos_que_el_oficial_desglosa_llevan_encabezado(self):
        desglosados = {bloque.clave for bloque in bloques_evaluacion() if bloque.desglosado}
        assert desglosados == {"1.1", "1.2", "3.1", "3.2", "3.3", "4.1", "4.2"}

    def test_los_ciclos_phva_del_instrumento_se_conservan(self):
        assert {bloque.ciclo for bloque in bloques_evaluacion()} == {
            "PLANEAR",
            "HACER",
            "VERIFICAR",
            "ACTUAR",
        }


@pytest.fixture(scope="module")
def texto_del_oficial(hoja_oficial) -> str:
    """Todo el texto de la hoja oficial, normalizado a espacios simples.

    Los encabezados de estándar vienen de distintas columnas según el estándar
    (A o B) y llevan el porcentaje como sufijo, así que se busca el nombre como
    subcadena del texto completo en vez de en una posición fija.
    """
    celdas = (
        _normalizar(hoja_oficial.cell_value(fila, columna))
        for fila in range(hoja_oficial.nrows)
        for columna in range(hoja_oficial.ncols)
    )
    return _ESPACIOS.sub(" ", " ".join(celdas))


@pytest.fixture(scope="module")
def porcentajes_por_encabezado(hoja_oficial) -> dict[str, float]:
    """Encabezado -> porcentaje, tal como los declara el oficial ("... (30%)").

    Solo se leen porcentajes normativos (los de los títulos de estándar y de grupo),
    nunca las celdas de calificación del evaluador.
    """
    porcentajes: dict[str, float] = {}
    for indice in range(hoja_oficial.nrows):
        for columna in range(hoja_oficial.ncols):
            texto = _normalizar(hoja_oficial.cell_value(indice, columna))
            encontrado = _RE_PORCENTAJE.search(texto)
            if encontrado:
                porcentajes[_ESPACIOS.sub(" ", encontrado.group("nombre"))] = float(
                    encontrado.group("pct").replace(",", ".")
                )
                break
    return porcentajes


class TestNombresOficialesDeEstandar:
    """Los 7 encabezados de estándar deben ser los del oficial, texto por texto."""

    def test_cada_encabezado_existe_literalmente_en_el_instrumento(self, texto_del_oficial):
        for bloque in bloques_evaluacion():
            nombre = _ESPACIOS.sub(" ", bloque.estandar_nombre_oficial)
            assert nombre in texto_del_oficial, (
                f"el estándar {bloque.estandar_num} no aparece en el .xls oficial: {nombre!r}"
            )

    def test_los_7_encabezados_son_distintos_y_no_se_inventa_ninguno(self):
        nombres = {bloque.estandar_num: bloque.estandar_nombre_oficial for bloque in bloques_evaluacion()}
        assert set(nombres) == {1, 2, 3, 4, 5, 6, 7}
        assert len(set(nombres.values())) == 7


class TestCierreNormativo:
    """Los porcentajes del cierre deben seguir siendo los que declara la norma.

    El `.xls` de `docs/` es una copia diligenciada: sus celdas de calificación
    reflejan la evaluación de quien lo llenó, no la norma. Lo que sí es normativo
    son los porcentajes de los estándares y de sus grupos, y eso es lo que se
    contrasta aquí — nunca los puntajes del evaluador anterior.
    """

    def test_los_11_bloques_declaran_el_porcentaje_del_oficial(self, porcentajes_por_encabezado):
        for bloque in bloques_evaluacion():
            declarado = self._porcentaje_del_oficial(bloque, porcentajes_por_encabezado)
            assert declarado is not None, f"el .xls no declara el porcentaje de {bloque.clave}"
            assert bloque.valor == pytest.approx(declarado / 100), bloque.clave

    def test_los_7_estandares_suman_el_100_por_ciento(self):
        assert total_minimos_estandares() == pytest.approx(1.0)

    @staticmethod
    def _porcentaje_del_oficial(bloque, porcentajes: dict[str, float]) -> float | None:
        """Porcentaje que el oficial declara para un bloque.

        Suele estar en el encabezado del estándar, pero el estándar 5 no repite su
        porcentaje en el título y lo declara en el de su grupo, así que se consulta
        el nombre del bloque, el del estándar y el de su primer ítem.
        """
        for nombre in (
            bloque.nombre,
            bloque.estandar_nombre_oficial,
            bloque.items[0].nombre_grupo,
        ):
            encontrado = porcentajes.get(_ESPACIOS.sub(" ", nombre))
            if encontrado is not None:
                return encontrado
        return None
