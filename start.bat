@echo off
echo Lancement DocuClassif AI - Mode 100%% OFFLINE
echo.

REM 1. Ollama
echo [1/3] Lancement Ollama...
start "Ollama" cmd /k "ollama serve"
timeout /t 3 >nul

REM 2. API FastAPI
echo [2/3] Lancement API FastAPI sur http://localhost:8000 ...
start "API FastAPI" cmd /k "call venv\Scripts\activate && uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 3 >nul

REM 3. Interface Streamlit
echo [3/3] Lancement Streamlit sur http://localhost:8501 ...
start "Streamlit" cmd /k "call venv\Scripts\activate && streamlit run interface/app.py"

echo.
echo Tous les services sont lances !
echo - API Docs : http://localhost:8000/docs
echo - Interface : http://localhost:8501
pause
