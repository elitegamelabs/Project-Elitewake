"""Listens in on another Play check: runs it unchanged, and when it has finished checks which sounds each machine
started while it ran (UEWSoundLibrary counts), and how the ship and soundscape loops moved on the client.

Set EW_AUDIO_DURING to the name of the check (a key of EXPECT below, e.g. cannon_fight for
verify_cannon_fight_play.py), run with run_play_check.py on that check's map, and point EW_PLAY_RESULT at
AudioDuring_<name>Result.json. Proves which sound starts on which machine and when, not how it sounds.
"""
import json
import os
import runpy
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
snd = unreal.EWSoundLibrary
NAME = os.environ['EW_AUDIO_DURING']
HERE = Path(__file__).resolve().parent
SAVED = Path(unreal.Paths.project_saved_dir())
RESULT = SAVED / f'AudioDuring_{NAME}Result.json'

# Check -> (its result file, sounds that must start on both machines (any of each tuple), on the client only, and
# the least the client's loop levels must reach while it runs).
EXPECT = {
    # On /Game/Elitewake/Maps/Test/Lvl_ShipsTest: shots fly both ways, hulls are struck, the sloop sinks.
    'cannon_fight': ('CannonFightPlayResult.json', [('S_CannonFire_v1',), ('S_HullHit_v1',), ('S_ShipSinking_v1',)], [], {}),
    'cannon': ('CannonPlayResult.json', [('S_CannonFire_v1',), ('S_ShotSplash_v1', 'S_PickaxeStone_v1')], [], {}),
    'leaks': ('LeaksPlayResult.json', [('S_Bail_v1',)], [], {'creak': .25}),
    # The sinking check sets the survivor down beside a crate rather than swimming there; ship_deck hears the strokes.
    'sinking': ('SinkingPlayResult.json', [('S_ShipSinking_v1',)], [], {}),
    'ship_deck': ('ShipDeckPlayResult.json', [('S_StepDeck_v1', 'S_StepDeck_v1b')], [('S_SwimStroke_v1',)],
                  {'creak': .4, 'rigging': .3}),
    # The sloop's anchor comes up at the capstan and goes down again at the end (its chain catching a moment later); she
    # sails and turns, and her wake trail (UEWWakeTrailComponent) reaches back about 20 m and bends with her.
    'ship_sailing': ('ShipSailingPlayResult.json', [('S_AnchorRaise_v1',), ('S_AnchorDrop_v1',), ('S_AnchorCatch_v1',)], [],
                     {'wake_patches': 10, 'wake_reach': 1500, 'wake_bend': 60}),
    'caves': ('CavesPlayResult.json', [], [('S_StepStone_v1',)], {'cave': .9}),
    'day_night': ('DayNightPlayResult.json', [], [], {'insects': .2}),
}
inner_result, both_need, client_need, levels_need = EXPECT[NAME]
INNER = SAVED / inner_result

worlds = lib.get_play_worlds()
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
client_world = worlds[pcs.index(client)]
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
scape = client.get_soundscape_component()
started = time.time()
if INNER.exists():
    INNER.unlink()
seen = {'creak': 0.0, 'rigging': 0.0, 'cave': 0.0, 'insects': 0.0, 'in_cave': False, 'ship_loops': False,
        'wake_patches': 0, 'wake_reach': 0.0, 'wake_bend': 0.0}
state = {'handle': None, 'shot': None, 'done_at': None}
# Seconds to keep listening once the check is done, for sounds that follow its last step (an anchor catching the bottom).
AFTER = 3.0
SHOTS = SAVED / 'Screenshots' / 'Wake'


def wake_shot(ship, trail):
    """While the sloop sails with her trail laid, the server's own survivor looks down on it from behind and above (its
    window is the one screenshots capture); taken a moment after it is put there, before it falls."""
    host_pc = next(c for c in pcs if c.has_authority())
    host = host_pc.get_controlled_pawn()
    if state['shot'] is None and trail.get_patch_count() >= 14:
        f = ship.get_actor_forward_vector()
        eye = ship.get_actor_location() - f * 3200 + unreal.Vector(0, 0, 1400)
        host.set_actor_location(eye, False, True)
        host_pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, ship.get_actor_location() - f * 900))
        state['shot'] = time.monotonic()
    elif state['shot'] and state['shot'] > 0 and time.monotonic() - state['shot'] > .35:
        SHOTS.mkdir(parents=True, exist_ok=True)
        unreal.SystemLibrary.execute_console_command(server_world, f'Shot showui filename="{SHOTS / "sloop_wake.png"}"')
        state['shot'] = -1


