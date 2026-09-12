# PROMPT DE ARRANQUE — Auditoría y remediación del Agente SG-SST (para OpenCode)

Pega esto como primer mensaje en OpenCode, dentro de la raíz del repo (donde está `CONSTITUTION.md`).

---

Eres el agente encargado de auditar y corregir el proyecto "Agente Inteligente SG-SST". Antes de escribir una sola línea de código, lee completo `CONSTITUTION.md` en la raíz de este repo — es la fuente única de verdad normativa, arquitectónica y de calidad del proyecto. No procedas sin haberlo leído.

## Reglas de trabajo obligatorias

1. **No toques nada de `src/domain/` sin un test que falle primero.** Este proyecto ya tuvo un bug crítico (Sección 5, hallazgo 5.1 de la constitution) que pasó inadvertido durante semanas porque no existía ni un solo test. Usa la skill `test-driven-development` de `obra/superpowers` para todo cambio en lógica de dominio.
2. **Usa `git-guardrails-claude-code`** (`mattpocock/skills`) antes de ejecutar cualquier comando git destructivo. Hay datos reales de empresa en `data/contexto_empresa.json` — no se versiona, no se fuerza push.
3. **Trabaja el backlog de la Sección 5 de `CONSTITUTION.md` en orden de prioridad**: primero todos los hallazgos marcados **P0**, luego P1, luego P2. No mezcles varios hallazgos en un mismo commit/rama — una rama por hallazgo, siguiendo el Principio IX (ramas por dominio, nunca directo a `main`).
4. **Usa `writing-plans` + `executing-plans`** (`obra/superpowers`) para descomponer cada hallazgo en pasos verificables antes de tocar código.
5. **Usa `verification-before-completion`** (`obra/superpowers`) antes de marcar cualquier hallazgo como resuelto: correr los tests, y además verificar manualmente que el caso de Capítulo III (>50 trabajadores o riesgo IV/V) ya no pinta todos los ítems del diagnóstico de amarillo.
6. **Usa `systematic-debugging`** (`obra/superpowers`) si algún hallazgo no es reproducible a la primera — no adivines la causa, reprodúcela con un script o test ejecutable antes de proponer el fix, igual que se hizo para confirmar el hallazgo 5.1 (está documentado en la constitution como ejemplo del método esperado).
7. **Usa `domain-modeling`** (`mattpocock/skills`) como guía para la migración de archivos de `src/*.py` (plano) a la estructura de subpaquetes `src/domain/`, `src/generation/`, `src/rendering/`, `src/integrations/`, `src/cli/` definida en la Sección 4 de la constitution.
8. **Usa `resolving-merge-conflicts`** (`mattpocock/skills`) si trabajas la migración de archivos en paralelo con otras ramas activas.
9. **No inventes normatividad.** Si necesitas un porcentaje de ponderación, un plazo o una regla que no esté en `docs/normativo/` ni en la constitution, márcalo explícitamente como pendiente de validar contra la fuente oficial — nunca lo completes por inferencia (Principio I y XI de la constitution).
10. **Antes de generar cualquier `.docx` de prueba**, usa la skill nativa `docx` en vez de reutilizar la lógica manual de `converter.py` (hallazgo 5.6/5.7) — esa lógica está marcada como defectuosa en la auditoría.

## Referencia disponible para el hallazgo 5.1/5.2/5.13/5.14 (NO copiar y pegar sin verificar)

Junto con este prompt se entrega una **implementación de referencia** ya probada (21/21 tests en verde) para `src/domain/clasificacion.py`, `tests/domain/test_clasificacion.py` y `src/domain/data/estandares_0312_capitulo_iii.json`. Es un punto de partida verificado, no un parche para aplicar a ciegas:

- Adáptala a la estructura real del repo (nombres de paquete, imports relativos, cómo `generador.py`/`diagnostico.py` importan hoy `clasificar_empresa` y `get_applicable_items` — no rompas esas firmas sin actualizar también a quienes las llaman).
- Corre los tests en el repo real después de integrarla — no asumas que porque pasaron en el entorno de referencia van a pasar igual aquí (rutas, `pythonpath`, versión de Python pueden diferir).
- Revisa especialmente el manejo del hallazgo 5.2 (Capítulo II con 22 ítems en vez de 21): la referencia expone `CAPITULO_II_CONTEO_VERIFICADO = False` en vez de inventar cuál ítem sobra. No "resuelvas" ese hallazgo adivinando un numeral a quitar — solo el anexo oficial de la Resolución 0312/2019 puede zanjarlo.
- Si detectas que la referencia no encaja bien con alguna otra parte del código real (por ejemplo cómo `ingesta.py` construye el `contexto`), ajústala — la prioridad es que el repo real quede correcto y testeado, no que la referencia se preserve intacta.

## Orden de trabajo sugerido (primera sesión)

1. Confirma que las skills de la Sección 7 de la constitution están instaladas; si falta alguna, instálala primero (`npx skills add <owner/repo> --skill <nombre>`).
2. Crea el `.gitignore` de la Sección 8 de la constitution ANTES de cualquier commit, si el repo aún no lo tiene.
3. Integra y adapta la referencia de `clasificacion.py` (ver sección anterior) al repo real. Corre los tests ahí, en el repo real, no confíes en que ya "están resueltos" solo porque se entregaron en la sesión de diseño.
4. Verifica manualmente el caso más importante: una empresa de Capítulo III (>50 trabajadores o riesgo IV/V) ya no debe tener todos sus ítems marcados como "No aplica" en el diagnóstico.
5. Repite el ciclo (test que falla → fix → test en verde → commit en su propia rama) para cada hallazgo P0 restante: 5.3, 5.5, 5.12.
6. Solo después de cerrar todos los P0, continúa con los P1 en el mismo orden en que aparecen en la tabla de la Sección 5.
7. **Solo cuando hayas verificado tú mismo (tests corriendo en el repo real, no en un entorno aislado) que un hallazgo está resuelto**, actualiza la tabla de la Sección 5 de `CONSTITUTION.md` marcando el estado (ej. añadiendo una columna o nota "✅ Resuelto en <rama/commit>") — la constitution es memoria viva, no un documento estático. No marques nada como resuelto por adelantado ni porque "la referencia ya lo tenía verde".

## Qué NO hacer

- No reestructures `docs/normativo/` (los 5 `.md` fuente + el `.docx`/`.xls` de referencia) — son de solo lectura según el Principio II.
- No agregues los 49 documentos faltantes al catálogo (hallazgo 5.10) hasta resolver la colisión de códigos `FT-SST-XXX` — hacerlo antes solo multiplicaría el problema por 49.
- No optimices ni refactorices código que no esté en el backlog de la Sección 5 "porque se ve feo" — cada cambio debe trazarse a un hallazgo numerado o a una regla de la constitution.

Empieza por leer `CONSTITUTION.md` completo y luego dime en qué hallazgo (P0) vas a empezar y por qué, antes de escribir código.
