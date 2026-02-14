# Docker Backup Tool — Pro Edition (PySide6)

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
docker-backup-pyside6/
├── main.py
├── volume_model.py
├── backup_worker.py
├── utils.py
├── config/
│ └── settings.json
└── requirements.txt

---

## 🛠 Requirements

- Python 3.9+
- WSL installed
- `docker-desktop` WSL distro
- rsync installed inside WSL

Install rsync if needed:

```bash
wsl -d docker-desktop -u root apk update
wsl -d docker-desktop -u root apk add rsync
```

Install Python dependencies:
```bash
pip install -r requirements.txt
```
▶️ Running the App
```bash
python main.py
```
🧠 How It Works

utils.list_volumes() runs find inside WSL

VolumeTreeModel builds a Qt model

User selects leaf nodes

BackupWorker runs rsync in a QThread

UI remains responsive

⚠️ Important Notes

Mirror mode (--delete) removes files in the destination that no longer exist in the source.

Always maintain:
Historical snapshots
Or separate backup archives

Recommended backup strategy:
```bash
C:\backups\
├── 2026-02-14\
├── 2026-02-15\
└── daily-volumes-backup\
```
🧪 Troubleshooting
Issue	            Fix
rsync not found	    Install rsync in WSL
Permission denied	Run WSL commands with -u root
No volumes shown	Ensure docker-desktop WSL distro exists
Destination errors	Use folder picker

📦 Packaging (Optional)

You can generate a Windows executable:
```bash
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```

🔮 Upcoming Features — Ultra Edition
The next evolution of this tool will include:

🔄 Real-Time Rsync Output Streaming
Display live rsync progress instead of waiting for completion.

📊 File-Level Progress Tracking
Show:
    Number of files processed
    Transfer speed
    Estimated time remaining

🌙 Dark Theme Support
Professional modern UI with theme switching.

🔍 Volume Search & Filtering
Search and filter large volume trees instantly.

💾 Auto-Save Settings

Remember:
    Last destination
    Mirror mode state
    Window size and layout

📅 Scheduled Backups
Integrated scheduler for automated daily/weekly backups.

📦 Snapshot Automation
One-click snapshot creation using:
```bash
cp -al
```
🧠 Smart Deduplication Logic
Avoid redundant rsync calls when parent and child are both selected.

📁 Backup Profiles
Create named backup presets.

🖥 Windows Installer
Proper .exe installer with icon and metadata.

👨‍💻 Credits
Developed by ChatGPT (2026).
Idea and Guidance by drem666.

🛡 Disclaimer
Test backups before relying on them in production environments.

Built with 🧠 + 🐳 + ⚡
---

You turned:
Flask + React extension  
→  
Professional native desktop application.
That’s a serious upgrade.
When you return, we’ll build Ultra Edition. 😎🚀