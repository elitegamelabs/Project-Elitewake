<# Build a local Development package with the two retained test maps.
No upload, account, installer, firewall, router or tester invitation operations. #>
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
    '-build','-cook','-stage','-pak','-iostore','-package','-archive',"-archivedirectory=$archive",
    '-map=/Game/ThirdPerson/Lvl_ThirdPerson+/Game/Elitewake/Maps/Lvl_M5PickupTest','-utf8output','-ubtargs=-NoUBA')
& $runUAT @arguments
if ($LASTEXITCODE -ne 0) { throw "Private package failed with exit code $LASTEXITCODE. Inspect Unreal's packaging log; no upload occurred." }
$runtimeRoot=Join-Path $archive 'Windows/EW'
if (!(Test-Path -LiteralPath (Join-Path $runtimeRoot 'Binaries/Win64/EW.exe'))) { throw 'Packaged runtime executable is missing.' }
$displayLabel="$buildLabel | $($revision.Substring(0,12)) | Development"
if ($dirty) { $displayLabel+=' | local changes' }
Set-Content -LiteralPath (Join-Path $runtimeRoot 'PrivateBuildLabel.txt') -Value $displayLabel -Encoding utf8
@{label=$buildLabel;sourceRevision=$revision;sourceHasLocalChanges=$dirty;configuration='Development';platform='Win64';released=$false;
  maps=@('/Game/ThirdPerson/Lvl_ThirdPerson','/Game/Elitewake/Maps/Lvl_M5PickupTest');
  scope='Local diagnostic package; original editor settings and source documents preserved; no LAN/Internet/distribution acceptance'} |
  ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $archive 'PrivateBuildInfo.json') -Encoding utf8
@'
# Local private test — unreleased

Added: inventory/crafting grids, M-key surrounding map preview, F10 Host/Join/Leave and visible build label.
Fixed: packaged startup GameFeatureData ensure; editor connector excluded from runtime targets.
Known issues: session progress is not saved; inventory privacy decision pending; production prologue and starter unlock trigger unresolved. Final animations/art/balance remain unfinished.
Coverage: this folder is not a certified release. Consult Docs/VERIFICATION.md for acceptance of this exact label. Rendered gameplay, prerequisites/clean PC, two-PC LAN, Internet, Shipping and distribution require separate checks.
Keep the entire Windows folder together. F10 shows the diagnostic build label; matching labels alone do not enforce network compatibility.
'@ | Set-Content -LiteralPath (Join-Path $archive 'TEST_NOTES.md') -Encoding utf8
Write-Output "Local package created: $archive"
