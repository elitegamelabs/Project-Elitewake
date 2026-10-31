<# Publish a multiplayer playtest build of Elitewake to the private playtest repository (owner, October 30: "for each update push the
client exe for multiplayer to that repo so I can add my friends to it and they can download the latest update").

  1. Packages a Windows Development build with Scripts/Verification/build_private_windows.ps1 (title screen, character creator, the
     coastal world; F10 hosts or joins a game over UDP port 7777), unless -ArchiveDirectory names one already built.
  2. Zips the game client only (the Windows folder: EW.exe and the files it runs from). The playtest repository holds nothing but the
     client and a README on putting it together (owner, October 30): no source code, no debug symbols (*.pdb), no build reports,
     manifests or launch scripts. A zip over GitHub's 2 GB asset limit is split into numbered parts with Combine-parts.bat beside them.
  3. Creates a release on the playtest repository (private), tagged with the build label, with a one-line note, and deletes the older
     releases (and their tags): only the newest client is there.
  4. Writes the repository's README.md (its only file): download, combine the parts, unzip, run, host and join.

Needs: gh signed in with access to the repository; Unreal Editor and EW closed while packaging; 15 GB free.
    powershell -NoProfile -File Scripts/Release/publish_playtest.ps1
    powershell -NoProfile -File Scripts/Release/publish_playtest.ps1 -ArchiveDirectory Saved/PrivateBuilds/local-20261030-230000 #>
param(
    [string]$Repo = 'elitegamelabs/Elitewake-Playtest',
    [string]$ArchiveDirectory = '',
    [string]$EngineRoot = 'C:/Program Files/Epic Games/UE_5.8'
)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path

if (-not $ArchiveDirectory) {
    $output = & (Join-Path $projectRoot 'Scripts/Verification/build_private_windows.ps1') -EngineRoot $EngineRoot
    $line = @($output | Where-Object { "$_" -like 'Local package created: *' })[-1]
    if (-not $line) { throw 'Packaging did not report its archive; nothing was published.' }
    $ArchiveDirectory = "$line".Substring('Local package created: '.Length).Trim()
}
$archive = (Resolve-Path $ArchiveDirectory).Path
if (!(Test-Path -LiteralPath (Join-Path $archive 'Windows/EW/Binaries/Win64/EW.exe'))) { throw "No packaged game in $archive." }
$info = Get-Content -LiteralPath (Join-Path $archive 'PrivateBuildInfo.json') -Raw | ConvertFrom-Json
$label = $info.label
$revision = $info.sourceRevision

$outDir = Join-Path $projectRoot "Saved/PlaytestReleases/$label"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
# The playtest repository's README (its only file).
$readme = Join-Path $outDir 'README.md'
@"
# Elitewake playtest

Private test builds of Elitewake for invited friends (Windows). Not a release: placeholder art, sounds and balance; things will break.
Please do not share the files outside the invited group.

Current build: **$label**

## Put it together
1. Open **Releases** (right side of this page), pick the one marked **Latest**, and under *Assets* download the
   ``Elitewake-Playtest-...zip`` file, or, if it comes in numbered parts (``.zip.001``, ``.zip.002``...), every part and
   **Combine-parts.bat**. Ignore the two "Source code" links: GitHub adds them to every release and they hold only this README.
2. Parts only: put the parts and Combine-parts.bat in one folder and double-click **Combine-parts.bat** (or open the .001 part with
   7-Zip). It makes the zip.
3. Right-click the zip, **Extract All**, into a folder of its own. Keep everything inside the ``Windows`` folder together.
4. Run ``Windows\EW.exe``. Windows may warn that the program is unsigned: More info, Run anyway. If it says a runtime is missing, run
   ``Windows\Engine\Extras\Redist\en-us\vc_redist.x64.exe`` once.

A new build replaces the old one: delete the old folder and repeat these steps.

## Play together
Everyone needs the **same build** (the label above; F10 shows it in game).

**The host** (the one whose world everybody joins):
1. On the router, forward **UDP port 7777** to the host PC's local IP address. (TCP is not needed.)
2. The first time the game runs, allow EW through Windows Firewall when asked (private and public networks), or add an inbound UDP 7777 rule.
3. Start the game, get into the world, press **F10**, then **Host Game**. The world reloads and waits for friends.
4. Tell friends your public IP address (search "what is my IP"), or a dynamic-DNS host name if you use one.

**A friend joining**:
1. Start the game and get into the world.
2. Press **F10**, type the host's public IP (for example ``203.0.113.25`` or ``203.0.113.25:7777``) in the box, then **Join Game**.
3. **Leave / Cancel** in the same menu goes back to playing alone.

On the same home network use the host's LAN address (like ``192.168.1.20``) instead; on the same PC, ``127.0.0.1``.
The host keeps each player's survivor (pack, purse, where they stood) and gives it back when they join again from the same PC.
A ship belongs to whoever bought her or first took her helm; only they can sail her. To share ships: press I, Tab to **Company**,
create one, invite your friends from **Invitations** (they accept there with Enter), then **Change who may sail** to Personal Shared
or Company. Companies last until the host closes the game.
When the host leaves, everyone is disconnected.

