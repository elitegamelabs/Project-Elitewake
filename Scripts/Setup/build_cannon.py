"""Build the stand-in ship's cannon and its test round shot, and stock them in the test map's ship holds.
Safe to run again. Run in the editor, outside Play, after build_ship_fittings.py and import_item_icons.py:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

- SM_CannonCarriage_v1: a wooden truck carriage on four small wheels, standing on the deck below its mount
  (cannon mounts sit 40 cm above the deck, level with the middle of the gunport).
- SM_CannonBarrel_v1: the iron barrel, its trunnions at the origin, reaching 1.5 m forward to the muzzle. It is the
  fitting's turning part: the ship aims it about the trunnions.
- DA_TestCannon: a Cannon fitting for any cannon hardpoint, loading DA_TestRoundShot.
- DA_TestRoundShot: round shot, stacking to 50 (confirmed for cannon ammo).
Both items are test placeholders: the cannon's recipe, cost, variants and art are open question 1, and their
weights are test tuning. The cannon art follows the shape of the fittings atlas's cannon until the owner's.
"""
import json
import math
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ship_geometry import Builder, make_timber_material, write_static_mesh  # noqa: E402

FOLDER = '/Game/Elitewake/World/Ships'
ITEMS = '/Game/Elitewake/Items/Testing'
ICONS = '/Game/Elitewake/UI/ItemIcons'
MAP = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
UV_TILE = 120.0
DECK = -40.0          # the deck, below the mount
MUZZLE = 150.0


def carriage():
    """Cheeks, bed, axles and wheels, from the deck up to the trunnions at the origin. The barrel points +X."""
    b = Builder()
    for y in (-19.0, 19.0):
        # Each cheek steps down toward the back, as a truck carriage's does.
        b.box((-8.0, y, DECK + 22.0), (78.0, 7.0, 24.0))
        b.box((-30.0, y, DECK + 38.0), (34.0, 7.0, 10.0))
        b.box((18.0, y, DECK + 38.0), (26.0, 7.0, 14.0))
    b.box((-8.0, 0.0, DECK + 13.0), (76.0, 32.0, 5.0))                 # bed between the cheeks
    for x in (-38.0, 22.0):
        b.tube([(x, -27.0, DECK + 12.0), (x, 27.0, DECK + 12.0)], 3.0, sides=10, iron=1.0)   # axle
        for y in (-25.0, 25.0):
            b.tube([(x, y - 3.0, DECK + 12.0), (x, y + 3.0, DECK + 12.0)], 12.0, sides=14)  # wheel
    for y in (-15.0, 15.0):
        b.tube([(0.0, y - 2.0, 0.0), (0.0, y + 4.0 * (1 if y > 0 else -1), 0.0)], 4.5, sides=10, iron=1.0)  # capsquare
    return b


def barrel():
    """Cast iron, thick at the breech and tapering to a swelled muzzle; trunnions at the origin."""
    b = Builder()
    profile = [(-52.0, 3.5), (-48.0, 6.0), (-44.0, 4.0), (-40.0, 13.0), (-10.0, 12.5), (-8.0, 13.5), (40.0, 10.5),
               (42.0, 11.5), (138.0, 8.5), (143.0, 10.5), (MUZZLE, 10.0)]
    for (x0, r0), (x1, r1) in zip(profile, profile[1:]):
        b.tube([(x0, 0.0, 0.0), (x1, 0.0, 0.0)], lambda k, a=r0, c=r1: (a, c)[k], sides=16, iron=1.0)
    b.tube([(0.0, -16.0, 0.0), (0.0, 16.0, 0.0)], 4.0, sides=10, iron=1.0)          # trunnions
    b.tube([(MUZZLE - .5, 0.0, 0.0), (MUZZLE + .5, 0.0, 0.0)], 5.5, sides=16, iron=1.0, capped=True)  # bore's dark face
    return b


def data_asset(name):
    path = f'{ITEMS}/{name}'
    asset = unreal.load_asset(path)
    if asset:
        return asset
    factory = unreal.DataAssetFactory()
    factory.set_editor_property('data_asset_class', unreal.EWItemDefinition)
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, ITEMS, unreal.EWItemDefinition, factory)
    assert asset, name
    return asset


def configure(item, values):
    for k, v in values.items():
        item.set_editor_property(k, v)
    assert unreal.EditorAssetLibrary.save_loaded_asset(item, False)
    return item


def stock_kit(cannon, shot):
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    assert level.load_level(MAP)
    kit = next((a for a in actors.get_all_level_actors() if isinstance(a, unreal.EWStarterKit)), None)
    assert kit, 'no test starter kit in the coastal map'
    cargo = list(kit.get_editor_property('ship_cargo'))
    for item, quantity in ((cannon, 1), (shot, 20)):   # a cannon per hardpoint; shot in every hold
        if not any(e.get_editor_property('item') == item for e in cargo):
            entry = unreal.EWStarterKitItem()
            entry.set_editor_property('item', item)
            entry.set_editor_property('quantity', quantity)
            cargo.append(entry)
    kit.set_editor_property('ship_cargo', cargo)
    assert level.save_current_level()
    return [f"{e.get_editor_property('quantity')} x {e.get_editor_property('item').get_name()}" for e in cargo]


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    timber = make_timber_material()
    carriage_mesh = write_static_mesh(carriage(), f'{FOLDER}/SM_CannonCarriage_v1', [timber], UV_TILE, collision=False)
    barrel_mesh = write_static_mesh(barrel(), f'{FOLDER}/SM_CannonBarrel_v1', [timber], UV_TILE, collision=False)
    shot = configure(data_asset('DA_TestRoundShot'), {
        'item_id': 'Test.RoundShot', 'display_name': 'Round Shot', 'category': unreal.EWItemCategory.AMMUNITION,
        'max_stack_size': 50, 'unit_weight': 2.0, 'icon': unreal.load_asset(f'{ICONS}/T_Icon_CannonAmmo_v1'),
        'description': 'Cast-iron shot for a ship’s cannon. Test fixture: its recipe and cost are open; weight is test tuning.'})
    cannon = configure(data_asset('DA_TestCannon'), {
        'item_id': 'Test.Cannon', 'display_name': 'Cannon', 'category': unreal.EWItemCategory.MISCELLANEOUS,
        'max_stack_size': 1, 'unit_weight': 60.0, 'icon': unreal.load_asset(f'{ICONS}/T_Icon_Cannon_v1'),
        'fitting_mount_type': unreal.EWShipMountType.CANNON, 'fitting_mesh': carriage_mesh,
        'fitting_mesh_transform': unreal.Transform(), 'fitting_turning_mesh': barrel_mesh,
        'fitting_turning_pivot': unreal.Transform(), 'cannon_ammo': shot, 'cannon_muzzle_length': MUZZLE,
        'description': 'A ship’s cannon for a gunport. Fit it at a cannon hardpoint, man it, and it loads the round '
                       'shot you carry. Test fixture: recipe, cost, variants and art are open; weight is test tuning.'})
    cargo = stock_kit(cannon, shot)
    Path(unreal.Paths.project_saved_dir(), 'CannonResult.json').write_text(json.dumps({'success': True, 'ship_cargo': cargo}, indent=2))
    unreal.log('Cannon built')


if __name__ == '__main__':
    main()