def watch():
    seen['cave'] = max(seen['cave'], scape.get_cave_level())
    seen['insects'] = max(seen['insects'], scape.get_insect_level())
    seen['in_cave'] = seen['in_cave'] or scape.is_in_cave()
    for ship in unreal.GameplayStatics.get_all_actors_of_class(client_world, unreal.EWShip):
        trail = ship.get_editor_property('wake_trail')
        if trail and trail.get_patch_count() > 2:
            n = trail.get_patch_count()
            seen['wake_patches'] = max(seen['wake_patches'], n)
            seen['wake_reach'] = max(seen['wake_reach'], trail.get_trail_reach())
            # How far the trail's middle lies off the line from its oldest to its newest patch: it bends with a turn.
            a, b, m = trail.get_patch_location(0), trail.get_patch_location(n - 1), trail.get_patch_location(n // 2)
            ab = b - a
            if ab.length() > 1:
                cross = abs((m.x - a.x) * ab.y - (m.y - a.y) * ab.x) / ab.length()
                seen['wake_bend'] = max(seen['wake_bend'], cross)
            if NAME == 'ship_sailing':
                server_ship = next((s for s in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWShip)
                                    if s.get_name() == ship.get_name()), None)
                if server_ship:
                    wake_shot(server_ship, server_ship.get_editor_property('wake_trail'))
        sounds = ship.get_editor_property('sounds')
        if sounds:
            seen['creak'] = max(seen['creak'], sounds.get_creak_level())
            seen['rigging'] = max(seen['rigging'], sounds.get_rigging_level())
            seen['ship_loops'] = seen['ship_loops'] or sounds.are_loops_playing()


def heard(world, names):
    return sum(snd.get_play_count(world, n) for n in names)


def finish(inner, error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    counts = {}
    problems = [] if error is None else [error]
    if inner and not inner.get('success'):
        problems.append(f'the check it listened to failed: {inner.get("error") or inner.get("errors")}')
    for names in both_need:
        c, s = heard(client_world, names), heard(server_world, names)
        counts['|'.join(names)] = (c, s)
        if not (c > 0 and s > 0):
            problems.append(f'{"/".join(names)} started (client, server) {(c, s)}')
    for names in client_need:
        c = heard(client_world, names)
        counts['|'.join(names) + ' (client)'] = c
        if c <= 0:
            problems.append(f'{"/".join(names)} never started on the client')
    for key, least in levels_need.items():
        if seen[key] < least:
            problems.append(f'the client\'s {key} level reached only {seen[key]:.2f} (needs {least})')
    if 'creak' in levels_need and not seen['ship_loops']:
        problems.append('a ship\'s loops never played on the client')
    if 'cave' in levels_need and not seen['in_cave']:
        problems.append('the client was never under a cave roof')
    RESULT.write_text(json.dumps({
        'success': not problems, 'listened_to': NAME, 'its_checks': len(inner.get('checks', [])) if inner else 0,
        'errors': problems or None, 'counts': counts, 'loop_levels': {k: round(v, 2) if isinstance(v, float) else v for k, v in seen.items()},
        'client_total': snd.get_total_play_count(client_world), 'server_total': snd.get_total_play_count(server_world),
        'finished_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, indent=2), encoding='utf-8')
    unreal.log(f'EWPLAYCHECK AudioDuring {NAME} success={not problems} {problems}')


def tick(delta):
    try:
        watch()
        inner = None
        if INNER.exists() and INNER.stat().st_mtime >= started:
            try:
                inner = json.loads(INNER.read_text(encoding='utf-8'))
            except ValueError:
                return
        if inner and (inner.get('success') or inner.get('finished_utc') or inner.get('error') or inner.get('errors')):
            state['done_at'] = state['done_at'] or time.monotonic()
            if time.monotonic() - state['done_at'] >= AFTER:
                finish(inner)
    except Exception as error:
        finish(None, repr(error))


runpy.run_path(str(HERE / f'verify_{NAME}_play.py'))
state['handle'] = unreal.register_slate_post_tick_callback(tick)
