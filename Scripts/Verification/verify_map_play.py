"""World map overview, free-pan/zoom, marker and input lifecycle on a listen server/client."""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
worlds = lib.get_play_worlds()
controllers = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
c = next(p for p in controllers if not p.has_authority())
host = next(p for p in controllers if p.has_authority())
cw = worlds[controllers.index(c)]
sw = worlds[controllers.index(host)]

def pid(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']

owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(sw, unreal.EWCharacter)
             if pid(p) == pid(c.get_controlled_pawn()))
server_pc = owner.get_controller()
pawn = c.get_controlled_pawn()
base = pawn.get_actor_location()
start_world = unreal.GameplayStatics.get_time_seconds(cw)
checks = []
phase = 0
handle = None
next_at = time.monotonic() + 3
assert not c.is_map_open()
assert lib.send_verification_gameplay_key(c, 'M')

def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    lib.send_verification_gameplay_key(c, 'M') if c.is_map_open() else None
    c.set_inventory_open(False)
    Path(unreal.Paths.project_saved_dir(), 'MapPlayResult.json').write_text(
        json.dumps({'success': error is None, 'checks': checks, 'error': error}, indent=2))

def tick(delta):
    global phase, next_at
    if phase == 3:
        pawn.add_movement_input(unreal.Vector(1, 0, 0), 1)
    if time.monotonic() < next_at:
        return
    next_at = time.monotonic() + 2
    try:
        ui = next((x for x in unreal.WidgetLibrary.get_all_widgets_of_class(cw, unreal.EWMapWidget, False)
                   if x.get_owning_player() == c and x.is_in_viewport()), None)
        if phase not in (4, 6):
            assert ui, 'local world-map widget missing'
        if phase == 0:
            assert c.is_map_open() and server_pc.is_map_open() and not host.is_map_open()
            assert ui.has_map_capture()
            assert len(unreal.GameplayStatics.get_all_actors_of_class(cw, unreal.SceneCapture2D)) == 1
            assert not unreal.GameplayStatics.get_all_actors_of_class(sw, unreal.SceneCapture2D)
            assert not c.is_move_input_ignored() and c.is_look_input_ignored()
            assert str(ui.get_region_title()).strip(), 'current region label is empty'
            assert 'SURROUNDING AREA' not in str(ui.get_region_title()).upper()
            hint = str(ui.get_map_hint_text())
            assert 'Walking remains available' not in hint and 'World continues' not in hint, hint
            regions = unreal.GameplayStatics.get_all_actors_of_class(cw, unreal.EWClimateRegion)
            assert len(regions) >= 5, f'world map only knows {len(regions)} island-region actors'
            xs = [r.get_actor_location().x for r in regions]
            ys = [r.get_actor_location().y for r in regions]
            rx = [r.get_editor_property('radii').x for r in regions]
            ry = [r.get_editor_property('radii').y for r in regions]
            world_width_x = max(x + radius for x, radius in zip(xs, rx)) - min(x - radius for x, radius in zip(xs, rx))
            world_width_y = max(y + radius for y, radius in zip(ys, ry)) - min(y - radius for y, radius in zip(ys, ry))
            full_world_width = max(world_width_x, world_width_y)
            assert ui.get_view_width() >= full_world_width * .9, (
                f'overview is too narrow for all {len(regions)} region actors: {ui.get_view_width():.0f} vs {full_world_width:.0f}')
            checks.append('M opens local full-world capture with region label and player marker')
            c.set_inventory_open(True)
            assert not any(x.is_in_viewport() and x.get_owning_player() == c for x in
                           unreal.WidgetLibrary.get_all_widgets_of_class(cw, unreal.EWInventoryWidget, False))
            assert lib.send_verification_gameplay_key(c, 'C') and lib.send_verification_gameplay_key(c, 'LeftShift')
            checks.append('Map removes status messages and blocks inventory, stance and sprint keys')
            state['center'] = ui.get_map_center()
            state['width'] = ui.get_view_width()
            ui.set_pan_input(unreal.Vector2D(1, 0))
        elif phase == 1:
            moved = (ui.get_map_center() - state['center']).length()
            assert moved > 100, f'right-stick pan did not move overview: {moved}'
            ui.set_pan_input(unreal.Vector2D(0, 0))
            state['center'] = ui.get_map_center()
            ui.adjust_zoom(1.0)
            checks.append(f'Free pan shifts map center without recentering ({moved:.0f} cm)')
        elif phase == 2:
            assert ui.get_view_width() < state['width'] * .9, 'zoom-in did not change map scale'
            state['center'] = ui.get_map_center()
            checks.append('Zoom input changes view scale independently of pan position')
        elif phase == 3:
            assert (pawn.get_actor_location() - base).length() > 15
            assert unreal.GameplayStatics.get_time_seconds(cw) > start_world + 8
            assert (ui.get_map_center() - state['center']).length() < 1, 'map camera followed/recentered on player'
            checks.append('Player movement does not recenter the freely panned map')
            assert lib.send_verification_gameplay_key(c, 'M')
        elif phase == 4:
            assert not c.is_map_open() and not server_pc.is_map_open()
            assert not c.is_look_input_ignored() and not c.is_move_input_ignored()
            assert not unreal.GameplayStatics.get_all_actors_of_class(cw, unreal.SceneCapture2D)
            checks.append('M closes and destroys capture; input restrictions clear')
            c.set_inventory_open(True)
            assert lib.send_verification_ui_key(c, 'M')
        elif phase == 5:
            assert c.is_map_open() and not any(x.is_in_viewport() and x.get_owning_player() == c for x in
                unreal.WidgetLibrary.get_all_widgets_of_class(cw, unreal.EWInventoryWidget, False))
            checks.append('M switches inventory into map without leaving inventory input locks')
            assert lib.send_verification_gameplay_key(c, 'M')
        elif phase == 6:
            for _ in range(5):
                assert lib.send_verification_gameplay_key(c, 'M')
                assert lib.send_verification_gameplay_key(c, 'M')
            assert not c.is_map_open() and not c.is_look_input_ignored()
            checks.append('Repeated open/close leaves no persistent input lock')
            finish()
            return
        phase += 1
    except Exception as exc:
        finish(f'Phase {phase}: {exc!r}')

state = {}
handle = unreal.register_slate_post_tick_callback(tick)
