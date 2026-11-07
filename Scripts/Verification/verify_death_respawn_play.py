"""Play: damage flashes a red number, dying fades to black with frost and a Respawn choice (mouse-less: Enter, then the controller's A), the dead survivor's belongings
wait in a bag where they fell, and they come back alive at a safe place a meaningful distance away (owner, October 22). Listen-server plus one client
(EW_PLAY_PLAYERS=2). Writes Saved/DeathRespawnPlayResult.json."""
import unreal, json, time
from pathlib import Path
lib = unreal.EWEditorVerificationLibrary
worlds = lib.get_play_worlds()
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]


def pid(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if pid(p) == pid(client.get_controlled_pawn()))
stats = owner.get_survival_component()
inv = owner.get_inventory_component()
wood = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWood')
assert wood
MIN_AWAY = 6000.0
phase = 0
next_at = time.monotonic() + 2
checks = []
handle = None
state = {}


def widget():
    return next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(client_world, unreal.EWDeathWidget, False) if w.get_owning_player() == client)


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    Path(unreal.Paths.project_saved_dir(), 'DeathRespawnPlayResult.json').write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error}, indent=2))


def bags():
    return unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWDeathBag)


def tick(delta):
    global phase, next_at
    if time.monotonic() < next_at:
        return
    next_at = time.monotonic() + 1.0
    try:
        if phase == 0:
            assert widget() is not None
            assert not stats.is_dead()
            assert inv.add_item(wood, 7) == 7
            state['flashes'] = widget().get_damage_flash_count()
            stats.apply_damage(6.0)
        elif phase == 1:
            w = widget()
            assert w.get_damage_flash_count() == state['flashes'] + 1, f"flash count {w.get_damage_flash_count()}"
            checks.append('A hit of six makes the client show one red damage number')
            assert not w.is_death_screen_shown()
            state['death_spot'] = owner.get_actor_location()
            state['region'] = None
            stats.apply_damage(1000.0)
        elif phase == 2:
            assert stats.is_dead() and owner.is_dead()
            w = widget()
            assert w.is_death_screen_shown(), 'no death screen'
            assert 0.0 < w.get_fade_alpha() <= 1.0
            assert not w.is_respawn_available() or w.get_fade_alpha() >= 0.99
            checks.append('Health at zero: the survivor is dead and the client fades the screen to black')
        elif phase == 4:
            w = widget()
            assert w.get_fade_alpha() >= 0.99 and w.is_respawn_available(), 'respawn not offered after the fade'
            checks.append('Fully black after the fade, Respawn is offered')
            assert lib.send_verification_ui_key(client, 'Enter')
        elif phase == 5:
            assert not stats.is_dead(), 'still dead after Enter'
            here = owner.get_actor_location()
            away = unreal.Vector.distance(here, state['death_spot'])
            assert away >= MIN_AWAY - 1, f'respawned only {away:.0f} cm from the death spot'
            assert stats.get_health() > 0
            checks.append(f'Enter respawns the survivor {away/100:.0f} m away, alive')
            bs = bags()
            assert len(bs) == 1, f'{len(bs)} death bags'
            assert bs[0].get_contents().get_item_count(wood) == 7, 'the bag does not hold the wood'
            assert inv.get_item_count(wood) == 0, 'the survivor still carries the wood'
            at, fell = bs[0].get_actor_location(), state['death_spot']
            # Under the body, on the ground (November 1: it had floated at the body's middle).
            assert ((at.x - fell.x) ** 2 + (at.y - fell.y) ** 2) ** .5 < 50 and at.z < fell.z - 40, (at, fell)
            checks.append('The seven wood wait in a bag at the place of death; the survivor carries none')
        elif phase == 7:
            w = widget()
            assert not w.is_death_screen_shown(), 'death screen still up'
            assert w.get_fade_alpha() < 0.05, f'screen still dark: {w.get_fade_alpha()}'
            checks.append('The black clears and the death screen goes after respawn')
            state['death_spot'] = owner.get_actor_location()
            stats.apply_damage(1000.0)
        elif phase == 10:
            w = widget()
            assert w.is_respawn_available(), 'second death: respawn not offered'
            assert lib.send_verification_ui_key(client, 'Gamepad_FaceButton_Bottom')
        elif phase == 11:
            assert not stats.is_dead(), 'the controller A button did not respawn'
            away = unreal.Vector.distance(owner.get_actor_location(), state['death_spot'])
            assert away >= MIN_AWAY - 1
            checks.append('The controller A button respawns too, again far from the second death')
            finish()
            return
        phase += 1
    except Exception as exc:
        finish(f'Phase {phase}: {exc!r}')


handle = unreal.register_slate_post_tick_callback(tick)
