"""Writes Content/Elitewake/Data/BuildZones.json from world_buildzones.py (run with plain Python, no editor needed)."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import world_buildzones as B  # noqa: E402

target = HERE.parents[1] / 'Content' / 'Elitewake' / 'Data' / 'BuildZones.json'
print(f'{B.export(target)} zones -> {target}')
