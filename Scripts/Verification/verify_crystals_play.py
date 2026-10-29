"""Play: crystals, obsidian and coal (owner, October 18 rules; asked again October 28). One player.
Placement: every cave holds ruby, sapphire, emerald and obsidian nodes; Winter has emerald and coal on its mountainsides; coal is nowhere else.
Mining (starter cave): a wooden pickaxe cannot mine a ruby node; a Metal pickaxe can, and the node gives 4 to 8 in all, then is gone from view;
a second node set to a 3 s respawn comes back after it. Every node is set to a 3600 s (60 min) respawn. Screenshots go to Saved/Screenshots/Crystals/.
Writes Saved/CrystalsPlayResult.json."""
import json
import math
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(unreal.Paths.project_dir()) / 'Scripts' / 'Setup'))
import world_terrain as T  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
inventory = pawn.get_inventory_component()
nodes = [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWMineable) if ' Node ' in str(a.get_actor_label())]
metal = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestMetalPickaxe')
wooden = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWoodenPickaxe')
report = {'checks': [], 'nodes': len(nodes)}
state = {'t0': time.monotonic() + 12, 'phase': 0, 'handle': None}
cave = T.CAVES['Starter']


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **values})
    assert ok, f'{label}: {values}'


def now():
    return unreal.GameplayStatics.get_time_seconds(world)


def label(n):
    return str(n.get_actor_label())


def kind(n):
    return label(n).split(' Node ')[0]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error)
    (saved / 'CrystalsPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK Crystals success={error is None} error={error}')


def face(n, distance=150.0):
    """Stand in front of a node (out along its +x) and look at it."""
    loc, fwd = n.get_actor_location(), n.get_actor_forward_vector()
    for lift in (110, 160, 220):
        spot = unreal.Vector(loc.x + fwd.x * distance, loc.y + fwd.y * distance, cave.floor + lift)
        if pawn.teleport(spot, unreal.Rotator()):
            break
    eye, _ = pawn.get_actor_eyes_view_point()
    aim = unreal.Vector(loc.x + fwd.x * 35, loc.y + fwd.y * 35, loc.z + fwd.z * 35)
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, aim))


def shot(name):
    unreal.SystemLibrary.execute_console_command(world, 'Shot showui filename="' + str(saved / 'Screenshots' / 'Crystals' / f'{name}.png') + '"')


