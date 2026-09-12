"""Subpaquete generation: clientes de LLM y registro de prompts."""
from agente_sgsst.generation.llm_client import LLMClient
from agente_sgsst.generation.prompt_registry import (
    PromptRegistry,
    construir_prompt,
    get_registry,
)

__all__ = [
    "LLMClient",
    "PromptRegistry",
    "construir_prompt",
    "get_registry",
]
