"""Play: ship names (FUTURE_IMPLEMENTATIONS Part 8, 12; November 8). Listen server plus one client:
    Scripts/Verification/run_play_check_once.ps1 -Check verify_ship_names_play.py -Result ShipNamesPlayResult.json -Players 2 -Kit 1
EW_PLAY_SHIPS=Schooner (the runner spawns a schooner, a second ship for the duplicate rule).
The client owns the sloop at Saltreach and talks to the harbor master, Captain Ines Calder, through the real dialogue window:
  1. "Register a name for my Sloop" opens the name box on the client.
  2. A blocked word is refused by the server; the ship stays unnamed.
  3. "Suggest a name" fills the box with a name that passes the rules.
  4. "Good Hope" is registered: the server and the client's copy of the ship carry it, the reply names her, both bows show it.
  5. The host, who does not own her, cannot rename her; another ship cannot take the same name.
  6. The client's map writes "Good Hope" beside her marker.
  7. Saved with the world and put back: she is the Good Hope again after being renamed in between.
Writes Saved/ShipNamesPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'ShipNamesPlayResult.json')
SLOT = 'ShipNamesTest'
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
host = next(c for c in pcs if c.has_authority())
server_world = worlds[pcs.index(host)]
client_world = worlds[pcs.index(client)]
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
report = {'checks': []}
state = {'phase': 0, 'at': time.monotonic() + 6, 'handle': None}


def pid(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter)
             if pid(p) == pid(client.get_controlled_pawn()))
owner_pc = owner.get_controller()
host_pawn = host.get_controlled_pawn()


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **{k: str(v) for k, v in values.items()}})
    assert ok, f'{label}: {values}'


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error, finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    RESULT.write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK ShipNames success={error is None} error={error}')


def peer(actor, cls):
    return next(a for a in unreal.GameplayStatics.get_all_actors_of_class(client_world, cls) if a.get_name() == actor.get_name())


def harbor():
    return next(a for a in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWHarborMaster)
                if str(a.get_editor_property('npc_name')) == 'Captain Ines Calder')


def window():
    return client.get_dialogue_widget()


def option_index(key):
    options = peer(harbor(), unreal.EWHarborMaster).get_dialogue_options_for(client.get_controlled_pawn())
    keys = [str(o.get_editor_property('key')) for o in options]
    return keys.index(key), options


def stand_before():
    master = harbor()
    loc, fwd = master.get_actor_location(), master.get_actor_forward_vector()
    owner.teleport(unreal.Vector(loc.x + fwd.x * 220, loc.y + fwd.y * 220, loc.z + 100), unreal.Rotator())
    eye, _ = owner.get_actor_eyes_view_point()
    client.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, unreal.Vector(loc.x, loc.y, loc.z + 120)))


def open_window():
    return lib.send_verification_interaction_request(client, peer(harbor(), unreal.EWHarborMaster))


def name_boards(ship):
    return [str(c.get_editor_property('text')) for c in ship.get_components_by_class(unreal.TextRenderComponent)
            if c.get_name().startswith('NameBoard') and c.is_visible()]


def submit(text):
    index, _ = option_index('NameShip')
    window().choose(index)
    window().set_entered_text(text)
    # Enter through the window, as a player presses it (a server request started from editor Python stays on the client).
    assert lib.send_verification_ui_key(client, 'Enter')


def tick(_):
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        if p == 0:
            master = harbor()
            ships = [s for s in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWShip) if not s.is_sinking()]
            near = sorted(ships, key=lambda s: (s.get_actor_location() - master.get_actor_location()).length())
            ship = near[0]
            ship.set_ship_owner(owner_pc)
            state['ship'] = ship
            state['other'] = next(s for s in ships if s != ship)
            # Into his approaches: towed to his first berth, as his own berth service does.
            check('towed in to a berth', ship.tow_to(master.get_editor_property('berths')[0].get_editor_property('where')))
            state.update(phase=10, at=time.monotonic() + 2)
        elif p == 10:
            master, ship = harbor(), state['ship']
            check('the harbor master finds the client\'s ship', master.find_ship_for(owner) == ship,
                  ship=ship.get_name(), distance=(ship.get_actor_location() - master.get_actor_location()).length())
            check('she has no name yet', ship.get_ship_name() == '')
            stand_before()
            state.update(phase=11, at=time.monotonic() + 2, tries=0)
        elif p == 11:
            check('the client asks to talk to the harbor master', open_window())
            state.update(phase=1, at=time.monotonic() + 1.5)
        elif p == 1:
            if not client.is_dialogue_open() and state['tries'] < 4:
                state['tries'] += 1
                stand_before()
                state.update(phase=11, at=time.monotonic() + 2)
                return
            check('the window is open on the client', client.is_dialogue_open(), tries=state['tries'])
            index, options = option_index('NameShip')
            check('the naming choice is open to her owner', options[index].get_editor_property('bEnabled'),
                  shown=options[index].get_editor_property('label'))
            window().choose(index)
            check('the name box opens', window().is_asking_for_text())
            window().suggest_text()
            suggested = window().get_entered_text()
            check('a suggestion fills the box', len(suggested) >= 2, suggested=suggested)
            window().set_entered_text('Hitler')
            check('Enter sends the name', lib.send_verification_ui_key(client, 'Enter'))
            check('the box closes on submit', not window().is_asking_for_text())
            state.update(phase=2, at=time.monotonic() + 2)
        elif p == 2:
            reply = str(client.get_last_dialogue_reply())


            check('a blocked word is refused', state['ship'].get_ship_name() == '' and 'will not register' in reply, reply=reply)
            submit('  Good   Hope ')
            state.update(phase=3, at=time.monotonic() + 2.5)
        elif p == 3:
            ship = state['ship']
            mine = peer(ship, unreal.EWShip)
            reply = str(client.get_last_dialogue_reply())
            check('the server registers her name, tidied', ship.get_ship_name() == 'Good Hope', name=ship.get_ship_name())
            check('the client\'s copy carries it', mine.get_ship_name() == 'Good Hope', name=mine.get_ship_name())
            check('the reply names her', 'Good Hope' in reply, reply=reply)
            boards = name_boards(mine)
            check('both bows show her name on the client', boards.count('GOOD HOPE') == 2, boards=boards)
            reason = str(ship.rename_or_refuse(host_pawn, 'Sea Thief')); ok = not reason
            check('the host, not her owner, cannot rename her', not ok and ship.get_ship_name() == 'Good Hope', reason=reason)
            other = state['other']
            other.set_ship_owner(owner_pc)
            reason = str(other.rename_or_refuse(owner, 'good hope')); ok = not reason
            check('another ship cannot take her name', not ok and 'already' in str(reason), reason=reason)
            client.close_dialogue()
            client.set_map_open(True)
            state.update(phase=4, at=time.monotonic() + 4)
        elif p == 4:
            maps = [w for w in unreal.WidgetLibrary.get_all_widgets_of_class(client_world, unreal.EWMapWidget, False)
                    if w.get_owning_player() == client and w.is_in_viewport()]
            shown = maps[0].get_shown_ship_names() if maps else []
            check('the client\'s map writes her name', 'Good Hope' in [str(s) for s in shown], shown=shown)
            client.set_map_open(False)
            owner.teleport(owner.get_actor_location() + unreal.Vector(0, 0, 50), unreal.Rotator())
            check('saved with the world', unreal.EWSurvivorSave.save_survivor(owner, SLOT, True))
            save = unreal.EWSurvivorSave.load_save(SLOT)
            names = [str(s.get_editor_property('ship_name')) for s in save.get_editor_property('ships')]
            check('the save holds her name', 'Good Hope' in names, names=names)
            reason = str(state['ship'].rename_or_refuse(owner, 'Brave Venture')); ok = not reason
            check('renamed in between', ok and state['ship'].get_ship_name() == 'Brave Venture', reason=reason)
            check('put back', save.apply_to(owner))
            state.update(phase=5, at=time.monotonic() + 2)
        else:
            names = [s.get_ship_name() for s in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWShip)]
            check('she is the Good Hope again', 'Good Hope' in names, names=names)
            finish()
    except Exception as error:      # noqa: BLE001
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
