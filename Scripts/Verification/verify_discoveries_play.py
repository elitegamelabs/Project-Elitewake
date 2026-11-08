"""Play: the Captain's discovery journal (FUTURE_IMPLEMENTATIONS Part 8, 63; November 7). Listen server plus one client:
    Scripts/Verification/run_play_check_once.ps1 -Check verify_discoveries_play.py -Result DiscoveriesPlayResult.json -Players 2 -Kit 1
The client's survivor is moved by the server (as any check does) and everything is read on the client's own screen.
  1. The client starts on the Starter Isle: it is discovered, on the client too.
  2. Copper Downs: reaching it discovers it, the client's HUD announces it, experience rises.
  3. Over the West Reef in the open sea: discovered and announced.
  4. Close to a living animal: its kind is noted as a creature.
  5. The client's Journal lists a Discoveries summary and a page for each discovery.
  6. Saved and put back: the save holds every discovery; restoring announces none of them again.
Writes Saved/DiscoveriesPlayResult.json.
"""
import json
import math
import sys
import time
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(unreal.Paths.project_dir(), 'Scripts', 'Setup')))
import world_layout as W  # noqa: E402
import world_reefs as R  # noqa: E402
import world_terrain as T  # noqa: E402

lib = unreal.EWEditorVerificationLibrary
RESULT = Path(unreal.Paths.project_saved_dir(), 'DiscoveriesPlayResult.json')
SHOTS = Path(unreal.Paths.project_saved_dir(), 'Screenshots', 'Discoveries')
SHOTS.mkdir(parents=True, exist_ok=True)
SLOT = 'DiscoveryTest'
worlds = lib.get_play_worlds()
assert len(worlds) == 2, 'Start Play as a listen server plus one client.'
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
host = next(c for c in pcs if c.has_authority())
server_world = worlds[pcs.index(host)]
client_world = worlds[pcs.index(client)]


def player_id(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


pawn = client.get_controlled_pawn()
owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if player_id(p) == player_id(pawn))
owner_pc = owner.get_controller()
settings = unreal.get_default_object(unreal.load_class(None, '/Script/UnrealEd.EditorPerformanceSettings'))
settings.set_editor_property('bThrottleCPUWhenNotForeground', False)
report = {'checks': []}
state = {'phase': 0, 'at': time.monotonic() + 4, 'handle': None, 'banners': []}


def check(label, ok, **values):
    report['checks'].append({'label': label, 'ok': bool(ok), **{k: str(v) for k, v in values.items()}})
    assert ok, f'{label}: {values}'


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error, finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    RESULT.write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK Discoveries success={error is None} error={error}')


def ids(pc):
    return [str(d.get_editor_property('id')) for d in pc.get_discoveries().get_discoveries()]


def hud():
    return next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(client_world, unreal.EWSurvivalWidget, False)
                if w.get_owning_player() == client)


def experience():
    p = owner.get_progression_component()
    return p.get_level() * 100000 + p.get_experience()


def inland(key, depth=2500.0):
    i = W.island(key)
    for k in range(24):
        a = 2 * math.pi * k / 24
        r = i.radius(a) - depth
        x, y = i.cx + r * math.cos(a), i.cy + r * math.sin(a)
        z = T.height(x, y)
        if z > T.SEA + 100:
            return unreal.Vector(x, y, z + 150)
    return unreal.Vector(i.cx, i.cy, T.height(i.cx, i.cy) + 150)


def move(to):
    owner.teleport(to, unreal.Rotator())


def watch_banner():
    shown = str(hud().get_displayed_discovery())
    if shown and (not state['banners'] or state['banners'][-1] != shown):
        state['banners'].append(shown)


def shot(name):
    unreal.SystemLibrary.execute_console_command(client_world, f'HighResShot 1920x1080 filename="{SHOTS / name}"')


