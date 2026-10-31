@echo off
title DocuRAG - Assistant RAG
echo Lancement de DocuRAG - Mode 100%% OFFLINE
echo.

REM 1. Ollama
echo [1/4] Lancement Ollama...
start "Ollama" cmd /k "ollama serve"
timeout /t 3 >nul

REM 2. API FastAPI
echo [2/4] Lancement API FastAPI sur http://localhost:8000 ...
start "API FastAPI" cmd /k "call venv\Scripts\activate && uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 3 >nul

REM 3. Interface Streamlit (pas d'ouverture automatique par Streamlit : ce script ouvre le navigateur)
echo [3/4] Lancement de l'interface sur http://localhost:8501 ...
start "DocuRAG" cmd /k "call venv\Scripts\activate && streamlit run interface/app.py --server.headless true"

REM 4. Attente que l'interface reponde (60 s maximum), puis ouverture du navigateur
echo [4/4] Ouverture du navigateur des que l'interface est prete...
for /l %%i in (1,1,60) do (
  curl -s -o NUL http://localhost:8501/_stcore/health && goto ouvrir
  timeout /t 1 >nul
)
echo L'interface met plus de 60 secondes a repondre. Ouvrez http://localhost:8501 manuellement.
goto fin

:ouvrir
start "" http://localhost:8501

:fin
echo.
echo DocuRAG est lance !
echo - Interface : http://localhost:8501
echo - API Docs  : http://localhost:8000/docs
echo.
pause
