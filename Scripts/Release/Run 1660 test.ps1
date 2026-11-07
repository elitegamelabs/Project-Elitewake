<# The minimum-machine test (owner, November 2: the game must run on the GTX 1660 Super at 1920x1080 Low, within about
4.5 GB of video memory). Run it on that PC from the build's folder (beside the Windows folder) by double-clicking
"Run 1660 test.bat". It takes about 4 minutes and needs nothing else installed.

It starts the game on Low at 1920x1080 in its benchmark mode (-EWBenchmark: a fixed tour of the spawn, Saltreach and one
island of each other region, recording frame times; the game quits by itself), samples the game's video memory with
Windows' own counter every 2 seconds, and writes "1660 test results <date>.txt" beside this file: the graphics card, each
stop's frames per second and worst frames, and its video memory against the 4.5 GB budget. Bring that file back.
Changes nothing on the PC. #>
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$exe = Join-Path $here 'Windows\EW\Binaries\Win64\EW.exe'
if (!(Test-Path -LiteralPath $exe)) { throw "The game is not beside this file (looked for $exe). Keep this file next to the Windows folder." }
$resultJson = Join-Path $here 'Windows\EW\Saved\EWBenchmark.json'
if (Test-Path -LiteralPath $resultJson) { Remove-Item -LiteralPath $resultJson }
Write-Host 'Starting the 1660 test: the game opens, tours six places by itself and closes (about 4 minutes). Please do not touch it.'
$game = Start-Process -FilePath $exe -PassThru -ArgumentList @('/Game/Elitewake/Maps/Lvl_CoastalPlayground', '-EWBenchmark', '-windowed',
    '-ResX=1920', '-ResY=1080', '-NoSplash', '-ExecCmds="scalability 0"')
$samples = New-Object System.Collections.Generic.List[object]
$deadline = (Get-Date).AddMinutes(15)
while (-not $game.HasExited -and (Get-Date) -lt $deadline) {
    try {
        $c = (Get-Counter "\GPU Process Memory(pid_$($game.Id)*)\Dedicated Usage" -ErrorAction Stop).CounterSamples | Measure-Object CookedValue -Sum
        $samples.Add([pscustomobject]@{ utc = (Get-Date).ToUniversalTime(); bytes = [double]$c.Sum })
    } catch { }
    Start-Sleep -Seconds 2
}
if (-not $game.HasExited) { Stop-Process -Id $game.Id -Force; Write-Warning 'The game did not finish its tour within 15 minutes and was closed.' }

$gpu = (Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name) -join ', '
$lines = @("Elitewake 1660 test, $(Get-Date -Format 'yyyy-MM-dd HH:mm')", "Graphics card(s): $gpu", 'Setting: Low, 1920x1080', '')
$budget = 4.5
if (Test-Path -LiteralPath $resultJson) {
    $bench = Get-Content -LiteralPath $resultJson -Raw | ConvertFrom-Json
    $lines += "Game's own report: success=$($bench.success) $($bench.error)  (card seen by the game: $($bench.gpu), $($bench.resolution))"
    $lines += ''
    $lines += 'Stop        FPS (mean)  worst 5% frames  worst frame  GPU ms  Video memory'
    foreach ($s in $bench.stops) {
        $from = [datetime]::Parse($s.began_utc).ToUniversalTime(); $to = [datetime]::Parse($s.ended_utc).ToUniversalTime()
        $inStop = @($samples | Where-Object { $_.utc -ge $from -and $_.utc -le $to })
        $vram = if ($inStop.Count) { ($inStop | Measure-Object bytes -Maximum).Maximum / 1GB } else { [double]::NaN }
        $fps = if ($s.frame_ms_mean -gt 0) { 1000 / $s.frame_ms_mean } else { 0 }
        $lines += ('{0,-10} {1,8:N0}     {2,8:N1} ms      {3,7:N1} ms  {4,6:N1}  {5,6:N2} GB' -f $s.stop, $fps, $s.frame_ms_p95, $s.frame_ms_worst, $s.gpu_ms_mean, $vram)
    }
} else {
    $lines += 'The game wrote no report (it may have crashed or been closed). Video memory below is still measured.'
}
$peak = if ($samples.Count) { ($samples | Measure-Object bytes -Maximum).Maximum / 1GB } else { [double]::NaN }
$lines += ''
$lines += ('Highest video memory during the test: {0:N2} GB (budget {1} GB): {2}' -f $peak, $budget, $(if ($peak -le $budget) { 'WITHIN BUDGET' } else { 'OVER BUDGET' }))
$out = Join-Path $here ("1660 test results $(Get-Date -Format 'yyyy-MM-dd HHmm').txt")
$lines | Set-Content -LiteralPath $out -Encoding utf8
$lines | ForEach-Object { Write-Host $_ }
Write-Host ''
Write-Host "Saved: $out"
