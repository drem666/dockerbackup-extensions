#!/bin/bash

# Script: ~/mnt/c/Users/USER/dockers/dockertransfersync.sh
# Purpose: Copy files/folders to Docker container using chosen method
# Supports: zip, tar, tar.gz, tar.bz2 (7z requires p7zip-full in container)

# Initialize variables
CONTAINER=""
METHOD=""
TYPE=""
SOURCE=""
DEST=""
LOG_DIR="$(dirname "$0")"
TIMESTAMP=$(date "+%Y.%m.%d-%H.%M.%S")

# Function to validate Docker container
validate_container() {
    if ! docker ps --format '{{.Names}}' | grep -qw "$1"; then
        echo "Error: Container '$1' does not exist or is not running."
        return 1
    fi
    return 0
}

# Function to validate paths
validate_path() {
    if [ "$1" = "source" ]; then
        if [ ! -e "$SOURCE" ]; then
            echo "Retry, source location not found. CTRL+C to exit"
            return 1
        fi
    else
        if ! docker exec "$CONTAINER" sh -c "[ -d '$DEST' ]" 2>/dev/null; then
            echo "Retry, destination location not found in container. CTRL+C to exit"
            return 1
        fi
    fi
    return 0
}

# Function to log operations
log_operation() {
    local log_file="$LOG_DIR/$TIMESTAMP-dockertransfersync-$METHOD-$CONTAINER.log"
    {
        echo "===== Docker Transfer Sync Log ====="
        echo "Timestamp: $TIMESTAMP"
        echo "Method: $METHOD"
        echo "Container: $CONTAINER"
        echo "Type: $TYPE"
        echo "Source: $SOURCE"
        echo "Destination: $DEST"
        echo "-----------------------------------"
        echo "Operation Output:"
        cat "$TEMP_LOG"
        echo "==================================="
    } > "$log_file"
    echo "Log saved to: $log_file"
}

# Main script
TEMP_LOG=$(mktemp)

# Get container name
while true; do
    read -rp "Enter container name: " CONTAINER
    if validate_container "$CONTAINER"; then
        break
    fi
done

# Get method
while true; do
    read -rp "Choose method (dockercp/rsync): " METHOD
    case $METHOD in
        dockercp|rsync) break ;;
        *) echo "Invalid method. Choose 'dockercp' or 'rsync'." ;;
    esac
done

# Get type (folder/compressed file)
while true; do
    read -rp "Is this a folder or compressed file? (folder/zip/tar/targz/bzip): " TYPE
    case $TYPE in
        folder|zip|tar|targz|bzip) break ;;
        *) echo "Invalid type. Supported: folder, zip, tar, targz, bzip (Note: 7z not supported directly)" ;;
    esac
done

# Get source location
if command -v zenity &>/dev/null; then
    SOURCE=$(zenity --file-selection --directory --title="Select source folder/file" 2>/dev/null)
fi

while [ -z "$SOURCE" ]; do
    read -rp "Enter full source path (GUI selection failed or unavailable): " SOURCE
    if ! validate_path "source"; then
        SOURCE=""
    fi
done

# Get destination location
while true; do
    read -rp "Enter destination path in container: " DEST
    if validate_path "destination"; then
        break
    fi
done

# Perform the copy operation
echo "Starting transfer with $METHOD..."
case $METHOD in
    dockercp)
        case $TYPE in
            folder)
                docker cp "$SOURCE" "$CONTAINER:$DEST" > "$TEMP_LOG" 2>&1
                ;;
            zip|tar|targz|bzip)
                docker cp "$SOURCE" "$CONTAINER:/tmp/tempfile.$TYPE" > "$TEMP_LOG" 2>&1
                case $TYPE in
                    zip) docker exec "$CONTAINER" sh -c "unzip /tmp/tempfile.zip -d '$DEST' && rm /tmp/tempfile.zip" >> "$TEMP_LOG" 2>&1 ;;
                    tar) docker exec "$CONTAINER" sh -c "tar xf /tmp/tempfile.tar -C '$DEST' && rm /tmp/tempfile.tar" >> "$TEMP_LOG" 2>&1 ;;
                    targz) docker exec "$CONTAINER" sh -c "tar xzf /tmp/tempfile.tar.gz -C '$DEST' && rm /tmp/tempfile.tar.gz" >> "$TEMP_LOG" 2>&1 ;;
                    bzip) docker exec "$CONTAINER" sh -c "tar xjf /tmp/tempfile.tar.bz2 -C '$DEST' && rm /tmp/tempfile.tar.bz2" >> "$TEMP_LOG" 2>&1 ;;
                esac
                ;;
        esac
        ;;
    rsync)
        case $TYPE in
            folder)
                if ! docker exec "$CONTAINER" command -v rsync >/dev/null 2>&1; then
                    echo "Installing rsync in container..." >> "$TEMP_LOG"
                    docker exec "$CONTAINER" sh -c 'apt-get update && apt-get install -y rsync || apk add rsync' >> "$TEMP_LOG" 2>&1
                fi
                rsync -avz "$SOURCE/" -e "docker exec -i $CONTAINER bash -c 'cat > /tmp/rsync.tar'" --files-from <(cd "$SOURCE" && find . -type f) >> "$TEMP_LOG" 2>&1
                docker exec "$CONTAINER" sh -c "mkdir -p '$DEST' && tar xf /tmp/rsync.tar -C '$DEST' && rm /tmp/rsync.tar" >> "$TEMP_LOG" 2>&1
                ;;
            *)
                echo "Note: Rsync method only supports folders directly. Using docker cp for archives." >> "$TEMP_LOG"
                docker cp "$SOURCE" "$CONTAINER:/tmp/tempfile.$TYPE" >> "$TEMP_LOG" 2>&1
                docker exec "$CONTAINER" sh -c "case '$TYPE' in
                    zip) unzip /tmp/tempfile.zip -d '$DEST' ;;
                    tar) tar xf /tmp/tempfile.tar -C '$DEST' ;;
                    targz) tar xzf /tmp/tempfile.tar.gz -C '$DEST' ;;
                    bzip) tar xjf /tmp/tempfile.tar.bz2 -C '$DEST' ;;
                esac && rm /tmp/tempfile.$TYPE" >> "$TEMP_LOG" 2>&1
                ;;
        esac
        ;;
esac

# Verify and log
if [ $? -eq 0 ]; then
    echo "Transfer completed successfully!"
else
    echo "Transfer encountered errors. Check log for details."
fi

log_operation
rm "$TEMP_LOG"