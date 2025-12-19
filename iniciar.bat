@echo off
REM ============================================
REM Script para iniciar el sistema STOCKEX
REM Inicia el servidor Django y abre el navegador automáticamente
REM ============================================

title STOCKEX - Iniciando...

echo.
echo ============================================
echo    STOCKEX - SISTEMA DE INVENTARIO
echo ============================================
echo.
echo Iniciando el servidor...
echo.

REM ============================================
REM Detectar el directorio del proyecto
REM ============================================
REM Guardar la ubicación del script
set SCRIPT_DIR=%~dp0

REM Intentar encontrar el directorio del proyecto
REM Opción 1: Si el script está en la raíz del proyecto
if exist "%~dp0manage.py" (
    set PROJECT_DIR=%~dp0
    goto :found_project
)

REM Opción 2: Buscar en la carpeta padre del script
pushd "%~dp0.."
if exist "manage.py" (
    set PROJECT_DIR=%CD%
    popd
    goto :found_project
)
popd

REM Opción 3: Buscar en Desktop/proyecto_boti (ubicación común)
set DESKTOP=%USERPROFILE%\Desktop
if exist "%DESKTOP%\proyecto_boti\manage.py" (
    set PROJECT_DIR=%DESKTOP%\proyecto_boti
    goto :found_project
)

REM Opción 4: Buscar en el directorio actual
if exist "manage.py" (
    set PROJECT_DIR=%CD%
    goto :found_project
)

REM Si no se encuentra, mostrar error
echo.
echo [ERROR] No se pudo encontrar el directorio del proyecto.
echo.
echo Por favor, asegurese de que el proyecto este en una de estas ubicaciones:
echo   - Misma carpeta que este script
echo   - Desktop\proyecto_boti
echo   - O ejecute este script desde la carpeta del proyecto
echo.
pause
exit /b 1

:found_project
REM Cambiar al directorio del proyecto
cd /d "%PROJECT_DIR%"

REM Detectar Python (intentar venv primero, luego Python del sistema)
set PYTHON_CMD=python
if exist "%PROJECT_DIR%\venv\Scripts\python.exe" (
    set PYTHON_CMD=%PROJECT_DIR%\venv\Scripts\python.exe
    echo [OK] Usando entorno virtual encontrado
) else if exist "%PROJECT_DIR%\env\Scripts\python.exe" (
    set PYTHON_CMD=%PROJECT_DIR%\env\Scripts\python.exe
    echo [OK] Usando entorno virtual encontrado
) else (
    echo [INFO] Usando Python del sistema
)

REM Verificar que Python existe
%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python no encontrado. Por favor instale Python 3.8 o superior.
    echo.
    pause
    exit /b 1
)

REM Verificar que Django está instalado
%PYTHON_CMD% -c "import django" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Django no está instalado.
    echo Instalando dependencias...
    %PYTHON_CMD% -m pip install -r "%PROJECT_DIR%\requirements.txt"
    if errorlevel 1 (
        echo.
        echo [ERROR] No se pudieron instalar las dependencias.
        echo.
        pause
        exit /b 1
    )
)

REM Verificar que la base de datos existe, si no, ejecutar migraciones
if not exist "%PROJECT_DIR%\db.sqlite3" (
    echo.
    echo [INFO] Base de datos no encontrada. Ejecutando migraciones...
    cd /d "%PROJECT_DIR%"
    %PYTHON_CMD% manage.py migrate
)

REM Obtener la IP local para mostrar en el mensaje
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set LOCAL_IP=%%a
    goto :ip_found
)
:ip_found
set LOCAL_IP=%LOCAL_IP: =%

REM Mostrar información de acceso
echo.
echo ============================================
echo    SERVIDOR INICIANDO...
echo ============================================
echo.
echo El sistema estara disponible en:
echo   - Esta PC: http://localhost:8000
echo   - Red local: http://%LOCAL_IP%:8000
echo.
echo Presione Ctrl+C para detener el servidor
echo.
echo ============================================
echo.

REM Esperar 2 segundos y abrir el navegador
timeout /t 2 /nobreak >nul
start http://localhost:8000

REM Iniciar el servidor Django
REM Usar 0.0.0.0 para permitir acceso desde otros dispositivos en la red local
%PYTHON_CMD% manage.py runserver 0.0.0.0:8000

REM Si el servidor se cierra, mantener la ventana abierta para ver errores
if errorlevel 1 (
    echo.
    echo [ERROR] El servidor se detuvo con un error.
    echo.
    pause
)

