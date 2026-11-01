# Run one Play check through run_play_check.py with an outside time limit, and print its result JSON.
# The runner's own timeout lives in Python and cannot fire if the runner fails to load, so this stops the editor itself after
# Timeout + 420 seconds (editor load, the check, a margin). Never run two editors on the project at once.
#   .\Scripts\Verification\run_play_check_once.ps1 -Check verify_elephant_play.py -Result ElephantPlayResult.json -Players 2 -Kit 1
# -Standalone 1 plays one survivor with no network (single-player checks such as verify_options_menu_play.py).
# -Yard held keeps the yard's sloop held (verify_voyage_ready_play.py); the default 'sold' releases it for older ship checks.
param([string]$Check, [string]$Result, [string]$Players = '2', [string]$Kit = '0', [string]$Timeout = '240',
      [string]$Window = '', [string]$Yard = 'sold', [string]$Standalone = '')
$Project = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Editor = "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
$env:EW_PLAY_MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
$env:EW_PLAY_CHECK = Join-Path $PSScriptRoot $Check
$env:EW_PLAY_RESULT = $Result
$env:EW_PLAY_PLAYERS = $Players
$env:EW_PLAY_STARTER_KIT = $Kit
$env:EW_PLAY_TIMEOUT = $Timeout
$env:EW_PLAY_YARD_SHIPS = $Yard
if ($Window) { $env:EW_PLAY_WINDOW = $Window } else { Remove-Item Env:EW_PLAY_WINDOW -ErrorAction SilentlyContinue }
if ($Standalone) { $env:EW_PLAY_STANDALONE = $Standalone } else { Remove-Item Env:EW_PLAY_STANDALONE -ErrorAction SilentlyContinue }
$out = Join-Path $Project "Saved\$Result"
Remove-Item $out -ErrorAction SilentlyContinue
$runner = (Join-Path $PSScriptRoot 'run_play_check.py') -replace '\\', '/'
$editor = Start-Process -PassThru -FilePath $Editor -ArgumentList @("`"$Project\EW.uproject`"", '/Game/Elitewake/Maps/Lvl_CoastalPlayground', '-unattended', "-ExecCmds=`"py $runner`"")
$limit = [int]$Timeout + 420
if (-not $editor.WaitForExit($limit * 1000)) {
    Stop-Process -Id $editor.Id -Force
    "$Check : editor stopped after $limit s with no finish"
}
if (Test-Path $out) { Get-Content $out -Raw } else { "$Check : no result file" }
