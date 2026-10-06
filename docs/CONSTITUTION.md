# CONSTITUTION.md — Agente Inteligente SG-SST (v2.0)

> Fuente única de verdad normativa, arquitectónica y de calidad para este repositorio.
> **v2.0 reemplaza** tanto el `constitution.md` inicial (arquitectura idealizada `backend/app/domain/`)
> como el `CONSTITUTION.md` de la sesión anterior (bitácora de una arquitectura `src/` ya construida
> pero con defectos no detectados). Esta versión concilia ambos con el código real subido y añade
> una auditoría con hallazgos verificados.

**Fecha:** 2026-09-10 · **Versión anterior:** v1.0 (`constitution.md`) y bitácora de sesión (`CONSTITUTION.md`)
**Marco normativo:** Decreto 1072 de 2015 + Resolución 0312 de 2019 (Colombia)

---

## 0. Qué cambió respecto a las dos versiones anteriores

1. La arquitectura objetivo ya **no** es `backend/app/domain/...` (eso nunca se construyó). El código real vive en `src/` plano, con `main.py` como CLI interactivo. La v2.0 **adopta `src/` como raíz** y define subpaquetes dentro de ella, en vez de forzar una reestructuración que ignore lo ya construido.
2. Se agrega la Sección 5, **Auditoría del código actual**, con hallazgos verificados (no solo leídos — el más grave se reprodujo con código ejecutable). Ningún agente debe seguir generando documentos con este código hasta resolver los ítems marcados **P0**.
3. Se incorpora Google Drive (`gdrive_sync.py`) como integración real del proyecto — no estaba contemplado en v1.0.
4. Se define gestión de secretos (`.env`, `credentials.json`, `token.pickle`), ausente en ambas versiones previas.

---

## 1. Propósito del proyecto (sin cambios de fondo)

Un agente que recibe datos de una empresa, clasifica el capítulo aplicable de la Resolución 0312/2019, calcula el diagnóstico ponderado (FT-SST-001), genera de forma híbrida (plantillas + LLM) el set de documentos del SG-SST, los exporta a `.docx` con el estándar visual FT-SST-002, los organiza en la arquitectura de carpetas PHVA, y opcionalmente los sincroniza a Google Drive.

---

## 2. Principios rectores (no negociables)

Se mantienen los 9 principios de v1.0 (fidelidad normativa, documentos maestros como especificación de solo lectura, motor determinista vs. generación LLM, encabezado FT-SST-002 obligatorio, regla del "No aplica", estrategia híbrida, arquitectura de carpetas como contrato, protección de PII, desarrollo agéntico auditable). Se añade:

### X. Gestión de secretos (nuevo)
`GROQ_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY` (`.env`), `credentials.json` y `token.pickle` (OAuth de Google Drive) **nunca** se versionan en git. El repo debe tener un `.gitignore` que los excluya explícitamente desde el primer commit. `token.pickle` contiene un refresh token de larga duración sin cifrar en disco — tratarlo con el mismo cuidado que una contraseña.

### XI. El motor de reglas no admite valores por defecto silenciosos (nuevo, aprendido de la auditoría)
Ningún componente determinista (`clasificacion.py`, el futuro motor de ponderación) puede devolver un resultado "razonable por defecto" ante una entrada inválida o fuera de rango (riesgo ARL fuera de I–V, capítulo no determinado, trabajadores ≤ 0). Debe fallar explícitamente (`ValueError`/excepción de dominio). Un valor por defecto silencioso es indistinguible de un cálculo correcto para quien lee el documento generado — y en este dominio esa ambigüedad es inaceptable.

---

## 3. Reglas de dominio (sin cambios respecto a v1.0)

