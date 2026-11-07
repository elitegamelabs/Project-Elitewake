<# Verify the prerequisite files staged by this installed engine's Win64 UAT.
Read-only except for the archive evidence report. Does not run installers. #>
param(
    [Parameter(Mandatory=$true)][string]$ArchiveDirectory,
    [string]$EngineRoot='C:/Program Files/Epic Games/UE_5.8'
)
$ErrorActionPreference='Stop'
$archive=(Resolve-Path -LiteralPath $ArchiveDirectory).Path
$sourceRoot=Join-Path $EngineRoot 'Engine/Extras/Redist/en-us'
$stagedRoot=Join-Path $archive 'Windows/Engine/Extras/Redist/en-us'
$checks=@()
$failure=$null
try {
    foreach ($name in @('vc_redist.x64.exe','vc_redist.arm64.exe')) {
        $source=Join-Path $sourceRoot $name
        $staged=Join-Path $stagedRoot $name
        if (!(Test-Path -LiteralPath $source -PathType Leaf)) { throw "Engine prerequisite missing: $name" }
        if (!(Test-Path -LiteralPath $staged -PathType Leaf)) { throw "Archived prerequisite missing: $name" }
        $signature=Get-AuthenticodeSignature -LiteralPath $staged
        if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'O=Microsoft Corporation(?:,|$)') {
            throw "Archived prerequisite does not have a valid Microsoft signature: $name ($($signature.Status))"
        }
        $sourceHash=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
        $stagedHash=(Get-FileHash -LiteralPath $staged -Algorithm SHA256).Hash
        if ($sourceHash -ne $stagedHash) { throw "Archived prerequisite differs from this engine's supplied file: $name" }
        $checks+=@{file="Windows/Engine/Extras/Redist/en-us/$name";sha256=$stagedHash;signature='Valid';signer=$signature.SignerCertificate.Subject}
    }
} catch {
    $failure=$_.Exception.Message
}
@{success=($null -eq $failure);scope='Bundled VC runtime presence, Microsoft signatures and exact engine hashes only';
  installersExecuted=$false;cleanPCAccepted=$false;checkedAtUtc=(Get-Date).ToUniversalTime().ToString('o');
  checks=$checks;failure=$failure} | ConvertTo-Json -Depth 5 |
    Set-Content -LiteralPath (Join-Path $archive 'PrerequisitesResult.json') -Encoding utf8
if ($failure) { throw $failure }
Write-Output 'Both archived VC runtime installers have valid Microsoft signatures and match the installed engine.'
