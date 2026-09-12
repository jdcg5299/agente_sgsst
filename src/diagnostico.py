"""
Diagnóstico inicial FT-SST-001 — hallazgos 5.3 y 5.4 de CONSTITUTION.md.

Antes: este archivo solo maquetaba una tabla HTML con columnas C/NC/NA vacías,
parseando `docs/tabla_ponderacion_resolucion_0312.md` línea por línea en runtime
(hallazgos 5.4) y sin calcular NINGÚN puntaje (hallazgo 5.3).

Ahora:
- La fuente de datos es el motor de dominio `src/domain/ponderacion.py` (JSON
  estructurado, no re-parseado del Markdown en cada ejecución).
- Si el contexto trae respuestas guardadas, se CALCULA el puntaje real
  (sumatoria por cumplimiento + "No aplica" que otorga puntaje completo).
- No se inventan resultados: sin respuestas completas, el informe queda
  explícitamente "pendiente de evaluación"; nunca se pinta amarillo nada
  sin una justificación real (Principio XI).
"""
import os
from datetime import datetime

from clasificacion import clasificar_empresa, get_applicable_items
from domain.ponderacion import calcular_diagnostico_capitulo_iii, cargar_estandares_capitulo_iii
from maquetador import get_header_ft_sst_002


def _filas_capitulo_iii(respuestas):
    """Construye las filas de la tabla para Capítulo III y opcionalmente el puntaje."""
    items = cargar_estandares_capitulo_iii()
    resultado = calcular_diagnostico_capitulo_iii(respuestas) if respuestas else None
    filas = []
    n = 1
    for item in sorted(items.values(), key=lambda it: (it.estandar_num, it.numeral)):
        celda_c = celda_nc = celda_na = ""
        estilo = ""
        if resultado is not None:
            resultado_item = next(r for r in resultado.items if r.numeral == item.numeral)
            if resultado_item.criterio.value == "C":
                celda_c = "X"
            elif resultado_item.criterio.value == "NC":
                celda_nc = "X"
            else:
                celda_na = "X"
                estilo = ' style="background-color: yellow;"'
        filas.append(
            f'  <tr{estilo}><td>{n}</td><td>{item.numeral}</td>'
            f'<td>{item.descripcion}</td><td>{item.valor_item * 100:.2f}%</td>'
            f'<td>{celda_c}</td><td>{celda_nc}</td><td>{celda_na}</td></tr>'
        )
        n += 1
    return filas, resultado


def _filas_genericas(capitulo, aplicables):
    """Filas sin ponderación oficial (Capítulos I y II) — NUMERALES SOLO, sin cálculos."""
    # La descripción por numeral no está disponible en las fuentes cargadas;
    # no se inventa (Principio I). Listamos los numerales aplicables.
    numeros_soles = sorted(aplicables)
    return [
        f'  <tr><td>{i}</td><td>{numeral}</td><td>(pendiente tabla oficial)</td><td>—</td>'
        f'<td></td><td></td><td></td></tr>'
        for i, numeral in enumerate(numeros_soles, start=1)
    ], None


def generar_diagnostico_base(contexto):
    empresa = contexto['empresa']
    capitulo = clasificar_empresa(empresa['total_trabajadores'], empresa['clase_riesgo_arl'])
    aplicables = get_applicable_items(capitulo)

    respuestas = (contexto.get('estado_sistema', {})
                  .get('diagnostico', {})
                  .get('respuestas') or None)

    if capitulo == "Capítulo III":
        filas, resultado = _filas_capitulo_iii(respuestas)
    else:
        filas, resultado = _filas_genericas(capitulo, aplicables)

    informe_path = "sistema_gestion/99_INFORMES_EJECUTIVOS/Diagnostico_Inicial_Resolucion_0312.md"
    header_table = get_header_ft_sst_002(
        "DIAGNÓSTICO INICIAL SG-SST", "FT-SST-001", "E2.3.1",
        empresa['razon_social'], fecha=datetime.now().strftime("%d/%m/%Y"),
    )

    matriz_html = "<table>\n"
    matriz_html += "  <tr><th>N°</th><th>Numeral</th><th>Descripción</th><th>Valor</th><th>C</th><th>NC</th><th>NA</th></tr>\n"
    matriz_html += "\n".join(filas)
    matriz_html += "\n</table>"

    if resultado is not None:
        resumen = (
            f"### Resultado del diagnóstico (Capítulo III)\n\n"
            f"- Puntaje obtenido: **{resultado.porcentaje * 100:.2f}%**\n"
            f"- Ítems evaluados: {len(resultado.items)} / 60\n"
        )
        nota_estado = ""
    else:
        resumen = (
            "### Evaluación pendiente\n\n"
            "_El diagnóstico de Capítulo III requiere las respuestas C/NC/NA de los 60 ítems "
            "para calcular el puntaje. Sin ellas no se calcula (Principio XI de CONSTITUTION.md)._"
        )
        nota_estado = "Pendiente de evaluación"

    contexto.setdefault('estado_sistema', {})
    contexto['estado_sistema']['capitulo_aplicable'] = capitulo
    if 'diagnostico' not in contexto['estado_sistema']:
        contexto['estado_sistema']['diagnostico'] = {}
    contexto['estado_sistema']['diagnostico'].update({
        'capitulo': capitulo,
        'estado': nota_estado or "Calculado",
        'porcentaje': resultado.porcentaje if resultado else None,
    })

    contenido = f"""# Diagnóstico Inicial SG-SST

{header_table.strip()}

## Capítulo Aplicable: {capitulo}

{matriz_html}

{resumen}
"""

    os.makedirs(os.path.dirname(informe_path), exist_ok=True)
    with open(informe_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join([line.rstrip() for line in contenido.split('\n')]))

    return contexto