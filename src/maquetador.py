def get_header_ft_sst_002(nombre_documento, codigo_formato, estandar_res, empresa_nombre, fecha):
    """
    Retorna el encabezado estandarizado bajo FT-SST-002 en formato Markdown.

    Corrige el hallazgo 5.8 de CONSTITUTION.md: la fecha era un literal duro
    ("31/08/2026") en cada encabezado. Ahora se recibe como parámetro
    (datetime.now() se genera en la capa de orquestación, no aquí) para mantener
    esta función pura y testeable.
    """
    return f"""| Logo | SISTEMA DE GESTIÓN DE SEGURIDAD Y SALUD EN EL TRABAJO | CÓDIGO: {codigo_formato} |
| :---: | :--- | :---: |
| | **{nombre_documento}** | **VERSIÓN:** 01 |
| | **ESTÁNDAR RES. 0312:** {estandar_res} | **FECHA:** {fecha} |
| | **EMPRESA:** {empresa_nombre} | **PÁGINA:** 1 de 1 |
"""