## Controls
WASD move, Space jump, Left Shift sprint, C crouch/prone, E interact (press to talk, hold for fittings and the anchor), Left Mouse attack,
1-8 hotbar, I inventory and journal, M map, F10 host/join. At a cannon: mouse aims, Left Mouse fires, Right Mouse marks a target.
Testing keys: Shift+1..5 jump to a region, Shift+6 to the nearest Port (Saltreach Freeport is the starting hub), F9 opens the item
spawner (one item per click or A). Escape opens the pause menu: Resume, Options (brightness, mouse and controller look speeds, volume), Main Menu.
"@ | Set-Content -LiteralPath $readme -Encoding utf8

# Zip the client (bsdtar writes zip); split it if it is over GitHub's per-file limit.
$zip = Join-Path $outDir "Elitewake-Playtest-$label.zip"
if (Test-Path -LiteralPath $zip) { throw "$zip already exists; publish a new build instead of overwriting one." }
# Windows' own tar (bsdtar, which writes zip), not a Unix tar that may come first on the PATH.
# The client only (the Windows folder; the build's reports and launch script beside it stay out): no debug symbols, manifests or
# engine debug tools (owner: nothing but the client in the playtest repository). NOTICES.txt stays: a third-party licence notice.
$exclude = @('*.pdb', 'Manifest_*.txt', 'GPUDumpViewer')
$excludeArgs = @($exclude | ForEach-Object { '--exclude'; $_ })
& (Join-Path $env:SystemRoot 'System32/tar.exe') -a -c -f $zip @excludeArgs -C $archive Windows
if ($LASTEXITCODE -ne 0) { throw 'Zipping the build failed; nothing was published.' }
$limit = 1900MB
$assets = @()
if ((Get-Item -LiteralPath $zip).Length -le $limit) { $assets = @($zip) }
else {
    $stream = [IO.File]::OpenRead($zip)
    try {
        $buffer = New-Object byte[] (64MB)
        $part = 0
        while ($stream.Position -lt $stream.Length) {
            $part++
            $name = '{0}.{1:D3}' -f $zip, $part
            $out = [IO.File]::Create($name)
            try {
                $written = 0
                while ($written -lt $limit -and ($read = $stream.Read($buffer, 0, [Math]::Min($buffer.Length, $limit - $written))) -gt 0) {
                    $out.Write($buffer, 0, $read); $written += $read
                }
            } finally { $out.Dispose() }
            $assets += $name
        }
    } finally { $stream.Dispose() }
    Remove-Item -LiteralPath $zip
    # A one-click way to put the parts back together, for anyone without 7-Zip.
    $leaf = Split-Path -Leaf $zip
    $joined = ($assets | ForEach-Object { '"' + (Split-Path -Leaf $_) + '"' }) -join '+'
    $combine = Join-Path $outDir 'Combine-parts.bat'
    Set-Content -LiteralPath $combine -Encoding ascii -Value @"
@echo off
rem Puts the downloaded parts back into one zip (keep this file beside them), then unzip $leaf.
cd /d "%~dp0"
copy /b $joined "$leaf"
echo.
echo Done: $leaf - now right-click it, Extract All.
pause
"@
    $assets += $combine
}

# A one-line note: no commit list, no code references (owner, October 30).
& gh release create $label @assets --repo $Repo --title "Playtest $label" --notes "Windows client. How to put it together: the README on the repository's front page." --latest
if ($LASTEXITCODE -ne 0) { throw 'Creating the GitHub release failed.' }

# Only the newest client stays: older releases and their tags go.
$older = @(& gh release list --repo $Repo --limit 100 --json tagName --jq '.[].tagName' | Where-Object { $_ -and $_ -ne $label })
foreach ($tag in $older) {
    & gh release delete $tag --repo $Repo --cleanup-tag --yes
    if ($LASTEXITCODE -ne 0) { Write-Warning "Could not delete the older release $tag." }
}

# The README is the repository's only file; replace it (or add it) on the default branch.
$current = $null
try { $current = & gh api "repos/$Repo/contents/README.md" --jq '.sha' 2>$null } catch { }
$body = @{ message = "Playtest README for $label"; content = [Convert]::ToBase64String([IO.File]::ReadAllBytes($readme)) }
if ($current) { $body.sha = "$current".Trim() }
$bodyFile = Join-Path $outDir 'readme-request.json'
$body | ConvertTo-Json | Set-Content -LiteralPath $bodyFile -Encoding ascii
& gh api -X PUT "repos/$Repo/contents/README.md" --input $bodyFile --silent
if ($LASTEXITCODE -ne 0) { throw 'Updating the playtest README failed (the release is published).' }
Write-Output "Published $label to $Repo ($($assets.Count) file(s))"
