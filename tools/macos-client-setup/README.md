# Offline DAoC macOS client setup

Lets players on a Mac (Apple Silicon or Intel) play Offline DAoC's Godot-based "new client"
natively, connecting to a server that already runs elsewhere (this project's server, on a TrueNAS
box or anywhere else) - no VM, no Wine.

This contains no game files. `Setup-Client.command` downloads two things fresh from their real
sources, every time it runs:

- the official Godot 4.7.2 (.NET) engine build, from
  [godotengine/godot-builds](https://github.com/godotengine/godot-builds) (MIT);
- the official Offline DAoC new-client project and converted content, from
  [shadowofze/OfflineDAoC](https://github.com/shadowofze/OfflineDAoC)'s own v0.36c release plus
  the v0.37c client patch (about 34 GB total) - the same release Windows players download, with
  only the `new-client/godot/` tree kept.

It does **not** install or run a server - point `client.conf` at a server that's already running
(this project's server, started separately; see the main repo's [docs/RUN.md](../../docs/RUN.md)).

## Setup

1. Double-click `Setup-Client.command`. It downloads about 34 GB in parts (resumable - if it
   stops, just run it again; already-verified parts are kept). Needs about 36 GB free disk space
   while it installs.
2. Edit `client.conf`: set `SERVER_HOST` to your server's address (a LAN IP works if you're on the
   same network; an external hostname works too, once you've port-forwarded TCP 10300 and UDP
   10400 on your router to the server).
3. Double-click `Play-DAoC.command` any time you want to play. Type your account name and password
   into the game's own login screen - this tool never asks for or stores them.

## Notes

- `CUSTOM_CLASS` in `client.conf` controls whether the Sluaghbinder shows up at character
  creation; it should match whether your server enables it
  (`classes / enable_sluaghbinder` in `serverconfig.xml`). Picking a class the server doesn't
  actually enable fails server-side either way - this just keeps the character screen honest.
- The pinned versions (Godot 4.7.2, Offline DAoC v0.36c + v0.37c patch) match the Offline DAoC
  version this project's own server tracks (see `UPSTREAM.md` in the repo root). If the server
  repo moves to a newer Offline DAoC version, update the `GODOT` / `BASE` / `PATCH` pins at the
  top of `setup_client.py` to match (the exact URLs, sizes and SHA-256 hashes are in
  `download-manifest.json` on each shadowofze/OfflineDAoC release).
- `python3 setup_client.py status` reports what's currently installed, without downloading
  anything.

## Where this came from

[trozzelle/OfflineDAoC-macOS](https://github.com/trozzelle/OfflineDAoC-macOS) (GPL-3.0) already
runs the same official client natively on macOS, as part of a larger all-in-one client+server
tool (its own server piece, `OfflineDAoC-macOS-server`, is itself a fork of this project). This
script borrows just that approach - the official Godot macOS build plus the official client
content, no Wine needed for the new client - and changes the one thing that didn't fit here: that
project hardcodes `127.0.0.1` because its client and server run on the same Mac; this one asks
`client.conf` for a server address instead, since this project's server runs separately.
