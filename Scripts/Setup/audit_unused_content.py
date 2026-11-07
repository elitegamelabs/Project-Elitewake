"""List /Game content nothing in the game reaches (owner, November 7: keep only what the game needs now and later).
Read-only. Run outside Play:
    UnrealEditor-Cmd.exe EW.uproject -run=pythonscript -script=Scripts/Setup/audit_unused_content.py
Roots: every map, every World Partition actor and object package, and every /Game path named in Source/, Config/
and Scripts/ (C++ loads by path, the setup scripts build and the checks use assets by path). From the roots it follows
the Asset Registry's hard and soft package dependencies. Writes Saved/UnusedContent.json: each unreached package with
its size on disk. A list to review, not a deletion.
"""
import json
import re
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
registry = unreal.AssetRegistryHelpers.get_asset_registry()
registry.search_all_assets(True)

packages = set()
for data in registry.get_assets_by_path('/Game', recursive=True, include_only_on_disk_assets=True):
    packages.add(str(data.package_name))

# Maps are roots only when the code or config name them (title, coast, the session harness); their World Partition
# objects come with them.
roots = set()
path_re = re.compile(r'/Game/[A-Za-z0-9_/\-]+')


def named_in(folders, suffixes):
    """Packages named exactly (an asset path, or a folder path covering them) in these folders' files."""
    found = set()
    for folder in folders:
        for file in (ROOT / folder).rglob('*'):
            if file.suffix.lower() not in suffixes:
                continue
            text = file.read_text(encoding='utf-8', errors='ignore')
            for match in path_re.findall(text):
                path = match.split('.')[0].rstrip('/')
                if path in packages:
                    found.add(path)
                elif path.count('/') >= 4:
                    found.update(n for n in packages if n.startswith(path + '/'))
    return found


# What the game loads: maps, world objects, and every path the C++ code and config name.
roots |= named_in(('Source', 'Config'), ('.h', '.cpp', '.cs', '.ini'))
for name in list(roots):
    leaf = name.rsplit('/', 1)[-1]
    roots.update(n for n in packages if ('/__ExternalActors__/' in n or '/__ExternalObjects__/' in n) and f'/{leaf}/' in n)
# What the setup and check scripts name: reported, not counted as used by the game.
scripted = named_in(('Scripts',), ('.py', '.ps1', '.json'))

options = unreal.AssetRegistryDependencyOptions(include_soft_package_references=True, include_hard_package_references=True,
                                                include_searchable_names=False, include_soft_management_references=True,
                                                include_hard_management_references=True)
reached, stack = set(), list(roots)
while stack:
    name = stack.pop()
    if name in reached:
        continue
    reached.add(name)
    for dep in registry.get_dependencies(name, options) or []:
        dep = str(dep)
        if dep.startswith('/Game/') and dep not in reached:
            stack.append(dep)

unused = []
for name in sorted(packages - reached):
    rel = name[len('/Game/'):]
    file = ROOT / 'Content' / (rel + '.uasset')
    if not file.exists():
        file = ROOT / 'Content' / (rel + '.umap')
    unused.append({'package': name, 'bytes': file.stat().st_size if file.exists() else 0, 'named_in_scripts': name in scripted})
report = {'packages': len(packages), 'roots': len(roots), 'reached': len(reached), 'unused': unused,
          'unused_mb': round(sum(u['bytes'] for u in unused) / 1e6, 1)}
Path(unreal.Paths.project_saved_dir(), 'UnusedContent.json').write_text(json.dumps(report, indent=2))
unreal.log(f'Unused content: {len(unused)} packages, {report["unused_mb"]} MB')
