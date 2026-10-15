"""Prepare the coastal map's sun for day and night (Source/EW/World/EWDayNight.*). Safe to run again. Run in the
editor outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

The sky clock moves the directional light tagged EWSun on every machine, so the map's sun is tagged, made movable
and kept as the atmosphere's first light (the clock adds the moon as the second). Maps without a tagged sun, such as
the title, keep their own lighting.
"""
import unreal

MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert level.load_level(MAP)
    suns = [a for a in actors.get_all_level_actors() if isinstance(a, unreal.DirectionalLight)]
    assert len(suns) == 1, f'expected one sun, found {len(suns)}'
    sun = suns[0]
    tags = list(sun.tags)
    if 'EWSun' not in [str(t) for t in tags]:
        sun.tags = tags + [unreal.Name('EWSun')]
    light = sun.get_component_by_class(unreal.DirectionalLightComponent)
    sun.root_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    light.set_editor_property('atmosphere_sun_light', True)
    light.set_editor_property('atmosphere_sun_light_index', 0)
    assert level.save_current_level()
    unreal.log('Day and night: sun tagged')


if __name__ == '__main__':
    main()
