"""Subpaquete cli: interfaz de usuario interactiva por consola."""
from agente_sgsst.cli.ingesta import solicitar_datos_usuario
from agente_sgsst.cli.main import menu_principal

__all__ = [
    "solicitar_datos_usuario",
    "menu_principal",
]
