#!/usr/bin/env bash
# navmesh-unpack.sh - rebuild a navmesh folder from the repo's world/navmesh/*.xz and verify it
# against world/navmesh-manifest.sha256. Used by build-release.sh and package-navmeshes.sh.
#
#   tools/navmesh-unpack.sh <destination folder>     (created if missing; MANIFEST.sha256 is copied in)
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="$REPO/world/navmesh-manifest.sha256"
OUT=${1:?"usage: $0 <destination folder>"}
compgen -G "$REPO/world/navmesh/*.xz" >/dev/null || { echo "navmesh-unpack: no world/navmesh/*.xz (is the checkout complete?)" >&2; exit 1; }

mkdir -p "$OUT"
grep -v '^#' "$MANIFEST" | awk '{print $2}' | xargs -P "$(nproc)" -I{} sh -c 'xz -dc "$1/world/navmesh/$2.xz" > "$3/$2"' _ "$REPO" {} "$OUT"
(cd "$OUT" && grep -v '^#' "$MANIFEST" | sha256sum --check --quiet) || { echo "navmesh-unpack: navmeshes failed verification against $MANIFEST" >&2; exit 1; }
cp "$MANIFEST" "$OUT/MANIFEST.sha256"
echo "navmesh-unpack: $(grep -vc '^#' "$MANIFEST") files verified into $OUT"
