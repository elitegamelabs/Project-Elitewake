"""Import the draft sounds in Art/Audio and give the animals their calls.
Safe to run again: sounds are re-imported over themselves, so a new take replaces them.
    UnrealEditor-Cmd.exe EW.uproject -run=pythonscript -script=<this file>

The sounds are drafts generated through the owner's Scenario account (Sonilo V1.1 Text to SFX, October 15), never
final audio. Each lands at /Game/Elitewake/Audio/<folder>/S_<name>_v1. One-shots fall off with distance through
SA_World_v1; the surf and wind loop and are heard everywhere (the soundscape fades them). Levels even out the takes,
which came back at very different loudness, and are tuning.
"""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
SOURCE = ROOT / 'Art/Audio'
FOLDER = '/Game/Elitewake/Audio'
ANIMALS = '/Game/Elitewake/Wildlife/Animals'
# Source file (Art/Audio/<folder>/<file>) -> asset name, volume, and how it plays: 'world' falls off with distance,
# 'loop' loops everywhere, 'flat' plays once everywhere.
SOUNDS = {
    'Work/SFX_ChopWood-v1.wav': ('S_ChopWood_v1', .8, 'world'),
    'Work/SFX_PickaxeStone-v1.wav': ('S_PickaxeStone_v1', .8, 'world'),
    'Work/SFX_GlanceClink-v1.wav': ('S_GlanceClink_v1', 1.2, 'world'),
    'Gather/SFX_GatherRustle-v1.wav': ('S_GatherRustle_v1', 1.4, 'world'),
    'Gather/SFX_Pickup-v1.wav': ('S_Pickup_v1', 2.5, 'flat'),
    'Footsteps/SFX_StepSand-v1.wav': ('S_StepSand_v1', .9, 'world'),
    'Footsteps/SFX_StepSand-v1b.wav': ('S_StepSand_v1b', .9, 'world'),
    'Footsteps/SFX_StepSnow-v1.wav': ('S_StepSnow_v1', .6, 'world'),
    'Ambience/AMB_OceanSurf-v1.wav': ('S_AmbOceanSurf_v1', 1.0, 'loop'),
    'Ambience/AMB_WinterWind-v1.wav': ('S_AmbWinterWind_v1', 1.4, 'loop'),
    'Ambience/AMB_Seabirds-v1.wav': ('S_AmbSeabirds_v1', 3.0, 'flat'),
    'Fauna/SFX_AlligatorHiss-v1.wav': ('S_AlligatorHiss_v1', .7, 'world'),
    'Fauna/SFX_AlligatorHiss-v1b.wav': ('S_AlligatorHiss_v1b', .7, 'world'),
    'Fauna/SFX_FlamingoCall-v1.wav': ('S_FlamingoCall_v1', .7, 'world'),
    'Fauna/SFX_PelicanCall-v1.wav': ('S_PelicanCall_v1', 1.0, 'world'),
}
# Animal -> its calls and the seconds between them while it goes about its day (0: only when provoked).
CALLS = {
    'Alligator': (['S_AlligatorHiss_v1', 'S_AlligatorHiss_v1b'], (0, 0)),
    'Flamingo': (['S_FlamingoCall_v1'], (20, 45)),
    'Pelican': (['S_PelicanCall_v1'], (30, 60)),
}
# Heard at full strength within 4 m, fading out by 40 m (tuning).
INNER, FALLOFF = 400.0, 3600.0


def attenuation():
    path = f'{FOLDER}/SA_World_v1'
    asset = unreal.load_asset(path) or unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        'SA_World_v1', FOLDER, unreal.SoundAttenuation, unreal.SoundAttenuationFactory())
    settings = asset.get_editor_property('attenuation')
    settings.set_editor_property('attenuation_shape', unreal.AttenuationShape.SPHERE)
    settings.set_editor_property('attenuation_shape_extents', unreal.Vector(INNER, 0, 0))
    settings.set_editor_property('falloff_distance', FALLOFF)
    settings.set_editor_property('distance_algorithm', unreal.AttenuationDistanceModel.NATURAL_SOUND)
    asset.set_editor_property('attenuation', settings)
    assert unreal.EditorAssetLibrary.save_loaded_asset(asset)
    return asset


def import_sound(source, name, volume, mode, falloff):
    filename = SOURCE / source
    assert filename.is_file(), filename
    folder = f'{FOLDER}/{source.split("/")[0]}'
    task = unreal.AssetImportTask()
    for k, v in {'filename': str(filename), 'destination_path': folder, 'destination_name': name,
                 'automated': True, 'replace_existing': True, 'save': True}.items():
        task.set_editor_property(k, v)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    wave = unreal.load_asset(f'{folder}/{name}')
    assert isinstance(wave, unreal.SoundWave), name
    wave.set_editor_property('volume', volume)
    wave.set_editor_property('looping', mode == 'loop')
    wave.set_editor_property('attenuation_settings', falloff if mode == 'world' else None)
    if mode == 'loop':
        # A loop faded right down keeps playing, so it comes back where it was instead of restarting.
        wave.set_editor_property('virtualization_mode', unreal.VirtualizationMode.PLAY_WHEN_SILENT)
    assert unreal.EditorAssetLibrary.save_loaded_asset(wave)
    return wave


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    falloff = attenuation()
    waves = {name: import_sound(source, name, volume, mode, falloff) for source, (name, volume, mode) in SOUNDS.items()}
    called = {}
    for animal, (calls, interval) in CALLS.items():
        definition = unreal.load_asset(f'{ANIMALS}/DA_Animal_{animal}')
        assert definition, animal
        definition.set_editor_property('calls', [waves[c] for c in calls])
        definition.set_editor_property('call_interval', unreal.Vector2D(*interval))
        assert unreal.EditorAssetLibrary.save_loaded_asset(definition)
        called[animal] = calls
    result = {'success': True, 'sounds': {n: round(w.get_editor_property('duration'), 2) for n, w in waves.items()}, 'calls': called}
    (ROOT / 'Saved/AudioImportResult.json').write_text(json.dumps(result, indent=2))
    unreal.log(f'Imported {len(waves)} sounds and gave {len(called)} animals their calls')


if __name__ == '__main__':
    main()
