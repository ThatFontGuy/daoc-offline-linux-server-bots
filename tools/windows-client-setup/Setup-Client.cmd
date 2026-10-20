@echo off
rem Downloads the official Offline DAoC client and sets up a one-click connector for a server you
rem choose. This file contains no game data itself - it runs setup-client.ps1, which downloads
rem the real installer fresh from shadowofze/OfflineDAoC (not hosted by this project) each time.
rem See GETTING-STARTED.md in this project for the full walkthrough.
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-client.ps1" %*
pause
