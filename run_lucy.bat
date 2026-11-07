@echo off
setlocal
title LUCY AI OPERATING SYSTEM
cd /d "%~dp0"

:: 1. Check known local Python installations first
if exist "%LOCALAPPDATA%\Python\bin\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Python\bin\python.exe"
    goto :found_python
)
if exist "C:\Users\admin\AppData\Local\Python\bin\python.exe" (
    set "PY_CMD=C:\Users\admin\AppData\Local\Python\bin\python.exe"
    goto :found_python
)
if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
    goto :found_python
)
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    goto :found_python
)
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    goto :found_python
)
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    goto :found_python
)

:: 2. Check py launcher
py -0 >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    goto :found_python
)

:: 3. Check python in PATH (skipping fake WindowsApps stubs)
for /f "delims=" %%I in ('where python 2^>nul') do (
    echo "%%I" | findstr /i "WindowsApps" >nul
    if errorlevel 1 (
        set "PY_CMD=%%I"
        goto :found_python
    )
)

echo [ERROR] No working Python 3 found.
echo Please ensure Python is installed and added to your PATH.
pause
exit /b 1

:found_python
"%PY_CMD%" run_lucy.py %*

if %errorlevel% neq 0 (
    echo.
    echo Lucy exited with code %errorlevel%.
    pause
)
