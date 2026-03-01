@echo off
echo [0/4] Stopping any running tm.exe processes...
taskkill /F /IM tm.exe >nul 2>&1

echo [1/4] Cleaning old cache...
if exist build rmdir /s /q build
if exist dist\tm.exe del /f /q dist\tm.exe

echo [2/4] Setting up Virtual Environment...
if not exist venv (
    echo Creating new virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install pyinstaller

echo [3/4] Building FusionHex TimeMachine (Premium)...
:: Note: Removed --noconsole so the CLI can pipe output to the terminal
pyinstaller --onefile --name "tm" --icon="assets\app_icon.ico" --add-data "assets;assets" _timemachine.py

echo [4/4] Build Complete! Check the "dist" folder.
pause