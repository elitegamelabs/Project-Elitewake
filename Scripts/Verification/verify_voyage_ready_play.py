"""Client acceptance for making the first voyage ready (CLAUDE.md Phase 1, slice 6, minutes 25-30; UEWArrivalComponent's boat,
provision and voyage steps, AEWShip::bHeldByYard, AEWShipwright::BuyShip, Scripts/Setup/build_voyage_ready.py).

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, without the test kit:
run_play_check.py with EW_PLAY_STARTER_KIT=0 and EW_PLAY_YARD_SHIPS=held (EW_PLAY_PLAYERS=2). The client's survivor has done the arrival and the town's first
four steps, and carries what a first session gathers: 40 Wood and 2 Cooked Meat, with 5 Copper. The server moves them between the
scenes (teleports stand in for walking and for the crossing itself); every action in a scene is the client's own key or request.

  1. The sloop moored at the east dock is the shipyard's: nobody may take her helm, and her hold says so.
  2. In town the prompt says to buy a raft from Elias Thorne; the compass marks him.
  3. Bess Harrow's wood job pays 70 Copper for 20 Wood (75 in the purse).
  4. Elias sells the raft for 60: she is afloat at the slipway, the client's, and the prompt moves on to loading her hold; the
     compass marks her.
  5. Marta Vell sells an empty waterskin for 15; held, E at the town well fills it.
  6. E at the raft's hold, then A for each stack, loads 2 food, the full waterskin and 20 wood; the provisions step is done on
     both machines.
  7. The prompt names the first voyage, the Swamp island, and the compass marks it with its distance.
  8. Arriving on the Swamp island (a teleport stands in for the crossing) finishes the steps: no prompt, no mark.
  9. The yard's hold on the sloop, the raft's owner and the steps survive a save and restore.
Writes Saved/VoyageReadyPlayResult.json.
"""
import json
import math
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import world_layout as W  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'VoyageReadyPlayResult.json')
SLOT = 'EW_VoyageReadyPlayCheck'
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]
ITEMS = '/Game/Elitewake/Items'
item = {'Wood': unreal.load_asset(f'{ITEMS}/Testing/DA_TestWood'),
        'Meat': unreal.load_asset(f'{ITEMS}/Food/DA_CookedMeat'),
        'Skin': unreal.load_asset(f'{ITEMS}/Testing/DA_TestHideWaterFlask'),
        'Full': unreal.load_asset(f'{ITEMS}/Testing/DA_TestWaterskinFull')}
assert all(item.values())
RAFT = unreal.load_asset('/Game/Elitewake/Ships/DA_Ship_Raft')
SLOOP = unreal.load_asset('/Game/Elitewake/Ships/DA_Ship_Sloop')
TOWN = unreal.EWTownStep
HAND = unreal.EWEquipmentSlot.MAIN_HAND


def player_id(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


pawn = client.get_controlled_pawn()
owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if player_id(p) == player_id(pawn))
server_pc = owner.get_controller()
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None}
m = {}
checks = []


def count(who, name):
    return who.get_inventory_component().get_item_count(item[name])


def prompt():
    return str(client.get_arrival_prompt_widget().get_displayed_prompt())


def compass():
    return next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(client_world, unreal.EWCompassWidget, False) if w.get_owning_player() == client)


def container():
    shown = [w for w in unreal.WidgetLibrary.get_all_widgets_of_class(client_world, unreal.EWContainerWidget, False) if w.is_in_viewport()]
    return shown[0] if shown else None


def townsfolk(name):
    return next(a for a in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWTownsfolk) if str(a.get_editor_property('npc_name')) == name)


def peer(actor):
    return next(a for a in unreal.GameplayStatics.get_all_actors_of_class(client_world, actor.get_class()) if a.get_name() == actor.get_name())


def ships(world=server_world):
    return [s for s in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWShip) if not s.is_actor_being_destroyed()]


