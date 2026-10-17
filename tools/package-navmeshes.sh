#!/usr/bin/env bash
# package-navmeshes.sh - pack the repo's navmeshes into dist/daoc-navmeshes-<set>.tar.xz (one GitHub
# release asset, ~360 MB), for people who run a release instead of building from source.
#
#   tools/package-navmeshes.sh               from world/navmesh/*.xz (the normal case)
#
# The repo itself carries one .xz per mesh (tools/navmesh-stage.sh adds new ones). About 4 minutes.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="$REPO/world/navmesh-manifest.sha256"
SET="$(sed -n 's/^# Navmesh set \([^:]*\):.*/\1/p' "$MANIFEST" | head -1)"
[[ -n $SET ]] || { echo "package-navmeshes: no set name in $MANIFEST" >&2; exit 1; }
OUT="$REPO/dist/daoc-navmeshes-$SET.tar.xz"

mkdir -p "$REPO/dist"
work=$(mktemp -d "$REPO/dist/.navmesh.XXXXXX")
trap 'rm -rf "$work"' EXIT
"$REPO/tools/navmesh-unpack.sh" "$work/navmesh"
echo "Packing (xz, multi-threaded) ..."
tar -C "$work" -cf - navmesh | xz -6 -T0 > "$OUT.tmp"
mv "$OUT.tmp" "$OUT"
sha256sum "$OUT" | awk '{print $1}' > "$OUT.sha256"
echo "Done: $OUT ($(du -h "$OUT" | cut -f1))"
