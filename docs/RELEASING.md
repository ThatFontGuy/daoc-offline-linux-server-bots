# Releasing and maintaining the data

## Publishing a release on GitHub

1. Build in the box: `tools/setup-build-box.sh --build` (or `tools/build-release.sh` inside it).
2. Tag first if you want a real version name: `git tag v0.34 && tools/build-release.sh`. The
   version comes from `git describe`.
3. Create a GitHub release and attach:
   - `dist/daoc-server-<version>-linux-x64.tar.gz` (server and world, ~85 MB);
   - `dist/daoc-navmeshes-classic-si-4.tar.xz` and its `.sha256` (~360 MB; make it with
     `tools/package-navmeshes.sh`), for people who use the
     release instead of building from source. Upload it once per navmesh set: attach it to every
     release, or keep a dedicated `navmeshes-classic-si-4` release and link to it.

   People building from source don't need this; the navmeshes are in the source
   (`world/navmesh/`).
4. Put the navmesh download URL in `deploy/release.conf`
   (`NAVMESH_URL=https://github.com/catastrophic-impact/daoc-offline-linux-server-bots/releases/download/<tag>/daoc-navmeshes-classic-si-4.tar.xz`),
   commit, and rebuild. `./navmesh-install.sh` with no arguments then downloads it automatically
   when the archive isn't next to the folder.

Never attach or commit a played database, logs, `serverconfig.xml` or `admins.json`.
`.gitignore` covers `dist/`, `.cache/`, `*.db`, `*.sqlite`, `*.nav` and logs.

## Navmeshes

The repo carries one compressed file per mesh: `world/navmesh/zone042.nav.xz` and so on, plus
`seams.json.xz`, `pockets.json.xz` and `roads.json.xz`, listed with their SHA-256 in
`world/navmesh-manifest.sha256`. Git stores identical files once, so an Offline DAoC release that
changes 3 meshes adds about 20 MB to the repo, not a whole new archive. The current set is the 103
meshes plus the three bot data files (zone borders, walled pockets, roads) from Offline DAoC 0.36
(see `UPSTREAM.md`).

```bash
tools/navmesh-unpack.sh <folder>      # repo -> verified folder (build-release.sh does this)
tools/navmesh-stage.sh <folder>       # folder of new meshes -> repo; only changed files are recompressed
tools/package-navmeshes.sh            # repo -> dist/daoc-navmeshes-<set>.tar.xz for a release (~4 min)
```

**New meshes from an Offline DAoC release:** read them out of the release zip
(`tools/world/rangezip.py`, folder `runtime/server/navmesh/`), run `tools/navmesh-stage.sh <folder>`,
`git add world/navmesh world/navmesh-manifest.sha256`, build, retest the bots (their route data,
`Bots/autonomous/data/*.json`, was tuned on the current set). If the set is a new one, also change
its name in the manifest header and in `deploy/navmesh-install.sh` (`SET=`) and `release.conf`.

## The world: upstream database pin and the Offline DAoC delta

- `tools/fetch-upstream-db.sh` pins OpenDAoC-Database (`DB_COMMIT`) and a content hash over its
  `.sql` files (`DB_CONTENT_SHA256`, independent of GitHub's archive compression).
- `world/patches/200-*.sql` are **generated**. Don't edit them by hand. They turn that upstream
  dump into the pristine world of the Offline DAoC release we track (0.36, plain edition).
- `world/patches/300-*.sql` are **hand-written** changes on top (for example
  `300-bot-login-speed.sql`). Add new world changes here, with a comment explaining why.

**Moving the upstream DB pin, or moving to a new Offline DAoC release** (rare and deliberate; for
a new release, skip step 1):
1. Set `DB_COMMIT` in `fetch-upstream-db.sh`, delete `.cache/`, move the old
   `world/upstream-db/*.tar.xz` away (otherwise it is used), run the script once (it downloads),
   and set `DB_CONTENT_SHA256` to the hash it prints in the mismatch message. Then bundle the new
   dump:
   `tar -C .cache/opendaoc-db-<commit> -cf - opendaoc-db-core | xz -9 > world/upstream-db/opendaoc-db-<commit>.tar.xz`
2. Build the plain upstream world (no patches):
   `dotnet src/WorldBuilder/bin/Release/net10.0/DaocWorldBuilder.dll --source <dump> --out /tmp/upstream.sqlite`
3. Regenerate the delta. You need the release's pristine plain-edition world DB:
   `editions/<version>-no-custom-class/runtime/data/opendaoc.sqlite3.db` inside the "b" release zip
   (for 0.36: SHA-256 `4fdb7ca4…`, also listed in the plain release's `download-manifest.json`).
   The zip is split in parts, so read the one file with HTTP range requests rather than downloading
   it all (see `tools/world/rangezip.py`).

   **Starting with 0.37, upstream ships world changes as a patch instead** (check the release's
   `download-manifest.json`: `"Mode": "patch"` means there is no full DB to range-read). Its
   game-patch zip has `db-<version>.json`: a row-level delta (`Insert`/`Update`/`Delete` per table,
   keyed by primary key) from the prior release's world. Apply it to the *previous* release's
   pristine DB instead of reading a new one out of a zip:
   `python3 tools/world/apply-release-db-delta.py db-<version>.json <previous pristine db> <pristine db>`
   (it verifies every `Update`'s "Old" row against the input DB first and refuses to continue
   silently if anything doesn't match). A `NewTables` entry is schema-only (no rows) and needs a
   matching `DataObject` on our side already; the script checks this.

   Either way, once you have the release's pristine plain-edition world DB:
   Set `WORLD` at the top of the script to the release, then
   `python3 tools/world/derive-world-delta.py <pristine db> /tmp/upstream.sqlite world/patches`
   (it removes nothing itself: delete the old `200-*` files first). Check the script's `EXCLUDED`
   list against the release's `progress-policy.json` (in its `OfflineDaoc.ProgressImport` source).
4. Verify: build with only the `200-*` patches (`--patches <folder with copies of them>`), then
   run the same script against the result. It must print `0 tables differ`.
5. Update `UPSTREAM.md`.

**Navmeshes change the same way now:** a patch-only release's game-patch zip only contains the
`runtime/server/navmesh/` files that actually changed (not all 106). Unpack the current set with
`tools/navmesh-unpack.sh`, overwrite just the changed files from the patch, then
`tools/navmesh-stage.sh <folder>` as above - it only recompresses files whose hash changed. If
anything in the set changed, bump the set name (`classic-si-N` -> `classic-si-N+1`) in
`world/navmesh-manifest.sha256`'s header, `deploy/navmesh-install.sh` (`SET=`) and
`deploy/release.conf`, even if only one file changed (precedent: 0.36 bumped the set for a
pockets.json-only change).

## Upgrading OpenDAoC itself

This code base is a heavily modified fork (about 720 upstream files changed). Upgrading means
merging. It's a project of its own, not a routine step; see `UPSTREAM.md`. Port individual
upstream fixes by hand and cite the upstream commit.
