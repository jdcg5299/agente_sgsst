from clasificacion import normalizar_riesgo_arl


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


def solicitar_datos_usuario(contexto):
    """Solicita los datos de la empresa de forma interactiva."""
    print("\n--- Por favor, proporcione los datos de la empresa ---")
    
    contexto['empresa']['razon_social'] = input("Razón Social: ")
    contexto['empresa']['nit'] = input("NIT: ")
    contexto['empresa']['direccion'] = input("Dirección: ")
    contexto['empresa']['representante_legal'] = input("Representante Legal: ")
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
