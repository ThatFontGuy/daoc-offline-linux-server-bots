#!/usr/bin/env python3
"""macOS setup for the Offline DAoC "new" (Godot) game client - the client only, no server.

For players on Apple Silicon (or Intel) Macs who want to connect to a DAoC server that already
runs elsewhere (for example this project's server on a TrueNAS box) without a Windows VM. This
contains no game files itself: `install` downloads the same two things any player gets, fresh,
each time it runs:

  - the official Godot 4.7.2 (.NET) engine build, from godotengine/godot-builds (MIT) - not a
    custom build, the same one upstream pins for its own macOS packaging;
  - the official Offline DAoC "new client" project and converted content, from
    shadowofze/OfflineDAoC's own v0.36c release plus the v0.37c client patch on top of it (about
    34 GB total) - the same release Windows players download, with only its new-client/godot/
    tree kept (the Windows-only engine and launcher are skipped).

`play` then launches that Godot build on the project, pointed at the server address in
client.conf (edit that file any time - no need to re-run `install`). `play` prompts for the account
and password fresh each run (not stored by this tool) and passes them on the command line: passing
--server= alone makes the client skip its own login screen straight to an auto-login attempt
(game/login_screen.gd has no field to type into in that mode), so credentials have to come in this
way, the same as upstream's own launcher and trozzelle's tool do it.

This approach - and the exact pins below - comes from inspecting trozzelle/OfflineDAoC-macOS
(GPL-3.0), which runs the same official client natively on macOS as part of a larger all-in-one
client+server tool. This script borrows just the client piece and (unlike that tool, which
hardcodes 127.0.0.1 for a same-box server) connects to a server address you choose, since this
project's server already runs separately.

Usage: double-click Setup-Client.command once, then Play-DAoC.command any time you want to play.
Or run directly: python3 setup_client.py install | play | status
"""
import getpass
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATE = HERE / ".state"
DOWNLOADS = STATE / "downloads"
GODOT_DIR = STATE / "Godot.app"
GODOT_RECORD = GODOT_DIR / ".godot-sha256.txt"
PROJECT_DIR = STATE / "new-client" / "godot"
CONF_FILE = HERE / "client.conf"
CONF_EXAMPLE = HERE / "client.conf.example"
DOTNET_DIR = Path.home() / ".dotnet"

KEEP = "new-client/godot/"
NEW_PORT = 10300
DONE = ".done"
PATCH_JSON = "patch.json"
ABSENT = "absent"
MARGIN_BYTES = 2 * 1024 ** 3
MAX_RETRIES = 3

# Pinned upstream artifacts (shadowofze/OfflineDAoC v0.36c + the v0.37c client patch on top of
# it, matching the Offline DAoC version this project's own server tracks - see UPSTREAM.md in the
# server repo). Update these together if the server repo moves to a newer Offline DAoC version.
GODOT = {
    "url": "https://github.com/godotengine/godot-builds/releases/download/4.7.2-stable/"
           "Godot_v4.7.2-stable_mono_macos.universal.zip",
    "bytes": 200756622,
    "sha256": "8af3977b60d2c59802f7c8ff1914b3ca02a5e294f7381fc1104ee777e33cbbd8",
}

