"""Play: the islands' mined specialties (CLAUDE.md 5.7; November 7). One player, standalone:
    Scripts/Verification/run_play_check_once.ps1 -Check verify_specialty_ores_play.py -Result SpecialtyOresPlayResult.json -Players 1 -Standalone 1
  1. Census: each ore's deposits lie on its planned islands (world_specialty_ores.ORES) and on no other island.
  2. A wooden pickaxe mines copper ore from a Copper Downs deposit.
  3. A wooden pickaxe gets nothing from sulfur ore; a Metal pickaxe mines it (CLAUDE.md 4).
Screenshots in Saved/Screenshots/Ores. Writes Saved/SpecialtyOresPlayResult.json.
"""
import json
import math
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(unreal.Paths.project_dir()) / 'Scripts' / 'Setup'))
import world_specialty_ores as O  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
inventory = pawn.get_inventory_component()
metal = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestMetalPickaxe')
wooden = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWoodenPickaxe')
deposits = [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWMineable) if ' Deposit ' in str(a.get_actor_label())]
(saved / 'Screenshots' / 'Ores').mkdir(parents=True, exist_ok=True)
report = {'checks': [], 'deposits': len(deposits)}
state = {'phase': 0, 'at': time.monotonic() + 3, 'handle': None, 'strikes': 0}


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **{k: str(v) for k, v in values.items()}})
    assert ok, f'{label}: {values}'


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error, finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    (saved / 'SpecialtyOresPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK SpecialtyOres success={error is None} error={error}')


def parts(a):
    name, rest = str(a.get_actor_label()).split(' Deposit ')
    return name, rest.rsplit(' ', 1)[0]


def face(node):
    """Stand on the ground a couple of metres from the deposit and look at it."""
    at = node.get_actor_location()
    for turn in range(0, 360, 45):
        x, y = at.x + 140 * math.cos(math.radians(turn)), at.y + 140 * math.sin(math.radians(turn))
        hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, at.z + 800), unreal.Vector(x, y, at.z - 800),
                                                     unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [pawn, node], unreal.DrawDebugTrace.NONE, True)
        if hit and pawn.teleport(unreal.Vector(x, y, hit.to_tuple()[4].z + 110), unreal.Rotator()):
            break
    eye, _ = pawn.get_actor_eyes_view_point()
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, unreal.Vector(at.x, at.y, at.z + 40)))
    report.setdefault('aimed_at', []).append(aimed())


def aimed():
    eye, rot = pawn.get_actor_eyes_view_point()
    rot = pc.get_control_rotation()
    hit = unreal.SystemLibrary.line_trace_single(world, eye, eye + unreal.MathLibrary.get_forward_vector(rot) * 400,
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [pawn], unreal.DrawDebugTrace.NONE, True)
    return str(hit.to_tuple()[9].get_actor_label()) if hit and hit.to_tuple()[9] else 'nothing'


def strike_until(node, item, limit, next_phase):
    if node.get_editor_property('remaining') > 0 and inventory.get_item_count(item) == 0 and state['strikes'] < limit:
        lib.send_verification_attack(pc, node)
        state['strikes'] += 1
        state['at'] = time.monotonic() + 1.7
        return
    state.update(phase=next_phase, at=time.monotonic() + .5)


def tick(_):
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        if p == 0:
            by = {}
            for a in deposits:
                name, island = parts(a)
                by.setdefault(name, {}).setdefault(island, 0)
                by[name][island] += 1
            report['by_ore'] = by
            for key, (name, _, _, isles, _, count) in O.ORES.items():
                found = by.get(name, {})
                check(f'{name} on its islands only', set(found) == set(isles), found=found)
                for island in isles:
                    check(f'{name} on {island}', found.get(island, 0) >= count - 2, count=found.get(island, 0))
            for animal in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWAnimal):
                animal.destroy_actor()        # nothing to bite the miner
            state['copper'] = next(a for a in deposits if parts(a) == ('Copper Ore', 'Plains2'))
            state['sulfur'] = next(a for a in deposits if parts(a)[0] == 'Sulfur Ore')
            state['copper_item'] = state['copper'].get_editor_property('resource')
            state['sulfur_item'] = state['sulfur'].get_editor_property('resource')
            inventory.add_item(wooden, 1)
            check('wooden pickaxe equipped', lib.send_verification_equipment_request(pc, wooden, unreal.EWEquipmentSlot.MAIN_HAND))
            face(state['copper'])
            state.update(phase=1, at=time.monotonic() + 2.5, strikes=0)
        elif p == 1:
            strike_until(state['copper'], state['copper_item'], 6, 2)
        elif p == 2:
            unreal.SystemLibrary.execute_console_command(world, f'HighResShot 1920x1080 filename="{saved / "Screenshots" / "Ores" / "Copper.png"}"')
            got = inventory.get_item_count(state['copper_item'])
            check('a wooden pickaxe mines copper ore', got > 0, got=got)
            face(state['sulfur'])
            state.update(phase=3, at=time.monotonic() + 2.5, strikes=0)
        elif p == 3:
            strike_until(state['sulfur'], state['sulfur_item'], 3, 4)
        elif p == 4:
            unreal.SystemLibrary.execute_console_command(world, f'HighResShot 1920x1080 filename="{saved / "Screenshots" / "Ores" / "Sulfur.png"}"')
            check('a wooden pickaxe gets nothing from sulfur ore', inventory.get_item_count(state['sulfur_item']) == 0)
            inventory.add_item(metal, 1)
            check('metal pickaxe equipped', lib.send_verification_equipment_request(pc, metal, unreal.EWEquipmentSlot.MAIN_HAND))
            face(state['sulfur'])
            state.update(phase=5, at=time.monotonic() + 2.0, strikes=0)
        elif p == 5:
            strike_until(state['sulfur'], state['sulfur_item'], 6, 6)
        else:
            got = inventory.get_item_count(state['sulfur_item'])
            check('a metal pickaxe mines sulfur ore', got > 0, got=got)
            finish()
    except Exception as error:      # noqa: BLE001
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
