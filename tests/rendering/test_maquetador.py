"""Tests del maquetador FT-SST-002 (hallazgos 5.8 y 5.9)."""
from __future__ import annotations

from pathlib import Path

from agente_sgsst.rendering.maquetador import get_header_ft_sst_002, _celda_logo


class TestCeldaLogo:
    def test_placeholder_cuando_no_logo(self):
        assert _celda_logo(None) == "Logo"
        assert _celda_logo("") == "Logo"
        assert _celda_logo("/no/existe.png") == "Logo"

    def test_imagen_markdown_cuando_logo_valido(self, tmp_path):
        logo = tmp_path / "logo.png"
        logo.write_bytes(b"\x89PNG fake")
        resultado = _celda_logo(str(logo))
        assert resultado.startswith("![Logo](")
        assert str(logo) in resultado


class TestHeaderFtSst002:
    def test_contiene_campos_obligatorios(self):
        header = get_header_ft_sst_002(
            "Política de SST", "FT-SST-012", "E2.1.1",
            "Acme S.A.S.", "13/09/2026",
        )
        assert "FT-SST-012" in header
        assert "Acme S.A.S." in header
        assert "E2.1.1" in header
        assert "13/09/2026" in header
        assert "| Logo |" in header

    def test_logo_imagen_markdown_cuando_path_valido(self, tmp_path):
        logo = tmp_path / "logo.png"
        logo.write_bytes(b"\x89PNG fake")
        header = get_header_ft_sst_002(
            "Acta de Asignación", "FT-SST-002", "E1.1.1",
            "Empresa X", "01/01/2026", logo_path=str(logo),
        )
        assert f"![Logo]({logo})" in header