def tick(_):
    try:
        watch_banner()
    except StopIteration:
        pass
    if time.monotonic() < state['at']:
        return
    try:
        p = state['phase']
        if p == 0:
            check('client discovered the Starter Isle', 'Starter' in ids(client), client=ids(client))
            report['host'] = ids(host)
            state['xp'] = experience()
            move(inland('Plains2'))
            state.update(phase=1, at=time.monotonic() + 3)
        elif p == 1:
            check('Copper Downs discovered on the client', 'Plains2' in ids(client), client=ids(client))
            check('experience rose', experience() > state['xp'], before=state['xp'], after=experience())
            shot('CopperDowns.png')
            reef = next(r for r in R.REEFS if r.key == 'Ocean1')
            move(unreal.Vector(reef.cx, reef.cy, T.SEA + 30))
            state.update(phase=2, at=time.monotonic() + 7)
        elif p == 2:
            check('West Reef discovered on the client', 'Ocean1' in ids(client), client=ids(client))
            animals = [a for a in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWAnimal)
                       if not a.is_dead() and a.get_editor_property('definition')]
            known = set(ids(owner_pc))
            animal = next(a for a in animals if a.get_editor_property('definition').get_name() not in known)
            state['creature'] = animal.get_editor_property('definition').get_name()
            at = animal.get_actor_location()
            move(unreal.Vector(at.x + 900, at.y, at.z + 200))
            state.update(phase=3, at=time.monotonic() + 3)
        elif p == 3:
            check('a creature kind noted', state['creature'] in ids(client), creature=state['creature'], client=ids(client))
            kinds = [d.get_editor_property('kind') for d in client.get_discoveries().get_discoveries()]
            check('it is a creature', unreal.EWPlaceKind.CREATURE in kinds)
            client.set_inventory_open(True)
            state.update(phase=4, at=time.monotonic() + 1)
        elif p == 4:
            menu = next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(client_world, unreal.EWInventoryWidget, False)
                        if w.get_owning_player() == client and w.is_in_viewport())
            menu.open_section(4)
            journal = menu.get_journal_panel()
            journal.refresh_discoveries()
            titles = [str(t) for t in journal.get_page_titles()]
            report['journal'] = titles
            check('the Journal has the summary page', 'The voyage so far' in titles, titles=titles)
            for name in ('Starter Isle', 'Copper Downs', 'West Reef'):
                check(f'the Journal has a page for {name}', name in titles, titles=titles)
            journal.show_page(titles.index('Copper Downs'))
            shot('Journal.png')
            state.update(phase=5, at=time.monotonic() + 1.5)
        elif p == 5:
            client.set_inventory_open(False)
            move(inland('Starter', 4000))
            state.update(phase=6, at=time.monotonic() + 2)
        elif p == 6:
            before = ids(owner_pc)
            check('saved', unreal.EWSurvivorSave.save_survivor(owner, SLOT, False))
            save = unreal.EWSurvivorSave.load_save(SLOT)
            saved = [str(d.get_editor_property('id')) for d in save.get_editor_property('discoveries')]
            check('the save holds every discovery', saved == before, saved=saved, before=before)
            state['announced'] = client.get_discoveries().get_announced_count()
            check('put back', save.apply_to(owner))
            state.update(phase=7, at=time.monotonic() + 3)
        elif p == 7:
            check('restored list unchanged on the client', ids(client) == ids(owner_pc), client=ids(client), server=ids(owner_pc))
            state.update(phase=8, at=time.monotonic(), until=time.monotonic() + 45)
        else:
            # The HUD shows one discovery at a time, about four seconds each: wait for the queue to reach these.
            wanted = ('Copper Downs', 'West Reef')
            if not all(n in state['banners'] for n in wanted) and time.monotonic() < state['until']:
                return
            for name in wanted:
                check(f'the HUD announced {name}', name in state['banners'], banners=state['banners'])
            after = client.get_discoveries().get_announced_count()
            count = len(ids(client))
            check('nothing announced again after restoring', after <= count, announced=after, discoveries=count)
            report['banners'] = state['banners']
            finish()
    except Exception as error:      # noqa: BLE001
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
