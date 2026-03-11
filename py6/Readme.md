# Docker Backup Tool (PySide6)

A professional desktop application for backing up and restoring Docker volumes with advanced features like compressed archives, backup history, and restore functionality. Built with PySide6 (Qt for Python) – fast, native, and clean.

## 🚀 Overview

  Docker Backup Tool allows you to:

  Browse Docker volumes in a tree view with tri‑state checkbox logic

  Select files and folders for backup

  Two backup modes:

    Copy (rsync) – incremental, mirror‑style sync (preserves file structure)

    Archive (tar.gz) – create timestamped compressed archives

  Choose backup destination via folder picker

  Run backups in background threads (UI stays responsive)

  View real‑time logs

  Track backup history – all archives are recorded in a JSON manifest

  Restore from any previously created archive (full or partial)

  Switch between light and dark themes (easily extendable)

## ScreenShots

## ✨ Features

### 📂 Volume Explorer

  Displays Docker volumes using a QTreeView

  Tri‑state checkbox logic (Checked / Partial / Unchecked)

  Automatic parent–child propagation

  Expand / collapse support

  Checkbox states persist during volume refreshes

### 💾 Backup Engine

Mode 1: rsync copy – uses rsync -a --delete --relative for fast, incremental backups

Mode 2: Archive – creates .tar.gz files with timestamps (e.g., backup_20260312_143022.tar.gz)

  Runs via WSL (docker-desktop distro)

  Automatically ensures destination paths exist

  Windows path ↔ Docker path conversion

  Leaf‑node selection logic avoids duplicate syncs

### 📜 Backup History & Restore
  Every archive backup is recorded in a backup_manifest.json file inside the destination folder

  Backup History dialog lists all archives with timestamps and item counts

  Restore an entire backup or choose specific items (planned)

  Restore worker runs in background, with progress indication

### 🖥 Professional UI

  Toolbar with:

    Refresh Volumes

    Run Backup (with mode selector)

    Mirror Mode toggle (for rsync)

  Settings

  Theme switcher

  Backup History button

  Split view: volume tree + real‑time log panel

  Progress bar and status notifications

  UI disabled during operations to prevent interference

  Fully styleable with QSS – light and dark themes included

## 📁 Project Structure

```ini
docker-backup-pyside6/
├── main.py                 # Main application window & UI logic
├── volume_model.py         # Tree model with tri‑state checkboxes
├── backup_worker.py        # Rsync backup worker (copy mode)
├── archive_worker.py       # Archive creation worker
├── restore_worker.py       # Restore from archive worker
├── backup_history.py       # Manifest management
├── utils.py                # Helper functions (path conversion, rsync calls)
├── settings_dialog.py      # Settings dialog
├── config/
│   ├── settings.json       # WSL paths, rsync flags, etc.
│   └── themes.qss          # Light and dark themes
├── requirements.txt        # Python dependencies
└── start.bat               # Quick launch script (optional)
```

## 🛠 Requirements

  Python 3.9+

  Windows 11 (or Windows 10 with WSL2)

  WSL installed with docker-desktop distro

  Docker Desktop running (the app accesses volumes via WSL)

  rsync installed inside the docker-desktop WSL distro (see installation)

## 📦 Installation

### Step 1: Clone the repository

```bash
git clone https://github.com/drem666/dockerbackup-extensions.git
cd dockerbackup-extensions/py6
```

### Step 2: Install Python dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Install rsync in the docker-desktop WSL distro

This is critical – without rsync the copy mode will fail.

Open PowerShell as Administrator and run:
```powershell
wsl -d docker-desktop -u root sh -c "apk update && apk add rsync"
```

Verify installation:
```powershell
wsl -d docker-desktop sh -c "which rsync"
# Expected output: /usr/bin/rsync
```

### Step 4: Start Docker Desktop

Make sure Docker Desktop is running before launching the app.

## ⚙️ Configuration

Edit config/settings.json to match your environment:

```json
{
  "docker_disk_base": "/tmp/docker-desktop-root/mnt/docker-desktop-disk/data/docker",
  "docker_host_mount_prefix": "/tmp/docker-desktop-root/run/desktop/mnt/host/",
  "wsl_distro": "docker-desktop",
  "rsync_flags": ["-a", "--delete", "--relative"]
}
```
### Settings Explained

```bash
docker_disk_base # Where Docker stores volumes inside the WSL distro (usually /var/lib/docker/volumes but may differ in Docker Desktop)

docker_host_mount_prefix # Prefix used to access Windows drives from inside the docker-desktop WSL distro (e.g., /mnt/host/c/)

wsl_distro # Name of the WSL distribution that runs Docker (normally docker-desktop)

rsync_flags # Default flags for rsync copy mode

  -a # archive mode (preserves permissions, timestamps)

  --delete # mirror mode (removes files in destination that no longer exist in source)

  --relative # preserve directory structure
```

### ▶️ Running the App

```bash
python main.py
```

Or double‑click start.bat in the folder. It is folder path agnostic.

