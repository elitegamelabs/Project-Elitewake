"""Client acceptance for the first resources and the first tool (CLAUDE.md Phase 1, slice 2; arrival_layout.FIRST_RESOURCES and
Scripts/Setup/build_first_resources.py).

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, WITHOUT the test starter kit:
run with run_play_check.py and EW_PLAY_STARTER_KIT=0 (EW_PLAY_PLAYERS=2). The client acts through its own keys, mouse,
controller buttons and menu only; the server is touched only to fill the pack for the full-pack check and to save.

  1. A new survivor arrives empty-handed, knowing only the first recipes (Stone Hatchet, Pickaxe, Campfire, Cooked Berry Dish).
  2. The first resources lie where they were authored, the same on both machines.
  3-6. Sticks (E), fibre (controller X), stones (E) and berries (E) are taken by hand: the prompt names each, the whole pile
     arrives in the pack on both machines and the pile is gone.
  7. In the menu the Stone Hatchet is ready to make; Enter makes it in its 5 s: 3 sticks, 2 stones and 4 fibre go, one
     Stone Hatchet arrives, with its flint head.
  8. Equipped, Left Mouse on an arrival oak gives Wood on both machines.
  9. With the pack full, loose stones say there is no room, and E takes nothing.
 10. Saved and restored, the survivor keeps the hatchet in hand and what they gathered.
Writes Saved/FirstResourcesPlayResult.json.
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
RESULT = Path(unreal.Paths.project_saved_dir(), 'FirstResourcesPlayResult.json')
SLOT = 'EW_FirstResourcesPlayCheck'
ITEMS = '/Game/Elitewake/Items/Testing'
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]
pawn = client.get_controlled_pawn()
HAND = unreal.EWEquipmentSlot.MAIN_HAND
item = {n: unreal.load_asset(f'{ITEMS}/DA_Test{n}') for n in ('Sticks', 'Fiber', 'Stone', 'AzulBerry', 'WoodenAxe', 'Wood')}
recipe = unreal.load_asset('/Game/Elitewake/Crafting/Testing/DA_RecipeStoneHatchet')
assert all(item.values()) and recipe


def player_id(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if player_id(p) == player_id(pawn))
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}}
checks = []
m = state['memo']


def count(who, name):
    return who.get_inventory_component().get_item_count(item[name])


def both(name, n):
    return count(owner, name) == n and count(pawn, name) == n


def node(world, label):
    found = [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWHandGatherable) if str(a.get_actor_label()) == label]
    return found[0] if found else None


def menu():
    return next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(client_world, unreal.EWInventoryWidget, False)
                if w.get_owning_player() == client and w.is_in_viewport())


def approach(target, distance=150.0):
    """Stand `distance` from the target on the spawn's side, facing its middle, and settle."""
    origin, extent = target.get_actor_bounds(False)
    away = unreal.Vector(A.SPAWN[0] - origin.x, A.SPAWN[1] - origin.y, 0)
    away = away * (1.0 / max(away.length(), 1.0))
    spot = unreal.Vector(origin.x, origin.y, target.get_actor_location().z) + away * distance + unreal.Vector(0, 0, 100)
    for p in (owner, pawn):
        assert p.teleport(spot, unreal.Rotator(0, 0, 0)), f'no room beside {target.get_actor_label()}'
        p.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
    m.update(target=origin + unreal.Vector(0, 0, extent.z * .5), t=time.monotonic())   # the pile's upper half: low piles sit in the slope


def aimed_at(label):
    """Keeps the client's view on the target's middle; true once the interaction trace lands on it."""
    def done():
        if time.monotonic() - m['t'] < .6:
            return False
        eye = pawn.get_actor_eyes_view_point()[0]
        client.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, m['target']))
        target = lib.get_verification_interaction_target(pawn)
        return target is not None and str(target.get_actor_label()) == label
    return done


# ---- steps ----------------------------------------------------------------------------------------------------------

def empty_handed():
    for who in (owner, pawn):
        pack = who.get_inventory_component()
        assert pack.get_used_slot_count() == 0, f'{who.get_name()} starts with {pack.get_used_slot_count()} slots filled'
        assert who.get_equipment_component().get_equipped_item(HAND) is None
        names = sorted(r.get_name() for r in pack.get_available_recipes())
        assert names == ['DA_RecipeCampfire', 'DA_RecipeCookedBerryDish', 'DA_RecipeStoneHatchet', 'DA_RecipeWoodenPickaxe'], names
    return True


