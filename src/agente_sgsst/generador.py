import os
import json
from datetime import datetime
from agente_sgsst.rendering.maquetador import get_header_ft_sst_002
from agente_sgsst.generation.llm_client import LLMClient
from agente_sgsst.rendering.converter import convertir_markdown_a_docx
from agente_sgsst.rendering.docx_plantilla import generar_docx_ft_sst_002
from agente_sgsst.generation.prompt_registry import construir_prompt
from agente_sgsst.domain.clasificacion import get_applicable_items

llm = LLMClient()

# Fuente de verdad: docs/catalogo_documental.md (hallazgo 5.10).
# (id, estándar, nombre, fase PHVA, carpeta destino)
_CATALOGO_MAESTRO = (
    ("D-001", "1.1.1", "Acta de asignacion del responsable SST", "PLANEAR", "01_PLANEAR/1.1_Recursos"),
    ("D-002", "1.1.2", "Manual de funciones con responsabilidades SST", "PLANEAR", "01_PLANEAR/1.1_Recursos"),
    ("D-003", "1.1.3", "Presupuesto anual de SST", "PLANEAR", "01_PLANEAR/1.1_Recursos"),
    ("D-004", "1.1.4", "Certificado de afiliacion al Sistema de Seguridad Social", "PLANEAR", "01_PLANEAR/1.1_Recursos"),
    ("D-005", "1.1.5", "Identificacion de trabajadores de alto riesgo", "PLANEAR", "01_PLANEAR/1.1_Recursos"),
    ("D-006", "1.1.6", "Acta de conformacion y reuniones COPASST", "PLANEAR", "01_PLANEAR/1.1_Recursos"),
    ("D-007", "1.1.7", "Registro capacitacion COPASST", "PLANEAR", "01_PLANEAR/1.1_Recursos"),
    ("D-008", "1.1.8", "Acta conformacion Comite Convivencia Laboral", "PLANEAR", "01_PLANEAR/1.1_Recursos"),
    ("D-009", "1.2.1", "Programa de capacitacion anual", "PLANEAR", "01_PLANEAR/1.1_Recursos"),
    ("D-010", "1.2.2", "Formato de induccion y reinduccion", "PLANEAR", "01_PLANEAR/1.1_Recursos"),
    ("D-011", "1.2.3", "Certificados curso 50 horas", "PLANEAR", "01_PLANEAR/1.1_Recursos"),
    ("D-012", "2.1.1", "Politica de SST", "PLANEAR", "01_PLANEAR/1.2_Gestion_Integral"),
    ("D-013", "2.2.1", "Fichas de objetivos de SST", "PLANEAR", "01_PLANEAR/1.2_Gestion_Integral"),
    ("D-014", "2.3.1", "Evaluacion Inicial SG-SST (FT-SST-001)", "PLANEAR", "01_PLANEAR/1.2_Gestion_Integral"),
    ("D-015", "2.4.1", "Plan Anual de Trabajo", "PLANEAR", "01_PLANEAR/1.2_Gestion_Integral"),
    ("D-016", "2.5.1", "Procedimiento de archivo y retencion", "PLANEAR", "01_PLANEAR/1.2_Gestion_Integral"),
    ("D-017", "2.6.1", "Informe rendicion de cuentas", "PLANEAR", "01_PLANEAR/1.2_Gestion_Integral"),
    ("D-018", "2.7.1", "Matriz de requisitos legales", "PLANEAR", "01_PLANEAR/1.2_Gestion_Integral"),
    ("D-019", "2.8.1", "Procedimiento de comunicacion", "PLANEAR", "01_PLANEAR/1.2_Gestion_Integral"),
    ("D-020", "2.9.1", "Procedimiento de adquisiciones", "PLANEAR", "01_PLANEAR/1.2_Gestion_Integral"),
    ("D-021", "2.10.1", "Procedimiento de contratistas", "PLANEAR", "01_PLANEAR/1.2_Gestion_Integral"),
    ("D-022", "2.11.1", "Procedimiento gestion del cambio", "PLANEAR", "01_PLANEAR/1.2_Gestion_Integral"),
    ("D-023", "3.1.1", "Profesiogramas y examenes medicos", "HACER", "02_HACER/2.1_Gestion_Salud"),
    ("D-024", "3.1.2", "Procedimiento custodia historias clinicas", "HACER", "02_HACER/2.1_Gestion_Salud"),
    ("D-025", "3.1.3", "Informe diagnostico de salud", "HACER", "02_HACER/2.1_Gestion_Salud"),
    ("D-026", "3.1.4", "Programa medicina preventiva", "HACER", "02_HACER/2.1_Gestion_Salud"),
    ("D-027", "3.1.5", "Perfiles de cargo (detallados)", "HACER", "02_HACER/2.1_Gestion_Salud"),
    ("D-028", "3.1.6", "Actas seguimiento recomendaciones", "HACER", "02_HACER/2.1_Gestion_Salud"),
    ("D-029", "3.1.7", "Programa estilos de vida saludable", "HACER", "02_HACER/2.1_Gestion_Salud"),
    ("D-030", "3.1.8", "Plan saneamiento (Agua, residuos)", "HACER", "02_HACER/2.1_Gestion_Salud"),
    ("D-031", "3.1.9", "PGIR (Residuos)", "HACER", "02_HACER/2.1_Gestion_Salud"),
    ("D-032", "3.2.1", "Formato reporte ATEL", "HACER", "02_HACER/2.2_ATEL"),
    ("D-033", "3.2.2", "Informe investigacion ATEL", "HACER", "02_HACER/2.2_ATEL"),
    ("D-034", "3.2.3", "Matriz estadistica ATEL", "HACER", "02_HACER/2.2_ATEL"),
    ("D-035", "3.3.1 - 3.3.6", "Indicadores de frecuencia, severidad, etc.", "HACER", "02_HACER/2.2_ATEL"),
    ("D-036", "4.1.1", "Matriz IPARV (GTC 45)", "HACER", "02_HACER/2.3_Peligros_Riesgos"),
    ("D-037", "4.1.2", "Registro participacion en IPARV", "HACER", "02_HACER/2.3_Peligros_Riesgos"),
    ("D-038", "4.1.3", "Inventario sustancias quimicas", "HACER", "02_HACER/2.3_Peligros_Riesgos"),
    ("D-039", "4.1.4", "Informe mediciones ambientales", "HACER", "02_HACER/2.3_Peligros_Riesgos"),
    ("D-040", "4.2.1", "Plan de medidas de prevencion", "HACER", "02_HACER/2.4_Operacion_Seguridad"),
    ("D-041", "4.2.2", "Plan de inspecciones", "HACER", "02_HACER/2.4_Operacion_Seguridad"),
    ("D-042", "4.2.3", "Programa mantenimiento", "HACER", "02_HACER/2.4_Operacion_Seguridad"),
    ("D-043", "4.2.4", "Formato entrega EPP", "HACER", "02_HACER/2.4_Operacion_Seguridad"),
    ("D-044", "4.2.5", "Plan de Emergencias", "HACER", "02_HACER/2.4_Operacion_Seguridad"),
    ("D-045", "4.2.6", "Acta conformacion brigada", "HACER", "02_HACER/2.4_Operacion_Seguridad"),
    ("D-046", "4.2.7", "Informe simulacro", "HACER", "02_HACER/2.4_Operacion_Seguridad"),
    ("D-047", "4.2.8", "Permisos trabajo alto riesgo", "HACER", "02_HACER/2.4_Operacion_Seguridad"),
    ("D-048", "4.2.9", "Procedimientos trabajo seguro (PETS)", "HACER", "02_HACER/2.4_Operacion_Seguridad"),
    ("D-049", "4.2.10", "Plan estrategico seguridad vial (PESV)", "HACER", "02_HACER/2.4_Operacion_Seguridad"),
    ("D-050", "5.1.1", "Fichas indicadores", "VERIFICAR", "03_VERIFICAR/3.1_Verificacion"),
    ("D-051", "5.1.2", "Plan programa auditoria", "VERIFICAR", "03_VERIFICAR/3.1_Verificacion"),
    ("D-052", "5.1.3", "Acta auditoria con COPASST", "VERIFICAR", "03_VERIFICAR/3.1_Verificacion"),
    ("D-053", "5.1.4", "Informe revision por la direccion", "VERIFICAR", "03_VERIFICAR/3.1_Verificacion"),
    ("D-054", "6.1.1", "Procedimiento acciones correctivas", "ACTUAR", "04_ACTUAR/4.1_Mejoramiento"),
    ("D-055", "6.1.2", "Registro seguimiento acciones", "ACTUAR", "04_ACTUAR/4.1_Mejoramiento"),
    ("D-056", "6.1.3", "Plan mejoramiento (hallazgos MinTrabajo)", "ACTUAR", "04_ACTUAR/4.1_Mejoramiento"),
    ("D-057", "6.1.4", "Informe mejoramiento continuo", "ACTUAR", "04_ACTUAR/4.1_Mejoramiento"),
    ("D-058", "N/A", "Informe de Gestion (Resumen)", "99_INFORMES", "99_INFORMES_EJECUTIVOS"),
    ("D-059", "N/A", "Informe Rendicion Cuentas Ejecutivo", "99_INFORMES", "99_INFORMES_EJECUTIVOS"),
    ("D-060", "N/A", "Diagnostico Inicial SG-SST (Completo)", "99_INFORMES", "99_INFORMES_EJECUTIVOS"),
)

