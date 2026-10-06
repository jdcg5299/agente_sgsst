# Agente SG-SST

Asistente inteligente para la construcción del **Sistema de Gestión de Seguridad y Salud en el Trabajo (SG-SST)** en Colombia.

Clasifica el capítulo aplicable de la Resolución 0312 de 2019, calcula el diagnóstico inicial ponderado (FT-SST-001) y lo entrega en Excel (.xlsx) replicando el instrumento oficial de la norma, genera el set documental con asistencia de un LLM, lo exporta en Markdown y Word (.docx) bajo el estándar visual FT-SST-002, lo organiza en la estructura de carpetas PHVA y, opcionalmente, lo sincroniza con Google Drive.

> **Normativa aplicada:** Decreto 1072 de 2015 · Resolución 0312 de 2019
> **Fuente única de verdad:** [`docs/CONSTITUTION.md`](docs/CONSTITUTION.md) — principios, reglas de dominio, arquitectura y auditoría del código.

---

## Tabla de contenidos

1. [Características](#características)
2. [Cumplimiento normativo](#cumplimiento-normativo)
3. [Arquitectura del proyecto](#arquitectura-del-proyecto)
4. [Requisitos previos](#requisitos-previos)
5. [Instalación y configuración](#instalación-y-configuración)
6. [Configuración de proveedores LLM](#configuración-de-proveedores-llm)
7. [Uso](#uso)
8. [Estructura de salida (PHVA)](#estructura-de-salida-phva)
9. [Catálogo de documentos](#catálogo-de-documentos)
10. [Pruebas](#pruebas)
11. [Docker](#docker)
12. [Seguridad y secretos](#seguridad-y-secretos)
13. [Proyectos pendientes](#proyectos-pendientes)
14. [Licencia](#licencia)

---

## Características

- **Clasificación automática del capítulo** aplicable según el total de trabajadores y la clase de riesgo ARL (Cap. I / II / III de la Res. 0312/2019).
- **Diagnóstico inicial ponderado (FT-SST-001)** con motor determinista en `domain/ponderacion.py`:
  - Los 60 ítems de Capítulo III suman 100%.
  - Regla "No aplica": otorga el puntaje completo del ítem, siempre con justificación.
  - Sin valores por defecto silenciosos: entradas incompletas o inválidas lanzan excepción (Principio XI).
- **Diagnóstico oficial en Excel**: el `.xlsx` replica el instrumento `docs/Diagnostico Resolucion 0312 de 2019 - 2026.xls` — 11 columnas (Ciclo, Numeral, Ítem, Criterio, Modo de verificación, Valor del ítem, Peso porcentual, Puntaje Posible ×3, Calificación), jerarquía estándar → bloque → ítems y cierre con "PORCENTAJE TOTAL DEL ESTANDAR" por bloque, "SUMA TOTAL", "SUMA TOTAL DE LOS ESTANDRES MINIMOS" y nivel del Art. 27. `tests/domain/test_fidelidad_instrumento.py` lo contrasta celda a celda contra el `.xls`, así que el texto y los pesos no pueden divergir del instrumento firmado. El `.md` queda solo como vista previa web; el diagnóstico **no** se entrega en `.docx`.
- **Generación híbrida de documentos**: plantillas + LLM, con el prompt resuelto únicamente desde `docs/master_prompts.md` (sin prompts embebidos en el código).
- **Exportación dual**: Markdown (.md) y Word (.docx), con encabezado estandarizado FT-SST-002.
- **Word fiel al formato oficial**: los `.docx` se generan a partir de la plantilla `docs/plantilla_ft_sst_002.docx` (header de sección fusionado, pie `Elaboró/Revisó/Aprobó`, Times New Roman 12pt, Letter, márgenes 3 cm) con el logo, la razón social, fecha y datos de la empresa insertados dinámicamente por documento.
- **Estructura de carpetas PHVA** (Planear–Hacer–Verificar–Actuar) como contrato de salida.
- **Sincronización opcional con Google Drive** (OAuth 2.0).
- **Multi-proveedor LLM**: Groq (por defecto), OpenAI y Gemini, con modo de simulación sin API keys.

## Cumplimiento normativo

| Norma | Rol en el proyecto |
|---|---|
| **Decreto 1072 de 2015** (Cap. 6, Título 4, Parte 2 del Libro 2) | Base del SG-SST, obligaciones del empleador, requisitos documentales y PHVA. |
| **Resolución 0312 de 2019** | Estándares mínimos por tamaño/riesgo de empresa y tabla de ponderación del diagnóstico (60 ítems para Cap. III). |
| **GTC 45** | Metodología para la matriz de identificación de peligros (IPARV). |

## Arquitectura del proyecto

El código vive bajo el paquete estándar `src/agente_sgsst/`, separado en capas según `docs/CONSTITUTION.md` §4:

```
Agente_SGSST/
├── .env                               # NO versionado (secretos, ver Seguridad)
├── .gitignore
├── pyproject.toml                     # Entrada CLI: agente_sgsst.main:main
├── Dockerfile
├── docker-compose.yml
├── data/
│   ├── contexto_empresa_template.json # Plantilla de contexto (versionada)
│   └── contexto_empresa.json          # Contexto real del runtime (NO versionado)
├── docs/
│   ├── CONSTITUTION.md                # Fuente de verdad: principios, reglas, auditoría
│   ├── master_prompts.md              # Archivo maestro de prompts (bloques ## [ID])
│   ├── catalogo_documental.md
│   ├── plantilla_ft_sst_002.docx      # Plantilla Word oficial (header/footer + estilos)
│   └── ...                            # Normativa y explicación del negocio
├── app.py                             # Front-end web (Streamlit)
├── sistema_gestion/                   # Salida generada (NO versionada)
├── src/
│   └── agente_sgsst/
│   │   ├── __init__.py
│   │   ├── main.py                    # Punto de entrada (orquestación del flujo)
│   │   ├── generador.py               # Orquestador de catálogo y generación LLM
│   │   ├── domain/                    # Lógica pura, sin LLM, 100% testeada
│   │   │   ├── clasificacion.py       #   Capítulo aplicable + ítems por capítulo
│   │   │   ├── ponderacion.py         #   Motor de ponderación (60 ítems)
│   │   │   └── data/estandares_0312_capitulo_iii.json
│   │   ├── generation/                # Prompts y clientes LLM
│   │   │   ├── prompt_registry.py     #   Resolución de prompts (GENERICO o específico)
│   │   │   └── llm_client.py          #   Cliente multi-proveedor (Groq/OpenAI/Gemini)
│   │   ├── rendering/                 # Maquetación y exportación
│   │   │   ├── maquetador.py          #   Encabezado FT-SST-002 (Markdown)
│   │   │   ├── docx_plantilla.py      #   Render .docx fiel a plantilla FT-SST-002
│   │   │   ├── converter.py           #   Markdown -> .docx (Pandoc o python-docx)
│   │   │   ├── excel_diagnostico.py   #   Diagnóstico FT-SST-001 .xlsx (instrumento oficial)
│   │   │   └── diagnostico.py         #   Informe FT-SST-001 (.xlsx oficial + .md vista previa)
│   │   ├── integrations/
│   │   │   └── gdrive_sync.py         #   Sincronización con Google Drive (PHVA)
│   │   └── cli/
│   │       ├── main.py                #   Menú interactivo
│   │       ├── ingesta.py             #   Captura de datos de la empresa
│   │       └── rut.py                 #   Parser RUT/Cámara de Comercio (pypdf)
└── tests/                             # pytest (161 tests)
    ├── domain/
    │   ├── test_clasificacion.py      # TDD del bug 5.1 (22 tests)
    │   ├── test_ponderacion.py        # Motor de ponderación (30 tests)
    │   └── test_fidelidad_instrumento.py  # Fidelidad al .xls oficial (16 tests)
    ├── generation/
    │   ├── test_prompt_registry.py    # Registro de prompts (7 tests)
    │   └── test_llm_client.py         # Reintentos y errores del cliente LLM (4 tests)
    ├── rendering/
    │   ├── test_diagnostico.py        # Entrega .xlsx + paridad con el .md (18 tests)
    │   ├── test_excel_diagnostico.py  # Instrumento oficial en .xlsx (32 tests)
    │   ├── test_converter.py          # Fallback python-docx + logo (9 tests)
    │   ├── test_docx_plantilla.py     # Render .docx fiel a plantilla (3 tests)
    │   └── test_maquetador.py         # Encabezado FT-SST-002 + logo (4 tests)
    ├── cli/
    │   └── test_rut.py                # Parser RUT/Cámara de Comercio (9 tests)
    └── generador/
        └── test_generador.py          # Catálogo 60 docs + filtrado por capítulo (7 tests)
```

## Requisitos previos

- **Python ≥ 3.11**
- **uv** (gestor de proyectos). En Windows: `winget install astral-sh.uv` · macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Pandoc** (opcional, recomendado) para conversión Markdown → .docx con estilos. Si no está, se usa el conversor nativo `python-docx`.

## Instalación y configuración

```bash
# 1. Clonar el repositorio
git clone https://github.com/jdcg5299/agente_sgsst.git
cd Agente_SGSST

# 2. Crear el entorno virtual e instalar dependencias
uv sync

# 3. Configurar secretos (nunca se versionan)
cp data/contexto_empresa_template.json data/contexto_empresa.json
# Crear .env (ver sección siguiente)
```

El contexto de empresa también se captura de forma interactiva la primera vez que se ejecuta la aplicación.

## Configuración de proveedores LLM

Crea un archivo `.env` en la raíz del proyecto:

```bash
LLM_PROVIDER=groq                 # groq | openai | gemini | simulado
GROQ_API_KEY=tu_clave_groq
OPENAI_API_KEY=tu_clave_openai
GEMINI_API_KEY=tu_clave_gemini
```

| Variable | Obligatoria | Descripción |
|---|---|---|
| `LLM_PROVIDER` | No | Proveedor a usar. Si se omite, se detecta por la clave disponible (Groq → OpenAI → simulado). `simulado` genera texto de ejemplo sin llamadas externas. |
| `GROQ_API_KEY` | Una de las tres | Clave de Groq (modelo `openai/gpt-oss-120b`). |
| `OPENAI_API_KEY` | Una de las tres | Clave de OpenAI (modelo `gpt-4o`). |
| `GEMINI_API_KEY` | Una de las tres | Clave de Google Gemini (modelo `gemini-1.5-pro`). |

**Sin ninguna clave** el agente opera en **modo simulado**: genera contenido de ejemplo para validar el flujo completo (menú, diagnóstico, exportación) sin consumir API.

## Uso

### A. Interfaz web (Streamlit) — recomendada para la mayoría de usuarios

```bash
uv run streamlit run app.py
```

La app web cubre todo el flujo: configuración de empresa (con autocompletado desde RUT en PDF y carga de logo), diagnóstico FT-SST-001 con puntaje ponderado, generación de documentos (integral o individual) y sincronización con Google Drive.

### B. Línea de comandos (CLI)

```bash
# Con el paquete instalado (recomendado)
uv run agente-sgsst

# Alternativa directa
uv run python -m agente_sgsst.main
```

El flujo automático ejecuta: ingesta de datos (si no existen) → diagnóstico inicial (paso 1) → menú principal.

```
============================================================
     AGENTE SG-SST - MENÚ PRINCIPAL
============================================================
1. Generar Sistema Integral Completo
2. Generar Documento Individual (Bajo Demanda)
3. Listar Documentos Disponibles
4. Actualizar Datos de la Empresa
5. Ver Estado Actual
6. Sincronizar con Google Drive
0. Salir
------------------------------------------------------------
```

## Estructura de salida (PHVA)

Cada documento generado se guarda en **Markdown y .docx** en la ubicación correspondiente del ciclo PHVA:

```
sistema_gestion/
├── 01_PLANEAR/
│   ├── 1.1_Recursos/
│   └── 1.2_Gestion_Integral/
├── 02_HACER/
│   ├── 2.1_Gestion_Salud/
│   ├── 2.2_ATEL/
│   ├── 2.3_Peligros_Riesgos/
│   └── 2.4_Operacion_Seguridad/
├── 03_VERIFICAR/
│   └── 3.1_Verificacion/
├── 04_ACTUAR/
│   └── 4.1_Mejoramiento/
└── 99_INFORMES_EJECUTIVOS/         # Diagnóstico FT-SST-001 (.xlsx oficial + .md vista previa), informes
```

## Catálogo de documentos

El catálogo maestro vive en `src/agente_sgsst/generador.py` (`cargar_catalogo()`). Cada documento se genera bajo demanda (opción 2) o como parte del sistema integral (opción 1), usando el prompt registrado en `docs/master_prompts.md` o el prompt `GENERICO`.

| ID | Documento | Estándar | Carpeta |
|---|---|---|---|
| D-001 | Acta de Asignación del Responsable SST | 1.1.1 | 1.1_Recursos |
| D-002 | Manual de funciones con responsabilidades SST | 1.1.2 | 1.1_Recursos |
| D-003 | Presupuesto anual de SST | 1.1.3 | 1.1_Recursos |
| D-004 | Certificado de afiliación al Sistema de Seguridad Social | 1.1.4 | 1.1_Recursos |
| D-012 | Política de SST | 2.1.1 | 1.2_Gestion_Integral |
| D-013 | Fichas de objetivos de SST | 2.2.1 | 1.2_Gestion_Integral |
| D-014 | Evaluación Inicial SG-SST (FT-SST-001) | 2.3.1 | 99_INFORMES_EJECUTIVOS |
| D-015 | Plan Anual de Trabajo | 2.4.1 | 1.2_Gestion_Integral |
| D-018 | Matriz de requisitos legales | 2.7.1 | 1.2_Gestion_Integral |
| D-036 | Matriz IPARV (GTC 45) | 4.1.1 | 2.3_Peligros_Riesgos |
| D-044 | Plan de Emergencias | 4.2.5 | 2.4_Operacion_Seguridad |

## Comandos rápidos con Make

Todas las ejecuciones comunes están en el [`Makefile`](Makefile) (GNU Make; en Windows: `choco install make`). El shell se resuelve solo: cmd en Windows, sh en Linux/CI.

| Comando | Acción |
|---|---|
| `make install` | Instala dependencias (`uv sync`) |
| `make test` | Ejecuta la suite de pytest |
| `make web` | Lanza la interfaz web Streamlit → http://localhost:8501 |
| `make cli` | Lanza el menú CLI interactivo |
| `make demo` | Regenera el diagnóstico DEMO de validación (no toca datos reales) |
| `make lint` | Verifica estilo con ruff (`ruff check .`) |
| `make lint-format` | Verifica formato con ruff (`ruff format --check .`) |
| `make docker-build` / `make docker-up` | Construye / levanta el contenedor |
| `make build` | Empaqueta con `uv build` |
| `make clean` | Elimina caches y artefactos de build (Windows) |

## Pruebas

```bash
uv run pytest        # o: make test
uv run ruff check .  # o: make lint
```

La suite cubre:

- **`tests/domain/`** → clasificación de capítulo y motor de ponderación (38 tests, TDD de los hallazgos P0 5.1 y 5.3).
- **`tests/generation/`** → registro de prompts (7 tests, hallazgo P0 5.5).
- **`tests/rendering/`** → conversión Markdown → .docx, encabezado FT-SST-002, logo y renderizado con plantilla Word (12 tests, hallazgos P1 5.6, 5.8, 5.9 + plantilla `docx_plantilla`).
- **`tests/cli/`** → parser de RUT / Cámara de Comercio (9 tests, Fase 1.2).
- **`tests/generador/`** → catálogo de 60 documentos y filtrado por capítulo (7 tests, hallazgos 5.10 y 5.11).

Cada fix del backlog en [`docs/CONSTITUTION.md` §5](docs/CONSTITUTION.md) exige un test que reproduzca el bug original antes de la corrección (definición de "hecho", §9).

## Docker

```bash
# Construir imagen
docker build -t agente-sgsst .

# Ejecutar CLI interactiva
docker run -it --rm \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e GEMINI_API_KEY=$GEMINI_API_KEY \
  -v $(pwd)/sistema_gestion:/app/sistema_gestion \
  -v $(pwd)/data:/app/data \
  agente-sgsst

# O usando docker-compose (carga las variables desde el entorno)
docker compose up --build
```

## Seguridad y secretos

En cumplimiento del Principio X de [`docs/CONSTITUTION.md`](docs/CONSTITUTION.md), **nunca se versionan**:

- `.env` (claves de API y proveedor LLM)
- `credentials.json` y `token.pickle` (credenciales OAuth de Google Drive)
- `data/contexto_empresa.json` (NIT y datos reales de la empresa)
- `sistema_gestion/` (documentos generados con datos de empresa)

El `.gitignore` los excluye explícitamente. No ejecutes `git add -A` sin revisar antes `git status`.

## Proyectos pendientes

Verifica el estado vigente en [`docs/CONSTITUTION.md` §5](docs/CONSTITUTION.md). Resumen:

- **5.9** — Captura e inserción del logo institucional en el encabezado.
- **5.10** — Registro único de códigos `FT-SST-XXX` antes de completar el catálogo a 60 documentos.
- **5.11** — Decisión explícita sobre filtrar por capítulo vs. generar el set completo.

## Licencia

Proyecto privado — uso interno. Autor: **Julian Correa** (`juliancorrea1630@gmail.com`).