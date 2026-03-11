import sys, re, os, subprocess
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTreeView, QFileDialog, QLineEdit, QMessageBox, QTextEdit, QSplitter,
    QToolBar, QStatusBar, QLabel, QProgressBar, QCheckBox, QComboBox, QDialog, QListWidget, QMessageBox
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QAction

from volume_model import VolumeTreeModel
from backup_worker import BackupWorker
from utils import convert_windows_path_to_docker, convert_docker_path_to_windows
from settings_dialog import SettingsDialog
from backup_history import BackupHistory
from archive_worker import ArchiveWorker
from restore_worker import RestoreWorker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("Drem666", "DockerBackupTool")
        self.setWindowTitle("Docker Backup Tool")
        self.resize(1100, 700)

        self._create_toolbar()
        # Backup mode selector
        self.toolbar.addSeparator()
        self.toolbar.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Copy (rsync)", "Archive (tar.gz)"])
        self.toolbar.addWidget(self.mode_combo)

        # History button
        history_btn = QPushButton("Backup History")
        history_btn.clicked.connect(self.open_history_dialog)
        self.toolbar.addWidget(history_btn)

        self._create_ui()
        self._create_statusbar()
        self._load_themes()
        self._apply_theme(self.current_theme)   # restore last theme
        self._load_settings()
        self.ensure_rsync()     

    def on_archive_finished(self, message, archive_path):
        self.log(message)
        self.run_action.setEnabled(True)
        self.progress.setVisible(False)
        QMessageBox.information(self, "Success", message)

        # Update history
        dest = self.dest_input.text().strip()
        win_path = convert_docker_path_to_windows(dest)
        if win_path:
            manifest_path = os.path.join(win_path, "backup_manifest.json")
            history = BackupHistory(manifest_path)
            # archive_path is a WSL path; store relative or full? We'll store the filename
            archive_filename = os.path.basename(archive_path)
            history.add_entry(self.model.get_selected_paths(), archive_filename)
    # -----------------------
    # Theme Switch
    # -----------------------
    def _load_themes(self):
        self.themes = {}
        themes_path = os.path.join(os.path.dirname(__file__), "config", "themes.qss")
        if not os.path.exists(themes_path):
            # Create a default themes.qss if missing
            os.makedirs(os.path.dirname(themes_path), exist_ok=True)
            with open(themes_path, "w") as f:
                f.write("/*Theme: Default*/\n/* (empty) */\n/*ThemeEnd*/")
        with open(themes_path, "r") as f:
            content = f.read()
        # Regex to capture theme blocks
        pattern = r"/\*Theme:\s*(.*?)\*/(.*?)/\*ThemeEnd\*/"
        matches = re.findall(pattern, content, re.DOTALL)
        for name, qss in matches:
            self.themes[name.strip()] = qss.strip()

        # Add theme combo to toolbar
        self.toolbar.addSeparator()
        self.toolbar.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(self.themes.keys())
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        self.toolbar.addWidget(self.theme_combo)

        # Restore last theme
        saved_theme = self.settings.value("theme", "Default")
        if saved_theme in self.themes:
            self.current_theme = saved_theme
        else:
            self.current_theme = "Default" if "Default" in self.themes else next(iter(self.themes))
        self.theme_combo.setCurrentText(self.current_theme)

    def _on_theme_changed(self, theme_name):
        self._apply_theme(theme_name)
        self.settings.setValue("theme", theme_name)

    def _apply_theme(self, theme_name):
        qss = self.themes.get(theme_name, "")
        self.setStyleSheet(qss)
        # Force repaint of tree view to refresh checkboxes
        if hasattr(self, 'tree'):
            self.tree.viewport().update()
            self.tree.update()  # sometimes needed
    # -----------------------
    # UI CREATION
    # -----------------------

    def _create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        self.toolbar = toolbar

        refresh_action = QAction("Refresh Volumes", self)
        refresh_action.triggered.connect(self.refresh_volumes)
        toolbar.addAction(refresh_action)

        self.run_action = QAction("Run Backup", self)
        self.run_action.triggered.connect(self.run_backup)
        toolbar.addAction(self.run_action)

        self.mirror_checkbox = QCheckBox("Mirror Mode (--delete)")
        self.mirror_checkbox.setChecked(True)
        toolbar.addWidget(self.mirror_checkbox)

        toolbar.addSeparator()

        # Settings button
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings_dialog)
        toolbar.addAction(settings_action)



    def open_settings_dialog(self):
        dialog = SettingsDialog(self)
        if dialog.exec():
            self._apply_destination_settings()

    def _apply_destination_settings(self):
        use_default = self.settings.value("use_default", "false") == "true"
        default_win_path = self.settings.value("default_win_path", "")

        if use_default and default_win_path:
            docker_path = convert_windows_path_to_docker(default_win_path)
            self.dest_input.setText(docker_path)
            self.dest_input.setReadOnly(True)
            # Disable browse button (if you have a reference to it)
            # You'll need to store browse_btn as an instance variable, e.g., self.browse_btn
            if hasattr(self, 'browse_btn'):
                self.browse_btn.setEnabled(False)
        else:
            self.dest_input.setReadOnly(False)
            if hasattr(self, 'browse_btn'):
                self.browse_btn.setEnabled(True)
            # Load last destination (auto-saved)
            last_dest = self.settings.value("last_destination", "")
            if last_dest:
                self.dest_input.setText(last_dest)

    def _create_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        # Splitter
        splitter = QSplitter(Qt.Horizontal)

        # Tree
        self.tree = QTreeView()
        self.model = VolumeTreeModel()
        self.tree.setModel(self.model)
        self.tree.setHeaderHidden(True)
        self.tree.expandToDepth(1)

        splitter.addWidget(self.tree)

        # Log Panel
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        splitter.addWidget(self.log_output)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter)

        # Destination row
        dest_layout = QHBoxLayout()

        self.dest_input = QLineEdit()
        self.dest_input.setPlaceholderText("Select backup destination...")

        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_folder)
        dest_layout.addWidget(self.browse_btn)

        dest_layout.addWidget(QLabel("Backup Destination:"))
        dest_layout.addWidget(self.dest_input)
        dest_layout.addWidget(self.browse_btn)

        main_layout.addLayout(dest_layout)

    def _create_statusbar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.status.addPermanentWidget(self.progress)

    def open_history_dialog(self):
        # Determine manifest path based on current destination? Or let user choose?
        # For simplicity, we'll use the current destination folder as base.
        dest = self.dest_input.text().strip()
        if not dest:
            QMessageBox.warning(self, "Error", "Please select a destination folder first.")
            return
        # Convert dest (WSL path) to Windows path for manifest
        # We need a function to convert back; we can store manifest in the same folder as archives.
        # For now, we'll assume the destination is a WSL path pointing to a Windows folder.
        # We'll store manifest in that folder (as Windows path).
        # We'll need a helper to convert WSL path to Windows. Let's add a function in utils.
        win_path = convert_docker_path_to_windows(dest)
        if not win_path:
            QMessageBox.warning(self, "Error", "Cannot determine Windows path for manifest.")
            return
        manifest_path = os.path.join(win_path, "backup_manifest.json")
        dlg = BackupHistoryDialog(manifest_path, self)
        dlg.exec()

    # -----------------------
    # FUNCTIONS
    # -----------------------

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Backup Folder")
        if folder:
            docker_path = convert_windows_path_to_docker(folder)
            self.dest_input.setText(docker_path)

    def refresh_volumes(self):
        """
        FIXED: Instead of creating a new model, update the existing one.
        This preserves the checkbox states.
        """
        print(">>> refresh_volumes called")
        self.log("Refreshing volume list...")
        
        # Save the current checked states
        checked_paths = self.model.get_selected_paths()
        
        # Rebuild the model
        self.model.rebuild()
        
        # Restore the checked states
        self.model.restore_checked_states(checked_paths)
        
        self.tree.expandToDepth(1)
        self.log("Volume list refreshed.")

    def run_backup(self):
        selected = self.model.get_selected_paths()
        dest = self.dest_input.text().strip()

        if not selected:
            QMessageBox.warning(self, "Error", "No volumes selected.")
            return

        if not dest:
            QMessageBox.warning(self, "Error", "No destination selected.")
            return

        mode = self.mode_combo.currentText()

        if mode == "Copy (rsync)":
            # Existing rsync logic
            self.log(f"Starting rsync backup of {len(selected)} items to {dest}...")
            self.run_action.setEnabled(False)
            self.progress.setVisible(True)
            self.progress.setRange(0, 0)

            self.worker = BackupWorker(selected, dest)
            self.worker.finished_signal.connect(self.on_backup_finished)
            self.worker.error_signal.connect(self.on_backup_error)
            self.worker.start()
        else:  # Archive mode
            self.log(f"Creating compressed archive of {len(selected)} items in {dest}...")
            self.run_action.setEnabled(False)
            self.progress.setVisible(True)
            self.progress.setRange(0, 0)

            self.archive_worker = ArchiveWorker(selected, dest)
            # 👇 Add these two connections right here
            self.archive_worker.finished_signal.connect(self.on_archive_finished)
            self.archive_worker.error_signal.connect(self.on_backup_error)  # reuse same error handler
            self.archive_worker.start()

    def on_backup_finished(self, message):
        self.log(message)
        self.run_action.setEnabled(True)
        self.progress.setVisible(False)
        QMessageBox.information(self, "Success", message)

    def on_backup_error(self, error):
        self.log(f"Error: {error}")
        self.run_action.setEnabled(True)
        self.progress.setVisible(False)
        QMessageBox.critical(self, "Backup Failed", error)

    def log(self, msg):
        self.log_output.append(msg)
        
    def _load_settings(self):
        """Load saved settings on startup"""
        self._apply_destination_settings()

    def check_rsync_installed(self):
        """Check if rsync is installed in docker-desktop WSL distro."""
        try:
            subprocess.run(
                ["wsl", "-d", "docker-desktop", "sh", "-c", "command -v rsync"],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def ensure_rsync(self):
        """Prompt user to install rsync if missing."""
        if not self.check_rsync_installed():
            reply = QMessageBox.question(
                self,
                "rsync Missing",
                "rsync is not installed in the docker-desktop WSL distro.\n\n"
                "Install it now? (requires admin rights)",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    subprocess.run(
                        ["wsl", "-d", "docker-desktop", "-u", "root", "sh", "-c", "apk update && apk add rsync"],
                        check=True
                    )
                    QMessageBox.information(self, "Success", "rsync installed.")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Installation failed: {e}")
            else:
                QMessageBox.warning(self, "Warning", "Backup will fail without rsync.")

    def restore_from_archive(self, archive_wsl_path, paths_to_restore):
        self.restore_worker = RestoreWorker(archive_wsl_path, paths_to_restore)
        self.restore_worker.finished_signal.connect(self.on_restore_finished)
        self.restore_worker.error_signal.connect(self.on_restore_error)
        self.restore_worker.start()
        self.log(f"Starting restore from {archive_wsl_path}...")
        # Disable UI etc.

    def on_restore_finished(self, message):
        self.log(message)
        QMessageBox.information(self, "Restore Complete", message)

    def on_restore_error(self, error):
        self.log(f"Restore error: {error}")
        QMessageBox.critical(self, "Restore Failed", error)

class BackupHistoryDialog(QDialog):
    def __init__(self, manifest_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Backup History")
        self.setMinimumSize(600, 400)
        self.manifest_path = manifest_path
        self.history = BackupHistory(manifest_path)

        layout = QVBoxLayout()

        self.list_widget = QListWidget()
        self.populate_list()
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        restore_btn = QPushButton("Restore Selected")
        restore_btn.clicked.connect(self.restore_selected)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(restore_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def populate_list(self):
        for entry in self.history.get_entries():
            text = f"{entry['timestamp']} - {entry['archive']} ({len(entry['paths'])} items)"
            self.list_widget.addItem(text)
            # Store entry data in item
            item = self.list_widget.item(self.list_widget.count()-1)
            item.setData(Qt.UserRole, entry)

    def restore_selected(self):
        current = self.list_widget.currentItem()
        if not current:
            QMessageBox.warning(self, "Error", "No backup selected.")
            return
        entry = current.data(Qt.UserRole)
        archive_filename = entry['archive']
        # Archive is stored in the same folder as manifest
        archive_path = os.path.join(os.path.dirname(self.manifest_path), archive_filename)
        # Convert to WSL path for restore
        wsl_archive = convert_windows_path_to_docker(archive_path)
        if not wsl_archive:
            QMessageBox.critical(self, "Error", "Cannot determine WSL path for archive.")
            return

        # Ask user if they want to restore all or select specific paths
        reply = QMessageBox.question(self, "Restore",
                                     "Restore all contents of this backup?\n"
                                     "Click No to select specific items.",
                                     QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        if reply == QMessageBox.Cancel:
            return

        # For now, we'll just restore all. Later we can add a selection dialog.
        self.parent().restore_from_archive(wsl_archive, paths=None if reply == QMessageBox.Yes else [])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())