"""Client acceptance for the core survival tools on the simplified island (owner, October 14).

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, after
Scripts/Setup/simplify_island.py and build_core_tools.py. Run unattended with run_play_check.py. The title's way
onto this map is verify_title_to_coast_play.

Through ordinary owned requests and keys, the client:
  1. spawns on the island carrying exactly the Hatchet, Pickaxe, Waterskin and Torch; no boats;
  2. equips the Hatchet (drawing it) and chops a palm with Left Mouse: Wood and Thatch arrive;
  3. equips the Pickaxe and mines a boulder with Left Mouse: Stone arrives;
  4. equips the Waterskin, presses E at the spring: the skin fills (a filling motion), thirst untouched;
  5. thirsty, drinks the full skin with Left Mouse: thirst quenched, the skin empty again;
  6. equips the Torch: it is dark until Left Mouse lights it (light and flame on both machines), and Left Mouse
     puts it out again.
Each step checks the server and the client's copy; animations are checked on the client's screen.
Writes Saved/CoreToolsPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'CoreToolsPlayResult.json')
T = '/Game/Elitewake/Items/Testing'
hatchet, pickaxe, skin, full_skin, torch, wood, thatch, stone = (unreal.load_asset(f'{T}/DA_Test{n}') for n in
    ('WoodenAxe', 'WoodenPickaxe', 'HideWaterFlask', 'WaterskinFull', 'InnTorch', 'Wood', 'Thatch', 'Stone'))
assert full_skin, 'Run Scripts/Setup/build_core_tools.py first.'
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
palms = [t for t in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWHarvestTree) if t.get_actor_label().startswith('Veyran Palm')]
rocks = list(unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWMineable))
spring = next(iter(unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWWaterSource)))
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}, 'aim': None}


def count(who, item):
    return who.get_inventory_component().get_item_count(item)


def held(who):
    return who.get_equipment_component().get_equipped_item(unreal.EWEquipmentSlot.MAIN_HAND)


def last_anim():
    a = pawn.get_last_tool_animation()
    return a.get_name() if a else None


def keep_aim():
    if not state['aim']:
        return
    for controller, who in ((client, pawn), (owner.get_controller(), owner)):
        eye = who.get_actor_location() + unreal.Vector(0, 0, who.get_editor_property('base_eye_height'))
        controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, state['aim']()))


def approach(target, distance, aim_height):
    """Stand `distance` from the target on the side toward the beach spawn, facing it, and settle."""
    base = target.get_actor_location()
    away = unreal.Vector(150 - base.x, -base.y, 0)
    away = away * (1.0 / max(away.length(), 1.0))
    spot = base + away * distance + unreal.Vector(0, 0, 110)
    for p in (owner, pawn):
        assert p.teleport(spot, unreal.Rotator()), f'no room beside {target.get_actor_label()}'
        p.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
    state['aim'] = lambda: base + unreal.Vector(0, 0, aim_height)
    keep_aim()
    state['memo'].update(t=time.monotonic(), pressed=False)


def equip(item):
    def begin():
        state['aim'] = None
        assert lib.send_verification_equipment_request(client, item, unreal.EWEquipmentSlot.MAIN_HAND)
    def done():
        if not (held(owner) == item and held(pawn) == item):
            return False
        mesh = pawn.get_held_mesh()
        assert mesh, f'nothing drawn in the client\'s hand for {item.get_name()}'
        return last_anim() == 'AS_Equip_v1'
    return begin, done


def press_after_settle(key='LeftMouseButton', interact=None):
    m = state['memo']
    if m['pressed']:
        return True
    if time.monotonic() - m['t'] < .8:
        return False
    if interact:
        assert lib.send_verification_interaction_request(client, interact)
    else:
        assert lib.send_verification_gameplay_key(client, key)
    m['pressed'] = True
    return True


# 1. Spawn ----------------------------------------------------------------------------------------------------

def spawned():
    assert not unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWShip), 'boats remain on the island'
    want = {hatchet: 1, pickaxe: 1, skin: 1, torch: 1}
    have = {e.get_editor_property('item_definition'): e.get_editor_property('quantity') for e in owner.get_inventory_component().get_inventory_entries()}
    seen = {e.get_editor_property('item_definition'): e.get_editor_property('quantity') for e in pawn.get_inventory_component().get_inventory_entries()}
    if have != want or seen != want:
        return False
    names = sorted(str(i.get_editor_property('display_name')) for i in want)
    state['memo']['supplies'] = names
    assert names == ['Hatchet', 'Pickaxe', 'Torch', 'Waterskin'], names
    return True


# 2-3. Gather --------------------------------------------------------------------------------------------------

def to_palm():
    tree = min(palms, key=lambda t: (t.get_actor_location() - unreal.Vector(150, 0, 0)).length())
    state['memo']['wood_from'] = (count(owner, wood), count(owner, thatch))
    approach(tree, 110, 120)


def chopped():
    if not press_after_settle():
        return False
    w0, t0 = state['memo']['wood_from']
    got = (count(owner, wood) - w0, count(owner, thatch) - t0)
    if got[0] <= 0 or got != (count(pawn, wood) - w0, count(pawn, thatch) - t0):
        return False
    state['memo']['chopped'] = got
    return True


def to_rock():
    rock = min(rocks, key=lambda t: (t.get_actor_location() - unreal.Vector(150, 0, 0)).length())
    _, extent = rock.get_actor_bounds(False)
    state['memo']['stone_from'] = count(owner, stone)
    approach(rock, max(extent.x, extent.y) + 55, 20)


def mined():
    m = state['memo']
    if not press_after_settle():
        return False
    # Strike again if the first swing found nothing, at the swing's own pace.
    if count(owner, stone) == m['stone_from'] and time.monotonic() - m['t'] > 2.0 and m.get('retries', 0) < 3:
        m['retries'] = m.get('retries', 0) + 1
        m['t'] = time.monotonic() - .8
        assert lib.send_verification_gameplay_key(client, 'LeftMouseButton')
        eye = owner.get_actor_location() + unreal.Vector(0, 0, owner.get_editor_property('base_eye_height'))
        hit = unreal.SystemLibrary.line_trace_single(server_world, eye, eye + owner.get_control_rotation().get_forward_vector() * 250,
                                                     unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [owner], unreal.DrawDebugTrace.NONE, True)
        m['aimed_at'] = str(hit.to_tuple()[9].get_actor_label()) if hit else None
    got = count(owner, stone) - state['memo']['stone_from']
    if got <= 0 or count(pawn, stone) - state['memo']['stone_from'] != got:
        return False
    state['memo']['mined'] = got
    return True


# 4-5. Water ---------------------------------------------------------------------------------------------------

def to_spring():
    state['memo']['hydration_before_fill'] = owner.get_survival_component().get_hydration()
    approach(spring, 120, 0)


def filled():
    if not press_after_settle(interact=next(iter(unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWWaterSource)))):
        return False
    if not (held(owner) == full_skin and held(pawn) == full_skin):
        return False
    assert owner.get_survival_component().get_hydration() == state['memo']['hydration_before_fill'], 'filling the skin drank instead'
    return last_anim() == 'AS_FillWaterskin_v1'


def thirsty():
    state['aim'] = None
    owner.get_survival_component().set_hydration(40)
    state['memo'].update(t=time.monotonic(), pressed=False)


def drank():
    if not press_after_settle():
        return False
    if not (held(owner) == skin and held(pawn) == skin):
        return False
    hydration = (owner.get_survival_component().get_hydration(), pawn.get_survival_component().get_hydration())
    if hydration != (100.0, 100.0):
        return False
    return last_anim() == 'AS_Drink_v1'


# 6. Torch -----------------------------------------------------------------------------------------------------

def light_shown(who):
    lamp = who.get_component_by_class(unreal.PointLightComponent)
    flame = next((c for c in who.get_components_by_class(unreal.StaticMeshComponent) if c.get_name() == 'HeldFlame'), None)
    return bool(lamp and lamp.is_visible()), bool(flame and flame.is_visible() and flame.get_editor_property('static_mesh'))


def dark_torch():
    assert not owner.is_held_item_lit() and light_shown(pawn) == (False, False), 'the torch burns before it is lit'
    state['memo'].update(t=time.monotonic(), pressed=False)
    return True


def lit():
    if not press_after_settle():
        return False
    if not (owner.is_held_item_lit() and pawn.is_held_item_lit()):
        return False
    shown = light_shown(pawn)
    assert shown == (True, True), f"the client shows light and flame {shown}"
    if last_anim() != 'AS_Ignite_v1':
        return False
    lamp = pawn.get_component_by_class(unreal.PointLightComponent)
    state['memo']['torch_candelas'] = round(lamp.get_editor_property('intensity'), 1)
    state['memo'].update(t=time.monotonic(), pressed=False)
    return True


def put_out():
    if not press_after_settle():
        return False
    return not owner.is_held_item_lit() and not pawn.is_held_item_lit() and light_shown(pawn) == (False, False)


EQUIP_HATCHET, EQUIP_PICKAXE, EQUIP_SKIN, EQUIP_TORCH = equip(hatchet), equip(pickaxe), equip(skin), equip(torch)
STEPS = [
    ('The client spawns on the island carrying the Hatchet, Pickaxe, Waterskin and Torch; no boats', lambda: None, spawned, 8),
    ('It equips the Hatchet: drawn into the hand with the draw motion', *EQUIP_HATCHET, 5),
    ('Left Mouse chops a palm: Wood and Thatch arrive, on server and client', to_palm, chopped, 6),
    ('It equips the Pickaxe', *EQUIP_PICKAXE, 5),
    ('Left Mouse mines a boulder: Stone arrives, on server and client', to_rock, mined, 6),
    ('It equips the Waterskin', *EQUIP_SKIN, 5),
    ('E at the spring fills the skin, with the filling motion; thirst is untouched', to_spring, filled, 6),
    ('Thirsty, Left Mouse drinks the full skin: thirst quenched, the skin empty again', thirsty, drank, 6),
    ('It equips the Torch, dark until lit', *EQUIP_TORCH, 5),
    ('', lambda: None, dark_torch, 2),
    ('Left Mouse lights the Torch: light and flame on both machines, with the lighting motion', lambda: None, lit, 6),
    ('Left Mouse puts the Torch out', lambda: None, put_out, 4),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    settings.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
    keep = ('supplies', 'chopped', 'mined', 'retries', 'aimed_at', 'torch_candelas')
    RESULT.write_text(json.dumps({'success': error is None, 'checks': [c for c in checks if c], 'error': error,
                                  'measured': {k: state['memo'][k] for k in keep if k in state['memo']}}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK CoreTools success={error is None} error={error}')


def tick(delta):
    keep_aim()
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
            raise TimeoutError(f'not done within {timeout} s; holding {held(owner)}, last animation {last_anim()}')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
