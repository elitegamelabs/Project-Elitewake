"""Import the draft sounds in Art/Audio and give the animals their calls.
Safe to run again: sounds are re-imported over themselves, so a new take replaces them.
    UnrealEditor-Cmd.exe EW.uproject -run=pythonscript -script=<this file>

The sounds are drafts generated through the owner's Scenario account (Sonilo V1.1 Text to SFX, October 15), never
final audio. Each lands at /Game/Elitewake/Audio/<folder>/S_<name>_v1. One-shots fall off with distance through
SA_World_v1, and the cannon's report and its shot's landing through SA_Far_v1; the soundscape's loops are heard
everywhere (it fades them), a ship's loops fall off with distance from her. Levels even out the takes, which came
back at very different loudness, and are tuning.
"""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
SOURCE = ROOT / 'Art/Audio'
FOLDER = '/Game/Elitewake/Audio'
ANIMALS = '/Game/Elitewake/Wildlife/Animals'
# Source file (Art/Audio/<folder>/<file>) -> asset name, volume, and how it plays: 'world' falls off with distance,
# 'far' too but carries across the water, 'loop' loops everywhere, 'worldloop' loops falling off with distance,
# 'flat' plays once everywhere.
SOUNDS = {
    'Work/SFX_ChopWood-v1.wav': ('S_ChopWood_v1', .8, 'world'),
    'Work/SFX_PickaxeStone-v1.wav': ('S_PickaxeStone_v1', .8, 'world'),
    'Work/SFX_GlanceClink-v1.wav': ('S_GlanceClink_v1', 1.2, 'world'),
    'Gather/SFX_GatherRustle-v1.wav': ('S_GatherRustle_v1', 1.4, 'world'),
    'Gather/SFX_Pickup-v1.wav': ('S_Pickup_v1', 2.5, 'flat'),
    'Footsteps/SFX_StepSand-v1.wav': ('S_StepSand_v1', .9, 'world'),
    'Footsteps/SFX_StepSand-v1b.wav': ('S_StepSand_v1b', .9, 'world'),
    'Footsteps/SFX_StepSnow-v1.wav': ('S_StepSnow_v1', .6, 'world'),
    # The loops are the v1 takes cross-faded end into start (Scripts/Art/make_audio_loops.py), so no seam is heard.
    'Ambience/AMB_OceanSurf-v2.wav': ('S_AmbOceanSurf_v2', 1.0, 'loop'),
    'Ambience/AMB_WinterWind-v2.wav': ('S_AmbWinterWind_v2', 1.4, 'loop'),
    'Ambience/AMB_Seabirds-v1.wav': ('S_AmbSeabirds_v1', 3.0, 'flat'),
    'Fauna/SFX_AlligatorHiss-v1.wav': ('S_AlligatorHiss_v1', .7, 'world'),
    'Fauna/SFX_AlligatorHiss-v1b.wav': ('S_AlligatorHiss_v1b', .7, 'world'),
    'Fauna/SFX_FlamingoCall-v1.wav': ('S_FlamingoCall_v1', .7, 'world'),
    'Fauna/SFX_PelicanCall-v1.wav': ('S_PelicanCall_v1', 1.0, 'world'),
    # The four regional animals (October 26): their main calls; the other calls in SCENARIO.md's queue are still to make.
    'Fauna/SFX_BearGrowl-v1.wav': ('S_BearGrowl_v1', .9, 'world'),
    'Fauna/SFX_LionRoar-v1.wav': ('S_LionRoar_v1', 1.0, 'far'),
    'Fauna/SFX_CrocodileBellow-v1.wav': ('S_CrocodileBellow_v1', .9, 'world'),
    'Fauna/SFX_ElephantTrumpet-v1.wav': ('S_ElephantTrumpet_v1', 1.0, 'far'),
    # The second batch (October 15 night): ships, decks, swimming, night and caves.
    'Ships/SFX_CannonFire-v1.wav': ('S_CannonFire_v1', .9, 'far'),
    'Ships/SFX_HullHit-v1.wav': ('S_HullHit_v1', .8, 'far'),
    'Ships/SFX_ShotSplash-v1.wav': ('S_ShotSplash_v1', .9, 'far'),
    'Ships/SFX_Bail-v1.wav': ('S_Bail_v1', 1.0, 'world'),
    'Ships/SFX_ShipSinking-v1.wav': ('S_ShipSinking_v1', .8, 'far'),
    'Ships/AMB_HullCreak-v2.wav': ('S_AmbHullCreak_v2', .7, 'worldloop'),
    'Ships/AMB_Rigging-v2.wav': ('S_AmbRigging_v2', .8, 'worldloop'),
    'Footsteps/SFX_StepDeck-v1.wav': ('S_StepDeck_v1', .6, 'world'),
    'Footsteps/SFX_StepDeck-v1b.wav': ('S_StepDeck_v1b', 1.2, 'world'),
    'Swimming/SFX_SwimStroke-v1.wav': ('S_SwimStroke_v1', 1.0, 'world'),
    'Ambience/AMB_NightInsects-v2.wav': ('S_AmbNightInsects_v2', .5, 'loop'),
    'Ambience/AMB_CaveDrips-v2.wav': ('S_AmbCaveDrips_v2', 1.2, 'loop'),
    # The third batch (October 16): steps on grass and stone, and each wooded region's own sound.
    'Footsteps/SFX_StepGrass-v1.wav': ('S_StepGrass_v1', 1.4, 'world'),
    'Footsteps/SFX_StepStone-v1.wav': ('S_StepStone_v1', .9, 'world'),
    'Ambience/AMB_ForestWind-v2.wav': ('S_AmbForestWind_v2', 1.0, 'loop'),
    'Ambience/AMB_JungleDay-v2.wav': ('S_AmbJungleDay_v2', .6, 'loop'),
    'Ambience/AMB_SwampFrogs-v2.wav': ('S_AmbSwampFrogs_v2', 1.2, 'loop'),
    # The fourth batch (October 16): the anchor's chain running out, catching on the bottom, and hove in at the capstan.
    'Ships/SFX_AnchorDrop-v1.wav': ('S_AnchorDrop_v1', .9, 'far'),
    'Ships/SFX_AnchorCatch-v1.wav': ('S_AnchorCatch_v1', .9, 'far'),
    'Ships/SFX_AnchorRaise-v1.wav': ('S_AnchorRaise_v1', .9, 'far'),
    # Saltreach Freeport (October 30): synthesized placeholders, made by Scripts/Art/make_town_sounds.py (no credits, nothing sampled).
    'Town/AMB_TavernMurmur-v1.wav': ('S_AmbTavernMurmur_v1', .8, 'worldloop'),
    'Town/AMB_MarketMurmur-v1.wav': ('S_AmbMarketMurmur_v1', .7, 'worldloop'),
    'Town/AMB_ShipyardWork-v1.wav': ('S_AmbShipyardWork_v1', 1.0, 'worldloop'),
    'Town/AMB_PierLapping-v1.wav': ('S_AmbPierLapping_v1', .8, 'worldloop'),
    'Town/SFX_HarborBell-v1.wav': ('S_HarborBell_v1', .8, 'far'),
    # The cave spider (October 30): synthesized by Scripts/Art/make_creature_sounds.py.
    'Fauna/SFX_SpiderChitter-v1.wav': ('S_SpiderChitter_v1', .9, 'world'),
    'Fauna/SFX_SpiderHiss-v1.wav': ('S_SpiderHiss_v1', 1.0, 'world'),
    'Fauna/SFX_SpiderDeath-v1.wav': ('S_SpiderDeath_v1', .9, 'world'),
}
# Animal -> its calls and the seconds between them while it goes about its day (0: only when provoked).
CALLS = {
    'Alligator': (['S_AlligatorHiss_v1', 'S_AlligatorHiss_v1b'], (0, 0)),
    'Flamingo': (['S_FlamingoCall_v1'], (20, 45)),
    'Pelican': (['S_PelicanCall_v1'], (30, 60)),
    'Bear': (['S_BearGrowl_v1'], (0, 0)),
    'Lion': (['S_LionRoar_v1'], (40, 90)),
    'GiantCrocodile': (['S_CrocodileBellow_v1'], (0, 0)),
    'Elephant': (['S_ElephantTrumpet_v1'], (45, 100)),
    'Spider': (['S_SpiderChitter_v1'], (25, 60)),
}
# Animal -> its attack and death sounds (October 30; species without their own are silent there for now).
STRIKES = {'Spider': (['S_SpiderHiss_v1'], ['S_SpiderDeath_v1'])}
# Falloff (tuning): world sounds are full within 4 m and gone by 40 m; far ones full within 20 m, gone by 400 m.
FALLOFFS = {'SA_World_v1': (400.0, 3600.0), 'SA_Far_v1': (2000.0, 38000.0)}


