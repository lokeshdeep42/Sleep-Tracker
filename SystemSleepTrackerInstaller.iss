[Setup]
AppName=System Sleep Tracker
AppVersion=1.0
DefaultDirName={pf}\System Sleep Tracker
DefaultGroupName=System Sleep Tracker
UninstallDisplayIcon={app}\System Sleep Tracker.exe
OutputBaseFilename=SystemSleepTrackerInstaller
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\System Sleep Tracker.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "config\db_config.json"; DestDir: "{app}\config"; Flags: ignoreversion

[Icons]
Name: "{group}\System Sleep Tracker"; Filename: "{app}\System Sleep Tracker.exe"; WorkingDir: "{app}"
