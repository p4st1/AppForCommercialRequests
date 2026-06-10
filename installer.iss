#define MyAppName "MyApp"
#define MyAppVersion "1.0.0"
#define MyAppExeName "MyApp.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-47AA-9999-123456789ABC}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=YourName
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=installer-output
OutputBaseFilename=MyAppSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}

[Files]
Source: "dist\MyApp\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent