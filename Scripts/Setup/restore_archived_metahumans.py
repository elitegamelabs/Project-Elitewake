"""Restore large source assets on a fresh checkout; never overwrite differing work."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    manifest = ROOT / 'Art/SourceAssets/MetaHumanArchives/manifest.json'
    for entry in json.loads(manifest.read_text(encoding='utf-8')):
        target = ROOT / entry['path']
        data = b''.join((ROOT / part).read_bytes() for part in entry['parts'])
        assert len(data) == entry['bytes'], f'Incorrect length: {target}'
        assert hashlib.sha256(data).hexdigest() == entry['sha256'], f'Corrupt archive: {target}'
        if target.exists():
            if hashlib.sha256(target.read_bytes()).hexdigest() != entry['sha256']:
                raise RuntimeError(f'Refusing to overwrite changed asset: {target}')
            print(f'Verified existing {entry["path"]}')
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as output:
                output.write(data)
            print(f'Restored {entry["path"]}')


if __name__ == '__main__':
    main()
