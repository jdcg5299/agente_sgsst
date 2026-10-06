"""Tests del manejo de errores del cliente LLM (sin errores crudos en documentos)."""

from __future__ import annotations

from unittest import mock

from agente_sgsst.generation.llm_client import LLMClient


def _cliente_groq():
    llm = LLMClient()
    llm.groq_key = "clave-de-prueba"
    llm.provider = "groq"
    return llm


def _respuesta_429():
    r = mock.MagicMock()
    r.status_code = 429
    r.headers = {"retry-after": "1"}
    r.text = '{"error":{"message":"Rate limit ... Please try again in 0.5s"}}'
    return r


def _respuesta_ok(contenido="OK REAL"):
    r = mock.MagicMock()
    r.status_code = 200
    r.json.return_value = {"choices": [{"message": {"content": contenido}}]}
    return r


def test_429_reintenta_y_devuelve_contenido_real():
    llm = _cliente_groq()
    llamadas = {"n": 0}

    def _post(*args, **kwargs):
        llamadas["n"] += 1
        return _respuesta_ok() if llamadas["n"] >= 3 else _respuesta_429()

    with (
        mock.patch("agente_sgsst.generation.llm_client.requests.post", side_effect=_post),
        mock.patch("agente_sgsst.generation.llm_client.time.sleep"),
    ):
        salida = llm.generar_texto("pregunta")

    assert salida == "OK REAL"
    assert llamadas["n"] == 3


def test_429_persistente_cae_a_simulado_sin_error_crudo():
    llm = _cliente_groq()
    with (
        mock.patch(
            "agente_sgsst.generation.llm_client.requests.post",
            side_effect=lambda *a, **k: _respuesta_429(),
        ),
        mock.patch("agente_sgsst.generation.llm_client.time.sleep"),
    ):
        salida = llm.generar_texto("pregunta")

    assert "Error en" not in salida
    assert "Modo Simulación" in salida
    assert salida.strip()


def test_error_http_no_incrusta_json_de_error_en_el_texto():
    llm = _cliente_groq()
    r = mock.MagicMock()
    r.status_code = 500
    r.json.return_value = {"error": {"message": "detalle interno secreto"}}
    with (
        mock.patch("agente_sgsst.generation.llm_client.requests.post", side_effect=lambda *a, **k: r),
        mock.patch("agente_sgsst.generation.llm_client.time.sleep"),
    ):
        salida = llm.generar_texto("pregunta")

    assert "detalle interno secreto" not in salida
    assert "Simulación" in salida


def test_sin_claves_genera_directamente_en_simulado():
    llm = LLMClient()
    llm.groq_key = ""
    llm.openai_key = ""
    llm.gemini_key = ""
    llm.provider = "simulado"

    salida = llm.generar_texto("pregunta")

    assert "Modo Simulación" in salida
