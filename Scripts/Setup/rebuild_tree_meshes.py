"""Rebuild the tree meshes of build_coastal_flora.py in place, without moving a tree: every tree already placed
picks up the new shape. Run after changing a tree's shape:
    UnrealEditor-Cmd.exe EW.uproject -run=pythonscript -script=<this file>
Set EW_TREES to a comma-separated list of kinds (Oak, Ash; default both).
"""
import json
import os
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_coastal_flora as F  # noqa: E402

KINDS = {'Oak': (F.oak, F.OAK, 'T_OakLeaves_v1', F.OAK_ART, 'M_OakLeaves_v1'),
         'Ash': (F.ash, F.ASH, 'T_AshLeaves_v1', F.ASH_ART, 'M_AshLeaves_v1')}


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    bark = unreal.load_asset(f'{F.FOLDER}/M_PalmBark_v1')
    assert bark, 'build_coastal_flora.py makes M_PalmBark_v1 first'
    built = {}
    for kind in os.environ.get('EW_TREES', 'Oak,Ash').split(','):
        make, shapes, texture, art, material = KINDS[kind]
        leaves = F.frond_material(F.import_texture(texture, art), f'{F.FOLDER}/{material}')
        built[kind] = [F.write_static_mesh(make(**shape), f'{F.FOLDER}/SM_{kind}_{k + 1}', [bark, leaves], 120.0).get_name()
                       for k, shape in enumerate(shapes)]
    Path(unreal.Paths.project_saved_dir(), 'TreeMeshesResult.json').write_text(json.dumps({'success': True, 'built': built}, indent=2))
    unreal.log(f'Tree meshes rebuilt: {built}')


main()