- Clasificación: Cap. I ≤10 trab. + riesgo I–III · Cap. II 11–50 + riesgo I–III · Cap. III >50 trab. **o** riesgo IV–V con cualquier tamaño.
- Ponderación: existe UNA sola Tabla de Valores de 60 ítems (Art. 27 y Anexo 1) que rige los tres capítulos, distribuida 10/15/20/30/10/5/10% por estándar. La fuente única de verdad es `src/domain/data/estandares_0312_capitulo_iii.json` (alineada al anexo oficial; `docs/tabla_ponderacion_resolucion_0312.md` quedó como referencia secundaria con divergencias ya corregidas en el JSON).
- Ítems aplicables por capítulo: Cap. I = 7 (Art. 3), Cap. II = 21 (Art. 9), Cap. III = 60 (Art. 16), mapeados 1:1 a los numerales de la Tabla de Valores en `clasificacion.py`.
- Regla "No aplica": otorga el puntaje completo del ítem + resaltado amarillo, siempre con justificación. Para empresas de menos de 50 trabajadores con riesgo I–III (Cap. I y II), los ítems NO aplicables se otorgan AUTOMÁTICamente con el porcentaje máximo en la columna "No Aplica" (Art. 27, parágrafo 2) — no requieren respuesta manual ni se resaltan en amarillo.
- ✅ **Resuelto (2026-09-25)**: cargada la tabla oficial de ponderación que también aplica a Capítulos I y II. No existen "anexos de ponderación propios" por capítulo: el modelo oficial es la Tabla de Valores única + conjunto aplicable (Arts. 3 y 9) + "No Aplica" automático (Art. 27). El motor de ponderación calcula los tres capítulos.
- ✅ **Resuelto (2026-09-25)**: la discrepancia 21 vs 22 de Capítulo II quedó conciliada contra el anexo oficial real. El Art. 9 lista 21 estándares; los 22 del checklist eran numeración propia del checklist, no numerales de la Tabla de Valores. `CAPITULO_II_CONTEO_VERIFICADO = True`.

---

## 4. Arquitectura de software — adoptando `src/` como raíz real

```
Agente_SGSST/
├── CONSTITUTION.md
├── .env                          # NO versionado (ver Principio X)
├── .gitignore                    # DEBE excluir .env, credentials.json, token.pickle, data/contexto_empresa.json
├── docs/
│   └── normativo/                 # los 5 documentos fuente + FT-SST-002 de referencia (solo lectura)
├── data/
│   ├── contexto_empresa_template.json
│   └── contexto_empresa.json      # generado en runtime, NO versionado (contiene NIT/datos reales)
├── sistema_gestion/                # salida generada, NO versionada
├── src/
│   ├── __init__.py
│   ├── domain/                    # NUEVO — lógica pura, sin LLM, 100% testeada
│   │   ├── __init__.py
│   │   ├── clasificacion.py       # MOVER Y CORREGIR aquí (ver backlog 5.1, 5.2)
│   │   ├── ponderacion.py         # NUEVO — motor de cálculo real (diagnostico.py hoy no calcula nada)
│   │   └── data/
│   │       └── estandares_0312_capitulo_iii.json   # tabla de 60 ítems en JSON, no parseada en runtime desde .md
│   ├── generation/
│   │   ├── __init__.py
│   │   ├── prompt_registry.py     # NUEVO — carga master_prompts.md, resuelve prompt específico o GENERICO
│   │   └── llm_client.py          # MOVER (ver backlog 5.7 sobre manejo de errores)
│   ├── rendering/
│   │   ├── __init__.py
│   │   ├── maquetador.py          # MOVER Y CORREGIR aquí (ver backlog 5.8, 5.9 — fecha fija, logo ausente)
│   │   ├── converter.py           # MOVER Y CORREGIR aquí (ver backlog 5.6 — tablas markdown mal convertidas)
│   │   └── diagnostico.py         # MOVER Y REESCRIBIR — hoy solo maqueta, no calcula (backlog 5.3, 5.4)
│   ├── generador.py                # ORQUESTADOR — MOVER Y CORREGIR (backlog 5.5, 5.10, 5.11)
│   ├── integrations/
│   │   ├── __init__.py
│   │   └── gdrive_sync.py          # MOVER — es una integración externa opcional, no core (backlog 5.12)
│   └── cli/
│       ├── __init__.py
│       ├── main.py                 # MOVER Y CORREGIR (backlog 5.13 — bug de menú "Salir"/opción 6)
│       └── ingesta.py              # MOVER Y AMPLIAR (backlog 5.14 — falta logo, falta OCR de RUT)
├── tests/
│   ├── domain/
│   │   ├── test_clasificacion.py   # OBLIGATORIO antes de tocar generador.py — no existe hoy
│   │   └── test_ponderacion.py     # OBLIGATORIO — no existe hoy
│   └── rendering/
│       └── test_converter.py       # cubrir el fallback python-docx (backlog 5.6)
├── Dockerfile
└── docker-compose.yml
```

