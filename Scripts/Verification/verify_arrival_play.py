"""Client acceptance for the Plains arrival (CLAUDE.md Phase 1, slice 1; Scripts/Setup/arrival_layout.py and build_arrival.py).

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, after build_arrival.py and
build_grass.py. Run unattended with run_play_check.py (EW_PLAY_PLAYERS=2). Everything the client does goes through its own
controller's keys and axes (keyboard, mouse and controller), never a server shortcut.

  1. Both survivors arrive at the south-shore spawn, the client facing toward Saltreach.
  2. The first view is safe and readable: no hostile creature within 100 m, the arrival oaks within the 70-degree view,
     a clear line from the client's eye to the top of Saltreach's lighthouse, the spring and track in place on both machines.
  3. No prompt covers the first view; then one prompt: look around (keyboard words).
  4. A nudge of the right stick switches it to controller words; the mouse finishes it, on server and client.
  5. W walks: done on both. 6. The controller's A jumps: done on both. 7. C crouches: done on both.
  8. At the spring the arrival prompt gives way to the interaction prompt; the controller's X drinks there: fresh water,
     and the arrival is finished on both, with nothing left on screen.
  9. Saved and restored, the survivor keeps their place in the arrival (finished, and part-way).
 10. The starter pond holds no piranhas.
Writes Saved/ArrivalPlayResult.json.
"""
import json
import math
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import arrival_layout as A  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'ArrivalPlayResult.json')
SLOT = 'EW_ArrivalPlayCheck'
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
host = next(c for c in pcs if c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]
pawn = client.get_controlled_pawn()
WORDS = {k: str(unreal.EWArrivalComponent.prompt_for(getattr(unreal.EWArrivalStep, k), False)) for k in ('LOOK', 'MOVE', 'JUMP', 'CROUCH', 'INTERACT')}
# Controller words name buttons with [Gamepad_...] tokens drawn as the pad's own icons (owner, November 1). This check pins
# the Xbox names (for the session only), so the plain words it reads do not depend on which pad is plugged in.
XBOX = {'Gamepad_Right2D': 'Right stick', 'Gamepad_Left2D': 'Left stick', 'Gamepad_FaceButton_Bottom': 'A',
        'Gamepad_FaceButton_Right': 'B', 'Gamepad_FaceButton_Left': 'X', 'Gamepad_FaceButton_Top': 'Y'}


def xbox_words(text):
    for key, name in XBOX.items():
        text = text.replace(f'[{key}]', name)
    return text


client.set_button_icons_choice(unreal.EWButtonIconsChoice.XBOX, False)
PAD = {k: xbox_words(str(unreal.EWArrivalComponent.prompt_for(getattr(unreal.EWArrivalStep, k), True))) for k in ('LOOK', 'MOVE', 'JUMP', 'CROUCH', 'INTERACT')}


def player_id(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if player_id(p) == player_id(pawn))
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}, 'held': []}
checks = []


def step_of(who):
    return who.get_arrival_component().get_step_index()


def both_at(n):
    return step_of(owner) == n and step_of(pawn) == n


def prompt():
    return str(client.get_arrival_prompt_widget().get_displayed_prompt())


def labelled(world, cls, start):
    return [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, cls) if str(a.get_actor_label()).startswith(start)]


def hold(key, down=True):
    lib.send_verification_gameplay_key_state(client, key, down)
    if down:
        state['held'].append(key)
    elif key in state['held']:
        state['held'].remove(key)


def release_all():
    for key in list(state['held']):
        hold(key, False)


# ---- checks ---------------------------------------------------------------------------------------------------------

def arrived():
    for who in (owner, host.get_controlled_pawn()):
        at = who.get_actor_location()
        d = math.hypot(at.x - A.SPAWN[0], at.y - A.SPAWN[1])
        assert d < 600, f'{who.get_name()} arrived {d / 100:.1f} m from the spawn'
    yaw = client.get_control_rotation().yaw
    off = A.relative(A.SPAWN_YAW, yaw)
    assert abs(off) < 10, f'client faces {yaw:.0f}, {off:.0f} degrees off'
    state['memo']['client_spawn_m'] = round(math.hypot(owner.get_actor_location().x - A.SPAWN[0], owner.get_actor_location().y - A.SPAWN[1]) / 100, 2)
    state['memo']['client_yaw'] = round(yaw, 1)
    return True


