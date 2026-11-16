"""Slice 3: create only the two approved new wearable items, recipes and icons.

Does not touch maps, existing items, recipes, player saves or other artwork.
Run outside Play; EW_QUIT_WHEN_DONE=1 closes the editor afterwards.
"""
import json
import os
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.project_dir())
ITEMS = '/Game/Elitewake/Items/Armor'
RECIPES = '/Game/Elitewake/Crafting/Testing'
ART = '/Game/Elitewake/UI/Icons/Equipment'


def asset(folder, name, cls):
    found = u.load_asset(folder + '/' + name)
    if found:
        assert isinstance(found, cls), name
        return found
    factory = u.DataAssetFactory()
    factory.set_editor_property('data_asset_class', cls)
    return u.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, cls, factory)


def main():
    assert not u.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    created = []
    for suffix, title, slot, weight, description, costs, seconds in (
        ('LeatherSeaBoots', 'Leather Sea Boots', u.EWEquipmentSlot.FEET, 1.4,
         'Stitched leather sea boots. Separate footwear with modest protection and warmth; worn weight still counts.',
         [('Resources/DA_Leather', 4), ('Testing/DA_TestFiber', 4)], 8.0),
        ('LeatherWristCuff', 'Leather Wrist Cuff', u.EWEquipmentSlot.ACCESSORY, .1,
         'A stitched leather wrist cuff. A cosmetic accessory with no attribute bonus; worn weight still counts.',
         [('Resources/DA_Leather', 2), ('Testing/DA_TestFiber', 2)], 6.0),
    ):
        task = u.AssetImportTask()
        task.set_editor_property('filename', str(ROOT / 'Art/UI/Icons/Equipment' / ('T_Icon_' + suffix + '.png')))
        task.set_editor_property('destination_path', ART)
        task.set_editor_property('automated', True)
        task.set_editor_property('replace_existing', True)
        task.set_editor_property('save', True)
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        icon = u.load_asset(ART + '/T_Icon_' + suffix)
        assert icon
        icon.set_editor_property('lod_group', u.TextureGroup.TEXTUREGROUP_UI)
        icon.set_editor_property('compression_settings', u.TextureCompressionSettings.TC_EDITOR_ICON)
        icon.set_editor_property('mip_gen_settings', u.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        icon.set_editor_property('max_texture_size', 256)
        assert u.EditorAssetLibrary.save_loaded_asset(icon)
        item = asset(ITEMS, 'DA_' + suffix, u.EWItemDefinition)
        for key, value in dict(item_id=suffix, display_name=title, description=description,
                               category=u.EWItemCategory.CLOTHING, max_stack_size=1, unit_weight=weight,
                               equipment_slot=slot, icon=icon, sell_value_copper=0,
                               armor_kind=u.EWArmorKind.CLOTH if slot == u.EWEquipmentSlot.FEET else u.EWArmorKind.NONE,
                               armor_reduction=.01 if slot == u.EWEquipmentSlot.FEET else 0.,
                               insulation=.05 if slot == u.EWEquipmentSlot.FEET else 0.,
                               overheat_penalty=.01 if slot == u.EWEquipmentSlot.FEET else 0.).items():
            item.set_editor_property(key, value)
        if slot == u.EWEquipmentSlot.ACCESSORY:
            material_path = ART + '/MI_LeatherWristCuff'
            material = u.load_asset(material_path)
            if not material:
                material = u.AssetToolsHelpers.get_asset_tools().create_asset('MI_LeatherWristCuff', ART,
                           u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
            u.MaterialEditingLibrary.set_material_instance_parent(material, u.load_asset('/Engine/BasicShapes/BasicShapeMaterial'))
            u.MaterialEditingLibrary.set_material_instance_vector_parameter_value(material, 'Color', u.LinearColor(.16, .08, .035, 1))
            assert u.EditorAssetLibrary.save_loaded_asset(material)
            part = u.EWWornMeshPart()
            part.set_editor_property('mesh', u.load_asset('/Engine/BasicShapes/Cylinder'))
            part.set_editor_property('bone', 'hand_l')
            part.set_editor_property('material', material)
            part.set_editor_property('relative_transform', u.Transform(location=u.Vector(-2, 0, 0),
                                    rotation=u.Rotator(pitch=90), scale=u.Vector(.09, .07, .045)))
            item.set_editor_property('worn_meshes', [part])
        assert u.EditorAssetLibrary.save_loaded_asset(item)
        recipe = asset(RECIPES, 'DA_Recipe' + suffix, u.EWCraftingRecipe)
        parts = []
        for path, count in costs:
            ingredient = u.EWCraftingIngredient()
            material = u.load_asset('/Game/Elitewake/Items/' + path)
            assert material, path
            ingredient.set_editor_property('item', material)
            ingredient.set_editor_property('quantity', count)
            parts.append(ingredient)
        recipe.set_editor_property('ingredients', parts)
        recipe.set_editor_property('output', item)
        recipe.set_editor_property('craft_seconds', seconds)
        recipe.set_editor_property('needs_fire', False)
        assert u.EditorAssetLibrary.save_loaded_asset(recipe)
        created.append(dict(item=item.get_path_name(), recipe=recipe.get_path_name(), icon=icon.get_path_name()))
    Path(u.Paths.project_saved_dir(), 'InventorySlice3Assets.json').write_text(json.dumps(dict(success=True, assets=created), indent=2))


try:
    main()
finally:
    if os.environ.get('EW_QUIT_WHEN_DONE') == '1':
        u.SystemLibrary.quit_editor()
