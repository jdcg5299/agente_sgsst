import os
import json
from datetime import datetime
from agente_sgsst.rendering.maquetador import get_header_ft_sst_002
from agente_sgsst.generation.llm_client import LLMClient
from agente_sgsst.rendering.converter import convertir_markdown_a_docx
from agente_sgsst.generation.prompt_registry import construir_prompt

llm = LLMClient()

def cargar_catalogo():
    return {
        "D-001": {"estandar": "1.1.1", "nombre": "Acta de asignacion del responsable SST", "carpeta": "01_PLANEAR/1.1_Recursos", "codigo": "FT-SST-002"},
        "D-002": {"estandar": "1.1.2", "nombre": "Manual de funciones con responsabilidades SST", "carpeta": "01_PLANEAR/1.1_Recursos", "codigo": "FT-SST-003"},
        "D-003": {"estandar": "1.1.3", "nombre": "Presupuesto anual de SST", "carpeta": "01_PLANEAR/1.1_Recursos", "codigo": "FT-SST-004"},
        "D-004": {"estandar": "1.1.4", "nombre": "Certificado de afiliacion al Sistema de Seguridad Social", "carpeta": "01_PLANEAR/1.1_Recursos", "codigo": "FT-SST-005"},
        "D-012": {"estandar": "2.1.1", "nombre": "Politica de SST", "carpeta": "01_PLANEAR/1.2_Gestion_Integral", "codigo": "FT-SST-012"},
        "D-013": {"estandar": "2.2.1", "nombre": "Fichas de objetivos de SST", "carpeta": "01_PLANEAR/1.2_Gestion_Integral", "codigo": "FT-SST-013"},
        "D-014": {"estandar": "2.3.1", "nombre": "Evaluacion Inicial SG-SST (FT-SST-001)", "carpeta": "99_INFORMES_EJECUTIVOS", "codigo": "FT-SST-001"},
        "D-015": {"estandar": "2.4.1", "nombre": "Plan Anual de Trabajo", "carpeta": "01_PLANEAR/1.2_Gestion_Integral", "codigo": "FT-SST-015"},
        "D-018": {"estandar": "2.7.1", "nombre": "Matriz de requisitos legales", "carpeta": "01_PLANEAR/1.2_Gestion_Integral", "codigo": "FT-SST-018"},
        "D-036": {"estandar": "4.1.1", "nombre": "Matriz IPARV (GTC 45)", "carpeta": "02_HACER/2.3_Peligros_Riesgos", "codigo": "FT-SST-036"},
        "D-044": {"estandar": "4.2.5", "nombre": "Plan de Emergencias", "carpeta": "02_HACER/2.4_Operacion_Seguridad", "codigo": "FT-SST-044"},
    }

def obtener_documento(doc_id):
    catalogo = cargar_catalogo()
    return catalogo.get(doc_id)

def generar_documento_individual(contexto, doc_id):
    """
    Genera un documento individual utilizando el LLM conectado y exporta tanto en .md como en .docx
    aplicando el estándar FT-SST-002.
    """
    doc_info = obtener_documento(doc_id)
    if not doc_info:
        print(f"Error: Documento {doc_id} no encontrado en catálogo.")
        return False
    
    empresa = contexto['empresa']
    capitulo = contexto['estado_sistema'].get('capitulo_aplicable', 'Capítulo I')

    # El prompt NO se hardcodea aquí (hallazgo 5.5): se resuelve y versiona desde
    # docs/master_prompts.md vía el registro de prompts.
    estandar_ref = f"E{doc_info['estandar']}"
    prompt = construir_prompt(
        doc_id=doc_id,
        empresa=empresa,
        capitulo=capitulo,
        nombre_documento=doc_info['nombre'],
        estandar=estandar_ref,
    )
    
    print(f"Generando contenido con IA para: {doc_info['nombre']}...")
    contenido_ia = llm.generar_texto(prompt)
    
    header = get_header_ft_sst_002(
        doc_info['nombre'].upper(),
        doc_info['codigo'],
        f"E{doc_info['estandar']}",
        empresa['razon_social'],
        fecha=datetime.now().strftime("%d/%m/%Y"),
    )
    
    # Estructura final Markdown
    markdown_content = f"""# {doc_info['nombre']}

{header.strip()}

{contenido_ia}

---
*Documento generado y certificado por Agente IA SG-SST (Decreto 1072 / Res. 0312)*
"""
    
    # Guardar en la carpeta correspondiente
    ruta_carpeta = f"sistema_gestion/{doc_info['carpeta']}"
    os.makedirs(ruta_carpeta, exist_ok=True)
    
    base_filename = f"{ruta_carpeta}/{doc_info['codigo']}_{doc_info['nombre'].replace(' ', '_')}"
    md_file = f"{base_filename}.md"
    docx_file = f"{base_filename}.docx"
    
    # Escribir Markdown
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
        
    print(f"Guardado Markdown: {md_file}")
    
    # Convertir a Word (.docx) usando la plantilla FT-SST-002 de referencia
    convertir_markdown_a_docx(md_file, docx_file)
    
    if doc_id not in contexto['estado_sistema']['documentos_generados']:
        contexto['estado_sistema']['documentos_generados'].append(doc_id)
    
    return True

def generar_documentos_por_capitulo(contexto):
    catalogo = cargar_catalogo()
    generados = 0
    for doc_id in catalogo.keys():
        if generar_documento_individual(contexto, doc_id):
            generados += 1
    print(f"Total documentos generados e integrados: {generados}")
    return generados
