# ============================================================
#  Agente SG-SST - Arranque de la interfaz web (Streamlit)
#  Uso:  .\run_web.ps1
#  La app queda disponible mientras esta ventana esté abierta.
#  URL:  http://localhost:8501
# ============================================================

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host ""
Write-Host "  Agente SG-SST - Interfaz web" -ForegroundColor Cyan
Write-Host "  Abriendo... http://localhost:8501" -ForegroundColor Green
Write-Host "  (Mantén esta ventana abierta. Ctrl+C para detener)." -ForegroundColor DarkGray
Write-Host ""

uv run streamlit run app.py