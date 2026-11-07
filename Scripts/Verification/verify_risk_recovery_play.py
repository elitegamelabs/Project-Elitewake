"""Client acceptance for risk and recovery on the Plains arrival (CLAUDE.md Phase 1, slice 4; Scripts/Setup/build_plains_threat.py,
UEWSurvivalComponent::UpdateRecovery, AEWCharacter::FindRespawnPoint).

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, without the test kit:
run_play_check.py with EW_PLAY_STARTER_KIT=0 (EW_PLAY_PLAYERS=2). Survivors are moved between the scenes by the server
(teleports stand in for walking there); every action in a scene is the client's own key, mouse or request.

  1. Two wild boars root in their Plains pocket off the track, on both machines.
  2. A survivor on the track at its nearest point is ignored: the boars stay calm and do no harm.
  3. Stepping within 4 m of one, it grunts, charges and gores: health falls on server and client and the client shows a red
     damage number. A sprinting survivor outruns it (its run is slower than a sprint) and away beyond 10 m it gives up.
  4. With the Stone Hatchet, Left Mouse kills it on both machines; E at the body gives 3-5 Raw Meat.
  5. Food sickness (raw meat's 25% chance, given here) shows on the client; the yarrow by the track reads "Gather
     Medicinal Herb" and E gathers all three; eating one ends the sickness on both machines.
  6. Fed and watered, a hurt survivor mends after a 10 s pause, about 0.11 health a second; beside a lit fire three times
     as fast.
  7. Killed carrying the meat and herbs, the survivor respawns on the Plains at least 60 m off and 30 m clear of any
     living boar, the meat and herbs in a bag where they fell; the bag survives a save and restore, and E at it takes
     everything back.
Writes Saved/RiskRecoveryPlayResult.json.
"""
import json
import math
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Setup'))
import arrival_layout as A  # noqa: E402
import world_layout as W  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'RiskRecoveryPlayResult.json')
SLOT = 'EW_RiskRecoveryPlayCheck'
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]
pawn = client.get_controlled_pawn()
HAND = unreal.EWEquipmentSlot.MAIN_HAND
item = {'Meat': unreal.load_asset('/Game/Elitewake/Items/Food/DA_RawMeat'),
        'Herb': unreal.load_asset('/Game/Elitewake/Items/Food/DA_MedicinalHerb'),
        'Hatchet': unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWoodenAxe')}
assert all(item.values())
MEND = 100.0 / (15 * 60)          # health a second, fed and watered (UEWSurvivalComponent::MendSeconds)


def player_id(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if player_id(p) == player_id(pawn))
stats = owner.get_survival_component()
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'swing_at': 0.0, 'follow': None}
m = {}
checks = []


def boars(world):
    return [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWAnimal)
            if str(a.get_editor_property('definition').get_editor_property('display_name')) == 'Wild Boar']


def copy_of(a):
    return next(c for c in boars(client_world) if c.get_name() == a.get_name())


def count(who, name):
    return who.get_inventory_component().get_item_count(item[name])


def death_widget():
    return next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(client_world, unreal.EWDeathWidget, False) if w.get_owning_player() == client)


def ground(x, y, z=3000, ignore=()):
    hit = unreal.SystemLibrary.line_trace_single(server_world, unreal.Vector(x, y, z), unreal.Vector(x, y, -3000),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [owner, *ignore], unreal.DrawDebugTrace.NONE, True)
    return hit.to_tuple()[4].z if hit else 0.0


def place(x, y, look_at):
    spot = unreal.Vector(x, y, ground(x, y) + 100)
    for p in (owner, pawn):
        p.set_actor_location(spot, False, True)
        p.get_component_by_class(unreal.CharacterMovementComponent).stop_movement_immediately()
    aim(look_at)


def aim(at):
    for controller, who in ((client, pawn), (owner.get_controller(), owner)):
        eye = who.get_actor_eyes_view_point()[0]
        controller.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, at))


