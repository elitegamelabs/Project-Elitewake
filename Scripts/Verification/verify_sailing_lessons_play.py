"""Play: the optional sailing lessons (FUTURE_IMPLEMENTATIONS Part 8, 64; November 8). Listen server plus one client:
    Scripts/Verification/run_play_check_once.ps1 -Check verify_sailing_lessons_play.py -Result SailingLessonsPlayResult.json -Players 2 -Kit 1
The client owns the sloop at Saltreach and asks the harbor master for lessons through the dialogue window. Each step's
prompt shows on the client's screen; doing the thing moves the lesson on:
  1 aboard  2 anchor up  3 under way (her sails set by the server's own station calls)  4 the helm taken and steered with
  the client's D key  5 the hold opened at the hatch through the client's interaction  6 anchor down  7 read, then done.
Then the lessons start again and are stopped from the harbor master (replayable, skippable).
Writes Saved/SailingLessonsPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'SailingLessonsPlayResult.json')
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
host = next(c for c in pcs if c.has_authority())
server_world = worlds[pcs.index(host)]
client_world = worlds[pcs.index(client)]
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
report = {'checks': [], 'prompts': {}}
state = {'phase': 'setup', 'at': time.monotonic() + 6, 'handle': None, 'deadline': 0}


def pid(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter)
             if pid(p) == pid(client.get_controlled_pawn()))
owner_pc = owner.get_controller()


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **{k: str(v) for k, v in values.items()}})
    assert ok, f'{label}: {values}'


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    lib.send_verification_gameplay_key_state(client, 'D', False)
    report.update(success=error is None, error=error, finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    RESULT.write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK SailingLessons success={error is None} error={error}')


def harbor():
    return next(a for a in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWHarborMaster)
                if str(a.get_editor_property('npc_name')) == 'Captain Ines Calder')


def peer(actor, cls):
    return next(a for a in unreal.GameplayStatics.get_all_actors_of_class(client_world, cls) if a.get_name() == actor.get_name())


def lessons():
    return client.get_lessons()


def prompt():
    widget = next((w for w in unreal.WidgetLibrary.get_all_widgets_of_class(client_world, unreal.EWArrivalPromptWidget, False)
                   if w.get_owning_player() == client), None)
    return str(widget.get_displayed_prompt()) if widget else ''


def stand_before_master():
    master = harbor()
    loc, fwd = master.get_actor_location(), master.get_actor_forward_vector()
    owner.teleport(unreal.Vector(loc.x + fwd.x * 220, loc.y + fwd.y * 220, loc.z + 100), unreal.Rotator())
    eye, _ = owner.get_actor_eyes_view_point()
    client.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, unreal.Vector(loc.x, loc.y, loc.z + 120)))


def board():
    ship = state['ship']
    owner.teleport(ship.get_actor_location() + unreal.Vector(0, 0, ship.get_deck_height() + 120), ship.get_actor_rotation())


def look_at_hatch():
    ship = state['ship']
    hatch = ship.get_cargo_hatch_world()
    local = ship.get_actor_transform().inverse_transform_location(hatch)
    spot = ship.get_actor_transform().transform_location(unreal.Vector(local.x + 140, local.y, local.z))
    owner.teleport(spot + unreal.Vector(0, 0, 100), unreal.Rotator())
    eye, _ = owner.get_actor_eyes_view_point()
    client.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, hatch))


def wait_step(step, seconds, then):
    """Move on when the client's lesson reaches `step` (or ends, for step -1), or fail after `seconds`."""
    state.update(phase='wait', want=step, deadline=time.monotonic() + seconds, then=then, at=time.monotonic() + .5)


def reached():
    want = state['want']
    if want == -1:
        return not lessons().is_in_lesson()
    return lessons().is_in_lesson() and lessons().get_step() >= want


