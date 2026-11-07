"""Client acceptance for the first-person body.

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client. Run unattended
with run_play_check.py.

  1. The client presses Z for first person: its own survivor stays drawn with only the head hidden, on its screen
     alone (the server still draws the head), and the eyes ride on the animated body, just above the chest.
  2. Turning the view turns the body, on the client and on the server.
  3. Walking backward keeps the body facing the view while it steps back.
  4. Crouching carries the eyes down with the body.
  5. Back in third person the head shows again and the body turns with its movement once more.
Writes Saved/FirstPersonPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'FirstPersonPlayResult.json')
BEACH = unreal.Vector(150, 0, 120)
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
pawn = client.get_controlled_pawn()


def player_id(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if player_id(p) == player_id(pawn))
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'input': None, 'memo': {}}


def body(who):
    return who.get_editor_property('mesh')


def eyes():
    return pawn.get_editor_property('first_person_camera').get_world_location()


def yaw_gap(a, b):
    return abs((a - b + 180) % 360 - 180)


def first_person():
    for p in (owner, pawn):
        assert p.teleport(BEACH, unreal.Rotator())
    client.set_control_rotation(unreal.Rotator())
    # Z, as a player presses it: the game's own input path tells the server to turn the body with the view.
    assert lib.send_verification_gameplay_key(client, 'Z')


def drawn():
    mine, theirs = body(pawn), body(owner)
    if not owner.is_facing_view():
        return False
    assert pawn.is_first_person and pawn.is_facing_view()
    assert not mine.get_editor_property('owner_no_see'), "the client's survivor is hidden from its own camera"
    assert mine.is_bone_hidden_by_name('neck_01'), "the client's own head is still drawn"
    assert not theirs.is_bone_hidden_by_name('neck_01'), 'the server hides the head too'
    # The hidden head no longer moves, so the eyes are measured from the upper chest, which still does.
    gap = (eyes() - mine.get_socket_location('spine_05')).length()
    state['memo']['eyes_from_chest'] = round(gap, 1)
    assert 10 < gap < 45, f'the eyes are {gap:.0f} cm from the upper chest'
    return True


def turn():
    client.set_control_rotation(unreal.Rotator(yaw=90))


def turned():
    mine, theirs = pawn.get_actor_rotation().yaw, owner.get_actor_rotation().yaw
    if yaw_gap(mine, 90) > 3 or yaw_gap(theirs, 90) > 5:
        return False
    state['memo'].update(client_yaw=round(mine, 1), server_yaw=round(theirs, 1))
    return True


def walk_back():
    state['memo'].update(start=owner.get_actor_location(), t=time.monotonic())
    state['input'] = lambda: pawn.do_move(0, -1)


def stepped_back():
    m = state['memo']
    if time.monotonic() - m['t'] < 1.5:
        return False
    state['input'] = None
    moved = owner.get_actor_location() - m['start']
    back = -(moved.x * owner.get_actor_forward_vector().x + moved.y * owner.get_actor_forward_vector().y)
    m.update(stepped_back=round(back), yaw_walking_back=round(owner.get_actor_rotation().yaw, 1))
    assert back > 100, f'stepped back only {back:.0f} cm'
    assert yaw_gap(owner.get_actor_rotation().yaw, 90) < 5 and yaw_gap(pawn.get_actor_rotation().yaw, 90) < 5, \
        'the body turned away from the view while walking backward'
    return True


def crouch():
    state['memo']['standing_eyes'] = eyes().z - pawn.get_actor_location().z + pawn.get_component_by_class(unreal.CapsuleComponent).get_scaled_capsule_half_height()
    pawn.crouch()


def crouched():
    if not (pawn.get_editor_property('bIsCrouched') and owner.get_editor_property('bIsCrouched')):
        return False
    height = eyes().z - pawn.get_actor_location().z + pawn.get_component_by_class(unreal.CapsuleComponent).get_scaled_capsule_half_height()
    m = state['memo']
    m.setdefault('crouched_eyes', height)
    m['crouched_eyes'] = min(m['crouched_eyes'], height)
    if m['standing_eyes'] - m['crouched_eyes'] < 20:
        return False
    gap = (eyes() - body(pawn).get_socket_location('spine_05')).length()
    assert 10 < gap < 45, f'crouched, the eyes are {gap:.0f} cm from the upper chest'
    m.update(standing_eyes=round(m['standing_eyes']), crouched_eyes=round(m['crouched_eyes']))
    pawn.un_crouch()
    return True


def third_person():
    assert lib.send_verification_gameplay_key(client, 'Z')


def back_to_third():
    if owner.is_facing_view():
        return False
    assert not body(pawn).is_bone_hidden_by_name('neck_01'), 'the head is still hidden in third person'
    assert not pawn.is_facing_view()
    return True


STEPS = [
    ('First person draws the survivor with only the head hidden, on its own screen alone, eyes above the chest', first_person, drawn, 5),
    ('Turning the view turns the body on client and server', turn, turned, 4),
    ('Walking backward steps back with the body still facing the view', walk_back, stepped_back, 5),
    ('Crouching carries the eyes down with the body', crouch, crouched, 5),
    ('Third person shows the head again and the body turns with its movement', third_person, back_to_third, 4),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    pawn.set_first_person_view(False)
    memo = {k: v for k, v in state['memo'].items() if k not in ('start', 't')}
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': memo}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK FirstPerson success={error is None} error={error}')


def tick(delta):
    if state['input']:
        state['input']()
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
            raise TimeoutError(f'not done within {timeout} s; client first person {pawn.is_first_person}, facing on client '
                               f'{pawn.is_facing_view()} and server {owner.is_facing_view()}, yaw {pawn.get_actor_rotation().yaw:.0f} / '
                               f'{owner.get_actor_rotation().yaw:.0f}; owner {owner.get_name()} pawn {pawn.get_name()}')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
