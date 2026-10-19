#!/usr/bin/env bash
# fetch-upstream-db.sh - provide the pinned OpenDAoC-Database dump in .cache/ and verify it.
# Uses the copy bundled in world/upstream-db/ (no internet needed); downloads only if that is missing.
# Prints the path of the verified opendaoc-db-core folder.
set -euo pipefail

# Pinned in UPSTREAM.md. The content hash covers the .sql files themselves (sorted
# "sha256  name" lines), so it does not depend on how GitHub compresses its archives.
DB_COMMIT="98738ab8495f7e0a17412318e7c7c32a96d0eb09"
DB_CONTENT_SHA256="82be1a5b46e309a3edb80740e0cb3097003423be0d9f407cd35c94650f21979d"

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CACHE="$REPO/.cache/opendaoc-db-$DB_COMMIT"
DUMP="$CACHE/opendaoc-db-core"

content_hash() { (cd "$1" && sha256sum *.sql | sort -k2 | sha256sum | cut -d' ' -f1); }

BUNDLED="$REPO/world/upstream-db/opendaoc-db-$DB_COMMIT.tar.xz"

if [[ ! -d $DUMP && -f $BUNDLED ]]; then
  mkdir -p "$CACHE"
  echo "Unpacking bundled OpenDAoC-Database $DB_COMMIT ..." >&2
  tar -xJf "$BUNDLED" -C "$CACHE"
fi
if [[ ! -d $DUMP ]]; then
  mkdir -p "$CACHE"
  echo "Downloading OpenDAoC-Database $DB_COMMIT ..." >&2
  curl -fsSL --retry 3 "https://codeload.github.com/OpenDAoC/OpenDAoC-Database/tar.gz/$DB_COMMIT" \
    | tar -xz -C "$CACHE" --strip-components=1 --wildcards '*/opendaoc-db-core/*'
fi
actual=$(content_hash "$DUMP")
if [[ $actual != "$DB_CONTENT_SHA256" ]]; then
  echo "fetch-upstream-db: content hash mismatch for $DUMP" >&2
  echo "  expected $DB_CONTENT_SHA256" >&2
  echo "  actual   $actual" >&2
  echo "  Delete $CACHE and retry; if it persists, the pin in this script needs updating." >&2
  exit 1
fi
echo "$DUMP"
