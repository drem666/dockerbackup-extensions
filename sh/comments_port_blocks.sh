#!/bin/bash

# Function to display usage information
usage() {
  echo "Usage: $0 -d <directory>"
  echo "  -d    Specify the directory containing docker-compose.yml files"
  exit 1
}

# Parse command-line options
while getopts ":d:" opt; do
  case ${opt} in
    d )
      target_dir="$OPTARG"
      ;;
    \? )
      echo "Invalid option: -$OPTARG" >&2
      usage
      ;;
    : )
      echo "Option -$OPTARG requires an argument." >&2
      usage
      ;;
  esac
done

# Check if the directory was provided
if [ -z "$target_dir" ]; then
  echo "Error: Directory not specified."
  usage
fi

# Verify that the provided path is a directory
if [ ! -d "$target_dir" ]; then
  echo "Error: '$target_dir' is not a valid directory."
  exit 1
fi

# Process each docker-compose.yml file in the specified directory
find "$target_dir" -type f -name "docker-compose.yml" | while read -r file; do
  echo "Processing $file"

  awk '
    BEGIN { in_ports_block=0 }
    /^[[:space:]]*ports:/ {
      in_ports_block=1
      print "#" $0
      next
    }
    in_ports_block {
      if (/^[[:space:]]*[^[:space:]]/) {
        in_ports_block=0
      } else {
        print "#" $0
        next
      }
    }
    { print }
  ' "$file" > "${file}.tmp" && mv "${file}.tmp" "$file"
done
