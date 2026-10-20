#!/bin/bash
# Downloads the official Godot engine build and the official Offline DAoC new-client content
# (about 34 GB total, resumable - rerun this any time it stops). See setup_client.py for what it
# does and where everything comes from.
set -euo pipefail
cd "$(dirname "$0")"
python3 setup_client.py install
echo
read -r -p "Press Enter to close..."
