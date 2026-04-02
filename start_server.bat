@echo off
setlocal

set "PORT=8000"
set "ROOT=%~dp0"
set "PYTHON_CMD="

cd /d "%ROOT%"

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
  py -3 --version >nul 2>&1
  if %ERRORLEVEL% EQU 0 (
    set "PYTHON_CMD=py -3"
  )
)

if not defined PYTHON_CMD (
  where python >nul 2>&1
  if %ERRORLEVEL% EQU 0 (
    set "PYTHON_CMD=python"
  )
)

if not defined PYTHON_CMD (
  where python3 >nul 2>&1
  if %ERRORLEVEL% EQU 0 (
    set "PYTHON_CMD=python3"
  )
)

if not defined PYTHON_CMD (
  echo Python is not installed or not added to PATH.
  echo Please install Python from https://www.python.org/downloads/
  pause
  exit /b 1
)

echo Starting static server at http://localhost:%PORT%
%PYTHON_CMD% -m http.server %PORT%
