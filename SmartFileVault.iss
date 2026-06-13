; Inno Setup Script for Smart File Vault
; Version 1.0
; Generated for The DevOps Rite

#define MyAppName "Smart File Vault"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "The DevOps Rite"
#define MyAppURL "https://thedevopsrite.in"
#define MyAppExeName "SmartFileVault.exe"
#define MyAppDescription "Secure file encryption and management application with two-factor password protection and recovery codes"

; Source paths
#define SourceDir "C:\Users\Shivam\Desktop\Smart File Vault"
#define BuildDir SourceDir + "\dist"

[Setup]
; Basic setup information
AppId={{12345678-1234-1234-1234-123456789012}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/support
AppUpdatesURL={#MyAppURL}/updates

; Installation directory
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=no
AllowNoIcons=no

; Installer appearance - Modern style (icon embedded in exe)
SetupIconFile={#SourceDir}\appLogo.ico
WizardImageFile={#SourceDir}\WizardImage.bmp
WizardSmallImageFile={#SourceDir}\WizardSmallImage.bmp
WizardStyle=modern

; Compiler settings
Compression=lzma
SolidCompression=yes
VersionInfoVersion=1.0.0.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
VersionInfoOriginalFilename={#MyAppExeName}
VersionInfoDescription={#MyAppDescription}
OutputDir={#BuildDir}
OutputBaseFilename=SmartFileVault-1.0.0-Setup

; User rights
PrivilegesRequired=admin
ShowTasksTreeLines=yes

; License file
LicenseFile={#SourceDir}\LICENSE

; Uninstall settings
Uninstallable=yes

; Registry
ChangesAssociations=yes
DisableWelcomePage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode
Name: "associatefiles"; Description: "Associate .vault files with {#MyAppName}"; GroupDescription: "File Associations"; Flags: unchecked

[Files]
; Main executable (all Python code is compiled into this file)
Source: "{#BuildDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Essential runtime files
Source: "{#SourceDir}\appLogo.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Registry]
Root: HKCU; Subkey: "Software\Classes\.vault"; ValueType: string; ValueName: ""; ValueData: "SmartFileVaultFile"; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\SmartFileVaultFile"; ValueType: string; ValueName: ""; ValueData: "{#MyAppName} File"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\SmartFileVaultFile\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKCU; Subkey: "Software\Classes\SmartFileVaultFile\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

[UninstallDelete]
Type: dirifempty; Name: "{userappdata}\SmartFileVault"
