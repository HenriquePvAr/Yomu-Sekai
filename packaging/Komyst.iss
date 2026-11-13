; Komyst Beta installer — 14D.2 frozen contract.
; BundleRoot is mandatory and must be supplied by the controlled build command.
#ifndef BundleRoot
  #error BundleRoot must point to the validated 14B.2 ONEDIR directory
#endif
#ifndef OutputDir
  #error OutputDir must point to the dedicated local installer artifact directory
#endif
#ifndef ProductVersion
  #error ProductVersion must be supplied from app_version.BUILD_VERSION by the release tool
#endif
[Setup]
AppId={{cff6c710-2b7d-4a09-8f25-e32ea363430f}
AppName=Komyst
AppVersion={#ProductVersion}
SetupIconFile={#SourcePath}\..\assets\branding\generated\komyst.ico
UninstallDisplayIcon={app}\_internal\assets\branding\generated\komyst.ico
DefaultDirName={localappdata}\Programs\Komyst
DefaultGroupName=Komyst
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
OutputDir={#OutputDir}
OutputBaseFilename=Komyst-{#ProductVersion}-Setup-x64
Compression=lzma2
SolidCompression=yes
CloseApplications=yes
RestartApplications=no
DisableProgramGroupPage=yes
Uninstallable=yes
ChangesEnvironment=no
CreateUninstallRegKey=yes
UninstallDisplayName=Komyst
SetupLogging=yes
UninstallFilesDir={app}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked

[InstallDelete]
; Beta2 copied the PyInstaller wrapper directory into {app}. Remove only that
; known legacy payload directory before laying down the flat beta3 payload.
Type: filesandordirs; Name: "{app}\Komyst"

[Files]
; BundleRoot is the candidate root. PyInstaller's COLLECT directory is the
; second Komyst level; copy its contents directly into {app}.
Source: "{#BundleRoot}\Komyst\Komyst\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

; Remove only disposable per-user execution state.  The device identity is deliberately
; stored under %LOCALAPPDATA%\Komyst\device-identity.bin and is not covered here, so
; reinstalling the app does not silently register a second device.
[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\Komyst\runtime\jobs.sqlite3"
Type: filesandordirs; Name: "{localappdata}\Komyst\runtime\ui_history.json"
Type: filesandordirs; Name: "{localappdata}\Komyst\runtime\ui_hidden_history.json"
Type: filesandordirs; Name: "{localappdata}\Komyst\runtime\logs"
Type: filesandordirs; Name: "{localappdata}\Komyst\runtime\cache"
Type: filesandordirs; Name: "{localappdata}\Komyst\runtime\output"
Type: filesandordirs; Name: "{localappdata}\Komyst\runtime\temp"
Type: filesandordirs; Name: "{localappdata}\Komyst\cache"
Type: filesandordirs; Name: "{localappdata}\Komyst\output"
Type: filesandordirs; Name: "{localappdata}\Komyst\temp"
; Legacy beta layouts that could otherwise resurrect RETOMAR cards after reinstall.
Type: filesandordirs; Name: "{localappdata}\Komyst\jobs.sqlite3"
Type: filesandordirs; Name: "{localappdata}\Komyst\ui_history.json"
Type: filesandordirs; Name: "{localappdata}\Komyst\ui_hidden_history.json"
Type: filesandordirs; Name: "{localappdata}\Komyst\logs"
Type: filesandordirs; Name: "{localappdata}\Komyst\.cache"

; Close only the product's own executable tree before Inno removes {app}.  This
; covers the desktop shell plus its frozen UI/worker children and prevents an
; orphaned Komyst.exe from keeping the install directory alive.
[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/F /T /IM Komyst.exe"; Flags: runhidden waituntilterminated skipifdoesntexist; RunOnceId: "KomystShutdown"

[Icons]
Name: "{group}\Komyst"; Filename: "{app}\Komyst.exe"; WorkingDir: "{app}"; IconFilename: "{app}\_internal\assets\branding\generated\komyst.ico"; IconIndex: 0
Name: "{autodesktop}\Komyst"; Filename: "{app}\Komyst.exe"; WorkingDir: "{app}"; IconFilename: "{app}\_internal\assets\branding\generated\komyst.ico"; IconIndex: 0; Tasks: desktopicon

[Run]
Filename: "{app}\Komyst.exe"; Description: "Iniciar o Komyst"; Flags: postinstall skipifsilent nowait
