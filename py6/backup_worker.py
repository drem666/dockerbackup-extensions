from PySide6.QtCore import QThread, Signal
from utils import run_backup


class BackupWorker(QThread):
    finished_signal = Signal(str)
    error_signal = Signal(str)

    def __init__(self, paths, destination):
        super().__init__()
        self.paths = paths
        self.destination = destination

    def run(self):
        try:
            run_backup(self.paths, self.destination)
            self.finished_signal.emit("Backup completed successfully.")
        except Exception as e:
            self.error_signal.emit(str(e))