def sloop():
    return next(s for s in ships() if s.get_editor_property('definition') == SLOOP)


def raft():
    found = [s for s in ships() if s.get_editor_property('definition') == RAFT]
    return found[0] if found else None


def ground(x, y, top=4000):
    hit = unreal.SystemLibrary.line_trace_single(server_world, unreal.Vector(x, y, top), unreal.Vector(x, y, -3000),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [owner, pawn], unreal.DrawDebugTrace.NONE, True)
    return hit.to_tuple()[4].z if hit else 0.0


def place(x, y, look_at, z=None):
    spot = unreal.Vector(x, y, (ground(x, y) if z is None else z) + 100)
    for p in (owner, pawn):
        p.set_actor_location(spot, False, True)
        p.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
    for controller, who in ((client, pawn), (server_pc, owner)):
        eye = who.get_actor_eyes_view_point()[0]
        controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, look_at))


def before(actor, distance):
    at, ahead = actor.get_actor_location(), actor.get_actor_forward_vector()
    place(at.x + ahead.x * distance, at.y + ahead.y * distance, unreal.Vector(at.x, at.y, at.z + 60), z=at.z - 90)


def bearing_to(at):
    here = pawn.get_actor_location()
    # A compass bearing, clockwise from north; north is the world's +Y (Source/EW/World/EWNorth.h; owner, November 1).
    return (math.degrees(math.atan2(at.y - here.y, at.x - here.x)) - 90) % 360


def marks(at, label):
    c = compass()
    off = abs((c.get_place_bearing() - bearing_to(at) + 180) % 360 - 180)
    assert c.is_showing_place() and off < 3, f'{label}: compass {c.get_place_bearing():.0f}, actual {bearing_to(at):.0f}'
    return c.get_place_metres()


def arrival(who=None):
    return (who or owner).get_arrival_component()


def press(key, every=1.0, ui=False):
    if time.monotonic() - m.get('pressed', 0.0) > every:
        m['pressed'] = time.monotonic()
        assert (lib.send_verification_ui_key if ui else lib.send_verification_gameplay_key)(client, key)


def talk(name, then):
    """E at a townsperson until the window opens, then one choice, then Escape; True once `then()` holds."""
    npc = townsfolk(name)
    if not m.get('chosen'):
        if not (client.is_dialogue_open() and client.get_dialogue_speaker() == peer(npc)):
            press('E')
            return False
        m['chosen'] = True
        assert lib.send_verification_dialogue_choice(client, peer(npc), m['choice'])
        return False
    if not then():
        return False
    if client.is_dialogue_open():
        press('Escape', ui=True)
        return False
    return True


def go_talk(name, choice):
    before(townsfolk(name), 200)
    m.update(choice=choice, chosen=False)


# ---- 1-2 ------------------------------------------------------------------------------------------------------------

def setup():
    a = arrival()
    a.set_step_index(99)
    a.set_town_steps_done(0b1111)                    # sold, stored, met the shipwright, seen the Company page
    owner.get_wallet_component().set_copper(5)
    pack = owner.get_inventory_component()
    for name, n in (('Wood', 40), ('Meat', 2)):
        assert pack.add_item(item[name], n) == n, name
    assert raft() is None, 'a raft is already afloat'


def sloop_is_the_yards():
    s = sloop()
    assert s.get_editor_property('held_by_yard'), 'the moored sloop is not the yard\'s'
    assert s.is_owned() and s.get_owner_name() == 'Saltreach shipyard', s.get_owner_name()
    assert not s.is_shipmate(owner), 'a survivor counts as her crew'
    assert not s.take_helm(owner), 'her helm was taken'
    assert townsfolk('Elias Thorne').find_held_ship(SLOOP) == s
    m['sloop_at'] = [round(v) for v in (s.get_actor_location().x, s.get_actor_location().y)]
    return True


def to_town():
    elias = townsfolk('Elias Thorne').get_actor_location()
    x, y = W.PORTS['Plains'].world(-600, -200)           # the town square
    place(x, y, unreal.Vector(elias.x, elias.y, elias.z + 80))


