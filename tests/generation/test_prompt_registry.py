"""
Tests del registro de prompts (hallazgo 5.5 de CONSTITUTION.md).

Antes el prompt estaba hardcodeado inline en `generador.py` (violando el
Principio VI/II: "todo prompt en producción debe existir primero en
master_prompts.md"). Estos tests verifican que la resolución de prompts pasa
única y exclusivamente por el registro, con fallback al prompt GENERICO y
sin prompts inventados.
"""
from __future__ import annotations

import pytest

from agente_sgsst.generation.prompt_registry import (
    PromptRegistry,
    construir_prompt,
    get_registry,
)

_EMPRESA_EJEMPLO = {
    "razon_social": "EMPRESA PRUEBA SAS",
    "nit": "900.123.456-7",
    "representante_legal": "JUANA PEREZ",
    "actividad_economica": "Comercio al por menor",
    "clase_riesgo_arl": "III",
    "total_trabajadores": 45,
}


class TestRegistroReal:
    def test_registro_singleton_carga_master_prompts(self):
        registry = get_registry()
        assert "D-001" in registry.ids_disponibles()
        assert "GENERICO" in registry._registros  # interna, pero clave de contrato

    def test_prompt_especifico_d001_no_es_el_generico(self):
        registry = get_registry()
        especifico = registry.obtener_prompt_plantilla("D-001")
        generico = registry.obtener_prompt_plantilla("NO_EXISTE")
        assert especifico != generico
        assert "Acta de Asignación" in especifico or "Acta de Asignacion" in especifico

    def test_fallback_al_generico_para_doc_sin_prompt_propio(self):
        registry = get_registry()
        plantilla = registry.obtener_prompt_plantilla("D-999")
        assert "[NOMBRE_DOCUMENTO]" in plantilla  # sigue siendo plantilla sin renderizar


class TestRenderizado:
    def test_placeholders_especificos_reemplazados(self):
        prompt = construir_prompt(
            doc_id="D-001",
            empresa=_EMPRESA_EJEMPLO,
            capitulo="Capítulo II",
            nombre_documento="Acta de Asignacion del Responsable SST",
            estandar="E1.1.1",
        )
        assert "EMPRESA PRUEBA SAS" in prompt
        assert "900.123.456-7" in prompt
        assert "Capítulo II" in prompt
        assert "JUANA PEREZ" in prompt
        assert "[RAZON_SOCIAL]" not in prompt  # ningún placeholder sin resolver

    def test_placeholder_actividad_y_riesgo_en_iparv(self):
        prompt = construir_prompt(
            doc_id="D-036",
            empresa=_EMPRESA_EJEMPLO,
            capitulo="Capítulo II",
            nombre_documento="Matriz IPARV (GTC 45)",
            estandar="E4.1.1",
        )
        assert "Comercio al por menor" in prompt
        assert "III" in prompt


class TestFailLoudSinMasterPrompts:
    def test_master_prompts_ausente_lanza_error(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="master_prompts"):
            PromptRegistry(ruta_master=tmp_path / "inexistente.md")

    def test_master_sin_generico_lanza_error(self, tmp_path):
        mal = tmp_path / "master_prompts.md"
        mal.write_text(
            "## [D-001] Acta\n- **Estándar Res. 0312:** E1.1.1\n- **Prompt:**\n> hola\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="GENERICO"):
            PromptRegistry(ruta_master=mal)