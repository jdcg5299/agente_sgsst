"""Tests del catálogo documental (hallazgos 5.10 y 5.11)."""
from __future__ import annotations

from agente_sgsst.generador import (
    cargar_catalogo,
    _codigo_formato,
    _numeral_documento,
    documentos_aplicables_por_capitulo,
)


class TestCatalogoNormalizado:
    def test_catalogo_tiene_60_documentos(self):
        catalogo = cargar_catalogo()
        assert len(catalogo) == 60

    def test_identificadores_estandar(self):
        catalogo = cargar_catalogo()
        for doc_id in ("D-001", "D-014", "D-036", "D-060"):
            assert doc_id in catalogo

    def test_codigo_ft_sst_normalizado(self):
        assert _codigo_formato("D-001") == "FT-SST-002"   # Acta del Responsable
        assert _codigo_formato("D-014") == "FT-SST-001"   # Diagnóstico inicial
        assert _codigo_formato("D-012") == "FT-SST-012"
        assert _codigo_formato("D-036") == "FT-SST-036"
        assert _codigo_formato("D-060") == "FT-SST-060"

    def test_numeral_desde_estandar_compuesto(self):
        assert _numeral_documento({"estandar": "3.3.1 - 3.3.6"}) == "3.3.1"
        assert _numeral_documento({"estandar": "4.1.1"}) == "4.1.1"
        assert _numeral_documento({"estandar": "N/A"}) is None


class TestFiltradoPorCapitulo:
    def test_capitulo_i_solo_los_7_estandares(self):
        # Res. 0312 Cap I (Art. 3): 7 estándares mínimos + siempre diagnóstico/informes.
        # Mapeados a los numerales oficiales de la Tabla de Valores: 1.1.1 (responsable),
        # 1.1.4 (afiliación SS), 1.2.1 (capacitación), 2.4.1 (plan anual), 3.1.4
        # (evaluaciones médicas), 4.1.1 (identificación de peligros), 4.2.1 (medidas).
        aplicables = set(documentos_aplicables_por_capitulo("Capítulo I"))
        assert aplicables == {
            "D-001",  # 1.1.1 Responsable SG-SST
            "D-004",  # 1.1.4 Afiliación SS
            "D-009",  # 1.2.1 Capacitación
            "D-015",  # 2.4.1 Plan Anual de Trabajo
            "D-026",  # 3.1.4 Evaluaciones médicas ocupacionales
            "D-036",  # 4.1.1 Identificación de peligros (IPARV)
            "D-040",  # 4.2.1 Medidas de prevención y control
            "D-014",  # Diagnóstico (siempre)
            "D-058", "D-059", "D-060",  # Informes ejecutivos (siempre)
        }

    def test_capitulo_iii_genera_el_catalogo_completo(self):
        catalogo = cargar_catalogo()
        aplicables = set(documentos_aplicables_por_capitulo("Capítulo III"))
        assert aplicables == set(catalogo.keys())

    def test_todo_documento_cumple_el_estandar_o_es_informe(self):
        catalogo = cargar_catalogo()
        for doc_id, info in catalogo.items():
            numeral = _numeral_documento(info)
            assert numeral is not None or doc_id in {"D-058", "D-059", "D-060"}, doc_id