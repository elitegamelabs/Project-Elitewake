<# Build a local Development package with the title screen, the retained test maps and the coastal playground, plus
a launcher that starts at the title screen for single-player testing.
Bundles engine-provided prerequisite installers without running them.
No upload, account, firewall, router or tester invitation operations. #>
param([string]$EngineRoot='C:/Program Files/Epic Games/UE_5.8')
$ErrorActionPreference='Stop'
$projectRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$project=Join-Path $projectRoot 'EW.uproject'
$runUAT=Join-Path $EngineRoot 'Engine/Build/BatchFiles/RunUAT.bat'
if (!(Test-Path $runUAT)) { throw 'Configured Unreal Automation Tool is missing.' }
if (Get-Process -Name UnrealEditor,EW -ErrorAction SilentlyContinue) { throw 'Close Unreal Editor and EW test games before packaging to avoid Live Coding/build conflicts.' }
if ((Get-PSDrive -Name ([IO.Path]::GetPathRoot($projectRoot).Substring(0,1))).Free -lt 15GB) { throw 'At least 15 GB free space is required for this diagnostic build.' }
$buildLabel='local-'+(Get-Date -Format 'yyyyMMdd-HHmmss')
$archive=Join-Path $projectRoot ('Saved/PrivateBuilds/'+$buildLabel)
if (Test-Path $archive) { throw 'Build output already exists; do not overwrite a previous package.' }
$revision=(& git -C $projectRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot record source revision.' }
$dirty=[bool](& git -C $projectRoot status --porcelain)
$arguments=@('BuildCookRun',"-project=$project",'-noP4','-unattended','-platform=Win64','-clientconfig=Development',
    '-build','-cook','-stage','-prereqs','-pak','-iostore','-package','-archive',"-archivedirectory=$archive",
    '-map=/Game/Elitewake/Maps/Lvl_Title+/Game/ThirdPerson/Lvl_ThirdPerson+/Game/Elitewake/Maps/Lvl_M5PickupTest+/Game/Elitewake/Maps/Lvl_CoastalPlayground',
    "-AdditionalCookerOptions=-CookDir=$projectRoot/Content/Elitewake",
    '-utf8output','-ubtargs=-NoUBA')
& $runUAT @arguments
if ($LASTEXITCODE -ne 0) { throw "Private package failed with exit code $LASTEXITCODE. Inspect Unreal's packaging log; no upload occurred." }
$registryPath=Join-Path $projectRoot 'Saved/Cooked/Windows/EW/AssetRegistry.bin'
$registryText=[Text.Encoding]::UTF8.GetString([IO.File]::ReadAllBytes($registryPath))
$requiredAssets=@('T_Axe_v1','T_Shovel_v1','T_Pickaxe_v1','T_Flask_v1','T_Torch_v1',
    'DA_TestWoodenAxe','DA_TestWoodenShovel','DA_TestWoodenPickaxe','DA_TestHideWaterFlask','DA_TestInnTorch',
    'DA_RecipeWoodenAxe','DA_RecipeWoodenShovel','DA_RecipeWoodenPickaxe','DA_RecipeHideWaterFlask',
    'DA_TestRepairKit','DA_RecipePrologueRepairKit')
$missingAssets=@($requiredAssets | Where-Object { !$registryText.Contains($_) })
if ($missingAssets.Count) { throw "Diagnostic assets absent from cooked registry: $($missingAssets -join ', '). Do not use this archive as starter-content acceptance." }
$containerCsv=Join-Path $archive 'StarterContainerListing.csv'
& (Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealPak.exe') $project IoStore "-List=$archive/Windows/EW/Content/Paks/EW-Windows.utoc" "-Csv=$containerCsv"
if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect archived diagnostic container.' }
$containerText=[IO.File]::ReadAllText($containerCsv)
$missingAssets=@($requiredAssets | Where-Object { !$containerText.Contains('/'+$_+'.uasset,') })
if ($missingAssets.Count) { throw "Diagnostic assets absent from archived container: $($missingAssets -join ', ')." }
@{success=$true;scope='Cooked registry and archived container presence only; not gameplay or rendering acceptance';assets=$requiredAssets} |
    ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $archive 'CookedStarterContentResult.json') -Encoding utf8
$runtimeRoot=Join-Path $archive 'Windows/EW'
if (!(Test-Path -LiteralPath (Join-Path $runtimeRoot 'Binaries/Win64/EW.exe'))) { throw 'Packaged runtime executable is missing.' }
& (Join-Path $PSScriptRoot 'verify_private_windows_prerequisites.ps1') -ArchiveDirectory $archive -EngineRoot $EngineRoot
$displayLabel="$buildLabel | $($revision.Substring(0,12)) | Development"
if ($dirty) { $displayLabel+=' | local changes' }
Set-Content -LiteralPath (Join-Path $runtimeRoot 'PrivateBuildLabel.txt') -Value $displayLabel -Encoding utf8
@{label=$buildLabel;sourceRevision=$revision;sourceHasLocalChanges=$dirty;configuration='Development';platform='Win64';released=$false;
  maps=@('/Game/Elitewake/Maps/Lvl_Title','/Game/ThirdPerson/Lvl_ThirdPerson','/Game/Elitewake/Maps/Lvl_M5PickupTest','/Game/Elitewake/Maps/Lvl_CoastalPlayground');
  prerequisites='Engine-provided signed VC runtime installers bundled and hash-checked; not installed or clean-PC verified';
  scope='Local diagnostic package; original editor settings and source documents preserved; no LAN/Internet/distribution acceptance'} |
  ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $archive 'PrivateBuildInfo.json') -Encoding utf8
