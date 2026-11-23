@echo off
cd /d "%~dp0"
set PY=
where py >nul 2>nul && set PY=py
if not defined PY where python >nul 2>nul && set PY=python
if not defined PY goto nopy
%PY% -c "import PySide6" >nul 2>nul || %PY% -m pip install PySide6
if "%PY%"=="py" (start "" pyw "%~dp0dbexplorer_app.py" %*) else (start "" pythonw "%~dp0dbexplorer_app.py" %*)
exit /b
:nopy
echo Python was not found.
echo Install Python from https://www.python.org/downloads/ and tick "Add python.exe to PATH", then run this file again.
pause
