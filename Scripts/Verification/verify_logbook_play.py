"""Play: the captain's logbook (FUTURE_IMPLEMENTATIONS Part 8, 13; November 8). Listen server plus one client:
    Scripts/Verification/run_play_check_once.ps1 -Check verify_logbook_play.py -Result LogbookPlayResult.json -Players 2 -Kit 1
The client owns the sloop at Saltreach; the server tows her (the harbor master's pilots' own tow, which carries whoever is aboard)
through a short voyage while the client stands on her deck:
  1. Lying in harbour at the start writes nothing; registering her name does.
  2. Towed out to sea: "Departed Saltreach Freeport."
  3. Struck by round shot: a damage line with the hull's state.
  4. Towed past Copper Downs with the client aboard: the discovery is in her log as well as the client's journal.
  5. Back to her berth with 20 wood in the hold: "Arrived at Saltreach Freeport." and a line on the hold.
  6. The shipwright repairs her: a repair line naming the port.
  7. The client's copy of her carries the same log; the client's Journal shows "The Good Hope's log" with the lines.
  8. Saved with the world and put back: the log is whole and the reload writes no new port lines.
Writes Saved/LogbookPlayResult.json.
"""
import json
import math
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(unreal.Paths.project_dir(), 'Scripts', 'Setup')))
import world_layout as W  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'LogbookPlayResult.json')
SLOT = 'LogbookTest'
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


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **{k: str(v) for k, v in values.items()}})
    assert ok, f'{label}: {values}'


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error, finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    RESULT.write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK Logbook success={error is None} error={error}')


def harbor():
    return next(a for a in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWHarborMaster)
                if str(a.get_editor_property('npc_name')) == 'Captain Ines Calder')


def lines(ship):
    return [str(e.get_editor_property('text')) for e in ship.get_logbook()]


def peer(actor):
    return next(a for a in unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWShip) if a.get_name() == actor.get_name())


def board():
    """Set the client down on her deck, over her middle."""
    ship = state['ship']
    top = ship.get_actor_location() + unreal.Vector(0, 0, ship.get_deck_height() + 120)
    owner.teleport(top, ship.get_actor_rotation())


def tow(x, y, yaw):
    return state['ship'].tow_to(unreal.Transform(unreal.Vector(x, y, state['berth'].translation.z), unreal.Rotator(0, 0, yaw)))


def off_island(key, out=6000.0):
    """A spot at sea just off island `key`'s shore, inside its sighting reach."""
    i = W.island(key)
    a = math.atan2(-i.cy, -i.cx)          # the side facing the middle of the world
    r = i.radius(a) + out
    return i.cx + r * math.cos(a), i.cy + r * math.sin(a), math.degrees(a) + 90