BASE = {
    "release_url": "https://github.com/shadowofze/OfflineDAoC/releases/download/v0.36c/",
    "root_folder": "OfflineDAoC-v0.36c",
    "unpacked_bytes": 33758711327,
    "parts": [
        {"name": "OfflineDAoC-v0.36c-part01.zip", "bytes": 1840662618, "sha256": "a782cbb828bb8b62570a3c73e3a1ef14d704b33764ce566e202dbf93ca28ac12"},
        {"name": "OfflineDAoC-v0.36c-part02.zip", "bytes": 1831910795, "sha256": "76d1d523126664bcfe326ea67976a9d7ee6a19c0743ac349383365a8d6927253"},
        {"name": "OfflineDAoC-v0.36c-part03.zip", "bytes": 1739876323, "sha256": "3fbb6b10e18997ba18afcc9f421401160f380eba59f2135d78e7c646907859e8"},
        {"name": "OfflineDAoC-v0.36c-part04.zip", "bytes": 1254219684, "sha256": "78795cff5988c30f509fa4ddd34d96e9d3558a031749d194735ff9c05dbb3c69"},
        {"name": "OfflineDAoC-v0.36c-part05.zip", "bytes": 1396669356, "sha256": "df4c7e8ddee9669ed193be4d8100d835b51a81b288c423111d75f8b36e839585"},
        {"name": "OfflineDAoC-v0.36c-part06.zip", "bytes": 1564469197, "sha256": "42f3b13760e15a1d83c9c573c8f61e0b4a432b7d974d3c7184249a23aa69bb0b"},
        {"name": "OfflineDAoC-v0.36c-part07.zip", "bytes": 1517661759, "sha256": "1eaa404729dc18aaebecf64306581bc341bb64c255e24add367b37c7023f6cc0"},
        {"name": "OfflineDAoC-v0.36c-part08.zip", "bytes": 1546709809, "sha256": "ddc103c0538c958cd340f8f637f059fd11b1a102f8d0d20c501e407b2de08162"},
        {"name": "OfflineDAoC-v0.36c-part09.zip", "bytes": 1616723879, "sha256": "2b12a42d1ba9438e52e2701a5ef1a9ec9c24bbdb2b4cb7f7cfb9e026e31c7624"},
        {"name": "OfflineDAoC-v0.36c-part10.zip", "bytes": 1799585431, "sha256": "8dc4a9e369ff7753d515ff6b66356c1fb0feb8014f6448cb46d8ebd8f6f21526"},
        {"name": "OfflineDAoC-v0.36c-part11.zip", "bytes": 1755120913, "sha256": "2bb7013721b7a34ec01b30de7ff6b0fe9f6929e5ac38be65f465a32d93e3e3b2"},
        {"name": "OfflineDAoC-v0.36c-part12.zip", "bytes": 1634256697, "sha256": "afb5b15f80083db12fe291c8594ef883d548b0e788aaa0f58e6d571b9e3c6e26"},
        {"name": "OfflineDAoC-v0.36c-part13.zip", "bytes": 1645985221, "sha256": "1d2623cc51c9f7bc5dd2876704526348ebd3f3efe9eb6e4de85263f3affc0ad5"},
        {"name": "OfflineDAoC-v0.36c-part14.zip", "bytes": 1652745752, "sha256": "b74c1f388b0a39a9262ea773e78e515fa05aa49ba1c74bea7a34e136cf2a0273"},
        {"name": "OfflineDAoC-v0.36c-part15.zip", "bytes": 1645569113, "sha256": "082776b1e4985c11e5afdd7db253556e84a7fec8bc2be1695d87bfa28fb9d7e0"},
        {"name": "OfflineDAoC-v0.36c-part16.zip", "bytes": 1644877640, "sha256": "857e6064ef89a30ccec215455330b070711bd0df40849951bf53c3397bcae688"},
        {"name": "OfflineDAoC-v0.36c-part17.zip", "bytes": 1697803933, "sha256": "aac692504d09b716d0588ba9ec7cacccd5cde2e79285dd3ec671ae206e11e20f"},
        {"name": "OfflineDAoC-v0.36c-part18.zip", "bytes": 1590626919, "sha256": "1605ec4bb167c95a8678bc1061544e6b9d120c1f052163d9213508ae59e346a2"},
        {"name": "OfflineDAoC-v0.36c-part19.zip", "bytes": 402403267, "sha256": "605b55d7220ec2c2c004c4f6181a366aecef44c39af5bf7aeea1d0b83fed7ff1"},
    ],
}

