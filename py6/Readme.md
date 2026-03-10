# Docker Backup Tool (PySide6)

A professional desktop application for backing up Docker volumes using **rsync** via WSL.

Built with **PySide6 (Qt for Python)** — no browser, no Flask, no npm.  
Fast. Native. Clean.

---

## 🚀 Overview

Docker Backup Tool allows you to:

- Browse Docker volumes in a tree view
- Select files and folders with tri-state checkbox logic
- Backup using rsync (incremental + mirror support)
- Choose backup destination via folder picker
- Run backups in background threads
- View logs in real time
- Keep the UI responsive during operations

This tool replaces the earlier Flask + React extension with a fully native desktop UI.

---

## ✨ Features

### 📂 Volume Explorer
- Displays Docker volumes using a `QTreeView`
- Tri-state checkbox logic (Checked / Partial / Unchecked)
- Automatic parent-child propagation
- Expand / collapse support

### 💾 Backup Engine
- Uses `rsync -a --delete --relative`
- Runs via WSL (`docker-desktop` distro)
- Ensures destination path exists
- Windows path → Docker path auto-conversion
- Leaf-node selection logic (avoids duplicate syncs)

### 🖥 Professional UI
- Toolbar (Refresh / Run Backup)
- Mirror mode toggle
- Split view (Tree + Log Panel)
- Real-time logging panel
- Progress indicator
- Status bar notifications
- UI disabled during backup

---

## 📁 Project Structure
```
docker-backup-pyside6/
├── main.py
├── volume_model.py
├── backup_worker.py
├── utils.py
├── settings_dialog.py
├── config/
│   ├── settings.json
│   └── themes.qss
└── requirements.txt
```

---

## 🛠 Requirements

- Python 3.9+
- Windows 11 (or Windows 10 with WSL2)
- WSL installed
- `docker-desktop` WSL distro
- **rsync installed inside WSL** ⚠️
- ⚠️MOST IMPORTANT: Docker-desktop must be running.  

---

## 📦 Installation

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Install rsync in WSL (CRITICAL!)

**This is required or you'll get "rsync: not found" errors!**

```bash
wsl -d docker-desktop sh -c "apk add rsync"
```

> **Why?** Docker Desktop's WSL distro uses Alpine Linux, which doesn't include rsync by default.

#### Alternative: Install rsync with root privileges

If the above fails, try:

```bash
wsl -d docker-desktop -u root sh -c "apk update && apk add rsync"
```

#### Verify rsync installation

```bash
wsl -d docker-desktop sh -c "which rsync"
```

Expected output: `/usr/bin/rsync`

---

### Step 3: START Docker-Desktop (CRITICAL!)
```bash
# ⚠️MOST IMPORTANT (Otherwise GUI wont run)
# The volume_models.py depends on docker running and the mounted vhdx to list volumes.
# If not found, you will get an error:
  File "C:\dockers\docker-backup-extension\py6\main.py", line 140, in _create_ui
    self.model = VolumeTreeModel()
  File "C:\dockers\docker-backup-extension\py6\volume_model.py", line 28, in __init__
    self._build_model()
  File "C:\dockers\docker-backup-extension\py6\volume_model.py", line 31, in _build_model
    volumes = list_volumes()
subprocess.CalledProcessError: Command '['wsl', '-d', 'docker-desktop', 'sh', '-c', "cd '/tmp/docker-desktop-root/mnt/docker-desktop-disk/' && find . \\( -type d -o -type f \\)"]' returned non-zero exit status 2.
```

## ▶️ Running the App

```bash
python main.py
```

---

## 🧠 How It Works

1. `utils.list_volumes()` runs `find` inside WSL
2. `VolumeTreeModel` builds a Qt model with tri-state checkboxes
3. User selects volumes/files/folders
4. `BackupWorker` runs rsync in a QThread
5. UI remains responsive during backup

---

## ⚙️ Configuration

Edit `config/settings.json`:

```json
{
  "docker_disk_base": "/tmp/docker-desktop-root/mnt/docker-desktop-disk/data/docker",
  "docker_host_mount_prefix": "/tmp/docker-desktop-root/run/desktop/mnt/host/",
  "wsl_distro": "docker-desktop",
  "rsync_flags": ["-a", "--delete", "--relative"]
}
```

### Settings Explained

- **docker_disk_base**: Where Docker stores volumes in WSL
- **docker_host_mount_prefix**: WSL path prefix for Windows drives
- **wsl_distro**: WSL distribution name (default: `docker-desktop`)
- **rsync_flags**: rsync command options
  - `-a`: Archive mode (preserves permissions, timestamps, etc.)
  - `--delete`: Mirror mode (removes files not in source)
  - `--relative`: Preserves directory structure

