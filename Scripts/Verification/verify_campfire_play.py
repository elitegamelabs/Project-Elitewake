"""Client acceptance for the campfire and the first cooked meal (CLAUDE.md Phase 1, slice 3; Source/EW/World/EWCampfire and
Scripts/Setup/build_campfire.py).

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, without the test kit:
run_play_check.py with EW_PLAY_STARTER_KIT=0 (EW_PLAY_PLAYERS=2). Gathering is slice 2's check, so the server hands the
client the wood, stones and berries; everything after that goes through the client's own keys, mouse, menu and hold.

  1. The survivor knows the Campfire and Cooked Berry Dish recipes; with nothing lit near, the dish says to cook by a fire.
  2. Enter in the menu makes a Campfire from 5 wood and 3 stones (5 s), on both machines.
  3. Held, its ghost shows blue on open ground ahead; Left Mouse lays it there: a lit fire on both machines, the hand empty.
  4. A second campfire held right beside it shows red, and Left Mouse lays nothing.
  5. By the fire the dish can be made: Enter cooks 3 berries into a Cooked Berry Dish in its 6 s, on both machines.
  6. Eaten, it gives 15 hunger and 2 health.
  7. E with wood in the pack adds it to the fire: it burns 3 minutes longer.
  8. Burnt down it goes dark on both machines; held E takes the cold ring up again as a Campfire.
  9. Laid again and saved, the burning fire comes back after a restore.
Writes Saved/CampfirePlayResult.json.
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
RESULT = Path(unreal.Paths.project_saved_dir(), 'CampfirePlayResult.json')
SLOT = 'EW_CampfirePlayCheck'
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]
pawn = client.get_controlled_pawn()
HAND = unreal.EWEquipmentSlot.MAIN_HAND
I = '/Game/Elitewake/Items/'
item = {'Wood': unreal.load_asset(I + 'Testing/DA_TestWood'), 'Stone': unreal.load_asset(I + 'Testing/DA_TestStone'),
        'Berry': unreal.load_asset(I + 'Testing/DA_TestAzulBerry'), 'Campfire': unreal.load_asset(I + 'Building/DA_Campfire'),
        'Dish': unreal.load_asset(I + 'Food/DA_CookedBerryDish')}
recipe = {n: unreal.load_asset(f'/Game/Elitewake/Crafting/Testing/DA_Recipe{n}') for n in ('Campfire', 'CookedBerryDish')}
assert all(item.values()) and all(recipe.values())


def player_id(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if player_id(p) == player_id(pawn))
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None}
m = {}
checks = []


def count(who, name):
    return who.get_inventory_component().get_item_count(item[name])


def both(name, n):
    return count(owner, name) == n and count(pawn, name) == n


def fires(world):
    return [f for f in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWCampfire) if not f.is_actor_being_destroyed()]


def menu():
    return next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(client_world, unreal.EWInventoryWidget, False)
                if w.get_owning_player() == client and w.is_in_viewport())


def ground(x, y):
    hit = unreal.SystemLibrary.line_trace_single(server_world, unreal.Vector(x, y, 3000), unreal.Vector(x, y, -3000),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [owner], unreal.DrawDebugTrace.NONE, True)
    return hit.to_tuple()[4] if hit else unreal.Vector(x, y, 0)


# A stand on the grass just inland of the spawn, off the track, facing a spot 2.5 m ahead.
STAND = (A.SPAWN[0] + 276.0 * 3, A.SPAWN[1] + 961.0 * 3)       # 9 m inland (toward the oaks) of the spawn
FACING = 74.0                                                   # inland


def stand_and_aim(ahead=250.0, side=0.0):
    g = ground(*STAND)
    for p in (owner, pawn):
        assert p.teleport(unreal.Vector(STAND[0], STAND[1], g.z + 100), unreal.Rotator(0, 0, FACING))
        p.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
    r, s = math.radians(FACING), math.radians(FACING + 90)
    tx, ty = STAND[0] + ahead * math.cos(r) + side * math.cos(s), STAND[1] + ahead * math.sin(r) + side * math.sin(s)
    m['aim_at'] = ground(tx, ty)
    m['t'] = time.monotonic()


def keep_aim():
    eye = pawn.get_actor_eyes_view_point()[0]
    client.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, m['aim_at']))
    return time.monotonic() - m['t'] > .8


def craft_in_menu(name):
    def begin():
        client.set_inventory_open(True)
        menu().focus_crafting()
        m['t'] = time.monotonic()

    def ready():
        if menu().get_shown_recipe() != recipe[name]:
            lib.send_verification_ui_key(client, 'Right')
            return False
        if not menu().is_craft_action_enabled():
            return False
        m['craft_at'] = time.monotonic()
        assert lib.send_verification_ui_key(client, 'Enter')
        return True
    return begin, ready


# ---- steps ----------------------------------------------------------------------------------------------------------

def knows_and_refuses():
    names = {r.get_name() for r in pawn.get_inventory_component().get_available_recipes()}
    assert {'DA_RecipeCampfire', 'DA_RecipeCookedBerryDish'} <= names, names
    assert not fires(server_world), 'a fire already burns'
    inv = owner.get_inventory_component()
    assert inv.add_item(item['Wood'], 6) == 6 and inv.add_item(item['Stone'], 3) == 3 and inv.add_item(item['Berry'], 3) == 3
    assert inv.get_craft_readiness(recipe['CookedBerryDish']) == unreal.EWCraftResult.NEEDS_FIRE
    return True


def no_fire_in_menu():
    if menu().get_shown_recipe() != recipe['CookedBerryDish']:
        lib.send_verification_ui_key(client, 'Right')
        return False
    if pawn.get_inventory_component().get_item_count(item['Berry']) != 3:
        return False                                    # the berries are still on their way to the client
    assert not menu().is_craft_action_enabled(), 'the dish can be cooked with no fire'
    client.set_inventory_open(False)
    return True


campfire_begin, campfire_ready = craft_in_menu('Campfire')


def campfire_made():
    if not both('Campfire', 1):
        return False
    m['campfire_seconds'] = round(time.monotonic() - m['craft_at'], 1)
    assert m['campfire_seconds'] >= 4.5 and both('Wood', 1) and both('Stone', 0)
    client.set_inventory_open(False)
    return True


def hold_campfire():
    assert lib.send_verification_equipment_request(client, item['Campfire'], HAND)
    stand_and_aim()


def ghost_blue():
    if not keep_aim() or pawn.get_equipment_component().get_equipped_item(HAND) != item['Campfire']:
        return False
    preview = client.get_placement_preview()
    if not preview.is_showing():
        return False
    assert preview.is_placeable(), 'ghost red on open grass'
    lib.send_verification_gameplay_key(client, 'LeftMouseButton')
    return True


def laid():
    lit = [f for f in fires(server_world) if f.is_lit()]
    seen = [f for f in fires(client_world) if f.is_lit()]
    if not lit or not seen:
        return False
    fire = lit[0]
    d = (fire.get_actor_location() - m['aim_at']).length()
    assert d < 60, f'laid {d:.0f} cm from where the ghost showed'
    assert owner.get_equipment_component().get_equipped_item(HAND) is None and count(owner, 'Campfire') == 0
    m['fire_at'] = [round(v) for v in (fire.get_actor_location().x, fire.get_actor_location().y, fire.get_actor_location().z)]
    m['fuel_after_laying'] = round(fire.get_fuel_left())
    return True


def second_held():
    assert owner.get_inventory_component().add_item(item['Campfire'], 1) == 1
    assert lib.send_verification_equipment_request(client, item['Campfire'], HAND)
    stand_and_aim(ahead=330.0, side=60.0)


def ghost_red():
    if not keep_aim() or pawn.get_equipment_component().get_equipped_item(HAND) != item['Campfire']:
        return False
    preview = client.get_placement_preview()
    if not preview.is_showing():
        return False
    assert not preview.is_placeable(), 'ghost blue beside a fire'
    lib.send_verification_gameplay_key(client, 'LeftMouseButton')
    m['t'] = time.monotonic()
    return True


def nothing_laid():
    if time.monotonic() - m['t'] < 1.5:
        return False
    assert len(fires(server_world)) == 1, 'a second fire was laid beside the first'
    assert owner.get_equipment_component().get_equipped_item(HAND) == item['Campfire'], 'the refused campfire left the hand'
    assert lib.send_verification_equipment_request(client, item['Campfire'], HAND, True)
    return True


dish_begin, dish_ready = craft_in_menu('CookedBerryDish')


def dish_made():
    if not both('Dish', 1):
        return False
    m['dish_seconds'] = round(time.monotonic() - m['craft_at'], 1)
    assert m['dish_seconds'] >= 5.5 and both('Berry', 0)
    client.set_inventory_open(False)
    return True


def eaten():
    stats = owner.get_survival_component()
    stats.set_hunger(50.0)
    stats.apply_damage(10.0)
    h0 = stats.get_health()
    assert owner.get_inventory_component().consume_food(item['Dish']) == unreal.EWFoodUseResult.SUCCESS
    m['dish_gives'] = [round(stats.get_hunger() - 50.0, 1), round(stats.get_health() - h0, 1)]
    assert m['dish_gives'] == [15.0, 2.0], m['dish_gives']
    stats.restore_health(100)
    return True


def to_fire():
    fire = fires(server_world)[0]
    m['fire'] = fire
    m['fuel_before'] = fire.get_fuel_left()
    at = fire.get_actor_location()
    r = math.radians(FACING + 180)
    for p in (owner, pawn):
        assert p.teleport(unreal.Vector(at.x + 150 * math.cos(r), at.y + 150 * math.sin(r), at.z + 100), unreal.Rotator(0, 0, FACING))
    m['aim_at'] = at + unreal.Vector(0, 0, 8)
    m['t'] = time.monotonic()


def feed_prompt():
    if not keep_aim():
        return False
    target = lib.get_verification_interaction_target(pawn)
    shown = str(client.get_interaction_widget().get_displayed_prompt())
    if not target or not shown:
        return False
    assert 'Add wood to the fire' in shown, shown
    m['feed_prompt'] = shown
    lib.send_verification_gameplay_key(client, 'E')
    return True


def fed():
    if not both('Wood', 0):
        return False
    m['fuel_gain'] = round(m['fire'].get_fuel_left() - m['fuel_before'])
    assert 170 <= m['fuel_gain'] <= 181, m['fuel_gain']
    return True


def burn_out():
    m['fire'].set_fuel(0.0)
    m['t'] = time.monotonic()


def cold_prompt():
    keep_aim()
    if any(f.is_lit() for f in fires(client_world)):
        return False
    shown = str(client.get_interaction_widget().get_displayed_prompt())
    if 'Take up the cold campfire' not in shown:
        return False
    assert shown.startswith('Hold'), shown
    m['cold_prompt'] = shown
    m['campfires_before'] = count(owner, 'Campfire')            # the refused second campfire is already in the pack
    lib.send_verification_gameplay_key_state(client, 'E', True)
    m['held_at'] = time.monotonic()
    return True


def taken_up():
    if time.monotonic() - m['held_at'] > 2.2:
        lib.send_verification_gameplay_key_state(client, 'E', False)
    if fires(server_world) or fires(client_world) or not both('Campfire', m['campfires_before'] + 1):
        return False
    lib.send_verification_gameplay_key_state(client, 'E', False)
    return True


def lay_again():
    assert lib.send_verification_equipment_request(client, item['Campfire'], HAND)
    stand_and_aim()


def laid_again():
    if not keep_aim():
        return False
    if not fires(server_world):
        if client.get_placement_preview().is_placeable() and time.monotonic() - m.get('clicked', 0) > 1.2:
            m['clicked'] = time.monotonic()
            lib.send_verification_gameplay_key(client, 'LeftMouseButton')
        return False
    return fires(server_world)[0].is_lit()


def saved_and_restored():
    fire = fires(server_world)[0]
    fuel, where = fire.get_fuel_left(), fire.get_actor_location()
    assert unreal.EWSurvivorSave.save_survivor(owner, SLOT, True), 'save failed'
    fire.destroy_actor()
    assert unreal.EWSurvivorSave.load_save(SLOT).apply_to(owner), 'restore failed'
    back = fires(server_world)
    assert len(back) == 1 and back[0].is_lit(), f'{len(back)} fires after the restore'
    assert abs(back[0].get_fuel_left() - fuel) < 5, (back[0].get_fuel_left(), fuel)
    assert (back[0].get_actor_location() - where).length() < 5, 'the fire came back elsewhere'
    unreal.GameplayStatics.delete_game_in_slot(SLOT, 0)
    m['restored_fuel'] = round(back[0].get_fuel_left())
    return True


STEPS = [
    ('The survivor knows the Campfire and Cooked Berry Dish; with nothing lit near, the dish cannot be cooked', lambda: None, knows_and_refuses, 10),
    ('In the menu the dish is greyed while no fire burns near', lambda: (client.set_inventory_open(True), menu().focus_crafting()), no_fire_in_menu, 8),
    ('Enter in the menu starts a Campfire', campfire_begin, campfire_ready, 8),
    ('... made from 5 wood and 3 stones in 5 s, on both machines', lambda: None, campfire_made, 10),
    ('Held, its ghost shows blue on open ground; Left Mouse lays it', hold_campfire, ghost_blue, 8),
    ('A lit fire stands where the ghost was, on both machines; the hand is empty', lambda: None, laid, 6),
    ('A second campfire held right beside it shows red', second_held, ghost_red, 8),
    ('... and Left Mouse lays nothing', lambda: None, nothing_laid, 5),
    ('By the fire, Enter in the menu cooks the berries', dish_begin, dish_ready, 8),
    ('... into a Cooked Berry Dish in its 6 s, on both machines', lambda: None, dish_made, 12),
    ('Eaten, the dish gives 15 hunger and 2 health', lambda: None, eaten, 5),
    ('At the fire with wood in the pack the prompt reads "Add wood to the fire"; E adds it', to_fire, feed_prompt, 6),
    ('... and the fire burns 3 minutes longer', lambda: None, fed, 6),
    ('Burnt down it goes dark on both machines; the prompt offers to take up the cold ring (hold)', burn_out, cold_prompt, 6),
    ('Held E takes it up: the Campfire is back in the pack, the ring gone on both machines', lambda: None, taken_up, 6),
    ('Laid again, it burns', lay_again, laid_again, 10),
    ('Saved and restored, the burning fire comes back where it was, with the burn time it had', lambda: None, saved_and_restored, 5),
]


def finish(error=None):
    lib.send_verification_gameplay_key_state(client, 'E', False)
    unreal.unregister_slate_post_tick_callback(state['handle'])
    client.set_inventory_open(False)
    out = {k: v for k, v in m.items() if k not in ('t', 'craft_at', 'held_at', 'clicked', 'fire', 'aim_at')}
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': out}, indent=2, default=str), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK Campfire success={error is None} error={error}')


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
            raise TimeoutError(f'not done within {timeout} s; prompt {str(client.get_interaction_widget().get_displayed_prompt())!r}, '
                               f'fires {len(fires(server_world))}')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
