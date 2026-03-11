from PySide6.QtCore import QThread, Signal
from utils import run_restore

class RestoreWorker(QThread):
    finished_signal = Signal(str)
    error_signal = Signal(str)

    def __init__(self, archive_path, paths_to_restore=None):
        super().__init__()
        self.archive_path = archive_path
        self.paths_to_restore = paths_to_restore  # None means restore all

    def run(self):
        try:
            run_restore(self.archive_path, self.paths_to_restore)
            self.finished_signal.emit("Restore completed successfully.")
        except Exception as e:
            self.error_signal.emit(str(e))