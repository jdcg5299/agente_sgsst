"""
Tests de la entrega del diagnóstico FT-SST-001 (`generar_diagnostico_base`).

Contrato de entrega (decisión del proyecto): el diagnóstico de la Resolución
0312/2019 se entrega en **Excel (.xlsx)**, que replica el instrumento oficial;
el `.md` queda solo como vista previa web y **no** se genera `.docx` del
diagnóstico (el estándar Word FT-SST-002 es para los documentos del sistema de
gestión, no para el diagnóstico).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from agente_sgsst.domain.clasificacion import get_applicable_items
from agente_sgsst.rendering.diagnostico import generar_diagnostico_base

INFORMES = "sistema_gestion/99_INFORMES_EJECUTIVOS"
NOMBRE = "Diagnostico_Inicial_Resolucion_0312"


def _contexto(empresa=None, respuestas=None):
    empresa = empresa or {
        "razon_social": "ALEXA S.A.S.",
        "nit": "900123456",
        "total_trabajadores": 20,
        "clase_riesgo_arl": 1,
    }
    estado = {"capitulo_aplicable": "Capítulo II", "documentos_generados": []}
    if respuestas is not None:
        estado["diagnostico"] = {"respuestas": respuestas}
    return {"empresa": empresa, "responsable_sst": {}, "estado_sistema": estado}


def _respuestas_todas_c(capitulo="Capítulo II"):
    return {numeral: ["C", ""] for numeral in get_applicable_items(capitulo)}


@pytest.fixture(autouse=True)
def _aislar_cwd(tmp_path, monkeypatch):
    """Genera los informes en un directorio temporal, no en el repositorio."""
    monkeypatch.chdir(tmp_path)


class TestArchivosGenerados:
    def test_escribe_el_xlsx_oficial_y_el_md_de_vista_previa(self):
        generar_diagnostico_base(_contexto(respuestas=_respuestas_todas_c()))
        assert (Path(INFORMES) / f"{NOMBRE}.xlsx").exists()
        assert (Path(INFORMES) / f"{NOMBRE}.md").exists()

    def test_no_genera_docx_del_diagnostico(self):
        generar_diagnostico_base(_contexto(respuestas=_respuestas_todas_c()))
        diagnosticos = list((Path(INFORMES)).glob(f"{NOMBRE}.*"))
        assert not [p for p in diagnosticos if p.suffix == ".docx"]


class TestContextoActualizado:
    def test_registra_capitulo_puntaje_y_estado(self):
        ctx = generar_diagnostico_base(_contexto(respuestas=_respuestas_todas_c()))
        diag = ctx["estado_sistema"]["diagnostico"]
        assert diag["capitulo"] == "Capítulo II"
        assert diag["estado"] == "Calculado"
        assert diag["porcentaje"] == pytest.approx(1.0)

    def test_clasifica_el_capitulo_segun_los_datos_de_la_empresa(self):
        ctx = generar_diagnostico_base(
            _contexto(
                empresa={
                    "razon_social": "GRAN S.A.S.",
                    "nit": "900999",
                    "total_trabajadores": 120,
                    "clase_riesgo_arl": 3,
                },
                respuestas={n: ["C", ""] for n in get_applicable_items("Capítulo III")},
            )
        )
        assert ctx["estado_sistema"]["diagnostico"]["capitulo"] == "Capítulo III"
        assert ctx["estado_sistema"]["capitulo_aplicable"] == "Capítulo III"


class TestSinRespuestas:
    def test_no_revienta_y_deja_el_diagnostico_pendiente(self):
        ctx = generar_diagnostico_base(_contexto())
        diag = ctx["estado_sistema"]["diagnostico"]
        assert diag["estado"] == "Pendiente de evaluación"
        assert diag["porcentaje"] is None

    def test_aun_asin_genera_los_dos_archivos(self):
        generar_diagnostico_base(_contexto())
        base = Path(INFORMES)
        assert (base / f"{NOMBRE}.xlsx").exists()
        assert (base / f"{NOMBRE}.md").exists()

    def test_el_md_dice_pendiente_y_no_inventa_puntaje(self):
        generar_diagnostico_base(_contexto())
        md = (Path(INFORMES) / f"{NOMBRE}.md").read_text(encoding="utf-8")
        assert "Evaluación pendiente" in md


def test_el_contexto_no_se_persiste_en_disco_por_el_generador():
    """`generar_diagnostico_base` solo devuelve el contexto; persiste la capa web."""
    ctx = generar_diagnostico_base(_contexto(respuestas=_respuestas_todas_c()))
    assert isinstance(ctx, dict)
    json.dumps(ctx)  # sigue siendo serializable para `guardar_contexto`


class TestParidadEntreLosDosFormatos:
    """El .xlsx y el .md deben narrar los mismos números.

    Es la invariante que justifica mover los totales al dominio: si cada
    renderizador calculara por su cuenta, podrían divergir en silencio. Aquí se
    comprueba que ambos coincidan en ítems y filas de cierre.
    """

    ETIQUETAS = (
        "PORCENTAJE TOTAL DEL ESTANDAR",
        "SUMA TOTAL",
        "SUMA TOTAL DE LOS ESTANDRES MINIMOS",
        "SUMA TOTAL DE LOS AVANCES MÍNIMOS DEL SG-SST",
    )

    def test_los_dos_formatos_generan_los_mismos_60_items(self):
        from openpyxl import load_workbook

        generar_diagnostico_base(_contexto(respuestas=_respuestas_todas_c()))
        base = Path(INFORMES)
        ws = load_workbook(base / f"{NOMBRE}.xlsx")["Diagnostico inicial"]
        md = (base / f"{NOMBRE}.md").read_text(encoding="utf-8")

        numerales_xlsx = [
            str(ws.cell(row=f, column=2).value or "").strip()
            for f in range(1, ws.max_row + 1)
            if re.fullmatch(r"\d+\.\d+\.\d+", str(ws.cell(row=f, column=2).value or "").strip())
        ]
        numerales_md = re.findall(r"<td>(\d+\.\d+\.\d+)</td>", md)
        assert numerales_xlsx == numerales_md
        assert len(numerales_xlsx) == 60

    def test_los_dos_formatos_generan_las_mismas_filas_de_cierre(self):
        from openpyxl import load_workbook

        generar_diagnostico_base(_contexto(respuestas=_respuestas_todas_c()))
        base = Path(INFORMES)
        ws = load_workbook(base / f"{NOMBRE}.xlsx")["Diagnostico inicial"]
        md = (base / f"{NOMBRE}.md").read_text(encoding="utf-8")
        for etiqueta in self.ETIQUETAS:
            en_xlsx = sum(
                1
                for f in range(1, ws.max_row + 1)
                if str(ws.cell(row=f, column=3).value or "").strip().startswith(etiqueta)
            )
            assert en_xlsx == md.count(etiqueta), etiqueta

    def test_el_total_calificado_es_el_mismo_en_los_dos_formatos(self):
        from openpyxl import load_workbook

        generar_diagnostico_base(_contexto(respuestas=_respuestas_todas_c()))
        base = Path(INFORMES)
        ws = load_workbook(base / f"{NOMBRE}.xlsx")["Diagnostico inicial"]
        md = (base / f"{NOMBRE}.md").read_text(encoding="utf-8")

        fila = next(
            f
            for f in range(1, ws.max_row + 1)
            if str(ws.cell(row=f, column=3).value or "").strip() == "SUMA TOTAL DE LOS ESTANDRES MINIMOS"
        )
        assert ws.cell(row=fila, column=6).value == pytest.approx(1.0)
        assert "100.00%" in md

    def test_en_estado_pendiente_el_peso_normativo_es_visible_en_los_dos_formatos(self):
        """El peso normativo no depende de la evaluación: el .md no puede ocultarlo.

        En estado pendiente el .xlsx escribe `valor_item` y `peso` del instrumento
        (excel_diagnostico._fila_item) porque son propios del formato oficial. El
        .md debe narrar exactamente lo mismo.
        """
        from openpyxl import load_workbook

        generar_diagnostico_base(_contexto())
        base = Path(INFORMES)
        ws = load_workbook(base / f"{NOMBRE}.xlsx")["Diagnostico inicial"]
        md = (base / f"{NOMBRE}.md").read_text(encoding="utf-8")
        filas_md = md.split("<tr>")

        numerales = [
            str(ws.cell(row=f, column=2).value or "").strip()
            for f in range(1, ws.max_row + 1)
            if re.fullmatch(r"\d+\.\d+\.\d+", str(ws.cell(row=f, column=2).value or "").strip())
        ]
        assert numerales  # los 60 ítems se listan aunque no haya respuestas
        for numeral in numerales:
            fila = next(
                f
                for f in range(1, ws.max_row + 1)
                if str(ws.cell(row=f, column=2).value or "").strip() == numeral
            )
            celdas = next(c for c in filas_md if f"<td>{numeral}</td>" in c)
            for columna in (6, 7):  # Valor del item | Peso porcentual
                peso = ws.cell(row=fila, column=columna).value
                if peso is None:
                    continue  # el peso del grupo solo se anota en su primera fila
                assert f"<td>{peso * 100:.2f}%</td>" in celdas, f"{numeral} col {columna}"

    def test_en_estado_pendiente_las_filas_de_cierre_muestran_el_mismo_valor(self):
        """En pendiente los subtotales conservan su valor: ambos formatos narran igual."""
        from openpyxl import load_workbook

        generar_diagnostico_base(_contexto())
        base = Path(INFORMES)
        ws = load_workbook(base / f"{NOMBRE}.xlsx")["Diagnostico inicial"]
        md = (base / f"{NOMBRE}.md").read_text(encoding="utf-8")
        filas_md = md.split("<tr>")

        valores_xlsx = [
            ws.cell(row=f, column=6).value
            for f in range(1, ws.max_row + 1)
            if any(str(ws.cell(row=f, column=3).value or "").strip().startswith(e) for e in self.ETIQUETAS)
            and ws.cell(row=f, column=6).value is not None
        ]
        assert valores_xlsx  # en pendiente hay subtotales con su valor normativo

        # Las filas de cierre se emiten en el mismo orden en ambos formatos; se
        # emparejan por posición, no por etiqueta, porque se repiten por bloque.
        valores_md = []
        for fila_md in filas_md:
            if not any(e in fila_md for e in self.ETIQUETAS):
                continue
            match = re.search(r"<td[^>]*>(\d+\.\d+)%</td>", fila_md)
            assert match, fila_md[:80]  # ninguna fila de cierre oculta su valor
            valores_md.append(match.group(1))

        assert len(valores_xlsx) == len(valores_md)
        for valor_xlsx, valor_md in zip(valores_xlsx, valores_md):
            assert f"{valor_xlsx * 100:.2f}" == valor_md


class TestContenidoDeUsuarioNoSeEjecuta:
    """La razón social viene de un formulario y se escribe sin escapar en dos sitios.

    En el .md llega a una tabla Markdown (donde un `|` la rompe y el HTML crudo se
    ejecuta en los visores que lo permiten) y en el .xlsx a una celda (donde un `=`
    inicial se convierte en fórmula). Se prueban los dos formatos.
    """

    MALICIOSO = {
        "razon_social": '<script>alert("x")</script> | S.A.S.',
        "nit": "<b>900</b>",
        "total_trabajadores": 20,
        "clase_riesgo_arl": 1,
    }

    def test_el_md_no_lleva_html_crudo_de_la_razon_social(self):
        generar_diagnostico_base(_contexto(empresa=self.MALICIOSO, respuestas=_respuestas_todas_c()))
        md = (Path(INFORMES) / f"{NOMBRE}.md").read_text(encoding="utf-8")
        assert "<script>" not in md
        assert "&lt;script&gt;" in md

    def test_el_md_no_rompe_la_tabla_con_una_razon_social_con_barra(self):
        generar_diagnostico_base(_contexto(empresa=self.MALICIOSO, respuestas=_respuestas_todas_c()))
        md = (Path(INFORMES) / f"{NOMBRE}.md").read_text(encoding="utf-8")
        assert "<b>900</b>" not in md
        assert "&#124;" in md

    def test_la_tabla_de_la_matriz_escapa_cada_celda(self):
        from agente_sgsst.rendering.diagnostico import _celda

        assert _celda("<b>x</b>") == "<td>&lt;b&gt;x&lt;/b&gt;</td>"

    def test_el_xlsx_no_interpreta_la_razon_social_como_formula(self):
        from openpyxl import load_workbook

        generar_diagnostico_base(_contexto(empresa=self.MALICIOSO, respuestas=_respuestas_todas_c()))
        ws = load_workbook(Path(INFORMES) / f"{NOMBRE}.xlsx")["Diagnostico inicial"]
        assert ws["A3"].data_type != "f"

    def test_una_razon_social_normal_se_muestra_tal_cual(self):
        generar_diagnostico_base(_contexto(respuestas=_respuestas_todas_c()))
        md = (Path(INFORMES) / f"{NOMBRE}.md").read_text(encoding="utf-8")
        assert "ALEXA S.A.S." in md
