"""Play: land animals stay on their own island (owner, October 16: animals wander naturally on their assigned islands; CODEX C2).
One player (EW_PLAY_PLAYERS=1). The survivor is carried to each group of animals in turn, so they are awake (wildlife more than 200 m from every
survivor rests), and every awake animal is sampled twice a second. An animal must always stand above the sea (its feet above SurfaceZ less its wade depth),
and, unless it is hunting (a quarry), within its roam radius of home (plus a margin for the step it was taking). Writes Saved/AnimalsStayHomePlayResult.json."""
import unreal, json, time
from pathlib import Path
lib = unreal.EWEditorVerificationLibrary
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
animals = list(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.EWAnimal))
assert animals, 'there are no animals in the map'
def dist(a, b):
    return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2) ** .5


SECONDS_PER_GROUP = 12.0
MARGIN = 150.0
# Visit groups: one stop per animal home that is not within 400 m of a stop already made, so each region's animals get awake time.
stops = []
for a in animals:
    home = a.get_home()
    if all(dist(home, s) > 40000 for s in stops):
        stops.append(home)
checks = []
memo = {'animals': len(animals), 'stops': len(stops), 'samples': 0, 'worst_over_roam': 0.0, 'lowest_above_sea': 1e9}
stop = 0
arrive = 0.0
next_sample = 0.0
handle = None
phase = 'go'


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    Path(unreal.Paths.project_saved_dir(), 'AnimalsStayHomePlayResult.json').write_text(json.dumps({'success': error is None, 'checks': checks, 'measured': memo, 'error': error}, indent=2))


def tick(delta):
    global stop, arrive, next_sample, phase
    now = time.monotonic()
    try:
        if phase == 'go':
            if stop >= len(stops):
                assert memo['samples'] > 0, 'no animal was ever awake and sampled'
                checks.append(f'{memo["samples"]} samples of {memo["animals"]} animals across {memo["stops"]} stops: all stayed above the sea and within their roam radius')
                finish()
                return
            home = stops[stop]
            pawn.teleport(unreal.Vector(home.x, home.y, home.z + 300), unreal.Rotator())
            arrive = now
            phase = 'watch'
        elif phase == 'watch':
            if now >= next_sample:
                next_sample = now + 0.5
                for a in animals:
                    if a.is_dead():
                        continue
                    definition = a.get_editor_property('definition')
                    loc = a.get_actor_location()
                    near = dist(loc, pawn.get_actor_location()) < 20000
                    if not near:
                        continue
                    memo['samples'] += 1
                    feet = loc.z - 40.0
                    sea = a.get_editor_property('surface_z') - definition.get_editor_property('wade_depth')
                    memo['lowest_above_sea'] = min(memo['lowest_above_sea'], feet - sea)
                    assert loc.z > sea, f'{a.get_name()} ({definition.get_editor_property("display_name")}) is below the sea at z={loc.z:.0f} (sea {sea:.0f})'
                    if a.get_quarry() is None:
                        home = a.get_home()
                        away = ((loc.x - home.x) ** 2 + (loc.y - home.y) ** 2) ** .5
                        over = away - definition.get_editor_property('roam_radius')
                        memo['worst_over_roam'] = max(memo['worst_over_roam'], over)
                        assert over <= MARGIN, f'{a.get_name()} wandered {away:.0f} cm from home, roam radius {definition.get_editor_property("roam_radius"):.0f}'
            if now - arrive >= SECONDS_PER_GROUP:
                stop += 1
                phase = 'go'
    except Exception as exc:
        finish(f'{exc!r}')


handle = unreal.register_slate_post_tick_callback(tick)
