<# Turn an encrypted local demo folder into one self-extracting, playable EXE. #>
param(
    [Parameter(Mandatory=$true)][string]$ArchiveDirectory,
    [string]$SevenZip='C:/Program Files/7-Zip/7z.exe',
    [string]$SfxModule='C:/UnrealProjects/EW/Saved/BuildTools/LzmaSdk/26.04/bin/7zSD.sfx',
    # Owner, October 19: the program is called Elite_Wake.exe, with the EW icon in a silver box.
    [string]$ProgramName='Elite_Wake',
    [string]$Icon=''
)
$ErrorActionPreference='Stop'
$archive=(Resolve-Path -LiteralPath $ArchiveDirectory).Path
if (!$Icon) { $Icon=Join-Path $PSScriptRoot '../../Build/Windows/Application.ico' }
if (!(Test-Path -LiteralPath $Icon)) { throw 'The program icon (Build/Windows/Application.ico) is missing; run Scripts/Setup/make_app_icon.py.' }
$Icon=(Resolve-Path -LiteralPath $Icon).Path
$windows=Join-Path $archive 'Windows'
$info=Join-Path $archive 'DemoBuildInfo.json'
if (!(Test-Path -LiteralPath $info)) { throw 'A verified encrypted demo build is required.' }
$meta=Get-Content -LiteralPath $info -Raw | ConvertFrom-Json
if (!$meta.assetsEncrypted -or !$meta.pakIndexRequiresKey) { throw 'Encryption verification has not passed.' }
$runtime=Join-Path $windows 'EW/Binaries/Win64/EW-Win64-Shipping.exe'
if (!(Test-Path -LiteralPath $runtime)) { throw 'The Windows Shipping runtime is missing.' }
if (!(Test-Path -LiteralPath $SfxModule)) { throw 'Download the official LZMA SDK self-extracting module first.' }
$unsafeFiles=@(Get-ChildItem -LiteralPath $windows -File -Recurse | Where-Object {$_.Name -in @('Crypto.json','DefaultCrypto.ini') -or $_.Extension -eq '.pdb'})
if ($unsafeFiles.Count) { throw 'Private crypto metadata or debug symbols were found in the distributable.' }
$launcherSource=Join-Path $archive 'DemoLauncher.cs'
@'
using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Windows.Forms;
using Microsoft.Win32;