# Documentos que se generan siempre, sin importar el capítulo (hallazgo 5.11):
# el Diagnóstico FT-SST-001 (D-014) y los informes ejecutivos (D-058 a D-060).
_DOCUMENTOS_SIEMPRE_INCLUIDOS = frozenset({"D-014", "D-058", "D-059", "D-060"})


def _codigo_formato(doc_id):
    """FT-SST-001 es el Diagnóstico (D-014); FT-SST-002 el Acta del Responsable
    (D-001, coincidente con el formato histórico de referencia). El resto toma su
    D-XXX. Corrige el hallazgo 5.10 (códigos no normalizados)."""
    if doc_id == "D-014":
        return "FT-SST-001"
    if doc_id == "D-001":
        return "FT-SST-002"
    return f"FT-SST-{doc_id.split('-')[1]}"


def cargar_catalogo():
    return {
        doc_id: {
            "estandar": estandar,
            "nombre": nombre,
            "fase": fase,
            "carpeta": carpeta,
            "codigo": _codigo_formato(doc_id),
        }
        for doc_id, estandar, nombre, fase, carpeta in _CATALOGO_MAESTRO
    }

def obtener_documento(doc_id):
    catalogo = cargar_catalogo()
    return catalogo.get(doc_id)


def _numeral_documento(info):
    """Devuelve el numeral ("1.1.1") del estándar del documento, o None si es N/A.

    Normaliza estándares compuestos del catálogo ("3.3.1 - 3.3.6") al primer
    numeral ("3.3.1") para poder compararlos contra las listas aplicables de la
    Resolución 0312 (get_applicable_items).
    """
    estandar = info["estandar"].strip()
    if estandar.upper() == "N/A":
        return None
    return estandar.split()[0].split("-")[0].strip()


