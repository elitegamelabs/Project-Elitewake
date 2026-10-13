<# Build a Windows package with the title screen, retained test maps and coastal playground, plus
a launcher that starts at the title screen for single-player testing. Development is the local diagnostic default;
Shipping is used by the private release workflow.
Bundles engine-provided prerequisite installers without running them.
No upload, account, firewall, router or tester invitation operations. #>
param(
    [string]$EngineRoot='C:/Program Files/Epic Games/UE_5.8',
    [ValidateSet('Development','Shipping')][string]$BuildConfiguration='Development',
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$')][string]$BuildLabel='',
    [switch]$RequireCleanSource,
    [switch]$IgnoreTemporaryCryptoConfig,
    [switch]$AllowOtherEditorProcess
)
$ErrorActionPreference='Stop'
$projectRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$project=Join-Path $projectRoot 'EW.uproject'
$runUAT=Join-Path $EngineRoot 'Engine/Build/BatchFiles/RunUAT.bat'
if (!(Test-Path $runUAT)) { throw 'Configured Unreal Automation Tool is missing.' }
if (!$AllowOtherEditorProcess -and (Get-Process -Name UnrealEditor,EW -ErrorAction SilentlyContinue)) { throw 'Close Unreal Editor and EW test games before packaging to avoid Live Coding/build conflicts.' }
if ((Get-PSDrive -Name ([IO.Path]::GetPathRoot($projectRoot).Substring(0,1))).Free -lt 15GB) { throw 'At least 15 GB free space is required for this diagnostic build.' }
if (!$BuildLabel) { $BuildLabel='local-'+(Get-Date -Format 'yyyyMMdd-HHmmss') }
$archive=Join-Path $projectRoot ('Saved/PrivateBuilds/'+$BuildLabel)
if (Test-Path $archive) { throw 'Build output already exists; do not overwrite a previous package.' }
$revision=(& git -C $projectRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot record source revision.' }
$statusLines=@(& git -C $projectRoot status --porcelain)
$unexpectedStatusLines=$statusLines
if ($IgnoreTemporaryCryptoConfig) {
    $allowedTemporaryPaths=@('Config/DefaultEngine.ini','Config/DefaultCrypto.ini')
    $unexpectedStatusLines=@($statusLines | Where-Object {
        $path=$_.Substring(3).Trim('"') -replace '\\','/'
        $path -notin $allowedTemporaryPaths
    })
}
$dirty=$unexpectedStatusLines.Count -gt 0
if ($RequireCleanSource -and $dirty) { throw 'Release packaging requires a clean checkout.' }
$arguments=@('BuildCookRun',"-project=$project",'-noP4','-unattended','-platform=Win64',"-clientconfig=$BuildConfiguration",
    '-build','-cook','-stage','-prereqs','-pak','-iostore','-package','-archive',"-archivedirectory=$archive",
    '-map=/Game/Elitewake/Maps/Lvl_Title+/Game/ThirdPerson/Lvl_ThirdPerson+/Game/Elitewake/Maps/Lvl_M5PickupTest+/Game/Elitewake/Maps/Lvl_CoastalPlayground',
    "-AdditionalCookerOptions=-CookDir=$projectRoot/Content/Elitewake",
    '-utf8output','-stdout','-FullStdOutLogOutput')
& $runUAT @arguments
if ($LASTEXITCODE -ne 0) { throw "Unreal Automation Tool failed with exit code $LASTEXITCODE." }
$requiredAssets=@(
    'Windows/EW/Content/Paks',
    'Windows/EW/Content/IoStore'
)
$missingAssets=@($requiredAssets | Where-Object { !(Test-Path -LiteralPath (Join-Path $archive $_)) })
if ($missingAssets.Count) { throw "Required packaged data is absent: $($missingAssets -join ', ')" }
$runtimeRoot=Join-Path $archive 'Windows/EW'
if (!(Test-Path -LiteralPath (Join-Path $runtimeRoot 'Binaries/Win64/EW.exe'))) { throw 'Packaged runtime executable is missing.' }
& (Join-Path $PSScriptRoot 'verify_private_windows_prerequisites.ps1') -ArchiveDirectory $archive -EngineRoot $EngineRoot
$displayLabel="$BuildLabel | $($revision.Substring(0,12)) | $BuildConfiguration"
if ($dirty) { $displayLabel+=' | local changes' }
Set-Content -LiteralPath (Join-Path $runtimeRoot 'PrivateBuildLabel.txt') -Value $displayLabel -Encoding utf8
@{label=$BuildLabel;sourceRevision=$revision;sourceHasLocalChanges=$dirty;configuration=$BuildConfiguration;platform='Win64';
  releaseChannel=$(if ($BuildConfiguration -eq 'Shipping') { 'private GitHub rolling prerelease' } else { 'local diagnostic package' });
  maps=@('/Game/Elitewake/Maps/Lvl_Title','/Game/ThirdPerson/Lvl_ThirdPerson','/Game/Elitewake/Maps/Lvl_M5PickupTest','/Game/Elitewake/Maps/Lvl_CoastalPlayground');
  prerequisites='Engine-provided signed VC runtime installers bundled and hash-checked; not installed or clean-PC verified';
  scope='Local diagnostic package; original editor settings and source documents preserved; no LAN/Internet/distribution acceptance'} |
  ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $runtimeRoot 'PrivateBuildInfo.json') -Encoding utf8
