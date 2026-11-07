"""Play: the islands' gathered specialties (CLAUDE.md 5.7; November 7). One player, standalone:
    Scripts/Verification/run_play_check_once.ps1 -Check verify_gathered_specialties_play.py -Result GatheredSpecialtiesPlayResult.json -Players 1 -Standalone 1
  1. Census: each item's patches lie on its planned island (world_gathered_specialties.ITEMS) and on no other island.
  2. Gathering clay by hand (E) on Clay Shore puts clay in the pack.
  3. Gathering dates on Oasis Isle puts dates, a food, in the pack.
Screenshots in Saved/Screenshots/Gathered. Writes Saved/GatheredSpecialtiesPlayResult.json.
"""
import json
import math
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(unreal.Paths.project_dir()) / 'Scripts' / 'Setup'))
import world_gathered_specialties as G  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
inventory = pawn.get_inventory_component()
patches = [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWHandGatherable) if ' Patch ' in str(a.get_actor_label())]
(saved / 'Screenshots' / 'Gathered').mkdir(parents=True, exist_ok=True)
report = {'checks': [], 'patches': len(patches)}
state = {'phase': 0, 'at': time.monotonic() + 3, 'handle': None}


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **{k: str(v) for k, v in values.items()}})
    assert ok, f'{label}: {values}'


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error, finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    (saved / 'GatheredSpecialtiesPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK GatheredSpecialties success={error is None} error={error}')


def parts(a):
    label = str(a.get_actor_label()) if unreal.SystemLibrary.is_valid(a) else ''
    if ' Patch ' not in label:
        return None, None              # gathered empty and gone
    name, rest = label.split(' Patch ')
    return name, rest.rsplit(' ', 1)[0]


def face(node):
    """Stand on the ground a metre from the patch and look down at it."""
    at = node.get_actor_location()
    for turn in range(0, 360, 45):
        x, y = at.x + 120 * math.cos(math.radians(turn)), at.y + 120 * math.sin(math.radians(turn))
        hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, at.z + 600), unreal.Vector(x, y, at.z - 600),
                                                     unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [pawn, node], unreal.DrawDebugTrace.NONE, True)
        if hit and pawn.teleport(unreal.Vector(x, y, hit.to_tuple()[4].z + 110), unreal.Rotator()):
            break
    eye, _ = pawn.get_actor_eyes_view_point()
    origin, extent = node.get_actor_bounds(False)
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, unreal.Vector(origin.x, origin.y, origin.z + extent.z * .3)))


def gather(name, island, shot):
    node = next(a for a in patches if parts(a) == (name, island))
    face(node)
    state.update(node=node, item=node.get_editor_property('item_definition'), shot=shot)


def tick(_):
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        if p == 0:
            by = {}
            for a in patches:
                name, island = parts(a)
                by.setdefault(name, {}).setdefault(island, 0)
                by[name][island] += 1
            report['by_item'] = by
            for key, (name, *_rest) in G.ITEMS.items():
                isles, count = G.ITEMS[key][4], G.ITEMS[key][7]
                found = by.get(name, {})
                check(f'{name} on its island only', set(found) == set(isles), found=found)
                for island in isles:
                    check(f'{name} on {island}', found.get(island, 0) >= count - 2, count=found.get(island, 0))
            for animal in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWAnimal):
                animal.destroy_actor()
            gather('Clay', 'Plains3', 'Clay')
            state.update(phase=1, at=time.monotonic() + 2.0)
        elif p in (1, 3):
            unreal.SystemLibrary.execute_console_command(world, f'HighResShot 1920x1080 filename="{saved / "Screenshots" / "Gathered" / (state["shot"] + ".png")}"')
            check(f'can gather {state["shot"]}', state['node'].can_interact(pawn))
            eye, _ = pawn.get_actor_eyes_view_point()
            hit = unreal.SystemLibrary.line_trace_single(world, eye, eye + unreal.MathLibrary.get_forward_vector(pc.get_control_rotation()) * 250,   # the game's reach
                                                         unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [pawn], unreal.DrawDebugTrace.NONE, True)
            report.setdefault('aimed_at', []).append(str(hit.to_tuple()[9].get_actor_label()) if hit and hit.to_tuple()[9] else 'nothing')
            report.setdefault('menu_blocked', []).append(pc.get_interaction_component().is_menu_blocked())
            node = state['node']
            at = node.get_actor_location()
            origin, extent = node.get_actor_bounds(False)
            under = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(at.x, at.y, at.z + 500), unreal.Vector(at.x, at.y, at.z - 500),
                                                           unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [node, pawn], unreal.DrawDebugTrace.NONE, True)
            down = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(at.x, at.y, at.z + 500), unreal.Vector(at.x, at.y, at.z - 500),
                                                          unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [pawn], unreal.DrawDebugTrace.NONE, True)
            mesh = node.get_editor_property('mesh')
            report.setdefault('down_hit', []).append([str(down.to_tuple()[9].get_actor_label()) if down else None,
                                                      str(mesh.get_collision_enabled()), str(mesh.get_collision_response_to_channel(unreal.CollisionChannel.ECC_VISIBILITY)),
                                                      str(mesh.static_mesh.get_name()) if mesh.static_mesh else None])
            report.setdefault('patch', []).append({'z': round(at.z), 'top': round(origin.z + extent.z), 'half': [round(extent.x), round(extent.z)],
                                                   'ground': round(under.to_tuple()[4].z) if under else None, 'eye_z': round(eye.z)})
            lib.send_verification_interaction_request(pc, state['node'])   # the request E sends
            state.update(phase=p + 1, at=time.monotonic() + 2.0)
        elif p == 2:
            got = inventory.get_item_count(state['item'])
            check('gathering clay puts clay in the pack', got > 0, got=got)
            gather('Dates', 'Desert1', 'Dates')
            state.update(phase=3, at=time.monotonic() + 2.0)
        else:
            got = inventory.get_item_count(state['item'])
            report['dates_left_in_patch'] = state['node'].get_editor_property('quantity') if unreal.SystemLibrary.is_valid(state['node']) else 'gone'
            report['dates_direct_add'] = inventory.add_item(state['item'], 1) if got == 0 else 'not tried'
            check('gathering dates puts dates in the pack', got > 0, got=got)
            check('dates are food', 'CONSUMABLE' in str(state['item'].get_editor_property('category')).upper()
                  and state['item'].get_editor_property('food_consumption_enabled'))
            finish()
    except Exception as error:      # noqa: BLE001
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
