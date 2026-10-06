"""DIAGNÓSTICO DEMO de validación del motor de ponderación (Res. 0312/2019).

Uso: `make demo` o `uv run python scripts/demo_diagnostico.py`

Qué hace y qué NO hace:
- Lee `data/contexto_empresa.json` SOLO en memoria (no lo modifica).
- Inyecta respuestas de ejemplo (todas "C") para los ítems APLICABLES del
  capítulo de la empresa y calcula el puntaje con el motor de dominio.
- Regenera el informe `Diagnostico_Inicial_Resolucion_0312.{md,xlsx}` en
  `sistema_gestion/99_INFORMES_EJECUTIVOS/` (el xlsx replica el instrumento
  oficial Res. 0312; el md se usa como vista previa web).

ADVERTENCIA: es una validación del flujo, NO un resultado real de la empresa.
No escribe en `data/contexto_empresa.json` ni en `.env`.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from agente_sgsst.domain.clasificacion import get_applicable_items
from agente_sgsst.rendering.diagnostico import generar_diagnostico_base

CONTEXTO_PATH = Path("data/contexto_empresa.json")
INFORME_MD = Path("sistema_gestion/99_INFORMES_EJECUTIVOS/Diagnostico_Inicial_Resolucion_0312.md")


def main() -> None:
    if not CONTEXTO_PATH.exists():
        raise SystemExit(
            f"No existe {CONTEXTO_PATH}. Ejecute primero la web o el CLI para configurar la empresa."
        )

    contexto = json.loads(CONTEXTO_PATH.read_text(encoding="utf-8"))
    empresa = contexto["empresa"]
    # El capítulo aplicable lo resuelve `generar_diagnostico_base` vía clasificar_empresa().

    contexto_demo = deepcopy(contexto)
    contexto_demo["estado_sistema"]["diagnostico"] = {
        "respuestas": {numeral: ("C", "") for numeral in _aplicables_demo(contexto)}
    }

    contexto_demo = generar_diagnostico_base(contexto_demo)
    diag = contexto_demo["estado_sistema"]["diagnostico"]
    pct = diag.get("porcentaje")

    xlsx_path = INFORME_MD.with_suffix(".xlsx")

    print(f"Empresa demo: {empresa.get('razon_social')} (NIT {empresa.get('nit')})")
    print(f"Capítulo:     {diag.get('capitulo')}")
    print(f"Estado:       {diag.get('estado')}")
    print(f"Puntaje DEMO: {(pct * 100):.2f}%" if pct is not None else "Sin puntaje (pendiente)")
    print(f"Markdown:     {INFORME_MD} (vista previa web)")
    print(f"Excel:        {xlsx_path}")
    print("ADVERTENCIA: puntaje demostrativo (todas las respuestas = 'C'), no es valor real de la empresa.")


def _aplicables_demo(contexto: dict) -> set[str]:
    """Resuelve los ítems aplicables del capítulo de la empresa para construir la ronda demo."""
    from agente_sgsst.domain.clasificacion import clasificar_empresa

    empresa = contexto["empresa"]
    capitulo = clasificar_empresa(empresa["total_trabajadores"], empresa["clase_riesgo_arl"])
    return get_applicable_items(capitulo)


if __name__ == "__main__":
    main()
