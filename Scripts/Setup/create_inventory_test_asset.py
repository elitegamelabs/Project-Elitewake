"""Run through Unreal's PythonScript commandlet to create the opt-in M5C fixture.

This uses Unreal asset APIs, never edits binary assets directly, and does not
overwrite an existing asset. Wood variants and production weight remain TBD.
"""
import unreal

ASSET_PATH = "/Game/Elitewake/Items/Testing/DA_TestWood"
if unreal.EditorAssetLibrary.does_asset_exist(ASSET_PATH):
    unreal.log("M5C fixture already exists; preserving existing content.")
else:
    item_class = unreal.load_class(None, "/Script/EW.EWItemDefinition")
    if item_class is None:
        raise RuntimeError("Build EWEditor before creating its native item asset.")
    factory = unreal.DataAssetFactory()
    factory.set_editor_property("data_asset_class", item_class)
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "DA_TestWood", "/Game/Elitewake/Items/Testing", item_class, factory
    )
    if asset is None:
        raise RuntimeError("Unreal could not create the M5C fixture.")
    asset.set_editor_property("item_id", "Test.Wood")
    asset.set_editor_property("display_name", "Wood (Test)")
    asset.set_editor_property("description", "Development fixture. Stack 250 follows the October Bible; 0.1 kg weight is temporary test tuning, not production wood balance.")
    category_enum = type(asset.get_editor_property("category"))
    asset.set_editor_property("category", category_enum.RESOURCE)
    asset.set_editor_property("max_stack_size", 250)
    asset.set_editor_property("unit_weight", 0.1)
    if not unreal.EditorAssetLibrary.save_loaded_asset(asset):
        raise RuntimeError("Unreal could not save the M5C fixture.")
    unreal.log("M5C persisted fixture saved: " + ASSET_PATH)
