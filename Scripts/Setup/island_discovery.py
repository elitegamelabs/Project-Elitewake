"""Island discovery data and per-player state, independent of Unreal runtime.

Stable keys match world_layout.py. The game/server adapter is responsible for
authoritative shoreline-entry detection, saving, networking, and the UI timer.
"""
from dataclasses import dataclass, field
from typing import Iterable

ISLAND_NAMES = {
    "Starter": "Hearthshore",
    "Plains2": "Oakheart Isle",
    "Plains3": "Mistwood Island",
    "Plains4": "Greenhaven",
    "Plains5": "Willowmere",
    "Plains6": "Suncrest Isle",
    "Winter1": "Frostfall Island",
    "Winter2": "Winterfang Isle",
    "Winter3": "Glacier's End",
    "Winter4": "Snowspire Island",
    "Winter5": "Icebound Reach",
    "Swamp1": "Mirehaven",
    "Swamp2": "Blackwater Isle",
    "Swamp3": "Reedshadow",
    "Swamp4": "Mossfen Island",
    "Swamp5": "Gloomwater Cay",
    "Desert1": "Golden Dunes",
    "Desert2": "Sunscorch Isle",
    "Desert3": "Mirage Point",
    "Desert4": "Amberwind Isle",
    "Desert5": "Dusthaven",
    "Jungle1": "Emerald Haven",
    "Jungle2": "Coralwind Cay",
    "Jungle3": "Vineheart Isle",
    "Jungle4": "Rainshadow Island",
    "Jungle5": "Verdant Reach",
}

ANNOUNCEMENT_SECONDS = 5.0


@dataclass
class IslandDiscovery:
    """One player's island discoveries; persist keys under the player's identity."""

    discovered: set[str] = field(default_factory=set)

    @classmethod
    def restore(cls, keys: Iterable[str]) -> "IslandDiscovery":
        """Reject unknown IDs instead of silently persisting corrupt world data."""
        saved = set(keys)
        unknown = saved - ISLAND_NAMES.keys()
        if unknown:
            raise ValueError(f"Unknown island keys in save: {sorted(unknown)}")
        return cls(saved)

    def discover(self, key: str) -> str | None:
        """Return announcement text exactly once; caller must be authoritative."""
        if key not in ISLAND_NAMES:
            raise KeyError(f"Unknown island key: {key}")
        if key in self.discovered:
            return None
        self.discovered.add(key)
        return ISLAND_NAMES[key]

    def map_label(self, key: str) -> str | None:
        """Undiscovered islands never expose their names on the map."""
        if key not in ISLAND_NAMES:
            raise KeyError(f"Unknown island key: {key}")
        return ISLAND_NAMES[key] if key in self.discovered else None

    def serialize(self) -> list[str]:
        return sorted(self.discovered)


def validate_world_keys(world_keys: Iterable[str]) -> None:
    """Ensure world generation and discovery catalogue stay in lockstep."""
    actual = list(world_keys)
    if len(actual) != len(set(actual)):
        raise ValueError("Duplicate island keys in world layout")
    missing = set(actual) - ISLAND_NAMES.keys()
    extra = ISLAND_NAMES.keys() - set(actual)
    if missing or extra:
        raise ValueError(f"Island catalogue mismatch: missing={sorted(missing)}, extra={sorted(extra)}")
    if len(set(ISLAND_NAMES.values())) != len(ISLAND_NAMES):
        raise ValueError("Island display names must be unique")
