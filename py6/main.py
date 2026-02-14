import sys, re, os
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("Drem666", "DockerBackupTool")
        self.setWindowTitle("Docker Backup Tool — Pro Edition")
        self.resize(1100, 700)

        self._create_toolbar()
        self._create_ui()
        self._create_statusbar()
        self._load_settings()
        self._load_themes()
        self._apply_theme(self.current_theme)   # restore last theme
    # -----------------------
    # Theme Switch
    # -----------------------
    def _load_themes(self):
        self.themes = {}
        themes_path = os.path.join(os.path.dirname(__file__), "config", "themes.qss")
        if not os.path.exists(themes_path):
            # Create a default themes.qss if missing
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
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(self.themes.keys())
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        self.toolbar.addWidget(QLabel("Theme:"))
        self.toolbar.addWidget(self.theme_combo)

        # Restore last theme
        self.current_theme = self.settings.value("theme", "Default")
        if self.current_theme in self.themes:
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

        refresh_action = QAction("Refresh Volumes", self)
        refresh_action.triggered.connect(self.refresh_volumes)
        toolbar.addAction(refresh_action)

        self.run_action = QAction("Run Backup", self)
        self.run_action.triggered.connect(self.run_backup)
        toolbar.addAction(self.run_action)

        self.mirror_checkbox = QCheckBox("Mirror Mode (--delete)")
        self.mirror_checkbox.setChecked(True)
        toolbar.addWidget(self.mirror_checkbox)

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

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_folder)

        dest_layout.addWidget(QLabel("Backup Destination:"))
        dest_layout.addWidget(self.dest_input)
        dest_layout.addWidget(browse_btn)

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
        self.log("Refreshing volume list...")
        self.model = VolumeTreeModel()
        self.tree.setModel(self.model)
        self.tree.expandToDepth(1)
        self.log("Volume list refreshed.")

    def run_backup(self):
        selected = self.model.get_selected_paths()
        dest = self.dest_input.text().strip()

        if not selected:
            QMessageBox.warning(self, "Error", "No volumes selected.")
            return

        if not dest:
            QMessageBox.warning(self, "Error", "No backup destination selected.")
            return

        # Optional: verify that the destination is reachable
        # (e.g., try to create a test file, but that might be overkill)
        self.progress.setVisible(True)

        self.log(f"Selected paths: {selected}")
        self.log(f"Destination: {dest}")

        self.progress.setVisible(True)
        self.progress.setRange(0, 0)  # Indeterminate

        self.set_ui_enabled(False)

        self.worker = BackupWorker(selected, dest)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.error_signal.connect(self.on_error)
        self.worker.start()

    def _load_settings(self):
        # Restore last destination
        last_dest = self.settings.value("last_destination", "")
        if last_dest:
            self.dest_input.setText(last_dest)

    def on_finished(self, msg):
        self.log(msg)
        self.progress.setVisible(False)
        self.set_ui_enabled(True)
        self.settings.setValue("last_destination", self.dest_input.text())
        QMessageBox.information(self, "Success", msg)

    def on_error(self, err):
        self.log(f"ERROR: {err}")
        self.progress.setVisible(False)
        self.set_ui_enabled(True)
        QMessageBox.critical(self, "Backup Failed", err)

    def set_ui_enabled(self, enabled):
        self.tree.setEnabled(enabled)
        self.run_action.setEnabled(enabled)

    def log(self, message):
        self.log_output.append(message)
        self.status.showMessage(message, 5000)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())