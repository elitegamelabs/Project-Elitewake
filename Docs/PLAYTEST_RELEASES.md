# Multiplayer playtest releases (owner, October 30, 2026)

The owner's friends test Elitewake over the Internet from a private repository: **https://github.com/elitegamelabs/Elitewake-Playtest**
(private; the owner invites friends as collaborators in its Settings > Collaborators). Each update is published there as a release; the
newest is marked **Latest**.

## Publishing (after each pushed update)
Close Unreal Editor and any running game, then:

    powershell -NoProfile -ExecutionPolicy Bypass -File Scripts/Release/publish_playtest.ps1

It packages a Windows Development build (`Scripts/Verification/build_private_windows.ps1`: title screen, character creator, the coastal
world), zips its `Windows` folder (split into 1.9 GB parts with Combine-parts.bat if larger, for GitHub's 2 GB file limit), creates a
release tagged with the build label, deletes the older releases and their tags, and rewrites the repository's README.md.
`-ArchiveDirectory <folder>` publishes an existing package without rebuilding.

**Nothing but the client and a README** (owner, October 30: "i don't want anything in the second, test, repo except the client exe's
and a readme on how to put them together"):
- The repository's only file is README.md: download, combine the parts, unzip, run, host and join, controls.
- The only release is the newest client: `EW.exe` and the files it runs from, without debug symbols (`*.pdb`), manifests, engine debug
  tools, build reports or launch scripts. `NOTICES.txt` (the FreeType licence notice) stays with the engine files.
- Release notes are one line; Issues, Projects and Wiki are off.
- GitHub adds "Source code (zip / tar.gz)" links to every release and they cannot be removed; they hold the README only, never game code.

## Playing together
- **Host:** forward **UDP 7777** on the router to the host PC, allow EW through Windows Firewall, then in game **F10 > Host Game**.
- **Friends:** **F10**, type the host's public IP (or a dynamic-DNS host name), **Join Game**. Same build label required (F10 shows it).
- The Join box accepts 127.0.0.1, LAN addresses, public IPv4 addresses and host names, with an optional port (default 7777); never a
  URL, option or path (`Elitewake.Multiplayer.PrivateAddress` test).

## Checked
- October 30: the packaged build hosts a listen server on UDP 7777 and a second copy on the same PC joins it ("Join succeeded", the client
  loads the coastal world from the host).

## Not done (M8)
- Multiplayer is not on the main menu yet (it says Coming Soon); hosting and joining are on F10, a test panel.
- A game across the Internet has not been verified by a check; only listen server and client on one PC are Play-checked.
- The host keeps each player's survivor (October 30): saved when they leave and every minute, given back when they rejoin (keyed by a
  stable id their game sends with Join; `verify_server_survivor_multiplayer_play`, and a standalone leave-and-rejoin). When the host
  leaves everyone is disconnected; there is no server browser, password or kick.
- The build is unsigned (Windows SmartScreen warns) and a Development build (testing keys such as Shift+1..6 work).