def authored():
    for label, kind, item_name, x, y, quantity in A.FIRST_RESOURCES:
        for world in (server_world, client_world):
            n = node(world, label)
            assert n, f'{label} missing'
            p = n.get_actor_location()
            assert math.hypot(p.x - x, p.y - y) < 50, f'{label} moved'
            assert n.get_editor_property('gathering_kind') == getattr(unreal.EWHandGatheringKind, kind), label
            assert n.get_editor_property('item_definition').get_name() == item_name, label
            assert n.get_editor_property('quantity') == quantity, label
    return True


def gather_steps(label, name, words, key):
    quantity = next(q for l, *_, q in A.FIRST_RESOURCES if l == label)

    def begin():
        m['had'] = count(owner, name)
        approach(node(server_world, label))

    def prompted():
        if not aimed_at(label)():
            return False
        shown = str(client.get_interaction_widget().get_displayed_prompt())
        if not shown:
            return False                    # the prompt is drawn on the widget's next frame
        assert words in shown, f'prompt {shown!r}, wanted {words!r}'
        m.setdefault('prompts', {})[label] = shown
        return True

    def take():
        assert lib.send_verification_gameplay_key(client, key) is not None

    def taken():
        if not both(name, m['had'] + quantity):
            return False
        return node(server_world, label) is None and node(client_world, label) is None

    return [(f'{label}: the prompt reads "{words}"', begin, prompted, 6),
            (f'{label}: {key} takes all {quantity} {name} into the pack on server and client; the pile is gone', take, taken, 6)]


def open_menu():
    client.set_inventory_open(True)
    menu().focus_crafting()


def hatchet_ready():
    shown = menu().get_shown_recipe()
    if shown != recipe:
        lib.send_verification_ui_key(client, 'Right')
        return False
    return menu().is_craft_action_enabled()


def craft():
    m['craft_at'] = time.monotonic()
    m['before'] = {n: count(owner, n) for n in ('Sticks', 'Stone', 'Fiber')}
    assert lib.send_verification_ui_key(client, 'Enter')


def crafted():
    if count(owner, 'WoodenAxe') == 0:
        return False
    m['craft_seconds'] = round(time.monotonic() - m['craft_at'], 1)
    assert m['craft_seconds'] >= 4.5, f'made in {m["craft_seconds"]} s'
    for name, cost in (('Sticks', 3), ('Stone', 2), ('Fiber', 4)):
        assert both(name, m['before'][name] - cost), f'{name}: {count(owner, name)} / {count(pawn, name)}'
    assert both('WoodenAxe', 1)
    hatchet = item['WoodenAxe']
    assert str(hatchet.get_editor_property('display_name')) == 'Stone Hatchet'
    held = hatchet.get_editor_property('held_mesh')
    assert held and 'M_Flint_v1' in [str(held.get_material(i).get_name()) for i in range(2) if held.get_material(i)], 'no flint head'
    client.set_inventory_open(False)
    return True


def equip():
    assert lib.send_verification_equipment_request(client, item['WoodenAxe'], HAND)


def equipped():
    return owner.get_equipment_component().get_equipped_item(HAND) == item['WoodenAxe'] and \
        pawn.get_equipment_component().get_equipped_item(HAND) == item['WoodenAxe']


def to_oak():
    oak = min((t for t in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWHarvestTree)
               if str(t.get_actor_label()).startswith('Arrival oak')),
              key=lambda t: (t.get_actor_location() - owner.get_actor_location()).length())
    base = oak.get_actor_location()
    away = unreal.Vector(A.SPAWN[0] - base.x, A.SPAWN[1] - base.y, 0)
    away = away * (1.0 / max(away.length(), 1.0))
    spot = base + away * 140 + unreal.Vector(0, 0, 110)
    look = unreal.MathLibrary.find_look_at_rotation(spot + unreal.Vector(0, 0, 60), base + unreal.Vector(0, 0, 120))
    for p in (owner, pawn):
        assert p.teleport(spot, unreal.Rotator(0, 0, look.yaw))
        p.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
    client.set_control_rotation(look)
    m.update(oak=str(oak.get_actor_label()), wood=count(owner, 'Wood'), t=time.monotonic())


