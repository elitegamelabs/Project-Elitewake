<#
Local loopback connection smoke check; optionally accepts a cooked Development executable.
Does not certify rendered gameplay, LAN/Internet, authentication, distribution or physical input. Leaves the owner's editor alone.
#>
param([int]$Port = 17887, [switch]$Gameplay, [string]$PackagedExecutable)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$engine = 'C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe'
$project = Join-Path $projectRoot 'EW.uproject'
$launchPrefix = @(('"' + $project + '"'))
$logPrefix = 'SeparateProcess'
if ($PackagedExecutable) {
    if ($Gameplay) { throw 'The editor-only gameplay harness is absent from packaged game targets.' }
    $engine = (Resolve-Path -LiteralPath $PackagedExecutable).Path
    $launchPrefix = @()
    $logPrefix = 'Packaged'
}
$logRoot = Join-Path $projectRoot 'Saved/Logs'
$hostLog = Join-Path $logRoot ($logPrefix + 'Host.log')
$clientLog = Join-Path $logRoot ($logPrefix + 'Client.log')
$resultPath = Join-Path $projectRoot $(if ($PackagedExecutable) { 'Saved/PackagedConnectionResult.json' } elseif ($Gameplay) { 'Saved/SeparateProcessGameplayResult.json' } else { 'Saved/SeparateProcessConnectionResult.json' })
$gameplayRoot = Join-Path $projectRoot 'Saved/SeparateGameplay'
$hostProcess = $null
$clientProcess = $null
$checks = @()
$passed = $false
$failure = $null
try {
    if ($Port -lt 1024 -or $Port -gt 65535) { throw 'Choose an unprivileged UDP port.' }
    if (Get-NetUDPEndpoint -LocalPort $Port -ErrorAction SilentlyContinue) { throw 'Test port is already in use.' }
    New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
    # These exact diagnostic logs are regenerated; no recursive filesystem actions.
    Remove-Item -LiteralPath $hostLog,$clientLog -ErrorAction SilentlyContinue
    $common = @('-game','-unattended','-nop4','-NullRHI','-nosound','-NoSplash','-ExecCmds="t.MaxFPS 60"','-log','-LogCmds="LogNet Verbose,LogGameMode Verbose"')
    $testMap = if ($Gameplay) { '/Game/Elitewake/Maps/Lvl_M5PickupTest?listen' } else { '/Game/ThirdPerson/Lvl_ThirdPerson?listen' }
    $hostArgs = $launchPrefix + @($testMap) + $common + @('-MULTIHOME=127.0.0.1',"-port=$Port",('-abslog="' + $hostLog + '"'))
    if ($Gameplay) {
        New-Item -ItemType Directory -Path $gameplayRoot -Force | Out-Null
        foreach ($marker in @('Host1','Host2','Host3','Host4','Host5','Client1','Client2','Client3','Client4','HostResult.txt','ClientResult.txt')) {
            Remove-Item -LiteralPath (Join-Path $gameplayRoot $marker) -ErrorAction SilentlyContinue
        }
        $hostArgs += '-EWVerifyRole=Host'
    }
    $hostProcess = Start-Process -FilePath $engine -ArgumentList $hostArgs -WindowStyle Hidden -PassThru
    $deadline = (Get-Date).AddSeconds(60)
    $joinRecorded = $false
    do {
        if ($hostProcess.HasExited) { throw 'Host process exited before listening. See host log.' }
        $text = if (Test-Path $hostLog) { Get-Content -LiteralPath $hostLog -Raw } else { '' }
        if ($text -match "listening on port $Port") { break }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)
    if ($text -notmatch "listening on port $Port") { throw 'Host did not begin listening within 60 seconds.' }
    $endpoints = @(Get-NetUDPEndpoint -OwningProcess $hostProcess.Id -LocalPort $Port -ErrorAction SilentlyContinue)
    if (!$endpoints -or @($endpoints | Where-Object LocalAddress -ne '127.0.0.1').Count) { throw 'Host binding is not exclusively loopback.' }
    $checks += 'Listen host is bound exclusively to loopback; no firewall/router changes'
    $clientArgs = $launchPrefix + @("127.0.0.1:$Port") + $common + @(('-abslog="' + $clientLog + '"'))
    if ($Gameplay) { $clientArgs += '-EWVerifyRole=Client' }
    $clientProcess = Start-Process -FilePath $engine -ArgumentList $clientArgs -WindowStyle Hidden -PassThru
    if ($hostProcess.Id -eq $clientProcess.Id) { throw 'Expected distinct process IDs.' }
    $checks += 'Host and client have distinct operating-system process IDs'
    $deadline = (Get-Date).AddSeconds(60)
    do {
        if ($hostProcess.HasExited -or $clientProcess.HasExited) { throw 'A test process exited during connection.' }
        $hostText = Get-Content -LiteralPath $hostLog -Raw
        $clientText = if (Test-Path $clientLog) { Get-Content -LiteralPath $clientLog -Raw } else { '' }
        $joinRecorded = ($hostText -match 'Join succeeded') -and ($clientText -match 'Welcomed by server')
        if ($joinRecorded) { break }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)
    if (!$joinRecorded) { throw 'Expected server join and client welcome evidence was not recorded.' }
    $checks += 'Server accepts client join and client receives server welcome in separate logs'
    Start-Sleep -Seconds 3
    if ($hostProcess.HasExited -or $clientProcess.HasExited) { throw 'A process exited after joining.' }
    $hostText = Get-Content -LiteralPath $hostLog -Raw
    $clientText = Get-Content -LiteralPath $clientLog -Raw
    if ($PackagedExecutable -and (($hostText + $clientText) -match 'Ensure condition failed:|Fatal error:')) {
        throw 'Packaged runtime recorded an ensure or fatal error; inspect both logs.'
    }
    if ($PackagedExecutable) {
        $labelPath=Join-Path (Split-Path $engine -Parent) '../../PrivateBuildLabel.txt'
        if (Test-Path -LiteralPath $labelPath) {
            $expectedLabel=(Get-Content -LiteralPath $labelPath -Raw).Trim()
            if (!$expectedLabel -or !$hostText.Contains('Private test build: '+$expectedLabel) -or !$clientText.Contains('Private test build: '+$expectedLabel)) {
                throw 'Packaged host/client did not load the archived build label.'
            }
            $checks += 'Both packaged processes load the archived private-test build label'
        }
    }
    $pawnNames = @([regex]::Matches($clientText,'PersistentLevel\.(BP_ThirdPersonCharacter_C_\d+)') | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique)
    if ($pawnNames.Count -ne 2) { throw 'Client log did not record two distinct runtime character instances.' }
    if ($clientText -match 'CreateSavedMove: Hit limit|NetworkFailure|TravelFailure') { throw 'Movement timing or connection failure was recorded; inspect client log.' }
    $checks += 'Client records two distinct character instances and remains connected during bounded observation'
    if ($Gameplay) {
        $deadline = (Get-Date).AddSeconds(90)
        $hostResult = Join-Path $gameplayRoot 'HostResult.txt'
        $clientResult = Join-Path $gameplayRoot 'ClientResult.txt'
        do {
            if ($hostProcess.HasExited -or $clientProcess.HasExited) { throw 'Gameplay process exited before acceptance.' }
            foreach ($report in @($hostResult,$clientResult)) {
                if ((Test-Path $report) -and (Get-Content -LiteralPath $report -Raw) -match '^FAIL') { throw (Get-Content -LiteralPath $report -Raw) }
            }
            if ((Test-Path $hostResult) -and (Test-Path $clientResult)) { break }
            Start-Sleep -Milliseconds 500
        } while ((Get-Date) -lt $deadline)
        if (!(Test-Path $hostResult) -or !(Test-Path $clientResult)) { throw 'Gameplay reports did not complete.' }
        foreach ($report in @($hostResult,$clientResult)) {
            $lines = @(Get-Content -LiteralPath $report)
            if ($lines[0] -ne 'PASS') { throw 'Gameplay report did not pass.' }
            $checks += $lines[1..($lines.Length-1)] | Where-Object { $_ }
        }
    }
    $passed = $true
} catch { $failure = $_.Exception.Message }
finally {
    # Terminate only the disposable processes created by this script.
    foreach ($ownedProcess in @($clientProcess,$hostProcess)) {
        if ($ownedProcess -and !$ownedProcess.HasExited) { $ownedProcess.Kill(); $ownedProcess.WaitForExit() }
    }
    @{success=$passed;checks=$checks;error=$failure;hostLog=$hostLog;clientLog=$clientLog;executable=$engine;scope=$(if ($PackagedExecutable) { 'Cooked Development package headless loopback connection only' } elseif ($Gameplay) { 'Headless loopback gameplay; inventory visibility recorded separately' } else { 'Headless separate-process loopback connection only' })} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $resultPath -Encoding utf8
}
if (!$passed) { throw $failure }
Write-Output "Passed $($checks.Count) checks. Rendering, physical input, LAN and distribution remain separate."
