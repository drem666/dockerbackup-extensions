from PySide6.QtCore import QThread, Signal
from utils import run_archive_backup

class ArchiveWorker(QThread):
    finished_signal = Signal(str, str)  # (message, archive_path)
    error_signal = Signal(str)

    def __init__(self, paths, destination_folder):
        super().__init__()
        self.paths = paths
        self.destination_folder = destination_folder
        self.archive_path = None

    def run(self):
        try:
            self.archive_path = run_archive_backup(self.paths, self.destination_folder)
            self.finished_signal.emit(f"Archive created: {self.archive_path}", self.archive_path)
        except Exception as e:
            self.error_signal.emit(str(e))