import os
import subprocess
import json

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


def run_backup(selected_paths, destination):
    ensure_destination(destination)

    base_prefix = SETTINGS["docker_disk_base"]

    for rel_path in selected_paths:
        clean_rel = rel_path.lstrip('/')
        src = os.path.join(base_prefix, clean_rel)

        cmd = [
            "wsl", "-d", SETTINGS["wsl_distro"],
            "rsync",
            *SETTINGS["rsync_flags"],
            src,
            destination
        ]

        subprocess.run(cmd, check=True)