**Por qué esta reorganización y no otra**: el código actual mezcla en un solo nivel (`src/*.py`) lógica de negocio pura (`clasificacion.py`), generación asistida por LLM (`generador.py`, `llm_client.py`), maquetación/exportación (`maquetador.py`, `converter.py`), integración externa (`gdrive_sync.py`) e interfaz de usuario (`main.py`, `ingesta.py`). Esta mezcla es exactamente lo que permitió que el bug de `get_applicable_items` pasara inadvertido: nadie puede testear `clasificacion.py` de forma aislada porque nada en el repo tiene tests. Separar en subpaquetes no es estética — es lo que hace posible escribir `tests/domain/test_clasificacion.py` sin necesitar un LLM, un archivo `.env` o Google Drive para correrlo.

---

## 5. Auditoría del código actual — hallazgos verificados

Prioridad: **P0** bloquea uso en producción · **P1** corregir antes de escalar a más empresas · **P2** deuda técnica aceptable a corto plazo.

| # | Prioridad | Archivo | Hallazgo | Evidencia / impacto |
|---|:---:|---|---|---|
| 5.1 | **P0** | `clasificacion.py` → `get_applicable_items()` | Para Capítulo III retorna `{"1","2",...,"60"}` (enteros como texto) en vez de los numerales reales (`"1.1.1"`, `"4.2.3"`, etc.). | **Verificado por ejecución**: en `diagnostico.py`, TODOS los 60 ítems reales de una empresa de Capítulo III (>50 trabajadores o riesgo IV/V — el caso más común) se marcan como "No aplica" (amarillo), invirtiendo el diagnóstico. El comentario del propio código lo admite: `# Todos (ejemplo simplificado)`. |
| 5.2 | **P0** | `clasificacion.py` → `get_applicable_items()` | La lista de Capítulo II tiene 22 numerales, no 21. | Contado y confirmado. Hereda un error ya presente en `checklist_documental_resolucion_0312.md` sin detectarlo. No usar como fuente de verdad hasta validar contra el anexo oficial real. |
| 5.3 | **P0** | `diagnostico.py` | No calcula ningún puntaje. Genera una tabla HTML con columnas "C/NC/NA" vacías; nunca suma ponderación, nunca aplica la regla de "No aplica otorga el puntaje del ítem". | El archivo se llama `diagnostico.py` pero solo maqueta un esqueleto visual — la funcionalidad central descrita en `explicacion_del_negocio.md` sección 3 (cálculo del puntaje) no existe todavía. |
| 5.4 | **P1** | `diagnostico.py` | Parsea `tabla_ponderacion_resolucion_0312.md` línea por línea con `lines[10:]` y `line.split("\|")` en tiempo de ejecución. | Frágil: cualquier edición del encabezado del `.md` (agregar una línea, cambiar el título) rompe el parseo silenciosamente sin error visible. Reemplazar por una tabla estructurada (JSON/YAML) cargada una sola vez, no re-parseada del Markdown en cada ejecución. |
| 5.5 | **P0** | `generador.py` → `generar_documento_individual()` | El prompt para el LLM está *hardcodeado inline* en la función, no viene de `master_prompts.md`. | Viola directamente el Principio VI/II de esta constitution ("todo prompt en producción debe existir primero en `master_prompts.md`"). Sin `prompt_registry.py`, no hay forma de auditar ni versionar qué prompt generó qué documento. |
| 5.6 | **P1** | `converter.py` → `_convertir_con_python_docx()` | El fallback sin Pandoc convierte líneas de tabla Markdown (`\|...\|`) en un párrafo de texto plano (`doc.add_paragraph(line_str)`), no en una tabla Word real. | El encabezado FT-SST-002 (una tabla) se rompe visualmente cada vez que Pandoc no está disponible — es decir, en cualquier entorno donde no se haya instalado explícitamente. Esto es silencioso: el `.docx` se genera "exitosamente" pero mal. |
| 5.7 | **P1** | `converter.py` | Usa como `reference_doc` por defecto el archivo de ejemplo real `"FT-SST-002 - Responsable del Sistema de Gestión...docx"` (el acta firmada con datos de una persona real). | Conceptualmente incorrecto para un sistema multiempresa: cada empresa necesita su propio logo/razón social en el encabezado, y un `reference-doc` de Pandoc solo aporta *estilos* (fuentes, bordes de tabla), no puede parametrizar el contenido por empresa. Además, usar el acta real de una persona como plantilla técnica mezcla un documento con PII real dentro del pipeline de referencia — moverlo fuera de `docs/normativo/` de producción y usar una plantilla en blanco. |
| 5.8 | **P1** | `maquetador.py` → `get_header_ft_sst_002()` | La fecha `"31/08/2026"` está **hardcodeada como literal** en cada encabezado generado, sin importar cuándo se genera realmente el documento. | Cada documento generado llevará la misma fecha falsa. Debe recibir la fecha como parámetro (`datetime.now()` en la capa de orquestación, no en `maquetador.py`, para mantenerlo puro y testeable). |
| 5.9 | **P1** | `ingesta.py` + `maquetador.py` + `converter.py` | Ningún archivo del proyecto captura ni inserta el **logo institucional**, pese a ser el input #1 obligatorio según `explicacion_del_negocio.md`. El encabezado siempre muestra el texto literal `"Logo"`. | Gap funcional transversal: falta capturar la ruta/archivo del logo en `ingesta.py`, pasarlo por el contexto, e insertarlo como imagen real en la celda del encabezado en `converter.py` (python-docx sí soporta `add_picture()` dentro de una celda de tabla). |
| 5.10 | **P1** | `generador.py` → `cargar_catalogo()` | Solo contiene 11 de los 60 documentos del catálogo maestro. El código asigna códigos `"codigo"` de forma arbitraria (ej. D-001 recibe `"FT-SST-002"`, que ya es el código reservado para el estándar visual/documento de referencia). | Colisión de nomenclatura: `FT-SST-002` no puede significar simultáneamente "el estándar visual de encabezado" y "el acta de asignación del responsable". Definir un registro único de códigos antes de completar el catálogo a 60 documentos. |
| 5.11 | **P2** | `generador.py` → `generar_documentos_por_capitulo()` | Pese al nombre de la función, genera TODOS los documentos del catálogo sin filtrar por el capítulo aplicable a la empresa (no usa `get_applicable_items()` en ningún momento). | Definir explícitamente si el sistema debe generar solo lo exigido por el capítulo de la empresa, o siempre el set completo como buena práctica adicional — hoy es ambiguo y el nombre de la función promete algo que no hace. |
| 5.12 | **P0** | `main.py` → `menu_principal()` | No existe rama `elif opcion == "0":` pese a que el menú ofrece "0. Salir". Seleccionar `"6"` (sincronizar con Drive) ejecuta un `break` que **cierra todo el programa**, no solo la sincronización. | **Verificado leyendo el flujo completo**: "Salir" (la opción documentada) cae en `else: "Opción no válida"` y nunca sale; sincronizar con Drive termina el programa aunque el usuario solo quería sincronizar y seguir trabajando. |
| 5.13 | **P1** | `clasificacion.py` → `clasificar_empresa()` | Representa el riesgo ARL como entero 1–5 (`int(clase_riesgo_arl)`), mientras que toda la normativa y los documentos fuente usan numerales romanos I–V. | No falla, pero (a) diverge de la terminología oficial usada en los documentos generados para el LLM (`empresa['clase_riesgo_arl']` se inserta tal cual en el prompt, mostrando "3" en vez de "III"), y (b) si algún input llega como `"III"` en vez de `3`, `int("III")` lanza `ValueError` sin manejo. Usar un enum `RiesgoARL` (I–V) como tipo canónico, con validación explícita en el borde de entrada. |
| 5.14 | **P0** | `clasificacion.py` + `ingesta.py` | Ni la clasificación ni la ingesta validan `total_trabajadores <= 0` de forma explícita — `ingesta.py` acepta 0 trabajadores como válido (`>= 0`), y con 0 trabajadores + riesgo ≤3, `clasificar_empresa` devuelve silenciosamente "Capítulo I". | Una empresa con 0 trabajadores no es un caso de negocio válido y debe rechazarse en el borde de entrada, no clasificarse como si fuera válida (ver Principio XI). |
| 5.15 | **P1** | `gdrive_sync.py` | Usa `pickle` para persistir el token OAuth en disco sin cifrar (`token.pickle`), y no hay `.gitignore` visible en los archivos entregados que lo excluya. | Riesgo de fuga de credenciales si el repo se sube sin excluir estos archivos (ver Principio X, nuevo). |
| 5.16 | **P2** | Todo el proyecto | Cero archivos de test en los 11 archivos subidos. | Sin tests, cada uno de los hallazgos anteriores pudo (y de hecho pasó) desapercibido. Antes de seguir agregando funcionalidad, `tests/domain/test_clasificacion.py` y `tests/domain/test_ponderacion.py` son el punto de entrada obligatorio (ver Sección 7). |
| 5.17 | **P1** | `estandares_0312_capitulo_iii.json` (+ `docs/tabla_ponderacion_resolucion_0312.md`) | La tabla maestra cargada divergía del Anexo 1 oficial de la Res. 0312/2019 en 2 valores (2.5.1 estaba 1% → oficial 2%; 2.11.1 estaba 2% → oficial 1%) y en grupos enteros: 3.1 usaba la numeración/descripciones del checklist (con "tareas de alto riesgo" inexistente en el anexo) en vez de los 9 numerales oficiales (3.1.1 = "Descripción sociodemográfica – Diagnóstico de condiciones de salud"), y 4.2 estaba en orden y redacción propios (faltaban 4.2.2 "Verificación de aplicación de medidas" y 4.2.6 "Entrega de EPP"). | **Verificado contra el PDF del Anexo 1** (`table_pct_mins/pct_max`). Enfrascado en el diff con `tabla_ponderacion_resolucion_0312.md` para decidir el caso 3.2.1; resuelto inclinándose al anexo oficial (1%) cuando el checklist trae otro valor. Sin esta corrección, cualquier puntaje de Cap. I/II/III saldría con valores errados. |

