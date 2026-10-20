#!/bin/bash
# Launches the installed client, connecting to client.conf's SERVER_HOST. Edit that file any time
# to point at a different server (LAN IP, or an external address once you've port-forwarded).
set -euo pipefail
cd "$(dirname "$0")"
python3 setup_client.py play
