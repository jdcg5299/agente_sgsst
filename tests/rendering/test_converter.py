"""
Tests del conversor Markdown -> docx (hallazgo 5.6 de CONSTITUTION.md).

Antes, el fallback sin Pandoc convertía las filas de tabla Markdown en párrafos
de texto plano (`doc.add_paragraph(line_str)`), rompiendo el encabezado FT-SST-002
en entornos sin Pandoc. Estos tests verifican que ahora se construye una tabla
Word real con python-docx.
"""

from __future__ import annotations


from agente_sgsst.rendering.converter import _convertir_con_python_docx, _parsear_tabla, _ruta_imagen_markdown

PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06"
    b"\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xfc\xcf\xc0P\x0f\x00"
    b"\x05\x04\x01\x80\x08\x98\xca!\x00\x00\x00\x00IEND\xaeB`\x82"
)


class TestParseoTabla:
    def test_ignora_fila_separadora(self):
        filas = [
            "| A | B |",
            "|---|---|",
            "| x | y |",
        ]
        matriz = _parsear_tabla(filas)
        assert matriz == [["A", "B"], ["x", "y"]]

    def test_recorta_pipes_extremos_y_espacios(self):
        matriz = _parsear_tabla(["| 1 |  2  |"])
        assert matriz == [["1", "2"]]


class TestConversionDocx:
    def test_tabla_markdown_se_convierte_en_tabla_word(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text(
            "# Encabezado FT-SST-002\n\n"
            "| Logo | SISTEMA | CODIGO |\n"
            "| :---: | :--- | :---: |\n"
            "| | Titulo | FT-SST-001 |\n",
            encoding="utf-8",
        )
        out = tmp_path / "doc.docx"

        ok = _convertir_con_python_docx(str(md), str(out))
        assert ok is True
        assert out.exists()

        import docx

        document = docx.Document(str(out))
        assert len(document.tables) == 1
        tabla = document.tables[0]
        # 2 filas de datos (la separadora se descarta)
        assert len(tabla.rows) == 2
        assert len(tabla.columns) == 3
        assert tabla.rows[0].cells[0].text == "Logo"  # encabezado
        assert tabla.rows[1].cells[2].text == "FT-SST-001"  # dato

    def test_encabezado_markdown_se_mantiene_como_heading(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text("# Diagnóstico Inicial\n\nPárrafo introductorio.\n", encoding="utf-8")
        out = tmp_path / "doc.docx"

        assert _convertir_con_python_docx(str(md), str(out)) is True

        import docx

        document = docx.Document(str(out))
        assert document.paragraphs[0].text == "Diagnóstico Inicial"


class TestTablaHtmlInformeDiagnostico:
    """Tablas HTML (matriz del diagnóstico Res. 0312) -> tablas Word reales."""

    def _convierte(self, md, tmp_path):
        md_path = tmp_path / "doc.md"
        md_path.write_text(md, encoding="utf-8")
        out = tmp_path / "doc.docx"
        assert _convertir_con_python_docx(str(md_path), str(out)) is True
        return out

    def test_tabla_html_con_colspan_y_amarillo(self, tmp_path):
        md = (
            "<table>\n"
            "  <tr><th>Ciclo</th><th>Numeral</th><th>Desc</th><th>Valor</th>"
            "<th>C</th><th>NC</th><th>NA</th></tr>\n"
            "  <tr><td>PLANEAR</td><td>1.1.1</td><td>Resp del SG-SST</td>"
            "<td>0.50%</td><td>X</td><td></td><td></td></tr>\n"
            '  <tr><td colspan="7">PORCENTAJE TOTAL DEL ESTÁNDAR</td></tr>\n'
            '  <tr style="background-color: yellow;"><td></td><td>1.1.2</td>'
            "<td>NA manual</td><td>0.50%</td><td></td><td></td><td>X</td></tr>\n"
            "</table>\n"
        )
        out = self._convierte(md, tmp_path)

        import docx
        from docx.enum.text import WD_COLOR_INDEX

        document = docx.Document(str(out))
        assert len(document.tables) == 1
        tabla = document.tables[0]
        assert len(tabla.rows) == 4
        assert tabla.rows[0].cells[0].text == "Ciclo"
        # colspan: la fila del subtotal queda con su texto en la primera celda
        assert tabla.rows[2].cells[0].text == "PORCENTAJE TOTAL DEL ESTÁNDAR"
        # fila amarilla: el run queda resaltado en amarillo
        run = tabla.rows[3].cells[1].paragraphs[0].runs[0]
        assert run.font.highlight_color == WD_COLOR_INDEX.YELLOW

    def test_tabla_html_se_para_en_encabezados_markdown(self, tmp_path):
        md = (
            "# Diagnóstico\n\n"
            "<table>\n<tr><td>a</td><td>b</td></tr>\n</table>\n\n"
            "## Resultado\n\nPárrafo final.\n"
        )
        out = self._convierte(md, tmp_path)

        import docx

        document = docx.Document(str(out))
        assert len(document.tables) == 1
        assert document.paragraphs[0].text == "Diagnóstico"
        assert any(p.text == "Resultado" for p in document.paragraphs)
        assert any("Párrafo final" in p.text for p in document.paragraphs)


class TestImagenLogo:
    def test_ruta_imagen_markdown_detecta_sintaxis(self):
        assert _ruta_imagen_markdown("![Logo](C:/logos/empresa.png)") == "C:/logos/empresa.png"
        assert _ruta_imagen_markdown("Logo") is None
        assert _ruta_imagen_markdown("") is None

    def test_logo_se_incrusta_en_celda_de_tabla(self, tmp_path):
        logo = tmp_path / "logo.png"
        logo.write_bytes(PNG_1X1)

        md = tmp_path / "logo.md"
        md.write_text(
            "| Logo | SISTEMA | CÓDIGO |\n"
            "| :---: | :--- | :---: |\n"
            f"| ![Logo]({logo}) | Título | FT-SST-001 |\n",
            encoding="utf-8",
        )
        out = tmp_path / "logo.docx"

        assert _convertir_con_python_docx(str(md), str(out)) is True

        import docx

        document = docx.Document(str(out))
        assert len(document.inline_shapes) == 1
        tabla = document.tables[0]
        # La celda del logo ya no contiene texto plano, contiene la imagen
        assert tabla.rows[1].cells[0].text == ""
        assert "Título" in tabla.rows[1].cells[1].text

    def test_logo_inexistente_degrada_a_mensaje(self, tmp_path):
        md = tmp_path / "logo.md"
        md.write_text(
            "| Logo | SISTEMA | CÓDIGO |\n"
            "| :---: | :--- | :---: |\n"
            "| ![Logo](/no/existe.png) | Título | FT-SST-001 |\n",
            encoding="utf-8",
        )
        out = tmp_path / "logo.docx"

        assert _convertir_con_python_docx(str(md), str(out)) is True

        import docx

        document = docx.Document(str(out))
        tabla = document.tables[0]
        assert "no encontrado" in tabla.rows[1].cells[0].text
