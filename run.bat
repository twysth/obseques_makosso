@echo off
setlocal

title Obseques MAKOSSO POATHY Jean Pierre

cd /d "%~dp0"

echo ============================================================
echo   OBSEQUES MAKOSSO POATHY JEAN PIERRE
echo   Lanceur de l'application
echo ============================================================
echo.

REM ============================================================
REM VERIFICATION DE PYTHON
REM ============================================================

where python >nul 2>&1

if errorlevel 1 (
    echo [ERREUR] Python n'est pas disponible dans le PATH.
    echo.
    echo Installez Python 3.12 puis redemarrez Windows.
    echo.
    pause
    exit /b 1
)

echo [OK] Python detecte.
python --version

echo.

REM ============================================================
REM VERIFICATION DE RUN.PY
REM ============================================================

if not exist "run.py" (
    echo [ERREUR] Le fichier run.py est introuvable.
    echo.
    pause
    exit /b 1
)

echo [OK] run.py detecte.

echo.

REM ============================================================
REM LANCEMENT
REM ============================================================

echo ============================================================
echo   Demarrage de Flask et Streamlit...
echo ============================================================
echo.

python "run.py"

echo.
echo ============================================================
echo   APPLICATION ARRETEE
echo ============================================================
echo.

pause

endlocal