### Estado de resolución — verificado 2026-09-11

> Memoria viva: cada marca **✅** fue verificada corriendo los tests en este repo real
> (`uv run pytest`) y, para 5.1, comprobando que el diagnóstico de Capítulo III ya no
> pinta los ítems de amarillo salvo los "No aplica" legítimos con justificación.

| Hallazgo | Estado | Verificación |
|---|---|---|
| 5.1, 5.2, 5.12, 5.13, 5.14 | ✅ Resuelto | `tests/domain/test_clasificacion.py` (22 tests) + diagnóstico Cap. III verificado manualmente; 5.2 conciliado contra el anexo oficial (Art. 9 = 21) el 2026-09-25 |
| 5.17 | ✅ Resuelto (2026-09-25) | JSON maestro reescrito al Anexo 1 oficial (pesos corregidos, grupos 3.1/4.2 descritos y numerados como el anexo) |
| 5.3, 5.4 | ✅ Resuelto | `tests/domain/test_ponderacion.py` (24 tests); `diagnostico.py` ya no parsea el `.md` en runtime; motor de ponderación extendido a los 3 capítulos con "No Aplica" automático (Art. 27 pár. 2) |
| 5.5 | ✅ Resuelto | `tests/generation/test_prompt_registry.py`; `generador.py` resuelve prompts solo vía `master_prompts.md` |
| 5.6 | ✅ Resuelto | `tests/rendering/test_converter.py`; el fallback crea tablas Word reales |
| 5.7 | ✅ Resuelto | `converter.py` ya no usa el acta con PII como `reference_doc` por defecto |
| 5.8 | ✅ Resuelto | `get_header_ft_sst_002(..., fecha=)` recibe la fecha desde la orquestación |
| 5.15 | ✅ Resuelto | `.gitignore` excluye `.env`, `credentials.json`, `token.pickle`, `data/contexto_empresa.json`, `sistema_gestion/` |
| 5.16 | ✅ Resuelto | Existen `tests/domain/`, `tests/generation/`, `tests/rendering/`, `tests/cli/`, `tests/generador/` (≥75 tests) |
| 5.9 | ✅ Resuelto (2026-09-13) | `ingesta.py` captura el logo (PNG/JPG) en `empresa['logo']`; `maquetador.py` lo incrusta como `![Logo](ruta)`; `converter.py` lo inserta como imagen real en la celda del encabezado (tests en `tests/rendering/`) |
| 5.10 | ✅ Resuelto (2026-09-13) | Catálogo completo con los 60 documentos desde `docs/catalogo_documental.md`; códigos `FT-SST-XXX` normalizados (FT-SST-001 Diagnóstico, FT-SST-002 Acta del Responsable) |
| 5.11 | ✅ Resuelto (2026-09-13) | `documentos_aplicables_por_capitulo()` filtra estricto por capítulo (Cap I=11, Cap II=25, Cap III=60) usando `get_applicable_items()`; siempre incluye Diagnóstico e informes ejecutivos |

