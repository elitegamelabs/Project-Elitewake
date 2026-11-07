"""Rebuild the tree meshes of build_coastal_flora.py in place, without moving a tree: every tree already placed
picks up the new shape. Run after changing a tree's shape:
    UnrealEditor-Cmd.exe EW.uproject -run=pythonscript -script=<this file>
Set EW_TREES to a comma-separated list of kinds (Oak, Ash, Birch, Spruce, Maravai; default Oak,Ash), and
EW_SNOW_PLANTS=1 to rebuild the Winter plants' snowy leaf material too.
"""
import json
import os
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_coastal_flora as F  # noqa: E402

# Kind: (shape builder, shapes, leaf texture, its art, leaf material, snow on the leaves, bark material name or None for
# the shared palm bark).
KINDS = {'Oak': (F.oak, F.OAK, 'T_OakLeaves_v1', F.OAK_ART, 'M_OakLeaves_v1', False, None),
         'Ash': (F.ash, F.ASH, 'T_AshLeaves_v1', F.ASH_ART, 'M_AshLeaves_v1', False, None),
         'Birch': (F.birch, F.BIRCH, 'T_BirchLeaves_v1', F.BIRCH_ART, 'M_BirchLeaves_v1', True, 'birch'),
         'Spruce': (F.spruce, F.SPRUCE, 'T_SpruceNeedles_v1', F.SPRUCE_ART, 'M_SpruceNeedles_v1', False, None),
         'Maravai': (F.maravai, F.MARAVAI, 'T_MaravaiLeaves_v1', F.LEAF_ART, 'M_MaravaiLeaves_v1', False, None)}


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    bark = unreal.load_asset(f'{F.FOLDER}/M_PalmBark_v1')
    assert bark, 'build_coastal_flora.py makes M_PalmBark_v1 first'
    built = {}
    for kind in os.environ.get('EW_TREES', 'Oak,Ash').split(','):
        make, shapes, texture, art, material, snow, bark_kind = KINDS[kind]
        leaves = F.frond_material(F.import_texture(texture, art), f'{F.FOLDER}/{material}', snow=snow)
        trunk = F.birch_bark_material() if bark_kind == 'birch' else bark
        built[kind] = [F.write_tree_mesh(make, shape, f'{F.FOLDER}/SM_{kind}_{k + 1}', [trunk, leaves]).get_name()
                       for k, shape in enumerate(shapes)]
    if os.environ.get('EW_SNOW_PLANTS'):
        # The Winter plants' snowy leaf material shares the leaves' snow.
        F.frond_material(F.import_texture('T_PalmFrond_v1', F.FROND_ART), f'{F.FOLDER}/M_PalmFrondSnow_v1', snow=True)
    Path(unreal.Paths.project_saved_dir(), 'TreeMeshesResult.json').write_text(json.dumps({'success': True, 'built': built}, indent=2))
    unreal.log(f'Tree meshes rebuilt: {built}')


main()
