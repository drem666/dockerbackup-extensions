import os, subprocess, json, datetime
from pathlib import Path

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "config", "settings.json")

with open(SETTINGS_PATH, "r") as f:
    SETTINGS = json.load(f)


def build_tree(paths):
    root = {"path": "/", "children": []}
    node_dict = {"/": root}

    for path in sorted(paths):
        if not path.startswith("/"):
            path = "/" + path

        node = {"path": path, "children": []}
        node_dict[path] = node

        parent = os.path.dirname(path)
        if not parent or parent == path:
            parent = "/"

        if parent not in node_dict:
            node_dict[parent] = {"path": parent, "children": []}

        node_dict[parent]["children"].append(node)

    return root["children"]


def list_volumes():
    base_dir = SETTINGS["docker_disk_base"]

    cmd = [
        "wsl", "-d", SETTINGS["wsl_distro"],
        "sh", "-c",
        f"cd '{base_dir}' && find . \\( -type d -o -type f \\)"
    ]

    output = subprocess.check_output(cmd, universal_newlines=True)
    lines = output.splitlines()

    paths = []
    for line in lines:
        if line.startswith("./"):
            rel = line[1:]
        else:
            rel = line
        if not rel:
            rel = "/"
        paths.append(rel)

    return build_tree(paths)


def convert_windows_path_to_docker(win_path):
    if not win_path:
        return ""
    # Normalize to backslashes for Windows drive detection
    win_path = win_path.replace('/', '\\')
    import re
    match = re.match(r"^([A-Za-z]):\\(.*)", win_path)
    if not match:
        # If it still doesn't match, maybe it's already a Docker path? Print a warning.
        print(f"Warning: Could not convert Windows path: {win_path}")
        return ""
    drive = match.group(1).lower()
    rest = match.group(2).replace("\\", "/")
    return f"{SETTINGS['docker_host_mount_prefix']}{drive}/{rest}"


def ensure_destination(dest):
    prefix = SETTINGS["docker_host_mount_prefix"]

    if dest.startswith(prefix):
        remainder = dest[len(prefix):].lstrip("/")
        parts = remainder.split("/", 1)
        drive = parts[0].upper() + ":\\"
        path_rest = parts[1].replace("/", "\\") if len(parts) > 1 else ""
        win_path = os.path.join(drive, path_rest)
        os.makedirs(win_path, exist_ok=True)
    else:
        subprocess.run(
            ["wsl", "-d", SETTINGS["wsl_distro"], "mkdir", "-p", dest],
            check=True
        )


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
        # Destination should be a folder where archives are stored
        self.log(f"Creating compressed archive of {len(selected)} items in {dest}...")
        self.run_action.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)

        self.archive_worker = ArchiveWorker(selected, dest)
        self.archive_worker.finished_signal.connect(self.on_archive_finished)
        self.archive_worker.error_signal.connect(self.on_backup_error)
        self.archive_worker.start()

def run_archive_backup(selected_paths, destination_folder):
    """
    Create a timestamped tar.gz archive of selected paths inside docker-desktop WSL.
    Returns the full path (inside WSL) of the created archive.
    """
    base_dir = SETTINGS["docker_disk_base"]
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"backup_{timestamp}.tar.gz"

    # Convert destination folder to WSL path
    wsl_dest_folder = convert_windows_path_to_docker(destination_folder)
    if not wsl_dest_folder:
        raise Exception("Invalid destination folder")

    # Ensure destination exists
    subprocess.run(
        ["wsl", "-d", SETTINGS["wsl_distro"], "mkdir", "-p", wsl_dest_folder],
        check=True
    )

    archive_path = os.path.join(wsl_dest_folder, archive_name)

    # Build tar command: change to base_dir, then tar the relative paths
    relative_paths = [p.lstrip('/') for p in selected_paths]
    # Use -C to change directory, then add each path
    # We need to quote paths to handle spaces
    cmd = [
        "wsl", "-d", SETTINGS["wsl_distro"],
        "sh", "-c",
        f"cd '{base_dir}' && tar -czf '{archive_path}' {' '.join(relative_paths)}"
    ]
    subprocess.run(cmd, check=True)

    return archive_path

def run_restore(archive_path, paths_to_restore=None):
    """
    Restore from a tar.gz archive. If paths_to_restore is None, restore all.
    Otherwise, restore only those paths (which must be relative to base_dir).
    """
    base_dir = SETTINGS["docker_disk_base"]

    if paths_to_restore:
        # Extract only specified paths
        # We need to pass them as arguments to tar
        paths_str = ' '.join(paths_to_restore)
        cmd = [
            "wsl", "-d", SETTINGS["wsl_distro"],
            "sh", "-c",
            f"cd '{base_dir}' && tar -xzf '{archive_path}' {paths_str}"
        ]
    else:
        # Extract all
        cmd = [
            "wsl", "-d", SETTINGS["wsl_distro"],
            "sh", "-c",
            f"cd '{base_dir}' && tar -xzf '{archive_path}'"
        ]

    subprocess.run(cmd, check=True)

def convert_docker_path_to_windows(docker_path):
    """Convert a WSL path like /mnt/host/c/... to Windows path C:\..."""
    prefix = SETTINGS["docker_host_mount_prefix"]
    if docker_path.startswith(prefix):
        remainder = docker_path[len(prefix):].lstrip('/')
        parts = remainder.split('/', 1)
        drive = parts[0].upper() + ":\\"
        if len(parts) > 1:
            rest = parts[1].replace('/', '\\')
            return os.path.join(drive, rest)
        else:
            return drive
    return None

def on_archive_finished(self, message):
    self.log(message)
    self.run_action.setEnabled(True)
    self.progress.setVisible(False)
    QMessageBox.information(self, "Success", message)

    # After successful archive, update history
    dest = self.dest_input.text().strip()
    win_path = convert_docker_path_to_windows(dest)
    if win_path:
        manifest_path = os.path.join(win_path, "backup_manifest.json")
        history = BackupHistory(manifest_path)
        # The archive filename can be extracted from message or we could return it
        # For simplicity, we'll just add an entry with the current selected paths
        # But we don't have the exact archive name. We could modify ArchiveWorker to return it.
        # Let's adjust ArchiveWorker to emit the archive path.
        # We'll need to modify archive_worker.py to store archive_path and emit it.
        pass