---

## 6. Reglas de negocio pendientes de implementar

1. ✅ **Captura y embebido de logo institucional** (hallazgo 5.9) — resuelto en 2026-09-13.
2. ✅ **Extracción automática desde RUT/Cámara de Comercio** (Razón Social, NIT, Dirección, Representante Legal, Actividad Económica) — resuelto en 2026-09-13 en `cli/rut.py` (extracción best-effort vía `pypdf`; los campos no detectados se piden manualmente).
3. ✅ **Registro único de códigos de documento** (`FT-SST-XXX`) y catálogo completo de 60 documentos (hallazgo 5.10) — resuelto en 2026-09-13.
4. ✅ **Decisión explícita sobre filtrado por capítulo** — resuelto en 2026-09-13: se genera solo lo estricto del capítulo aplicable más Diagnóstico e informes ejecutivos (hallazgo 5.11).
5. ✅ **Motor de ponderación real** (`src/agente_sgsst/domain/ponderacion.py`) — resuelto (hallazgo 5.3).
6. ✅ **Conversión .docx determinista sin Pandoc** (`converter.py` nativo `python-docx`, sin `reference_doc`) — resuelto en 2026-10-06 (recomendación `docx` de la Sección 7).

---

## 7. Skills instaladas/recomendadas y cómo se aplican aquí

