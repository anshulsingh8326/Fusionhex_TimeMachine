#include "version_vars.iss"

[Setup]
AppId={{D3F4A5E8-F9B2-4A73-8C21-996458AAB123}}
AppName={#AppTitle}
AppVersion={#AppVer}
AppPublisher=FusionHex
AppPublisherURL=https://www.fusionhex.com/
DefaultDirName={localappdata}\FusionHex_TimeMachine
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename={#OutputName}
SetupIconFile=assets\{#IconName}
UninstallDisplayIcon={app}\assets\{#IconName}
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
; Set to NO to prevent the native 1-minute freeze. We handle it manually in [Code].
ChangesEnvironment=no

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\{#ExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "config.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userprograms}\{#AppTitle}"; Filename: "wscript.exe"; Parameters: "//B ""{app}\run_hidden.vbs"" ""{app}\{#ExeName}"""; IconFilename: "{app}\assets\{#IconName}"; WorkingDir: "{app}"
Name: "{commondesktop}\{#AppTitle}"; Filename: "wscript.exe"; Parameters: "//B ""{app}\run_hidden.vbs"" ""{app}\{#ExeName}"""; IconFilename: "{app}\assets\{#IconName}"; WorkingDir: "{app}"; Tasks: desktopicon

[UninstallDelete]
Type: files; Name: "{app}\run_hidden.vbs"
Type: dirifempty; Name: "{app}\assets"
Type: dirifempty; Name: "{app}"

[Registry]
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\TimeMachine"; ValueType: string; ValueName: "MUIVerb"; ValueData: "{#AppTitle}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\TimeMachine"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\assets\{#IconName}"
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\TimeMachine"; ValueType: string; ValueName: "SubCommands"; ValueData: ""

Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\TimeMachine\shell\01create"; ValueType: string; ValueData: "Create Snapshot"
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\TimeMachine\shell\01create"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\assets\create.ico"
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\TimeMachine\shell\01create\command"; ValueType: string; ValueData: "wscript.exe //B ""{app}\run_hidden.vbs"" ""{app}\{#ExeName}"" _ctx_create ""%V """

Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\TimeMachine\shell\02fav"; ValueType: string; ValueData: "Create Favorite Snapshot"
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\TimeMachine\shell\02fav"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\assets\fav.ico"
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\TimeMachine\shell\02fav\command"; ValueType: string; ValueData: "wscript.exe //B ""{app}\run_hidden.vbs"" ""{app}\{#ExeName}"" _ctx_create ""%V "" --fav"

Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\TimeMachine\shell\03restore"; ValueType: string; ValueData: "Restore from Snapshot..."
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\TimeMachine\shell\03restore"; ValueType: dword; ValueName: "CommandFlags"; ValueData: "$20"
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\TimeMachine\shell\03restore"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\assets\restore.ico"
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\TimeMachine\shell\03restore\command"; ValueType: string; ValueData: "wscript.exe //B ""{app}\run_hidden.vbs"" ""{app}\{#ExeName}"" _ctx_restore ""%V """

Root: HKCU; Subkey: "Software\Classes\Directory\shell\TimeMachine"; ValueType: string; ValueName: "MUIVerb"; ValueData: "{#AppTitle}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\Directory\shell\TimeMachine"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\assets\{#IconName}"
Root: HKCU; Subkey: "Software\Classes\Directory\shell\TimeMachine"; ValueType: string; ValueName: "SubCommands"; ValueData: ""

Root: HKCU; Subkey: "Software\Classes\Directory\shell\TimeMachine\shell\01create"; ValueType: string; ValueData: "Create Snapshot"
Root: HKCU; Subkey: "Software\Classes\Directory\shell\TimeMachine\shell\01create"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\assets\create.ico"
Root: HKCU; Subkey: "Software\Classes\Directory\shell\TimeMachine\shell\01create\command"; ValueType: string; ValueData: "wscript.exe //B ""{app}\run_hidden.vbs"" ""{app}\{#ExeName}"" _ctx_create ""%1 """

Root: HKCU; Subkey: "Software\Classes\Directory\shell\TimeMachine\shell\02fav"; ValueType: string; ValueData: "Create Favorite Snapshot"
Root: HKCU; Subkey: "Software\Classes\Directory\shell\TimeMachine\shell\02fav"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\assets\fav.ico"
Root: HKCU; Subkey: "Software\Classes\Directory\shell\TimeMachine\shell\02fav\command"; ValueType: string; ValueData: "wscript.exe //B ""{app}\run_hidden.vbs"" ""{app}\{#ExeName}"" _ctx_create ""%1 "" --fav"

Root: HKCU; Subkey: "Software\Classes\Directory\shell\TimeMachine\shell\03restore"; ValueType: string; ValueData: "Restore from Snapshot..."
Root: HKCU; Subkey: "Software\Classes\Directory\shell\TimeMachine\shell\03restore"; ValueType: dword; ValueName: "CommandFlags"; ValueData: "$20"
Root: HKCU; Subkey: "Software\Classes\Directory\shell\TimeMachine\shell\03restore"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\assets\restore.ico"
Root: HKCU; Subkey: "Software\Classes\Directory\shell\TimeMachine\shell\03restore\command"; ValueType: string; ValueData: "wscript.exe //B ""{app}\run_hidden.vbs"" ""{app}\{#ExeName}"" _ctx_restore ""%1 """

Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Check: NeedsAddPath(ExpandConstant('{app}')); Flags: uninsdeletevalue

[Code]
const
  WM_SETTINGCHANGE = $001A;
  SMTO_ABORTIFHUNG = 2;

// Replaced WPARAM and LRESULT with standard Pascal Longint types
function SendMessageTimeout(hWnd: HWND; Msg: UINT; wParam: Longint; lParam: String; fuFlags: UINT; uTimeout: UINT; out lpdwResult: DWORD): Longint;
  external 'SendMessageTimeoutW@user32.dll stdcall';

function NeedsAddPath(Param: string): boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', OrigPath)
  then begin
    Result := True;
    exit;
  end;
  Result := Pos(';' + Param + ';', ';' + OrigPath + ';') = 0;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  VbsPath, VbsContent: string;
  dwResult: DWORD;
begin
  if CurStep = ssPostInstall then
  begin
    // 1. Generate the silent runner script
    VbsPath := ExpandConstant('{app}\run_hidden.vbs');
    VbsContent := 'Set objShell = CreateObject("WScript.Shell")' + #13#10 + 'cmd = ""' + #13#10 + 'For Each arg In WScript.Arguments' + #13#10 + 'cmd = cmd & """" & arg & """ "' + #13#10 + 'Next' + #13#10 + 'objShell.Run cmd, 0, False';
    SaveStringToFile(VbsPath, VbsContent, False);
    
    // 2. Broadcast the PATH update with a strict 100ms timeout
    SendMessageTimeout($FFFF, WM_SETTINGCHANGE, 0, 'Environment', SMTO_ABORTIFHUNG, 100, dwResult);
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  dwResult: DWORD;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Also broadcast the rapid refresh when uninstalling
    SendMessageTimeout($FFFF, WM_SETTINGCHANGE, 0, 'Environment', SMTO_ABORTIFHUNG, 100, dwResult);
  end;
end;