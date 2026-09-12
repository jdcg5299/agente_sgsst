"""
Registro de prompts — hallazgo 5.5 de CONSTITUTION.md (Sección 5).

Antes: `generador.py` tenía el prompt del LLM hardcodeado inline en la función
`generar_documento_individual()`, sin forma de auditar ni versionar qué prompt
generó qué documento (violación del Principio VI/II: "todo prompt en producción
debe existir primero en `master_prompts.md`").

Ahora: este módulo es la ÚNICA forma de obtener un prompt en producción. Carga
`docs/master_prompts.md` una sola vez, resuelve el prompt específico del
documento (por su ID del catálogo, ej. "D-001") o cae al prompt GENERICO si el
documento aún no tiene prompt propio. Los placeholders se reemplazan con los
datos reales de la empresa (Principio III: el orquestador inyecta contexto, no
la capa de generación).

Regla estricta: si `master_prompts.md` falta, no se genera ningun documento —
fallar ruidosamente es preferible a inventar un prompt (Principio XI).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_PROYECTO_RAIZ = Path(__file__).resolve().parents[2]


def _resolver_master_prompts() -> Path:
    """Localiza `docs/master_prompts.md` de forma robusta a la ubicación del paquete.

    Se busca, en orden: (1) junto al proyecto raíz si `docs/` está en el CWD,
    (2) como recurso de datos del paquete (copia instalable), y (3) subiendo desde
    el paquete hasta encontrar un directorio `docs/`.
    """
    candidatos = [
        Path.cwd() / "docs" / "master_prompts.md",
        Path(__file__).parent / "data" / "master_prompts.md",
        *_PROYECTO_RAIZ.glob("docs/master_prompts.md"),
    ]
    for ruta in candidatos:
        if ruta.exists():
            return ruta
    raise FileNotFoundError(
        "No se localizó docs/master_prompts.md. Todo prompt de producción debe vivir "
        "en master_prompts.md (Principio VI/II de CONSTITUTION.md); sin el archivo "
        "maestro el agente NO está autorizado a generar documentos."
    )


_MASTER_PROMPTS = _resolver_master_prompts()
_PROMPT_GENERICO_KEY = "GENERICO"

# Placeholders soportados (formato [PLACEHOLDER] y {PLACEHOLDER}).
PLACEHOLDERS = (
    "RAZON_SOCIAL",
    "NIT",
    "CAPITULO",
    "RIESGO",
    "TRABAJADORES",
    "REPRESENTANTE_LEGAL",
    "ACTIVIDAD_ECONOMICA",
    "NOMBRE_DOCUMENTO",
    "ESTANDAR",
)


def _parsear_master_prompts(ruta: Path) -> dict[str, dict[str, str]]:
    """Parsea `master_prompts.md` en bloques `## [ID] Título`.

    Devuelve: { "D-001": {"nombre": ..., "estandar": ..., "prompt": ...}, ...,
    "GENERICO": {"prompt": ...} }.
    """
    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró {ruta}. Todo prompt de producción debe vivir en "
            "master_prompts.md (Principio VI/II de CONSTITUTION.md); sin el archivo "
            "maestro el agente NO está autorizado a generar documentos."
        )

    texto = ruta.read_text(encoding="utf-8")
    bloques = re.split(r"^##\s+\[([A-Z0-9-]+)\]\s*(.*)$", texto, flags=re.MULTILINE)
    # bloques: [pre, id1, titulo1, cuerpo1, id2, titulo2, cuerpo2, ...]
    registros: dict[str, dict[str, str]] = {}
    for i in range(1, len(bloques) - 2, 3):
        doc_id = bloques[i].strip()
        titulo = bloques[i + 1].strip()
        cuerpo = bloques[i + 2].strip()

        estandar_match = re.search(r"\*\*Estándar Res\.\s*0312:\*\*\s*(\S+)", cuerpo)
        prompt_match = re.search(r"\*\*Prompt:\*\*\s*(.*)$", cuerpo, flags=re.DOTALL)

        estandar = estandar_match.group(1) if estandar_match else ""
        prompt = ""
        if prompt_match:
            prompt = re.sub(r"^\s*>\s?", "", prompt_match.group(1), flags=re.MULTILINE)
        prompt = prompt.strip()

        registros[doc_id] = {"nombre": titulo, "estandar": estandar, "prompt": prompt}

    return registros


class PromptRegistry:
    """Repositorio de prompts con carga única de master_prompts.md."""

    def __init__(self, ruta_master: Path | None = None):
        self._ruta = ruta_master or _MASTER_PROMPTS
        self._registros = _parsear_master_prompts(self._ruta)
        if _PROMPT_GENERICO_KEY not in self._registros:
            raise ValueError(
                f"{self._ruta} no define el bloque [{_PROMPT_GENERICO_KEY}]. "
                "El prompt por defecto es obligatorio para los documentos del catálogo "
                "que aún no tienen un prompt propio."
            )

    def ids_disponibles(self) -> list[str]:
        return [k for k in self._registros if k != _PROMPT_GENERICO_KEY]

    def existe_prompt_especifico(self, doc_id: str) -> bool:
        return doc_id in self._registros and bool(self._registros[doc_id]["prompt"])

    def obtener_prompt_plantilla(self, doc_id: str) -> str:
        """Devuelve la plantilla específica del doc o la GENERICA si no existe."""
        if self.existe_prompt_especifico(doc_id):
            return self._registros[doc_id]["prompt"]
        return self._registros[_PROMPT_GENERICO_KEY]["prompt"]

    @staticmethod
    def renderizar(prompt_plantilla: str, datos: dict[str, Any]) -> str:
        """Reemplaza los placeholders [X] o {X} por los valores del contexto."""
        prompt = prompt_plantilla
        for clave in PLACEHOLDERS:
            valor = str(datos.get(clave, "")) if datos.get(clave) is not None else ""
            prompt = prompt.replace(f"[{clave}]", valor).replace(f"{{{clave}}}", valor)
        return prompt


_registry: PromptRegistry | None = None


def get_registry() -> PromptRegistry:
    """Singleton del registro (carga única de master_prompts.md)."""
    global _registry
    if _registry is None:
        _registry = PromptRegistry()
    return _registry


def construir_prompt(doc_id: str, empresa: dict, capitulo: str, nombre_documento: str, estandar: str) -> str:
    """Orquesta la resolución del prompt y su renderizado para un documento.

    `empresa` debe contener: razon_social, nit, representante_legal,
    actividad_economica, clase_riesgo_arl, total_trabajadores.
    """
    registry = get_registry()
    plantilla = registry.obtener_prompt_plantilla(doc_id)

    datos = {
        "RAZON_SOCIAL": empresa.get("razon_social", ""),
        "NIT": empresa.get("nit", ""),
        "CAPITULO": capitulo,
        "RIESGO": empresa.get("clase_riesgo_arl", ""),
        "TRABAJADORES": empresa.get("total_trabajadores", ""),
        "REPRESENTANTE_LEGAL": empresa.get("representante_legal", ""),
        "ACTIVIDAD_ECONOMICA": empresa.get("actividad_economica", ""),
        "NOMBRE_DOCUMENTO": nombre_documento,
        "ESTANDAR": estandar,
    }
    return registry.renderizar(plantilla, datos)