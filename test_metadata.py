#!/usr/bin/env python3

import json
import os

print("Testing metadata loading...")

metadata_file = 'pdf_metadata.json'
if not os.path.exists(metadata_file):
    print(f"Error: {metadata_file} not found")
    exit(1)

print(f"Loading metadata from {metadata_file}")
with open(metadata_file, 'r', encoding='utf-8') as f:
    metadata = json.load(f)

print(f"Loaded {len(metadata)} metadata entries")

# Filter only completed downloads
completed_metadata = [item for item in metadata if item.get('download_status') == 'completed']

print(f"Found {len(completed_metadata)} completed PDF downloads")

if not completed_metadata:
    print("No completed PDF downloads found")
    exit(1)

print("Metadata loading successful!")
print(f"First completed item: {completed_metadata[0]['pdf_filename']}")