internal static class DemoLauncher
{
    [STAThread]
    private static int Main()
    {
        try
        {
            if (!Environment.Is64BitOperatingSystem)
                throw new InvalidOperationException("This demo requires 64-bit Windows.");
            string root = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            string installer = Path.Combine(root, @"Engine\Extras\Redist\en-us\vc_redist.x64.exe");
            FileVersionInfo required = FileVersionInfo.GetVersionInfo(installer);
            Version minimum = new Version(required.FileMajorPart, required.FileMinorPart, required.FileBuildPart);
            bool runtimeReady = false;
            using (RegistryKey key = Registry.LocalMachine.OpenSubKey(@"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64"))
            {
                Version installed;
                string version = key == null ? "" : Convert.ToString(key.GetValue("Version", "")).TrimStart('v', 'V');
                runtimeReady = key != null && Convert.ToInt32(key.GetValue("Installed", 0)) == 1 &&
                    Version.TryParse(version, out installed) && installed >= minimum;
            }
            if (!runtimeReady)
            {
                if (MessageBox.Show("Elitewake needs the Microsoft Visual C++ runtime included with this demo. Open Microsoft's installer now?", "ELITEWAKE", MessageBoxButtons.YesNo, MessageBoxIcon.Information) != DialogResult.Yes)
                    return 0;
                using (Process setup = Process.Start(new ProcessStartInfo(installer) { UseShellExecute = true }))
                {
                    setup.WaitForExit();
                    if (setup.ExitCode != 0 && setup.ExitCode != 3010)
                        throw new InvalidOperationException("The Microsoft runtime installation did not finish. You can launch the demo again to retry.");
                }
            }
            string game = Path.Combine(root, @"EW\Binaries\Win64\EW-Win64-Shipping.exe");
            using (Process play = Process.Start(new ProcessStartInfo(game, "/Game/Elitewake/Maps/Lvl_Title")
                { WorkingDirectory = Path.GetDirectoryName(game), UseShellExecute = false }))
            {
                play.WaitForExit();
                return play.ExitCode;
            }
        }
        catch (Exception error)
        {
            MessageBox.Show(error.Message, "ELITEWAKE", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }
}
'@ | Set-Content -LiteralPath $launcherSource -Encoding utf8
$csc=Join-Path $env:WINDIR 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
& $csc '/nologo' '/target:winexe' '/platform:x64' '/optimize+' '/reference:System.Windows.Forms.dll' ("/win32icon:"+$Icon) ("/out:"+(Join-Path $windows 'LaunchDemo.exe')) $launcherSource
if ($LASTEXITCODE -ne 0) { throw 'The single-file demo launcher could not be compiled.' }
Copy-Item -LiteralPath $info -Destination (Join-Path $windows 'DEMO_BUILD.json')
@'
ELITEWAKE — PRIVATE WINDOWS DEMO

Double-click Elite_Wake.exe. It extracts the game temporarily, then opens
the title screen. Press any key, then choose Single Player to explore the coast.
The temporary game folder is removed after you close the game. Keep the EXE
to play again. The game requires 64-bit Windows and a DirectX 12 capable GPU.
If needed, the launcher offers the included official Microsoft runtime installer.

WASD: move. Space: jump or swim up. Left Shift: sprint.
Tap C: crouch. Hold C: prone. Z: switch first/third person.
E: interact; hold for ship fittings and anchor. Left Mouse: attack/gather.
1–8: hotbar. I: inventory/crafting/journal. M: map.
The on-screen Journal contains the current ship controls and playtest guides.

This is the current development demo, with placeholder characters and unfinished
systems. Game assets are encrypted to deter casual extraction. Client-side
encryption cannot guarantee that recipients cannot recover game data.

Single-file packaging uses the public-domain LZMA SDK by Igor Pavlov.
'@ | Set-Content -LiteralPath (Join-Path $windows 'DEMO_README.txt') -Encoding utf8
$payload=Join-Path $archive 'DemoPayload.7z'
if (Test-Path -LiteralPath $payload) { throw 'A payload already exists; preserve it and use a fresh build.' }
Push-Location $windows
try {
    & $SevenZip a '-t7z' '-m0=LZMA2' '-mx=1' '-ms=off' $payload '*' '-xr!*.pdb' '-xr!Manifest_*.txt' *> (Join-Path $archive 'SingleExePack.log')
    if ($LASTEXITCODE -ne 0) { throw 'The demo payload could not be archived.' }
} finally { Pop-Location }
$config=Join-Path $archive 'SingleExeConfig.txt'
[IO.File]::WriteAllText($config,";!@Install@!UTF-8!`r`nTitle=`"Elite Wake`"`r`nProgress=`"yes`"`r`nRunProgram=`"LaunchDemo.exe`"`r`n;!@InstallEnd@!`r`n",(New-Object Text.UTF8Encoding($false)))
$output=Join-Path $archive ($ProgramName+'.exe')
# The self-extractor shows the program's icon: stamp a copy of the module (the original stays untouched).
$stampedSfx=Join-Path $archive 'SingleExeModule.sfx'
Copy-Item -LiteralPath $SfxModule -Destination $stampedSfx
& (Join-Path $PSScriptRoot 'set_exe_icon.ps1') -Executable $stampedSfx -Icon $Icon -AsInvoker
if (Test-Path -LiteralPath $output) { throw 'A final EXE already exists and will not be overwritten.' }
$outStream=[IO.File]::Create($output)
try {
    foreach ($part in @($stampedSfx,$config,$payload)) {
        $inputStream=[IO.File]::OpenRead($part)
        try { $inputStream.CopyTo($outStream) } finally { $inputStream.Dispose() }
    }
} finally { $outStream.Dispose() }
& $SevenZip t $output *> (Join-Path $archive 'SingleExeVerification.log')
if ($LASTEXITCODE -ne 0) { throw 'The final single-EXE archive integrity check failed.' }
$hash=(Get-FileHash -LiteralPath $output -Algorithm SHA256).Hash
"$hash  $ProgramName.exe" | Set-Content -LiteralPath (Join-Path $archive ($ProgramName+'.sha256.txt')) -Encoding ascii
Write-Output "Single encrypted demo EXE ready: $output"
Write-Output "Size: $([math]::Round((Get-Item -LiteralPath $output).Length/1MB)) MB"