@'
# Private Windows playtest

Single-player testing: double-click Play Elitewake.bat. It opens the title screen: click START YOUR JOURNEY, make your survivor (body, colouring, height; drag to turn them), then SET SAIL for the coastal playground: the island and islet, ocean, swimming and sea creatures, the dock, and the raft, dinghy and sloop, with a test starter kit (tools on you, each ship's helm and sails in its own hold). F10 in the game hosts or joins a session.

Ships: raft, dinghy and sloop. Swim to a ship, press E at a side ladder and climb; use the helm to steer and the sail to move. The coastal map has deep-water distance and an island islet. The starter kit is a test fixture, not the production prologue.

Latest: title screen and character creator; ladders climbed with the arrows; ship labels; ATLAS-style sail trim and a compass; sea creatures to fight and harvest (sharks, mantas and squid attack swimmers); tools held in the hand with a chop.
Known issues: survivors are stand-in mannequins until the real characters arrive; freshwater fish wait for ponds; cannons are stand-in boxes; session progress is not saved; production prologue and starter recipe unlocks unresolved. Final animations, art and balance remain unfinished.
Coverage: this folder is not a certified release. Consult Docs/VERIFICATION.md for acceptance of this exact label. Rendered gameplay, clean PC, two-PC LAN, Internet, Shipping and distribution require separate checks.
Keep the entire Windows folder together. F10 shows the build label; matching labels alone do not enforce network compatibility.

Windows prerequisites: signed Microsoft VC runtime installers are bundled in Windows/Engine/Extras/Redist/en-us. On an x64 tester PC, run vc_redist.x64.exe interactively if the runtime is missing, then launch Windows/EW.exe. The engine also stages vc_redist.arm64.exe for ARM64 emulation; this does not certify native ARM64 support. PrerequisitesResult.json records signatures and matching engine/package hashes, not installation success or clean-PC portability. These installers have not been run by the build script. GameInput redistribution is not opted in by this project; physical controller support remains unverified.
'@ | Set-Content -LiteralPath (Join-Path $archive 'TEST_NOTES.md') -Encoding utf8
Set-Content -LiteralPath (Join-Path $archive 'Play Elitewake.bat') -Encoding ascii -Value @'
@echo off
start "" "%~dp0WindowsEW.exe" /Game/Elitewake/Maps/Lvl_Title
'@
Write-Output "Windows package created: $archive"
