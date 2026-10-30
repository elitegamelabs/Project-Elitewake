"""Apply the owner's sailing rules (Docs/OwnerDecisions/SAIL_SPEED_WIND_AND_CODEX_PRIORITY_2026-10-18.md, with the delegated choices in
Docs/REPORTS/2026-10-18_ChatGPT_Delegated_Decisions.md) to the existing assets. Safe to run again:
  - each ship definition's TopSpeed becomes its class base speed: raft 3, dinghy 5 (delegated: between the raft and the sloop), sloop 8,
    schooner 10, brigantine 12 knots (the builders now write the same values);
  - the three standard sails get their whole-ship multipliers: small 1.30, medium 1.50, large 1.80;
  - the three weighted sails are made beside them (Items/Ships/DA_Sail<Size>Weighted: 1.25, 1.40, 1.70, a weighted hem that steadies the
    ship). They fit the same mounts as the standard sails of their size and, until their own art, look like the rig's sail there.
The raft's Small sail hardpoint is built by build_small_craft.py. Sails have no recipes yet (shipyard crafting is open).
    UnrealEditor-Cmd.exe EW.uproject -unattended -nosplash -nullrhi -run=pythonscript -script=<this file>"""
import json
from pathlib import Path
import unreal

KNOT = 51.4444
SHIPS = '/Game/Elitewake/Ships'
ITEMS = '/Game/Elitewake/Items'
SPEEDS = {'Raft': 3, 'Dinghy': 5, 'Sloop': 8, 'Schooner': 10, 'Brigantine': 12}
STANDARD = {'Small': ('Testing/DA_TestSailSmall', 1.30, 1.25), 'Medium': ('Testing/DA_TestSailMedium', 1.50, 1.40),
            'Large': ('Testing/DA_TestSailLarge', 1.80, 1.70)}


def main():
    lib = unreal.EditorAssetLibrary
    report = {'speeds': {}, 'sails': {}}
    for ship, knots in SPEEDS.items():
        d = unreal.load_asset(f'{SHIPS}/DA_Ship_{ship}')
        assert d, ship
        d.set_editor_property('top_speed', knots * KNOT)
        assert lib.save_loaded_asset(d, False)
        report['speeds'][ship] = round(knots * KNOT, 1)
    for size, (path, standard, weighted) in STANDARD.items():
        sail = unreal.load_asset(f'{ITEMS}/{path}')
        assert sail, path
        sail.set_editor_property('sail_speed_multiplier', standard)
        sail.set_editor_property('weighted_sail', False)
        assert lib.save_loaded_asset(sail, False)
        target = f'{ITEMS}/Ships/DA_Sail{size}Weighted'
        heavy = unreal.load_asset(target) or lib.duplicate_asset(f'{ITEMS}/{path}', target)
        assert heavy, target
        heavy.set_editor_property('item_id', f'Ship.Sail{size}Weighted')
        heavy.set_editor_property('display_name', unreal.Text(f'{size} Weighted Sail'))
        heavy.set_editor_property('description', unreal.Text(
            f'A {size.lower()} sail assembly with its own mast and a sewn-in weighted hem. Fits a {size.lower()} sail hardpoint. '
            f'A little slower than a plain sail ({weighted:.2f} times the ship\'s base speed at full sail) but steadier in the wind.'))
        heavy.set_editor_property('sail_speed_multiplier', weighted)
        heavy.set_editor_property('weighted_sail', True)
        assert lib.save_loaded_asset(heavy, False)
        report['sails'][size] = {'standard': standard, 'weighted': weighted}
    report['success'] = True
    Path(unreal.Paths.project_saved_dir(), 'SailRulesResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'Sail rules applied: {report}')


if __name__ == '__main__':
    main()