@'
# Local private test — unreleased

Single-player testing: double-click Play Elitewake.bat. It opens the title screen: click START YOUR JOURNEY, make your survivor (body, colouring, height; drag to turn them), then SET SAIL for the coastal playground: the island and islet, ocean, swimming and sea creatures, the dock, and the raft, dinghy and sloop, with a test starter kit (tools on you, each ship's helm and sails in its own hold). F10 in the game hosts or joins a session.

Controls: WASD move, Space jump, Left Shift sprint, tap C crouch / hold C prone, Z first or third person, E interact (hold for fittings and the anchor), Left Mouse attack or chop with the tool in hand, 1-8 hotbar, I inventory, crafting and Journal, M map, F10 host/join.
Ships: raft, dinghy and sloop. Swim to a ship, press E at a side ladder and climb with the Up and Down arrows. Labels on screen mark each ship's ladders, mounts, anchor and hold. Each ship's helm and sails are in its own hold (hold E at the hatch). Fit them by looking at a mount and holding E, raise the anchor at the capstan, take the helm, then W/S set sail, A/D steer and Shift+A/D trim the sails to the wind shown on the compass. The Journal (I, then JOURNAL) has a guide to each.
Latest: title screen and character creator; ladders climbed with the arrows; ship labels; ATLAS-style sail trim and a compass; sea creatures to fight and harvest (sharks, mantas and squid attack swimmers); tools held in the hand with a chop.
Known issues: survivors are stand-in mannequins until the real characters arrive; freshwater fish wait for ponds; cannons are stand-in boxes; session progress is not saved; production prologue and starter recipe unlocks unresolved. Final animations, art and balance remain unfinished.
Coverage: this folder is not a certified release. Consult Docs/VERIFICATION.md for acceptance of this exact label. Rendered gameplay, clean PC, two-PC LAN, Internet, Shipping and distribution require separate checks.
Keep the entire Windows folder together. F10 shows the diagnostic build label; matching labels alone do not enforce network compatibility.

Windows prerequisites: signed Microsoft VC runtime installers are bundled in Windows/Engine/Extras/Redist/en-us. On an x64 tester PC, run vc_redist.x64.exe interactively if the runtime is missing, then launch Windows/EW.exe. The engine also stages vc_redist.arm64.exe for ARM64 emulation; this does not certify native ARM64 support. These installers have not been run by the build script. PrerequisitesResult.json records signatures and matching engine/package hashes, not installation success or clean-PC portability. GameInput redistribution is not opted in by this project; physical controller support remains unverified.
'@ | Set-Content -LiteralPath (Join-Path $archive 'TEST_NOTES.md') -Encoding utf8
# Single-player testing starts on the title screen, which leads through the character creator to the coast.
Set-Content -LiteralPath (Join-Path $archive 'Play Elitewake.bat') -Encoding ascii -Value @'
@echo off
start "" "%~dp0Windows\EW.exe" /Game/Elitewake/Maps/Lvl_Title
'@
Write-Output "Local package created: $archive"