def documentos_aplicables_por_capitulo(capitulo):
    """Retorna los doc_ids del catálogo exigidos para el capítulo (hallazgo 5.11).

    Capítulo III exige los 60 estándares de la Resolución 0312 y el catálogo
    maestro mapea 1:1 cada documento a un estándar, por lo que aplica completo.
    Para Capítulo I y II se filtra de forma estricta contra la lista aplicable
    de estándares (7 y 21 respectivamente), más los documentos siempre
    incluidos (Diagnóstico FT-SST-001 e informes ejecutivos).
    """
    catalogo = cargar_catalogo()
    if capitulo == "Capítulo III":
        return list(catalogo.keys())

    aplicables = get_applicable_items(capitulo)
    resultado = []
    for doc_id, info in catalogo.items():
        if doc_id in _DOCUMENTOS_SIEMPRE_INCLUIDOS:
            resultado.append(doc_id)
            continue
        numeral = _numeral_documento(info)
        if numeral is not None and numeral in aplicables:
            resultado.append(doc_id)
    return resultado

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
        logo_path=empresa.get('logo') or None,
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
    
    # Convertir a Word (.docx) usando la plantilla oficial FT-SST-002
    generar_docx_ft_sst_002(md_file, docx_file, doc_info, contexto)
    
    if doc_id not in contexto['estado_sistema']['documentos_generados']:
        contexto['estado_sistema']['documentos_generados'].append(doc_id)
    
    return True

def generar_documentos_por_capitulo(contexto):
    capitulo = contexto['estado_sistema'].get('capitulo_aplicable', 'Capítulo I')
    doc_ids = list(documentos_aplicables_por_capitulo(capitulo))
    print(f"Generando {len(doc_ids)} documentos aplicables al {capitulo}...")
    generados = 0
    for doc_id in doc_ids:
        if generar_documento_individual(contexto, doc_id):
            generados += 1
    print(f"Total documentos generados e integrados: {generados}")
    return generados