PATCH = {
    "release_url": "https://github.com/shadowofze/OfflineDAoC/releases/download/v0.37c/",
    "root_folder": "OfflineDAoC-v0.37c-client-patch",
    "unpacked_bytes": 3577331455,
    "parts": [
        {"name": "OfflineDAoC-v0.37c-client-patch-part01.zip", "bytes": 904068156, "sha256": "1d9b5796b1594d0c798cabb7d443dce7b7e25fc609bb4ac852805b94293cc49a"},
        {"name": "OfflineDAoC-v0.37c-client-patch-part02.zip", "bytes": 762980382, "sha256": "e5dce62abea6bca8516fd353be588c0004e53fec476416b13be2efcaef1705d9"},
    ],
}


def say(msg: str) -> None:
    print(msg, flush=True)


def fail(msg: str) -> "NoReturn":
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path, want_bytes: int, want_sha256: str) -> None:
    """Download url to dest, verified against want_sha256; a dest that already matches is kept
    as-is (a rerun resumes). Up to MAX_RETRIES attempts, each a fresh full download - these parts
    come over plain HTTPS with no server-side range support guaranteed."""
    if dest.is_file() and dest.stat().st_size == want_bytes and sha256_file(dest) == want_sha256:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            say(f"  downloading {dest.name} ({want_bytes / 1024 ** 2:.0f} MB, attempt {attempt}/{MAX_RETRIES}) ...")
            tmp = dest.with_suffix(dest.suffix + ".part")
            with urllib.request.urlopen(url, timeout=60) as resp, tmp.open("wb") as out:
                shutil.copyfileobj(resp, out, 1 << 20)
            if sha256_file(tmp) != want_sha256:
                tmp.unlink(missing_ok=True)
                raise ValueError(f"{dest.name} failed SHA-256 verification")
            os.replace(tmp, dest)
            return
        except (urllib.error.URLError, ValueError, OSError) as e:
            last_error = e
            time.sleep(2 * attempt)
    fail(f"could not download {url} after {MAX_RETRIES} attempts: {last_error}")


def extract_filtered(zip_path: Path, root_folder: str, dest: Path) -> None:
    """Extract root_folder/new-client/godot/... of zip_path into dest (that prefix dropped). Any
    entry outside root_folder/, or one that would land outside dest, is refused before anything
    is written (zip-slip protection)."""
    root = root_folder + "/"
    keep = root + KEEP
    base = str(dest.resolve()) + os.sep
    with zipfile.ZipFile(zip_path) as zf:
        infos = zf.infolist()
        for info in infos:
            if not info.filename.startswith(root):
                fail(f"refusing unexpected zip entry {info.filename!r} in {zip_path.name}")
            if info.filename.startswith(keep):
                target = (dest / info.filename[len(keep):]).resolve()
                if not (str(target) + os.sep).startswith(base) and str(target) != base.rstrip(os.sep):
                    fail(f"zip-slip attempt in {info.filename!r} ({zip_path.name})")
        for info in infos:
            if not info.filename.startswith(keep) or info.filename == keep:
                continue
            target = dest / info.filename[len(keep):]
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, target.open("wb") as out:
                shutil.copyfileobj(src, out, 1 << 20)
            stamp = time.mktime(info.date_time + (0, 0, -1))
            os.utime(target, (stamp, stamp))


def read_patch(zip_path: Path, root_folder: str):
    name = root_folder + "/" + PATCH_JSON
    with zipfile.ZipFile(zip_path) as zf:
        if name not in zf.namelist():
            return None
        return json.loads(zf.read(name))


def _godot_files(patch):
    return {f["Path"][len(KEEP):]: f for f in patch.get("Files") or [] if f["Path"].startswith(KEEP)}


def _file_sha(path: Path) -> str:
    return sha256_file(path) if path.is_file() else ABSENT


