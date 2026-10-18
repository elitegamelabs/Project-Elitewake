"""Build the railing modules that fit a ship's railing hardpoints, and their test items. Safe to run again. Run in the
editor, outside Play, before the ship scripts that offer railing hardpoints (build_sloop_hull.py):
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

Owner, October 17 (MILESTONES, ship systems expansion): railing hardpoints on the sloop (one per side), schooner
(two) and brigantine (three) take interchangeable modules: a plain wooden railing, a dinghy attachment, or a
two-cannon railing; their timber, curve, grain and weathering match the hull. DECIDED (delegated, sizes tuning):
each module fills a 3.3 m gap the hull leaves in its bulwark under the continuous top rail. In the module's own
frame X points outboard, Y runs along the hull and Z up from the deck.
  - Plain wooden railing: a sill on the deck, a rail under the hull's rail and turned balusters between.
  - Two-cannon railing: the same with two framed ports 1.6 m apart for the cannons fitted behind it (the ship's
    cannon places that belong to this railing open while it is fitted: UEWItemDefinition::FittingCannonSlots).
  - Dinghy attachment: the plain railing with two curved davits swung outboard, blocks and falls hanging. It does
    not carry or launch a dinghy yet (later work).
Recipes, costs and weights are test tuning, as for the other test fittings.
Writes Saved/RailingsResult.json.
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
LENGTH = 330.0          # cm along the hull: the bulwark gap a module fills
HEIGHT = 66.0           # cm from the deck to the underside of the hull's top rail (the sloop's, amidships)
PORTS = (-80.0, 80.0)   # two-cannon railing: port centres along the module (cm)
PORT_WIDTH, PORT_SILL, PORT_HEAD = 58.0, 18.0, 58.0


def frame(b, ports=()):
    """Sill, top rail, end posts and balusters every 22 cm, leaving the ports open."""
    half = LENGTH / 2
    b.box((0, 0, 4), (12, LENGTH, 8))                     # sill on the deck
    b.box((0, 0, HEIGHT - 4), (10, LENGTH, 8))            # rail under the hull's rail
    for y in (-half + 5, half - 5):
        b.box((0, y, HEIGHT / 2), (12, 10, HEIGHT))       # end posts against the bulwark
    y = -half + 16
    while y < half - 12:
        if all(abs(y - p) > PORT_WIDTH / 2 + 6 for p in ports):
            # A turned baluster: thicker at the foot and under the rail, waisted between.
            b.tube([(0, y, 8), (0, y, 20), (0, y, HEIGHT / 2), (0, y, HEIGHT - 16), (0, y, HEIGHT - 8)],
                   lambda k: (3.6, 2.6, 2.2, 2.8, 3.4)[k], sides=8)
        y += 22
    for p in ports:
        # A framed port: sill, head and cheeks, the head under a short false rail.
        b.box((0, p, PORT_SILL), (14, PORT_WIDTH + 14, 8))
        b.box((0, p, PORT_HEAD), (14, PORT_WIDTH + 14, 8))
        for s in (-1, 1):
            b.box((0, p + s * (PORT_WIDTH / 2 + 4), (PORT_SILL + PORT_HEAD) / 2), (14, 8, PORT_HEAD - PORT_SILL + 8))
        b.box((0, p, PORT_SILL / 2), (12, PORT_WIDTH + 10, PORT_SILL))


def plain():
    b = Builder()
    frame(b)
    return b


def two_cannon():
    b = Builder()
    frame(b, PORTS)
    return b


def dinghy():
    b = Builder()
    frame(b)
    for y in (-110.0, 110.0):
        # A davit: up from the deck inside the rail, curving out over the side, a block hanging from its end.
        path = [(-20 + 130 * max(0.0, (t - .4) / .6) ** 1.6, y, 8 + 220 * min(1.0, t * 1.15)) for t in (k / 10 for k in range(11))]
        b.tube(path, lambda k: 6.0 - 2.0 * k / 10, sides=10, iron=0.0)
        tip = path[-1]
        b.box((tip[0], tip[1], tip[2] - 14), (10, 8, 18), iron=1.0)          # the block
        b.tube([(tip[0], tip[1], tip[2] - 24), (tip[0], tip[1], tip[2] - 150)], 0.9, sides=6)   # the fall
    return b


def data_asset(name, configure):
    path = f'{ITEMS}/{name}'
    asset = unreal.load_asset(path)
    if not asset:
        factory = unreal.DataAssetFactory()
        factory.set_editor_property('data_asset_class', unreal.EWItemDefinition)
        asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, ITEMS, unreal.EWItemDefinition, factory)
    configure(asset)
    assert unreal.EditorAssetLibrary.save_loaded_asset(asset)
    return asset


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    timber = make_timber_material()
    report = {}
    for name, item_id, display, build, slots, weight in (
            ('DA_TestRailingPlain', 'Test.RailingPlain', 'Wooden Railing', plain, 0, 20.0),
            ('DA_TestRailingTwoCannon', 'Test.RailingTwoCannon', 'Two-Cannon Railing', two_cannon, 2, 30.0),
            ('DA_TestRailingDinghy', 'Test.RailingDinghy', 'Dinghy Davits', dinghy, 0, 40.0)):
        mesh = write_static_mesh(build(), f'{FOLDER}/SM_{name[7:]}_v1', [timber], 120.0)

        def configure(item, item_id=item_id, display=display, mesh=mesh, slots=slots, weight=weight):
            item.set_editor_property('item_id', item_id)
            item.set_editor_property('display_name', display)
            item.set_editor_property('category', unreal.EWItemCategory.MISCELLANEOUS)
            item.set_editor_property('max_stack_size', 1)
            item.set_editor_property('unit_weight', weight)
            item.set_editor_property('fitting_mount_type', unreal.EWShipMountType.RAILING)
            item.set_editor_property('fitting_cannon_slots', slots)
            item.set_editor_property('fitting_mesh', mesh)
            item.set_editor_property('fitting_mesh_transform', unreal.Transform())
            item.set_editor_property('description', 'Ship railing module, test fixture. Weight is test tuning; recipe and cost pending.')
        data_asset(name, configure)
        report[name] = {'mesh': mesh.get_name(), 'cannon_slots': slots}
    Path(unreal.Paths.project_saved_dir(), 'RailingsResult.json').write_text(json.dumps({'success': True, 'modules': report}, indent=2))
    unreal.log(f'Railings built: {list(report)}')


if __name__ == '__main__':
    main()
