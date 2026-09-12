# GUÍA Y REGLAS DE NEGOCIO DEL AGENTE DE SG-SST
## Marco Normativo: Decreto 1072 de 2015 y Resolución 0312 de 2019 (Colombia)

Este documento constituye la **guía maestra y el conjunto de reglas de negocio** que el agente inteligente utilizará para recopilar información, clasificar empresas, calcular ponderaciones, maquetar documentos bajo el estándar visual (FT-SST-002) y generar de forma completa el Sistema de Gestión de Seguridad y Salud en el Trabajo (SG-SST).

---

## 1. 📥 ENTRADAS OBLIGATORIAS (INPUTS DEL USUARIO)
Para iniciar la elaboración de cualquier SG-SST, el agente debe solicitar y validar los siguientes datos de la empresa contratante:
1. **Logo institucional** de la empresa (imagen en formato PNG o JPG).
2. **RUT o Cámara de Comercio** (para extraer automáticamente: Razón Social, NIT, Dirección, Representante Legal y Actividad Económica Principal).
3. **Clase de Riesgo de la ARL** (Riesgo I, II, III, IV o V según la actividad económica).
4. **Número total de trabajadores** vinculados (directos, temporales y contratistas permanentes).

---

## 2. 🗂️ CLASIFICACIÓN Y APLICABILIDAD (RESOLUCIÓN 0312 DE 2019)
Con base en el número de trabajadores y el nivel de riesgo de la ARL, el agente determinará automáticamente el capítulo aplicable de la Resolución 0312 de 2019:

* **Capítulo I (7 Estándares Mínimos):**
  * Empresas de **10 o menos trabajadores** clasificadas en Riesgo I, II o III.
  * Perfil del responsable: Técnico en SST (licencia vigente, curso 50h, 1 año de experiencia).
* **Capítulo II (21 Estándares Mínimos):**
  * Empresas de **11 a 50 trabajadores** clasificadas en Riesgo I, II o III.
  * Perfil del responsable: Tecnólogo o Profesional en SST (licencia vigente, curso 50h, 2 años de experiencia).
* **Capítulo III (60 Estándares Mínimos - Estructura PHVA Completa):**
  * Empresas de **más de 50 trabajadores** (Riesgo I a V).
  * Empresas de **50 o menos trabajadores** clasificadas en **Riesgo Alto (IV o V)**.
  * Perfil del responsable: Profesional en SST o con posgrado en SST (licencia vigente, curso 50h).

---

## 3. 📊 REGLAS DE NEGOCIO PARA EL DIAGNÓSTICO Y PONDERACIÓN (FT-SST-001)
El archivo de diagnóstico inicial y evaluación de estándares mínimos se regirá por las siguientes reglas estrictas:
1. **Ponderación Individual:** Cada uno de los 60 ítems posee un valor porcentual definido (ver `tabla_ponderacion_resolucion_0312.md`).
2. **Criterios de Calificación:** Las columnas de evaluación son: `Cumple totalmente`, `No cumple`, y `No aplica`.
3. **Manejo de Ítems que "No Aplican":**
   * Cuando un estándar o ítem no aplique a la empresa según su clasificación de capítulo o justificación normativa:
     * Se diligenciará automáticamente el campo **`No aplica`** con el valor exacto de la ponderación del ítem.
     * Se asignará ese mismo valor en la columna **`Calificación de la empresa o contratante`**.
     * Se rellenará dicha celda con **color amarillo** (indicador visual de ítem excluido justificadamente que otorga puntaje).
4. **Puntaje Total:** La calificación final es la sumatoria de los puntos obtenidos por cumplimiento total más los puntos otorgados por los ítems que aplican como "No aplica".

---

## 4. 🎨 ESTÁNDAR VISUAL Y DE MAQUETACIÓN DE DOCUMENTOS (FT-SST-002)
Todos los documentos, políticas, formatos, actas y matrices generados por el agente deben mantener una identidad visual coherente y profesional, tomando como referencia el formato guía institucional (**FT-SST-002**):

### Estructura de Encabezado Institucional Obligatorio:
Cada documento debe iniciar con una tabla de cabecera estándar con el siguiente formato Markdown / HTML:

