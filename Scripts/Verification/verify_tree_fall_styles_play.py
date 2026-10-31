"""Each tree species falls in its own way (single-player Play session). Owner, October 27: different animations for the different
trees when they are cut down. Styles are placeholder tuning (TBD): Oak heavy and slow, Ash steady, Birch flexing, Spruce stiff,
Palm whipping side to side.
Picks one tree of each style the map has, fells all of them at once (server fell, direction +X) and samples how each comes down:
the time to lie down, the biggest sideways sway while falling, and the biggest bounce after landing. Checks that the style a tree
reports matches its species, and that the styles really differ in what is measured.
Writes Saved/TreeFallStylesPlayResult.json."""
import json
import time
from pathlib import Path
import unreal

lib = unreal.EWEditorVerificationLibrary
saved = Path(unreal.Paths.project_saved_dir())
world = lib.get_play_worlds()[0]
pc = unreal.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
tree_cls = unreal.load_class(None, '/Script/EW.EWHarvestTree')
species_prefix = {'Oak': 'Oak', 'Ash': 'Ash', 'Birch': 'Birch', 'Spruce': 'Spruce', 'Palm': 'Veyran Palm'}
picked = {}
for t in unreal.GameplayStatics.get_all_actors_of_class(world, tree_cls):
    style = str(t.get_fall_style_name())
    label = str(t.get_actor_label())
    if t.is_felled():
        continue
    want = species_prefix.get(style)
    if want and not label.startswith(want):
        continue            # the style comes from the mesh name: the label must agree
    if style in species_prefix and style not in picked:
        picked[style] = t
state = {'t0': time.monotonic() + 12, 'phase': 0, 'handle': None, 'samples': {k: [] for k in picked}, 'fell_at': None}
report = {'styles_found': sorted(picked), 'styles_missing': sorted(set(species_prefix) - set(picked)),
          'labels': {k: str(v.get_actor_label()) for k, v in picked.items()}}


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(state['handle'])
    report.update(success=error is None, error=error)
    (saved / 'TreeFallStylesPlayResult.json').write_text(json.dumps(report, indent=2))
    unreal.log(f'EWPLAYCHECK TreeFallStyles success={error is None} error={error}')


def tick(delta):
    now = time.monotonic()
    if now < state['t0']:
        return
    try:
        if state['phase'] == 0:
            assert len(picked) >= 3, f'need at least three species on the map, found {sorted(picked)}'
            for style, tree in picked.items():
                assert tree.get_actor_up_vector().z > .99, f'{style} not upright'
                assert tree.fell(unreal.Vector(1, 0, 0)), f'{style} would not fall'
            state['fell_at'] = now
            state['phase'] = 1
            return
        t = now - state['fell_at']
        for style, tree in picked.items():
            up = tree.get_actor_up_vector()
            state['samples'][style].append((t, up.x, up.y, up.z))
        if t < 9.0:
            return
        results = {}
        for style, s in state['samples'].items():
            first = next((i for i, x in enumerate(s) if x[3] < .03), None)      # almost down
            lying = s[first][0] if first is not None else None
            sway = max(abs(x[2]) for x in s)
            bounce = 0.0
            if first is not None:
                low = next((i for i in range(first, len(s)) if s[i][3] < .004), len(s) - 1)      # touchdown
                bounce = max(x[3] for x in s[low:])      # how far the trunk lifts again after touching down
            results[style] = {'seconds_to_lie_down': round(lying, 2) if lying is not None else None,
                              'max_sway_up_y': round(sway, 3), 'max_bounce_up_z': round(bounce, 3)}
        report['results'] = results
        for style, r in results.items():
            assert r['seconds_to_lie_down'] is not None, f'{style} never lay down'
            assert r['seconds_to_lie_down'] > 1.0, f'{style} fell too fast'
        # sway styles move sideways, stiff styles do not; heavier styles bounce more than stiff ones
        for style in ('Palm', 'Birch'):
            if style in results:
                assert results[style]['max_sway_up_y'] > .03, f'{style} should sway ({results[style]})'
        for style in ('Oak', 'Spruce'):
            if style in results:
                assert results[style]['max_sway_up_y'] < .01, f'{style} should not sway ({results[style]})'
        if 'Oak' in results:
            assert results['Oak']['max_bounce_up_z'] > .015, f'Oak should bounce on landing ({results["Oak"]})'
        if 'Oak' in results and 'Spruce' in results:
            assert results['Oak']['max_bounce_up_z'] > results['Spruce']['max_bounce_up_z'], 'Oak should bounce more than stiff Spruce'
        times = {round(r['seconds_to_lie_down'], 1) for r in results.values()}
        assert len(times) >= 2, 'every species took the same time to fall'
        finish()
    except Exception as error:
        finish(repr(error))


state['handle'] = unreal.register_slate_post_tick_callback(tick)
