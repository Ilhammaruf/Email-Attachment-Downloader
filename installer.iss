; Inno Setup Script for Email Attachment Downloader
; -----------------------------------------------------
; Before running this script, compile your Python app using PyInstaller:
;   cd email_attachment_downloader
;   pip install pyinstaller
;   pyinstaller --onedir --windowed --name "EmailAttachmentDownloader" --icon "icon.ico" main.py
;
; Then run this script with Inno Setup Compiler

#define MyAppName "Email Attachment Downloader"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Tsvetan Gerginov"
#define MyAppURL "https://github.com/TsvetanG2/email-attachment-downloader"
#define MyAppExeName "EmailAttachmentDownloader.exe"

[Setup]
; Unique identifier for this application (generate your own GUID)
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Output settings
OutputDir=installer_output
OutputBaseFilename=EmailAttachmentDownloader_Setup_{#MyAppVersion}
; Installer appearance
SetupIconFile=icon.ico
WizardStyle=modern
; License agreement
LicenseFile=LICENSE
; Compression
Compression=lzma2
SolidCompression=yes
; Privileges (uncomment next line if app doesn't need admin rights)
; PrivilegesRequired=lowest
; Windows version requirements
MinVersion=10.0
; Uninstall settings
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Main application files from PyInstaller output
; Adjust the source path based on your PyInstaller output location
Source: "dist\EmailAttachmentDownloader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Include README if desired
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion; DestName: "README.txt"
; Include LICENSE file
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Optional: Check if Visual C++ Redistributable is installed (needed for some PyInstaller builds)
function VCRedistNeedsInstall: Boolean;
var
  Version: String;
begin
  Result := True;
  if RegQueryStringValue(HKEY_LOCAL_MACHINE,
    'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64',
    'Version', Version) then
  begin
    Result := False;
  end;
end;

// Optional: Custom initialization
function InitializeSetup(): Boolean;
begin
  Result := True;
  // Add any pre-installation checks here
end;

// Optional: Clean up user data on uninstall (uncomment if needed)
// procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
// begin
//   if CurUninstallStep = usPostUninstall then
//   begin
//     if MsgBox('Do you want to remove all application settings and data?',
//       mbConfirmation, MB_YESNO) = IDYES then
//     begin
//       DelTree(ExpandConstant('{userappdata}\EmailAttachmentDownloader'), True, True, True);
//     end;
//   end;
// end;