```markdown
| Logo Empresa | SISTEMA DE GESTIÓN DE SEGURIDAD Y SALUD EN EL TRABAJO | CÓDIGO: FT-SST-XXX |
| :---: | :--- | :---: |
| *(Insertar Logo)* | **[NOMBRE OFICIAL DEL DOCUMENTO / FORMATO]** | **VERSIÓN:** 01 |
| | **ESTÁNDAR RES. 0312:** [Ej. E2.3.1] | **FECHA:** [DD/MM/AAAA] |
| | **EMPRESA:** [Razón Social de la Empresa] | **PÁGINA:** 1 de 1 |
```

### Lineamientos de Estilo:
* **Tipografía y Textos:** Lenguaje formal, técnico y jurídico adaptado al Decreto 1072 de 2015.
* **Tablas:** Todas las matrices (IPARV, Matriz Legal, Plan Anual de Trabajo, Cronograma) deben presentarse en formato tabular Markdown limpiamente estructurado con sus respectivos encabezados en negrita.
* **Secciones:** Uso jerárquico de títulos (`#`, `##`, `###`) para separar objetivos, alcance, responsabilidades, desarrollo del procedimiento y control de cambios.

---

## 5. 🤖 ESTRATEGIA DE GENERACIÓN DOCUMENTAL (ENFOQUE HÍBRIDO)
El sistema operará bajo un modelo híbrido para optimizar la completitud legal y evitar omisiones:
1. **Plantillas Estructurales Base (Esquemas Obligatorios):**
   * Formato de Encabezado y Estilo Visual (FT-SST-002).
   * Matriz de Identificación de Peligros, Evaluación y Valoración de Riesgos (IPARV - Metodología GTC 45).
   * Matriz de Requisitos Legales.
   * Plan Anual de Trabajo (con cronograma Ene-Dic, presupuesto, responsable y metas).
   * Formato de Diagnóstico Inicial (FT-SST-001) con ponderaciones automáticas.
   * Consolidado de Indicadores (Frecuencia, Severidad, Ausentismo, Prevalencia, Incidencia).
2. **Generación Dinámica Completa por el LLM:**
   * El agente redactará de manera autónoma los más de 40 documentos complementarios requeridos por el Decreto 1072 y la Resolución 0312 (Políticas, Objetivos, Actas de COPASST, Comité de Convivencia, Procedimientos de Contratistas, Adquisiciones, Preparación de Emergencias, Profesiogramas, Inducciones, etc.).
   * Incluso para documentos que requieran ejecución temporal (como actas de reuniones mensuales), el agente **generará la estructura completa diligenciada con los datos de la empresa**, lista para su respectiva firma y uso operativo.

---

## 6. 📁 ARQUITECTURA DE CARPETAS Y ENTREGABLES
El agente organizará todos los archivos generados en una estructura de directorios limpia y jerarquizada por Ciclo PHVA:

* `01_PLANEAR/`
  * `1.1_Recursos/` (Asignación, Presupuesto, COPASST, CCL, Seguridad Social)
  * `1.2_Gestion_Integral/` (Política, Objetivos, Diagnóstico, Plan de Trabajo, Matriz Legal, Comunicaciones, Adquisiciones, Contratistas, Gestión del Cambio)
* `02_HACER/`
  * `2.1_Gestion_Salud/` (Evaluaciones médicas, Perfiles de cargo, Estilos de vida, Saneamiento)
  * `2.2_ATEL/` (Reporte e investigación de accidentes/incidentes, Estadísticas)
  * `2.3_Peligros_Riesgos/` (Matriz IPARV, Sustancias químicas, Mediciones ambientales)
  * `2.4_Operacion_Seguridad/` (Medidas de control, Mantenimiento, EPP, Tareas de alto riesgo, Plan de Emergencias, Brigada, Simulacros)
* `03_VERIFICAR/`
  * `3.1_Verificacion/` (Indicadores SG-SST, Auditoría anual con COPASST, Revisión por la Alta Dirección)
* `04_ACTUAR/`
  * `4.1_Mejoramiento/` (Acciones correctivas/preventivas, Planes de mejoramiento)
* `99_INFORMES_EJECUTIVOS/`
  * `Diagnostico_Inicial_Resolucion_0312.md`
  * `Informe_Rendicion_de_Cuentas.md`
  * `Informe_Revision_por_la_Direccion.md`
