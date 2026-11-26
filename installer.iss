[Setup]
AppName=venUs Suite
AppVersion=2.0.0
AppPublisher=venUs
DefaultDirName={localappdata}\venUs Suite
DefaultGroupName=venUs Suite
OutputDir=release
OutputBaseFilename=venUs_Suite_Setup_v2.0.0
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Créer un raccourci sur le Bureau"; GroupDescription: "Raccourcis :"

[Files]
Source: "dist\venUs Suite.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\venUs Suite"; Filename: "{app}\venUs Suite.exe"
Name: "{autodesktop}\venUs Suite"; Filename: "{app}\venUs Suite.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\venUs Suite.exe"; Description: "Lancer venUs Suite"; Flags: nowait postinstall skipifsilent