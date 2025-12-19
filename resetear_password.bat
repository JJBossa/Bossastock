@echo off
REM ============================================
REM Script para resetear contraseña de usuario
REM ============================================

title Resetear Contraseña - STOCKEX

echo.
echo ============================================
echo    RESETEAR CONTRASEÑA DE USUARIO
echo ============================================
echo.

REM Cambiar al directorio del script
cd /d "%~dp0"

REM Detectar Python
set PYTHON_CMD=python
if exist "venv\Scripts\python.exe" (
    set PYTHON_CMD=venv\Scripts\python.exe
) else if exist "env\Scripts\python.exe" (
    set PYTHON_CMD=env\Scripts\python.exe
)

echo.
echo Ingrese el nombre de usuario a resetear:
set /p USERNAME=
echo.
echo Ingrese la nueva contraseña:
set /p PASSWORD=
echo.

echo Reseteando contraseña...
%PYTHON_CMD% manage.py shell -c "from django.contrib.auth.models import User; u = User.objects.get(username='%USERNAME%'); u.set_password('%PASSWORD%'); u.save(); print(f'Contraseña actualizada para usuario: {u.username}')"

if errorlevel 1 (
    echo.
    echo [ERROR] No se pudo resetear la contraseña. Verifique que el usuario existe.
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo [OK] Contraseña actualizada exitosamente!
    echo.
    pause
)

