"""
Ingesta automática desde el RUT / Cámara de Comercio (PDF) — Fase 1.2.

Extrae de mejor esfuerzo los datos básicos de la empresa desde el texto del PDF
para autocompletar el contexto (razon_social, nit, direccion,
representante_legal, actividad_economica). Si un campo no puede determinarse,
se devuelve vacío y la ingesta interactiva lo solicita manualmente.
"""

from __future__ import annotations

import os
import re

_NIT_DOTS = re.compile(r"\d{1,3}(?:\.\d{3})+-\d")
_NIT_LIMPIO = re.compile(r"\b\d{9,12}\b")

_CAMPOS = ("razon_social", "nit", "direccion", "representante_legal", "actividad_economica")

_CLAVES_TEXTO = {
    "razon_social": ("raz[oó]n social", "nombre o raz[oó]n social", "raz[oó]n o denominaci[oó]n"),
    "representante_legal": ("representante legal", "nombre del representante"),
    "direccion": ("direcci[oó]n", "domicilio"),
    "actividad_economica": ("actividad econ[oó]mica", "ciiu"),
    "nit": ("nit", "n[oó] identificacion", "identificaci[oó]n tributaria"),
}


def _lineas(contenido: str) -> list[str]:
    return [linea.strip() for linea in contenido.splitlines() if linea.strip()]


def _valor_de_clave(lineas: list[str], clave: str) -> str:
    """Busca la primera línea que contenga la clave y devuelve su valor.

    El valor puede estar tras un separador (':', '-') en la misma línea, o en la
    siguiente línea no vacía si esta parece contenido de valor.
    """
    patrones = _CLAVES_TEXTO[clave]
    for i, linea in enumerate(lineas):
        baja = linea.lower()
        if not any(re.search(p, baja) for p in patrones):
            continue
        resto = re.split(r"[:]\s*|\s-\s*", linea, maxsplit=1)
        if len(resto) == 2 and resto[1]:
            return resto[1].strip()
        if i + 1 < len(lineas):
            siguiente = lineas[i + 1]
            if len(siguiente) > 2 and not any(
                re.search(p, siguiente.lower()) for p in _CLAVES_TEXTO.get(clave, ())
            ):
                return siguiente
        return ""
    return ""


def _extraer_nit(texto: str) -> str:
    match = _NIT_DOTS.search(texto)
    if match:
        return match.group(0)
    match = _NIT_LIMPIO.search(texto)
    if match:
        return match.group(0)
    return ""


def extraer_datos_rut(pdf_path: str) -> dict:
    """Extrae los datos de la empresa desde un PDF de RUT/Cámara de Comercio.

    Retorna un dict con las claves de `contexto['empresa']` ('' cuando no se
    pudo determinar). Lanza FileNotFoundError si el archivo no existe.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"No se encontró el PDF: {pdf_path}")

    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    texto = "\n".join(page.extract_text() or "" for page in reader.pages)
    lineas = _lineas(texto)

    datos = {campo: _valor_de_clave(lineas, campo) for campo in _CAMPOS}
    datos["nit"] = _extraer_nit(texto)
    return datos
