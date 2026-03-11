import json
import os
from datetime import datetime

class BackupHistory:
    def __init__(self, manifest_path):
        self.manifest_path = manifest_path
        self.entries = []
        self.load()

    def load(self):
        if os.path.exists(self.manifest_path):
            with open(self.manifest_path, 'r') as f:
                self.entries = json.load(f)
        else:
            self.entries = []

    def save(self):
        with open(self.manifest_path, 'w') as f:
            json.dump(self.entries, f, indent=2)

    def add_entry(self, paths, archive_filename):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "paths": paths,
            "archive": archive_filename
        }
        self.entries.append(entry)
        self.save()

    def get_entries(self):
        return self.entries