def told_to_buy():
    if 'buy your first boat' not in prompt():
        return False
    m['boat_prompt'] = prompt()
    m['elias_m'] = marks(townsfolk('Elias Thorne').get_actor_location(), 'Elias')
    return True


# ---- 3-4: earning and buying ------------------------------------------------------------------------------------------

def paid_for_wood():
    return owner.get_wallet_component().get_copper() == 75 and count(owner, 'Wood') == 20 and pawn.get_wallet_component().get_copper() == 75


def bought_raft():
    r = raft()
    if not r or not arrival(pawn).is_town_step_done(TOWN.BOAT):
        return False
    assert owner.get_wallet_component().get_copper() == 15
    assert r.is_owned() and r.is_shipmate(owner) and not r.get_editor_property('held_by_yard')
    m['raft_owner'] = r.get_owner_name()
    m['raft_reply'] = str(client.get_last_dialogue_reply())
    return True


def told_to_load():
    if client.is_dialogue_open():
        press('Escape', ui=True)
        return False
    if 'her hold' not in prompt():
        here = owner.get_actor_location()
        place(here.x, here.y, raft().get_actor_location(), z=here.z - 100)    # turned from Elias toward the slip
        return False
    m['load_prompt'] = prompt()
    m['raft_m'] = marks(raft().get_actor_location(), 'raft')
    return True


# ---- 5: water ---------------------------------------------------------------------------------------------------------

def bought_skin():
    return owner.get_wallet_component().get_copper() == 0 and count(owner, 'Skin') == 1


def to_well():
    x, y = W.PORTS['Plains'].world(-600 + 150, -900)
    well = W.PORTS['Plains'].world(-600, -900)
    assert lib.send_verification_equipment_request(client, item['Skin'], HAND)
    place(x, y, unreal.Vector(well[0], well[1], ground(x, y) + 70))


def filled():
    held = owner.get_equipment_component().get_equipped_item(HAND)
    if held == item['Full']:
        assert lib.send_verification_equipment_request(client, item['Full'], HAND, True)   # back into the pack
        return True
    shown = str(client.get_interaction_widget().get_displayed_prompt())
    if 'Fill' in shown:
        m['well_prompt'] = shown
        press('E', every=1.5)
    return False


# ---- 6: loading the hold ----------------------------------------------------------------------------------------------

def to_hold():
    r = raft()
    hatch = r.get_cargo_hatch_world()
    at = r.get_actor_location()
    place(at.x, at.y, hatch, z=at.z)
    m['opened'] = False


def loaded():
    if not m['opened']:
        # Hold E at the hatch: the owned request a held E sends once its time is up (verify_ship_cargo_play does the same).
        if time.monotonic() - m.get('pressed', 0.0) > 1.5:
            m['pressed'] = time.monotonic()
            copy = next(c for c in ships(client_world) if c.get_name() == raft().get_name())
            assert lib.send_verification_interaction_request(client, copy)
        if container():
            m['opened'] = True
        return False
    hold = raft().get_cargo()
    ready = hold.get_item_count(item['Wood']) >= 20 and hold.get_item_count(item['Meat']) >= 2 and hold.get_item_count(item['Full']) >= 1
    if not ready:
        press('Gamepad_FaceButton_Bottom', every=.8, ui=True)       # A: the pack's first stack across
        return False
    return arrival().is_town_step_done(TOWN.PROVISION) and arrival(pawn).is_town_step_done(TOWN.PROVISION)