def chopped():
    if time.monotonic() - m['t'] < .8:
        return False
    if count(owner, 'Wood') > m['wood'] and count(pawn, 'Wood') == count(owner, 'Wood'):
        m['wood_from_one_swing'] = count(owner, 'Wood') - m['wood']
        return True
    if time.monotonic() - m.get('swung', 0) > 1.3:
        m['swung'] = time.monotonic()
        lib.send_verification_gameplay_key(client, 'LeftMouseButton')
    return False


def fill_pack():
    pack = owner.get_inventory_component()
    m['filler'] = pack.add_item(item['Stone'], 100000)
    assert pack.get_room_for(item['Stone'], 1) == 0
    approach(node(server_world, 'Arrival stones 2'))


def full_prompt():
    if not aimed_at('Arrival stones 2')():
        return False
    shown = str(client.get_interaction_widget().get_displayed_prompt())
    if 'No room in your pack' not in shown:
        return False
    m['full_prompt'] = shown
    m['stones_before'] = count(owner, 'Stone')
    lib.send_verification_gameplay_key(client, 'E')
    m['t'] = time.monotonic()
    return True


def nothing_taken():
    if time.monotonic() - m['t'] < 1.5:
        return False
    assert count(owner, 'Stone') == m['stones_before'], 'a full pack took stones'
    assert node(server_world, 'Arrival stones 2').get_editor_property('quantity') == 4
    assert owner.get_inventory_component().remove_item(item['Stone'], m['filler'])
    return True


def saved_and_restored():
    pack = owner.get_inventory_component()
    held = {n: count(owner, n) for n in ('Sticks', 'Stone', 'Fiber', 'AzulBerry', 'Wood')}
    assert unreal.EWSurvivorSave.save_survivor(owner, SLOT, False), 'save failed'
    pack.remove_item(item['Sticks'], 1)
    assert unreal.EWSurvivorSave.load_save(SLOT).apply_to(owner), 'restore failed'
    for n, c in held.items():
        assert count(owner, n) == c, f'{n} {count(owner, n)} after restore, saved {c}'
    assert owner.get_equipment_component().get_equipped_item(HAND) == item['WoodenAxe']
    unreal.GameplayStatics.delete_game_in_slot(SLOT, 0)
    m['restored'] = held
    return True


STEPS = [
    ('A new survivor arrives empty-handed, knowing only the first four recipes, on server and client', lambda: None, empty_handed, 10),
    ('The first resources lie where they were authored, the same on both machines', lambda: None, authored, 5),
    *gather_steps('Arrival sticks 1', 'Sticks', 'Collect Sticks', 'E'),
    *gather_steps('Arrival fiber 1', 'Fiber', 'Gather Fiber', 'Gamepad_FaceButton_Left'),
    *gather_steps('Arrival stones 1', 'Stone', 'Collect Stone', 'E'),
    *gather_steps('Arrival berries 1', 'AzulBerry', 'Gather', 'E'),
    ('In the menu the Stone Hatchet is ready to make', open_menu, hatchet_ready, 8),
    ('Enter makes it in its 5 s: 3 sticks, 2 stones and 4 fibre go, one Stone Hatchet (flint head) arrives on both', craft, crafted, 12),
    ('Equipped, the Stone Hatchet is in hand on both', equip, equipped, 5),
    ('Left Mouse on an arrival oak gives Wood on both', to_oak, chopped, 10),
    ('With the pack full, loose stones say there is no room', fill_pack, full_prompt, 8),
    ('... and E takes nothing', lambda: None, nothing_taken, 5),
    ('Saved and restored, the survivor keeps the hatchet in hand and what they gathered', lambda: None, saved_and_restored, 5),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    client.set_inventory_open(False)
    out = {k: v for k, v in m.items() if k not in ('target', 't', 'craft_at', 'swung')}
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': out}, indent=2, default=str), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK FirstResources success={error is None} error={error}')


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
            raise TimeoutError(f'not done within {timeout} s; prompt {str(client.get_interaction_widget().get_displayed_prompt())!r}')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
