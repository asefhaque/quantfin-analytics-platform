@echo off
title QuantFin Analytics Platform - Asef Haque
cd /d "%~dp0"
echo ========================================================
echo Starting QuantFin Analytics Platform...
echo ========================================================
if exist ".venv_quant\Scripts\python.exe" (
    echo Using dedicated virtual environment (.venv_quant)...
    ".venv_quant\Scripts\python.exe" -m streamlit run app.py
) else (
    echo Using system Python / Streamlit...
    streamlit run app.py
)
pause
