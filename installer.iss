; ============================================================
; ENILINE Media Player Installer
; Build:
;   iscc installer.iss
;
; Expected application directory:
;   dist\ENILINE_Media_Player\
;
; Expected executable:
;   dist\ENILINE_Media_Player\ENILINE_Media_Player.exe
; ============================================================

#define MyAppName "ENILINE Media Player"
#define MyAppExeName "ENILINE_Media_Player.exe"
#define MyAppVersion "1.1"
#define MyAppPublisher "ENILINE"
#define MyAppURL "https://github.com/ENILINE/ENILINE_Media_Player"
#define MyAppSource "dist\ENILINE_Media_Player"

[Setup]
; ------------------------------------------------------------
; Application identity
; ------------------------------------------------------------
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; ------------------------------------------------------------
; Installation location
; ------------------------------------------------------------
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}

; Require administrator privileges because this installer
; registers HKLM file associations and RegisteredApplications.
PrivilegesRequired=admin

; ------------------------------------------------------------
; Installer appearance / behavior
; ------------------------------------------------------------
AllowNoIcons=yes
WizardStyle=modern

Compression=lzma2
SolidCompression=yes

; Use 64-bit Program Files on x64 Windows.
ArchitecturesInstallIn64BitMode=x64compatible

; Tell Windows that this installer changes file associations.
ChangesAssociations=yes

; ------------------------------------------------------------
; Output
; ------------------------------------------------------------
OutputDir=dist
OutputBaseFilename=ENILINE_Media_Player_Setup

; ------------------------------------------------------------
; Uninstaller metadata
; ------------------------------------------------------------
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; \
    Description: "创建桌面快捷方式"; \
    GroupDescription: "附加图标:"; \
    Flags: unchecked

[Files]
; Copy the complete application directory into {app}.
Source: "{#MyAppSource}\*"; \
    DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; ------------------------------------------------------------
; Start Menu
; ------------------------------------------------------------

Name: "{group}\{#MyAppName}"; \
    Filename: "{app}\{#MyAppExeName}"

Name: "{group}\卸载 {#MyAppName}"; \
    Filename: "{uninstallexe}"

; ------------------------------------------------------------
; Desktop shortcut
; ------------------------------------------------------------

Name: "{autodesktop}\{#MyAppName}"; \
    Filename: "{app}\{#MyAppExeName}"; \
    Tasks: desktopicon

[Run]
; ------------------------------------------------------------
; Launch application after installation
; ------------------------------------------------------------

Filename: "{app}\{#MyAppExeName}"; \
    Description: "启动 {#MyAppName}"; \
    Flags: nowait postinstall skipifsilent

[Registry]
; ============================================================
; RegisteredApplications
;
; This registers the application with Windows so it can appear
; in Windows "Default apps" / "Choose defaults by file type".
; ============================================================

Root: HKLM; \
    Subkey: "SOFTWARE\RegisteredApplications"; \
    ValueType: string; \
    ValueName: "{#MyAppName}"; \
    ValueData: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}\Capabilities"; \
    Flags: uninsdeletevalue

; ============================================================
; Application Capabilities
; ============================================================

