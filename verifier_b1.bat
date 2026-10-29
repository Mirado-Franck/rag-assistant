@echo off
REM ===========================================================================
REM  verifier_b1.bat - Controle d'installation + tests de la partie B1 (Jour 3)
REM  Double-clic, ou dans PowerShell : .\verifier_b1.bat
REM  Aucune politique d'execution a modifier.
REM ===========================================================================
setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo.
echo ==========================================================
echo   DocuClassif AI - verification de la partie B1
echo ==========================================================
echo Projet : %CD%
echo.

REM --- 1. Choisir l'interpreteur Python (venv en priorite) -------------------
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
  echo [1/4] Python : ECHEC - aucun Python trouve.
  echo       Installe Python 3.10+ et coche "Add python.exe to PATH".
  goto :fin_ko
)
echo [1/4] Python : %PY%
%PY% --version

REM --- 2. Streamlit ---------------------------------------------------------
echo.
echo [2/4] Streamlit
%PY% -c "import streamlit" >nul 2>&1
if errorlevel 1 (
  echo       absent - installation en cours...
  %PY% -m pip install -r interface\requirements.txt
  if errorlevel 1 goto :fin_ko
)
%PY% -c "import streamlit; print('      version ' + streamlit.__version__)"

REM --- 3. Arborescence ------------------------------------------------------
echo.
echo [3/4] Fichiers attendus
set MANQUANTS=0

call :check interface\app.py
call :check interface\nav.py
call :check interface\theme.py
call :check interface\data_mock.py
call :check interface\requirements.txt
call :check interface\assets\style.css
call :check interface\.streamlit\config.toml
call :check interface\pages\1_Upload.py
call :check interface\pages\2_Questions.py
call :check interface\pages\3_Dashboard.py
call :check tests\test_ui_b1.py

if not %MANQUANTS%==0 (
  echo.
  echo INSTALLATION B1 : INCOMPLETE - %MANQUANTS% fichier^(s^) manquant^(s^)
  echo Refais l'etape 2 du GUIDE_INSTALLATION_B1.md : extraire interface_B1.zip
  echo a la racine du projet ^(a cote du dossier interface^).
  goto :fin_ko
)

REM --- Restes de l'ancienne version ----------------------------------------
set RESTES=0
for %%F in (interface\pages\*.py) do (
  if /I not "%%~nxF"=="1_Upload.py" if /I not "%%~nxF"=="2_Questions.py" if /I not "%%~nxF"=="3_Dashboard.py" (
    set RESTES=1
    echo.
    echo       ATTENTION : fichier en trop : interface\pages\%%~nxF
  )
)
if %RESTES%==1 (
  echo       Ce sont des restes de l'ancienne version. Supprime-les :
  echo         del "interface\pages\NOM_DU_FICHIER.py"
  echo       ^(ou refais l'etape 2 du guide pour repartir propre^)
)

findstr /C:"st.page_link(" "interface\app.py" >nul 2>&1
if not errorlevel 1 (
  echo.
  echo       ATTENTION : interface\app.py est l'ANCIENNE version
  echo       ^(elle contient st.page_link vers pages\Upload.py^).
  echo       Remplace-la par celle de l'archive : GUIDE_INSTALLATION_B1.md etape 2.
)

REM --- 4. Tests -------------------------------------------------------------
echo.
echo [4/4] Tests automatiques
echo.
%PY% tests\test_ui_b1.py
set CODE=%errorlevel%

echo.
if %CODE%==0 (
  echo ==========================================================
  echo   INSTALLATION B1 : OK
  echo   TESTS : tous verts
  echo   Etape suivante : lancer_ui.bat
  echo                   ou  python -m streamlit run interface\app.py
  echo ==========================================================
  echo.
  echo Preuve a joindre au ticket :
  echo   %PY% tests\test_ui_b1.py ^> preuve_tests_B1.txt 2^>^&1
) else (
  goto :fin_ko
)
echo.
pause
exit /b 0

:check
if exist "%~1" (
  echo       OK      %~1
) else (
  echo       MANQUE  %~1
  set /a MANQUANTS+=1
)
exit /b 0

:fin_ko
echo.
echo ==========================================================
echo   PROBLEME DETECTE - voir les messages ci-dessus
echo   Depannage : GUIDE_INSTALLATION_B1.md ^(derniere section^)
echo ==========================================================
echo.
pause
exit /b 1
