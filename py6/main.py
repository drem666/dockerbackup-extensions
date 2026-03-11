import sys, re, os, subprocess
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton,
    QTreeView, QFileDialog, QLineEdit,
    QMessageBox, QTextEdit, QSplitter,
    QToolBar, QStatusBar, QLabel,
    QProgressBar, QCheckBox, QComboBox
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QAction

from volume_model import VolumeTreeModel
from backup_worker import BackupWorker
from utils import convert_windows_path_to_docker
from settings_dialog import SettingsDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("Drem666", "DockerBackupTool")
        self.setWindowTitle("Docker Backup Tool")
        self.resize(1100, 700)

        self._create_toolbar()
        self._create_ui()
        self._create_statusbar()
        self._load_themes()
        self._apply_theme(self.current_theme)   # restore last theme
        self._load_settings()    
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

        # Theme combo will be added later in _load_themes

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

        # Add mirror mode flag if checked
        if self.mirror_checkbox.isChecked():
            # This will be handled in utils.py by adding --delete to rsync_flags
            pass

        self.log(f"Starting backup of {len(selected)} items to {dest}...")
        self.run_action.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)  # Indeterminate

        self.worker = BackupWorker(selected, dest)
        self.worker.finished_signal.connect(self.on_backup_finished)
        self.worker.error_signal.connect(self.on_backup_error)
        self.worker.start()

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

    def check_rsync():
        try:
            subprocess.run(
                ["wsl", "-d", "docker-desktop", "sh", "-c", "command -v rsync"],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    if not check_rsync():
        reply = QMessageBox.question(
            self,
            "rsync Missing",
            "rsync is not installed in the docker-desktop WSL distro.\n\n"
            "Install it now? (requires admin rights)",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            subprocess.run(
                ["wsl", "-d", "docker-desktop", "-u", "root", "sh", "-c", "apk update && apk add rsync"],
                check=True
            )
            QMessageBox.information(self, "Success", "rsync installed. Please restart the backup.")
        else:
            QMessageBox.warning(self, "Warning", "Backup will fail without rsync.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())