@echo off
REM Build gtd.py into a single EXE with no console
py -m pyinstaller --onefile --windowed gtd.py 

echo.
echo Build finished!
echo Your EXE is in the "dist" folder.
pause 