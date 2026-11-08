"""The sextant (FUTURE_IMPLEMENTATIONS Part 8, 09; November 8). Safe to run again; the map is not touched. In the editor,
outside Play (EW_QUIT_WHEN_DONE=1 closes it at the end):
    UnrealEditor.exe EW.uproject -SCCProvider=None -ExecCmds="py <this file>"
  DA_Sextant (Items/Tools): held in the main hand, it reads the latitude on the HUD (EWNorth::LatitudeAt). 1.2 kg; a Port's
  resource trader pays 60 Copper.
  DA_RecipeSextant (Crafting/Testing): 3 Copper Ingot, 1 Iron Ingot and 1 Wood at a lit fire, 10 s; the Metalwork skill
  unlocks it (EWSkillTree.cpp). Numbers are tuning.
  Icon: Art/UI/Icons/Tools/T_Icon_Sextant.png (Scripts/Art/draw_sextant_icon.py). Writes Saved/SextantResult.json.
"""
import json
import os
from pathlib import Path
import unreal

ITEMS = '/Game/Elitewake/Items'


def data_asset(folder, name, cls):
    asset = unreal.load_asset(f'{folder}/{name}')
    if not asset:
        factory = unreal.DataAssetFactory()
        factory.set_editor_property('data_asset_class', cls)
        asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, cls, factory)
    return asset


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    task = unreal.AssetImportTask()
    task.set_editor_property('filename', str(Path(unreal.Paths.project_dir(), 'Art/UI/Icons/Tools/T_Icon_Sextant.png')))
    task.set_editor_property('destination_path', '/Game/Elitewake/UI/Icons/Tools')
    task.set_editor_property('replace_existing', True)
    task.set_editor_property('automated', True)
    task.set_editor_property('save', True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    sextant = data_asset(f'{ITEMS}/Tools', 'DA_Sextant', unreal.EWItemDefinition)
    for k, v in {'item_id': 'Sextant', 'display_name': 'Sextant',
                 'description': 'A brass sextant. Hold it and sight the horizon: it gives your latitude, how far north you are.',
                 'category': unreal.EWItemCategory.TOOL, 'max_stack_size': 1, 'unit_weight': 1.2, 'sell_value_copper': 60,
                 'equipment_slot': unreal.EWEquipmentSlot.MAIN_HAND, 'sextant': True,
                 'icon': unreal.load_asset('/Game/Elitewake/UI/Icons/Tools/T_Icon_Sextant')}.items():
        sextant.set_editor_property(k, v)
    assert unreal.EditorAssetLibrary.save_loaded_asset(sextant)
    recipe = data_asset('/Game/Elitewake/Crafting/Testing', 'DA_RecipeSextant', unreal.EWCraftingRecipe)
    parts = []
    for path, n in (('Resources/DA_CopperIngot', 3), ('Resources/DA_IronIngot', 1), ('Testing/DA_TestWood', 1)):
        part = unreal.EWCraftingIngredient()
        part.set_editor_property('item', unreal.load_asset(f'{ITEMS}/{path}'))
        part.set_editor_property('quantity', n)
        parts.append(part)
    recipe.set_editor_property('ingredients', parts)
    recipe.set_editor_property('output', sextant)
    recipe.set_editor_property('craft_seconds', 10.0)
    recipe.set_editor_property('needs_fire', True)
    assert unreal.EditorAssetLibrary.save_loaded_asset(recipe)
    Path(unreal.Paths.project_saved_dir(), 'SextantResult.json').write_text(json.dumps({'success': True}))
    unreal.log('EWSEXTANT done')


if __name__ == '__main__':
    try:
        main()
    finally:
        if os.environ.get('EW_QUIT_WHEN_DONE') == '1':
            unreal.SystemLibrary.quit_editor()
