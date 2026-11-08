"""Make Elitewake-Setup.exe and Elitewake-Data.bin from an existing playtest zip (owner, November 7: friends get only an
exe and a README; no rebuild of the game unless the owner asks).
    python Scripts/Release/make_playtest_installer.py Saved/PlaytestReleases/<label>
The folder holds the zip publish_playtest.ps1 made (one .zip, or .zip.001/.zip.002 parts). The zip is cut in two near
its middle: the first piece goes inside the exe (after the installer program, Scripts/Release/PlaytestInstaller/Setup.cs,
then the build label and a 32-byte trailer), the second is Elitewake-Data.bin. Each stays under GitHub's 2 GB per file.
Writes both, and README.md, to <folder>/installer.
"""
import struct
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSC = Path(r'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe')
LIMIT = 1_990_000_000
CHUNK = 64 * 1024 * 1024


class Joined:
    """The zip's parts read as one file (to check it before cutting)."""
    def __init__(self, paths):
        self.files = [open(p, 'rb') for p in paths]
        self.sizes = [p.stat().st_size for p in paths]
        self.pos = 0

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        self.pos = offset if whence == 0 else self.pos + offset if whence == 1 else sum(self.sizes) + offset
        return self.pos

    def read(self, n=-1):
        out, total = bytearray(), sum(self.sizes)
        n = total - self.pos if n is None or n < 0 else n
        while n > 0 and self.pos < total:
            start = 0
            for f, size in zip(self.files, self.sizes):
                if self.pos < start + size:
                    f.seek(self.pos - start)
                    data = f.read(min(n, start + size - self.pos))
                    out += data
                    self.pos += len(data)
                    n -= len(data)
                    break
                start += size
        return bytes(out)


def copy_range(parts, start, length, out):
    stream = Joined(parts)
    stream.seek(start)
    while length > 0:
        data = stream.read(min(CHUNK, length))
        out.write(data)
        length -= len(data)


def main():
    folder = Path(sys.argv[1]).resolve()
    label = folder.name
    parts = sorted(folder.glob('*.zip.0*')) or sorted(folder.glob('*.zip'))
    assert parts, f'no playtest zip in {folder}'
    names = zipfile.ZipFile(Joined(parts)).namelist()
    assert any(n.replace('\\', '/') == 'Windows/EW.exe' for n in names), 'the zip has no Windows/EW.exe at its top'
    total = sum(p.stat().st_size for p in parts)
    out = folder / 'installer'
    out.mkdir(exist_ok=True)
    stub = out / 'stub.exe'
    subprocess.run([str(CSC), '/nologo', '/optimize+', '/target:exe', f'/out:{stub}', '/r:System.IO.Compression.dll',
                    '/r:System.IO.Compression.FileSystem.dll', str(ROOT / 'Scripts/Release/PlaytestInstaller/Setup.cs')], check=True)
    stub_size = stub.stat().st_size
    label_bytes = label.encode('utf-8')
    a_len = min(total // 2, LIMIT - stub_size - len(label_bytes) - 32)
    b_len = total - a_len
    assert a_len + stub_size + 32 + len(label_bytes) < LIMIT and b_len < LIMIT, 'the build is too large for two files'
    setup, data = out / 'Elitewake-Setup.exe', out / 'Elitewake-Data.bin'
    with open(setup, 'wb') as f:
        f.write(stub.read_bytes())
        copy_range(parts, 0, a_len, f)
        f.write(label_bytes)
        f.write(struct.pack('<qqq', a_len, b_len, len(label_bytes)) + b'EWSETUP1')
    with open(data, 'wb') as f:
        copy_range(parts, a_len, b_len, f)
    stub.unlink()
    print(f'{setup.name} {setup.stat().st_size / 1e9:.2f} GB, {data.name} {data.stat().st_size / 1e9:.2f} GB, build {label}')


if __name__ == '__main__':
    main()