def readable():
    at = owner.get_actor_location()
    hostile = []
    for cls in (unreal.EWAnimal, unreal.EWFish):
        for c in unreal.GameplayStatics.get_all_actors_of_class(server_world, cls):
            d = c.get_editor_property('definition')
            p = c.get_actor_location()
            if d and d.get_editor_property('aggressive') and math.hypot(p.x - at.x, p.y - at.y) < 10000:
                hostile.append(str(c.get_actor_label()))
    assert not hostile, f'hostile within 100 m: {hostile}'
    oaks = labelled(server_world, unreal.EWHarvestTree, 'Arrival oak')
    assert len(oaks) == len(A.OAKS), f'{len(oaks)} arrival oaks'
    for o in oaks:
        p = o.get_actor_location()
        rel = A.relative(A.SPAWN_YAW, A.bearing(A.SPAWN[0], A.SPAWN[1], p.x, p.y))
        assert abs(rel) <= 35, f'{o.get_actor_label()} at {rel:.0f} degrees, outside the view'
    for world in (server_world, client_world):
        assert len(labelled(world, unreal.StaticMeshActor, 'Arrival track')) >= 8, 'track missing'
        assert labelled(world, unreal.EWWaterSource, 'Arrival spring'), 'spring missing'
    # The client's own eye to the lighthouse's top 8 m: one clear line (or one that meets the lighthouse itself) is enough.
    eye = pawn.get_actor_eyes_view_point()[0]
    lx, ly, lz = A.SALTREACH_LIGHT
    seen = []
    for drop in (0, 200, 400, 600, 800):
        hit = unreal.SystemLibrary.line_trace_single(client_world, eye, unreal.Vector(lx, ly, lz - drop), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                                                     False, [pawn], unreal.DrawDebugTrace.NONE, True)
        blocked = hit is not None and hit.to_tuple()[0]
        actor = hit.to_tuple()[9] if blocked else None
        label = str(actor.get_actor_label()) if actor else ''
        if not blocked or 'lighthouse' in label.lower():
            seen.append(drop)
        else:
            state['memo'].setdefault('lighthouse_blockers', []).append(label or str(actor))
    assert seen, f'nothing clear to the lighthouse: {state["memo"].get("lighthouse_blockers")}'
    state['memo']['lighthouse_clear_drops_cm'] = seen
    return True


def first_prompt():
    if not client.get_arrival_prompt_widget().is_prompt_visible():
        return False
    assert unreal.GameplayStatics.get_time_seconds(client_world) >= 2.5, 'a prompt covers the first view'
    assert prompt() == WORDS['LOOK'], f'first prompt {prompt()!r}'
    assert not str(client.get_interaction_widget().get_displayed_prompt()), 'two prompts at once'
    # Seen first this long into the client's game (the arrival waits 3 s so the first view is read without a prompt).
    state['memo']['first_prompt_seen_at_world_s'] = round(unreal.GameplayStatics.get_time_seconds(client_world), 1)
    return True


def stick_nudge():
    lib.send_verification_gameplay_axis(client, 'Gamepad_RightX', .4)


def controller_words():
    return prompt() == PAD['LOOK'] and step_of(pawn) == 0


def mouse_look():
    state['memo']['mouse_samples'] = 0


def looked():
    if both_at(1):
        return True
    lib.send_verification_gameplay_axis(client, 'MouseX', 6.0)
    state['memo']['mouse_samples'] += 1
    return False


def walk_prompt():
    return client.get_arrival_prompt_widget().is_prompt_visible() and prompt() == WORDS['MOVE']


def walk():
    hold('W')


def walked():
    if both_at(2):
        hold('W', False)
        return True
    return False


def jump_prompt():
    return client.get_arrival_prompt_widget().is_prompt_visible() and prompt() == WORDS['JUMP']


def jump():
    hold('Gamepad_FaceButton_Bottom')
    state['memo']['jump_at'] = time.monotonic()


def jumped():
    if time.monotonic() - state['memo']['jump_at'] > .3:
        hold('Gamepad_FaceButton_Bottom', False)
    return both_at(3)


def crouch_prompt():
    return client.get_arrival_prompt_widget().is_prompt_visible() and prompt() == PAD['CROUCH']


def crouch():
    hold('C')
    state['memo']['crouch_at'] = time.monotonic()


def crouched():
    if time.monotonic() - state['memo']['crouch_at'] > .15:
        hold('C', False)
    if both_at(4):
        return True
    return False


def to_spring():
    # Stand up again (C toggles), then stand at the spring's edge looking into the pool, as a player walking up to it would.
    if pawn.get_editor_property('is_crouched'):
        lib.send_verification_gameplay_key(client, 'C')
    owner.get_survival_component().set_hydration(80.0)
    state['memo']['hydration_before'] = 80.0
    water = labelled(server_world, unreal.StaticMeshActor, 'Arrival spring water')[0].get_actor_location()
    yaw = A.SPAWN_YAW + 180.0
    r = math.radians(yaw)
    x, y = water.x - 180 * math.cos(r), water.y - 180 * math.sin(r)
    for who in (owner, pawn):
        who.set_actor_location(unreal.Vector(x, y, water.z + 120), False, True)
    state['memo']['spring'] = [round(water.x), round(water.y), round(water.z)]