def tick(delta):
    if time.monotonic() < state['t0']:
        return
    try:
        p = state['phase']
        if p == 0:
            by = {}
            for n in nodes:
                by.setdefault(label(n).split(' Node ')[1].rsplit(' ', 1)[0], []).append(kind(n))
            report['by_place'] = {k: {x: v.count(x) for x in set(v)} for k, v in by.items()}
            for place, kinds in by.items():
                if place.endswith('cave'):
                    for want in ('Ruby', 'Sapphire', 'Emerald', 'Obsidian'):
                        check(f'{want} in {place}', want in kinds)
            winter = [k for place, v in by.items() if 'Winter' in place and 'mountain' in place for k in v]
            check('emerald on the winter mountains', winter.count('Emerald') >= 2, count=winter.count('Emerald'))
            check('coal on the winter mountains', winter.count('Coal') >= 5, count=winter.count('Coal'))
            check('coal only in Winter', all('Winter' in label(n) for n in nodes if kind(n) == 'Coal'))
            check('every node respawns after 3600 s', all(abs(n.get_editor_property('respawn_seconds') - 3600) < 1 and n.get_editor_property('respawn_when_depleted') for n in nodes))
            check('every node needs a metal pickaxe', all('METAL' in str(n.get_editor_property('minimum_pickaxe_tier')).upper() for n in nodes))
            check('every node holds 4 to 8', all(4 <= n.get_editor_property('remaining') <= 8 for n in nodes))
            for animal in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWAnimal):
                animal.destroy_actor()      # the cave spiders would bite the miner
            rubies = [n for n in nodes if kind(n) == 'Ruby' and 'Starter cave' in label(n)]
            check('two rubies in the starter cave', len(rubies) >= 2)
            state['ruby'], state['ruby2'] = rubies[0], rubies[1]
            state['ruby_item'] = state['ruby'].get_editor_property('resource')
            inventory.remove_item(state['ruby_item'], 100000)
            face(state['ruby'], 190)
            state.update(phase=1, at=now() + 1.5)
        elif p == 1:
            if now() < state['at']:
                return
            shot('Ruby')
            inventory.add_item(wooden, 1)
            check('wooden pickaxe equipped', lib.send_verification_equipment_request(pc, wooden, unreal.EWEquipmentSlot.MAIN_HAND))
            face(state['ruby'])
            state.update(phase=2, at=now() + 2.0)
        elif p == 2:
            if now() < state['at']:
                return
            lib.send_verification_attack(pc, state['ruby'])
            state.update(phase=3, at=now() + 2.0)
        elif p == 3:
            if now() < state['at']:
                return
            check('a wooden pickaxe gets nothing from a ruby node', inventory.get_item_count(state['ruby_item']) == 0)
            inventory.add_item(metal, 1)
            check('metal pickaxe equipped', lib.send_verification_equipment_request(pc, metal, unreal.EWEquipmentSlot.MAIN_HAND))
            face(state['ruby'])
            state.update(phase=4, at=now() + 2.0, strikes=0)
        elif p == 4:
            if now() < state['at']:
                return
            node = state['ruby']
            if node.get_editor_property('remaining') > 0 and state['strikes'] < 12:
                eye, rot = pawn.get_actor_eyes_view_point()
                res = unreal.SystemLibrary.line_trace_single(world, eye, eye + unreal.MathLibrary.get_forward_vector(rot) * 400, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [pawn], unreal.DrawDebugTrace.NONE, True)
                report.setdefault('aim_hits', []).append(res.to_tuple()[9].get_name() if res and res.to_tuple()[9] else 'nothing')
                report['node_name'] = node.get_name()
                lib.send_verification_attack(pc, node)
                state['strikes'] += 1
                state['at'] = now() + 1.7
                return
            got = inventory.get_item_count(state['ruby_item'])
            report['ruby_mined'] = got
            report['strikes'] = state['strikes']
            check('a metal pickaxe empties the ruby node for 4 to 8', node.get_editor_property('remaining') == 0 and 4 <= got <= 8, got=got)
            check('the emptied node is hidden', not node.get_editor_property('mesh').is_visible())
            n2 = state['ruby2']
            n2.set_editor_property('respawn_seconds', 3.0)
            inventory.remove_item(state['ruby_item'], 100000)
            face(n2)
            state.update(phase=5, at=now() + 2.0, strikes=0)
        elif p == 5:
            if now() < state['at']:
                return
            node = state['ruby2']
            if node.get_editor_property('remaining') > 0 and state['strikes'] < 12:
                lib.send_verification_attack(pc, node)
                state['strikes'] += 1
                state['at'] = now() + 1.7
                return
            check('second ruby node emptied', node.get_editor_property('remaining') == 0)
            state.update(phase=6, at=now() + 5.0)
        elif p == 6:
            if now() < state['at']:
                return
            node = state['ruby2']
            back = node.get_editor_property('remaining')
            check('the node came back after its respawn time', 4 <= back <= 8 and node.get_editor_property('mesh').is_visible(), remaining=back)
            # a look at each gem in the starter cave
            emerald = next(n for n in nodes if kind(n) == 'Emerald' and 'Starter cave' in label(n))
            face(emerald, 200)
            state.update(phase=7, at=now() + 1.2, look=['Emerald', 'Sapphire', 'Obsidian'], seen=0)
        elif p == 7:
            if now() < state['at']:
                return
            names = state['look']
            if state['seen'] < len(names):
                if state['seen'] > 0 or True:
                    shot(names[state['seen']])
                state['seen'] += 1
                if state['seen'] < len(names):
                    n = next(x for x in nodes if kind(x) == names[state['seen']] and 'Starter cave' in label(x))
                    face(n, 200)
                state['at'] = now() + 1.2
                return
            decor = [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor) if 'Crystal Decor' in str(a.get_actor_label())]
            by_cave = {}
            for a in decor:
                by_cave[str(a.get_actor_label()).split(' cave')[0]] = by_cave.get(str(a.get_actor_label()).split(' cave')[0], 0) + 1
            report['decor'] = by_cave
            check('every cave is hung with decorative crystals', len(by_cave) == 5 and all(v >= 20 for v in by_cave.values()), by_cave=by_cave)
            mid = cave.world(cave.chamber_u - 250, 0.0)
            assert pawn.teleport(unreal.Vector(mid[0], mid[1], cave.floor + 120), unreal.Rotator())
            pc.set_control_rotation(unreal.Rotator(10, math.degrees(cave.heading) if hasattr(cave, 'heading') else 0, 0))
            state.update(phase=8, at=now() + 1.5)
        elif p == 8:
            if now() < state['at']:
                return
            shot('CaveOverview')
            state.update(phase=9, at=now() + .5)
        elif p == 9:
            if now() < state['at']:
                return
            finish()
    except Exception as error:
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
