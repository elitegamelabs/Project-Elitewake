"""Build an index of source artwork without changing any image pixels."""
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / 'Art'

def main():
    assets = []
    for path in sorted(ART.rglob('*.png')):
        relative = path.relative_to(ROOT).as_posix()
        sidecar = path.with_suffix('.json')
        meta = json.loads(sidecar.read_text(encoding='utf-8-sig')) if sidecar.exists() else {}
        with Image.open(path) as image:
            image.load()
            size = list(image.size)
            alpha = list(image.getchannel('A').getextrema()) if 'A' in image.getbands() else None
        status = meta.get('status', 'Existing source reference; consult adjacent README/selection/roster metadata')
        warnings = []
        if '/Growth/' in relative:
            status = 'DRAFT: species identity needs correction before modeling or runtime use'
            warnings.append('First growth board does not faithfully match the requested species rows; remaining boards not generated.')
        if 'forage3-Atlas-v1' in relative or ('/Survival/' in relative and '/Matte-v2/' not in relative):
            status = 'Legacy art; newer version preferred'
        if 'Brigantine-Exterior-Mast-Sockets-v2' in relative:
            status = 'Alternate reference only; owner-selected original hulls remain canonical'
        if 'insects1-Atlas' in relative:
            warnings.append('Bloodwing depiction needs anatomy review against the mosquito-like guide description.')
        if 'blueprints-Atlas' in relative:
            warnings.append('Decorative diagram references only; wooden-tool drawing needs material correction.')
        columns, rows = meta.get('columns'), meta.get('rows')
        slots = []
        if columns and rows:
            for index, item in enumerate(meta.get('items', [])):
                details = dict(item) if isinstance(item, dict) else {'name': item}
                row, column = divmod(index, columns)
                details.update(index=index, row=row, column=column,
                               uv={'min': [column / columns, row / rows],
                                   'max': [(column + 1) / columns, (row + 1) / rows]})
                slots.append(details)
            if len(slots) > columns * rows:
                raise ValueError(f'Too many atlas entries: {relative}')
        assets.append({'path': relative, 'bytes': path.stat().st_size,
                       'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                       'dimensions': size, 'alphaRange': alpha, 'status': status,
                       'metadata': sidecar.relative_to(ROOT).as_posix() if sidecar.exists() else None,
                       'columns': columns, 'rows': rows, 'items': slots, 'reviewNotes': warnings})
    catalog = {'version': 1, 'purpose': 'Original Elitewake 2D source art and modeling references',
               'limitations': 'Images are not 3D meshes, rigs, animations or proof of gameplay integration. Atlas UVs are equal-cell reference regions, not final sprite packing.',
               'authority': 'Docs/WORLD_STRUCTURE_OWNER_DECISIONS_2026-10-14.md',
               'assets': assets}
    (ART / 'CATALOG.json').write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    lines = ['# Elitewake artwork catalog', '',
             'Original source images for the team and Claude. This folder is part of the project. Images are **2D references**, not newly imported 3D meshes or implemented gameplay.', '',
             '[Machine-readable catalog](CATALOG.json) includes dimensions, alpha ranges, hashes, atlas names and row/column UV regions. Adjacent JSON files preserve generation prompts. Run `python Scripts/Art/build_art_catalog.py` from the repository to rebuild it.', '',
             '## Start here', '',
             '- [Latest owner decisions](../Docs/WORLD_STRUCTURE_OWNER_DECISIONS_2026-10-14.md)',
             '- [Milestones](../Docs/MILESTONES.md) and [remaining-work checklist](../Docs/REMAINING_WORK_2026-10-14.md)',
             '- [Claude terrain/model handoff](../Docs/MILESTONE_WORLD_MESH_HANDOFF_2026-10-14.md)',
             '- [Single Player](../Docs/SINGLE_PLAYER_RULES.md) / [Multiplayer](../Docs/MULTIPLAYER_RULES.md)',
             '- [Animal roster](Concepts/Animals/2026-10-12/roster.json): guide region labels are provenance, not final five-region spawn assignments.',
             '- [Owner-selected ship originals](Concepts/Boats/2026-10-11/selection.json): later alternate hulls do not replace these.', '',
             '## Coverage and review', '',
             'The October 14 atlases cover currency, common resources, ore and ingots, tools, crops, orchard fruit, regional forage/herbs/fungi/insects/trees, animal materials, weapons, ammunition, medicine, placeables, ship fittings, decorative recipe references, clothing and climate motifs. Existing animal, ship, sail, workstation, fish, HUD and title images are indexed too. Generic animal materials may be reused for species-specific drops; art does not establish new recipes, values or unlocks.', '',
             'Growth stages remain incomplete. The first growth board has incorrect species imagery and is explicitly a draft. Do not treat it as an approved mesh reference. Tree/crop growth boards, seed and sapling imagery, multi-view modeling references, claim flags and neon ghost-ship group art remain on the checklist. Berry bushes are wild-only and static; no berry seeds or planted growth stages.', '',
             'Forage sheet 3 version 2 replaces version 1. Insects sheet 1 needs Bloodwing anatomy review. Blueprint diagrams are illustrative and need a wooden-tool material correction. Atlas arrangements and cutout quality need visual approval before runtime binding. No game balance or distribution is inferred from art. Duplicate ZIP bundles are excluded from this publication; individual source images are supplied.', '',
             f'Indexed images: **{len(assets)}**. PNG sources are stored through Git LFS; use a normal Git LFS checkout to obtain full-resolution files.', '',
             '## Images', '', '| Image | Size | Named atlas slots | Status |', '| --- | --- | --- | --- |']
    for entry in assets:
        label = entry['path'][4:]
        lines.append(f"| [{label}]({label}) | {entry['dimensions'][0]} × {entry['dimensions'][1]} | {len(entry['items']) or '—'} | {entry['status'].replace('|', '/')} |")
    (ART / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'images': len(assets), 'atlasSlots': sum(len(x['items']) for x in assets),
                      'reviewFlagged': sum(bool(x['reviewNotes']) for x in assets)}))

if __name__ == '__main__':
    main()
