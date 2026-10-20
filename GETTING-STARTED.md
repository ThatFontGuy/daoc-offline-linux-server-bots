# Getting started: run your own Dark Age of Camelot server with bots

This walks through everything from zero: getting the server running on a Linux machine, then
connecting a Windows game client to it. No prior experience with Linux, DAoC servers, or this
project is assumed.

**The short version:** you run a small, free server program on a Linux machine (your own PC, a
home server, a cheap VPS — anything). It builds a complete classic Dark Age of Camelot world
(Classic + Shrouded Isles) filled with autonomous bots that level, group, raid and fight on their
own, plus "companion" bots you can summon to help you. Then you install the actual game client
(a separate, free download) on a Windows PC and point it at your server.

---

## Part 1: Setting up the server

**What you need:** a 64-bit Linux machine (a spare PC, a home server, a cloud VPS, a Steam Deck —
anything reasonably modern) with about 6 GB of free disk space and internet access.

### 1. Download the server

Go to the project's [Releases page](https://github.com/ThatFontGuy/daoc-offline-linux-server-bots/releases)
and download the newest `daoc-server-<version>-linux-x64.tar.gz`.

### 2. Extract it and set it up

Open a terminal on your Linux machine, go to wherever you downloaded the file, and run:

```bash
tar -xzf daoc-server-*-linux-x64.tar.gz
cd daoc-server
./navmesh-install.sh
```

`navmesh-install.sh` downloads one more file automatically (the "navmeshes" — the data that lets
monsters and bots walk around obstacles instead of into walls) and installs it. This takes a
minute or two depending on your connection.

### 3. Tell the server its own address

Before starting it, open `config/serverconfig.xml` in a text editor and find the line with
`<RegionIP>`. Set it to this machine's address on your home network (for example
`192.168.1.50`) — **not** `127.0.0.1` or `localhost`. This step matters a lot: skip it and
clients will often connect, then immediately fail right after picking a character, which is a
confusing error to debug blind. If you don't know this machine's address, on Linux run `ip a` and
look for an address starting with `192.168.` or `10.`.

### 4. Start it

```bash
./daoc-server.sh start
```

This starts the server in the background and opens an admin screen in the same terminal, with
tabs for server status, managing bots, turning the bot population on/off, and managing accounts.
**Ctrl+Q** closes this screen (it'll ask whether to stop the server or leave it running in the
background) — `./daoc-admin` reopens it later. `./daoc-server.sh stop` stops it from any terminal.

Your server is now running and waiting for a client to connect, on TCP port 10300.

---

## Part 2: Setting up the game client (Windows)

The game client is a separate, free download — not part of this project, since the project is
server-only. This covers the classic client; a new client is in development separately (see
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)).

### 1. Download the client

Go to [shadowofze/OfflineDAoC's releases](https://github.com/shadowofze/OfflineDAoC/releases) and
find the release matching your server's world version (check with `./daoc-admin status` on the
server — it'll show something like `0.37` or `0.37b`). Under that release's **Assets**, download
the two small files listed there (something like `DOWNLOAD-AND-PLAY-v0.37.cmd` and
`Get-OfflineDAoC.ps1`) into a new, empty folder with a short path (for example `C:\Games\OfflineDAoC`).

### 2. Install it

Double-click the `.cmd` file (no need to open PowerShell yourself — it does that internally).
Press **2** for a new install. It downloads the complete game (about 5 GB) into a new folder next
to it.

### 3. Find `connect.exe` — don't use the normal launcher

This is the single most important step, and the one most likely to trip you up: **don't**
double-click `START OFFLINE DAOC.cmd`. That launcher always starts its own separate, local,
single-player server on your own PC — it has nothing to do with the server you just set up, and
running it will just confuse you with a different, empty world.

Instead, look inside the folder the installer created (something like `playable-v0.37`) for a
file called `connect.exe`. It's usually nested a few folders deep, for example:
```
playable-v0.37\runtime\client-opendaoc\app\connect.exe
```
(the exact folder name can vary slightly — if `client-opendaoc\app` isn't there, look for a
sibling folder called `client` instead). Easiest way to find it: use File Explorer's search box,
scoped to your `playable-v0.37` folder, and search for `connect.exe`. It should be sitting right
next to a file called `game.dll`.

### 4. Make a shortcut to connect (recommended)

Once you've found it, create a text file next to `connect.exe` named `CONNECT TO SERVER.cmd`
with this content (use a real text editor like Notepad, and make sure Windows doesn't save it as
`CONNECT TO SERVER.cmd.txt` — in File Explorer, show file extensions first):

```batch
@echo off
rem Connects directly to your DAoC server, bypassing the single-player launcher.
set SERVER=192.168.1.50
set ACCOUNT=youraccountname
set PASSWORD=yourpassword

connect.exe game.dll %SERVER% %ACCOUNT% %PASSWORD%
pause
```

Replace `192.168.1.50` with your server's actual address (the same one you put in
`serverconfig.xml` above), and pick any account name and password you like — your account is
created automatically the first time you connect. From now on, just double-click this file
instead of hunting for `connect.exe` each time.

(Heads up: this stores your password as plain text in the file. That's fine for a personal server
on your own network, but don't reuse an important password here.)

### 5. Connect

Double-click `CONNECT TO SERVER.cmd`. The game should launch and log straight into your server.
If it connects but then kicks you out right after picking a character, double-check `RegionIP`
on the server (step 3 of Part 1) — that's almost always the cause.

### 6. Make your account an admin (optional)

Back on the server, once you've logged in at least once:
```bash
./daoc-admin accounts set-role youraccountname admin
```

---

## Letting friends connect from outside your home

By default, only devices on your own home network can reach the server. To let friends connect
from elsewhere:

1. Make sure `<RegionIP>` in `config/serverconfig.xml` is set to your **public** IP address (or a
   dynamic DNS hostname if your public IP changes), not your local network address.
2. On your home router, forward **TCP port 10300** and **UDP port 10400** to the Linux machine
   running the server.
3. Friends use the same `connect.exe game.dll <your-public-address> <their-account> <their-password>`
   approach as above, with your public address instead of your local one.

---

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Client connects, then disconnects right after character select | `<RegionIP>` isn't set to the server's real address |
| `./daoc-server.sh start` says the port is already in use | Another copy of the server (or an old one) is still running; stop it first |
| Can't find `connect.exe` | It's nested inside the install, not at the top level — see Part 2, step 3 |
| The game starts but shows an empty, unfamiliar world | You used `START OFFLINE DAOC.cmd` by accident — that starts a separate local server, not yours |
| Batch file closes immediately with no message | Open it from inside a Command Prompt instead of double-clicking, so you can read the error before the window closes, or add `pause` at the end if it's missing |

For anything server-side beyond this (managing bots, accounts, upgrading, running it as a
background service), see [deploy/README-release.md](deploy/README-release.md) — it ships inside
the downloaded server folder too.
