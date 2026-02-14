import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QPushButton,
    QTreeView, QFileDialog, QLineEdit,
    QMessageBox, QLabel, QFormLayout, QHBoxLayout
)
from PySide6.QtCore import Qt

from volume_model import VolumeTreeModel
from backup_worker import BackupWorker
from utils import convert_windows_path_to_docker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Docker Backup Tool (PySide6)")
        self.resize(800, 600)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Tree
        self.tree = QTreeView()
        self.model = VolumeTreeModel()
        self.tree.setModel(self.model)
        self.tree.expandToDepth(1)
        layout.addWidget(self.tree)

        # Destination
        form_layout = QFormLayout()

        self.dest_input = QLineEdit()
        self.dest_input.setPlaceholderText("Select backup destination...")

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_folder)

        h_layout = QHBoxLayout()
        h_layout.addWidget(self.dest_input)
        h_layout.addWidget(browse_btn)

        form_layout.addRow("Backup Destination:", h_layout)

        layout.addLayout(form_layout)

        # Browse Button
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_folder)
        layout.addWidget(browse_btn)

        # Run Backup Button
        run_btn = QPushButton("Run Backup")
        run_btn.clicked.connect(self.run_backup)
        layout.addWidget(run_btn)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Backup Folder")
        if folder:
            docker_path = convert_windows_path_to_docker(folder)
            self.dest_input.setText(docker_path)

    def run_backup(self):
        selected = self.model.get_selected_paths()
        dest = self.dest_input.text()

        if not selected or not dest:
            QMessageBox.warning(self, "Error", "Select volumes and destination.")
            return

        self.worker = BackupWorker(selected, dest)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.error_signal.connect(self.on_error)
        self.worker.start()

    def on_finished(self, msg):
        QMessageBox.information(self, "Success", msg)

    def on_error(self, err):
        QMessageBox.critical(self, "Error", err)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())