def follow():
    target, distance = state['follow'] or (None, 0)
    if target and not target.is_dead():
        at = target.get_actor_location()
        side = target.get_actor_right_vector()
        place(at.x + side.x * distance, at.y + side.y * distance, at)


def swing():
    if time.monotonic() >= state['swing_at']:
        state['swing_at'] = time.monotonic() + 1.0
        assert lib.send_verification_gameplay_key(client, 'LeftMouseButton')


def notices(who):
    return {str(n.get_editor_property('id')) for n in who.get_survival_component().get_debuff_notices()}


# ---- 1-3: the boars ---------------------------------------------------------------------------------------------------

def present():
    found, seen = boars(server_world), boars(client_world)
    assert len(found) == 2, f'{len(found)} boars on the server'
    if len(seen) != 2:
        return False
    for b in found:
        at = b.get_actor_location()
        assert W.region_of(at.x, at.y) == 'Plains', (at.x, at.y)
        assert A.distance_to_route(at.x, at.y) > 3000, f'a boar {A.distance_to_route(at.x, at.y) / 100:.0f} m from the track'
    run = found[0].get_editor_property('definition').get_editor_property('run_speed')
    sprint = owner.get_editor_property('sprint_speed')
    assert run < sprint, f'a boar runs {run} cm/s, a sprint is {sprint}'
    m['boar_run_vs_sprint'] = [run, sprint]
    return True


def to_track():
    b = boars(server_world)[0]
    at = b.get_actor_location()
    nearest = min(A.smoothed_route(), key=lambda p: math.hypot(p[0] - at.x, p[1] - at.y))
    place(nearest[0], nearest[1], at)
    m.update(t=time.monotonic(), health0=stats.get_health(), track_m=round(math.hypot(nearest[0] - at.x, nearest[1] - at.y) / 100))


def ignored_on_track():
    assert all(b.get_quarry() is None for b in boars(server_world)), 'a boar went for a survivor on the track'
    assert stats.get_health() == m['health0']
    return time.monotonic() - m['t'] > 6.0


def near_boar():
    b = boars(server_world)[0]
    m.update(boar=b, health0=stats.get_health(), flashes=death_widget().get_damage_flash_count(), cues=copy_of(b).get_cues_heard())
    at = b.get_actor_location()
    side = b.get_actor_right_vector()
    place(at.x + side.x * 400, at.y + side.y * 400, at)


def gored():
    b = m['boar']
    if b.get_quarry() != owner or stats.get_health() >= m['health0'] or pawn.get_survival_component().get_health() >= m['health0']:
        return False
    if death_widget().get_damage_flash_count() <= m['flashes'] or copy_of(b).get_cues_heard() <= m['cues']:
        return False
    m['gore'] = round(m['health0'] - stats.get_health(), 1)
    m['client_cues'] = copy_of(b).get_cues_heard() - m['cues']
    return True


def run_off():
    b = m['boar']
    at, home = b.get_actor_location(), b.get_home()
    away = unreal.Vector(at.x - home.x, at.y - home.y, 0)
    away = away * (1.0 / away.length()) if away.length() > 1 else unreal.Vector(0, -1, 0)
    place(at.x + away.x * 1500, at.y + away.y * 1500, at)


def gave_up():
    return m['boar'].get_quarry() is None


# ---- 4: the kill ------------------------------------------------------------------------------------------------------

def arm():
    stats.restore_health(100)
    assert owner.get_inventory_component().add_item(item['Hatchet'], 1) == 1
    assert lib.send_verification_equipment_request(client, item['Hatchet'], HAND)
    state['follow'] = (m['boar'], 110)
    m['t'] = time.monotonic()


def killed():
    if time.monotonic() - m['t'] > 1.0:
        swing()
    b = m['boar']
    if not (b.is_dead() and copy_of(b).is_dead()):
        return False
    state['follow'] = None
    m['health_after_fight'] = round(stats.get_health())
    at = b.get_actor_location()
    place(at.x - 140, at.y, at)
    m.update(meat0=count(owner, 'Meat'), pressed=0.0)
    return True


