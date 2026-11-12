; Side-by-side diagnostic installer for bounded native ad geometry updates.
#ifndef BundleRoot
  #error BundleRoot is required
#endif
#ifndef OutputDir
  #error OutputDir is required
#endif
[Setup]
AppId={{D4G-EVENT-STORM-FIX-20260915}
AppName=Komyst - Native Ads Event Storm Fix
AppVersion=0.9.0-beta.44
DefaultDirName={localappdata}\Programs\Komyst-NativeAdsEventStormFix
DefaultGroupName=Komyst - Native Ads Event Storm Fix
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
OutputDir={#OutputDir}
OutputBaseFilename=Komyst-NativeAds-EventStormFix-Setup-x64
Compression=lzma2
SolidCompression=yes
CloseApplications=no
DisableProgramGroupPage=yes
Uninstallable=yes
ChangesEnvironment=no
CreateUninstallRegKey=yes
[Files]
Source: "{#BundleRoot}\Komyst\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
[Icons]
Name: "{group}\Komyst - Native Ads Event Storm Fix"; Filename: "{app}\Komyst.exe"; WorkingDir: "{app}"
[Run]
Filename: "{app}\Komyst.exe"; Description: "Iniciar Komyst - Native Ads Event Storm Fix"; Flags: postinstall skipifsilent nowait
