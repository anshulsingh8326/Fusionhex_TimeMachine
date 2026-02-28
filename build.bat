@echo off
echo [0/4] Stopping any running TimeMachine processes...
taskkill /F /IM TimeMachine.exe >nul 2>&1

echo [1/4] Cleaning old cache...
if exist build rmdir /s /q build
if exist dist\TimeMachine.exe del /f /q dist\TimeMachine.exe

echo [2/4] Setting up Virtual Environment...
if not exist venv (
    echo Creating new virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat

echo Installing/Verifying PyInstaller...
pip install pyinstaller

echo [3/4] Building FusionHex TimeMachine...
pyinstaller --onefile --noconsole ^
--name "TimeMachine" ^
--icon="assets\app_icon.ico" ^
--add-data "assets;assets" ^
timemachine.py

echo [4/4] Build Complete! Check the "dist" folder.
pause