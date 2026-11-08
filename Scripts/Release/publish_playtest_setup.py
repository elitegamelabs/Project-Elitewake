"""Publish a packaged build to the friends' playtest repository (owner, November 7: the third playtest repository holds
nothing but a README; each build's exe and README go out in compressed zips). Release assets:
  Elitewake-Playtest-<label>-Part1.zip  (Elitewake-Setup.exe and README.md)
  Elitewake-Playtest-<label>-Part2.zip  (Elitewake-Data.bin)
Two zips because GitHub refuses any file over 2 GB and the game is about 3 GB. Run only when the owner asks for a playtest build:
    python Scripts/Release/publish_playtest_setup.py Saved/PrivateBuilds/<label>
  1. Zips the game client (the Windows folder, without debug symbols, manifests or engine debug tools) with Windows' tar.
  2. make_playtest_installer.py cuts the zip into the setup exe and the data file (each under GitHub's 2 GB per file).
  3. Writes the repository's README.md (its only file) for this build.
  4. Packs the setup exe and README into Part1.zip and the data file into Part2.zip (deflate, best compression).
  5. Deletes the older releases and publishes this one as Latest with the two zips.
Needs gh signed in with access to the repository.
"""
import base64
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = 'elitegamelabs/Elitewake-Playtest-Setup'
sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_playtest_installer  # noqa: E402


def run(*args, **kw):
    print('>', ' '.join(str(a) for a in args[:4]), '...')
    return subprocess.run([str(a) for a in args], check=True, **kw)


def readme(label):
    """The README: setup steps for this build, then playing together and the controls from the older playtest README."""
    src = (ROOT / 'Scripts/Release/publish_playtest.ps1').read_text(encoding='utf-8')
    play = src[src.index('## Play together'):src.index('"@ | Set-Content')].replace('``', '`').rstrip()
    sep = chr(92)
    game = sep.join(['Elitewake', 'Windows', 'EW.exe'])
    redist = sep.join(['Elitewake', 'Windows', 'Engine', 'Extras', 'Redist', 'en-us', 'vc_redist.x64.exe'])
    return f"""# Elitewake playtest

A private test build of Elitewake for invited friends (Windows 10 or 11). Not a release: placeholder art, sounds and balance;
things will break. Please do not share the files outside the invited group.

Current build: **{label}**

## Set it up
1. Open **Releases** (right side of this page), pick the one marked **Latest**, and under *Assets* download both zips:
   **...-Part1.zip** and **...-Part2.zip** (under 2 GB each). Ignore the two "Source code" links GitHub adds.
2. Make one folder with about 10 GB free, and extract **both** zips into it (right-click, Extract All, choose that same
   folder). It then holds Elitewake-Setup.exe, Elitewake-Data.bin and this README.
3. Double-click **Elitewake-Setup.exe**. Windows may warn that the program is unsigned: click **More info**, then **Run anyway**.
   It puts the game together in an **Elitewake** folder next to it (about a minute) and starts it.
4. Next time, start the game with **{game}**, or run the setup again (it skips straight to the game).
5. If Windows says a runtime is missing, run **{redist}** once.

A new build replaces the old one: extract the two new zips into the same folder and run the setup; it replaces the old game.

## Getting started
Single Player: choose a Freeport on the world map, then Create New Survivor (or Resume Game after playing before), make your
survivor and press Set Sail.

{play}
"""


def main():
    archive = Path(sys.argv[1]).resolve()
    label = archive.name
    assert (archive / 'Windows/EW.exe').exists() or (archive / 'Windows/EW/Binaries/Win64/EW.exe').exists(), f'no game in {archive}'
    out = ROOT / 'Saved/PlaytestReleases' / label
    out.mkdir(parents=True, exist_ok=True)
    zip_path = out / f'Elitewake-Playtest-{label}.zip'
    if not zip_path.exists():
        excludes = []
        for pattern in ('*.pdb', 'Manifest_*.txt', 'GPUDumpViewer'):
            excludes += ['--exclude', pattern]
        run(Path(os.environ['SystemRoot']) / 'System32/tar.exe', '-a', '-c', '-f', zip_path, *excludes, '-C', archive, 'Windows')
    sys.argv = [sys.argv[0], str(out)]
    make_playtest_installer.main()
    installer = out / 'installer'
    text = readme(label)
    (installer / 'README.md').write_text(text, encoding='utf-8')

    current = subprocess.run(['gh', 'api', f'repos/{REPO}/contents/README.md', '--jq', '.sha'], capture_output=True, text=True)
    body = {'message': f'README for build {label}', 'content': base64.b64encode(text.encode('utf-8')).decode()}
    if current.returncode == 0 and current.stdout.strip():
        body['sha'] = current.stdout.strip()
    put = installer / 'readme-put.json'
    put.write_text(json.dumps(body))
    run('gh', 'api', '-X', 'PUT', f'repos/{REPO}/contents/README.md', '--input', put, capture_output=True)
    put.unlink()

    # The release's downloads: the exe and README in one compressed zip, the data in another.
    import zipfile
    zips = []
    for part, members in ((1, ('Elitewake-Setup.exe', 'README.md')), (2, ('Elitewake-Data.bin',))):
        target = installer / f'Elitewake-Playtest-{label}-Part{part}.zip'
        with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED, compresslevel=9, allowZip64=True) as z:
            for name in members:
                z.write(installer / name, name)
        assert target.stat().st_size < 1_990_000_000, f'{target.name} is over the 2 GB GitHub limit'
        zips.append(target)

    tags = subprocess.run(['gh', 'release', 'list', '--repo', REPO, '--json', 'tagName', '--jq', '.[].tagName'],
                          capture_output=True, text=True, check=True).stdout.split()
    for tag in tags:
        run('gh', 'release', 'delete', tag, '--repo', REPO, '--yes', '--cleanup-tag')
    run('gh', 'release', 'create', label, *zips, '--repo', REPO,
        '--title', f'Elitewake playtest {label}', '--notes',
        'Download both zips, extract them into one folder and run Elitewake-Setup.exe. See the README.', '--latest')
    assets = subprocess.run(['gh', 'release', 'view', label, '--repo', REPO, '--json', 'assets', '--jq',
                             '.assets[] | "\\(.name) \\(.size) \\(.state)"'], capture_output=True, text=True, check=True).stdout
    print(assets)
    for target in zips:
        size = target.stat().st_size
        assert f'{target.name} {size} uploaded' in assets, f'{target.name} did not upload completely'
    print(f'Published {label} to {REPO}')


if __name__ == '__main__':
    main()
