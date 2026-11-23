@echo off
chcp 65001 >nul
python -m pip install PySide6 pyinstaller
python -m PyInstaller --noconsole --onefile --name DBExplorer --icon "%~dp0muimi.ico" --add-data "%~dp0muimi.ico;." "%~dp0dbexplorer_app.py"
echo เสร็จแล้ว ไฟล์อยู่ที่ dist\DBExplorer.exe
pause