def attenuation(name):
    inner, falloff = FALLOFFS[name]
    asset = unreal.load_asset(f'{FOLDER}/{name}') or unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, FOLDER, unreal.SoundAttenuation, unreal.SoundAttenuationFactory())
    settings = asset.get_editor_property('attenuation')
    settings.set_editor_property('attenuation_shape', unreal.AttenuationShape.SPHERE)
    settings.set_editor_property('attenuation_shape_extents', unreal.Vector(inner, 0, 0))
    settings.set_editor_property('falloff_distance', falloff)
    settings.set_editor_property('distance_algorithm', unreal.AttenuationDistanceModel.NATURAL_SOUND)
    asset.set_editor_property('attenuation', settings)
    assert unreal.EditorAssetLibrary.save_loaded_asset(asset)
    return asset


def import_sound(source, name, volume, mode, falloffs):
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
    wave.set_editor_property('looping', mode in ('loop', 'worldloop'))
    wave.set_editor_property('attenuation_settings', falloffs['SA_Far_v1'] if mode == 'far' else
                             falloffs['SA_World_v1'] if mode in ('world', 'worldloop') else None)
    if mode in ('loop', 'worldloop'):
        # A loop faded right down keeps playing, so it comes back where it was instead of restarting.
        wave.set_editor_property('virtualization_mode', unreal.VirtualizationMode.PLAY_WHEN_SILENT)
    assert unreal.EditorAssetLibrary.save_loaded_asset(wave)
    return wave


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    falloffs = {name: attenuation(name) for name in FALLOFFS}
    waves = {name: import_sound(source, name, volume, mode, falloffs) for source, (name, volume, mode) in SOUNDS.items()}
    called = {}
    for animal, (calls, interval) in CALLS.items():
        definition = unreal.load_asset(f'{ANIMALS}/DA_Animal_{animal}')
        assert definition, animal
        definition.set_editor_property('calls', [waves[c] for c in calls])
        definition.set_editor_property('call_interval', unreal.Vector2D(*interval))
        assert unreal.EditorAssetLibrary.save_loaded_asset(definition)
        called[animal] = calls
    for animal, (attacks, deaths) in STRIKES.items():
        definition = unreal.load_asset(f'{ANIMALS}/DA_Animal_{animal}')
        assert definition, animal
        definition.set_editor_property('attack_sounds', [waves[c] for c in attacks])
        definition.set_editor_property('death_sounds', [waves[c] for c in deaths])
        assert unreal.EditorAssetLibrary.save_loaded_asset(definition)
    result = {'success': True, 'sounds': {n: round(w.get_editor_property('duration'), 2) for n, w in waves.items()}, 'calls': called}
    (ROOT / 'Saved/AudioImportResult.json').write_text(json.dumps(result, indent=2))
    unreal.log(f'Imported {len(waves)} sounds and gave {len(called)} animals their calls')


if __name__ == '__main__':
    main()
