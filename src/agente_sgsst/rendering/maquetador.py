import os
import re

_IMAGEN_MARKDOWN = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)$")


def _celda_markdown(texto) -> str:
    """Deja un texto listo para una celda de tabla Markdown.

    `|` cerraría la celda y rompería la tabla, y el HTML crudo (`<script>`, etc.)
    se ejecutaría en los visores que permiten HTML. Se neutraliza con entidades,
    que el visor muestra como el carácter original.
    """
    return (
        str(texto or "")
        .replace("&", "&amp;")
        .replace("|", "&#124;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _celda_logo(logo_path):
    """Devuelve el contenido Markdown de la celda de logo.

    Corrige el hallazgo 5.9 de CONSTITUTION.md: si se dispone de una ruta válida
    al logo institucional (PNG/JPG), se incrusta la imagen `![Logo](ruta)` en el
    encabezado; de lo contrario se mantiene el texto placeholder 'Logo'.
    """
    if isinstance(logo_path, str) and logo_path and os.path.exists(logo_path):
        return f"![Logo]({logo_path})"
    return "Logo"


def get_header_ft_sst_002(
    nombre_documento, codigo_formato, estandar_res, empresa_nombre, fecha, logo_path=None
):
    """
    Retorna el encabezado estandarizado bajo FT-SST-002 en formato Markdown.

    Corrige el hallazgo 5.8 de CONSTITUTION.md: la fecha era un literal duro
    ("31/08/2026") en cada encabezado. Ahora se recibe como parámetro
    (datetime.now() se genera en la capa de orquestación, no aquí) para mantener
    esta función pura y testeable.

    Hallazgo 5.9: la celda 'Logo' ahora admite la ruta del logo institucional
    (parámetro opcional `logo_path`) e incrusta la imagen en el Markdown.

    `empresa_nombre` es texto capturado en un formulario, por eso pasa por
    `_celda_markdown`: no debe poder romper la tabla ni inyectar HTML en el .md.
    """
    return (
        f"| {_celda_logo(logo_path)} | SISTEMA DE GESTIÓN DE SEGURIDAD Y SALUD EN EL TRABAJO | "
        f"CÓDIGO: {codigo_formato} |\n"
        "| :---: | :--- | :---: |\n"
        f"| | **{nombre_documento}** | **VERSIÓN:** 01 |\n"
        f"| | **ESTÁNDAR RES. 0312:** {estandar_res} | **FECHA:** {fecha} |\n"
        f"| | **EMPRESA:** {_celda_markdown(empresa_nombre)} | **PÁGINA:** 1 de 1 |\n"
    )