---

## ⚠️ Important Notes

### Mirror Mode (`--delete`)

**Warning:** Mirror mode removes files in the destination that no longer exist in the source.

Always maintain:
- Historical snapshots, OR
- Separate backup archives

### Recommended Backup Strategy

```
C:\backups\
├── 2026-02-14\           ← Daily snapshots
├── 2026-02-15\
└── daily-volumes-backup\  ← Current mirror
```

---

## 🧪 Troubleshooting

| Issue | Fix |
|-------|-----|
| **rsync: not found** | Run `wsl -d docker-desktop sh -c "apk add rsync"` |
| **Command returned exit status 127** | rsync not installed (see above) |
| **No volumes selected** | Check volumes in the tree before clicking Run Backup |
| **Permission denied** | Run WSL commands with `-u root` flag |
| **No volumes shown** | Ensure `docker-desktop` WSL distro exists and is running |
| **Destination errors** | Use the folder picker to select a valid Windows path |
| **Path conversion issues** | Check `docker_host_mount_prefix` in settings.json |

### Common Error Messages

**Error: `/bin/sh: rsync: not found`**
```bash
# Solution:
wsl -d docker-desktop sh -c "apk add rsync"
```

**Error: `Command '['wsl', '-d', 'docker-desktop', 'rsync', ...]' returned non-zero exit status 127`**
```bash
# Exit status 127 = command not found
# Solution: Install rsync (see above)
```

---

## 🎨 Theme Support

The app includes theme switching! Themes are defined in `config/themes.qss`:

```css
/*Theme: Dark*/
QMainWindow {
    background-color: #2b2b2b;
    color: #ffffff;
}
/*ThemeEnd*/

/*Theme: Light*/
QMainWindow {
    background-color: #ffffff;
    color: #000000;
}
/*ThemeEnd*/
```

Switch themes from the toolbar dropdown.

---

## 📦 Packaging (Optional)

You can generate a Windows executable:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```

---

## 🔮 Upcoming Features — Ultra Edition

The next evolution of this tool will include:

### 🔄 Real-Time Rsync Output Streaming
Display live rsync progress instead of waiting for completion.

### 📊 File-Level Progress Tracking
Show:
- Number of files processed
- Transfer speed
- Estimated time remaining

### 🌙 Enhanced Dark Theme
Professional modern UI with improved theme switching.

### 🔍 Volume Search & Filtering
Search and filter large volume trees instantly.

### 💾 Enhanced Auto-Save Settings

Remember:
- Last destination
- Mirror mode state
- Window size and layout
- Last selected volumes

### 📅 Scheduled Backups
Integrated scheduler for automated daily/weekly backups.

### 📦 Snapshot Automation
One-click snapshot creation using:
```bash
cp -al  # Hard-link snapshots for space efficiency
```

### 🧠 Smart Deduplication Logic
Avoid redundant rsync calls when parent and child are both selected.

### 📋 Backup Profiles
Create named backup presets for different scenarios.

### 🖥 Windows Installer
Proper .exe installer with icon and metadata.

### 🔐 Encryption Support
Optional backup encryption for sensitive data.

---

## 💻 Development Notes

### Bug Fixes Implemented

**v1.1 - Fixed "No volumes selected" error**
- Issue: Checkbox states stored as integers but compared as enums
- Solution: Consistent `Qt.CheckState` enum usage throughout
- Files modified: `volume_model.py`

**v1.0 - Initial Release**
- Ported from Flask + React to native PySide6
- Implemented tri-state checkbox logic
- Added background worker threads

---

## 💨 Credits

**Developed by:** ChatGPT/DeepSeek/Claude Sonnet 4.5, 2026  
**Idea and Guidance:** drem666  
**Debugging Partner:** Also drem666 (excellent troubleshooting skills! 👏)

---

## 🛡 Disclaimer

**Always test backups before relying on them in production environments.**

Verify that:
- Rsync is installed correctly
- Backup destinations are accessible
- Mirror mode behavior is understood
- File permissions are preserved

---

Built with 🧠 + 🐳 + ⚡

---

## 🎯 Quick Start Checklist

- [ ] Install Python 3.9+
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] **Install rsync in WSL: `wsl -d docker-desktop sh -c "apk add rsync"`**
- [ ] Verify Docker Desktop is running
- [ ] Run the app: `python main.py`
- [ ] Select volumes to backup
- [ ] Choose destination folder
- [ ] Click "Run Backup"
- [ ] Monitor progress in log panel

---
# LICENSE
MIT
