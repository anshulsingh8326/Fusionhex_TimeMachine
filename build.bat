@echo off
echo [0/4] Stopping any running TimeMachine processes...
:: /F forcefully kills it, /IM targets the image name. The >nul hides errors if it's not running.
taskkill /F /IM TimeMachine.exe >nul 2>&1

echo [1/4] Cleaning old cache...
if exist build rmdir /s /q build
if exist dist\TimeMachine.exe del /f /q dist\TimeMachine.exe

echo [2/4] Activating Virtual Environment...
call venv\Scripts\activate.bat

echo [3/4] Building FusionHex TimeMachine...
pyinstaller --onefile --noconsole ^
--name "TimeMachine" ^
--icon="assets\app_icon.ico" ^
--add-data "assets;assets" ^
timemachine.py

echo [4/4] Build Complete! Check the "dist" folder.
pause