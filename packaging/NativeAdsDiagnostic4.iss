; Side-by-side Diagnostic4 installer. Authentication remains untouched.
#ifndef BundleRoot
  #error BundleRoot is required
#endif
#ifndef OutputDir
  #error OutputDir is required
#endif
[Setup]
AppId={{D4F4C42A-9D03-4E62-9E18-2C7E0C7C41D4}
AppName=Komyst - Native Ads Diagnostic 4
AppVersion=0.9.0-beta.44
DefaultDirName={localappdata}\Programs\Komyst-NativeAdsD4
DefaultGroupName=Komyst - Native Ads D4
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
OutputDir={#OutputDir}
OutputBaseFilename=Komyst-NativeAds-Diagnostic4-Setup-x64
Compression=lzma2
SolidCompression=yes
CloseApplications=no
DisableProgramGroupPage=yes
Uninstallable=yes
ChangesEnvironment=no
CreateUninstallRegKey=yes
UninstallDisplayName=Komyst - Native Ads Diagnostic 4
[Files]
Source: "{#BundleRoot}\Komyst\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
[Icons]
Name: "{group}\Komyst - Native Ads D4"; Filename: "{app}\Komyst-NativeAdsD4.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Komyst - Native Ads D4"; Filename: "{app}\Komyst-NativeAdsD4.exe"; WorkingDir: "{app}"
[Run]
Filename: "{app}\Komyst-NativeAdsD4.exe"; Description: "Iniciar Komyst - Native Ads D4"; Flags: postinstall skipifsilent nowait
