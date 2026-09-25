"""
Aplicación Web Front-end con Streamlit para el Agente Inteligente SG-SST.
Permite la configuración de empresa, diagnóstico ponderado FT-SST-001,
generación masiva o individual de documentos normativos bajo estándar FT-SST-002,
y sincronización con Google Drive.
"""
import os
import json
import streamlit as st
from pathlib import Path

from agente_sgsst.domain.clasificacion import clasificar_empresa, get_applicable_items
from agente_sgsst.domain.ponderacion import cargar_estandares_capitulo_iii
from agente_sgsst.rendering.diagnostico import generar_diagnostico_base
from agente_sgsst.generador import cargar_catalogo, generar_documento_individual, documentos_aplicables_por_capitulo
from agente_sgsst.integrations.gdrive_sync import GoogleDriveSync

st.set_page_config(
    page_title="Agente SG-SST (Decreto 1072 / Res. 0312)",
    page_icon="🛡️",
    layout="wide",
)

CONTEXTO_PATH = "data/contexto_empresa.json"
DATA_TEMPLATE = "data/contexto_empresa_template.json"


def cargar_contexto():
    if not os.path.exists(CONTEXTO_PATH):
        os.makedirs("data", exist_ok=True)
        if os.path.exists(DATA_TEMPLATE):
            with open(DATA_TEMPLATE, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {
                "empresa": {
                    "razon_social": "",
                    "nit": "",
                    "direccion": "",
                    "representante_legal": "",
                    "actividad_economica": "",
                    "clase_riesgo_arl": 1,
                    "total_trabajadores": 10,
                    "logo": "",
                },
                "responsable_sst": {"nombre": "", "cc": "", "formacion": "", "licencia": ""},
                "estado_sistema": {"capitulo_aplicable": "", "documentos_generados": []},
            }
        with open(CONTEXTO_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    with open(CONTEXTO_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_contexto(ctx):
    os.makedirs("data", exist_ok=True)
    with open(CONTEXTO_PATH, "w", encoding="utf-8") as f:
        json.dump(ctx, f, indent=2, ensure_ascii=False)


def main():
    st.title("🛡️ Agente Inteligente SG-SST (Colombia)")
    st.markdown("Sistema de Gestión de Seguridad y Salud en el Trabajo bajo **Decreto 1072 de 2015** y **Resolución 0312 de 2019**.")

    contexto = cargar_contexto()

    # Sidebar Navigation
    menu = st.sidebar.selectbox(
        "Navegación",
        [
            "🏢 1. Configuración de Empresa",
            "📊 2. Diagnóstico Inicial (FT-SST-001)",
            "📑 3. Generación de Documentos",
            "☁️ 4. Google Drive",
        ],
    )

    # -------------------------------------------------------------------------
    # 1. CONFIGURACIÓN DE EMPRESA
    # -------------------------------------------------------------------------
    if menu == "🏢 1. Configuración de Empresa":
        st.header("Configuración y Datos de la Empresa")

        # Subir Logo
        st.subheader("Logo Institucional")
        logo_file = st.file_uploader("Subir Logo (PNG / JPG)", type=["png", "jpg", "jpeg"])
        if logo_file is not None:
            os.makedirs("data", exist_ok=True)
            logo_path = os.path.join("data", logo_file.name)
            with open(logo_path, "wb") as f:
                f.write(logo_file.getbuffer())
            contexto["empresa"]["logo"] = logo_path
            st.success(f"Logo guardado en {logo_path}")

        if contexto["empresa"].get("logo"):
            st.image(contexto["empresa"]["logo"], width=150, caption="Logo actual")

        # Formulario de datos
        st.subheader("Información General")
        with st.form("form_empresa"):
            razon_social = st.text_input("Razón Social", value=contexto["empresa"].get("razon_social", ""))
            nit = st.text_input("NIT / N° RUT (o Cámara de Comercio)", value=contexto["empresa"].get("nit", ""))
            direccion = st.text_input("Dirección", value=contexto["empresa"].get("direccion", ""))
            rep_legal = st.text_input("Representante Legal", value=contexto["empresa"].get("representante_legal", ""))
            actividad = st.text_input("Actividad Económica Principal", value=contexto["empresa"].get("actividad_economica", ""))

            riesgo_actual = contexto["empresa"].get("clase_riesgo_arl", 1)
            riesgo_idx = int(riesgo_actual) - 1 if 1 <= int(riesgo_actual) <= 5 else 0
            riesgo_arl = st.selectbox("Clase de Riesgo ARL (I - V)", [1, 2, 3, 4, 5], index=riesgo_idx)

            trabajadores = st.number_input("Número total de trabajadores", min_value=1, value=int(contexto["empresa"].get("total_trabajadores", 10)))

            st.subheader("Responsable del SG-SST")
            resp = contexto.setdefault("responsable_sst", {})
            resp_nombre = st.text_input("Nombre del Responsable SST", value=resp.get("nombre", ""))
            resp_cc = st.text_input("Cédula del Responsable SST", value=resp.get("cc", ""))

            submitted = st.form_submit_button("Guardar Datos")
            if submitted:
                contexto["empresa"]["razon_social"] = razon_social
                contexto["empresa"]["nit"] = nit
                contexto["empresa"]["direccion"] = direccion
                contexto["empresa"]["representante_legal"] = rep_legal
                contexto["empresa"]["actividad_economica"] = actividad
                contexto["empresa"]["clase_riesgo_arl"] = int(riesgo_arl)
                contexto["empresa"]["total_trabajadores"] = int(trabajadores)

                resp["nombre"] = resp_nombre
                resp["cc"] = resp_cc

                # Actualizar clasificación automática
                cap = clasificar_empresa(int(trabajadores), int(riesgo_arl))
                contexto.setdefault("estado_sistema", {})["capitulo_aplicable"] = cap

                guardar_contexto(contexto)
                st.success(f"¡Datos guardados! Clasificación automática: **{cap}**")

    # -------------------------------------------------------------------------
    # 2. DIAGNÓSTICO INICIAL (FT-SST-001)
    # -------------------------------------------------------------------------
    elif menu == "📊 2. Diagnóstico Inicial (FT-SST-001)":
        st.header("Diagnóstico Inicial de Estándares Mínimos (FT-SST-001)")

        empresa = contexto["empresa"]
        if not empresa.get("razon_social"):
            st.warning("⚠️ Primero configure los datos de la empresa en la sección 1.")
        else:
            capitulo = clasificar_empresa(empresa["total_trabajadores"], empresa["clase_riesgo_arl"])
            st.info(f"Empresa: **{empresa['razon_social']}** (NIT: {empresa['nit']}) | Capítulo aplicable: **{capitulo}**")

            diag_previo = contexto.get("estado_sistema", {}).get("diagnostico", {})
            respuestas_guardadas = diag_previo.get("respuestas") or {}

            # ------------------------------------------------------------------
            # Marcado C/NC/NA de los ítems aplicables del capítulo.
            # Los ítems NO aplicables (empresas <50 trabajadores con riesgo I/II/III)
            # se otorgan automáticamente con puntaje máximo al calcular (Art. 27) —
            # no se piden en el formulario.
            # ------------------------------------------------------------------
            st.subheader("Calificación por ítem aplicable (C / NC / NA)")
            items = cargar_estandares_capitulo_iii()
            aplicables = get_applicable_items(capitulo)
            opciones = ["C", "NC", "NA"]

            with st.form("form_diagnostico"):
                respuestas_form = {}
                for numeral in sorted(aplicables):
                    item = items[numeral]
                    saved = respuestas_guardadas.get(numeral)
                    st.markdown(
                        f"**{item.numeral}** — {item.descripcion} *(valor {item.valor_item * 100:.2f}%)*"
                    )
                    previo = saved[0] if saved and saved[0] in opciones else None
                    indice = opciones.index(previo) if previo else 0
                    criterio = st.selectbox(
                        "Criterio",
                        opciones,
                        index=indice,
                        key=f"crit_{item.numeral}",
                        label_visibility="collapsed",
                    )
                    justificacion = st.text_input(
                        "Justificación (obligatoria si 'No aplica')",
                        value=(saved[1] if saved else ""),
                        key=f"just_{item.numeral}",
                    )
                    respuestas_form[item.numeral] = (criterio, justificacion.strip())
                    st.markdown("---")

                calcular = st.form_submit_button("💾 Guardar respuestas y calcular puntaje")

            if calcular:
                sin_justif = [n for n, (c, j) in respuestas_form.items() if c == "NA" and not j]
                if sin_justif:
                    st.error(
                        "Ítems marcados como 'No aplica' sin justificación: "
                        f"{', '.join(sorted(sin_justif))}. La justificación es obligatoria "
                        "(Principio I de CONSTITUTION.md)."
                    )
                else:
                    contexto.setdefault("estado_sistema", {})
                    if "diagnostico" not in contexto["estado_sistema"]:
                        contexto["estado_sistema"]["diagnostico"] = {}
                    contexto["estado_sistema"]["diagnostico"]["respuestas"] = {
                        numeral: list(resp) for numeral, resp in respuestas_form.items()
                    }
                    try:
                        contexto = generar_diagnostico_base(contexto)
                        guardar_contexto(contexto)
                        pct = contexto["estado_sistema"]["diagnostico"].get("porcentaje")
                        st.success(
                            f"¡Puntaje calculado: **{pct * 100:.2f}%**!"
                            if pct is not None
                            else "Respuestas guardadas. Regénere el diagnóstico para ver el puntaje."
                        )
                    except Exception as e:
                        st.error(f"Error al calcular el puntaje: {e}")

            if st.button("Generar / Actualizar Diagnóstico FT-SST-001"):
                contexto = generar_diagnostico_base(contexto)
                guardar_contexto(contexto)
                st.success("¡Diagnóstico generado con éxito!")

            diag_path = Path("sistema_gestion/99_INFORMES_EJECUTIVOS/Diagnostico_Inicial_Resolucion_0312.md")
            if diag_path.exists():
                st.markdown("---")
                st.subheader("Vista Previa del Diagnóstico")
                st.markdown(diag_path.read_text(encoding="utf-8"))

                docx_diag = diag_path.with_suffix(".docx")
                if docx_diag.exists():
                    with open(docx_diag, "rb") as f:
                        st.download_button("📥 Descargar Diagnóstico en Word (.docx)", f, file_name=docx_diag.name)

    # -------------------------------------------------------------------------
    # 3. GENERACIÓN DE DOCUMENTOS
    # -------------------------------------------------------------------------
    elif menu == "📑 3. Generación de Documentos":
        st.header("Generador de Documentos del SG-SST (Estándar FT-SST-002)")

        empresa = contexto["empresa"]
        if not empresa.get("razon_social"):
            st.warning("⚠️ Primero configure los datos de la empresa en la sección 1.")
        else:
            capitulo = contexto.get("estado_sistema", {}).get("capitulo_aplicable", "Capítulo I")
            st.info(f"Capítulo activo: **{capitulo}**")

            st.subheader("Opción A: Generación Integral Completa")
            if st.button("🚀 Generar todos los documentos aplicables"):
                with st.spinner("Generando documentos con IA y aplicando formato FT-SST-002..."):
                    contexto = generar_diagnostico_base(contexto)
                    from agente_sgsst.generador import generar_documentos_por_capitulo
                    total = generar_documentos_por_capitulo(contexto)
                    guardar_contexto(contexto)
                    st.success(f"¡Se generaron {total} documentos exitosamente!")

            st.subheader("Opción B: Generación Individual (Bajo Demanda)")
            catalogo = cargar_catalogo()
            doc_id_sel = st.selectbox(
                "Seleccione el documento del catálogo",
                options=list(catalogo.keys()),
                format_func=lambda x: f"{x}: {catalogo[x]['nombre']} (Estándar {catalogo[x]['estandar']})",
            )

            if st.button("Generar Documento Seleccionado"):
                with st.spinner(f"Generando {doc_id_sel}..."):
                    success = generar_documento_individual(contexto, doc_id_sel)
                    guardar_contexto(contexto)
                    if success:
                        st.success(f"Documento {doc_id_sel} generado con éxito.")
                        info = catalogo[doc_id_sel]
                        docx_path = f"sistema_gestion/{info['carpeta']}/{info['codigo']}_{info['nombre'].replace(' ', '_')}.docx"
                        if os.path.exists(docx_path):
                            with open(docx_path, "rb") as f:
                                st.download_button(f"📥 Descargar {info['codigo']}.docx", f, file_name=os.path.basename(docx_path))
                    else:
                        st.error("Error al generar el documento.")

    # -------------------------------------------------------------------------
    # 4. GOOGLE DRIVE
    # -------------------------------------------------------------------------
    elif menu == "☁️ 4. Google Drive":
        st.header("Sincronización con Google Drive")
        st.markdown("Sube automáticamente la estructura PHVA (`sistema_gestion/`) a Google Drive mediante OAuth 2.0.")

        cred_file = st.file_uploader("Subir credentials.json de Google Cloud", type=["json"])
        if cred_file is not None:
            with open("credentials.json", "wb") as f:
                f.write(cred_file.getbuffer())
            st.success("¡credentials.json guardado correctamente!")

        if st.button("☁️ Sincronizar con Google Drive"):
            with st.spinner("Sincronizando archivos..."):
                try:
                    sync = GoogleDriveSync()
                    sync.sincronizar_directorio()
                    st.success("¡Sincronización completada con Google Drive!")
                except Exception as e:
                    st.error(f"Error en sincronización: {e}")


if __name__ == "__main__":
    main()
