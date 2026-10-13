<#
Build and archive a Windows Shipping package with temporary Unreal AES content encryption.
The key is read only from EW_PAK_AES_KEY and is never written to the package or source control.
#>
param(
    [string]$EngineRoot='C:/Program Files/Epic Games/UE_5.8',
    [string]$BuildLabel='',
    [switch]$ValidateOnly
)
$ErrorActionPreference='Stop'
$projectRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$engineConfig=Join-Path $projectRoot 'Config/DefaultEngine.ini'
$cryptoConfig=Join-Path $projectRoot 'Config/DefaultCrypto.ini'
$secret=$env:EW_PAK_AES_KEY
if ([string]::IsNullOrWhiteSpace($secret)) { throw 'Set the repository Actions secret EW_PAK_AES_KEY before publishing a release.' }
try { $keyBytes=[Convert]::FromBase64String($secret) } catch { throw 'EW_PAK_AES_KEY must be Base64-encoded.' }
if ($keyBytes.Length -ne 32) { throw 'EW_PAK_AES_KEY must decode to exactly 32 bytes.' }
if (!(Test-Path -LiteralPath $engineConfig)) { throw 'Project DefaultEngine.ini is missing.' }
if (Test-Path -LiteralPath $cryptoConfig) { throw 'DefaultCrypto.ini already exists; refusing to overwrite a local file.' }
$engineOriginal=[IO.File]::ReadAllBytes($engineConfig)
$engineText=[Text.Encoding]::UTF8.GetString($engineOriginal)
if ($engineText -match '(?im)^\[PlatformCrypto\]') { throw 'DefaultEngine.ini already has a PlatformCrypto section; review it before configuring a release build.' }
$utf8NoBom=New-Object System.Text.UTF8Encoding($false)
$engineAdded=$false
try {
    $updatedEngine=$engineText.TrimEnd()+"`r`n`r`n[PlatformCrypto]`r`nPlatformRequiresDataCrypto=True`r`nPakEncryptionRequired=True`r`n"
    $engineAdded=$true
    [IO.File]::WriteAllText($engineConfig,$updatedEngine,$utf8NoBom)
    $cryptoText=@"
[/Script/CryptoKeys.CryptoKeysSettings]
EncryptionKey=$secret
bEncryptPakIniFiles=True
bEncryptPakIndex=True
bEncryptUAssetFiles=True
bEncryptAllAssetFiles=True
"@
    [IO.File]::WriteAllText($cryptoConfig,$cryptoText,$utf8NoBom)
    if ($ValidateOnly) {
        Write-Output 'Temporary encryption configuration validated; the project configuration will be restored without packaging.'
        return
    }
    if (!$BuildLabel) { $BuildLabel='playtest-'+$env:GITHUB_SHA.Substring(0,12) }
    & (Join-Path $PSScriptRoot 'build_private_windows.ps1') -EngineRoot $EngineRoot -BuildConfiguration Shipping -BuildLabel $BuildLabel -RequireCleanSource -IgnoreTemporaryCryptoConfig -AllowOtherEditorProcess
    $archive=Join-Path $projectRoot ('Saved/PrivateBuilds/'+$BuildLabel)
    $runtimeRoot=Join-Path $archive 'Windows/EW'
    $zipPath=Join-Path $env:RUNNER_TEMP 'Elitewake-Windows-Playtest.zip'
    if (!(Test-Path -LiteralPath (Join-Path $runtimeRoot 'EW.exe'))) { throw 'Shipping executable was not produced.' }
    $metadataPath=Join-Path $runtimeRoot 'PrivateBuildInfo.json'
    $metadata=Get-Content -LiteralPath $metadataPath -Raw | ConvertFrom-Json
    $metadata.contentEncryption='Unreal AES content encryption configured; key held in repository Actions secret; extraction resistance only'
    $metadata | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $metadataPath -Encoding utf8
    # Rebuild the zip so its metadata describes the encryption configuration.
    if (Test-Path -LiteralPath $zipPath) { Remove-Item -LiteralPath $zipPath -Force }
    Compress-Archive -Path (Join-Path $archive '*') -DestinationPath $zipPath -CompressionLevel Fastest
    $zipInfo=Get-Item -LiteralPath $zipPath
    if ($zipInfo.Length -ge 2GB) { throw 'The package exceeds the GitHub Releases 2 GiB per-file limit.' }
    "archive=$archive`nzip=$zipPath`nsize=$($zipInfo.Length)" | Add-Content -LiteralPath $env:GITHUB_OUTPUT
    Write-Output "Encrypted Shipping package is ready for the private playtest release ($([math]::Round($zipInfo.Length/1GB,2)) GiB)."
}
finally {
    if ($engineAdded) { [IO.File]::WriteAllBytes($engineConfig,$engineOriginal) }
    if (Test-Path -LiteralPath $cryptoConfig) { Remove-Item -LiteralPath $cryptoConfig -Force }
    [Array]::Clear($keyBytes,0,$keyBytes.Length)
    $secret=$null
    $env:EW_PAK_AES_KEY=$null
}

