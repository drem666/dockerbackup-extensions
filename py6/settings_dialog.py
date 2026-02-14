# settings_dialog.py
import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QCheckBox, QFileDialog,
                               QDialogButtonBox, QFormLayout)
from PySide6.QtCore import QSettings
from utils import convert_windows_path_to_docker

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(500, 200)

        self.settings = QSettings("Drem666", "DockerBackupTool")

        # Load current settings
        self.default_win_path = self.settings.value("default_win_path", "")
        self.use_default = self.settings.value("use_default", "false") == "true"

        # Create widgets
        self.win_path_edit = QLineEdit(self.default_win_path)
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_folder)

        self.docker_path_label = QLabel()
        self.update_docker_path(self.default_win_path)

        self.lock_checkbox = QCheckBox("Use this as default destination (lock)")
        self.lock_checkbox.setChecked(self.use_default)

        # Connect signals
        self.win_path_edit.textChanged.connect(self.on_win_path_changed)

        # Layout
        form_layout = QFormLayout()
        form_layout.addRow("Windows path:", self.win_path_edit)
        form_layout.addRow("", self.browse_btn)
        form_layout.addRow("Docker path:", self.docker_path_label)
        form_layout.addRow("", self.lock_checkbox)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout = QVBoxLayout()
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Default Backup Folder")
        if folder:
            self.win_path_edit.setText(folder)

    def on_win_path_changed(self, text):
        self.update_docker_path(text)

    def update_docker_path(self, win_path):
        docker_path = convert_windows_path_to_docker(win_path)
        self.docker_path_label.setText(docker_path if docker_path else "(invalid path)")

    def accept(self):
        # Save settings
        win_path = self.win_path_edit.text()
        self.settings.setValue("default_win_path", win_path)
        self.settings.setValue("use_default", "true" if self.lock_checkbox.isChecked() else "false")
        super().accept()