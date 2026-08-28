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
ChangesEnvironment=yes

[Files]
Source: "dist\{#ExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "config.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userprograms}\{#AppTitle}"; Filename: "wscript.exe"; Parameters: "//B ""{app}\run_hidden.vbs"" ""{app}\{#ExeName}"""; IconFilename: "{app}\assets\{#IconName}"; WorkingDir: "{app}"

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
  VbsPath: string;
  VbsContent: string;
begin
  if CurStep = ssPostInstall then
  begin
    VbsPath := ExpandConstant('{app}\run_hidden.vbs');
    VbsContent := 'Set objShell = CreateObject("WScript.Shell")' + #13#10 + 'cmd = ""' + #13#10 + 'For Each arg In WScript.Arguments' + #13#10 + 'cmd = cmd & """" & arg & """ "' + #13#10 + 'Next' + #13#10 + 'objShell.Run cmd, 0, False';
    SaveStringToFile(VbsPath, VbsContent, False);
  end;
end;