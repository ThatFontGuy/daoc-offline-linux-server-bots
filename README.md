# DAoC Server

**New to this? Start with [GETTING-STARTED.md](GETTING-STARTED.md)** — a complete, beginner-friendly,
step-by-step walkthrough from downloading the server through connecting a game client.

A Linux-first, server-only DAoC server with autonomous and companion bots, based on a pinned
OpenDAoC fork from Offline DAoC (synced to 0.37). It builds into one portable folder that needs no
.NET install. The game client is not included; players install it separately — see
[Connecting a client](#connecting-a-client) below. (**Note:** earlier versions of this README
pointed at the unrelated opendaoc.com client; that's for a different, incompatible live server.
Use [shadowofze/OfflineDAoC](https://github.com/shadowofze/OfflineDAoC)'s client instead, as
described below.)

This is based off of Shadowofze's work at: https://github.com/shadowofze/OfflineDAoC

This project is meant to provide a fast and simple portable server on Linux instead of Windows. Tested on steam deck
but should work on any modern distro.

## Quick start: download a release (no build tools needed)

The easiest way to run this if you just want to play: grab a pre-built release, no .NET SDK,
cmake or distrobox required.

1. Go to the [Releases page](../../releases) and download `daoc-server-<version>-linux-x64.tar.gz`
   (the server) from the latest release.
2. Extract it, then:
   ```bash
   cd daoc-server
   ./navmesh-install.sh
   ./daoc-server.sh start
   ```
   `navmesh-install.sh` downloads the navmesh archive (~360 MB) automatically on first run. To
   avoid that extra download (or install offline), grab `daoc-navmeshes-classic-si-4.tar.xz` from
   the same release yourself and put it next to the `daoc-server` folder before running the script.
3. Connect a client — see [Connecting a client](#connecting-a-client) below.

That's it. Requirements: x86-64 Linux with glibc 2.34+ (Ubuntu 22.04+, Debian 12+, Fedora 35+,
SteamOS, Arch) and `libicu` (almost every distro has it already). Releases are built automatically
by [GitHub Actions](.github/workflows/release.yml) on every tagged version, directly from this
repo's source — nothing hidden.

## Building from source instead

If you want to build it yourself (to make changes, or just because you prefer it):

### What you need

**To run the server:** x86-64 Linux with glibc 2.34 or newer (Ubuntu 22.04+, Debian 12+,
Fedora 35+, SteamOS, Arch) and libicu (almost every distro has it). Nothing else; .NET is bundled.

**To build it, either:**
- **distrobox** (step 2a, recommended). It's preinstalled on SteamOS and packaged by most distros
  (https://distrobox.it). The build tools go into a container, not onto your system. **Or:**
- the **.NET 10 SDK, cmake, g++ and curl** installed yourself (step 2b).

Also: about **6 GB** of free disk space, and internet for the first build (for the build container and tools; the world database and navmeshes are already in the source).

Everything else is in the source, including the world and the navmeshes (`world/navmesh/`, one
compressed file per mesh, about 360 MB in all).

### 1. Get the source

```bash
git clone https://github.com/ThatFontGuy/daoc-offline-linux-server-bots.git
cd daoc-offline-linux-server-bots
```

Or download it as a ZIP from GitHub (**Code → Download ZIP**) and unpack it.

### 2a. Build (with distrobox, recommended)

From the source folder:

```bash
tools/setup-build-box.sh --build
```

This one command:
1. Creates a build container (`daoc-server-box`, Ubuntu 22.04).
2. Installs the .NET 10 SDK, cmake and g++ inside it. Nothing is installed on your system.
3. Builds the server, the world and the navmeshes into `dist/daoc-server`.

The first run takes several minutes. Re-running it is safe.

### 2b. Build (without distrobox)

Install the **.NET 10 SDK**, **cmake**, **g++** and **curl** with your package manager, then run
`tools/build-release.sh`.

### 3. The result

```
dist/daoc-server/                              <- the server, ready to start (world and navmeshes installed)
dist/daoc-server-<version>-linux-x64.tar.gz    <- the server without navmeshes, as one file
dist/daoc-navmeshes-classic-si-4.tar.xz        <- the navmeshes, as one file
```

To run it on another Linux machine, copy `dist/daoc-server` (or the two archives, then run
`./navmesh-install.sh` with the navmesh archive next to the folder). It needs no distrobox and no
.NET there.

### 4. Start the server

```bash
cd dist/daoc-server
./daoc-server.sh start
```

The server starts in the background and an admin screen opens in the same terminal:

| Tab | What you can do |
|---|---|
| **Server** | Status, live log, **Stop server** |
| **Bots** | See every bot and what it is doing; **create** real bots (realm, level 1 or 50, class, count); **delete** |
| **Population** | Turn bots on/off; set the most bots in the world at once |
| **Accounts** | Create accounts; make an account **player / GM / admin** |

- **Ctrl+Q** closes the screen and asks whether to stop the server or leave it running.
- `./daoc-admin` reopens the screen later.
- `./daoc-server.sh stop` stops the server from any terminal. It saves first.

Rebuilding replaces `dist/daoc-server`, including its world and saves. To keep a world you play
on, run your server from a copy outside `dist/`, and upgrade it as described in
[docs/RUN.md](docs/RUN.md).

## Connecting a client

The game client is a separate install (not part of this project). Get it from
[shadowofze/OfflineDAoC](https://github.com/shadowofze/OfflineDAoC/releases) — download the
release matching this server's world version (shown in `./daoc-admin status`, currently `0.37`
or `0.37b` for the Sluaghbinder). Use its downloader to install the client; **don't** use its
launcher's "START SERVER" button — that starts its own separate local server, not this one.
Instead, point the client straight at this machine, on port **10300**:

**Windows, the original client (run from inside the installed game folder):**
```
connect.exe game.dll <this machine's address> <account> <password>
```
No launcher, no Wine — run it directly in a Command Prompt.

**Linux or macOS, the original client, via Wine:**
```bash
wine connect.exe game.dll <this machine's address> <account> <password>
```

**The new Godot client (0.37c, BETA):** speaks the same protocol and takes the same kind of
argument. Instead of its launcher, run the client executable directly with
`--server=<this machine's address> --account=<account>` and its own password flag (same
`--name=value` style; see
[shadowofze/OfflineDAoC docs/NEW-CLIENT.md](https://github.com/shadowofze/OfflineDAoC/blob/main/docs/NEW-CLIENT.md)
for where that executable is inside its install). Windows only for now — it's built on Godot 4,
which is genuinely cross-platform, so a native macOS/Linux build of it is a plausible future
addition to this project, just not done yet.

Accounts are created on first login. To make yours an admin, go to the **Accounts** tab, or run
`./daoc-admin accounts set-role <account> admin`.

**Players on other machines:**
1. Edit `config/serverconfig.xml` and set `<RegionIP>` to this machine's LAN address (for
   example `192.168.1.20`), or to your public address when port-forwarding.
2. Restart the server.
3. Players connect to that address. Forward TCP 10300 and UDP 10400 on your router to let in
   players from outside your home network.

## What's in the game

- **World:** Classic + Shrouded Isles (the Offline DAoC 0.37 world), with Darkness Falls, the
  Realm Exchange and stablemaster routes.
- **Autonomous bots:** persistent characters that level, hunt, travel, group, raid and fight in
  RvR on their own. Manage them in the admin screen's Bots and Population tabs.
- **Companion bots:** summon helpers into your group:

  | Command | What |
  |---|---|
  | `/spawn [class]` | Companion class menu, or a companion of that class |
  | `/classes` | Your realm's classes and their party roles |
  | `/aggressive`, `/defensive` | Companions assist you, or wait for enemies to approach |
  | `/pull`, `/grind` | Order an engage; stationary automatic pulls |
  | `/raid 40`, `/raid 80` | A level-50 companion raid |
  | `/tele <bot>`, `/mobs`, `/stables` | Teleport to a bot or camp; monsters by level; stable routes |

## More

- [GETTING-STARTED.md](GETTING-STARTED.md): complete beginner walkthrough, server through client
- [deploy/README-release.md](deploy/README-release.md): the guide shipped inside the server folder
  (all admin commands, upgrading)
- [docs/RUN.md](docs/RUN.md): running and administering a server
- [docs/BUILD.md](docs/BUILD.md): building, testing and project layout
- [docs/BOTS-DEV.md](docs/BOTS-DEV.md): working on the bots (code map, 15-second dev loop)
- [docs/RELEASING.md](docs/RELEASING.md): publishing releases, navmesh set, world data
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): how the system fits together, decisions, known issues
- [AGENTS.md](AGENTS.md): start here as a contributor or AI assistant (folders, environment, rules)

## License

GPL v3. Based on OpenDAoC; see [src/LICENSE](src/LICENSE).