def told_of_voyage():
    if container():
        press('Escape', ui=True)
        return False
    if 'Swamp island' not in prompt():
        if 'Open the hold' in str(client.get_interaction_widget().get_displayed_prompt()):
            # Facing the hold, its prompt has the screen (one at a time): the survivor turns out to sea, toward the Swamp.
            here, port = owner.get_actor_location(), W.PORTS['Swamp']
            place(here.x, here.y, unreal.Vector(port.cx, port.cy, here.z), z=here.z - 100)
        return False
    swamp = next(r for r in unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWClimateRegion)
                 if r.get_editor_property('region') == unreal.EWRegion.SWAMP)
    m['voyage_prompt'] = prompt()
    m['swamp_m'] = marks(swamp.get_actor_location(), 'Swamp')
    return True


# ---- 7-8: the crossing and after --------------------------------------------------------------------------------------

def cross():
    swamp = W.PORTS['Swamp']
    x, y = swamp.world(-1500, 0)                       # ashore behind the Swamp's port site
    place(x, y, unreal.Vector(swamp.cx, swamp.cy, ground(x, y) + 150))
    m['t'] = time.monotonic()


def arrived():
    if not (arrival().is_town_complete() and arrival(pawn).is_town_complete()):
        return False
    if time.monotonic() - m['t'] < 2.5:
        return False
    assert prompt() == '', prompt()
    assert not compass().is_showing_place()
    m['arrived_after_s'] = round(time.monotonic() - m['t'], 1)
    return True


def saved_and_restored():
    r, s = raft(), sloop()
    assert unreal.EWSurvivorSave.save_survivor(owner, SLOT, True), 'save failed'
    s.set_editor_property('held_by_yard', False)
    r.set_ship_owner(None)
    arrival().set_town_steps_done(0)
    assert unreal.EWSurvivorSave.load_save(SLOT).apply_to(owner), 'restore failed'
    unreal.GameplayStatics.delete_game_in_slot(SLOT, 0)
    assert sloop().get_editor_property('held_by_yard'), "the sloop is no longer the yard's"
    assert raft() and raft().is_owned() and raft().is_shipmate(owner), 'the raft lost her owner'
    assert arrival().is_town_complete()
    return True


STEPS = [
    ('The moored sloop is the shipyard\'s: owned by it, nobody\'s crew, her helm refused; Elias holds her for sale', setup, sloop_is_the_yards, 5),
    ('In town the prompt says to buy a raft from Elias Thorne; the compass marks him', to_town, told_to_buy, 10),
    ('Bess Harrow\'s wood job pays 70 Copper for 20 Wood, on both machines', lambda: go_talk('Bess Harrow', 'Job1'), lambda: talk('Bess Harrow', paid_for_wood), 10),
    ('Elias sells the raft for 60: afloat at the slipway, the client\'s; the boat step is done', lambda: go_talk('Elias Thorne', 'Ship0'), lambda: talk('Elias Thorne', bought_raft), 12),
    ('The prompt says to load her hold; the compass marks the raft', lambda: None, told_to_load, 10),
    ('Marta Vell sells an empty waterskin for 15', lambda: go_talk('Marta Vell', 'Buy5'), lambda: talk('Marta Vell', bought_skin), 10),
    ('Held, E at the town well fills it', to_well, filled, 12),
    ('E at the raft\'s hold, A for each stack: 2 food, the full waterskin and 20 wood loaded; the provisions step is done on both machines', to_hold, loaded, 20),
    ('The prompt names the first voyage, the Swamp island; the compass marks it with its distance', lambda: None, told_of_voyage, 10),
    ('Ashore on the Swamp island the steps are done: no prompt, no mark', cross, arrived, 15),
    ('The yard\'s hold on the sloop, the raft\'s owner and the steps survive a save and restore', lambda: None, saved_and_restored, 5),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    out = {k: v for k, v in m.items() if k not in ('t', 'pressed', 'chosen', 'choice', 'opened')}
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': out}, indent=2, default=str), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK VoyageReady success={error is None} error={error}')


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
            raise TimeoutError(f'not done within {timeout} s; prompt {prompt()!r}, '
                               f'interaction {str(client.get_interaction_widget().get_displayed_prompt())!r}, '
                               f'copper {owner.get_wallet_component().get_copper()}')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
