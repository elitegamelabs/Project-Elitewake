<# Capture actual rendered packaged startup frames, including UI, at several sizes.
No desktop input, networking, fixture grants or editor setting changes. Human visual
inspection is required; screenshot generation alone is not visual acceptance. #>
param([Parameter(Mandatory=$true)][string]$PackagedExecutable,
    [ValidateSet('Standard','AspectRatios')][string]$CaptureSet='Standard')
$ErrorActionPreference='Stop'
$projectRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$runtimeExe=(Resolve-Path -LiteralPath $PackagedExecutable).Path
$runtimeRoot=[IO.Path]::GetFullPath((Join-Path (Split-Path $runtimeExe -Parent) '../..'))
if (!(Test-Path -LiteralPath (Join-Path $runtimeRoot 'PrivateBuildLabel.txt'))) { throw 'Choose a labelled diagnostic package runtime executable.' }
$label=(Get-Content -LiteralPath (Join-Path $runtimeRoot 'PrivateBuildLabel.txt') -Raw).Trim()
$evidenceRoot=Join-Path $projectRoot ('Saved/RenderedStartup/'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
if (Test-Path -LiteralPath $evidenceRoot) { throw 'Evidence folder already exists; do not overwrite a run.' }
New-Item -ItemType Directory -Path $evidenceRoot | Out-Null
$screenRoot=Join-Path $runtimeRoot 'Saved/Screenshots/Windows'
$captures=@(); $ownedGame=$null; $passed=$false; $failure=$null
try {
    $sizes=if ($CaptureSet -eq 'AspectRatios') { @(@(1024,768),@(3440,1440)) } else { @(@(1280,720),@(1920,1080),@(2560,1440)) }
    foreach ($size in $sizes) {
        $name="$($size[0])x$($size[1])"
        $logPath=Join-Path $evidenceRoot ($name+'.log')
        $started=Get-Date
        $args=@('-RenderOffscreen','-windowed','-ForceRes',"-ResX=$($size[0])","-ResY=$($size[1])",'-unattended','-nosound','-NoSplash',
            '-ExecCmds="t.MaxFPS 30,Shot showui"',('-abslog="'+$logPath+'"'))
        $ownedGame=Start-Process -FilePath $runtimeExe -ArgumentList $args -WindowStyle Hidden -PassThru
        $deadline=(Get-Date).AddSeconds(45)
        $shot=$null
        do {
            if ($ownedGame.HasExited) { throw "Rendered game exited before $name capture." }
            $shot=Get-ChildItem -LiteralPath $screenRoot -Filter '*.png' -ErrorAction SilentlyContinue |
                Where-Object LastWriteTime -ge $started | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            if ($shot) { break }
            Start-Sleep -Milliseconds 500
        } while ((Get-Date) -lt $deadline)
        if (!$shot) { throw "No $name screenshot within 45 seconds." }
        Start-Sleep -Seconds 2 # Allow screenshot encoding/file completion before terminating this helper.
        $log=Get-Content -LiteralPath $logPath -Raw
        if ($log -match 'Fatal error:|Ensure condition failed:|LogD3D12RHI: Error:' -or !$log.Contains('Private test build: '+$label)) {
            throw "Rendered $name startup recorded a renderer/runtime error or incorrect build label."
        }
        $target=Join-Path $evidenceRoot ($name+'.png')
        Copy-Item -LiteralPath $shot.FullName -Destination $target
        # The PNG header confirms actual capture size rather than trusting requested window arguments.
        $png=[IO.File]::ReadAllBytes($target)
        if ($png.Length -lt 24 -or [BitConverter]::ToString($png,0,8) -ne '89-50-4E-47-0D-0A-1A-0A') { throw 'Capture is not a valid PNG header.' }
        $width=[uint32]$png[16]*16777216+[uint32]$png[17]*65536+[uint32]$png[18]*256+[uint32]$png[19]
        $height=[uint32]$png[20]*16777216+[uint32]$png[21]*65536+[uint32]$png[22]*256+[uint32]$png[23]
        if ($width -ne $size[0] -or $height -ne $size[1]) { throw "Requested $name but captured ${width}x${height}." }
        $captures+=@{image=$target;log=$logPath;width=$width;height=$height}
        $ownedGame.Kill(); $ownedGame.WaitForExit(); $ownedGame=$null
    }
    $passed=$true
} catch { $failure=$_.Exception.Message }
finally {
    if ($ownedGame -and !$ownedGame.HasExited) { $ownedGame.Kill(); $ownedGame.WaitForExit() }
    @{success=$passed;error=$failure;executable=$runtimeExe;buildLabel=$label;captureSet=$CaptureSet;captures=$captures;visualReview='Pending';
      scope='Offscreen rendered packaged startup frame including UI; no input/menu/network or hardware acceptance'} |
        ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $evidenceRoot 'Result.json') -Encoding utf8
}
if (!$passed) { throw $failure }
Write-Output "Captured $($captures.Count) rendered startup sizes for visual review: $evidenceRoot"
