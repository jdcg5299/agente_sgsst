"""
Tests del motor de ponderación (hallazgo 5.3 de CONSTITUTION.md).

El motor es el cálculo real del FT-SST-001: sumatoria por cumplimiento + ítems
"No aplica" (que otorgan puntaje completo con justificación). Ningún defecto debe
pasar silencioso: entradas incompletas, numerales desconocidos o "No aplica" sin
justificación lanzan excepción (Principio XI).
"""
from __future__ import annotations

import pytest

from src.domain.ponderacion import (
    CriterioCalificacion,
    ResultadoDiagnosticoCapituloIII,
    calcular_diagnostico,
    calcular_diagnostico_capitulo_iii,
    cargar_estandares_capitulo_iii,
)


def _respuestas_de_relleno(con=None, excepto=None):
    """Genera respuestas para los 60 ítems: por defecto 'C', con excepciones.

    `con`: dict numeral -> (criterio, justificacion) para sobrescribir.
    `excepto`: set de numerales a NO incluir (para tests de incompletitud).
    """
    items = cargar_estandares_capitulo_iii()
    respuestas = {numeral: ("C", "") for numeral in items}
    if excepto:
        for numeral in excepto:
            respuestas.pop(numeral, None)
    if con:
        respuestas.update(con)
    return respuestas


class TestIntegridadTabla:
    def test_hay_exactamente_60_items(self):
        assert len(cargar_estandares_capitulo_iii()) == 60

    def test_suma_de_items_es_100_porciento(self):
        total = sum(item.valor_item for item in cargar_estandares_capitulo_iii().values())
        assert abs(total - 1.0) < 1e-9

    def test_suma_por_estandar_es_100_porciento(self):
        items = cargar_estandares_capitulo_iii()
        total = sum({item.estandar_num: item.valor_estandar for item in items.values()}.values())
        assert abs(total - 1.0) < 1e-9


class TestCalculoBasico:
    def test_todo_cumplimiento_da_100_porciento(self):
        resultado = calcular_diagnostico_capitulo_iii(_respuestas_de_relleno())
        assert isinstance(resultado, ResultadoDiagnosticoCapituloIII)
        assert resultado.capitulo == "Capítulo III"
        assert resultado.porcentaje == pytest.approx(1.0)
        assert resultado.total_obtenido == pytest.approx(1.0)

    def test_todo_no_cumple_da_cero(self):
        respuestas = _respuestas_de_relleno(
            con={numeral: ("NC", "") for numeral in cargar_estandares_capitulo_iii()}
        )
        resultado = calcular_diagnostico_capitulo_iii(respuestas)
        assert resultado.porcentaje == pytest.approx(0.0)
        assert resultado.total_obtenido == pytest.approx(0.0)

    def test_todo_no_aplica_otorga_el_100_porciento(self):
        """La regla 'No aplica' otorga el puntaje completo del ítem (explicacion_del_negocio.md, §3.3)."""
        con = {
            numeral: ("NA", f"No aplica para esta empresa — {numeral}")
            for numeral in cargar_estandares_capitulo_iii()
        }
        resultado = calcular_diagnostico_capitulo_iii(_respuestas_de_relleno(con=con))
        assert resultado.porcentaje == pytest.approx(1.0)

    def test_caso_mixto_calcula_la_sumatoria_correcta(self):
        # Valores verificados contra docs/tabla_ponderacion_resolucion_0312.md:
        # 2.4.1 = 2.0% | 4.1.1 = 4.0% | 5.1.1 = 5.0% -> 0.11 si el resto no cumple.
        todo_no_cumple = {numeral: ("NC", "") for numeral in cargar_estandares_capitulo_iii()}
        con = {
            **todo_no_cumple,
            "2.4.1": ("C", ""),
            "4.1.1": ("C", ""),
            "5.1.1": ("NA", "El plan de emergencias se delega según normatividad local."),
        }
        resultado = calcular_diagnostico_capitulo_iii(con)
        assert resultado.total_obtenido == pytest.approx(0.02 + 0.04 + 0.05)
        assert resultado.porcentaje == pytest.approx(0.11)

    def test_item_no_aplica_registrado_con_puntaje_completo(self):
        resultado = calcular_diagnostico_capitulo_iii(_respuestas_de_relleno(con={"5.1.2": ("NA", "Justificación")}))
        item = next(i for i in resultado.items if i.numeral == "5.1.2")
        assert item.criterio is CriterioCalificacion.NO_APLICA
        assert item.puntos_obtenidos == pytest.approx(item.valor_item)

    def test_resumen_por_estandar(self):
        resultado = calcular_diagnostico_capitulo_iii(_respuestas_de_relleno())
        assert len(resultado.por_estandar) == 7
        assert abs(sum(r.valor_maximo for r in resultado.por_estandar) - 1.0) < 1e-9


class TestValidacionEstricta:
    def test_no_aplica_sin_justificacion_lanza_error(self):
        with pytest.raises(ValueError, match="justificación"):
            calcular_diagnostico_capitulo_iii(_respuestas_de_relleno(con={"2.1.1": ("NA", "")}))

    def test_numeral_desconocido_lanza_error(self):
        respuestas = _respuestas_de_relleno()
        respuestas["99.9.9"] = ("C", "")
        with pytest.raises(ValueError, match="desconocidos"):
            calcular_diagnostico_capitulo_iii(respuestas)

    def test_respuestas_incompletas_lanzan_error(self):
        excepto = {"1.1.1", "7.1.4"}
        with pytest.raises(ValueError, match="faltan 2"):
            calcular_diagnostico_capitulo_iii(_respuestas_de_relleno(excepto=excepto))

    def test_criterio_invalido_lanza_error(self):
        with pytest.raises(ValueError, match="Criterio inválido"):
            calcular_diagnostico_capitulo_iii(_respuestas_de_relleno(con={"2.1.1": ("X", "")}))

    def test_respuesta_no_es_dict_lanza_error(self):
        with pytest.raises(ValueError, match="dict"):
            calcular_diagnostico_capitulo_iii(["2.1.1"])  # type: ignore[arg-type]


class TestRechazoOtrosCapitulos:
    @pytest.mark.parametrize("capitulo", ["Capítulo I", "Capítulo II"])
    def test_no_inventa_ponderacion_para_capitulos_sin_tabla_cargada(self, capitulo):
        """Principio XI: sin tabla oficial no se calcula, se falla explícito."""
        with pytest.raises(NotImplementedError, match="No existe motor de ponderación"):
            calcular_diagnostico(capitulo, _respuestas_de_relleno())

    def test_capitulo_iii_se_calcula_tambien_via_dispatcher(self):
        resultado = calcular_diagnostico("Capítulo III", _respuestas_de_relleno())
        assert resultado.porcentaje == pytest.approx(1.0)