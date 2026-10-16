# ELITEWAKE Tool, Craftable, and Placeable Item Turnaround Requirements
Date: 2026-10-15
Status: Requested production requirement

## Scope
Create six-view directional reference images for every existing tool, craftable item, and placeable item that needs a 3D model:
- Front
- Back
- Left side
- Right side
- Top
- Underside/bottom

Use the current repository's canonical asset/item catalog. Do not invent missing item definitions. Keep each item's views consistent in scale, proportions, materials, colors, and identifying details. Prefer high-resolution individual sheets per asset or clearly labeled sheets grouped by sensible asset category.

## Preserve current UI pictures
Do not replace, edit, regenerate, recolor, crop, or otherwise change the existing item pictures/icons shown in the inventory or crafting menu. Those pictures must remain exactly as they are. New directional sheets are additional modeling references only; store them separately and do not substitute them for runtime inventory/crafting icons.

## Placeable item coverage
Include all placeable items listed in the project, such as buildable structures, crafting stations, storage, decorative objects, and other deployable/placeable assets where applicable. Capture the whole object from all six directions, including bases, undersides, attachment points, and relevant assembly details.

## Production tracking
Track each asset separately:
1. Six directional reference views complete.
2. 3D model created.
3. Materials/textures created.
4. Rigging completed where applicable.
5. Animations created where applicable.
6. Imported and integrated into Unreal Engine 5.8.
7. Verified in-game.

Do not mark a model, animation, or Unreal integration complete merely because reference images exist. Keep this work scoped to tools, craftable items, and placeable items; do not modify unrelated assets or systems.

## Suggested organization
- `Art/Tools/Turnarounds/`
- `Art/CraftableItems/Turnarounds/`
- `Art/PlaceableItems/Turnarounds/`

Organize by existing canonical asset names. Preserve existing UI icon/image files and their paths.

## Acceptance criteria
- Every in-scope tool, craftable item, and placeable item has six labeled views, including top and underside.
- Existing inventory and crafting-menu item pictures are unchanged.
- Reference images are separate from finished 3D models and runtime UI icons.
- The manifest honestly records missing views, models, textures, rigs, animations, and Unreal integration.