## 🧠 How It Works

  1. Volume listing – utils.list_volumes() runs find inside the docker-desktop WSL distro to get a tree of all files/folders under docker_disk_base.

  2. Model – VolumeTreeModel builds a Qt tree model with tri‑state checkboxes.

  3. User selects items to back up.

      Backup – Depending on the chosen mode:

  4. Copy mode: BackupWorker runs rsync via WSL.

  5. Archive mode: ArchiveWorker runs tar -czf inside WSL to create a timestamped archive in the destination folder.

  6. History – After a successful archive backup, an entry is added to backup_manifest.json in the destination folder.

  7. Restore – From the Backup History dialog, select an archive and click Restore. RestoreWorker runs tar -xzf to extract files back into the original volume locations.

## 🖥 Usage Guide

  1. Selecting Volumes

    Expand the tree and check items. Parent–child relationships are automatically managed (checking a parent checks all children; unchecking a parent unchecks all children; partial states appear when some but not all children are checked).

  2. Backup Destination

    Click Browse to choose a Windows folder. The path is automatically converted to the equivalent WSL path (e.g., C:\Backups → /mnt/host/c/Backups).

  3. Backup Mode

    Use the Mode dropdown on the toolbar:

      Copy (rsync) – ideal for frequent, incremental backups to a folder. Mirror mode (--delete) can be toggled.

      Archive (tar.gz) – creates a compressed, timestamped archive. Good for snapshots.

  4. Running a Backup

    Click Run Backup. The UI will be disabled, and progress is shown in the status bar. Logs appear in the right panel.

  5. Backup History

    Click Backup History to open a dialog listing all previous archives stored in the current destination folder.
    Select an entry and click Restore Selected. You’ll be asked whether to restore all contents or choose specific items (partial restore coming soon).

  6. Theme Switching

    Use the Theme dropdown to switch between light and dark modes. Add your own themes by editing config/themes.qss.

## Settings

  The Settings dialog allows you to:

  Set a default backup destination and lock it

  Auto‑detect or manually adjust the WSL paths used by the app

  View current rsync flags

## ⚠️ Important Notes

- Mirror Mode (--delete)

Warning: When enabled, files in the destination that no longer exist in the source will be deleted. Always maintain separate historical snapshots if you need to keep older versions.

- Archive Backups

  Archives are stored as .tar.gz files in your chosen destination folder.

  The manifest (backup_manifest.json) records each archive along with the list of backed‑up paths and a timestamp.

- Restore Safety

  Restoring overwrites existing files in the volumes. Consider stopping containers that use those volumes before restoring to avoid corruption (especially databases).

## 🧪 Troubleshooting

|Issue	|Solution|
|-------|--------|
|rsync: not found	|Run the rsync installation command (see Installation)|
|Command returned exit status 127	|rsync missing or incorrect WSL distro name|
|No volumes shown	|Ensure Docker Desktop is running and the docker-desktop WSL distro exists (wsl -l -v)|
|Path conversion errors	|Check docker_host_mount_prefix in settings.json. The default should work for most Windows 11 installations.|
|Permission denied	|Some operations may require running WSL commands as root. The app does not auto‑elevate; you may need to manually adjust permissions inside WSL.|
|Checkboxes not updating visually	|Try switching themes or restarting the app. This is a known Qt quirk – a force‑repaint is triggered on theme change.|
|Backup history empty	|Ensure the destination folder is the same one where archives were saved. The manifest is stored in that folder.|

## Common Error Messages

  1. rsync: not found

  ```powershell
  wsl -d docker-desktop -u root sh -c "apk add rsync"
  ```
  2. tar: unrecognized option: czf (unlikely, but if using BusyBox tar)

  ```powershell
  wsl -d docker-desktop -u root sh -c "apk add tar"
```
## 🎨 Theme Support

The app includes two built‑in themes: Light and Dark. Themes are defined in config/themes.qss using a simple block format:

```css
/*Theme: Light*/
QMainWindow {
    background-color: #f0f0f0;
    color: #000000;
}
/* ... more styling ... */
/*ThemeEnd*/
/*Theme: Dark*/
QMainWindow {
    background-color: #2b2b2b;
    color: #ffffff;
}
/* ... more styling ... */
/*ThemeEnd*/
```
You can easily add new themes by copying the block and changing the name and colors.

## 🔮 Future Enhancements

  Partial restore – select specific files/folders from an archive

  Scheduled backups – integrate with Windows Task Scheduler or a built‑in timer

  Encryption – optional archive encryption

  Snapshot automation – hard‑link based snapshots for space‑efficient versioning

  Search/filter in volume tree

  Windows installer – one‑click .exe setup

💻 Development & Credits

  Developed by: drem666, with assistance from AI language models (DeepSeek, ChatGPT, Claude)

  Original idea & guidance: drem666

  Debugging & testing: drem666 (excellent troubleshooting skills! 👏)

  The app builds upon earlier prototypes (Flask+React version) and incorporates community solutions for VHDX compaction and rsync‑based backups.

## 🛡 License

MIT License – feel free to use, modify, and distribute. See the LICENSE file for details.


## Built with 🧠 + 🐳 + ⚡

## ✅ Quick Start Checklist

  Install Python 3.9+

  Install dependencies: pip install -r requirements.txt

  Install rsync in WSL: wsl -d docker-desktop -u root sh -c "apk add rsync"

  Start Docker Desktop

  Run the app: python main.py

  Browse volumes, select items

  Choose destination folder

  Select backup mode (Copy or Archive)

  Click Run Backup

  Monitor progress in log panel

  Explore Backup History to restore previous archives

  If you encounter any issues or have feature requests, please open an issue on GitHub.
---
