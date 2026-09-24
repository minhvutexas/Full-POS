[Setup]
AppName=Nail POS
AppVersion=1.0
AppPublisher=My Nail Salon
DefaultDirName={autopf}\Nail POS
DefaultGroupName=Nail POS
OutputDir=installer
OutputBaseFilename=NailPOS-Setup
SetupIconFile=icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\NailPOS.exe
MinVersion=10.0
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "dist\NailPOS.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Nail POS"; Filename: "{app}\NailPOS.exe"
Name: "{group}\Uninstall Nail POS"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Nail POS"; Filename: "{app}\NailPOS.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\NailPOS.exe"; Description: "Launch Nail POS now"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
