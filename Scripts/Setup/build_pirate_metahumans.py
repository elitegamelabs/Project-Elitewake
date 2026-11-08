"""Make the pirate survivors as MetaHumans (owner, November 7: a pirate with a real face instead of the faceless mannequin;
the creator's sliders will drive its face and body bones). Run in the visible editor, outside Play, with the owner ready to
sign in to Epic in the browser (the face rig and skin textures come from Epic's MetaHuman cloud service):
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"   (EW_QUIT_WHEN_DONE=1 quits after)
  1. MH_PirateMale and MH_PirateFemale under /Game/Elitewake/Characters/MetaHumans, bodies set by measurements
     (tuning: a weathered working sailor's proportions).
  2. Face rig (joints, so the face sliders have bones to move) and skin textures, from the cloud.
  3. Assembled with the optimized pipeline at medium quality (the GTX 1660 Super budget) into /Game/Elitewake/Characters/Survivors.
Writes Saved/PirateMetaHumans.json. Clothing comes later (a free Fab outfit, owner's choice).
"""
import json
import os
from pathlib import Path
import unreal

FOLDER = '/Game/Elitewake/Characters/MetaHumans'
BUILD = '/Game/Elitewake/Characters/Survivors'
# Body measurements in cm (tuning). Names as the body constraints report them, lower case with underscores.
BODIES = {
    'MH_PirateMale': {'height': 180.0, 'chest': 104.0, 'waist': 86.0, 'hips': 98.0, 'upper_arm_length': 34.0},
    'MH_PirateFemale': {'height': 168.0, 'chest': 92.0, 'waist': 72.0, 'hips': 100.0, 'upper_arm_length': 31.0},
}
mh = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
report = {}


def log(name, value):
    report[name] = value
    unreal.log(f'EWPIRATE {name}: {value}')


def character(name):
    asset = unreal.load_asset(f'{FOLDER}/{name}')
    if not asset:
        asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            asset_name=name, package_path=FOLDER, asset_class=unreal.MetaHumanCharacter,
            factory=unreal.new_object(type=unreal.MetaHumanCharacterFactoryNew))
    return asset


def shape(asset, measures):
    constraints = mh.get_body_constraints(asset)
    by_name = {str(c.name).lower().replace(' ', '_'): c for c in constraints}
    log(f'{asset.get_name()}.constraints', sorted(by_name))
    for key, value in measures.items():
        if key in by_name:
            by_name[key].is_active = True
            by_name[key].target_measurement = value
    mh.set_body_constraints(asset, list(by_name.values()))
    mh.commit_body_state(asset)


def cloud(asset):
    rig = unreal.MetaHumanCharacterAutoRiggingRequestParams()
    rig.blocking = True
    rig.report_progress = True
    rig.rig_type = unreal.MetaHumanRigType.JOINTS_ONLY
    mh.request_auto_rigging(asset, rig)
    textures = unreal.MetaHumanCharacterTextureRequestParams()
    textures.blocking = True
    textures.report_progress = True
    mh.request_texture_sources(asset, textures)


def build(asset):
    params = unreal.MetaHumanCharacterEditorBuildParameters()
    params.pipeline_type = unreal.MetaHumanDefaultPipelineType.OPTIMIZED
    params.pipeline_quality = unreal.MetaHumanQualityLevel.MEDIUM
    params.absolute_build_path = f'{BUILD}/{asset.get_name()}'
    params.common_folder_path = f'{BUILD}/Common'
    params.enable_wardrobe_item_validation = False
    log(f'{asset.get_name()}.can_build', str(mh.can_build_meta_human(asset)))
    mh.build_meta_human(character=asset, params=params)


ONLY = [n for n in os.environ.get('EW_PIRATES', '').split(',') if n]           # rerun some, e.g. EW_PIRATES=MH_PirateMale
STAGES = os.environ.get('EW_PIRATE_STAGES', 'shape,cloud,build').split(',')  # e.g. EW_PIRATE_STAGES=build (no sign-in)
for name, measures in BODIES.items():
    if ONLY and name not in ONLY:
        continue
    asset = character(name)
    if not mh.try_add_object_to_edit(asset):
        log(f'{name}.error', 'could not open for editing')
        continue
    try:
        for stage, fn in (('shape', lambda: shape(asset, measures)), ('cloud', lambda: cloud(asset)), ('build', lambda: build(asset))):
            if stage not in STAGES:
                continue
            try:
                fn()
                log(f'{name}.{stage}', 'done')
            except Exception as e:      # noqa: BLE001
                log(f'{name}.{stage}', f'failed: {e!r}')
    finally:
        if mh.is_object_added_for_editing(asset):
            mh.remove_object_to_edit(asset)
    unreal.EditorAssetLibrary.save_loaded_asset(asset)
built = [str(d.package_name) for d in unreal.AssetRegistryHelpers.get_asset_registry().get_assets_by_path(BUILD, recursive=True)]
log('built_assets', len(built))
report['built_sample'] = [b for b in built if 'SKM' in b or 'BP_' in b][:20]
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
Path(unreal.Paths.project_saved_dir(), 'PirateMetaHumans.json').write_text(json.dumps(report, indent=2))
if os.environ.get('EW_QUIT_WHEN_DONE') == '1':
    unreal.SystemLibrary.quit_editor()
