"""Play: armor in a hosted game (owner, November 8). Listen server plus one client:
    Scripts/Verification/run_play_check_once.ps1 -Check verify_armor_multiplayer_play.py -Result ArmorMultiplayerPlayResult.json -Players 2 -Kit 1
  1. The client puts on a metal helmet, a fur jacket and cloth pants through its own equipment request: the server's copy wears
     them, and both screens draw the pieces on that survivor.
  2. The host puts on the full metal set: the client's screen draws it on the host.
  3. A host's punch on the client in the open (outside the Freeport) is reduced by the client's armor, on the server.
  4. The client takes off its helmet: both screens stop drawing it.
Writes Saved/ArmorMultiplayerPlayResult.json.
"""
import json
import math
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(unreal.Paths.project_dir(), 'Scripts', 'Setup')))
import world_layout as W  # noqa: E402
import world_terrain as T  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'ArmorMultiplayerPlayResult.json')
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
host = next(c for c in pcs if c.has_authority())
server_world = worlds[pcs.index(host)]
client_world = worlds[pcs.index(client)]
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
ITEMS = '/Game/Elitewake/Items/Armor'
HEAD, CHEST, LEGS = unreal.EWEquipmentSlot.HEAD, unreal.EWEquipmentSlot.CHEST, unreal.EWEquipmentSlot.LEGS
report = {'checks': []}
state = {'phase': 0, 'at': time.monotonic() + 6, 'handle': None}


def pid(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


def peer_in(world, pawn):
    return next(p for p in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWCharacter) if pid(p) == pid(pawn))


client_pawn = client.get_controlled_pawn()
owner = peer_in(server_world, client_pawn)          # the client's survivor, on the server
host_pawn = host.get_controlled_pawn()


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **{k: str(v) for k, v in values.items()}})
    assert ok, f'{label}: {values}'


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error, finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    RESULT.write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK ArmorMultiplayer success={error is None} error={error}')


def piece(name):
    return unreal.load_asset(f'{ITEMS}/DA_{name}')


def worn(pawn):
    return sorted(e.get_editor_property('item_definition').get_name() for e in pawn.get_equipment_component().get_equipment_entries()
                  if e.get_editor_property('item_definition') and e.get_editor_property('slot') in (HEAD, CHEST, LEGS))


def open_ground():
    """Inland on Copper Downs, well outside any Freeport."""
    i = W.island('Plains2')
    a = 0.4
    r = i.radius(a) - 3000
    x, y = i.cx + r * math.cos(a), i.cy + r * math.sin(a)
    return unreal.Vector(x, y, T.height(x, y) + 150)


def tick(_):
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        if p == 0:
            for name in ('MetalTricornHelmet', 'FurJacket', 'ClothPants'):
                owner.get_inventory_component().add_item(piece(name), 1)
            for name in ('MetalTricornHelmet', 'MetalCuirass', 'MetalPants'):
                host_pawn.get_inventory_component().add_item(piece(name), 1)
            state.update(phase=1, at=time.monotonic() + 1.5)
        elif p == 1:
            # The client asks through its own controller, as its menu does; the host through its own.
            for name, slot in (('MetalTricornHelmet', HEAD), ('FurJacket', CHEST), ('ClothPants', LEGS)):
                check(f'the client asks to wear the {name}', lib.send_verification_equipment_request(client, piece(name), slot))
            for name, slot in (('MetalTricornHelmet', HEAD), ('MetalCuirass', CHEST), ('MetalPants', LEGS)):
                check(f'the host wears the {name}', lib.send_verification_equipment_request(host, piece(name), slot))
            state.update(phase=2, at=time.monotonic() + 2.5)
        elif p == 2:
            want = sorted(['DA_MetalTricornHelmet', 'DA_FurJacket', 'DA_ClothPants'])
            check('the server has the client wearing the mixed outfit', worn(owner) == want, worn=worn(owner))
            check('the client sees its own outfit', worn(client_pawn) == want, worn=worn(client_pawn))
            check('the client\'s screen draws its armor', client_pawn.get_armor_piece_count() > 0, shapes=client_pawn.get_armor_piece_count())
            check('the host\'s screen draws the client\'s armor', owner.get_armor_piece_count() == client_pawn.get_armor_piece_count(),
                  host=owner.get_armor_piece_count(), client=client_pawn.get_armor_piece_count())
            host_seen = peer_in(client_world, host_pawn)
            check('the client\'s screen draws the host\'s metal set', host_seen.get_armor_piece_count() == host_pawn.get_armor_piece_count() > 0,
                  client=host_seen.get_armor_piece_count(), host=host_pawn.get_armor_piece_count())
            check('the server reckons the client\'s armor', abs(owner.get_armor_reduction() - (.08 + .036 + .035)) < .002,
                  reduction=owner.get_armor_reduction())
            # A punch in the open.
            spot = open_ground()
            owner.teleport(spot, unreal.Rotator())
            host_pawn.teleport(spot + unreal.Vector(-120, 0, 0), unreal.Rotator())
            owner.get_survival_component().restore_health(1000)
            state['health'] = owner.get_survival_component().get_health()
            owner.take_physical_damage(10)
            check('a 10-point blow on the client takes 8.49 on the server', abs(state['health'] - owner.get_survival_component().get_health() - 8.49) < .02,
                  lost=state['health'] - owner.get_survival_component().get_health())
            check('the client takes off its helmet', lib.send_verification_equipment_request(client, None, HEAD, True))
            state['before'] = owner.get_armor_piece_count()
            state.update(phase=3, at=time.monotonic() + 2.5)
        else:
            check('the helmet is off on the server', 'DA_MetalTricornHelmet' not in worn(owner), worn=worn(owner))
            check('both screens draw fewer pieces', owner.get_armor_piece_count() < state['before']
                  and client_pawn.get_armor_piece_count() == owner.get_armor_piece_count(),
                  host=owner.get_armor_piece_count(), client=client_pawn.get_armor_piece_count(), before=state['before'])
            finish()
    except Exception as error:      # noqa: BLE001
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
