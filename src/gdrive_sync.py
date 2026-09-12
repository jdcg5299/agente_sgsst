"""Compatibilidad hacia atrás para imports directos desde src/gdrive_sync.py."""
from agente_sgsst.integrations.gdrive_sync import GoogleDriveSync

__all__ = ["GoogleDriveSync"]