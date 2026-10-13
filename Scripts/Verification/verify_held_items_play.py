"""Client acceptance for tools shown in the hand and swung as tools.

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, with the tools from
Scripts/Setup/build_held_tools.py and the swings from Scripts/Setup/configure_attack_animations.py.
Run unattended with run_play_check.py.

Through ordinary hotbar requests, the client:
  1. puts its wooden axe on the hotbar and selects it: the axe is in the survivor's right hand on its own screen
     and on the host's,
  2. selects its wooden pickaxe instead: the hand now holds the pickaxe on both,
  3. swings with Left Mouse: a tool swing plays (not a punch) on both screens,
  4. takes the pickaxe off: the hand is empty on both.
Writes Saved/HeldItemsPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'HeldItemsPlayResult.json')
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
pawn = client.get_controlled_pawn()


def player_id(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if player_id(p) == player_id(pawn))
ITEMS = '/Game/Elitewake/Items/Testing'
axe, pickaxe = unreal.load_asset(f'{ITEMS}/DA_TestWoodenAxe'), unreal.load_asset(f'{ITEMS}/DA_TestWoodenPickaxe')
axe_mesh, pickaxe_mesh = (i.get_editor_property('held_mesh') for i in (axe, pickaxe))
assert axe_mesh and pickaxe_mesh, 'Run Scripts/Setup/build_held_tools.py first.'
SPOT = unreal.Vector(150, 0, 120)
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}}


def held(who):
    return who.get_held_mesh()


def holding(mesh):
    return lambda: held(pawn) == mesh and held(owner) == mesh


def setup():
    for p in (owner, pawn):
        assert p.teleport(SPOT, unreal.Rotator())
    inventory = owner.get_inventory_component()
    for item in (axe, pickaxe):
        if inventory.get_item_count(item) == 0:
            assert inventory.add_item(item, 1) == 1
    equipped = owner.get_equipment_component().get_equipped_item(unreal.EWEquipmentSlot.MAIN_HAND)
    if equipped:
        assert lib.send_verification_equipment_request(client, equipped, unreal.EWEquipmentSlot.MAIN_HAND, True)


def empty_hands():
    return held(pawn) is None and held(owner) is None


def select_axe():
    assert lib.send_verification_hotbar_request(client, 0, axe, False)
    assert lib.send_verification_hotbar_request(client, 1, pickaxe, False)
    state['memo']['t'] = time.monotonic()


def axe_bound():
    return time.monotonic() - state['memo']['t'] > .5


def activate(slot):
    return lambda: lib.send_verification_hotbar_request(client, slot, None, True)


def swing():
    state['memo']['t'] = time.monotonic()
    assert lib.send_verification_gameplay_key(client, 'LeftMouseButton')


def swinging_tool():
    swings = pawn.get_editor_property('tool_swing_animations')
    punches = pawn.get_editor_property('attack_animations')
    assert swings, 'no tool swings configured'
    def playing(who, anims):
        instance = who.get_editor_property('mesh').get_anim_instance()
        def on(a):
            result = instance.is_playing_slot_animation(a, 'DefaultSlot')
            return result[0] if isinstance(result, tuple) else bool(result)
        return any(on(a) for a in anims)
    if not (playing(pawn, swings) and playing(owner, swings)):
        return False
    assert not playing(pawn, punches), 'a punch played with a tool in hand'
    return True


def unequip():
    assert lib.send_verification_equipment_request(client, pickaxe, unreal.EWEquipmentSlot.MAIN_HAND, True)


STEPS = [
    ('', setup, empty_hands, 5),
    ('', select_axe, axe_bound, 3),
    ('Selecting the wooden axe on the hotbar puts it in the right hand, on the client and the host', activate(0), holding(axe_mesh), 5),
    ('Selecting the wooden pickaxe swaps it in, on both', activate(1), holding(pickaxe_mesh), 5),
    ('Left Mouse swings the pickaxe with a tool swing, not a punch, on both', swing, swinging_tool, 3),
    ('Taking it off empties the hand on both', unequip, empty_hands, 5),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    RESULT.write_text(json.dumps({'success': error is None, 'checks': [c for c in checks if c], 'error': error}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK HeldItems success={error is None} error={error}')


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
            raise TimeoutError(f'not done within {timeout} s; client holds {held(pawn)}, host sees {held(owner)}')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
