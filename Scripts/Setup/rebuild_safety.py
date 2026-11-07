"""Small, pure-Python safety checks for the large world rebuild."""

import shutil
from pathlib import Path


PACKAGE_TAG = b'\xc1\x83\x2a\x9e'
GIB = 1024 ** 3
MIN_FREE_GIB = 120


def check_map_and_space(map_file, minimum_free_gib=MIN_FREE_GIB):
    """Fail before another step when a map save is invalid or space is too low."""
    map_file = Path(map_file)
    free = shutil.disk_usage(map_file.parent).free
    minimum = minimum_free_gib * GIB
    if free < minimum:
        raise RuntimeError(
            f'World rebuild stopped: {free / GIB:.1f} GiB free on the map drive; '
            f'at least {minimum_free_gib} GiB is required before another step'
        )
    if map_file.exists():
        with map_file.open('rb') as source:
            if source.seek(0, 2) < 4:
                raise RuntimeError(f'World rebuild stopped: map package is incomplete: {map_file}')
            source.seek(-4, 2)
            if source.read(4) != PACKAGE_TAG:
                raise RuntimeError(f'World rebuild stopped: map package is incomplete: {map_file}')
    return free
