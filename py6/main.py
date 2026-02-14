import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton,
    QTreeView, QFileDialog, QLineEdit,
    QMessageBox, QTextEdit, QSplitter,
    QToolBar, QStatusBar, QLabel,
    QProgressBar, QCheckBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from volume_model import VolumeTreeModel
from backup_worker import BackupWorker
from utils import convert_windows_path_to_docker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Docker Backup Tool — Pro Edition")
        self.resize(1100, 700)

        self._create_toolbar()
        self._create_ui()
        self._create_statusbar()

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

        self.log(f"Selected paths: {selected}")
        self.log(f"Destination: {dest}")

        self.progress.setVisible(True)
        self.progress.setRange(0, 0)  # Indeterminate

        self.set_ui_enabled(False)

        self.worker = BackupWorker(selected, dest)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.error_signal.connect(self.on_error)
        self.worker.start()

    def on_finished(self, msg):
        self.log(msg)
        self.progress.setVisible(False)
        self.set_ui_enabled(True)
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