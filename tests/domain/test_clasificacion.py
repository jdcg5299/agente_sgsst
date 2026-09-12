"""
Tests del módulo de clasificación corregido.

Estructura TDD: cada bloque "Reproducción del bug original" primero demuestra,
con el código EXACTO que estaba en el `clasificacion.py` subido, que el defecto
existe — y luego el bloque "Corrección verificada" prueba que el nuevo
`src/domain/clasificacion.py` ya no lo tiene. Así queda documentado en el propio
test suite qué se rompía y por qué, no solo que "ahora pasa".
"""
from __future__ import annotations

import pytest

from agente_sgsst.domain.clasificacion import (
    CAPITULO_II_CONTEO_VERIFICADO,
    RiesgoARL,
    clasificar_empresa,
    get_applicable_items,
)


# ---------------------------------------------------------------------------
# Reproducción del bug original (hallazgo 5.1) — código EXACTO de clasificacion.py
# tal como fue subido, aislado aquí solo para dejar la regresión documentada.
# ---------------------------------------------------------------------------
def _get_applicable_items_original_con_bug(capitulo):
    items_capitulo_1 = {"1.1.1", "1.1.4", "1.2.1", "2.1.1", "2.2.1", "2.4.1", "2.5.1"}
    items_capitulo_2 = {
        "1.1.1", "1.1.2", "1.1.4", "1.1.6", "1.1.8", "1.2.1",
        "2.1.1", "2.2.1", "2.3.1", "2.4.1", "2.5.1", "2.6.1", "2.7.1", "2.8.1", "2.11.1",
        "3.1.1", "3.1.2", "3.2.1", "3.2.2", "3.3.1", "4.1.1", "4.2.1",
    }
    if capitulo == "Capítulo I":
        return items_capitulo_1
    elif capitulo == "Capítulo II":
        return items_capitulo_2
    else:
        return {str(i) for i in range(1, 61)}  # <- el bug: "1".."60", no numerales reales


class TestReproduccionHallazgo51:
    def test_el_bug_original_marca_todo_como_no_aplica_en_capitulo_iii(self):
        """Demuestra el hallazgo 5.1 tal como se documentó en CONSTITUTION.md."""
        aplicables_originales = _get_applicable_items_original_con_bug("Capítulo III")
        numerales_reales = ["1.1.1", "2.1.1", "4.1.1", "6.1.4"]

        # Con el código original, NINGÚN numeral real aparece en el set "aplicables"
        # de Capítulo III -> diagnostico.py los pintaría TODOS de amarillo.
        for numeral in numerales_reales:
            assert numeral not in aplicables_originales, (
                f"Si esto falla, el bug original ya no está presente en la función "
                f"de referencia (no debería pasar, es código congelado para el test)"
            )


class TestCorreccionHallazgo51:
    def test_capitulo_iii_retorna_numerales_reales_con_puntos(self):
        aplicables = get_applicable_items("Capítulo III")
        for numeral in ["1.1.1", "2.1.1", "4.1.1", "6.1.4", "7.1.4"]:
            assert numeral in aplicables

    def test_capitulo_iii_tiene_exactly_60_numerales(self):
        assert len(get_applicable_items("Capítulo III")) == 60

    def test_capitulo_iii_ya_no_contiene_indices_enteros_de_relleno(self):
        aplicables = get_applicable_items("Capítulo III")
        assert "1" not in aplicables
        assert "60" not in aplicables

    def test_capitulo_iii_coincide_con_la_tabla_de_ponderacion(self):
        """Misma fuente de datos que el motor de ponderación — sin duplicación (DRY)."""
        import json
        from pathlib import Path

        ruta = Path(__file__).parents[2] / "src/agente_sgsst/domain/data/estandares_0312_capitulo_iii.json"
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        numerales_tabla = {item["numeral"] for item in datos["items"]}
        assert get_applicable_items("Capítulo III") == numerales_tabla


class TestHallazgo52DiscrepanciaCapituloII:
    def test_capitulo_ii_tiene_22_items_no_21_como_dice_la_fuente(self):
        """Documenta la discrepancia en vez de ocultarla (hallazgo 5.2)."""
        aplicables = get_applicable_items("Capítulo II")
        assert len(aplicables) == 22  # la fuente checklist trae 22, pese a decir "21"

    def test_bandera_de_conteo_verificado_es_falsa(self):
        """La bandera debe advertir explícitamente que el conteo no está conciliado
        contra el anexo oficial — no debe pasar desapercibido como si fuera correcto."""
        assert CAPITULO_II_CONTEO_VERIFICADO is False

    def test_capitulo_i_si_tiene_el_conteo_correcto(self):
        assert len(get_applicable_items("Capítulo I")) == 7


class TestHallazgo513RepresentacionDeRiesgo:
    def test_acepta_formato_oficial_romano(self):
        assert clasificar_empresa(5, "III") == "Capítulo I"

    def test_acepta_formato_numerico_por_compatibilidad(self):
        # Mismo resultado con 3 (numérico, como usa ingesta.py hoy) que con "III"
        assert clasificar_empresa(5, 3) == clasificar_empresa(5, "III")

    def test_acepta_enum_directamente(self):
        assert clasificar_empresa(5, RiesgoARL.III) == "Capítulo I"

    def test_riesgo_invalido_lanza_error_explicito(self):
        with pytest.raises(ValueError, match="Clase de riesgo ARL inválida"):
            clasificar_empresa(5, "VI")

    def test_riesgo_numerico_fuera_de_rango_lanza_error(self):
        with pytest.raises(ValueError, match="Clase de riesgo ARL inválida"):
            clasificar_empresa(5, 9)


class TestHallazgo514ValidacionDeTrabajadores:
    def test_cero_trabajadores_ya_no_se_acepta_silenciosamente(self):
        """Antes: 0 trabajadores + riesgo <=3 devolvía 'Capítulo I' sin avisar."""
        with pytest.raises(ValueError, match="entero positivo"):
            clasificar_empresa(0, "I")

    def test_trabajadores_negativos_lanza_error(self):
        with pytest.raises(ValueError, match="entero positivo"):
            clasificar_empresa(-3, "I")


class TestClasificarEmpresaFronteras:
    """Los mismos casos límite verificados en el motor original de la sesión anterior,
    ahora contra la versión integrada a src/domain/."""

    def test_frontera_10_vs_11(self):
        assert clasificar_empresa(10, "I") == "Capítulo I"
        assert clasificar_empresa(11, "I") == "Capítulo II"

    def test_frontera_50_vs_51(self):
        assert clasificar_empresa(50, "I") == "Capítulo II"
        assert clasificar_empresa(51, "I") == "Capítulo III"

    @pytest.mark.parametrize("trabajadores", [1, 10, 11, 50])
    def test_riesgo_alto_siempre_capitulo_iii(self, trabajadores):
        assert clasificar_empresa(trabajadores, "IV") == "Capítulo III"
        assert clasificar_empresa(trabajadores, "V") == "Capítulo III"
