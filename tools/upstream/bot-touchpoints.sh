#!/usr/bin/env bash
# bot-touchpoints.sh - list the files OUTSIDE the Bots module that reference bot types.
# These are where core and bots are coupled. After an upstream sync, any file here that the sync
# changed deserves a look (see docs/UPSTREAM-SYNC.md). Run from anywhere; prints repo-relative paths.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../src"
grep -rlE '\b(GameBot|IGamePlayer|BotBrain|BotManager|Autonomous[A-Z][A-Za-z]+|Companion[A-Z][A-Za-z]+|Bot[A-Z][A-Za-z]+)\b' \
  --include=*.cs GameServer CoreServer CoreBase CoreDatabase Pathing | sort | sed 's|^|src/|'
