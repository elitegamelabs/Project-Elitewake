"""Pure-Python population rules for the twenty-island world (CLAUDE.md 5.6 and 5.7; owner, November 1).

Each island carries its own planned mix (world_islands.ISLANDS[key]['wildlife']), so the islands of a region differ and every
species stays in its region. Only species that exist in the game today are placed (EXISTING); the others arrive later as
realistic, rigged assets (Phase 5) and join their islands then. Counts are a placement plan, not a cap on wild animals.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_layout as W  # noqa: E402
from world_islands import ISLANDS as PLAN, REGION_SPECIES  # noqa: E402

# The animals built today (Content/Elitewake/Wildlife/Animals/DA_Animal_*). Spiders are placed by add_spiders.py.
EXISTING = {'Alligator', 'Bear', 'Boar', 'Cottonmouth', 'Elephant', 'Flamingo', 'GiantCrocodile', 'Lion', 'Pelican',
            'SquirrelMonkey', 'Tortoise',
            # November 6: so every island carries wildlife (build_animals.NEW_SPECIES)
            'Deer', 'Caribou', 'Wolf', 'Hare', 'Snake', 'PolarBear', 'Crocodile'}
# How many of each species an island carries (tuning): herds, prides and flocks at a believable size for about 2.5 km2.
PER_SPECIES = {'Alligator': 10, 'Bear': 3, 'Boar': 8, 'Cottonmouth': 10, 'Elephant': 6, 'Flamingo': 10, 'GiantCrocodile': 1,
               'Lion': 4, 'Pelican': 10, 'SquirrelMonkey': 16, 'Tortoise': 8,
               'Deer': 12, 'Caribou': 12, 'Wolf': 5, 'Hare': 10, 'Snake': 8, 'PolarBear': 3, 'Crocodile': 4}
HABITAT = {'Alligator': 'low', 'Cottonmouth': 'low', 'SquirrelMonkey': 'trees', 'Tortoise': 'inland',
           'Flamingo': 'shore', 'Pelican': 'shore', 'Bear': 'inland', 'Lion': 'inland', 'GiantCrocodile': 'low',
           'Elephant': 'inland', 'Boar': 'inland',
           'Deer': 'inland', 'Caribou': 'inland', 'Wolf': 'inland', 'Hare': 'inland', 'Snake': 'inland', 'PolarBear': 'inland',
           'Crocodile': 'low'}
# Wildlife keeps clear of people (CLAUDE.md 5.6): cm from safe landings and villages.
CLEAR_PASSIVE, CLEAR_AGGRESSIVE = 15000.0, 25000.0


def target_counts(island):
    """The placement plan for one island: its planned species that exist today, each at its usual number."""
    planned = PLAN[island.key]['wildlife']
    assert set(planned) <= REGION_SPECIES[island.region], f'{island.key} plans species from outside its region'
    return {kind: PER_SPECIES[kind] for kind in planned if kind in EXISTING and kind != 'Spider'}


def missing_counts(island, existing_counts):
    """Population deficits only; running placement again must not duplicate existing animals."""
    return {kind: max(0, target - existing_counts.get(kind, 0))
            for kind, target in target_counts(island).items()}
