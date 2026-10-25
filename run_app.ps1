# QuantFin Analytics Platform Launch Script
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Starting QuantFin Analytics Platform (Asef Haque)..." -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

$VenvPython = Join-Path $ScriptDir ".venv_quant\Scripts\python.exe"

if (Test-Path $VenvPython) {
    Write-Host "Using dedicated virtual environment (.venv_quant)..." -ForegroundColor Green
    & $VenvPython -m streamlit run app.py
} else {
    Write-Host "Using system streamlit..." -ForegroundColor Yellow
    streamlit run app.py
}