def apply_patch_part(zip_path: Path, root_folder: str, dest: Path, patch) -> None:
    """Write root_folder/files/new-client/godot/... of a patch part over dest (the base's godot
    tree), verified file by file against patch.json before and after writing."""
    root = root_folder + "/"
    keep = root + "files/" + KEEP
    listed = _godot_files(patch)
    base = str(dest.resolve()) + os.sep
    with zipfile.ZipFile(zip_path) as zf:
        infos = zf.infolist()
        for info in infos:
            if not info.filename.startswith(root):
                fail(f"refusing unexpected zip entry {info.filename!r} in {zip_path.name}")
            if info.filename.startswith(keep) and not info.is_dir():
                rel = info.filename[len(keep):]
                target = (dest / rel).resolve()
                if not str(target).startswith(base):
                    fail(f"zip-slip attempt in {info.filename!r} ({zip_path.name})")
                if rel not in listed:
                    fail(f"{zip_path.name} carries {rel}, which its patch.json does not list")
        for info in infos:
            if not info.filename.startswith(keep) or info.is_dir():
                continue
            rel = info.filename[len(keep):]
            want, target = listed[rel], dest / rel
            current = _file_sha(target)
            if current == want["Sha256"]:
                continue
            if current not in want["From"]:
                fail(f"the new client's {rel} is not the file this patch replaces ({current[:12]}); "
                     "delete .state/new-client and rerun install")
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_name(target.name + ".tmp")
            with zf.open(info) as src, tmp.open("wb") as out:
                shutil.copyfileobj(src, out, 1 << 20)
            if sha256_file(tmp) != want["Sha256"]:
                tmp.unlink()
                fail(f"{rel} from {zip_path.name} failed SHA-256 verification")
            stamp = time.mktime(info.date_time + (0, 0, -1))
            os.utime(tmp, (stamp, stamp))
            os.replace(tmp, target)


def finish_patch(dest: Path, patch) -> None:
    for r in patch.get("Remove") or []:
        if r["Path"].startswith(KEEP):
            target = dest / r["Path"][len(KEEP):]
            current = _file_sha(target)
            if current != ABSENT and current not in r["From"]:
                fail(f"the new client's {r['Path'][len(KEEP):]} is not the file this patch removes")
            target.unlink(missing_ok=True)
    missing = [rel for rel, f in _godot_files(patch).items()
               if not (dest / rel).is_file() or (dest / rel).stat().st_size != f["Bytes"]]
    if missing:
        fail(f"the patch left {len(missing)} new-client file(s) unwritten, e.g. {missing[0]}")


def needed_bytes() -> int:
    return BASE["unpacked_bytes"] + PATCH["unpacked_bytes"] + max(
        p["bytes"] for p in BASE["parts"] + PATCH["parts"]) + MARGIN_BYTES


def install_godot() -> None:
    if GODOT_DIR.is_dir() and GODOT_RECORD.is_file() and GODOT_RECORD.read_text().strip() == GODOT["sha256"]:
        say("Godot already installed")
        return
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    zip_path = DOWNLOADS / "Godot_v4.7.2-stable_mono_macos.universal.zip"
    say("fetching the official Godot 4.7.2 (.NET) macOS build ...")
    download(GODOT["url"], zip_path, GODOT["bytes"], GODOT["sha256"])
    unpack = STATE / ".godot.new"
    shutil.rmtree(unpack, ignore_errors=True)
    unpack.mkdir(parents=True)
    # ditto (not zipfile) to keep the .app bundle's resource forks and extended attributes, and
    # its code signature, intact.
    subprocess.run(["/usr/bin/ditto", "-x", "-k", str(zip_path), str(unpack)], check=True)
    app = next(unpack.glob("Godot*.app"), None)
    if app is None:
        fail(f"{zip_path.name} holds no Godot*.app")
    shutil.rmtree(GODOT_DIR, ignore_errors=True)
    app.rename(GODOT_DIR)
    shutil.rmtree(unpack, ignore_errors=True)
    GODOT_RECORD.write_text(GODOT["sha256"] + "\n")
    say(f"Godot installed: {GODOT_DIR}")