Root: HKLM; \
    Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}\Capabilities"; \
    ValueType: string; \
    ValueName: "ApplicationName"; \
    ValueData: "{#MyAppName}"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}\Capabilities"; \
    ValueType: string; \
    ValueName: "ApplicationDescription"; \
    ValueData: "ENILINE Media Player - Windows 媒体播放器"; \
    Flags: uninsdeletekey

; ============================================================
; MP4
; ============================================================

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\.mp4\OpenWithProgids"; \
    ValueType: string; \
    ValueName: "{#MyAppName}.mp4"; \
    ValueData: ""; \
    Flags: uninsdeletevalue

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.mp4"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{#MyAppName} mp4"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.mp4\DefaultIcon"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{app}\{#MyAppExeName},0"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.mp4\shell\open\command"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: """{app}\{#MyAppExeName}"" ""%1"""; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}\Capabilities\FileAssociations"; \
    ValueType: string; \
    ValueName: ".mp4"; \
    ValueData: "{#MyAppName}.mp4"; \
    Flags: uninsdeletevalue

; ============================================================
; MKV
; ============================================================

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\.mkv\OpenWithProgids"; \
    ValueType: string; \
    ValueName: "{#MyAppName}.mkv"; \
    ValueData: ""; \
    Flags: uninsdeletevalue

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.mkv"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{#MyAppName} mkv"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.mkv\DefaultIcon"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{app}\{#MyAppExeName},0"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.mkv\shell\open\command"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: """{app}\{#MyAppExeName}"" ""%1"""; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}\Capabilities\FileAssociations"; \
    ValueType: string; \
    ValueName: ".mkv"; \
    ValueData: "{#MyAppName}.mkv"; \
    Flags: uninsdeletevalue

; ============================================================
; AVI
; ============================================================

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\.avi\OpenWithProgids"; \
    ValueType: string; \
    ValueName: "{#MyAppName}.avi"; \
    ValueData: ""; \
    Flags: uninsdeletevalue

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.avi"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{#MyAppName} avi"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.avi\DefaultIcon"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{app}\{#MyAppExeName},0"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.avi\shell\open\command"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: """{app}\{#MyAppExeName}"" ""%1"""; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}\Capabilities\FileAssociations"; \
    ValueType: string; \
    ValueName: ".avi"; \
    ValueData: "{#MyAppName}.avi"; \
    Flags: uninsdeletevalue

; ============================================================
; MOV
; ============================================================

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\.mov\OpenWithProgids"; \
    ValueType: string; \
    ValueName: "{#MyAppName}.mov"; \
    ValueData: ""; \
    Flags: uninsdeletevalue

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.mov"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{#MyAppName} mov"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.mov\DefaultIcon"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{app}\{#MyAppExeName},0"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.mov\shell\open\command"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: """{app}\{#MyAppExeName}"" ""%1"""; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}\Capabilities\FileAssociations"; \
    ValueType: string; \
    ValueName: ".mov"; \
    ValueData: "{#MyAppName}.mov"; \
    Flags: uninsdeletevalue

; ============================================================
; WMV
; ============================================================

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\.wmv\OpenWithProgids"; \
    ValueType: string; \
    ValueName: "{#MyAppName}.wmv"; \
    ValueData: ""; \
    Flags: uninsdeletevalue

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.wmv"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{#MyAppName} wmv"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.wmv\DefaultIcon"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{app}\{#MyAppExeName},0"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.wmv\shell\open\command"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: """{app}\{#MyAppExeName}"" ""%1"""; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}\Capabilities\FileAssociations"; \
    ValueType: string; \
    ValueName: ".wmv"; \
    ValueData: "{#MyAppName}.wmv"; \
    Flags: uninsdeletevalue

; ============================================================
; FLV
; ============================================================

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\.flv\OpenWithProgids"; \
    ValueType: string; \
    ValueName: "{#MyAppName}.flv"; \
    ValueData: ""; \
    Flags: uninsdeletevalue

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.flv"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{#MyAppName} flv"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.flv\DefaultIcon"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{app}\{#MyAppExeName},0"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.flv\shell\open\command"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: """{app}\{#MyAppExeName}"" ""%1"""; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}\Capabilities\FileAssociations"; \
    ValueType: string; \
    ValueName: ".flv"; \
    ValueData: "{#MyAppName}.flv"; \
    Flags: uninsdeletevalue

; ============================================================
; WEBM
; ============================================================

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\.webm\OpenWithProgids"; \
    ValueType: string; \
    ValueName: "{#MyAppName}.webm"; \
    ValueData: ""; \
    Flags: uninsdeletevalue

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.webm"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{#MyAppName} webm"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.webm\DefaultIcon"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{app}\{#MyAppExeName},0"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.webm\shell\open\command"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: """{app}\{#MyAppExeName}"" ""%1"""; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}\Capabilities\FileAssociations"; \
    ValueType: string; \
    ValueName: ".webm"; \
    ValueData: "{#MyAppName}.webm"; \
    Flags: uninsdeletevalue

; ============================================================
; TS
; ============================================================

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\.ts\OpenWithProgids"; \
    ValueType: string; \
    ValueName: "{#MyAppName}.ts"; \
    ValueData: ""; \
    Flags: uninsdeletevalue

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.ts"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{#MyAppName} ts"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.ts\DefaultIcon"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{app}\{#MyAppExeName},0"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.ts\shell\open\command"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: """{app}\{#MyAppExeName}"" ""%1"""; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}\Capabilities\FileAssociations"; \
    ValueType: string; \
    ValueName: ".ts"; \
    ValueData: "{#MyAppName}.ts"; \
    Flags: uninsdeletevalue

; ============================================================
; M4V
; ============================================================

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\.m4v\OpenWithProgids"; \
    ValueType: string; \
    ValueName: "{#MyAppName}.m4v"; \
    ValueData: ""; \
    Flags: uninsdeletevalue

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.m4v"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{#MyAppName} m4v"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.m4v\DefaultIcon"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{app}\{#MyAppExeName},0"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.m4v\shell\open\command"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: """{app}\{#MyAppExeName}"" ""%1"""; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}\Capabilities\FileAssociations"; \
    ValueType: string; \
    ValueName: ".m4v"; \
    ValueData: "{#MyAppName}.m4v"; \
    Flags: uninsdeletevalue

; ============================================================
; MPG
; ============================================================

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\.mpg\OpenWithProgids"; \
    ValueType: string; \
    ValueName: "{#MyAppName}.mpg"; \
    ValueData: ""; \
    Flags: uninsdeletevalue

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.mpg"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{#MyAppName} mpg"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.mpg\DefaultIcon"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{app}\{#MyAppExeName},0"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.mpg\shell\open\command"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: """{app}\{#MyAppExeName}"" ""%1"""; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}\Capabilities\FileAssociations"; \
    ValueType: string; \
    ValueName: ".mpg"; \
    ValueData: "{#MyAppName}.mpg"; \
    Flags: uninsdeletevalue

; ============================================================
; MPEG
; ============================================================

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\.mpeg\OpenWithProgids"; \
    ValueType: string; \
    ValueName: "{#MyAppName}.mpeg"; \
    ValueData: ""; \
    Flags: uninsdeletevalue

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.mpeg"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{#MyAppName} mpeg"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.mpeg\DefaultIcon"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{app}\{#MyAppExeName},0"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.mpeg\shell\open\command"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: """{app}\{#MyAppExeName}"" ""%1"""; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}\Capabilities\FileAssociations"; \
    ValueType: string; \
    ValueName: ".mpeg"; \
    ValueData: "{#MyAppName}.mpeg"; \
    Flags: uninsdeletevalue

; ============================================================
; 3GP
; ============================================================

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\.3gp\OpenWithProgids"; \
    ValueType: string; \
    ValueName: "{#MyAppName}.3gp"; \
    ValueData: ""; \
    Flags: uninsdeletevalue

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.3gp"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{#MyAppName} 3gp"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.3gp\DefaultIcon"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{app}\{#MyAppExeName},0"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.3gp\shell\open\command"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: """{app}\{#MyAppExeName}"" ""%1"""; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}\Capabilities\FileAssociations"; \
    ValueType: string; \
    ValueName: ".3gp"; \
    ValueData: "{#MyAppName}.3gp"; \
    Flags: uninsdeletevalue

; ============================================================
; MP3
; ============================================================

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\.mp3\OpenWithProgids"; \
    ValueType: string; \
    ValueName: "{#MyAppName}.mp3"; \
    ValueData: ""; \
    Flags: uninsdeletevalue

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.mp3"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{#MyAppName} mp3"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.mp3\DefaultIcon"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{app}\{#MyAppExeName},0"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.mp3\shell\open\command"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: """{app}\{#MyAppExeName}"" ""%1"""; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}\Capabilities\FileAssociations"; \
    ValueType: string; \
    ValueName: ".mp3"; \
    ValueData: "{#MyAppName}.mp3"; \
    Flags: uninsdeletevalue

; ============================================================
; FLAC
; ============================================================

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\.flac\OpenWithProgids"; \
    ValueType: string; \
    ValueName: "{#MyAppName}.flac"; \
    ValueData: ""; \
    Flags: uninsdeletevalue

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.flac"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{#MyAppName} flac"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.flac\DefaultIcon"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{app}\{#MyAppExeName},0"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.flac\shell\open\command"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: """{app}\{#MyAppExeName}"" ""%1"""; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}\Capabilities\FileAssociations"; \
    ValueType: string; \
    ValueName: ".flac"; \
    ValueData: "{#MyAppName}.flac"; \
    Flags: uninsdeletevalue

; ============================================================
; WAV
; ============================================================

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\.wav\OpenWithProgids"; \
    ValueType: string; \
    ValueName: "{#MyAppName}.wav"; \
    ValueData: ""; \
    Flags: uninsdeletevalue

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.wav"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{#MyAppName} wav"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.wav\DefaultIcon"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{app}\{#MyAppExeName},0"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.wav\shell\open\command"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: """{app}\{#MyAppExeName}"" ""%1"""; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}\Capabilities\FileAssociations"; \
    ValueType: string; \
    ValueName: ".wav"; \
    ValueData: "{#MyAppName}.wav"; \
    Flags: uninsdeletevalue

; ============================================================
; OGG
; ============================================================

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\.ogg\OpenWithProgids"; \
    ValueType: string; \
    ValueName: "{#MyAppName}.ogg"; \
    ValueData: ""; \
    Flags: uninsdeletevalue

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.ogg"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{#MyAppName} ogg"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.ogg\DefaultIcon"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{app}\{#MyAppExeName},0"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.ogg\shell\open\command"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: """{app}\{#MyAppExeName}"" ""%1"""; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}\Capabilities\FileAssociations"; \
    ValueType: string; \
    ValueName: ".ogg"; \
    ValueData: "{#MyAppName}.ogg"; \
    Flags: uninsdeletevalue

; ============================================================
; OGA
; ============================================================

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\.oga\OpenWithProgids"; \
    ValueType: string; \
    ValueName: "{#MyAppName}.oga"; \
    ValueData: ""; \
    Flags: uninsdeletevalue

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.oga"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{#MyAppName} oga"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.oga\DefaultIcon"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{app}\{#MyAppExeName},0"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.oga\shell\open\command"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: """{app}\{#MyAppExeName}"" ""%1"""; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}\Capabilities\FileAssociations"; \
    ValueType: string; \
    ValueName: ".oga"; \
    ValueData: "{#MyAppName}.oga"; \
    Flags: uninsdeletevalue

; ============================================================
; AAC
; ============================================================

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\.aac\OpenWithProgids"; \
    ValueType: string; \
    ValueName: "{#MyAppName}.aac"; \
    ValueData: ""; \
    Flags: uninsdeletevalue

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.aac"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{#MyAppName} aac"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.aac\DefaultIcon"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{app}\{#MyAppExeName},0"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.aac\shell\open\command"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: """{app}\{#MyAppExeName}"" ""%1"""; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}\Capabilities\FileAssociations"; \
    ValueType: string; \
    ValueName: ".aac"; \
    ValueData: "{#MyAppName}.aac"; \
    Flags: uninsdeletevalue

; ============================================================
; M4A
; ============================================================

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\.m4a\OpenWithProgids"; \
    ValueType: string; \
    ValueName: "{#MyAppName}.m4a"; \
    ValueData: ""; \
    Flags: uninsdeletevalue

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.m4a"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{#MyAppName} m4a"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.m4a\DefaultIcon"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{app}\{#MyAppExeName},0"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.m4a\shell\open\command"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: """{app}\{#MyAppExeName}"" ""%1"""; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}\Capabilities\FileAssociations"; \
    ValueType: string; \
    ValueName: ".m4a"; \
    ValueData: "{#MyAppName}.m4a"; \
    Flags: uninsdeletevalue

; ============================================================
; WMA
; ============================================================

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\.wma\OpenWithProgids"; \
    ValueType: string; \
    ValueName: "{#MyAppName}.wma"; \
    ValueData: ""; \
    Flags: uninsdeletevalue

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.wma"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{#MyAppName} wma"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.wma\DefaultIcon"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{app}\{#MyAppExeName},0"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.wma\shell\open\command"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: """{app}\{#MyAppExeName}"" ""%1"""; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}\Capabilities\FileAssociations"; \
    ValueType: string; \
    ValueName: ".wma"; \
    ValueData: "{#MyAppName}.wma"; \
    Flags: uninsdeletevalue

; ============================================================
; OPUS
; ============================================================

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\.opus\OpenWithProgids"; \
    ValueType: string; \
    ValueName: "{#MyAppName}.opus"; \
    ValueData: ""; \
    Flags: uninsdeletevalue

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.opus"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{#MyAppName} opus"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.opus\DefaultIcon"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{app}\{#MyAppExeName},0"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.opus\shell\open\command"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: """{app}\{#MyAppExeName}"" ""%1"""; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}\Capabilities\FileAssociations"; \
    ValueType: string; \
    ValueName: ".opus"; \
    ValueData: "{#MyAppName}.opus"; \
    Flags: uninsdeletevalue

; ============================================================
; MKA
; ============================================================

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\.mka\OpenWithProgids"; \
    ValueType: string; \
    ValueName: "{#MyAppName}.mka"; \
    ValueData: ""; \
    Flags: uninsdeletevalue

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.mka"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{#MyAppName} mka"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.mka\DefaultIcon"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: "{app}\{#MyAppExeName},0"; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\Classes\{#MyAppName}.mka\shell\open\command"; \
    ValueType: string; \
    ValueName: ""; \
    ValueData: """{app}\{#MyAppExeName}"" ""%1"""; \
    Flags: uninsdeletekey

Root: HKLM; \
    Subkey: "SOFTWARE\{#MyAppPublisher}\{#MyAppName}\Capabilities\FileAssociations"; \
    ValueType: string; \
    ValueName: ".mka"; \
    ValueData: "{#MyAppName}.mka"; \
    Flags: uninsdeletevalue