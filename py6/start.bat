@echo off
setlocal

:: Set Python Path (optional if you need a specific one)
set PYTHON_EXEC=python

:: Automatically locate script directory (even if launched from elsewhere)
cd /d "%~dp0"
pip install pyside6
python.exe -m pip install --upgrade pip

:: Launch the Tor Multiple Instance Manager GUI
%PYTHON_EXEC% -m main

pause
