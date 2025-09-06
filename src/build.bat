@echo off
set EXENAME=GTDyno

REM Build gtd.py into a single EXE with no console window
 pyinstaller --onefile --windowed --name GTDyno --exclude-module tkinter --exclude-module test gtd.py

echo.
echo %EXENAME% built!
pause
