@echo off
set EXENAME=GTDyno

REM Build gtd.py into a single EXE with no console window
py -m pyinstaller --onefile --windowed --name %EXENAME% gtd.py

echo.
echo %EXENAME% built!
pause
