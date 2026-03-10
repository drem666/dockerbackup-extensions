# Docker Backup Extension
Version 1.0

## 📌 Overview
This extension provides a simple interface to back up Docker volumes to a local directory. It uses rsync for efficient incremental/daily syncs and supports both Windows and Linux file paths.

## 🎯 Key Features
• Volume Browsing: View Docker volumes and their contents in a tree structure
• Incremental Backups: Only syncs changed files (-a flag)
• Mirror Mode: Optional deletion of obsolete files in destination (--delete flag)
• Cross-Platform: Works with Windows paths (e.g., C:\Backups) and Linux/WSL paths
• Simple UI: React-based interface for folder selection

## ⚠️ Important Note
The --delete flag permanently removes files from the backup destination if they no longer exist in the source.
Always keep a separate backup of previous versions in case you need to restore deleted files.

## 🛠️ Setup
1. Install Dependencies:
bash
# Backend (Python)
pip install -r backend/requirements.txt
# Frontend (Node.js)
cd frontend
npm install

2. Install rsync in WSL:
bash
wsl -d docker-desktop -u root apk update
wsl -d docker-desktop -u root apk add rsync

3. Start Services:
bash
# Backend (Flask API)
python backend/app.py
# Frontend (React UI)
cd frontend
npm start

🖥️ Usage
1. Access UI: Open http://localhost:3000
2. Select Paths:
◇ Browse Docker volumes
◇ Check folders/files to back up
3. Set Destination:
◇ Windows Path: C:\backups\daily-volumes-backup
◇ Linux/WSL Path: /mnt/host/c/backups/daily-volumes-backup
4. Run Backup: Click "Run Backup"

💾 Backup Strategy Recommendation
To retain historical versions:
📂 C:\backups\
├── 📁 2025-02-20\  # Daily snapshot
├── 📁 2025-02-21\
└── 📁 daily-volumes-backup\       # Active mirror (synced by this tool)
Implementation:
bash
# Manual example (run daily)
cp -al daily-volumes-backup 2025-02-21  # Create hardlink-based snapshot

🔄 CLI Usage (Advanced)
bash
# Manual backup via curl
curl -X POST http://localhost:5000/api/backup \
  -H "Content-Type: application/json" \
  -d '{
    "paths": ["/volume1", "/volume2/data"],
    "destination": "/mnt/host/c/backups/daily-volumes-backup"
  }'

💾 Manually Using Windows System Applications
Poweriso (iso/daa) archives, 7zip (7z/zip) archives
📂 C:\backups\
├── 2025.02.20-daily-volumes-backup.7z  # Daily snapshot
├── 2025.02.21-daily-volumes-backup.daa
└── 📁 daily-volumes-backup/       # Active mirror (synced by this tool)

❗ Troubleshooting

| Issue | Solution |
| rsync: not found | Reinstall rsync in WSL |
| Path errors | Use absolute paths starting with / |
| Permission denied | Run WSL commands with -u root |

# LICENSE
MIT

Developed with 🧠 by DeepSeek & ChatGPT (2025)
Always test backups before relying on them!
