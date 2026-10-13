"""Client acceptance for a survivor's chosen look on the coast.

Needs Play in /Game/Elitewake/Maps/Lvl_CoastalPlayground as a listen server plus one client, with the body roster
from Scripts/Setup/build_title.py. Run unattended with run_play_check.py.

  1. The client asks for the look the character creator would send (the woman, the third colouring, 4% taller):
     its survivor wears it on its own screen and on the host's.
  2. An impossible request (a body and colouring the roster lacks, an absurd height) is brought within the roster.
Writes Saved/AppearancePlayResult.json.
"""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'AppearancePlayResult.json')
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
pawn = client.get_controlled_pawn()


def player_id(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if player_id(p) == player_id(pawn))
roster = unreal.load_asset('/Game/Elitewake/Characters/DA_BodyRoster')
bodies, tones = roster.get_editor_property('bodies'), roster.get_editor_property('tones')
checks = []
state = {'index': 0, 'begun': False, 'deadline': 0.0, 'handle': None, 'memo': {}}


def look(body, tone, height):
    a = unreal.EWAppearance()
    a.body, a.tone, a.height = body, tone, height
    return a


def wears(who, body, height):
    mesh = who.get_editor_property('mesh')
    return mesh.get_editor_property('skeletal_mesh_asset') == bodies[body].get_editor_property('mesh') \
        and abs(mesh.get_editor_property('relative_scale3d').z - height) < .001


def ask_woman():
    assert lib.send_verification_appearance_request(client, look(1, 2, 1.04))


def woman_everywhere():
    if not (wears(pawn, 1, 1.04) and wears(owner, 1, 1.04)):
        return False
    a = pawn.get_appearance()
    assert a.body == 1 and a.tone == 2, a
    return True


def ask_nonsense():
    assert lib.send_verification_appearance_request(client, look(200, 200, 9.0))


def clamped():
    a = owner.get_appearance()
    if a.tone != len(tones) - 1:
        return False   # not arrived yet
    assert a.body == len(bodies) - 1 and abs(a.height - 1.08) < .001, a
    return wears(pawn, len(bodies) - 1, 1.08)


STEPS = [
    ('The client asks for the woman, third colouring, 4% taller: its survivor wears it on its screen and the host\'s', ask_woman, woman_everywhere, 5),
    ('An impossible request is brought within the roster on both', ask_nonsense, clamped, 5),
]


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    RESULT.write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK Appearance success={error is None} error={error}')


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
            seen = {name: (who.get_editor_property('mesh').get_editor_property('skeletal_mesh_asset').get_name(),
                           round(who.get_editor_property('mesh').get_editor_property('relative_scale3d').z, 3), str(who.get_appearance()))
                    for name, who in (('client', pawn), ('host', owner))}
            raise TimeoutError(f'not done within {timeout} s; {seen}')
    except Exception as error:
        finish(f'step {state["index"]} ({description}): {error!r}')


state['handle'] = unreal.register_slate_post_tick_callback(tick)