def harvested():
    b = m['boar']
    aim(b.get_actor_location())
    if not b.is_harvested():
        if time.monotonic() - m['pressed'] > 1.0:
            m['pressed'] = time.monotonic()
            lib.send_verification_gameplay_key(client, 'E')
        return False
    gained = count(owner, 'Meat') - m['meat0']
    if not copy_of(b).is_harvested() or count(pawn, 'Meat') != count(owner, 'Meat'):
        return False
    assert 3 <= gained <= 5, f'a boar gave {gained} Raw Meat'
    m['meat'] = gained
    return True


# ---- 5: sickness and the herb ------------------------------------------------------------------------------------------

def fall_sick():
    stats.contract_food_sickness(180.0)


def sick_shown():
    return stats.is_food_sick() and 'FoodSickness' in notices(pawn)


def to_herbs():
    _, x, y, _ = A.HERBS[1]
    nodes = [h for h in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWHandGatherable)
             if math.hypot(h.get_actor_location().x - x, h.get_actor_location().y - y) < 50]
    assert len(nodes) == 1, f'{len(nodes)} herb clumps at {A.HERBS[1][0]}'
    m['herb_at'] = nodes[0].get_actor_location() + unreal.Vector(0, 0, 45)
    place(x - 150, y, m['herb_at'])
    m.update(pressed=0.0)


def herb_prompt():
    aim(m['herb_at'])
    shown = str(client.get_interaction_widget().get_displayed_prompt())
    if not shown:
        return False
    assert 'Gather Medicinal Herb' in shown, shown
    m['herb_prompt'] = shown
    return True


def herbs_gathered():
    aim(m['herb_at'])
    if count(owner, 'Herb') < 3:
        if time.monotonic() - m['pressed'] > .8:
            m['pressed'] = time.monotonic()
            lib.send_verification_gameplay_key(client, 'E')
        return False
    return count(pawn, 'Herb') == 3


def eat_herb():
    assert lib.send_verification_food_request(client, item['Herb'])


def cured():
    if stats.is_food_sick() or 'FoodSickness' in notices(pawn) or count(pawn, 'Herb') != 2:
        return False
    return count(owner, 'Herb') == 2


# ---- 6: mending -------------------------------------------------------------------------------------------------------

def hurt():
    stats.set_hunger(80.0)
    stats.set_hydration(80.0)
    stats.restore_health(100)
    stats.apply_damage(40.0)
    m.update(t=time.monotonic(), h0=stats.get_health())


def paused_then_mends():
    elapsed = time.monotonic() - m['t']
    if elapsed < 8.0:
        assert stats.get_health() == m['h0'], 'mending started before the pause'
        return False
    if 'from' not in m and elapsed >= 11.0:
        m.update(**{'from': (time.monotonic(), stats.get_health())})
    if 'from' not in m or time.monotonic() - m['from'][0] < 6.0:
        return False
    t0, h0 = m.pop('from')
    rate = (stats.get_health() - h0) / (time.monotonic() - t0)
    assert .75 * MEND < rate < 1.3 * MEND, f'mending {rate:.3f} a second; expected about {MEND:.3f}'
    assert abs(pawn.get_survival_component().get_health() - stats.get_health()) < 1.0, 'client health differs'
    m['mend_rate'] = round(rate, 3)
    return True


def light_fire():
    """A campfire laid from the hand, as in slice 3."""
    campfire = unreal.load_asset('/Game/Elitewake/Items/Building/DA_Campfire')
    assert owner.get_inventory_component().add_item(campfire, 1) == 1
    assert lib.send_verification_equipment_request(client, campfire, HAND)
    at = owner.get_actor_location()
    m.update(aim_at=unreal.Vector(at.x + 220, at.y, ground(at.x + 220, at.y)), clicked=0.0, **{'from': None})


