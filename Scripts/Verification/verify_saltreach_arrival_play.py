"""Client acceptance for reaching Saltreach (CLAUDE.md Phase 1, slice 5, minutes 20-25; UEWArrivalComponent's town steps,
AEWStrongbox, AEWMerchant's empty-purse greeting, Scripts/Setup/build_saltreach_welcome.py).

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, without the test kit:
run_play_check.py with EW_PLAY_STARTER_KIT=0 (EW_PLAY_PLAYERS=2). The client's survivor has finished the arrival prompts and
carries what the Plains gave (wood, raw meat, the Stone Hatchet), with an empty purse. The server moves them between the scenes
(teleports stand in for walking); every action in a scene is the client's own key or request.

  1. At the track's end, inside the town, the client is told one thing: their purse is empty and a trader at the market buys
     what they gathered; the compass marks the nearest market trader, with the distance.
  2. E at Oskar Brann opens his window; he greets an empty purse by explaining it. Selling pays the purse on both machines
     and the prompt moves on to the strongbox, the compass with it.
  3. E at the strongbox opens "YOUR STRONGBOX"; A puts the hatchet in. It is in this player's store on server and client; the
     host's own store is empty, and the client's machine has no other player's store at all.
  4. The prompt moves on to the shipyard; E at Elias Thorne does that step.
  5. The prompt names the Company page; I, then Tab twice, opens it and the town steps are done: no prompt, no compass mark.
  6. Killed and respawned, the survivor's strongbox still holds the hatchet.
  7. The strongbox and the town steps survive a save and restore; E at the strongbox, Right, A takes the hatchet back.
Writes Saved/SaltreachArrivalPlayResult.json.
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
RESULT = Path(unreal.Paths.project_saved_dir(), 'SaltreachArrivalPlayResult.json')
SLOT = 'EW_SaltreachArrivalPlayCheck'
TOWN_STEPS = 0b1111   # Sell, Store, Shipyard, Company: this slice's; slice 6's (boat, hold, voyage) follow them
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
host = next(c for c in pcs if c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]
item = {'Wood': unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWood'),
        'Meat': unreal.load_asset('/Game/Elitewake/Items/Food/DA_RawMeat'),
        'Hatchet': unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWoodenAxe')}
assert all(item.values())
TOWN = unreal.EWTownStep


def player_id(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


def server_pawn():
    pawn = client.get_controlled_pawn()
    return next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter)
                if player_id(p) == player_id(pawn) and not p.is_actor_being_destroyed())


owner = server_pawn()
server_pc = owner.get_controller()
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None}
m = {}
checks = []


def pawn():
    return client.get_controlled_pawn()


def count(inventory, name):
    return inventory.get_item_count(item[name])


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


def strongbox():
    found = unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWStrongbox)
    assert len(found) == 1, f'{len(found)} strongboxes'
    return found[0]


def ground(x, y):
    hit = unreal.SystemLibrary.line_trace_single(server_world, unreal.Vector(x, y, 4000), unreal.Vector(x, y, -3000),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [owner, pawn()], unreal.DrawDebugTrace.NONE, True)
    return hit.to_tuple()[4].z if hit else 0.0


def place(x, y, look_at, z=None):
    spot = unreal.Vector(x, y, (ground(x, y) if z is None else z) + 100)
    for p in (owner, pawn()):
        p.set_actor_location(spot, False, True)
        p.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
    for controller, who in ((client, pawn()), (server_pc, owner)):
        eye = who.get_actor_eyes_view_point()[0]
        controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, look_at))


def before(actor, distance):
    at, ahead = actor.get_actor_location(), actor.get_actor_forward_vector()
    place(at.x + ahead.x * distance, at.y + ahead.y * distance, unreal.Vector(at.x, at.y, at.z + 60), z=at.z - 90 if isinstance(actor, unreal.EWTownsfolk) else at.z)


def bearing_to(at):
    here = pawn().get_actor_location()
    return math.degrees(math.atan2(at.y - here.y, at.x - here.x)) % 360


def arrival(who=None):
    return (who or owner).get_arrival_component()


def press(key, every=1.0, ui=False):
    if time.monotonic() - m.get('pressed', 0.0) > every:
        m['pressed'] = time.monotonic()
        assert (lib.send_verification_ui_key if ui else lib.send_verification_gameplay_key)(client, key)


# ---- 1: arriving ------------------------------------------------------------------------------------------------------

def arrive():
    arrival().set_step_index(99)                     # the arrival prompts are done
    arrival().set_town_steps_done(0)
    owner.get_wallet_component().set_copper(0)
    pack = owner.get_inventory_component()
    for name, n in (('Wood', 10), ('Meat', 3), ('Hatchet', 1)):
        assert pack.add_item(item[name], n) == n, name
    end, before_end = A.smoothed_route()[-1], A.smoothed_route()[-8]
    trader = townsfolk('Oskar Brann').get_actor_location()
    place(end[0], end[1], unreal.Vector(trader.x, trader.y, ground(end[0], end[1]) + 150))
    m['track_end_in_town'] = bool(unreal.EWSafeZone.find_at(server_world, owner.get_actor_location()))
    if not m['track_end_in_town']:
        # The track ends at the town's edge: a few more steps the way it runs, into the safe zone.
        dx, dy = end[0] - before_end[0], end[1] - before_end[1]
        k = 1500 / math.hypot(dx, dy)
        place(end[0] + dx * k, end[1] + dy * k, unreal.Vector(trader.x, trader.y, ground(end[0], end[1]) + 150))
    m['t'] = time.monotonic()


def told_to_sell():
    a = arrival()
    if not (a.is_complete() and arrival(pawn()).is_in_town() and 'purse is empty' in prompt()):
        return False
    c = compass()
    assert c.is_showing_place(), 'the compass shows no place'
    oskar = townsfolk('Oskar Brann').get_actor_location()
    off = abs((c.get_place_bearing() - bearing_to(oskar) + 180) % 360 - 180)
    assert off < 3, f'the compass marks {c.get_place_bearing():.0f}, Oskar is at {bearing_to(oskar):.0f}'
    m.update(sell_prompt=prompt(), sell_prompt_after_s=round(time.monotonic() - m['t'], 1), market_m=c.get_place_metres())
    return True


# ---- 2: selling -------------------------------------------------------------------------------------------------------

def to_oskar():
    before(townsfolk('Oskar Brann'), 200)


def oskar_explains():
    oskar = townsfolk('Oskar Brann')
    if not (client.is_dialogue_open() and client.get_dialogue_speaker() == peer(oskar)):
        press('E')
        return False
    line = str(client.get_dialogue_widget().get_shown_line())
    assert 'Empty purse' in line, line
    m['greeting'] = line
    return True


def sold():
    if owner.get_wallet_component().get_copper() == 0:
        if not m.get('chose'):
            m['chose'] = True
            assert lib.send_verification_dialogue_choice(client, peer(townsfolk('Oskar Brann')), 'SellAll')
        return False
    expected = 10 * item['Wood'].get_editor_property('sell_value_copper') + 3 * item['Meat'].get_editor_property('sell_value_copper')
    copper = owner.get_wallet_component().get_copper()
    assert copper == expected, f'{copper} copper, expected {expected}'
    if pawn().get_wallet_component().get_copper() != expected:
        return False
    assert count(owner.get_inventory_component(), 'Hatchet') == 1, 'the hatchet was sold'
    m['copper'] = copper
    return arrival(pawn()).is_town_step_done(TOWN.SELL)


def told_to_store():
    if client.is_dialogue_open():
        press('Escape', ui=True)
        m['turned'] = False
        return False
    if not m.get('turned'):
        # Facing Oskar, his "Talk to" prompt has the screen (one prompt at a time): the survivor turns toward the town.
        m['turned'] = True
        here = owner.get_actor_location()
        place(here.x, here.y, strongbox().get_actor_location(), z=here.z - 100)
        return False
    if 'strongbox' not in prompt():
        return False
    c = compass()
    off = abs((c.get_place_bearing() - bearing_to(strongbox().get_actor_location()) + 180) % 360 - 180)
    assert c.is_showing_place() and off < 3, f'compass {c.get_place_bearing():.0f} vs strongbox {bearing_to(strongbox().get_actor_location()):.0f}'
    m.update(store_prompt=prompt(), strongbox_m=c.get_place_metres())
    return True


# ---- 3: the strongbox -------------------------------------------------------------------------------------------------

def to_strongbox():
    before(strongbox(), 170)
    m['opened'] = False


def stored():
    box = server_pc.get_strongbox()
    if not m['opened']:
        press('E')
        if container():
            m['opened'] = True
            assert container().get_cursor_column() == 0
        return False
    if count(box, 'Hatchet') == 0:
        press('Gamepad_FaceButton_Bottom', every=.8, ui=True)       # A: the hatchet across, from the pack's first row
        return False
    mine = client.get_strongbox()
    if count(mine, 'Hatchet') != 1:
        return False
    assert count(owner.get_inventory_component(), 'Hatchet') == 0
    assert count(host.get_strongbox(), 'Hatchet') == 0, "the host's strongbox has it"
    others = [c for c in unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWPlayerController)]
    assert others == [client], f"the client's machine holds {len(others)} players"
    return arrival(pawn()).is_town_step_done(TOWN.STORE)


def told_about_yard():
    if container():
        press('Escape', ui=True)
        m['turned'] = False
        return False
    if not m.get('turned'):
        m['turned'] = True
        here = owner.get_actor_location()
        place(here.x, here.y, townsfolk('Elias Thorne').get_actor_location(), z=here.z - 100)
        return False
    if 'shipyard' not in prompt():
        return False
    c = compass()
    elias = townsfolk('Elias Thorne').get_actor_location()
    off = abs((c.get_place_bearing() - bearing_to(elias) + 180) % 360 - 180)
    assert c.is_showing_place() and off < 3, f'compass {c.get_place_bearing():.0f} vs Elias {bearing_to(elias):.0f}'
    m.update(yard_prompt=prompt(), yard_m=c.get_place_metres())
    return True


# ---- 4-5: the shipyard and the Company page --------------------------------------------------------------------------

def to_elias():
    before(townsfolk('Elias Thorne'), 200)


def spoke_to_elias():
    if not client.is_dialogue_open():
        press('E')
        return False
    return arrival(pawn()).is_town_step_done(TOWN.SHIPYARD)


def told_about_company():
    if client.is_dialogue_open():
        press('Escape', ui=True)
        m['turned'] = False
        return False
    if not m.get('turned'):
        m['turned'] = True
        here = owner.get_actor_location()
        place(here.x, here.y, strongbox().get_actor_location(), z=here.z - 100)
        return False
    if 'Company' not in prompt():
        return False
    assert not compass().is_showing_place(), 'the Company page is not a place'
    m['company_prompt'] = prompt()
    m['tabs'] = 0
    return True


def slice5_done(a):
    return a.get_town_steps_done() & TOWN_STEPS == TOWN_STEPS


def company_opened():
    if not client.is_inventory_open():
        press('I')
        return False
    if m['tabs'] < 2:
        if time.monotonic() - m.get('pressed', 0.0) > .6:
            m['pressed'] = time.monotonic()
            assert lib.send_verification_ui_key(client, 'Tab')
            m['tabs'] += 1
        return False
    if not (slice5_done(arrival()) and slice5_done(arrival(pawn()))):
        return False
    m['section'] = client.get_inventory_widget().get_selected_section()
    return True


def town_done():
    if client.is_inventory_open():
        press('Escape', ui=True)
        return False
    if time.monotonic() - m['pressed'] < 2.5:
        return False
    # The town's own four are done; the next is slice 6's (buy a boat), shown on the compass at Elias Thorne.
    assert 'first boat' in prompt(), prompt()
    assert compass().is_showing_place()
    return True


# ---- 6-7: kept through death, save and restore -----------------------------------------------------------------------

def die():
    owner.get_survival_component().apply_damage(1000.0)


def respawned():
    global owner
    if owner.get_survival_component().is_dead():
        w = next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(client_world, unreal.EWDeathWidget, False) if w.get_owning_player() == client)
        if w.is_respawn_available():
            press('Enter', every=1.5, ui=True)
        return False
    owner = server_pawn()
    if owner.get_survival_component().is_dead() or owner.get_controller() != server_pc:
        return False
    assert count(server_pc.get_strongbox(), 'Hatchet') == 1 and count(client.get_strongbox(), 'Hatchet') == 1, 'the strongbox lost the hatchet'
    return True


def saved_and_restored():
    assert unreal.EWSurvivorSave.save_survivor(owner, SLOT, False), 'save failed'
    box = server_pc.get_strongbox()
    box.remove_item(item['Hatchet'], 1)
    arrival().set_town_steps_done(0)
    assert unreal.EWSurvivorSave.load_save(SLOT).apply_to(owner), 'restore failed'
    unreal.GameplayStatics.delete_game_in_slot(SLOT, 0)
    assert count(box, 'Hatchet') == 1, 'the restored strongbox is empty'
    assert slice5_done(arrival()), 'the town steps were not restored'
    return True


def to_strongbox_again():
    before(strongbox(), 170)
    m['opened'] = False


def taken_back():
    if not m['opened']:
        press('E')
        if container():
            m['opened'] = True
        return False
    if count(owner.get_inventory_component(), 'Hatchet') == 0:
        w = container()
        press('Right' if w.get_cursor_column() != 1 else 'Gamepad_FaceButton_Bottom', every=.7, ui=True)
        return False
    return count(server_pc.get_strongbox(), 'Hatchet') == 0 and count(pawn().get_inventory_component(), 'Hatchet') == 1


STEPS = [
    ('Inside the town at the track\'s end, one prompt: the purse is empty, sell to a market trader; the compass marks the nearest', arrive, told_to_sell, 12),
    ('E at Oskar Brann opens his window; he explains the empty purse', to_oskar, oskar_explains, 8),
    ('Selling pays the purse on both machines and does the sell step; the hatchet is kept', lambda: None, sold, 8),
    ('The prompt and the compass move on to the strongbox', lambda: None, told_to_store, 8),
    ('E at the strongbox, A: the hatchet is in this player\'s store alone, on server and client', to_strongbox, stored, 15),
    ('The prompt and the compass move on to the shipyard', lambda: None, told_about_yard, 8),
    ('E at Elias Thorne does the shipyard step', to_elias, spoke_to_elias, 8),
    ('The prompt names the Company page; the compass marks no place', lambda: None, told_about_company, 8),
    ('I, then Tab twice, opens the Company page; the town steps are done on both machines', lambda: None, company_opened, 10),
    ('Then no prompt and no compass mark', lambda: None, town_done, 8),
    ('Killed and respawned, the strongbox still holds the hatchet', die, respawned, 15),
    ('The strongbox and the town steps survive a save and restore', lambda: None, saved_and_restored, 5),
    ('E at the strongbox, Right, A takes the hatchet back into the pack', to_strongbox_again, taken_back, 15),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    out = {k: v for k, v in m.items() if k not in ('t', 'pressed', 'chose', 'opened', 'tabs', 'turned')}
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': out}, indent=2, default=str), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK SaltreachArrival success={error is None} error={error}')


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
                               f'interaction {str(client.get_interaction_widget().get_displayed_prompt())!r}')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
