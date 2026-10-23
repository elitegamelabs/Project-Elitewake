"""Pure-Python population rules shared by world setup and offline migration tests."""
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
           'Flamingo': 'shore', 'Pelican': 'shore'}
LEGACY_ISLAND_KEYS = frozenset(i.key for i in W.generate_legacy())


# The five-island world's islands are about 2 km across, several times the area of the old ones: the same species in larger numbers (tuning).
FIVE_ISLAND_DENSITY = 7


def target_counts(island):
    """The population plan for one island (scaled up on the five-island world's larger islands)."""
    base = STARTER if island.key == 'Starter' else PER_ISLAND[island.region]
    return {k: v * FIVE_ISLAND_DENSITY for k, v in base.items()} if W.FIVE_ISLAND_WORLD else base


def missing_counts(island, existing_counts):
    """Population deficits only; running placement again must not duplicate existing animals."""
    return {kind: max(0, target - existing_counts.get(kind, 0))
            for kind, target in target_counts(island).items()}


def expansion_islands(islands=None, existing_added_keys=()):
    """Return only new layout islands not already populated; never target the original 26."""
    islands = W.ISLANDS if islands is None else islands
    if W.FIVE_ISLAND_WORLD:
        return list(islands)          # the whole world is new: every island is populated afresh
    existing_added_keys = set(existing_added_keys)
    return [island for island in islands
            if island.key not in LEGACY_ISLAND_KEYS and island.key not in existing_added_keys]