def mends_faster_by_fire():
    if m['from'] is None:
        aim(m['aim_at'])
        lit = [f for f in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCampfire) if f.is_lit()]
        if not lit or not [f for f in unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWCampfire) if f.is_lit()]:
            if client.get_placement_preview().is_placeable() and time.monotonic() - m['clicked'] > 1.2:
                m['clicked'] = time.monotonic()
                lib.send_verification_gameplay_key(client, 'LeftMouseButton')
            return False
        m['fire'] = lit[0]
        m['from'] = (time.monotonic(), stats.get_health())
        return False
    t0, h0 = m['from']
    if time.monotonic() - t0 < 5.0:
        return False
    rate = (stats.get_health() - h0) / (time.monotonic() - t0)
    assert 2.4 * MEND < rate < 3.6 * MEND, f'by the fire {rate:.3f} a second; expected about {3 * MEND:.3f}'
    m['fire_mend_rate'] = round(rate, 3)
    m['fire'].destroy_actor()
    m.pop('from')
    return True


# ---- 7: death, the bag, respawn -----------------------------------------------------------------------------------------

def die():
    assert lib.send_verification_equipment_request(client, item['Hatchet'], HAND, True)
    homes = [b.get_home() for b in boars(server_world)]
    x, y = homes[0].x - 7000, homes[0].y - 1500              # about 70 m from the boars, on the Plains by the track
    place(x, y, unreal.Vector(x + 100, y, ground(x, y)))
    m.update(death_spot=owner.get_actor_location(), carried={n: count(owner, n) for n in ('Meat', 'Herb', 'Hatchet')})
    assert m['carried']['Meat'] >= 3 and m['carried']['Herb'] == 2
    stats.apply_damage(1000.0)


def respawn_offered():
    w = death_widget()
    if not (stats.is_dead() and w.is_death_screen_shown() and w.is_respawn_available()):
        return False
    assert lib.send_verification_ui_key(client, 'Enter')
    return True


def respawned():
    if stats.is_dead():
        return False
    here = owner.get_actor_location()
    away = (here - m['death_spot']).length()
    assert away >= 5999, f'respawned {away / 100:.0f} m from the death spot'
    assert W.region_of(here.x, here.y) == 'Plains', f'respawned in {W.region_of(here.x, here.y)}'
    living = [(b.get_actor_location() - here).length() for b in boars(server_world) if not b.is_dead()]
    clear = min(living) if living else None
    assert clear is None or clear >= 3000, f'respawned {clear / 100:.0f} m from a living boar'
    m['living_boars'] = len(living)
    m['boar_home_m'] = round(min((b.get_home() - here).length() for b in boars(server_world)) / 100)
    bags = unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWDeathBag)
    assert len(bags) == 1, f'{len(bags)} bags'
    held = {n: bags[0].get_contents().get_item_count(item[n]) for n in m['carried']}
    assert held == m['carried'], f'the bag holds {held}; the survivor carried {m["carried"]}'
    assert all(count(owner, n) == 0 for n in m['carried'])
    at, fell = bags[0].get_actor_location(), m['death_spot']
    assert math.hypot(at.x - fell.x, at.y - fell.y) < 60, 'the bag is not where the survivor fell'
    lift = at.z - ground(at.x, at.y, at.z + 100, [bags[0]])
    assert abs(lift) < 30, f'the bag is {lift:.0f} cm off the ground'
    m['bag_lift_cm'] = round(lift)
    m.update(respawn_m=round(away / 100), boar_clear_m=None if clear is None else round(clear / 100), bag=bags[0])
    return True


def bag_saved_and_restored():
    bag = m['bag']
    where, held = bag.get_actor_location(), dict(m['carried'])
    assert unreal.EWSurvivorSave.save_survivor(owner, SLOT, True), 'save failed'
    bag.destroy_actor()
    assert unreal.EWSurvivorSave.load_save(SLOT).apply_to(owner), 'restore failed'
    unreal.GameplayStatics.delete_game_in_slot(SLOT, 0)
    back = [b for b in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWDeathBag) if not b.is_actor_being_destroyed()]
    assert len(back) == 1, f'{len(back)} bags after the restore'
    assert {n: back[0].get_contents().get_item_count(item[n]) for n in held} == held, 'the restored bag lost its contents'
    assert (back[0].get_actor_location() - where).length() < 5
    m['bag'] = back[0]
    return True