def tick(_):
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        if p == 0:
            master = harbor()
            ships = [s for s in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWShip) if not s.is_sinking()]
            ship = min(ships, key=lambda s: (s.get_actor_location() - master.get_actor_location()).length())
            ship.set_ship_owner(owner_pc)
            state['ship'] = ship
            berth = master.get_editor_property('berths')[0].get_editor_property('where')
            state['berth'] = berth
            check('towed in to a berth', ship.tow_to(berth))
            state.update(phase=1, at=time.monotonic() + 5)
        elif p == 1:
            ship = state['ship']
            report['start_lines'] = lines(ship)
            check('lying in harbour at the start writes nothing', lines(ship) == [], lines=lines(ship), port=ship.get_port_call_name())
            check('she knows she lies in Saltreach', ship.get_port_call_name() == 'Saltreach Freeport', port=ship.get_port_call_name())
            check('named', str(ship.rename_or_refuse(owner, 'Good Hope')) == '')
            check('the name is logged', any('harbour book as the Good Hope' in l for l in lines(ship)), lines=lines(ship))
            ship.get_cargo().add_item(unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWood'), 20)
            board()
            state.update(phase=2, at=time.monotonic() + 1.5)
        elif p == 2:
            lane = harbor().get_editor_property('departure_lane')
            rot = lane.rotation.rotator()
            fwd = unreal.MathLibrary.get_forward_vector(rot)
            out = lane.translation + fwd * 60000
            check('towed out to sea', tow(out.x, out.y, rot.yaw))
            state.update(phase=3, at=time.monotonic() + 5)
        elif p == 3:
            ship = state['ship']
            check('departure logged', 'Departed Saltreach Freeport.' in lines(ship), lines=lines(ship), port=ship.get_port_call_name())
            hit = ship.get_actor_location() + ship.get_actor_right_vector() * 300
            ship.take_round_shot(hit, ship.get_actor_right_vector(), None)
            check('damage logged', any(l.startswith('Holed by round shot. Hull at') for l in lines(ship)), lines=lines(ship))
            x, y, yaw = off_island('Plains2')
            board()
            state.update(phase=4, at=time.monotonic() + 1, dest=(x, y, yaw))
        elif p == 4:
            x, y, yaw = state['dest']
            check('towed past Copper Downs with the client aboard', tow(x, y, yaw))
            state.update(phase=5, at=time.monotonic() + 4)
        elif p == 5:
            ship = state['ship']
            found = [str(d.get_editor_property('id')) for d in client.get_discoveries().get_discoveries()]
            report['aboard'] = str(unreal.EWShip.find_ship_carrying(owner)) if hasattr(unreal.EWShip, 'find_ship_carrying') else 'n/a'
            check('the client discovered Copper Downs', 'Plains2' in found, found=found)
            check('the discovery is in her log', 'Discovered Copper Downs.' in lines(ship), lines=lines(ship))
            berth = state['berth']
            check('towed home', ship.tow_to(berth))
            state.update(phase=6, at=time.monotonic() + 5)
        elif p == 6:
            ship = state['ship']
            check('arrival logged', 'Arrived at Saltreach Freeport.' in lines(ship), lines=lines(ship))
            check('the hold is noted', any(l.startswith('In the hold: 20') and 'Wood' in l for l in lines(ship)), lines=lines(ship))
            ship.repair_at_shipyard()
            check('the repair is logged with the port', 'Repaired by the shipwright at Saltreach Freeport.' in lines(ship), lines=lines(ship))
            state['count'] = len(lines(ship))
            client.set_inventory_open(True)
            state.update(phase=7, at=time.monotonic() + 2)
        elif p == 7:
            ship = state['ship']
            mine = peer(ship)
            check('the client\'s copy carries the same log', lines(mine) == lines(ship), client=len(lines(mine)), server=len(lines(ship)))
            menu = next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(client_world, unreal.EWInventoryWidget, False)
                        if w.get_owning_player() == client and w.is_in_viewport())
            menu.open_section(4)
            journal = menu.get_journal_panel()
            journal.refresh_discoveries()
            titles = [str(t) for t in journal.get_page_titles()]
            report['journal'] = titles
            check('the Journal has her log', "The Good Hope's log" in titles, titles=titles)
            journal.show_page(titles.index("The Good Hope's log"))
            client.set_inventory_open(False)
            board()
            check('saved with the world', unreal.EWSurvivorSave.save_survivor(owner, SLOT, True))
            save = unreal.EWSurvivorSave.load_save(SLOT)
            saved = next((s for s in save.get_editor_property('ships') if str(s.get_editor_property('ship_name')) == 'Good Hope'), None)
            check('the save holds her log', saved is not None and len(saved.get_editor_property('logbook')) == state['count'],
                  saved=None if saved is None else len(saved.get_editor_property('logbook')))
            check('put back', save.apply_to(owner))
            state.update(phase=8, at=time.monotonic() + 6)
        else:
            ships = [s for s in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWShip) if s.get_ship_name() == 'Good Hope']
            check('she is back', len(ships) == 1)
            check('her log is whole and the reload wrote no new lines', len(lines(ships[0])) == state['count'],
                  now=len(lines(ships[0])), before=state['count'], lines=lines(ships[0]))
            report['log'] = lines(ships[0])
            finish()
    except Exception as error:      # noqa: BLE001
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
