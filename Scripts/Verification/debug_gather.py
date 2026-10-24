"""Debug: put a berry bush 1.5 m ahead of the survivor and press E; report what the eye trace sees and what arrives. EW_PLAY_PLAYERS=2. Writes Saved/DebugGather.json."""
import unreal, json, time
from pathlib import Path
lib = unreal.EWEditorVerificationLibrary
worlds = lib.get_play_worlds()
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server = next(w for w, c in zip(worlds, pcs) if c.has_authority())


def pid(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server, unreal.EWCharacter) if pid(p) == pid(client.get_controlled_pawn()))
berry = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestAzulBerry')
out = {'steps': []}
state = {'i': 0, 'at': time.monotonic() + 3}
handle = None


def finish():
    unreal.unregister_slate_post_tick_callback(handle)
    Path(unreal.Paths.project_saved_dir(), 'DebugGather.json').write_text(json.dumps(out, indent=1, default=str))


def setup():
    client.set_inventory_open(False)
    for w in worlds:
        for p in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.EWCharacter):
            ok = p.teleport(unreal.Vector(0, 0, 96) if pid(p) == pid(owner) else unreal.Vector(-500, 500, 96), unreal.Rotator())
            out['steps'].append(('teleport', p.get_name(), ok))
    for c in pcs:
        c.set_control_rotation(unreal.Rotator())
    node = lib.spawn_verification_hand_gatherable(server, unreal.Vector(150, 0, 160), berry, 5)
    node.set_editor_property('gathering_kind', unreal.EWHandGatheringKind.BERRIES)
    node.force_net_update()
    out['node'] = str(node.get_actor_location())


def look():
    eye, rot = owner.get_actor_eyes_view_point()
    hit = unreal.SystemLibrary.line_trace_single(server, eye, eye + rot.get_forward_vector() * 300, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [owner], unreal.DrawDebugTrace.NONE, True)
    out['eye'] = str(eye)
    out['pawn'] = str(owner.get_actor_location())
    out['hit'] = str(hit.to_tuple()[9] if hit else None)
    out['inventory_open_client'] = bool(client.is_inventory_open())


def press():
    assert lib.send_verification_ui_key(client, 'E')


def result():
    out['berries'] = owner.get_inventory_component().get_item_count(berry)
    out['entries'] = [str(e.get_editor_property('item_definition').get_name()) for e in owner.get_inventory_component().get_inventory_entries()]


steps = [(setup, 2.0), (look, 0.5), (press, 2.5), (result, 0.5)]


def tick(delta):
    if time.monotonic() < state['at']:
        return
    try:
        if state['i'] >= len(steps):
            finish()
            return
        fn, wait = steps[state['i']]
        fn()
        state['i'] += 1
        state['at'] = time.monotonic() + wait
    except Exception as exc:
        out['error'] = repr(exc)
        finish()


handle = unreal.register_slate_post_tick_callback(tick)
