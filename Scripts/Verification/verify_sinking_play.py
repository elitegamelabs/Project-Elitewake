"""Client acceptance for sinking and wreck crates (M2: a ship that fills or is destroyed goes down, leaving wreck
crates with its hold; design reference: wreck loot floats in crates for about 15 real minutes). Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client
(the dinghy's rule is checked on the ships test map by verify_dinghy_unsinkable_play.py). Run unattended with run_play_check.py.

The sloop's hold is stocked (server, Play only; whatever fittings she has go too), the client's survivor stands on her
deck, and her hull is struck until it is destroyed (AEWShip::TakeRoundShot, as cannon balls do).
  1. Her hull destroyed, she is sinking on server and client, and nothing aboard can be used.
  2. Wreck crates float up at the surface round her, holding exactly her hold and her fittings, on the client too,
     each due to last about 15 minutes.
  3. She goes down by the bow and is gone within 30 s, on both; the survivor who was aboard is left swimming.
  4. The survivor swims to a crate, opens it (Interact) and takes a stack from it.
Writes Saved/SinkingPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'SinkingPlayResult.json')
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]
pawn = client.get_controlled_pawn()
TESTING = '/Game/Elitewake/Items/Testing'
GOODS = {'DA_TestStone': 30, 'DA_TestWood': 40, 'DA_TestFiber': 25, 'DA_TestSticks': 12, 'DA_TestOre': 8,
         'DA_TestThatch': 20, 'DA_TestHide': 5, 'DA_TestRoundShot': 6}


def player_id(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


def ship_named(world, ship_id):
    return next((s for s in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWShip)
                 if str(s.get_editor_property('definition').get_editor_property('ship_id')) == ship_id), None)


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if player_id(p) == player_id(pawn))
ship = ship_named(server_world, 'Sloop')
ship_name = ship.get_name()
peer = next(s for s in unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWShip) if s.get_name() == ship_name)
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}, 'aim': None}


def crates(world):
    return unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWWreckCrate)


def totals(inventories):
    out = {}
    for inv in inventories:
        for e in inv.get_inventory_entries():
            name = e.item_definition.get_name()
            out[name] = out.get(name, 0) + e.quantity
    return out


def destroy(target):
    t = target.get_actor_transform()
    extent = target.get_editor_property('definition').get_editor_property('hull_extent')
    k = 0
    while target.get_hull_health() > 0 and k < 100:
        where = t.transform_location(unreal.Vector(-200 + 15 * k, extent.y, extent.z - 15))
        target.take_round_shot(where, target.get_actor_right_vector(), None)
        k += 1


def stock_and_board():
    cargo = ship.get_cargo()
    for name, n in GOODS.items():
        assert cargo.add_item(unreal.load_asset(f'{TESTING}/{name}'), n) == n, name
    m = state['memo']
    m['want'] = totals([cargo])
    fitted = [f.item.get_name() for f in ship.get_installed_fittings() if f.item]
    for name in fitted:
        m['want'][name] = m['want'].get(name, 0) + 1
    hatch = ship.get_cargo_hatch_world()
    for p in (owner, pawn):
        assert p.teleport(unreal.Vector(hatch.x, hatch.y, hatch.z + 120), ship.get_actor_rotation()), 'no room on deck'
    m.update(t=time.monotonic(), fitted=len(fitted))


def destroyed():
    m = state['memo']
    if time.monotonic() - m['t'] < 1.5:
        return False
    if 'z0' not in m:
        assert ship.is_aboard(owner), 'the survivor is not aboard'
        m['z0'] = ship.get_actor_location().z
        destroy(ship)
        m['t2'] = time.monotonic()
        return False
    if not (ship.is_sinking() and peer.is_sinking()):
        return False
    assert not ship.can_interact(owner), 'the sinking ship still offers something'
    m['sink_t'] = m['t2']
    return True


def floated():
    m = state['memo']
    mine, seen = crates(server_world), crates(client_world)
    if not mine or len(seen) < len(mine):
        return False
    got = totals([c.get_contents() for c in mine])
    assert got == m['want'], f'crates hold {got}, she carried {m["want"]}'
    assert totals([c.get_contents() for c in seen]) == got, 'the client sees different crate contents'
    for c in mine:
        z = c.get_actor_location().z
        assert abs(z - c.get_editor_property('surface_z')) < 30, f'a crate at {z:.0f}, not on the surface'
        assert 840 < c.get_life_span() <= 900, f'a crate lasts {c.get_life_span():.0f} s'
    assert ship.get_cargo().get_used_slot_count() == 0, 'the hold still holds goods'
    m.update(crates=len(mine), crate_stacks=sum(c.get_contents().get_used_slot_count() for c in mine))
    return True


def gone():
    m = state['memo']
    alive = [s for s in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWShip) if s.get_name() == ship_name]
    if alive:
        s = alive[0]
        if time.monotonic() - m['sink_t'] > 10 and 'mid' not in m:
            m['mid'] = True
            drop = m['z0'] - s.get_actor_location().z
            pitch = s.get_actor_rotation().pitch
            assert drop > 150 and pitch < -10, f'10 s in she has dropped {drop:.0f} cm, pitch {pitch:.1f}'
            m.update(drop_at_10s_cm=round(drop), pitch_at_10s=round(pitch, 1))
        return False
    if any(s.get_name() == ship_name for s in unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWShip)):
        return False
    m['gone_s'] = round(time.monotonic() - m['sink_t'], 1)
    assert m['gone_s'] < 36, m['gone_s']
    return True


def swimming():
    if time.monotonic() - state['memo']['sink_t'] < state['memo']['gone_s'] + 2:
        return False
    mode = pawn.get_component_by_class(unreal.CharacterMovementComponent).movement_mode
    assert mode == unreal.MovementMode.MOVE_SWIMMING, f'the survivor is {mode}, not swimming'
    return True


def to_crate():
    crate = crates(server_world)[0]
    at = crate.get_actor_location()
    # Beside it in the water, on whichever side has room.
    for dx, dy in ((-180, 0), (180, 0), (0, -180), (0, 180)):
        if owner.teleport(unreal.Vector(at.x + dx, at.y + dy, at.z - 40), unreal.Rotator()):
            break
    else:
        raise AssertionError('no room in the water beside the crate')
    pawn.teleport(owner.get_actor_location(), unreal.Rotator())
    state['aim'] = lambda: crate.get_actor_location()
    state['memo'].update(crate=crate.get_name(), t=time.monotonic(), opened=False,
                         before=totals([owner.get_inventory_component()]))


def keep_aim():
    if not state['aim']:
        return
    for controller, who in ((client, pawn), (owner.get_controller(), owner)):
        eye = who.get_actor_location() + unreal.Vector(0, 0, who.get_editor_property('base_eye_height'))
        controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, state['aim']()))


def took():
    m = state['memo']
    keep_aim()
    if time.monotonic() - m['t'] < 1.0:
        return False
    crate = next(c for c in crates(server_world) if c.get_name() == m['crate'])
    crate_peer = next((c for c in crates(client_world) if c.get_name() == m['crate']), None)
    if not m['opened']:
        assert crate.can_interact(owner), 'the crate is out of reach'
        assert lib.send_verification_interaction_request(client, crate_peer)
        m['opened'], m['t'] = True, time.monotonic()
        return False
    if 'sent' not in m:
        if client.get_open_container() != crate_peer:
            return False
        # A few from the first stack (a whole stack may be more than a survivor can carry).
        entry = crate.get_contents().get_inventory_entries()[0]
        m.update(item=entry.item_definition.get_name(), qty=min(entry.quantity, 3), left=entry.quantity - min(entry.quantity, 3), sent=True)
        assert lib.send_verification_container_transfer(client, crate_peer, False, 0, m['qty'])
        return False
    now = totals([owner.get_inventory_component()])
    if now.get(m['item'], 0) - m['before'].get(m['item'], 0) < m['qty']:
        return False
    assert totals([crate.get_contents()]).get(m['item'], 0) == m['left'], 'the crate did not give them up'
    m['took'] = f"{m['qty']} {m['item']}"
    return True


STEPS = [
    ('Her hull destroyed with goods and a crew aboard, the sloop sinks on server and client; nothing aboard can be used', stock_and_board, destroyed, 8),
    ('Wreck crates float at the surface holding exactly her hold and fittings, on the client too, each lasting about 15 min', lambda: None, floated, 6),
    ('She goes down by the bow and is gone within 30 s, on both', lambda: None, gone, 45),
    ('The survivor who was aboard is left swimming', lambda: None, swimming, 10),
    ('The survivor swims to a crate, opens it and takes a stack', to_crate, took, 12),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    keep = {k: v for k, v in state['memo'].items() if isinstance(v, (int, float, str)) and k not in ('t', 't2', 'sink_t', 'z0', 'opened', 'qty', 'left', 'sent', 'mid')}
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': keep,
                                  'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK Sinking success={error is None} error={error}')


def tick(delta):
    description, begin, done, timeout = STEPS[state['index']]
    try:
        if not state['begun']:
            begin()
            state.update(begun=True, deadline=time.monotonic() + timeout)
            return
        if done():
            checks.append(description)
            state.update(index=state['index'] + 1, begun=False)
            if state['index'] == len(STEPS):
                finish()
        elif time.monotonic() > state['deadline']:
            p = pawn.get_actor_location()
            m = state['memo']
            stage = {k: m.get(k) for k in ('opened', 'sent', 'item', 'qty')}
            raise TimeoutError(f'not done within {timeout} s; survivor at ({p.x:.0f}, {p.y:.0f}, {p.z:.0f}); {stage}; open {client.get_open_container()}')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
