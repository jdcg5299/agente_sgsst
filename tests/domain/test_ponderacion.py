"""
Tests del motor de ponderación (hallazgo 5.3 de CONSTITUTION.md).

El motor es el cálculo real del FT-SST-001: sumatoria por cumplimiento + ítems
"No aplica" (que otorgan puntaje completo con justificación). Ningún defecto debe
pasar silencioso: entradas incompletas, numerales desconocidos o "No aplica" sin
justificación lanzan excepción (Principio XI).
"""

from __future__ import annotations

import pytest

from agente_sgsst.domain.clasificacion import get_applicable_items
from agente_sgsst.domain.ponderacion import (
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


def _respuestas_aplicables(capitulo, con=None, excepto=None):
    """Genera respuestas para los ítems APLICABLES del capítulo (por defecto 'C').

    Los numerales no aplicables NO se responden: el motor los otorga
    automáticamente como "No Aplica" (Art. 27 parágrafo 2).
    """
    respuestas = {numeral: ("C", "") for numeral in get_applicable_items(capitulo)}
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


class TestTextoOficialDelInstrumento:
    """El JSON maestro se reconstruyó desde el instrumento oficial de docs/ (.xls).

    Cada ítem debe traer el texto íntegro de sus tres columnas normativas
    (Ítem, Criterio, Modo de verificación) para que el diagnóstico entregado en
    Excel sea el instrumento auditable y no un resumen.
    """

    def test_todos_los_items_traen_criterio_y_modo_de_verificacion(self):
        items = cargar_estandares_capitulo_iii()
        sin_texto = [
            item.numeral
            for item in items.values()
            if not item.criterio.strip() or not item.modo_verificacion.strip()
        ]
        assert sin_texto == []

    def test_todos_los_items_traen_descripcion_y_nombre_de_grupo(self):
        items = cargar_estandares_capitulo_iii()
        sin_texto = [
            item.numeral
            for item in items.values()
            if not item.descripcion.strip() or not item.nombre_grupo.strip()
        ]
        assert sin_texto == []

    def test_las_descripciones_son_el_texto_del_instrumento(self):
        items = cargar_estandares_capitulo_iii()
        assert "diseñe e implemente" in items["1.1.1"].descripcion
        assert "seguridad social integral" in items["1.1.4"].descripcion

    def test_los_pesos_3_2_1_y_3_2_3_siguen_al_instrumento(self):
        items = cargar_estandares_capitulo_iii()
        assert items["3.2.1"].valor_item == pytest.approx(0.01)
        assert items["3.2.3"].valor_item == pytest.approx(0.02)

    def test_la_suma_por_grupo_coincide_con_su_valor_declarado(self):
        items = cargar_estandares_capitulo_iii()
        suma_por_grupo: dict[str, float] = {}
        declarado: dict[str, float] = {}
        for item in items.values():
            suma_por_grupo[item.numeral_grupo] = suma_por_grupo.get(item.numeral_grupo, 0.0) + item.valor_item
            declarado[item.numeral_grupo] = item.valor_numeral_grupo
        for grupo, suma in suma_por_grupo.items():
            assert suma == pytest.approx(declarado[grupo]), grupo

    def test_un_estandar_tiene_7_grupos_o_mas_y_el_6_1_es_del_verificar(self):
        items = cargar_estandares_capitulo_iii()
        assert items["6.1.1"].ciclo == "VERIFICAR"
        assert items["7.1.1"].ciclo == "ACTUAR"


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
        resultado = calcular_diagnostico_capitulo_iii(
            _respuestas_de_relleno(con={"5.1.2": ("NA", "Justificación")})
        )
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


class TestCalculoPorCapitulo:
    """Capítulos I y II usan la misma Tabla de Valores (Art. 27); los ítems no
    aplicables se otorgan automáticamente con puntaje máximo (Art. 27 parágrafo 2)."""

    def test_capitulo_ii_todo_cumplimiento_da_100_porciento(self):
        # Los 21 aplicables cumplen; los 39 restantes se otorgan automáticamente.
        resultado = calcular_diagnostico("Capítulo II", _respuestas_aplicables("Capítulo II"))
        assert isinstance(resultado, ResultadoDiagnosticoCapituloIII)
        assert resultado.capitulo == "Capítulo II"
        assert resultado.porcentaje == pytest.approx(1.0)
        assert resultado.total_obtenido == pytest.approx(1.0)

    def test_capitulo_ii_evalua_los_60_items_de_la_tabla(self):
        resultado = calcular_diagnostico("Capítulo II", _respuestas_aplicables("Capítulo II"))
        assert len(resultado.items) == 60
        assert resultado.total_posible == pytest.approx(1.0)

    def test_capitulo_ii_no_aplica_automatico_con_puntaje_y_justificacion(self):
        resultado = calcular_diagnostico("Capítulo II", _respuestas_aplicables("Capítulo II"))
        auto_na = [item for item in resultado.items if item.automatico]
        assert len(auto_na) == 39  # 60 tabla - 21 aplicables
        assert all(item.criterio is CriterioCalificacion.NO_APLICA for item in auto_na)
        assert all(item.puntos_obtenidos == pytest.approx(item.valor_item) for item in auto_na)
        assert all(item.justificacion.strip() for item in auto_na)

    def test_capitulo_ii_un_no_cumple_baja_el_puntaje(self):
        respuestas = _respuestas_aplicables("Capítulo II", con={"4.1.1": ("NC", "")})
        resultado = calcular_diagnostico("Capítulo II", respuestas)
        assert resultado.porcentaje == pytest.approx(1.0 - 0.04)

    def test_capitulo_ii_no_aplica_manual_exige_justificacion(self):
        respuestas = _respuestas_aplicables("Capítulo II", con={"4.1.1": ("NA", "")})
        with pytest.raises(ValueError, match="justificación"):
            calcular_diagnostico("Capítulo II", respuestas)

    def test_capitulo_ii_faltan_aplicables_lanzan_error(self):
        respuestas = _respuestas_aplicables("Capítulo II", excepto={"4.1.1", "1.1.1"})
        with pytest.raises(ValueError, match="faltan 2"):
            calcular_diagnostico("Capítulo II", respuestas)

    def test_capitulo_ii_item_no_aplicable_respondido_manualmente_error(self):
        # 4.2.2 NO aplica al Capítulo II (Art. 9): el motor lo rechaza porque debe
        # otorgarse automáticamente, no responderse.
        respuestas = _respuestas_aplicables("Capítulo II")
        respuestas["4.2.2"] = ("NC", "")
        with pytest.raises(ValueError, match="no aplicables al Capítulo II"):
            calcular_diagnostico("Capítulo II", respuestas)

    def test_capitulo_i_todo_cumplimiento_da_100_porciento(self):
        resultado = calcular_diagnostico("Capítulo I", _respuestas_aplicables("Capítulo I"))
        assert resultado.capitulo == "Capítulo I"
        assert resultado.porcentaje == pytest.approx(1.0)
        assert len([item for item in resultado.items if item.automatico]) == 53

    def test_capitulo_desconocido_lanza_error(self):
        with pytest.raises(ValueError, match="no soportado"):
            calcular_diagnostico("Capítulo IV", _respuestas_de_relleno())

    def test_capitulo_iii_se_calcula_tambien_via_dispatcher(self):
        resultado = calcular_diagnostico("Capítulo III", _respuestas_de_relleno())
        assert resultado.porcentaje == pytest.approx(1.0)
