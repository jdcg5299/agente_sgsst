"""
Diagnóstico inicial FT-SST-001 — hallazgos 5.3 y 5.4 de CONSTITUTION.md, y modelo oficial.

Antes: este archivo solo maquetaba una tabla HTML con columnas C/NC/NA vacías,
parseando `docs/tabla_ponderacion_resolucion_0312.md` línea por línea en runtime
(hallazgos 5.4) y sin calcular NINGÚN puntaje (hallazgo 5.3). Para Capítulos I y II,
ni siquiera había descripciones oficiales (solo numerales y "(pendiente tabla oficial)").

Ahora:
- La fuente de datos es el motor de dominio `src/domain/ponderacion.py` (JSON
  estructurado con la Tabla de Valores oficial — Art. 27 y Anexo 1).
- Se usa la MISMA tabla de 60 ítems para los tres capítulos. En Cap. I y II los
  ítems no aplicables (Arts. 3 y 9) se otorgan automáticamente como "No Aplica"
  con puntaje máximo (Art. 27 parágrafo 2) y se muestran SIN resaltado amarillo.
- Si el contexto trae respuestas guardadas, se CALCULA el puntaje real
  (sumatoria por cumplimiento + "No aplica" que otorga puntaje completo).
- No se inventan resultados: sin respuestas completas, el informe queda
  explícitamente "pendiente de evaluación" (Principio XI).
"""
import os
from datetime import datetime

from agente_sgsst.domain.clasificacion import clasificar_empresa, get_applicable_items
from agente_sgsst.domain.ponderacion import calcular_diagnostico, cargar_estandares_capitulo_iii
from agente_sgsst.rendering.maquetador import get_header_ft_sst_002


def _filas_tabla(capitulo, respuestas):
    """Construye las 60 filas de la Tabla de Valores y, si hay respuestas, el puntaje.

    Solo los numerales APLICABLES del capítulo requieren respuesta manual; los no
    aplicables (empresas <50 trabajadores, riesgo I/II/III) se otorgan automáticamente
    como "No Aplica" con puntaje completo y NO se resaltan en amarillo (no son una
    omisión del evaluador, sino la regla del Art. 27 parágrafo 2).
    """
    items = cargar_estandares_capitulo_iii()
    aplicables = get_applicable_items(capitulo)
    resultado = calcular_diagnostico(capitulo, respuestas) if respuestas else None
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
                # Amarillo solo para "No Aplica" manual (hallazgo a verificar por el
                # evaluador), NO para el "No Aplica" automático de la norma.
                if not resultado_item.automatico:
                    estilo = ' style="background-color: yellow;"'
        filas.append(
            f'  <tr{estilo}><td>{n}</td><td>{item.numeral}</td>'
            f'<td>{item.descripcion}</td><td>{item.valor_item * 100:.2f}%</td>'
            f'<td>{celda_c}</td><td>{celda_nc}</td><td>{celda_na}</td></tr>'
        )
        n += 1
    return filas, resultado


def generar_diagnostico_base(contexto):
    empresa = contexto['empresa']
    capitulo = clasificar_empresa(empresa['total_trabajadores'], empresa['clase_riesgo_arl'])
    aplicables = get_applicable_items(capitulo)

    respuestas = (contexto.get('estado_sistema', {})
                  .get('diagnostico', {})
                  .get('respuestas') or None)

    filas, resultado = _filas_tabla(capitulo, respuestas)

    informe_path = "sistema_gestion/99_INFORMES_EJECUTIVOS/Diagnostico_Inicial_Resolucion_0312.md"
    header_table = get_header_ft_sst_002(
        "DIAGNÓSTICO INICIAL SG-SST", "FT-SST-001", "E2.3.1",
        empresa['razon_social'], fecha=datetime.now().strftime("%d/%m/%Y"),
    )

    matriz_html = "<table>\n"
    matriz_html += "  <tr><th>N°</th><th>Numeral</th><th>Descripción</th><th>Valor</th><th>C</th><th>NC</th><th>NA</th></tr>\n"
    matriz_html += "\n".join(filas)
    matriz_html += "\n</table>"

    nombres_articulo = {
        "Capítulo I": "Artículo 3",
        "Capítulo II": "Artículo 9",
        "Capítulo III": "Artículo 16",
    }
    n_aplicables = len(aplicables)

    if resultado is not None:
        n_manuales = resultado.aplicables
        n_auto_na = len(resultado.items) - n_manuales
        resumen = (
            f"### Resultado del diagnóstico ({capitulo})\n\n"
            f"- Puntaje obtenido: **{resultado.porcentaje * 100:.2f}%**\n"
        )
        if capitulo == "Capítulo III":
            resumen += f"- Ítems evaluados: {len(resultado.items)} / 60\n"
        else:
            resumen += (
                f"- Ítems evaluados: {n_manuales} / {n_aplicables} aplicables "
                f"({nombres_articulo[capitulo]}); {n_auto_na} ítems no aplicables "
                "otorgados automáticamente con puntaje máximo (Art. 27, parágrafo 2).\n"
            )
        nota_estado = ""
    else:
        if capitulo == "Capítulo III":
            resumen = (
                "### Evaluación pendiente\n\n"
                "_El diagnóstico de Capítulo III requiere las respuestas C/NC/NA de los 60 ítems "
                "para calcular el puntaje. Sin ellas no se calcula (Principio XI de CONSTITUTION.md)._"
            )
        else:
            resumen = (
                "### Evaluación pendiente\n\n"
                f"_El diagnóstico de {capitulo} requiere marcar C/NC/NA en los {n_aplicables} ítems "
                f"aplicables ({nombres_articulo[capitulo]}). Los {60 - n_aplicables} ítems no aplicables "
                "se otorgarán automáticamente con puntaje máximo (Art. 27, parágrafo 2) al calcular._"
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