# settings_dialog.py
import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QCheckBox, QFileDialog,
                               QDialogButtonBox, QFormLayout)
from PySide6.QtCore import QSettings
-from utils import convert_windows_path_to_docker
+from utils import convert_windows_path_to_docker
+import json

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
-        self.resize(500, 200)
+        self.resize(600, 400)

        self.settings = QSettings("Drem666", "DockerBackupTool")

        # Load current settings
        self.default_win_path = self.settings.value("default_win_path", "")
        self.use_default = self.settings.value("use_default", "false") == "true"
+        
+        # Load JSON settings
+        self.json_settings = self._load_json_settings()

        # Create widgets
        self.win_path_edit = QLineEdit(self.default_win_path)
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_folder)

        self.docker_path_label = QLabel()
        self.update_docker_path(self.default_win_path)

        self.lock_checkbox = QCheckBox("Use this as default destination (lock)")
        self.lock_checkbox.setChecked(self.use_default)
+        
+        # Create JSON settings widgets
+        self.docker_disk_base_edit = QLineEdit(self.json_settings.get("docker_disk_base", ""))
+        self.docker_disk_base_detect_btn = QPushButton("AutoDetect")
+        self.docker_disk_base_detect_btn.clicked.connect(self.auto_detect_docker_disk_base)
+        
+        self.docker_host_mount_prefix_edit = QLineEdit(self.json_settings.get("docker_host_mount_prefix", ""))
+        self.docker_host_mount_prefix_detect_btn = QPushButton("AutoDetect")
+        self.docker_host_mount_prefix_detect_btn.clicked.connect(self.auto_detect_docker_host_mount_prefix)
+        
+        self.wsl_distro_edit = QLineEdit(self.json_settings.get("wsl_distro", ""))
+        self.wsl_distro_detect_btn = QPushButton("AutoDetect")
+        self.wsl_distro_detect_btn.clicked.connect(self.auto_detect_wsl_distro)
+        
+        self.rsync_flags_edit = QLineEdit(", ".join(self.json_settings.get("rsync_flags", [])))
+        self.rsync_flags_edit.setReadOnly(True)
+        self.rsync_flags_edit.setStyleSheet("background-color: #f0f0f0;")

        # Connect signals
        self.win_path_edit.textChanged.connect(self.on_win_path_changed)

        # Layout
+        main_layout = QVBoxLayout()
+        
+        # JSON settings section
+        json_group_layout = QFormLayout()
+        json_group_layout.addRow("docker_disk_base:", self._create_json_row(self.docker_disk_base_edit, self.docker_disk_base_detect_btn))
+        json_group_layout.addRow("docker_host_mount_prefix:", self._create_json_row(self.docker_host_mount_prefix_edit, self.docker_host_mount_prefix_detect_btn))
+        json_group_layout.addRow("wsl_distro:", self._create_json_row(self.wsl_distro_edit, self.wsl_distro_detect_btn))
+        json_group_layout.addRow("rsync_flags:", self.rsync_flags_edit)
+        
+        main_layout.addWidget(QLabel("<b>Settings.json Configuration</b>"))
+        main_layout.addLayout(json_group_layout)
+        main_layout.addSpacing(20)
+        
+        # Windows path section (existing functionality)
+        main_layout.addWidget(QLabel("<b>Backup Destination Settings</b>"))
         form_layout = QFormLayout()
         form_layout.addRow("Windows path:", self.win_path_edit)
         form_layout.addRow("", self.browse_btn)
         form_layout.addRow("Docker path:", self.docker_path_label)
         form_layout.addRow("", self.lock_checkbox)