def to_bag():
    at = m['bag'].get_actor_location()
    place(at.x - 150, at.y, at)
    m.update(pressed=0.0, opened=False)


def bag_emptied():
    aim(m['bag'].get_actor_location() if not m['bag'].is_actor_being_destroyed() else owner.get_actor_location())
    if not m['opened']:
        if time.monotonic() - m['pressed'] > 1.0:
            m['pressed'] = time.monotonic()
            lib.send_verification_gameplay_key(client, 'E')
        shown = [w for w in unreal.WidgetLibrary.get_all_widgets_of_class(client_world, unreal.EWContainerWidget, False) if w.is_in_viewport()]
        if shown:
            m.update(opened=True, widget=shown[0])
        return False
    if all(count(owner, n) == v for n, v in m['carried'].items()):
        bags = [b for b in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWDeathBag) if not b.is_actor_being_destroyed()]
        return not bags and all(count(pawn, n) == v for n, v in m['carried'].items())
    if time.monotonic() - m['pressed'] > .6:
        m['pressed'] = time.monotonic()
        # The client's own keys (an RPC called from Python would run only on the client): Right to the bag, A to take.
        if m['widget'].get_cursor_column() != 1:
            assert lib.send_verification_ui_key(client, 'Right')
        else:
            assert lib.send_verification_ui_key(client, 'Gamepad_FaceButton_Bottom')
    return False


STEPS = [
    ('Two wild boars root in their Plains pocket off the track, on both machines; a boar runs slower than a sprint', lambda: None, present, 10),
    ('A survivor on the track at its nearest point is ignored: no charge, no harm', to_track, ignored_on_track, 9),
    ('Within 4 m one grunts, charges and gores: health falls on server and client, a red number shows', near_boar, gored, 10),
    ('Away beyond 10 m the boar gives up', run_off, gave_up, 6),
    ('With the Stone Hatchet, Left Mouse kills it on both machines', arm, killed, 30),
    ('E at the body gives 3 to 5 Raw Meat', lambda: None, harvested, 8),
    ('Food sickness shows on the client', fall_sick, sick_shown, 5),
    ('At the yarrow by the track the prompt reads "Gather Medicinal Herb"', to_herbs, herb_prompt, 6),
    ('E gathers all three herbs, on both machines', lambda: None, herbs_gathered, 8),
    ('Eating one ends the sickness on both machines', eat_herb, cured, 5),
    ('Fed and watered, a hurt survivor mends after a 10 s pause, about 0.11 health a second', hurt, paused_then_mends, 25),
    ('Beside a campfire laid from the hand the survivor mends three times as fast', light_fire, mends_faster_by_fire, 15),
    ('Killed carrying the meat and herbs, the client is offered Respawn; Enter takes it', die, respawn_offered, 12),
    ('Back on the Plains 60 m off and 30 m clear of the boars; meat, herbs and hatchet wait in a bag on the ground where they fell', lambda: None, respawned, 6),
    ('The bag and what it holds survive a save and restore', lambda: None, bag_saved_and_restored, 5),
    ('E at the bag opens it; Right, then A for each stack, takes everything back into the pack; the emptied bag goes', to_bag, bag_emptied, 15),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    out = {k: v for k, v in m.items() if isinstance(v, (int, float, str, list, dict)) and k not in ('t', 'pressed', 'carried', 'clicked')}
    out['carried'] = m.get('carried')
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error, 'measured': out}, indent=2, default=str), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK RiskRecovery success={error is None} error={error}')


def tick(delta):
    follow()
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
            raise TimeoutError(f'not done within {timeout} s; health {stats.get_health():.1f}, '
                               f'prompt {str(client.get_interaction_widget().get_displayed_prompt())!r}')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
