"""Rebuild the tree materials (bark and leaves) with the felled-tree fade parameter. Safe to run again; changes the materials
in place, so the tree meshes and placed trees keep working. Run in the editor outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"
Writes Saved/TreeMaterialsResult.json and quits the editor."""
import json
from pathlib import Path
import sys
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_coastal_flora as F  # noqa: E402

report = {'built': [], 'error': None}
try:
    F.bark_material()
    F.birch_bark_material()
    for name, art, path, snow in (
            ('T_PalmFrond_v1', F.FROND_ART, f'{F.FOLDER}/M_PalmFrond_v1', False),
            ('T_PalmFrond_v1', F.FROND_ART, f'{F.FOLDER}/M_PalmFrondSnow_v1', True),
            ('T_MaravaiLeaves_v1', F.LEAF_ART, f'{F.FOLDER}/M_MaravaiLeaves_v1', False),
            ('T_OakLeaves_v1', F.OAK_ART, f'{F.FOLDER}/M_OakLeaves_v1', False),
            ('T_AshLeaves_v1', F.ASH_ART, f'{F.FOLDER}/M_AshLeaves_v1', False),
            ('T_BirchLeaves_v1', F.BIRCH_ART, f'{F.FOLDER}/M_BirchLeaves_v1', True),
            ('T_SpruceNeedles_v1', F.SPRUCE_ART, f'{F.FOLDER}/M_SpruceNeedles_v1', False)):
        F.frond_material(F.import_texture(name, art), path, snow=snow)
        report['built'].append(path)
except Exception as error:      # noqa: BLE001
    import traceback
    report['error'] = traceback.format_exc()
(Path(unreal.Paths.project_saved_dir()) / 'TreeMaterialsResult.json').write_text(json.dumps(report, indent=2))
unreal.SystemLibrary.quit_editor()
