@echo off
echo =========================================
echo  FusionHex TimeMachine Master Build System
echo =========================================
echo [1] Build VIP Edition (CLI + Context Menus)
echo [2] Build Free Edition (GUI Dashboard Only)
set /p flavor="Select Build Type (1 or 2): "

echo [0/6] Stopping any running instances...
taskkill /F /IM tm.exe >nul 2>&1
taskkill /F /IM TimeMachine.exe >nul 2>&1

echo [1/6] Activating Virtual Environment...
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install pyinstaller >nul 2>&1

echo [2/6] Parsing config.json for Version Metadata...
python -c "import json; c=json.load(open('config.json')); f=open('version_vars.iss','w'); f.write('#define AppVer ' + repr(c['version_vip'] if '%flavor%'=='1' else c['version']) + '\n#define AppTitle ' + repr(c['vipapp_title'] if '%flavor%'=='1' else c['app_title']) + '\n')"

echo [3/6] Configuring Flavor Environment...
if "%flavor%"=="1" (
    echo VIP > build_flavor.txt
    set EXE_NAME=tm
    set ICON_FILE=vip_app_icon.ico
    set CONSOLE_FLAG=--console
    set OUTPUT_NAME=TimeMachine_VIP_Setup
) else (
    echo FREE > build_flavor.txt
    set EXE_NAME=TimeMachine
    set ICON_FILE=app_icon.ico
    set CONSOLE_FLAG=--windowed
    set OUTPUT_NAME=TimeMachine_Free_Setup
)

echo [4/6] Building Executable with PyInstaller...
if exist build rmdir /s /q build
if exist "dist\%EXE_NAME%.exe" del /f /q "dist\%EXE_NAME%.exe"
pyinstaller --onefile %CONSOLE_FLAG% --name "%EXE_NAME%" --icon="assets\%ICON_FILE%" --add-data "assets;assets" --add-data "build_flavor.txt;." main.py
del build_flavor.txt

echo [5/6] Compiling Inno Setup Installer...
"D:\Program Files\Inno Setup 6\ISCC.exe" setup.iss /DOutputDir="dist" /DOutputName="%OUTPUT_NAME%" /DExeName="%EXE_NAME%.exe" /DIconName="%ICON_FILE%" /DIsVip="%flavor%"

echo [6/6] Cleaning up raw executables...
del version_vars.iss
if exist "dist\%EXE_NAME%.exe" del /f /q "dist\%EXE_NAME%.exe"

echo =========================================
echo  Build & Packaging Complete! Check "dist".
echo =========================================
pause