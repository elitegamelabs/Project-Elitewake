"""Read-only: what the pirate MetaHumans are made of (bones of body and face, the blueprint's parts and their anim classes),
to map the creator's sliders onto them. Writes Saved/PirateAnatomy.json.
    UnrealEditor-Cmd.exe EW.uproject -run=pythonscript -script=<this file>
"""
import json
from pathlib import Path
import unreal

BUILD = '/Game/Elitewake/Characters/Survivors'
out = {}
for name in ('MH_PirateMale', 'MH_PirateFemale'):
    entry = {}
    for part in ('Body', 'Face'):
        mesh = unreal.load_asset(f'{BUILD}/{name}/{name}/{part}/SKM_{name}_{part}Mesh')
        if not mesh:
            entry[part] = None
            continue
        skeleton = mesh.get_editor_property('skeleton')
        bones = [str(b) for b in unreal.EWEditorVerificationLibrary.get_skeleton_bone_names(mesh)] if hasattr(unreal.EWEditorVerificationLibrary, 'get_skeleton_bone_names') else []
        entry[part] = {'skeleton': skeleton.get_path_name() if skeleton else None, 'bones': len(bones), 'names': bones,
                       'materials': [m.get_editor_property('material_interface').get_path_name() if m.get_editor_property('material_interface') else None
                                     for m in mesh.get_editor_property('materials')],
                       'morphs': [str(m.get_name()) for m in mesh.get_editor_property('morph_targets')][:400]}
    bp = unreal.load_asset(f'{BUILD}/{name}/{name}/BP_{name}')
    gen = bp.generated_class() if bp else None
    cdo = unreal.get_default_object(gen) if gen else None
    comps = []
    if bp:
        sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        for handle in sub.k2_gather_subobject_data_for_blueprint(bp):
            data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
            obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data)
            if obj:
                info = {'name': obj.get_name(), 'class': obj.get_class().get_name()}
                try:
                    info['anim_class'] = str(obj.get_editor_property('anim_class'))
                    info['mesh'] = obj.get_editor_property('skeletal_mesh_asset').get_path_name() if obj.get_editor_property('skeletal_mesh_asset') else None
                except Exception:      # noqa: BLE001
                    pass
                comps.append(info)
    entry['blueprint'] = {'class': gen.get_path_name() if gen else None, 'components': comps}
    out[name] = entry
Path(unreal.Paths.project_saved_dir(), 'PirateAnatomy.json').write_text(json.dumps(out, indent=1))
unreal.log('Pirate anatomy written')