def tick(_):
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        if p == 'wait':
            if reached():
                state['phase'] = state['then']
                state['at'] = time.monotonic() + .5
                return
            if time.monotonic() > state['deadline']:
                ship = state.get('ship')
                check(f'the lesson reaches step {state["want"]}', False, step=lessons().get_step(), active=lessons().is_in_lesson(),
                      prompt=prompt(), speed=ship.get_speed() if ship else None, fraction=ship.get_sail_fraction() if ship else None,
                      wind=ship.get_wind_factor() if ship else None, main=ship.get_mount_sail_state('Mainsail') if ship else None,
                      crewed=state.get('crewed'))
            return
        if p == 'setup':
            master = harbor()
            ships = [s for s in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWShip) if not s.is_sinking()]
            ship = min(ships, key=lambda s: (s.get_actor_location() - master.get_actor_location()).length())
            ship.set_ship_owner(owner_pc)
            ship.tow_to(master.get_editor_property('berths')[0].get_editor_property('where'))
            # A sold sloop comes bare: her wheel and two sails, as the sail-crew check fits them.
            for mount, item in (('Helm', 'DA_TestShipHelm'), ('Mainsail', 'DA_TestSailMedium'), ('Headsail', 'DA_TestSailSmall')):
                if not ship.get_fitting(mount):
                    ship.verification_install_fitting(mount, unreal.load_asset(f'/Game/Elitewake/Items/Testing/{item}'))
            check('the sloop has her helm and both sails', all(ship.get_fitting(m) for m in ('Helm', 'Mainsail', 'Headsail')))
            state['ship'] = ship
            stand_before_master()
            state.update(phase='talk', at=time.monotonic() + 2)
        elif p == 'talk':
            check('no lesson before asking', not lessons().is_in_lesson())
            check('the client talks to the harbor master', lib.send_verification_interaction_request(client, peer(harbor(), unreal.EWHarborMaster)))
            state.update(phase='ask', at=time.monotonic() + 1.5)
        elif p == 'ask':
            check('the window opens', client.is_dialogue_open())
            check('the client asks for lessons', lib.send_verification_dialogue_choice(client, peer(harbor(), unreal.EWHarborMaster), 'LessonsStart'))
            wait_step(0, 5, 'started')
        elif p == 'started':
            # Escape through the window, as a player leaves it (a close started from editor Python stays on the client).
            lib.send_verification_ui_key(client, 'Escape')
            state.update(phase='step1', at=time.monotonic() + 1)
        elif p == 'step1':
            report['prompts']['1'] = prompt()
            check('step 1 is shown on the client', 'Sailing 1/7' in prompt(), prompt=prompt())
            board()
            wait_step(1, 6, 'step2')
        elif p == 'step2':
            report['prompts']['2'] = prompt()
            check('step 2 asks for the anchor', 'Sailing 2/7' in prompt(), prompt=prompt())
            check('the anchor comes up', state['ship'].set_anchored(owner, False))
            wait_step(2, 6, 'step3')
        elif p == 'step3':
            report['prompts']['3'] = prompt()
            check('step 3 asks for sail', 'Sailing 3/7' in prompt(), prompt=prompt())
            ship = state['ship']
            state['crewed'] = ship.crew_every_sail()
            # To the wheel: the helm mount, as a player walks up to it.
            helm = next(m for m in ship.get_editor_property('definition').get_editor_property('mounts')
                        if m.get_editor_property('type') == unreal.EWShipMountType.HELM)
            at = ship.get_actor_transform().transform_location(helm.get_editor_property('transform').translation)
            owner.teleport(at - ship.get_actor_forward_vector() * 90 + unreal.Vector(0, 0, 100), ship.get_actor_rotation())
            state.update(phase='helm', at=time.monotonic() + 1)
        elif p == 'helm':
            ship = state['ship']
            check('the helm is taken to set the crewed sails', ship.take_helm(owner))
            report['menu_blocked'] = owner_pc.get_interaction_component().is_menu_blocked()
            report['helmsman'] = str(ship.get_helmsman()) if hasattr(ship, 'get_helmsman') else 'n/a'
            state['stepped'] = [ship.step_sails(owner, 1) for _ in range(4)]
            report['stepped'] = state['stepped']
            wait_step(3, 40, 'step4')
        elif p == 'step4':
            report['prompts']['4'] = prompt()
            report['speed'] = state['ship'].get_speed()
            check('step 4 asks for the helm', 'Sailing 4/7' in prompt(), prompt=prompt())
            check('the client presses D to steer', lib.send_verification_gameplay_key_state(client, 'D', True))
            wait_step(4, 8, 'step5')
        elif p == 'step5':
            lib.send_verification_gameplay_key_state(client, 'D', False)
            report['prompts']['5'] = prompt()
            check('step 5 asks for the hold', 'Sailing 5/7' in prompt(), prompt=prompt())
            ship = state['ship']
            for _ in range(4):
                ship.step_sails(owner, -1)
            ship.set_anchored(owner, True)       # hold her still while the client goes below
            ship.leave_helm(owner, True)
            state.update(phase='hatch', at=time.monotonic() + 4, tries=0)
        elif p == 'hatch':
            look_at_hatch()
            state.update(phase='open', at=time.monotonic() + 1)
        elif p == 'open':
            aimed = lib.get_verification_interaction_target(owner)
            report.setdefault('aimed', []).append(str(aimed.get_name()) if aimed else 'nothing')
            check('the client opens the hold at the hatch', lib.send_verification_interaction_request(client, peer(state['ship'], unreal.EWShip)))
            wait_step(5, 8, 'step6')
        elif p == 'step6':
            client.set_container_open(None)
            report['prompts']['6'] = prompt()
            check('step 6 asks to drop the anchor', 'Sailing 6/7' in prompt(), prompt=prompt())
            check('the anchor goes down', state['ship'].set_anchored(owner, False) and state['ship'].set_anchored(owner, True))
            wait_step(6, 6, 'step7')
        elif p == 'step7':
            report['prompts']['7'] = prompt()
            check('step 7 is about damage and bailing', 'Sailing 7/7' in prompt(), prompt=prompt())
            wait_step(-1, 20, 'done')
        elif p == 'done':
            check('the lessons end by themselves', not lessons().is_in_lesson() and lessons().get_finished_count() == 1,
                  finished=lessons().get_finished_count())
            check('the prompt goes', 'Sailing' not in prompt(), prompt=prompt())
            stand_before_master()
            state.update(phase='again', at=time.monotonic() + 2)
        elif p == 'again':
            lib.send_verification_interaction_request(client, peer(harbor(), unreal.EWHarborMaster))
            state.update(phase='again2', at=time.monotonic() + 1.5)
        elif p == 'again2':
            check('the lessons can be taken again', lib.send_verification_dialogue_choice(client, peer(harbor(), unreal.EWHarborMaster), 'LessonsStart'))
            wait_step(0, 5, 'stop')
        elif p == 'stop':
            check('restarted from step 1', lessons().get_step() == 0)
            check('and stopped', lib.send_verification_dialogue_choice(client, peer(harbor(), unreal.EWHarborMaster), 'LessonsStop'))
            wait_step(-1, 5, 'end')
        else:
            check('stopped part-way, nothing more is asked', not lessons().is_in_lesson() and lessons().get_finished_count() == 1)
            finish()
    except Exception as error:      # noqa: BLE001
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
