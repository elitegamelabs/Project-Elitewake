"""Diagnostic checkerboard icon fixtures only. No production art, unlocks or grants."""
import unreal
texture=unreal.load_asset('/Engine/EngineResources/DefaultTexture')
assert texture
folder='/Game/Elitewake/Items/Testing'
items=[]
for suffix,label in [('IconMaterial','Icon material (Test)'),('IconOutput','Icon output (Test)')]:
    name='DA_Test'+suffix
    item=unreal.load_asset(folder+'/'+name)
    if not item:
        factory=unreal.DataAssetFactory()
        factory.set_editor_property('data_asset_class',unreal.EWItemDefinition)
        item=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,folder,unreal.EWItemDefinition,factory)
        assert item
        item.set_editor_property('item_id','Test.'+suffix)
        item.set_editor_property('display_name',label)
        item.set_editor_property('description','Diagnostic icon fixture: shared engine checkerboard, temporary 1 kg weight; not a gameplay recipe.')
        item.set_editor_property('max_stack_size',250)
        item.set_editor_property('unit_weight',1.0)
        item.set_editor_property('icon',texture)
        assert unreal.EditorAssetLibrary.save_loaded_asset(item)
    items.append(item)
folder='/Game/Elitewake/Crafting/Testing'
name='DA_RecipeIconCheck'
if not unreal.EditorAssetLibrary.does_asset_exist(folder+'/'+name):
    factory=unreal.DataAssetFactory()
    factory.set_editor_property('data_asset_class',unreal.EWCraftingRecipe)
    recipe=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,folder,unreal.EWCraftingRecipe,factory)
    assert recipe
    cost=unreal.EWCraftingIngredient()
    cost.set_editor_property('item',items[0]);cost.set_editor_property('quantity',1)
    recipe.set_editor_property('ingredients',[cost]);recipe.set_editor_property('output',items[1])
    assert unreal.EditorAssetLibrary.save_loaded_asset(recipe)