| Skill | Origen | Aplicación concreta en este proyecto |
|---|---|---|
| `test-driven-development` | `obra/superpowers` | Escribir `tests/domain/test_clasificacion.py` **antes** de tocar `clasificacion.py` para el hallazgo 5.1/5.2 — el test debe fallar primero reproduciendo el bug, igual que hicimos arriba. |
| `verification-before-completion` | `obra/superpowers` | Ningún hallazgo P0 se marca resuelto sin correr los tests y confirmar que el diagnóstico de una empresa de Capítulo III ya no pinta todo de amarillo. |
| `systematic-debugging` | `obra/superpowers` | Ya aplicado arriba para el hallazgo 5.1 (hipótesis → reproducción ejecutable → confirmación) — mismo método para los demás hallazgos P0/P1. |
| `git-guardrails-claude-code` | `mattpocock/skills` | Instalar antes de que el agente toque `main.py`/`generador.py` — hay datos reales de empresa en `data/contexto_empresa.json`, no versionar por accidente con un `git add .` + `push --force`. |
| `domain-modeling` | `mattpocock/skills` | Guía la separación `src/domain/` vs `src/generation/` vs `src/rendering/` de la Sección 4. |
| `writing-plans` + `executing-plans` | `obra/superpowers` | Usar para trabajar el backlog de la Sección 5 en orden (P0 primero), un plan por hallazgo, no todo a la vez. |
| `resolving-merge-conflicts` | `mattpocock/skills` | Útil en cuanto se muevan los 8 archivos de `src/` plano a los subpaquetes nuevos — es una reorganización de archivos con alto riesgo de conflicto si hay más de una rama activa. |
| `docx` / `xlsx` / `pdf` (nativas) | Claude/OpenCode | ✅ Concretado en 2026-10-06: `converter.py` es ahora un conversor nativo `python-docx` determinista (tablas e imágenes reales, sin Pandoc ni `reference_doc` con PII), reemplazando el parser de Markdown línea por línea más la rama externa. |

---

## 8. Gestión de secretos (ver Principio X)

`.gitignore` mínimo obligatorio antes del primer commit:
```
.env
credentials.json
token.pickle
data/contexto_empresa.json
sistema_gestion/
__pycache__/
*.pyc
```

## 9. Definición de "hecho" (ampliada)

Ningún hallazgo de la Sección 5 se considera resuelto sin:
1. Un test en `tests/` que reproduce el bug original y falla contra el código viejo.
2. La corrección que hace pasar ese test.
3. Verificación manual de que el caso más común (Capítulo III) produce un diagnóstico coherente (0 ítems pintados de amarillo si todo se marca "Cumple totalmente").
4. Commit en una rama de feature, nunca directo a `main` (Principio IX de v1.0, sigue vigente).

## 10. Proceso de enmienda

Igual que v1.0: todo cambio a las Secciones 3 y 5 requiere cita textual del artículo/numeral normativo que lo sustenta, o evidencia reproducible (como la de la Sección 5) si es una corrección de bug de código en vez de una regla normativa.

---
*Fin de CONSTITUTION.md — v2.0. Reemplaza a `constitution.md` v1.0 y a la bitácora `CONSTITUTION.md` de la sesión anterior.*
