"""Play: level, experience and stat points (owner, October 22). The Survivor panel shows level and stats before any point is earned, with the raise arrows faint and
dead; earning a level makes one live; C then Down then Enter (the keyboard path of the controller's d-pad and A) spends it; the stat's effect lands on the server and
replicates. Listen-server plus one client (EW_PLAY_PLAYERS=2). Writes Saved/StatsPlayResult.json."""
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
progress = owner.get_progression_component()
stats = owner.get_survival_component()
remote_progress = client.get_controlled_pawn().get_progression_component()
remote_stats = client.get_controlled_pawn().get_survival_component()
phase = 0
next_at = time.monotonic() + 2
checks = []
handle = None
state = {}


def menu():
    return next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(client_world, unreal.EWInventoryWidget, False)
                if w.get_owning_player() == client and w.is_in_viewport())


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    client.set_inventory_open(False)
    Path(unreal.Paths.project_saved_dir(), 'StatsPlayResult.json').write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error}, indent=2))


def tick(delta):
    global phase, next_at
    if time.monotonic() < next_at:
        return
    next_at = time.monotonic() + 1.5
    try:
        if phase == 0:
            assert progress.get_level() == 1 and progress.get_unspent_points() == 0
            state['max_health'] = stats.get_max_health()
            client.set_inventory_open(True)
        elif phase == 1:
            m = menu()
            assert 'LEVEL 1' in str(m.get_level_text()), str(m.get_level_text())
            for s in range(4):
                assert not m.is_stat_arrow_enabled(s), f'arrow {s} live with no points'
                assert m.get_stat_arrow_opacity(s) < 0.5
            checks.append('Level and four stats show before any point is earned, the raise arrows faint and disabled')
            need = progress.get_experience_for_next_level()
            gained = progress.grant_experience(need)
            assert gained == 1, f'{gained} levels'
        elif phase == 2:
            m = menu()
            assert remote_progress.get_level() == 2 and remote_progress.get_unspent_points() == 1, 'level did not replicate'
            assert 'LEVEL 2' in str(m.get_level_text())
            for s in range(4):
                assert m.is_stat_arrow_enabled(s) and m.get_stat_arrow_opacity(s) > 0.9, f'arrow {s} not live'
            checks.append('One level earns exactly one point; all four arrows become clear and live on the client')
            assert lib.send_verification_ui_key(client, 'C')
        elif phase == 3:
            assert menu().get_stat_focus() == 0, 'C did not start choosing a stat'
            assert lib.send_verification_ui_key(client, 'Gamepad_DPad_Down')
            assert lib.send_verification_ui_key(client, 'Gamepad_DPad_Up')
            assert lib.send_verification_ui_key(client, 'Up')       # wraps to the last stat
        elif phase == 4:
            assert menu().get_stat_focus() == 3, f'focus {menu().get_stat_focus()}'
            assert lib.send_verification_ui_key(client, 'Down')      # wraps back to the first
        elif phase == 5:
            assert menu().get_stat_focus() == 0
            assert lib.send_verification_ui_key(client, 'Gamepad_FaceButton_Bottom')
        elif phase == 6:
            assert progress.get_unspent_points() == 0, 'the controller A button did not spend the point'
            assert progress.get_stat_points(unreal.EWStat.VITALITY) == 1
            assert stats.get_max_health() == state['max_health'] + 10, f'max health {stats.get_max_health()}'
            assert remote_stats.get_max_health() == state['max_health'] + 10, 'max health did not replicate'
            m = menu()
            for s in range(4):
                assert not m.is_stat_arrow_enabled(s), 'arrows stay live with no point left'
            checks.append('A spends the point: Vitality 1, +10 maximum health on server and client, arrows go faint again')
            progress.grant_experience(progress.get_experience_for_next_level())
        elif phase == 7:
            m = menu()
            assert m.is_stat_arrow_enabled(2)
            assert lib.send_verification_ui_key(client, 'Down')
            assert lib.send_verification_ui_key(client, 'Down')
            assert lib.send_verification_ui_key(client, 'Enter')
        elif phase == 8:
            total = sum(progress.get_stat_points(s) for s in (unreal.EWStat.VITALITY, unreal.EWStat.ENDURANCE, unreal.EWStat.STRENGTH, unreal.EWStat.FORTITUDE))
            assert total == 2 and progress.get_unspent_points() == 0, f'total {total}, unspent {progress.get_unspent_points()}'
            checks.append('A second level earns a second point, spent on another stat; the total of spent points equals levels gained')
            finish()
            return
        phase += 1
    except Exception as exc:
        finish(f'Phase {phase}: {exc!r}')


handle = unreal.register_slate_post_tick_callback(tick)
