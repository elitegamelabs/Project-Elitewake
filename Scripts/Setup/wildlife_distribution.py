"""Pure-Python population rules for the canonical five-island world."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_layout as W  # noqa: E402


PER_ISLAND = {'Swamp': {'Alligator': 2, 'Cottonmouth': 2},
              'Jungle': {'SquirrelMonkey': 3, 'Tortoise': 1},
              'Desert': {'Tortoise': 2, 'Flamingo': 2, 'Pelican': 1},
              'Plains': {'Pelican': 2, 'Flamingo': 1},
              'Winter': {}}
STARTER = {'Pelican': 2, 'Flamingo': 2, 'Tortoise': 1, 'SquirrelMonkey': 2}
HABITAT = {'Alligator': 'low', 'Cottonmouth': 'low', 'SquirrelMonkey': 'trees', 'Tortoise': 'inland',
           'Flamingo': 'shore', 'Pelican': 'shore', 'Bear': 'inland', 'Lion': 'inland', 'GiantCrocodile': 'low',
           'Elephant': 'inland'}
# The five islands are about 2 km across: use the same species in larger numbers (tuning).
FIVE_ISLAND_DENSITY = 7
# The four approved large animals (counts per island are tuning, not scaled by the density above; the only Plains
# island is the starter, so its lion is placed 26 m or more from the spawn and dock by place_animals.py):
# bears in Winter, lions on the Plains, giant crocodiles in the Swamp, elephants in the Jungle (owner, October 16 correction).
LARGE_FIVE_ISLAND = {'Winter': {'Bear': 2}, 'Plains': {'Lion': 1}, 'Swamp': {'GiantCrocodile': 1}, 'Jungle': {'Elephant': 2}}


def target_counts(island):
    """The population plan for one of the five large islands."""
    base = STARTER if island.key == 'Starter' else PER_ISLAND[island.region]
    counts = {k: v * FIVE_ISLAND_DENSITY for k, v in base.items()}
    counts.update(LARGE_FIVE_ISLAND.get(island.region, {}))
    return counts


def missing_counts(island, existing_counts):
    """Population deficits only; running placement again must not duplicate existing animals."""
    return {kind: max(0, target - existing_counts.get(kind, 0))
            for kind, target in target_counts(island).items()}
