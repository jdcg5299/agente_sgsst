"""Compatibilidad hacia atrás para imports directos desde src/llm_client.py."""
from agente_sgsst.generation.llm_client import LLMClient

__all__ = ["LLMClient"]