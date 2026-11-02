"""The twenty-island plan (CLAUDE.md 5.7; owner-approved November 1): four islands per region, each worth visiting for its own
specialty, one village per region, and the wildlife that belongs there. Plain Python (no Unreal), the data the island
generators and checks read; checked by Scripts/Tests/test_world_islands.py. Many resources and species here do not exist yet
as items or assets: they are the plan, added during island production (species as realistic, rigged assets, Phase 5).

Keys keep the existing island keys where an island already exists (Starter, Winter1, Swamp1, Desert1, Jungle1).
"""

REGIONS = ('Plains', 'Winter', 'Swamp', 'Desert', 'Jungle')

# Every island has these within about 3 minutes' walk of a safe landing (CLAUDE.md 5.3).
BASICS = ('fresh water', 'wood', 'stone', 'fiber', 'food', 'hide or meat')

# Species allowed in each region (CLAUDE.md 5.6): nothing appears outside its region.
REGION_SPECIES = {
    'Plains': {'Boar', 'Hare', 'Pelican', 'Flamingo', 'Deer', 'Lion', 'WildHorse', 'WadingBird', 'Wolf'},
    'Winter': {'MountainGoat', 'Bear', 'Caribou', 'Hare', 'Fox', 'Wolf', 'Eagle', 'Seal', 'Walrus', 'PolarBear'},
    'Swamp': {'Heron', 'Turtle', 'Otter', 'Cottonmouth', 'Alligator', 'Boar', 'GiantCrocodile', 'Snake', 'Spider', 'Frog', 'Crocodile'},
    'Desert': {'Gazelle', 'Tortoise', 'Flamingo', 'Scorpion', 'Snake', 'Vulture', 'Pelican', 'Jackal', 'Oryx'},
    'Jungle': {'SquirrelMonkey', 'Parrot', 'Tapir', 'Jaguar', 'Snake', 'Monkey', 'Tortoise', 'Elephant', 'Boar'},
}


def _island(region, name, specialty, wildlife, village=False):
    return {'region': region, 'name': name, 'specialty': tuple(specialty), 'wildlife': tuple(wildlife), 'village': village}


ISLANDS = {
    'Starter': _island('Plains', 'P1 Starter', ('oak', 'flint', 'berries', 'spring pond'), ('Boar', 'Hare', 'Pelican', 'Flamingo'), village=True),
    'Plains2': _island('Plains', 'P2 Copper Downs', ('copper ore', 'iron ore', 'limestone'), ('Boar', 'Deer', 'Lion')),
    'Plains3': _island('Plains', 'P3 Clay Shore', ('clay', 'sand', 'herbs'), ('Deer', 'WildHorse', 'WadingBird')),
    'Plains4': _island('Plains', 'P4 Oak Heights', ('ship timber', 'herbs', 'hides'), ('Deer', 'Boar', 'Wolf')),
    'Winter1': _island('Winter', 'W1 Coal Spine', ('coal',), ('MountainGoat', 'Bear')),
    'Winter2': _island('Winter', 'W2 Birch Haven', ('birch', 'furs'), ('Caribou', 'Hare', 'Fox'), village=True),
    'Winter3': _island('Winter', 'W3 Iron Cliffs', ('iron ore', 'building stone', 'emerald'), ('Wolf', 'Eagle')),
    'Winter4': _island('Winter', 'W4 Ice Reach', ('ice', 'fine furs', 'emerald caves'), ('Seal', 'Walrus', 'PolarBear')),
    'Swamp1': _island('Swamp', 'S1 River Isle', ('coast-to-coast river', 'spruce', 'reeds'), ('Heron', 'Turtle', 'Otter', 'Cottonmouth'), village=True),
    'Swamp2': _island('Swamp', 'S2 Bog Fen', ('bog iron', 'peat'), ('Alligator', 'Boar')),
    'Swamp3': _island('Swamp', 'S3 Resin Woods', ('resin', 'pitch'), ('GiantCrocodile', 'Snake')),
    'Swamp4': _island('Swamp', 'S4 Mushroom Hollows', ('mushrooms', 'medicinal herbs', 'dark gems'), ('Spider', 'Frog', 'Crocodile')),
    'Desert1': _island('Desert', 'D1 Oasis Isle', ('oasis spring', 'dates', 'coconuts'), ('Gazelle', 'Tortoise', 'Flamingo'), village=True),
    'Desert2': _island('Desert', 'D2 Sulfur Flats', ('sulfur ore',), ('Scorpion', 'Snake', 'Vulture')),
    'Desert3': _island('Desert', 'D3 Salt Pans', ('salt', 'sandstone'), ('Flamingo', 'Pelican', 'Jackal')),
    'Desert4': _island('Desert', 'D4 Copper Canyon', ('copper ore', 'iron ore', 'amber'), ('Snake', 'Tortoise', 'Oryx')),
    'Jungle1': _island('Jungle', 'J1 Waterfall Basin', ('waterfalls', 'fruit'), ('SquirrelMonkey', 'Parrot', 'Tapir'), village=True),
    'Jungle2': _island('Jungle', 'J2 Gem Ridge', ('green gems', 'copper ore'), ('Jaguar', 'Snake')),
    'Jungle3': _island('Jungle', 'J3 Spice Isle', ('exotic plants', 'spice herbs', 'trade fruit'), ('Monkey', 'Tortoise', 'Parrot')),
    'Jungle4': _island('Jungle', 'J4 Vine Woods', ('ash timber', 'vines', 'rope fiber'), ('Elephant', 'Boar')),
}

# Saltreach is the Plains village; the other regions' villages are new.
VILLAGES = {region: next(k for k, i in ISLANDS.items() if i['region'] == region and i['village']) for region in REGIONS}

# Wildlife keeps clear of people (CLAUDE.md 5.6), metres from safe landings and villages.
CLEAR_OF_PEOPLE_M = {'passive': 150, 'aggressive': 250}
# No 200 m square holds more than this share of an island's animals.
MAX_SHARE_PER_200M = .15
# A walk across each island, minutes, preferably in every direction (owner, November 1; replaces 15-20 and 30-45).
CROSSING_MINUTES = (6, 17)
# Inland water depths at the deepest point (owner, November 1, in feet: ponds 15 ft, lakes 50 ft).
POND_DEPTH_CM = 457.0
LAKE_DEPTH_CM = 1524.0
