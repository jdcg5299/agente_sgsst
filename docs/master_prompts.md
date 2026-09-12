# ARCHIVO MAESTRO DE PROMPTS — AGENTE SG-SST
Este archivo contiene los prompts especializados para cada tipo de documento del Sistema de Gestión de Seguridad y Salud en el Trabajo, basados en el Decreto 1072 de 2015 y la Resolución 0312 de 2019.

---

## [D-001] Acta de Asignación del Responsable SST
- **Estándar Res. 0312:** E1.1.1
- **Prompt:**
> Actúa como Consultor Senior en SG-SST. Redacta el documento formal de "Acta de Asignación del Responsable del Sistema de Gestión de Seguridad y Salud en el Trabajo (SG-SST)" para la empresa [RAZON_SOCIAL] con NIT [NIT].
> La empresa está clasificada en el Capítulo [CAPITULO] de la Resolución 0312 de 2019, con nivel de riesgo ARL [RIESGO] y [TRABAJADORES] trabajadores.
> Designa al responsable con base en la normatividad vigente, estableciendo sus funciones principales (planear, organizar, dirigir, desarrollar y aplicar el SG-SST, rendir cuentas a la alta dirección, promover la participación).
> Incluye espacios formales para firmas del Representante Legal ([REPRESENTANTE_LEGAL]) y del Responsable del SG-SST.
> Mantén un tono legal, formal y estructurado en Markdown.

---

## [D-012] Política de Seguridad y Salud en el Trabajo
- **Estándar Res. 0312:** E2.1.1
- **Prompt:**
> Actúa como Consultor Senior en SG-SST. Redacta la "Política de Seguridad y Salud en el Trabajo (SST)" para la empresa [RAZON_SOCIAL] con NIT [NIT], dedicada a [ACTIVIDAD_ECONOMICA].
> La política debe dar cumplimiento estricto al Artículo 2.2.4.6.5 del Decreto 1072 de 2015.
> Debe incluir obligatoriamente los compromisos de:
> 1. Protección de la seguridad y salud de todos los trabajadores.
> 2. Identificación de peligros, evaluación y valoración de riesgos y establecimiento de controles.
> 3. Cumplimiento de la normatividad nacional vigente aplicable en materia de riesgos laborales.
> 4. Mejora continua del SG-SST.
> La política debe estar fechada, firmada por el Representante Legal ([REPRESENTANTE_LEGAL]) y ser concisa, visible y difundida a todos los niveles de la organización.

---

## [D-015] Plan Anual de Trabajo
- **Estándar Res. 0312:** E2.4.1
- **Prompt:**
> Actúa como Consultor Senior en SG-SST. Diseña el "Plan Anual de Trabajo del SG-SST" en formato tabular para la empresa [RAZON_SOCIAL] con NIT [NIT], aplicable al periodo anual vigente.
> El plan debe estructurarse por Ciclo PHVA (Planear, Hacer, Verificar, Actuar) e incluir columnas para: Numeral Res. 0312, Actividad / Objetivo, Meta, Recursos (Financieros, Técnicos, Humanos), Responsable, y Cronograma trimestral/mensual (Ene - Dic).
> Asegúrate de incluir las actividades obligatorias del Capítulo [CAPITULO] de la Resolución 0312 de 2019.

---

## [D-036] Matriz de Identificación de Peligros, Evaluación y Valoración de Riesgos (IPARV - GTC 45)
- **Estándar Res. 0312:** E4.1.1
- **Prompt:**
> Actúa como Higienista y Especialista en Seguridad y Salud en el Trabajo. Elabora la estructura de la "Matriz de Identificación de Peligros, Evaluación y Valoración de Riesgos (IPARV) bajo la metodología GTC 45" para la empresa [RAZON_SOCIAL], cuya actividad económica principal es [ACTIVIDAD_ECONOMICA] y clase de riesgo ARL es [RIESGO].
> Genera una tabla detallada con al menos 5 procesos/actividades típicos de este sector económico, incluyendo columnas para: Proceso, Zona/Lugar, Actividad, Tarea, Rutinaria (Sí/No), Peligro (Descripción y Clasificación: Biológico, Físico, Químico, Psicosocial, Biomecánico, Condiciones de Seguridad, Fenómenos Naturales), Efectos Posibles, Controles Existentes (Fuente, Medio, Individuo), Evaluación del Riesgo (Nivel de Deficiencia, Nivel de Exposición, Nivel de Probabilidad, Interpretación del Nivel de Probabilidad, Nivel de Consecuencia, Nivel de Riesgo e Intervención), y Medidas de Intervención recomendadas (Eliminación, Sustitución, Controles de Ingeniería, Controles Administrativos, EPP).

---

## [GENERICO] Prompt por Defecto para Documentos del Catálogo
- **Prompt:**
> Actúa como Consultor Senior en Seguridad y Salud en el Trabajo (SG-SST) en Colombia. Redacta el documento oficial denominado "[NOMBRE_DOCUMENTO]" correspondiente al estándar [ESTANDAR] de la Resolución 0312 de 2019, para la empresa [RAZON_SOCIAL] con NIT [NIT], representada legalmente por [REPRESENTANTE_LEGAL].
> El contenido debe estar redactado con rigor técnico y jurídico, cumpliendo a cabalidad con el Decreto 1072 de 2015.
> Incluye objetivos claros, alcance, responsabilidades, desarrollo técnico del procedimiento o formato, y control de cambios.
