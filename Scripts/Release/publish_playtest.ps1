<# Publish a multiplayer playtest build of Elitewake to the private playtest repository (owner, October 30: "for each update push the
client exe for multiplayer to that repo so I can add my friends to it and they can download the latest update").

  1. Packages a Windows Development build with Scripts/Verification/build_private_windows.ps1 (title screen, character creator, the
     coastal world; F10 hosts or joins a game over UDP port 7777), unless -ArchiveDirectory names one already built.
  2. Adds PLAYTEST_README.md (install, host, join, router port) to the build.
  3. Zips the game only: no source code ever goes to the playtest repository (owner, October 30), and the zip leaves out the debug
     symbols (*.pdb) and the build's internal reports (asset listings, build info, test notes). A zip over GitHub's 2 GB asset limit is
     split into numbered parts with Combine-parts.bat beside them.
  4. Creates a release on the playtest repository (private), tagged with the build label, with plain notes (no commits, no code
     references). The newest release is marked latest, so friends always download from the top.

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

@"
# Elitewake playtest — $label

Private test build for friends of the developer. Not a release: placeholder art, sounds and balance; things will break.

## Install
1. Download every file of this release. If it comes in numbered parts (.001, .002...), put them in one folder and double-click
   **Combine-parts.bat** (or open the .001 part with 7-Zip) to get the zip.
2. Unzip into a folder of its own (keep everything together).
3. If Windows says a runtime is missing, run ``Windows\Engine\Extras\Redist\en-us\vc_redist.x64.exe`` once.
4. Start the game with **Play Elitewake.bat** (or ``Windows\EW.exe``). Windows may warn that the program is unsigned: More info, Run anyway.

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
Progress in a hosted game is not saved yet. When the host leaves, everyone is disconnected.

## Controls
WASD move, Space jump, Left Shift sprint, C crouch/prone, E interact (press to talk, hold for fittings and the anchor), Left Mouse attack,
1-8 hotbar, I inventory and journal, M map, F10 host/join. At a cannon: mouse aims, Left Mouse fires, Right Mouse marks a target.
Testing keys: Shift+1..5 jump to a region, Shift+6 to the nearest Port (Saltreach Freeport is the starting hub).
"@ | Set-Content -LiteralPath (Join-Path $archive 'PLAYTEST_README.md') -Encoding utf8

# Zip the whole build (bsdtar writes zip); split it if it is over GitHub's per-file limit.
$outDir = Join-Path $projectRoot "Saved/PlaytestReleases/$label"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$zip = Join-Path $outDir "Elitewake-Playtest-$label.zip"
if (Test-Path -LiteralPath $zip) { throw "$zip already exists; publish a new build instead of overwriting one." }
# Windows' own tar (bsdtar, which writes zip), not a Unix tar that may come first on the PATH.
# The game only: no debug symbols, no internal build reports (owner: no source code or code details in the playtest repository).
$exclude = @('*.pdb', 'StarterContainerListing.csv', 'CookedStarterContentResult.json', 'PrivateBuildInfo.json', 'PrerequisitesResult.json', 'TEST_NOTES.md')
$excludeArgs = @($exclude | ForEach-Object { '--exclude'; $_ })
& (Join-Path $env:SystemRoot 'System32/tar.exe') -a -c -f $zip @excludeArgs -C $archive .
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

# Plain notes: no commit list, no code references (owner, October 30).
$notesFile = Join-Path $outDir 'notes.md'
@"
Playtest build **$label** (Windows). Download every file, combine the parts if there are several (Combine-parts.bat), unzip, and read
PLAYTEST_README.md inside: install, hosting (forward UDP 7777) and joining (F10, Join Game with the host's address).

Everyone in a game needs this same build. This release replaces the earlier ones.
"@ | Set-Content -LiteralPath $notesFile -Encoding utf8

& gh release create $label @assets --repo $Repo --title "Playtest $label" --notes-file $notesFile --latest
if ($LASTEXITCODE -ne 0) { throw 'Creating the GitHub release failed.' }
Write-Output "Published $label to $Repo ($($assets.Count) file(s))"
