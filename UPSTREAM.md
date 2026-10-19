# Upstream

Policy: **static snapshot, manual pulls.** See docs/ARCHITECTURE.md §9.

## Offline DAoC (direct parent)

- Upstream: https://github.com/shadowofze/OfflineDAoC (has git history and release tags).
- Our `src/` = upstream `source/server/` (`GameServer` with its `bots/` folder at `src/Bots`, `CoreBase`, `CoreDatabase`, `CoreServer`,
  `Pathing`, `Tests`, `sharedModules`) plus our own changes.
- Original fork point: upstream **`08ebffe`** (2026-10-01, between v0.33 and v0.34). Found by matching
  blobs: 3,214 of our 3,228 files were identical to it.
- **Synced to v0.35 / 0.35b "Claude Takeover III" (`d337d18`, 2026-10-08).** Applied
  `08ebffe..d337d18` for `source/server/{GameServer,CoreServer,Tests}` (our commit `5bf27bd`).
  Not imported: `source/server/tools/` (Windows client patchers and navmesh analysis scripts).
  - `CoreServer/Actions/ConsoleStart.cs`: kept ours. Upstream `c1c465c` (PR #3) backs off on stdin
    EOF; our console thread already stops reading at EOF.
- **Synced to v0.36 (`d88b7b2`, 2026-10-16).** v0.36, v0.36b and v0.36c are the same commit; the editions differ only in
  release packaging, which we don't import. Applied `d337d18..d88b7b2` for `source/server/{GameServer,CoreServer,CoreBase,
  CoreDatabase,Pathing,sharedModules,Tests}` with `git apply -p3 --directory=src` (clean, no conflicts). Includes the
  save-snapshot memory-leak fix (`CoreDatabase/DataObject.cs`, `UT_DataObjectSnapshot`), dead-pet cleanup, and the new
  autonomous bot logic (`bots/autonomous/AutonomousArmyPush`, `ZoneRoads`, ...). Not imported: client, launcher, release
  scripts and `tools/`. Sluaghbinder additions (`CripplingPlague`) came along because they are woven into shared enums;
  they stay off via `classes / enable_sluaghbinder = False`.
- **Synced to v0.37 (`ab4df02`, 2026-10-18).** v0.37, v0.37b and v0.37c are the same commit; the editions differ only
  in release packaging (0.37c adds the new Godot client), which we don't import. Applied `d88b7b2..ab4df02` with
  `tools/upstream/sync.sh offlinedaoc apply v0.37b` (74 files; one rejected hunk). Includes guilds for gamebots
  (`gameutils/Guild.cs`, `GuildMgr.cs`, `bots/autonomous/AutonomousBotGuilds.cs`), bot group travel as one pack
  (`AutonomousGroupFormationFollow`), further Caer Sidi/Galladoria raid progress, and quest/pathfinding fixes.
  - `Bots/autonomous/AutonomousPopulationController.cs`: one hunk conflicted with our own bot-login-pacing and
    `max_active_bots` logic (`bot_logins_per_second`, `LogOutExcessBots`). Hand-merged upstream's `OrphanChecked`
    cache, the orphan-repair interval (1 -> 10 minutes) and the new guild reconcile/remove hooks; verified against
    upstream's file afterward (`diff` showed only our own additions remaining).
- Next pull: `tools/upstream/sync.sh offlinedaoc report|check|apply <tag>` (docs/UPSTREAM-SYNC.md). Our own changes on top are small: `Admin.Host/`,
  `DaocAdmin/`, `Admin.Protocol/`, `WorldBuilder/`, population settings, login handler, console
  host, the csproj files and `Pathing/Detour/CMakeLists.txt`.
- The Sluaghbinder ("b" edition) code stays in, switched off by `classes / enable_sluaghbinder = False`,
  as upstream does for its plain edition.

## World data and navmeshes

- Upstream ships its world DB and navmeshes only inside the release zip, never in git.
- **World: v0.36 (plain edition).** The plain DB is `OfflineDAoC-v0.36b/editions/0.36-no-custom-class/runtime/data/opendaoc.sqlite3.db`
  inside `OfflineDAoC-v0.36b.zip.001-.003` (SHA-256 `4fdb7ca4…`, matching the v0.36 `download-manifest.json`). It was
  read straight out of the split zip with HTTP range requests (about 30 MB transferred of 4.8 GB).
- `world/patches/200-*.sql` turn the OpenDAoC-Database dump (below) into that DB's world. They were regenerated with
  `tools/world/derive-world-delta.py` and verified to reproduce it exactly (0 differing tables).
  Compared with the 0.35 patches: 557 missing quest reward items are fixed, startup errors fell from 1,157 to 390.
  The 390 left are in upstream's own 0.36 DB (for example 7 missing poison/potion spells, 42 missing NPC templates).
- **Navmeshes: set `classic-si-3`, from the v0.36b zip** (`runtime/server/navmesh/`, 106 files, read with the same range
  requests). The 103 `zone*.nav` files and `seams.json` are byte-identical to the 0.35 set (`classic-si-2`); `pockets.json`
  changed and `roads.json` is new (read by `Bots/autonomous/AutonomousZoneRoads`; without it long bot walks use Detour only).
  Stored as one `.xz` per mesh in `world/navmesh/` so unchanged meshes cost nothing in later updates.
  - 0.35 reference: `OfflineDAoC-v0.35b.zip`, SHA-256 `5a1d77df…`, DB SHA-256 `feb4a511…`.

## OpenDAoC

- Upstream: https://github.com/OpenDAoC/OpenDAoC-Core. Offline DAoC is a fork of it with no recorded
  fork point. Compared with upstream `f0aaa1e` (2026-09-26): ~722 core files and ~50k lines differ,
  excluding `bots/`.
- Ported OpenDAoC fixes: none yet. Record each as `upstream <sha> -> our commit <sha>: why`.
- World data: https://github.com/OpenDAoC/OpenDAoC-Database, pinned at `98738ab8495f7e0a17412318e7c7c32a96d0eb09`
  (2026-09-29). A compressed copy is bundled in `world/upstream-db/` (with its GPL LICENSE);
  `tools/fetch-upstream-db.sh` unpacks it (or downloads, if it's missing) and checks a content hash
  over the `.sql` files. Moving the pin means re-running the delta script and re-verifying.
