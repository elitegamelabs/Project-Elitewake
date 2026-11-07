"""Bare-hand punches by arm (owner, November 3). Listen server plus one client with the starter kit, 1920x1080:
    .\\Scripts\\Verification\\run_play_check_once.ps1 -Check verify_punches_play.py -Result PunchesPlayResult.json -Players 2 -Kit 1 -Window 1920x1080
  1. Bare-handed in third person: Right Mouse punches with the right arm (MM_Attack_01), Left Mouse with the left
     (MM_Attack_02), on the client's screen and as the server shows it.
  2. On a controller the same: RT the right arm, LT the left.
  3. In first person the client's own screen shows the first-person jab (AS_PunchFP_*), the server the third-person punch.
  4. With the wooden axe in hand Left Mouse swings the axe (no punch) and Right Mouse and LT do nothing.
Screenshots of each punch at its reach in Saved/Screenshots/Punches/ (owner visual review pending).
Writes Saved/PunchesPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'PunchesPlayResult.json')
SHOTS = Path(unreal.Paths.project_saved_dir(), 'Screenshots', 'Punches')
SHOTS.mkdir(parents=True, exist_ok=True)
for old in SHOTS.glob('*.png'):
    old.unlink()
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]
pawn = client.get_controlled_pawn()


def player_id(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if player_id(p) == player_id(pawn))
axe = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWoodenAxe')
SPOT = unreal.Vector(150, 0, 120)          # the arrival beach, open sky
report = {'checks': [], 'seen': []}
state = {'i': 0, 'at': time.monotonic() + 2.0, 'h': None, 'step_began': None}


def name(anim):
    return anim.get_name() if anim else None


def clear():
    for p in (pawn, owner):
        p.get_editor_property('mesh').get_anim_instance().montage_stop(0.0, None)   # any punch still playing


def punch(key, mine, theirs, label, shot):
    """Press key; this screen should play `mine`, the server `theirs`; capture at the reach."""
    def go():
        clear()
        lib.send_verification_gameplay_key(client, key)
        state['memo'] = {'key': key, 'mine': mine, 'theirs': theirs, 'label': label, 'shot': shot, 't': time.monotonic()}
        return .25 if shot else .05
    def check():
        m = state['memo']
        here, there = name(pawn.get_last_swing_animation()), name(owner.get_last_swing_animation())
        if shot:
            unreal.SystemLibrary.execute_console_command(client_world, f'Shot showui filename="{SHOTS / (shot + ".png")}"')
        report['seen'].append({'label': label, 'key': key, 'client': here, 'server': there})
        assert here == mine, f'{label}: the client played {here}, expected {mine}'
        if theirs is not None:
            # The server learns of the swing a moment later.
            return ('wait_server', theirs)
        report['checks'].append(label)
        return 1.2
    return [go, check]


def nothing(key, label):
    def go():
        clear()
        state['last0'] = pawn.get_last_swing_animation()
        lib.send_verification_gameplay_key(client, key)
        return .6
    def check():
        assert pawn.get_last_swing_animation() == state['last0'], f'{label}: {key} played {name(pawn.get_last_swing_animation())}'
        report['checks'].append(label)
        return 1.2
    return [go, check]


def setup():
    for p in (owner, pawn):
        assert p.teleport(SPOT, unreal.Rotator())
    client.set_control_rotation(unreal.Rotator(0, -5, 0))
    held = owner.get_equipment_component().get_equipped_item(unreal.EWEquipmentSlot.MAIN_HAND)
    assert held is None, f'the survivor starts with {held.get_name()} in hand'
    pawn.set_first_person_view(False)
    return 2.0


def first_person():
    pawn.set_first_person_view(True)
    return 1.5


def third_person():
    pawn.set_first_person_view(False)
    return 1.5


def equip_axe():
    assert lib.send_verification_equipment_request(client, axe, unreal.EWEquipmentSlot.MAIN_HAND)
    return 2.0


def axe_swing():
    clear()
    state['last0'] = pawn.get_last_swing_animation()
    lib.send_verification_gameplay_key(client, 'LeftMouseButton')
    return .6


def axe_swung():
    got = name(pawn.get_last_swing_animation())
    assert got and 'Punch' not in got and 'MM_Attack' not in got, f'with the axe in hand Left Mouse played {got}'
    report['checks'].append(f'With the axe in hand Left Mouse swings it ({got}), no punch')
    return 1.2


R, L, FPR, FPL = 'MM_Attack_01', 'MM_Attack_02', 'AS_PunchFP_Right_v1', 'AS_PunchFP_Left_v1'
STEPS = [setup,
         *punch('RightMouseButton', R, R, 'Third person: Right Mouse punches with the right arm', '01_third_right_mouse'),
         *punch('LeftMouseButton', L, L, 'Third person: Left Mouse punches with the left arm', '02_third_left_mouse'),
         *punch('Gamepad_RightTrigger', R, R, 'Third person: RT punches with the right arm', None),
         *punch('Gamepad_LeftTrigger', L, L, 'Third person: LT punches with the left arm', None),
         first_person,
         *punch('RightMouseButton', FPR, R, 'First person: the right fist thrown out in front; others see the right hook', '03_first_right'),
         *punch('LeftMouseButton', FPL, L, 'First person: the left fist thrown out in front; others see the left hook', '04_first_left'),
         *punch('Gamepad_RightTrigger', FPR, R, 'First person: RT, right fist', None),
         *punch('Gamepad_LeftTrigger', FPL, L, 'First person: LT, left fist', None),
         third_person, equip_axe, axe_swing, axe_swung,
         *nothing('RightMouseButton', 'With the axe in hand Right Mouse does nothing'),
         *nothing('Gamepad_LeftTrigger', 'With the axe in hand LT does nothing')]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['h'])
    report.update(success=error is None, error=error)
    RESULT.write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPUNCHES success={error is None} error={error}')


def tick(delta):
    now = time.monotonic()
    try:
        if state.get('poll'):
            label, theirs, deadline = state['poll']
            got = name(owner.get_last_swing_animation())
            if got == theirs:
                report['checks'].append(label)
                state['poll'] = None
                state['at'] = now + 1.2
            elif now > deadline:
                raise AssertionError(f'{label}: the server shows {got}, expected {theirs}')
            return
        if now < state['at']:
            return
        if state['i'] >= len(STEPS):
            finish()
            return
        r = STEPS[state['i']]()
        state['i'] += 1
        if isinstance(r, tuple) and r[0] == 'wait_server':
            state['poll'] = (state['memo']['label'], r[1], now + 5.0)
        else:
            state['at'] = now + (r if isinstance(r, float) else .5)
    except Exception as error:
        finish(repr(error))


state['h'] = unreal.register_slate_post_tick_callback(tick)