def ensure_dotnet() -> None:
    marker = DOTNET_DIR / "shared" / "Microsoft.NETCore.App"
    if marker.is_dir() and any(p.name.startswith("10.") for p in marker.iterdir()):
        say(".NET 10 runtime already installed")
        return
    say("fetching the .NET 10 runtime (installed into ~/.dotnet if missing) ...")
    script = STATE / "dotnet-install.sh"
    STATE.mkdir(parents=True, exist_ok=True)
    download_plain("https://dot.net/v1/dotnet-install.sh", script)
    script.chmod(0o755)
    subprocess.run(["/bin/bash", str(script), "--channel", "10.0", "--runtime", "dotnet",
                    "--install-dir", str(DOTNET_DIR)], check=True)


def download_plain(url: str, dest: Path) -> None:
    """A small plain-text fetch (no size/hash pin expected) - just the installer script, run
    straight from Microsoft's own dot.net redirector, same as this project's build-box setup."""
    with urllib.request.urlopen(url, timeout=30) as resp, dest.open("wb") as out:
        shutil.copyfileobj(resp, out)


def install_content() -> None:
    free = shutil.disk_usage(HERE).free
    need = needed_bytes()
    if free < need and not PROJECT_DIR.is_dir():
        fail(f"the new client needs about {need / 1024 ** 3:.1f} GB free while it installs; "
             f"{free / 1024 ** 3:.1f} GB is free")
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)

    base_cache = DOWNLOADS / "v0.36c"
    base_cache.mkdir(parents=True, exist_ok=True)
    base_parts = BASE["parts"]
    todo = [p for p in base_parts if not (base_cache / (p["name"] + DONE)).exists()]
    if todo:
        say(f"fetching the base client content (about {sum(p['bytes'] for p in todo) / 1024 ** 3:.1f} GB "
            f"in {len(todo)} part(s); {BASE['unpacked_bytes'] / 1024 ** 3:.0f} GB installed)")
    for i, part in enumerate(base_parts, 1):
        done = base_cache / (part["name"] + DONE)
        if done.exists():
            continue
        zip_path = base_cache / part["name"]
        say(f"  base part {i}/{len(base_parts)}: {part['name']}")
        download(BASE["release_url"] + part["name"], zip_path, part["bytes"], part["sha256"])
        extract_filtered(zip_path, BASE["root_folder"], PROJECT_DIR)
        zip_path.unlink()
        done.touch()

    patch_cache = DOWNLOADS / "v0.37c-patch"
    patch_cache.mkdir(parents=True, exist_ok=True)
    patch_parts = PATCH["parts"]
    patch_json_path = patch_cache / PATCH_JSON
    # A part whose .done marker exists was already downloaded, verified and applied in a previous
    # run - its zip is deleted once applied, so it must never be re-fetched just to re-check for
    # patch.json (the earlier version of this loop did exactly that, wasting ~1.6 GB on every rerun).
    pending = [p for p in patch_parts if not (patch_cache / (p["name"] + DONE)).exists()]
    if pending:
        say(f"fetching the 0.37c client patch (about {sum(p['bytes'] for p in pending) / 1024 ** 3:.1f} GB "
            f"in {len(pending)} part(s))")
        # Download every pending part first (one of them carries patch.json; which one isn't
        # guaranteed), then apply them all against the shared patch.json.
        for i, part in enumerate(pending, 1):
            zip_path = patch_cache / part["name"]
            if not zip_path.is_file():
                say(f"  patch part {i}/{len(pending)}: {part['name']}")
                download(PATCH["release_url"] + part["name"], zip_path, part["bytes"], part["sha256"])
            found = read_patch(zip_path, PATCH["root_folder"])
            if found is not None and not patch_json_path.is_file():
                patch_json_path.write_text(json.dumps(found))
        if not patch_json_path.is_file():
            fail("no patch.json found in any 0.37c client patch part")
        patch = json.loads(patch_json_path.read_text())
        for part in pending:
            zip_path = patch_cache / part["name"]
            apply_patch_part(zip_path, PATCH["root_folder"], PROJECT_DIR, patch)
            zip_path.unlink()
            (patch_cache / (part["name"] + DONE)).touch()
        finish_patch(PROJECT_DIR, patch)
    say(f"new client content installed: {PROJECT_DIR}")


