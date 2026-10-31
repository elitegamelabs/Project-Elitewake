"""Build an index of source artwork without changing any image pixels."""
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / 'Art'
ANIMAL_PROTOTYPES = {'american_alligator', 'cottonmouth', 'monkey'}


def classify_png(relative, meta):
    """Return an honest art status and implementation class for an indexed source image."""
    parts = Path(relative).parts
    status = meta.get('status', 'Existing source reference; consult adjacent selection/roster metadata and CLAUDE.md')
    classification = 'reference'
    warnings = []

    if parts[:3] == ('Art', 'Flora', 'Growth'):
        classification = 'pending-model'
        status = 'DRAFT reference: species identity needs correction before modeling or runtime use'
        warnings.append('The first growth board does not faithfully match the requested species rows; remaining boards are not generated.')
    elif parts[:3] == ('Art', 'Fauna', 'Fish'):
        classification = 'generated-in-editor-draft'
        status = 'Generated cutout and procedural mesh input; editor-built creature assets still need visual review'
    elif parts[:2] == ('Art', 'Flora'):
        classification = 'generated-in-editor-draft'
        status = 'Generated leaf-card texture used by editor-built vegetation drafts; this is not a tree mesh'
    elif parts[:3] == ('Art', 'Concepts', 'Animals'):
        if Path(relative).stem in ANIMAL_PROTOTYPES:
            classification = 'reference'
            status = 'Reference for an existing coastal prototype; compare the in-game model against this image'
        else:
            classification = 'pending-model'
            status = '2D animal modeling reference; follow the roster and milestones for per-species model status'
    elif parts[:3] == ('Art', 'Items', 'Icons'):
        classification = 'in-game-art-source'
        status = ('Review sheet of the cut inventory icons' if Path(relative).name == 'contact-sheet.png' else
                  'In-game inventory icon source cut from a reviewed atlas cell; visual polish remains reviewable')
    elif parts[:3] == ('Art', 'UI', 'Survival'):
        if 'Matte-v2' not in parts:
            classification = 'legacy'
            status = 'Legacy art; newer version preferred'
        else:
            classification = 'in-game-art-source'
            status = 'Updated survival indicator art source; rendered appearance still needs visual review'

    if Path(relative).name == 'Brigantine-Exterior-Mast-Sockets-v2.png':
        classification = 'reference'
        status = 'Alternate reference only; owner-selected original hulls remain canonical'
    if 'insects1-Atlas' in relative:
        warnings.append('Bloodwing depiction needs anatomy review against the mosquito-like guide description.')
    if 'blueprints-Atlas' in relative:
        warnings.append('Decorative diagram references only; wooden-tool drawing needs material correction.')
    if 'forage3-Atlas-v1' in relative:
        classification = 'legacy'
        status = 'Legacy art; version 2 is preferred'
    return classification, status, warnings


def editor_folder_statuses():
    """Summarize selected generated Unreal folders without implying the drafts are final art."""
    folders = [
        ('Content/Elitewake/Wildlife/Animals', 'generated-in-editor-draft',
         'Six coastal land-animal prototypes; the owner roster contains additional species.'),
        ('Content/Elitewake/Wildlife/Fish', 'generated-in-editor-draft',
         'Procedural aquatic-creature prototypes sourced from Art/Fauna/Fish; visual review remains open.'),
        ('Content/Elitewake/World/Flora', 'generated-in-editor-draft',
         'Editor-built vegetation prototypes using Art/Flora leaf textures; not a complete regional flora set.'),
        ('Content/Elitewake/World/Rocks', 'generated-in-editor-draft',
         'Editor-built rock variants; art and placement remain prototype content.'),
        ('Content/Elitewake/World/Materials', 'generated-in-editor-draft',
         'World material and texture prototypes; not final art approval.'),
        ('Content/Elitewake/Animations/Tools', 'generated-in-editor-draft',
         'Imported or configured animation assets; motion and retargeting need in-game review.'),
    ]
    result = []
    for relative, status, notes in folders:
        folder = ROOT / relative
        if folder.is_dir():
            files = [path.relative_to(ROOT).as_posix() for path in sorted(folder.rglob('*.uasset'))]
            result.append({'path': relative, 'status': status, 'assetCount': len(files), 'assets': files, 'notes': notes})
    return result


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
        classification, status, warnings = classify_png(relative, meta)
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
                       'dimensions': size, 'alphaRange': alpha, 'classification': classification, 'status': status,
                       'metadata': sidecar.relative_to(ROOT).as_posix() if sidecar.exists() else None,
                       'columns': columns, 'rows': rows, 'items': slots, 'reviewNotes': warnings})
    catalog = {'version': 1, 'purpose': 'Original Elitewake 2D source art and modeling references',
               'limitations': 'Images are not 3D meshes, rigs, animations or proof of gameplay integration. Atlas UVs are equal-cell reference regions, not final sprite packing.',
               'authority': 'CLAUDE.md',
               'classificationGuide': {
                   'reference': '2D source art or concept art; it is not a runtime 3D asset.',
                   'generated-in-editor-draft': 'Generated or imported Unreal prototype content; it still needs in-game visual review.',
                   'pending-model': 'A modeling reference or growth-stage brief whose corresponding model work remains tracked separately.',
                   'in-game-art-source': 'A source image used by a current UI implementation; visual polish is still reviewable.',
                   'legacy': 'Older source art retained for history; a newer version is preferred.'},
               'generatedEditorFolders': editor_folder_statuses(),
               'assets': assets}
    (ART / 'CATALOG.json').write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'images': len(assets), 'atlasSlots': sum(len(x['items']) for x in assets),
                      'classifications': {kind: sum(x['classification'] == kind for x in assets)
                                          for kind in sorted({x['classification'] for x in assets})},
                      'generatedEditorFolders': len(catalog['generatedEditorFolders']),
                      'reviewFlagged': sum(bool(x['reviewNotes']) for x in assets)}))

if __name__ == '__main__':
    main()
