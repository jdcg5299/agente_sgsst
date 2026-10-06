"""
Sincronizador avanzado con Google Drive (OAuth 2.0).
Replica la estructura jerárquica PHVA (Planear, Hacer, Verificar, Actuar)
y evita re-subir archivos ya existentes.
"""

import os
import pickle
import json
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
_CACHE_PATH = ".gdrive_cache.json"


class GoogleDriveSync:
    """
    Sincronizador de la estructura SG-SST con Google Drive usando OAuth 2.0.
    Replicación jerárquica y caché de archivos subidos.
    """

    def __init__(self, credentials_path="credentials.json", token_path="token.pickle"):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = self._autenticar()
        self.cache = self._cargar_cache()

    def _autenticar(self):
        creds = None
        if os.path.exists(self.token_path):
            with open(self.token_path, "rb") as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    creds = None
            if not creds:
                if os.path.exists(self.credentials_path):
                    try:
                        flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                        creds = flow.run_local_server(port=0)
                    except Exception as e:
                        print(f"Error en flujo OAuth local: {e}")
                        return None
                else:
                    print("Aviso: No se encontró 'credentials.json'. Google Drive operará en modo simulado.")
                    return None

            with open(self.token_path, "wb") as token:
                pickle.dump(creds, token)

        try:
            return build("drive", "v3", credentials=creds)
        except Exception as e:
            print(f"Error al conectar con Google Drive API: {str(e)}")
            return None

    def _cargar_cache(self):
        if os.path.exists(_CACHE_PATH):
            try:
                with open(_CACHE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _guardar_cache(self):
        try:
            with open(_CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, indent=2)
        except Exception:
            pass

    def obtener_o_crear_carpeta(self, nombre, parent_id=None):
        if not self.service:
            return f"simulated_id_{nombre}"

        # Buscar si ya existe la carpeta en el parent
        query = f"name='{nombre}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        else:
            query += " and 'root' in parents"

        results = self.service.files().list(q=query, spaces="drive", fields="files(id, name)").execute()
        files = results.get("files", [])
        if files:
            return files[0]["id"]

        # Si no existe, crearla
        file_metadata = {"name": nombre, "mimeType": "application/vnd.google-apps.folder"}
        if parent_id:
            file_metadata["parents"] = [parent_id]

        file = self.service.files().create(body=file_metadata, fields="id").execute()
        return file.get("id")

    def subir_archivo(self, ruta_local, parent_id=None):
        if not self.service:
            print(f"[Simulación GDrive] Subido: {ruta_local}")
            return "simulated_file_id"

        nombre_archivo = os.path.basename(ruta_local)
        mtime_local = os.path.getmtime(ruta_local)

        # Verificar caché para omitir subida si no ha cambiado
        cache_key = f"{parent_id}_{nombre_archivo}"
        if cache_key in self.cache and self.cache[cache_key].get("mtime") == mtime_local:
            print(f"Omitido (sin cambios): {nombre_archivo}")
            return self.cache[cache_key].get("file_id")

        # Verificar si ya existe en Drive
        query = f"name='{nombre_archivo}' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        results = self.service.files().list(q=query, spaces="drive", fields="files(id, name)").execute()
        files = results.get("files", [])

        media = MediaFileUpload(ruta_local, resumable=True)
        if files:
            file_id = files[0]["id"]
            # Actualizar archivo existente
            file = self.service.files().update(fileId=file_id, media_body=media).execute()
            print(f"Actualizado en Google Drive: {nombre_archivo} (ID: {file.get('id')})")
        else:
            # Crear archivo nuevo
            file_metadata = {"name": nombre_archivo}
            if parent_id:
                file_metadata["parents"] = [parent_id]
            file = self.service.files().create(body=file_metadata, media_body=media, fields="id").execute()
            print(f"Subido a Google Drive: {nombre_archivo} (ID: {file.get('id')})")

        file_id = file.get("id")
        self.cache[cache_key] = {"file_id": file_id, "mtime": mtime_local}
        self._guardar_cache()
        return file_id

    def sincronizar_directorio(self, raiz_local="sistema_gestion", drive_root_name="Sistema_Gestion_SGSST"):
        """
        Sincroniza recursivamente la carpeta local con Google Drive manteniendo la estructura PHVA.
        Omitiendo archivos ya subidos y sin cambios.
        """
        if not self.service:
            print("Sincronización con Google Drive simulada correctamente.")
            return

        print(f"Iniciando sincronización jerárquica de '{raiz_local}' con Google Drive...")
        root_id = self.obtener_o_crear_carpeta(drive_root_name)

        # Mapeo de rutas relativas a IDs de carpetas en Drive
        folder_id_map = {"": root_id}

        for dirpath, dirnames, filenames in os.walk(raiz_local):
            rel_path = os.path.relpath(dirpath, raiz_local)
            if rel_path == ".":
                current_parent_id = root_id
            else:
                # Construir o buscar carpetas padres jerárquicamente
                partes = rel_path.split(os.sep)
                parent_key = ""
                curr_id = root_id
                for parte in partes:
                    parent_key = os.path.join(parent_key, parte) if parent_key else parte
                    if parent_key not in folder_id_map:
                        folder_id_map[parent_key] = self.obtener_o_crear_carpeta(parte, parent_id=curr_id)
                    curr_id = folder_id_map[parent_key]
                current_parent_id = curr_id

            for filename in filenames:
                ruta_completa = os.path.join(dirpath, filename)
                if os.path.isfile(ruta_completa):
                    self.subir_archivo(ruta_completa, parent_id=current_parent_id)

        print("Sincronización jerárquica con Google Drive completada con éxito.")
