"""Client sailing acceptance for the raft and the dinghy on the coastal map.

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, with both craft from
Scripts/Setup/build_small_craft.py. Run unattended with run_play_check.py.

For each craft, through ordinary owned requests and movement input, the client:
  1. finds the built-in steering already fitted (the raft's paddles, the dinghy's tiller); on the dinghy it also
     installs a carried Small sail on the dinghy's own mast; the raft has no sail at all,
  2. raises the anchor, takes the built-in helm and sets full sail (on the raft, a hard stroke) with forward input,
  3. sails or paddles for 4 s, leaves the helm and drops the anchor.
Each step waits for its result on the server and on the client's copy, with a timeout.
Writes Saved/SmallCraftPlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'SmallCraftPlayResult.json')
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]
# Crew dependency (owner, October 18): the helm sets only sails with a hired sailhand, so every ship here is crewed first.
for _s in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWShip):
    _s.crew_every_sail()
pawn = client.get_controlled_pawn()


def player_id(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if player_id(p) == player_id(pawn))


def craft(ship_id):
    ship = next(s for s in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWShip)
                if str(s.get_editor_property('definition').get_editor_property('ship_id')) == ship_id)
    peer = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWShip) if a.get_name() == ship.get_name())
    return ship, peer


sail = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestSailSmall')
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
old_throttle = settings.get_editor_property('bThrottleCPUWhenNotForeground')
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'aim': None, 'input': None, 'frame': 0, 'handle': None, 'memo': {}}

# Where to stand, in each craft's frame, to reach each place without bumping its thwarts, crate or mast.
STANDS = {'Raft': {'Anchor': (120, -40), 'Helm': (-70, 0)},
          'Dinghy': {'Sail': (-30, 0), 'Anchor': (85, 0), 'Helm': (-30, 0)}}


def steps_for(ship_id):
    ship, peer = craft(ship_id)

    def target(name):
        return ship.get_anchor_point_world() if name == 'Anchor' else ship.get_mount_world_transform(name).translation

    def go(name):
        def begin():
            x, y = STANDS[ship_id][name]
            spot = ship.get_actor_transform().transform_location(unreal.Vector(x, y, ship.get_deck_height() + 98))
            for p in (owner, pawn):
                assert p.teleport(spot, ship.get_actor_rotation())
            state['aim'] = lambda: target(name)
            keep_aim()
            assert lib.send_verification_interaction_request(client, peer)
        return begin

    paddled = ship.get_editor_property('definition').get_editor_property('paddled')

    def prepare():
        state['current'] = ship_id
        builtin = ship.get_fitting('Helm')
        assert builtin and peer.get_fitting('Helm') == builtin, 'built-in steering must be fitted on both copies'
        assert ship.get_fitting('Sail') is None and ship.is_anchored()
        mounts = [str(m.get_editor_property('mount_id')) for m in ship.get_editor_property('definition').get_editor_property('mounts')]
        if paddled:
            # Owner, October 18: the raft has one functional Small sail hardpoint (empty, as every hull's are).
            assert mounts == ['Helm', 'Sail'], f'a paddled raft has its paddles and one sail hardpoint: {mounts}'
        else:
            assert owner.get_inventory_component().add_item(sail, 1) == 1

    def full_sail():
        state['aim'] = None
        state['frame0'] = state['frame']
        taps = (0, 10) if paddled else (0, 10, 20, 30)
        state['input'] = lambda f: pawn.do_move(0, 1) if any(start <= f < start + 5 for start in taps) else pawn.do_move(0, 0)

    def begin_run():
        state['memo'][ship_id] = {'start': ship.get_actor_location(), 't': time.monotonic()}
        state['input'] = None

    def ran():
        m = state['memo'][ship_id]
        if time.monotonic() - m['t'] < 4.0:
            return False
        m['moved'] = (ship.get_actor_location() - m['start']).length()
        m['gap'] = (ship.get_actor_location() - peer.get_actor_location()).length()
        assert m['moved'] > 100, f'moved only {m["moved"]:.0f} cm'
        assert m['gap'] < 300, f'client copy {m["gap"]:.0f} cm from server'
        # The helmsman works the helm on every screen: a paddle stroke with a paddle in hand, or hands on the tiller.
        wanted = 'AS_Paddle_v1' if paddled else 'AS_HelmHold_v1'
        for who, where in ((pawn, 'client'), (owner, 'host')):
            loop = who.get_loop_animation()
            assert loop and loop.get_name() == wanted, f'{where} plays {loop.get_name() if loop else None}, not {wanted}'
            held = who.get_held_mesh()
            if paddled:
                assert held and held.get_name() == 'SM_HeldPaddle_v1', f'{where} holds {held}'
        return True

    def leave():
        assert lib.send_verification_interaction_request(client, peer)

    if paddled:
        rigging = [(f'{ship_id}: its paddles are fitted on server and client, and its one Small sail hardpoint is empty', prepare, lambda: True, 2)]
    else:
        rigging = [(f'{ship_id}: built-in steering is fitted on server and client; Small sail granted in Play only', prepare, lambda: True, 2),
                   (f'{ship_id}: client installs the Small sail on its own mast', go('Sail'),
                    lambda: ship.get_fitting('Sail') == sail and peer.get_fitting('Sail') == sail, 6)]
    effort = 'a hard stroke' if paddled else 'full sail'
    return rigging + [
        (f'{ship_id}: client raises the anchor', go('Anchor'), lambda: not ship.is_anchored() and not peer.is_anchored(), 6),
        (f'{ship_id}: client takes the built-in helm', go('Helm'),
         lambda: ship.get_helmsman() == owner and peer.get_helmsman() == pawn, 6),
        (f'{ship_id}: forward input sets {effort}', full_sail,
         lambda: ship.get_sail_state() == unreal.EWSailState.FULL and peer.get_sail_state() == unreal.EWSailState.FULL, 6),
        (f'{ship_id}: the craft moves for 4 s, the client copy keeps up, and the helmsman ' + ('paddles with a paddle in hand' if paddled else 'holds the tiller'), begin_run, ran, 8),
        (f'{ship_id}: client leaves the helm', leave, lambda: ship.get_helmsman() is None and peer.get_helmsman() is None, 6),
        (f'{ship_id}: client drops the anchor', go('Anchor'), lambda: ship.is_anchored() and peer.is_anchored(), 6),
    ]


def keep_aim():
    if not state['aim']:
        return
    eye = owner.get_actor_location() + unreal.Vector(0, 0, owner.get_editor_property('base_eye_height'))
    rotation = unreal.MathLibrary.find_look_at_rotation(eye, state['aim']())
    owner.get_controller().set_control_rotation(rotation)
    client.set_control_rotation(rotation)


STEPS = steps_for('Raft') + steps_for('Dinghy')


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    settings.set_editor_property('bThrottleCPUWhenNotForeground', old_throttle)
    RESULT.write_text(json.dumps({
        'success': error is None, 'checks': checks, 'error': error,
        'runs': {k: {'moved': round(v.get('moved', 0)), 'gap': round(v.get('gap', 0))} for k, v in state['memo'].items()},
    }, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK SmallCraft success={error is None} error={error}')


def tick(delta):
    state['frame'] += 1
    if state['input']:
        state['input'](state['frame'] - state.get('frame0', 0))
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
            raise TimeoutError(f'not done within {timeout} s')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
