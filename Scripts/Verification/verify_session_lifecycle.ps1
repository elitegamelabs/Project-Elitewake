<# Two disposable loopback-only game processes exercise native Host/Join/Leave and errors.
Not LAN/Internet/package or physical button acceptance. Does not edit editor preferences. #>
param([int]$Port=17887)
$ErrorActionPreference='Stop'
$projectRoot=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$engine='C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe'
$reportRoot=Join-Path $projectRoot 'Saved/SessionLifecycle'
$project=Join-Path $projectRoot 'EW.uproject'
$hostProcess=$null; $clientProcess=$null
$passed=$false; $failure=$null; $checks=@()
try {
    if ($Port -lt 1024 -or $Port -ge 65535) { throw 'Choose a port from 1024 to 65534.' }
    if (Get-NetUDPEndpoint -LocalPort $Port,($Port+1) -ErrorAction SilentlyContinue) { throw 'A requested diagnostic port is occupied.' }
    New-Item -ItemType Directory -Path $reportRoot -Force | Out-Null
    foreach ($name in @('HostReady','ClientLeft','HostLeaveObserved','ClientRejoined','HostFinished','HostResult.txt','ClientResult.txt')) {
        Remove-Item -LiteralPath (Join-Path $reportRoot $name) -ErrorAction SilentlyContinue
    }
    $common=@(('"'+$project+'"'),'/Game/ThirdPerson/Lvl_ThirdPerson','-game','-unattended','-nop4','-NullRHI','-nosound','-NoSplash',
        '-ExecCmds="t.MaxFPS 60"','-MULTIHOME=127.0.0.1',"-port=$Port", "-EWVerifyPort=$Port")
    $hostArgs=$common+@('-EWVerifySessionRole=Host',('-abslog="'+(Join-Path $reportRoot 'Host.log')+'"'))
    $hostProcess=Start-Process -FilePath $engine -ArgumentList $hostArgs -WindowStyle Hidden -PassThru
    $deadline=(Get-Date).AddSeconds(60)
    while (!(Test-Path (Join-Path $reportRoot 'HostReady'))) {
        if ($hostProcess.HasExited) { throw 'Host exited before its ready checkpoint.' }
        $failureReport=Join-Path $reportRoot 'HostResult.txt'
        if ((Test-Path $failureReport) -and (Get-Content $failureReport -Raw) -match '^FAIL') { throw (Get-Content $failureReport -Raw) }
        if ((Get-Date) -ge $deadline) { throw 'Host did not become ready within 60 seconds.' }
        Start-Sleep -Milliseconds 500
    }
    $endpoints=@(Get-NetUDPEndpoint -OwningProcess $hostProcess.Id -LocalPort $Port -ErrorAction SilentlyContinue)
    if (!$endpoints -or @($endpoints | Where-Object LocalAddress -ne '127.0.0.1').Count) { throw 'Host binding is not exclusively loopback.' }
    $checks+='Host initiated through GameInstance API binds exclusively to loopback'
    $clientArgs=$common+@('-EWVerifySessionRole=Client',('-abslog="'+(Join-Path $reportRoot 'Client.log')+'"'))
    $clientProcess=Start-Process -FilePath $engine -ArgumentList $clientArgs -WindowStyle Hidden -PassThru
    $deadline=(Get-Date).AddSeconds(150)
    $reports=@((Join-Path $reportRoot 'HostResult.txt'),(Join-Path $reportRoot 'ClientResult.txt'))
    do {
        if ($hostProcess.HasExited -or $clientProcess.HasExited) { throw 'Test process exited before lifecycle completed.' }
        foreach ($report in $reports) {
            if ((Test-Path $report) -and (Get-Content $report -Raw) -match '^FAIL') { throw (Get-Content $report -Raw) }
        }
        if ((Test-Path $reports[0]) -and (Test-Path $reports[1])) { break }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)
    foreach ($report in $reports) {
        if (!(Test-Path $report)) { throw 'Missing completed lifecycle report.' }
        $lines=@(Get-Content -LiteralPath $report)
        if ($lines[0] -ne 'PASS') { throw 'Lifecycle report did not pass.' }
        $checks += $lines[1..($lines.Length-1)] | Where-Object { $_ }
    }
    $passed=$true
} catch { $failure=$_.Exception.Message }
finally {
    foreach ($ownedProcess in @($clientProcess,$hostProcess)) {
        if ($ownedProcess -and !$ownedProcess.HasExited) { $ownedProcess.Kill(); $ownedProcess.WaitForExit() }
    }
    @{success=$passed;checks=$checks;error=$failure;scope='Headless loopback Host/Join/Leave and connection recovery; not physical UI or LAN'} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $projectRoot 'Saved/SessionLifecycleResult.json') -Encoding utf8
}
if (!$passed) { throw $failure }
Write-Output "Passed $($checks.Count) session lifecycle checkpoints."
