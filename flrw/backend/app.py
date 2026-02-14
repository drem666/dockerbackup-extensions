import os
import subprocess
from flask import Flask, jsonify, request

app = Flask(__name__)

def build_tree(paths):
    """
    Builds a nested tree structure from a list of relative paths.
    Each node is a dictionary with 'path' and 'children' keys.
    """
    tree = []
    node_dict = {}
    root = {"path": "/", "children": []}
    node_dict["/"] = root

    for path in sorted(paths):
        if not path.startswith("/"):
            path = "/" + path
        node = {"path": path, "children": []}
        node_dict[path] = node

        parent = os.path.dirname(path)
        if parent == "" or parent == path:
            parent = "/"
        if parent not in node_dict:
            node_dict[parent] = {"path": parent, "children": []}
            if parent != "/":
                tree.append(node_dict[parent])
        node_dict[parent]["children"].append(node)
    
    tree = root["children"]
    return tree

def list_volumes():
    """
    Uses WSL to run 'find' via sh to list all files and directories under the Docker disk mount.
    """
    base_dir = "/tmp/docker-desktop-root/mnt/docker-desktop-disk/"
    # Using a find command that returns both directories and files.
    cmd = [
        "wsl", "-d", "docker-desktop", "sh", "-c",
        f"cd '{base_dir}' && find . \\( -type d -o -type f \\)"
    ]
    try:
        output = subprocess.check_output(cmd, universal_newlines=True)
        lines = output.splitlines()
        paths = []
        for line in lines:
            # The output is relative; we convert it to have a leading '/'
            if line.startswith("./"):
                rel = line[1:]  # This leaves the slash intact.
            else:
                rel = line
            if not rel:
                rel = "/"
            paths.append(rel)
        tree = build_tree(paths)
        return tree
    except Exception as e:
        print("Error in list_volumes:", e)
        return {"error": str(e)}

def ensure_destination(dest):
    """Improved destination handling with WSL support"""
    prefix = "/tmp/docker-desktop-root/run/desktop/mnt/host/"
    if dest.startswith(prefix):
        # Windows path creation
        remainder = dest[len(prefix):].lstrip("/")
        if not remainder:
            raise Exception("Invalid destination path")
        parts = remainder.split("/", 1)
        drive = parts[0].upper() + ":\\"
        path_rest = parts[1].replace("/", "\\") if len(parts) > 1 else ""
        win_path = os.path.join(drive, path_rest)
        os.makedirs(win_path, exist_ok=True)
    else:
        # Create Linux path directly in WSL
        subprocess.run(
            ["wsl", "-d", "docker-desktop", "mkdir", "-p", dest],
            check=True,
            stderr=subprocess.PIPE
        )

@app.route('/api/volumes', methods=['GET'])
def get_volumes():
    volumes = list_volumes()
    return jsonify(volumes)

@app.route('/api/backup', methods=['POST'])
def backup():
    data = request.get_json()
    selected_paths = data.get('paths', [])
    destination = data.get('destination')
    
    if not selected_paths or not destination:
        return jsonify({"error": "Paths and destination must be provided."}), 400

    try:
        ensure_destination(destination)
    except Exception as e:
        return jsonify({"error": f"Destination error: {str(e)}"}), 500

    # Rsync through WSL with proper paths
    base_prefix = "/tmp/docker-desktop-root/mnt/docker-desktop-disk/"
    for rel_path in selected_paths:
        # Clean path construction
        clean_rel = rel_path.lstrip('/')
        src = os.path.join(base_prefix, clean_rel)
        
        # Execute rsync through WSL
        cmd = [
            "wsl", "-d", "docker-desktop",
            "rsync", "-a", "--delete", "--relative",
            src, destination
        ]
        
        try:
            result = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
        except subprocess.CalledProcessError as e:
            return jsonify({
                "error": f"rsync failed: {e.stderr}",
                "command": " ".join(cmd)
            }), 500

    return jsonify({"status": "Backup completed successfully"})
if __name__ == '__main__':
    app.run(port=5000, debug=True)
