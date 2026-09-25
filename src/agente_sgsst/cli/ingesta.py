from agente_sgsst.domain.clasificacion import normalizar_riesgo_arl

_LOGO_EXTENSIONES_VALIDAS = {".png", ".jpg", ".jpeg"}


def _capturar_riesgo_arl():
    """Captura la clase de riesgo ARL aceptando formato romano (I-V) o numérico (1-5).

    Corrige el hallazgo 5.13: el valor canónico almacenado es el numeral romano
    (formato oficial), no el entero — así los prompts al LLM y los documentos
    generados muestran "III" en vez de "3".
    """
    while True:
        entrada = input("Clase de Riesgo ARL (I-V o 1-5): ").strip()
        try:
            return normalizar_riesgo_arl(entrada).value
        except ValueError as e:
            print(f"Entrada no válida. {e}")


def _capturar_logo():
    """Captura la ruta del logo institucional (hallazgo 5.9).

    Solicita la ruta de la imagen PNG/JPG. Admite vacío (Enter): se usará el
    texto placeholder 'Logo' en el encabezado FT-SST-002.
    """
    import os

    while True:
        ruta = input("Ruta del logo institucional (PNG/JPG, Enter para omitir): ").strip()
        if not ruta:
            return ""
        if not os.path.exists(ruta):
            print("La ruta no existe. Verifique el archivo e intente de nuevo.")
            continue
        if os.path.splitext(ruta)[1].lower() not in _LOGO_EXTENSIONES_VALIDAS:
            print("Formato no soportado. Use PNG o JPG.")
            continue
        return ruta


def _capturar_datos_desde_rut(contexto):
    """Autocompleta datos de la empresa desde el RUT/Cámara de Comercio (Fase 1.2).

    Si el usuario entrega un PDF válido y pypdf logra leer texto, se rellenan los
    campos encontrados; los restantes siguen vacíos para pedirse manualmente.
    """
    ruta = input("Ruta del RUT / Cámara de Comercio en PDF (Enter para omitir): ").strip()
    if not ruta:
        return contexto

    from agente_sgsst.cli.rut import extraer_datos_rut

    try:
        datos = extraer_datos_rut(ruta)
        extraidos = {k: v for k, v in datos.items() if v}
        if extraidos:
            for campo, valor in extraidos.items():
                contexto['empresa'][campo] = valor
            print(f"Datos autocompletados desde el PDF: {', '.join(sorted(extraidos))}")
        else:
            print("No se logró extraer datos del PDF. Complete los datos manualmente.")
    except Exception as e:
        print(f"Error al leer el PDF ({str(e)}). Complete los datos manualmente.")
    return contexto


def solicitar_datos_usuario(contexto):
    """Solicita los datos de la empresa de forma interactiva."""
    print("\n--- Por favor, proporcione los datos de la empresa ---")
    
    contexto['empresa']['logo'] = _capturar_logo()
    contexto = _capturar_datos_desde_rut(contexto)

    if not contexto['empresa']['razon_social']:
        contexto['empresa']['razon_social'] = input("Razón Social: ")
    if not contexto['empresa']['nit']:
        contexto['empresa']['nit'] = input("NIT: ")
    if not contexto['empresa']['direccion']:
        contexto['empresa']['direccion'] = input("Dirección: ")
    if not contexto['empresa']['representante_legal']:
        contexto['empresa']['representante_legal'] = input("Representante Legal: ")
    if not contexto['empresa']['actividad_economica']:
        contexto['empresa']['actividad_economica'] = input("Actividad Económica Principal: ")
    
    contexto['empresa']['clase_riesgo_arl'] = _capturar_riesgo_arl()
            
    while True:
        try:
            contexto['empresa']['total_trabajadores'] = int(input("Número total de trabajadores: "))
            if contexto['empresa']['total_trabajadores'] > 0:
                break
            print("El número de trabajadores debe ser mayor a 0 (entero positivo).")
        except ValueError:
            print("Entrada no válida. Por favor, ingrese un número entero.")

    return contexto
