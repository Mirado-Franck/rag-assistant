@echo off
REM ===========================================================
REM  lancer_ui.bat - Lance l'interface DocuClassif AI (B1)
REM  Double-clic, puis ouvrir http://localhost:8501
REM ===========================================================
setlocal
cd /d "%~dp0"

set PY=
if exist "venv\Scripts\python.exe" set PY=venv\Scripts\python.exe
if not defined PY if exist ".venv\Scripts\python.exe" set PY=.venv\Scripts\python.exe
if not defined PY (
  py --version >nul 2>&1
  if not errorlevel 1 set PY=py
)
if not defined PY (
  python --version >nul 2>&1
  if not errorlevel 1 set PY=python
)
if not defined PY (
  echo [ERREUR] Python introuvable.
  pause
  exit /b 1
)

%PY% -c "import streamlit" >nul 2>&1
if errorlevel 1 (
  echo Installation des dependances...
  %PY% -m pip install -r interface\requirements.txt
)

if not exist "interface\app.py" (
  echo [ERREUR] interface\app.py introuvable.
  echo Extrais interface_B1.zip a la racine du projet ^(voir GUIDE_INSTALLATION_B1.md^).
  pause
  exit /b 1
)

echo.
echo Interface : http://localhost:8501
echo Ctrl+C pour arreter.
echo.
%PY% -m streamlit run interface\app.py
pause
