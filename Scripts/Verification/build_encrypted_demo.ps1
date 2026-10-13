<# Build the current local demo once. No GitHub, runner or release setup required. #>
param(
    [string]$EngineRoot='C:/Program Files/Epic Games/UE_5.8',
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$')][string]$BuildLabel=('demo-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
)
$ErrorActionPreference='Stop'
$projectRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$archive=Join-Path $projectRoot ('Saved/PrivateBuilds/'+$BuildLabel)
$buildRoot=Join-Path $projectRoot ('Saved/DemoBuildSource/'+$BuildLabel)
$engineConfig=Join-Path $buildRoot 'Config/DefaultEngine.ini'
$cryptoConfig=Join-Path $buildRoot 'Config/DefaultCrypto.ini'
$runUAT=Join-Path $EngineRoot 'Engine/Build/BatchFiles/RunUAT.bat'
if (Test-Path -LiteralPath $archive) { throw 'Choose a new build label; existing packages are preserved.' }
if (Test-Path -LiteralPath $buildRoot) { throw 'Choose a new label; existing source snapshots are preserved.' }
if (Test-Path -LiteralPath (Join-Path $projectRoot 'Config/DefaultCrypto.ini')) { throw 'Existing crypto settings must be reviewed before creating a new build key.' }
if (!(Test-Path -LiteralPath $runUAT)) { throw 'Unreal Automation Tool is missing.' }
if ((Get-PSDrive C).Free -lt 20GB) { throw 'At least 20 GB free space is required.' }
New-Item -ItemType Directory -Path $buildRoot | Out-Null
Copy-Item -LiteralPath (Join-Path $projectRoot 'EW.uproject') -Destination $buildRoot
foreach ($folder in @('Source','Content','Config','Binaries','Plugins','Build')) {
    $original=Join-Path $projectRoot $folder
    if (!(Test-Path -LiteralPath $original)) { continue }
    & robocopy $original (Join-Path $buildRoot $folder) /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP /XD Intermediate Saved /XF *.pdb *.obj *.ilk *.exp *.lib | Out-Null
    if ($LASTEXITCODE -gt 7) { throw "Could not snapshot $folder." }
}
$manifest=@()
foreach ($file in (Get-ChildItem -LiteralPath $buildRoot -File -Recurse)) {
    $relative=$file.FullName.Substring($buildRoot.Length+1)
    $original=Join-Path $projectRoot $relative
    $snapshotHash=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
    if ((Get-FileHash -LiteralPath $original -Algorithm SHA256).Hash -ne $snapshotHash) { throw "Source changed while copying $relative. Retry with a new label after the edit completes." }
    $manifest+=@{path=$relative;sha256=$snapshotHash;bytes=$file.Length}
}
New-Item -ItemType Directory -Path $archive | Out-Null
@{capturedAtUtc=(Get-Date).ToUniversalTime().ToString('o');files=$manifest} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $archive 'SourceSnapshot.json') -Encoding utf8
Write-Output "Captured isolated demo source ($($manifest.Count) files). Starting Shipping build."
$engineOriginal=[IO.File]::ReadAllBytes($engineConfig)
$engineText=[Text.Encoding]::UTF8.GetString($engineOriginal)
if ($engineText -match '(?im)^\[PlatformCrypto\]') { throw 'An existing PlatformCrypto override must be reviewed first.' }
$utf8NoBom=New-Object Text.UTF8Encoding($false)
$bytes=New-Object byte[] 32
$rng=[Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($bytes)
$rng.Dispose()
$key=[Convert]::ToBase64String($bytes)
$engineChanged=$false
try {
    $engineChanged=$true
    [IO.File]::WriteAllText($engineConfig,$engineText.TrimEnd()+"`r`n`r`n[PlatformCrypto]`r`nPlatformRequiresDataCrypto=True`r`nPakEncryptionRequired=True`r`n",$utf8NoBom)
    [IO.File]::WriteAllText($cryptoConfig,"[/Script/CryptoKeys.CryptoKeysSettings]`r`nEncryptionKey=$key`r`nbEncryptPakIniFiles=True`r`nbEncryptPakIndex=True`r`nbEncryptUAssetFiles=True`r`nbEncryptAllAssetFiles=True`r`n",$utf8NoBom)
    $argsUAT=@('BuildCookRun',"-project=$buildRoot/EW.uproject",'-noP4','-unattended','-platform=Win64','-clientconfig=Shipping',
        '-build','-cook','-stage','-prereqs','-pak','-iostore','-compressed','-nodebuginfo','-package','-archive',"-archivedirectory=$archive",
        '-map=/Game/Elitewake/Maps/Lvl_Title+/Game/ThirdPerson/Lvl_ThirdPerson+/Game/Elitewake/Maps/Lvl_M5PickupTest+/Game/Elitewake/Maps/Lvl_CoastalPlayground',
        "-AdditionalCookerOptions=-CookDir=$buildRoot/Content/Elitewake",'-utf8output','-ubtargs=-NoUBA')
    & $runUAT @argsUAT *> (Join-Path $archive 'Build.log')
    if ($LASTEXITCODE -ne 0) { throw "Unreal packaging failed with exit code $LASTEXITCODE. See $archive/Build.log." }
    $windows=Join-Path $archive 'Windows'
    if (!(Test-Path -LiteralPath (Join-Path $windows 'EW.exe'))) { throw 'The game launcher is missing.' }
    $toc=Join-Path $windows 'EW/Content/Paks/EW-Windows.utoc'
    $stream=[IO.File]::OpenRead($toc)
    try {
        $header=New-Object byte[] 81
        if ($stream.Read($header,0,81) -ne 81) { throw 'The game container header is incomplete.' }
        if ([Text.Encoding]::ASCII.GetString($header,0,16) -ne '-==--==--==--==-') { throw 'Unexpected Unreal container format.' }
        if (($header[80] -band 2) -eq 0) { throw 'The game asset container is not encrypted.' }
    } finally { $stream.Dispose() }
    $cryptoCache=Join-Path $buildRoot 'Saved/Cooked/Windows/EW/Metadata/Crypto.json'
    if (!(Test-Path -LiteralPath $cryptoCache)) { throw 'Generated crypto metadata is missing; verification cannot continue.' }
    $pakTool=Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealPak.exe'
    & $pakTool "$windows/EW/Content/Paks/EW-Windows.pak" '-List' "-CryptoKeys=$cryptoCache" *> (Join-Path $archive 'PakVerification.log')
    if ($LASTEXITCODE -ne 0) { throw 'Encrypted configuration container could not be opened with the build key.' }
    & $pakTool "$windows/EW/Content/Paks/EW-Windows.pak" '-List' *> (Join-Path $archive 'PakWithoutKey.log')
    if ($LASTEXITCODE -eq 0) { throw 'The configuration container index could be read without the build key.' }
    $keyFiles=@(Get-ChildItem -LiteralPath $windows -Recurse -File | Where-Object {$_.Name -in @('Crypto.json','DefaultCrypto.ini')})
    if ($keyFiles.Count) { throw 'Plaintext crypto configuration was staged in the game folder.' }
    & (Join-Path $PSScriptRoot 'verify_private_windows_prerequisites.ps1') -ArchiveDirectory $archive -EngineRoot $EngineRoot
    $revision=(& git -C $projectRoot rev-parse HEAD).Trim()
    @{buildLabel=$BuildLabel;sourceRevision=$revision;configuration='Shipping';localWorkingCopy=$true;assetsEncrypted=$true;
        pakIndexRequiresKey=$true;startupMap='/Game/Elitewake/Maps/Lvl_Title';playableMap='/Game/Elitewake/Maps/Lvl_CoastalPlayground';
        packagedAtUtc=(Get-Date).ToUniversalTime().ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $archive 'DemoBuildInfo.json') -Encoding utf8
    Write-Output "Encrypted demo built and container encryption verified: $windows"
} finally {
    if ($engineChanged) { [IO.File]::WriteAllBytes($engineConfig,$engineOriginal) }
    if (Test-Path -LiteralPath $cryptoConfig) { Remove-Item -LiteralPath $cryptoConfig -Force }
    [Array]::Clear($bytes,0,$bytes.Length)
    $key=$null
}
