"""Tests del parser de RUT / Cámara de Comercio (Fase 1.2)."""

from __future__ import annotations

import pytest

from agente_sgsst.cli.rut import _lineas, _valor_de_clave, _extraer_nit, extraer_datos_rut


TEXTO_EJEMPLO = """
RAZON SOCIAL: EMPRESA PRUEBA SAS
RUT 901.123.456-7
DIRECCION: Calle 1 # 2-3
REPRESENTANTE LEGAL: Juan Perez Gomez
ACTIVIDAD ECONOMICA: Comercio al por mayor
"""


class TestLineas:
    def test_filtra_vacias_y_recorta(self):
        assert _lineas("  a  \n\n b \n") == ["a", "b"]


class TestValorDeClave:
    def test_extrae_valor_tras_dos_puntos(self):
        lineas = _lineas(TEXTO_EJEMPLO)
        assert _valor_de_clave(lineas, "razon_social") == "EMPRESA PRUEBA SAS"

    def test_extrae_direccion(self):
        assert _valor_de_clave(_lineas(TEXTO_EJEMPLO), "direccion") == "Calle 1 # 2-3"

    def test_extrae_representante_legal(self):
        assert _valor_de_clave(_lineas(TEXTO_EJEMPLO), "representante_legal") == "Juan Perez Gomez"

    def test_devuelve_vacio_si_no_hay_clave(self):
        assert _valor_de_clave(["SIN DATOS"], "razon_social") == ""


class TestExtraerNit:
    def test_nit_con_puntos_y_digito(self):
        assert _extraer_nit("NIT 901.123.456-7 del contribuyente") == "901.123.456-7"

    def test_nit_numerico_largo(self):
        assert _extraer_nit("Documento: 900123456") == "900123456"

    def test_sin_nit(self):
        assert _extraer_nit("no hay identificador") == ""


class TestExtraerDatosRut:
    def test_archivo_inexistente_lanza_error(self):
        with pytest.raises(FileNotFoundError):
            extraer_datos_rut("no/existe.pdf")