def aimed():
    water = state['memo']['spring']
    eye = pawn.get_actor_eyes_view_point()[0]
    dx, dy = water[0] - eye.x, water[1] - eye.y
    flat = math.hypot(dx, dy) - 50
    pitch = -math.degrees(math.atan2(eye.z - water[2], flat))
    client.set_control_rotation(unreal.Rotator(0, pitch, math.degrees(math.atan2(dy, dx))))
    target = lib.get_verification_interaction_target(pawn)
    return target is not None and str(target.get_actor_label()).startswith('Arrival spring')


def one_prompt_at_spring():
    interaction = str(client.get_interaction_widget().get_displayed_prompt())
    if not interaction:
        return False
    assert 'fresh water' in interaction.lower(), interaction
    assert not client.get_arrival_prompt_widget().is_prompt_visible(), 'arrival prompt over the interaction prompt'
    state['memo']['spring_prompt'] = interaction
    return True


def drink():
    lib.send_verification_gameplay_key(client, 'Gamepad_FaceButton_Left')


def drank():
    if owner.get_survival_component().get_hydration() <= state['memo']['hydration_before']:
        return False
    assert both_at(5), f'arrival not finished: server {step_of(owner)}, client {step_of(pawn)}'
    return not client.get_arrival_prompt_widget().is_prompt_visible()


def saved_and_restored():
    arrival = owner.get_arrival_component()
    assert unreal.EWSurvivorSave.save_survivor(owner, SLOT, False), 'save failed'
    arrival.set_step_index(0)
    assert unreal.EWSurvivorSave.load_save(SLOT).apply_to(owner), 'restore failed'
    assert arrival.get_step_index() == 5, f'restored finished arrival as step {arrival.get_step_index()}'
    arrival.set_step_index(2)
    assert unreal.EWSurvivorSave.save_survivor(owner, SLOT, False)
    arrival.set_step_index(5)
    assert unreal.EWSurvivorSave.load_save(SLOT).apply_to(owner)
    assert arrival.get_step_index() == 2, f'restored part-way arrival as step {arrival.get_step_index()}'
    arrival.set_step_index(5)
    unreal.GameplayStatics.delete_game_in_slot(SLOT, 0)
    return True


def no_piranhas():
    fish = [f for f in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWFish)
            if math.hypot(f.get_actor_location().x + 1700, f.get_actor_location().y - 1500) < 900]
    kinds = sorted({str(f.get_editor_property('definition').get_editor_property('display_name')) for f in fish})
    assert 'Piranha' not in kinds, kinds
    state['memo']['pond_fish'] = kinds
    return True


STEPS = [
    ('Both survivors arrive at the south-shore spawn, the client facing Saltreach', lambda: None, arrived, 10),
    ('The first view is safe and readable: no hostile within 100 m, oaks in view, the lighthouse in sight, spring and track on both machines',
     lambda: None, readable, 5),
    ('After the first view, one prompt: look around (keyboard words)', lambda: None, first_prompt, 10),
    ('A nudge of the right stick switches it to controller words', stick_nudge, controller_words, 3),
    ('The mouse looks around: done on server and client', mouse_look, looked, 8),
    ('Next prompt: W A S D to walk', lambda: None, walk_prompt, 5),
    ('W walks: done on server and client', walk, walked, 8),
    ('Next prompt: Space to jump (keyboard words, the keyboard last used)', lambda: None, jump_prompt, 5),
    ("The controller's A jumps: done on server and client", jump, jumped, 6),
    ('Next prompt: B to crouch (controller words, the controller last used)', lambda: None, crouch_prompt, 5),
    ('C crouches: done on server and client', crouch, crouched, 6),
    ('At the spring the survivor faces its water', to_spring, aimed, 6),
    ('There the interaction prompt alone shows: drink fresh water', lambda: None, one_prompt_at_spring, 5),
    ("The controller's X drinks: fresh water, and the arrival is finished on server and client, nothing left on screen", drink, drank, 6),
    ('Saved and restored, the survivor keeps their place in the arrival', lambda: None, saved_and_restored, 5),
    ('The starter pond holds no piranhas', lambda: None, no_piranhas, 5),
]


def finish(error=None):
    release_all()
    unreal.unregister_slate_post_tick_callback(state['handle'])
    state['memo']['server_step'] = step_of(owner)
    state['memo']['client_step'] = step_of(pawn)
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': state['memo']}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK Arrival success={error is None} error={error}')


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
            raise TimeoutError(f'not done within {timeout} s; steps server {step_of(owner)} client {step_of(pawn)}, prompt {prompt()!r}, '
                               f'interaction {str(client.get_interaction_widget().get_displayed_prompt())!r}')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
