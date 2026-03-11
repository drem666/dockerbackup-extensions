

Interactive container selection
Validation of container existence
Source/destination path validation
File/folder transfer into containers
Multiple transfer methods (docker cp or rsync)
Archive extraction inside container
Timestamped operation logging

## The Bash script contributes several useful operational features that are worth porting.
Key ideas in the script
The script implements a robust interactive container transfer utility with:

## Container validation
Ensures the container exists and is running (docker ps check).

## Source path validation
Ensures the file or folder exists locally.

## Destination validation inside container
Uses docker exec to verify the destination directory exists.

## Multiple transfer methods
    docker cp
    rsync

## Archive-aware transfers
Handles:
    zip
    tar
    tar.gz
    tar.bz2

## Temporary staging in /tmp
Archives are copied to /tmp and then extracted in the destination.

## Automatic cleanup
Removes temp files inside container after extraction.

## Timestamped operation logs