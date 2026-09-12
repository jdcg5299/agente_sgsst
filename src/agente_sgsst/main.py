"""Punto de entrada del Agente SG-SST (CLI interactiva)."""
import os
import json
import shutil

from agente_sgsst.cli.ingesta import solicitar_datos_usuario
from agente_sgsst.rendering.diagnostico import generar_diagnostico_base
from agente_sgsst.generador import generar_documento_individual, generar_documentos_por_capitulo, cargar_catalogo

# Configuración básica
CONTEXTO_PATH = "data/contexto_empresa.json"
DATA_TEMPLATE = "data/contexto_empresa_template.json"

def asegurar_estructura():
    """Crea la estructura de carpetas si no existe."""
    carpetas = [
        "sistema_gestion/01_PLANEAR/1.1_Recursos",
        "sistema_gestion/01_PLANEAR/1.2_Gestion_Integral",
        "sistema_gestion/02_HACER/2.1_Gestion_Salud",
        "sistema_gestion/02_HACER/2.2_ATEL",
        "sistema_gestion/02_HACER/2.3_Peligros_Riesgos",
        "sistema_gestion/02_HACER/2.4_Operacion_Seguridad",
        "sistema_gestion/03_VERIFICAR/3.1_Verificacion",
        "sistema_gestion/04_ACTUAR/4.1_Mejoramiento",
        "sistema_gestion/99_INFORMES_EJECUTIVOS"
    ]
    for carpeta in carpetas:
        os.makedirs(carpeta, exist_ok=True)

def cargar_o_crear_contexto():
    """Carga el contexto o crea uno nuevo desde la plantilla."""
    if not os.path.exists(CONTEXTO_PATH):
        print("Creando nuevo contexto de empresa...")
        shutil.copy(DATA_TEMPLATE, CONTEXTO_PATH)
    
    with open(CONTEXTO_PATH, 'r') as f:
        return json.load(f)

def guardar_contexto(contexto):
    """Guarda el contexto actualizado."""
    with open(CONTEXTO_PATH, 'w') as f:
        json.dump(contexto, f, indent=2)

def mostrar_menu():
    """Muestra el menú principal."""
    print("\n" + "="*60)
    print("     AGENTE SG-SST - MENÚ PRINCIPAL")
    print("="*60)
    print("1. Generar Sistema Integral Completo")
    print("2. Generar Documento Individual (Bajo Demanda)")
    print("3. Listar Documentos Disponibles")
    print("4. Actualizar Datos de la Empresa")
    print("5. Ver Estado Actual")
    print("6. Sincronizar con Google Drive")
    print("0. Salir")
    print("-"*60)

def listar_documentos():
    """Muestra los documentos disponibles en el catálogo."""
    catalogo = cargar_catalogo()
    print("\n--- DOCUMENTOS DISPONIBLES EN CATÁLOGO ---")
    for doc_id, info in catalogo.items():
        print(f"  {doc_id}: {info['nombre']} (Estándar: {info['estandar']})")

def menu_principal(contexto):
    """Bucle principal del menú interactivo."""
    while True:
        mostrar_menu()
        opcion = input("Seleccione una opción: ").strip()
        
        if opcion == "1":
            print("\n--- GENERANDO SISTEMA INTEGRAL COMPLETO ---")
            contexto = generar_diagnostico_base(contexto)
            generar_documentos_por_capitulo(contexto)
            guardar_contexto(contexto)
            print("Sistema Integral generado exitosamente.")
            
        elif opcion == "2":
            listar_documentos()
            doc_id = input("\nIngrese el ID del documento a generar (ej: D-001): ").strip().upper()
            if doc_id:
                if generar_documento_individual(contexto, doc_id):
                    guardar_contexto(contexto)
                    print("\nDocumento generado exitosamente.")
                else:
                    print("Error al generar el documento.")
            else:
                print("ID no valido.")
                
        elif opcion == "3":
            listar_documentos()
            
        elif opcion == "4":
            print("\n--- ACTUALIZANDO DATOS DE LA EMPRESA ---")
            contexto = solicitar_datos_usuario(contexto)
            guardar_contexto(contexto)
            print("Datos actualizados.")
            
        elif opcion == "5":
            print(f"\n--- ESTADO ACTUAL ---")
            print(f"Empresa: {contexto['empresa']['razon_social']}")
            print(f"NIT: {contexto['empresa']['nit']}")
            print(f"Capítulo: {contexto['estado_sistema'].get('capitulo_aplicable', 'No determinado')}")
            print(f"Documentos generados: {len(contexto['estado_sistema'].get('documentos_generados', []))}")
            
        elif opcion == "6":
            print("\n--- SINCRONIZANDO CON GOOGLE DRIVE ---")
            from agente_sgsst.integrations.gdrive_sync import GoogleDriveSync
            sync = GoogleDriveSync()
            sync.sincronizar_directorio()
            print("Sincronización finalizada.")

        elif opcion == "0":
            print("\n¡Hasta luego!")
            break
            
        else:
            print("Opción no válida. Intente nuevamente.")

def main():
    """Punto de entrada principal para el comando de terminal o script."""
    print("--- Motor del Agente SG-SST ---")
    
    asegurar_estructura()
    contexto = cargar_o_crear_contexto()
    
    # Ingesta interactiva solo si no hay datos
    if not contexto['empresa']['razon_social']:
        contexto = solicitar_datos_usuario(contexto)
        guardar_contexto(contexto)
    
    # Ejecutar diagnóstico inicial (Paso 1) si no existe
    if not contexto['estado_sistema'].get('capitulo_aplicable'):
        contexto = generar_diagnostico_base(contexto)
        guardar_contexto(contexto)
        print("Paso 1 (Diagnóstico) completado.")
    
    # Entrar al menú principal
    menu_principal(contexto)

if __name__ == "__main__":
    main()