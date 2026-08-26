; Inno Setup script for the ShopDesk Windows installer.
; Build with:  iscc packaging\installer.iss /DAppVersion=2.0.0

#ifndef AppVersion
  #define AppVersion "2.0.0"
#endif
#define AppName "ShopDesk"
#define AppPublisher "devShakib015"
#define AppUrl "https://github.com/devShakib015/BusinessMonitoringApp"
#define AppExe "ShopDesk.exe"

[Setup]
AppId={{7F3C2A54-9E1B-4F6D-8C21-5D0A6B3E77A1}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppUrl}
AppSupportURL={#AppUrl}/issues
AppUpdatesURL={#AppUrl}/releases
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
OutputDir=..\dist\installer
OutputBaseFilename=ShopDesk-{#AppVersion}-Setup
SetupIconFile=..\app\resources\shopdesk.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Shortcuts:"

[Files]
Source: "..\dist\ShopDesk\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\ShopDesk\*";         DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md";               DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\{#AppName}";        Filename: "{app}\{#AppExe}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}";  Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "Start {#AppName} now"; Flags: nowait postinstall skipifsilent

; Shop data lives in %LOCALAPPDATA%\ShopDesk and is deliberately left in place
; on uninstall -- removing a shop's sales history is not the installer's call.
[UninstallDelete]
Type: filesandordirs; Name: "{app}\_internal"