def cmd_install(_args) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    if not CONF_FILE.is_file() and CONF_EXAMPLE.is_file():
        shutil.copy(CONF_EXAMPLE, CONF_FILE)
        say(f"created {CONF_FILE.name} from {CONF_EXAMPLE.name} - edit it with your server's address")
    install_godot()
    ensure_dotnet()
    install_content()
    say("")
    say("Done. Edit client.conf with your server's address, then double-click Play-DAoC.command.")


def read_conf():
    host, custom_class_off, account, password = None, True, "", ""
    if CONF_FILE.is_file():
        for line in CONF_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if key == "SERVER_HOST":
                host = value
            elif key == "CUSTOM_CLASS":
                custom_class_off = value.lower() != "on"
            elif key == "ACCOUNT":
                account = value
            elif key == "PASSWORD":
                password = value
    if not host:
        if not CONF_FILE.is_file() and CONF_EXAMPLE.is_file():
            fail(f"no {CONF_FILE.name} yet; run Setup-Client.command first (it creates one from "
                 f"{CONF_EXAMPLE.name})")
        fail(f"set SERVER_HOST in {CONF_FILE}")
    return host, custom_class_off, account, password


def cmd_play(_args) -> None:
    if not (GODOT_DIR / "Contents" / "MacOS").is_dir():
        fail("Godot is not installed yet; run Setup-Client.command first")
    if not (PROJECT_DIR / "project.godot").is_file():
        fail("the new client is not installed yet; run Setup-Client.command first")
    host, custom_class_off, account, password = read_conf()
    # --server= alone skips the client's own login screen straight to an auto-login attempt
    # (game/login_screen.gd: `if Server.active: _server_login()`, with no field to type into) -
    # account and password must come from the command line, same as the launcher upstream and
    # trozzelle's tool use. client.conf's ACCOUNT/PASSWORD are used if set (plaintext, like the
    # Windows CONNECT TO SERVER.cmd); left blank, they're prompted for fresh each run instead.
    if not account:
        account = input("Account name (letters/numbers only - created on first login): ").strip()
    if not account:
        fail("an account name is required")
    if not password:
        password = getpass.getpass("Password: ")
    if not password:
        fail("a password is required")
    say(f"launching the new client, connecting to {host}:{NEW_PORT} as {account} ...")
    argv = [
        "/usr/bin/open", "-n", str(GODOT_DIR),
        "--env", f"DOTNET_ROOT={DOTNET_DIR}",
        "--args", "--path", str(PROJECT_DIR), "--",
        f"--server={host}", f"--account={account}", f"--password={password}",
    ]
    if custom_class_off:
        argv.append("--custom-class=off")
    subprocess.run(argv, check=True)


def cmd_status(_args) -> None:
    say(f"Godot installed: {(GODOT_DIR / 'Contents' / 'MacOS').is_dir()}")
    say(f"New client installed: {(PROJECT_DIR / 'project.godot').is_file()}")
    if CONF_FILE.is_file():
        host, custom_class_off, account, password = read_conf()
        say(f"client.conf: SERVER_HOST={host} CUSTOM_CLASS={'off' if custom_class_off else 'on'} "
            f"ACCOUNT={account or '(prompted)'} PASSWORD={'(set)' if password else '(prompted)'}")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("install", help="download Godot and the new client's content").set_defaults(func=cmd_install)
    sub.add_parser("play", help="launch the client, connecting to client.conf's SERVER_HOST").set_defaults(func=cmd_play)
    sub.add_parser("status", help="show what is installed").set_defaults(func=cmd_status)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