+        main_layout.addLayout(form_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

-        main_layout = QVBoxLayout()
-        main_layout.addLayout(form_layout)
         main_layout.addWidget(button_box)
         self.setLayout(main_layout)
+    
+    def _create_json_row(self, edit_widget, button_widget):
+        """Helper to create a row with edit field and button"""
+        row_layout = QHBoxLayout()
+        row_layout.addWidget(edit_widget)
+        row_layout.addWidget(button_widget)
+        widget = QWidget()
+        widget.setLayout(row_layout)
+        return widget

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Default Backup Folder")
        if folder:
            self.win_path_edit.setText(folder)

    def on_win_path_changed(self, text):
        self.update_docker_path(text)

    def update_docker_path(self, win_path):
        docker_path = convert_windows_path_to_docker(win_path)
        self.docker_path_label.setText(docker_path if docker_path else "(invalid path)")
+    
+    def _load_json_settings(self):
+        """Load settings from JSON file"""
+        config_path = os.path.join(os.path.dirname(__file__), "config", "settings.json")
+        try:
+            with open(config_path, 'r') as f:
+                return json.load(f)
+        except Exception as e:
+            print(f"Error loading settings.json: {e}")
+            return {}
+    
+    def _save_json_settings(self):
+        """Save settings to JSON file"""
+        config_path = os.path.join(os.path.dirname(__file__), "config", "settings.json")
+        try:
+            # Create directory if it doesn't exist
+            os.makedirs(os.path.dirname(config_path), exist_ok=True)
+            
+            updated_settings = {
+                "docker_disk_base": self.docker_disk_base_edit.text(),
+                "docker_host_mount_prefix": self.docker_host_mount_prefix_edit.text(),
+                "wsl_distro": self.wsl_distro_edit.text(),
+                "rsync_flags": [flag.strip() for flag in self.rsync_flags_edit.text().split(",") if flag.strip()]
+            }
+            
+            with open(config_path, 'w') as f:
+                json.dump(updated_settings, f, indent=2)
+        except Exception as e:
+            print(f"Error saving settings.json: {e}")
+    
+    def auto_detect_docker_disk_base(self):
+        """Auto-detect docker_disk_base path"""
+        # Common paths to check
+        common_paths = [
+            "/tmp/docker-desktop-root/mnt/docker-desktop-disk/",
+            "/mnt/docker-desktop-disk/",
+            "/var/lib/docker/volumes/"
+        ]
+        
+        for path in common_paths:
+            if os.path.exists(path):
+                self.docker_disk_base_edit.setText(path)
+                return
+        
+        QMessageBox.information(self, "AutoDetect", "Could not auto-detect docker_disk_base path")
+    
+    def auto_detect_docker_host_mount_prefix(self):
+        """Auto-detect docker_host_mount_prefix path"""
+        # Common paths to check
+        common_paths = [
+            "/tmp/docker-desktop-root/run/desktop/mnt/host/",
+            "/run/desktop/mnt/host/",
+            "/mnt/host/"
+        ]
+        
+        for path in common_paths:
+            if os.path.exists(path):
+                self.docker_host_mount_prefix_edit.setText(path)
+                return
+        
+        QMessageBox.information(self, "AutoDetect", "Could not auto-detect docker_host_mount_prefix path")
+    
+    def auto_detect_wsl_distro(self):
+        """Auto-detect WSL distro"""
+        # Try to detect WSL distro
+        try:
+            import subprocess
+            result = subprocess.run(['wsl', '--list', '--quiet'], capture_output=True, text=True)
+            if result.returncode == 0:
+                distros = [line.strip() for line in result.stdout.split('\n') if line.strip()]
+                if distros:
+                    # Prefer docker-desktop if available, otherwise use first distro
+                    if 'docker-desktop' in distros:
+                        self.wsl_distro_edit.setText('docker-desktop')
+                    else:
+                        self.wsl_distro_edit.setText(distros[0])
+                    return
+        except Exception:
+            pass
+        
+        QMessageBox.information(self, "AutoDetect", "Could not auto-detect WSL distro")

    def accept(self):
        # Save settings
        win_path = self.win_path_edit.text()
        self.settings.setValue("default_win_path", win_path)
        self.settings.setValue("use_default", "true" if self.lock_checkbox.isChecked() else "false")
+        
+        # Save JSON settings
+        self._save_json_settings()
+        
         super().accept()
