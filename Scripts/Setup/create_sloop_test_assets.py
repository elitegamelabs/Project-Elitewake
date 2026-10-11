"""Create the first sloop: ship definition, helm and sail test fittings, and one bare hull in the coastal map.

Follows the ship model in Docs/DESIGN_REFERENCE.md#ship-model: a complete hull with a helm mount, a Medium
mainsail mount, a Small headsail mount and the two confirmed cannon hardpoints. The hull starts bare.
Sizes, weights and speeds are labelled test tuning, not balance.

Run outside Play, from the editor's Python console or headless:
UnrealEditor-Cmd.exe EW.uproject -run=pythonscript -script=<this file>
Existing assets and an existing placed ship are kept, never overwritten.
"""
import json
from pathlib import Path
import unreal

assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play before saving fixtures.'
tools = unreal.AssetToolsHelpers.get_asset_tools()

def data_asset(folder, name, cls, configure):
    asset = unreal.load_asset(f'{folder}/{name}')
    if asset:
        return asset, False
    factory = unreal.DataAssetFactory()
    factory.set_editor_property('data_asset_class', cls)
    asset = tools.create_asset(name, folder, cls, factory)
    assert asset, name
    configure(asset)
    assert unreal.EditorAssetLibrary.save_loaded_asset(asset)
    return asset, True

def fitting(name, item_id, display, mount_type, sail_size, weight):
    def configure(item):
        item.set_editor_property('item_id', item_id)
        item.set_editor_property('display_name', display)
        item.set_editor_property('category', unreal.EWItemCategory.MISCELLANEOUS)
        item.set_editor_property('max_stack_size', 1)
        item.set_editor_property('unit_weight', weight)
        item.set_editor_property('fitting_mount_type', mount_type)
        item.set_editor_property('fitting_sail_size', sail_size)
        item.set_editor_property('description', 'Ship fitting test fixture. Weight is test tuning; recipe, station cost and art pending.')
    return data_asset('/Game/Elitewake/Items/Testing', name, unreal.EWItemDefinition, configure)

created = []
items = {}
for name, item_id, display, mount_type, size, weight in (
        ('DA_TestShipHelm', 'Test.ShipHelm', "Ship's Wheel", unreal.EWShipMountType.HELM, unreal.EWSailSize.NONE, 25.0),
        ('DA_TestSailSmall', 'Test.SailSmall', 'Small Sail', unreal.EWShipMountType.SAIL, unreal.EWSailSize.SMALL, 15.0),
        ('DA_TestSailMedium', 'Test.SailMedium', 'Medium Sail', unreal.EWShipMountType.SAIL, unreal.EWSailSize.MEDIUM, 30.0)):
    items[name], new = fitting(name, item_id, display, mount_type, size, weight)
    if new:
        created.append(name)

def mount(mount_id, mount_type, location, size=unreal.EWSailSize.NONE):
    m = unreal.EWShipMount()
    m.set_editor_property('mount_id', mount_id)
    m.set_editor_property('type', mount_type)
    m.set_editor_property('sail_size', size)
    m.set_editor_property('transform', unreal.Transform(location=unreal.Vector(*location)))
    return m

def configure_sloop(ship):
    ship.set_editor_property('ship_id', 'Sloop')
    ship.set_editor_property('display_name', 'Sloop')
    # About 10 m long, 3.2 m beam and 2 m deep; deck top at +100 cm. Test tuning.
    ship.set_editor_property('hull_extent', unreal.Vector(500, 160, 100))
    ship.set_editor_property('hull_draft', 60.0)
    ship.set_editor_property('crew_capacity', 6)
    ship.set_editor_property('top_speed', 700.0)
    ship.set_editor_property('turn_rate', 30.0)
    ship.set_editor_property('mounts', [
        mount('Helm', unreal.EWShipMountType.HELM, (-380, 0, 140)),
        mount('Mainsail', unreal.EWShipMountType.SAIL, (0, 0, 140), unreal.EWSailSize.MEDIUM),
        mount('Headsail', unreal.EWShipMountType.SAIL, (360, 0, 140), unreal.EWSailSize.SMALL),
        mount('PortCannon', unreal.EWShipMountType.CANNON, (-80, -130, 140)),
        mount('StarboardCannon', unreal.EWShipMountType.CANNON, (-80, 130, 140)),
    ])

sloop, new = data_asset('/Game/Elitewake/Ships', 'DA_Ship_Sloop', unreal.EWShipDefinition, configure_sloop)
if new:
    created.append('DA_Ship_Sloop')
mounts = sloop.get_editor_property('mounts')
assert [str(m.get_editor_property('mount_id')) for m in mounts] == ['Helm', 'Mainsail', 'Headsail', 'PortCannon', 'StarboardCannon']
assert sum(1 for m in mounts if m.get_editor_property('type') == unreal.EWShipMountType.CANNON) == 2

# Place one bare sloop off the coastal dock, floating with its hull bottom HullDraft below the waterline.
map_path = '/Game/Elitewake/Maps/Lvl_CoastalPlayground'
world = unreal.EditorLoadingAndSavingUtils.load_map(map_path)
existing = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWShip)
placed = False
if not existing:
    waterline = -65.0
    extent, draft = sloop.get_editor_property('hull_extent'), sloop.get_editor_property('hull_draft')
    location = unreal.Vector(6200, 1400, waterline - draft + extent.z)
    ship = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.EWShip, location, unreal.Rotator(0, 0, 0))
    assert ship
    ship.set_editor_property('definition', sloop)
    ship.set_actor_label('Sloop_BareHull')
    assert unreal.EditorLoadingAndSavingUtils.save_map(world, map_path)
    placed = True
ships = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWShip)
assert len(ships) == 1 and ships[0].get_editor_property('definition') == sloop
assert not ships[0].get_installed_fittings(), 'The placed sloop must start as a bare hull.'

Path(unreal.Paths.project_saved_dir(), 'SloopTestAssets.json').write_text(json.dumps({
    'success': True, 'created': created, 'ship_placed_now': placed,
    'ship_location': str(ships[0].get_actor_location()), 'definition': sloop.get_path_name(),
    'fittings': [i.get_path_name() for i in items.values()],
    'scope': 'Test fixtures; bare hull with no fittings; no normal grants, recipes or sailing yet'
}, indent=2), encoding='utf-8')
unreal.log(f'EWSLOOP created={created} placed={placed}')
