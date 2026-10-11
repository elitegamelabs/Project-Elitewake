# Placeholder item icons

Temporary inventory icons generated with ChatGPT image generation for Elitewake's test items. Each is a 1254 × 1254 RGBA PNG with a transparent background. They are 2D stand-ins, not final art or 3D models.

| Source | Unreal texture | Item |
| --- | --- | --- |
| `Axe-v1.png` | `/Game/Elitewake/UI/PlaceholderIcons/T_Axe_v1` | Wooden Axe |
| `Shovel-v1.png` | `/Game/Elitewake/UI/PlaceholderIcons/T_Shovel_v1` | Wooden Shovel |
| `Pickaxe-v1.png` | `/Game/Elitewake/UI/PlaceholderIcons/T_Pickaxe_v1` | Wooden Pickaxe |
| `Flask-v1.png` | `/Game/Elitewake/UI/PlaceholderIcons/T_Flask_v1` | Hide Water Flask |
| `Torch-v1.png` | `/Game/Elitewake/UI/PlaceholderIcons/T_Torch_v1` | Inn Torch |
| `RepairKit-v1.png` | not imported yet | Repair Kit |

`generation.json` records each image's exact prompt and SHA-256 hash. The shared prompt direction: one complete item, a readable silhouette, semi-realistic hand-painted weathered wood, cord or hide, with no text, frame, scenery or modern parts.

To import and assign: create the Repair Kit assets first with `Scripts/Setup/create_prologue_repair_recipe.py`, then run `Scripts/Setup/import_placeholder_item_art.py` from the editor's Python console. The importer leaves existing textures alone and grants no items or recipes.

Final art gets a new version number or path. Do not overwrite these files.
