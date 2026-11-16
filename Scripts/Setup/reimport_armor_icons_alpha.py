"""Reimport only nine existing clothing textures; retain their asset paths and item/recipe references.
Export each resulting texture for an independent alpha-channel audit. Does not save maps or item definitions.
"""
import json
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.project_dir())
NAMES = ['ClothHeadWrap', 'ClothChest', 'ClothPants', 'FurHood', 'FurJacket', 'FurPants',
         'MetalTricornHelmet', 'MetalCuirass', 'MetalPants']
FOLDER = '/Game/Elitewake/UI/Icons/Armor'
OUT = Path(u.Paths.project_saved_dir(), 'ClothingIconAlpha')
OUT.mkdir(parents=True, exist_ok=True)
report = dict(success=False, icons=[], error=None)
try:
    assert not u.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    for name in NAMES:
        item = u.load_asset('/Game/Elitewake/Items/Armor/DA_' + name)
        before = str(item.get_editor_property('icon'))
        old_texture = u.load_asset(FOLDER + '/T_Icon_' + name)
        assert old_texture, name
        original_path = old_texture.get_path_name()
        task = u.AssetImportTask()
        for key, value in dict(filename=str(ROOT/'Art/UI/Icons/Armor'/('T_Icon_'+name+'.png')),
                               destination_path=FOLDER, automated=True, replace_existing=True, save=False).items():
            task.set_editor_property(key, value)
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        texture = u.load_asset(FOLDER + '/T_Icon_' + name)
        assert texture.get_path_name() == original_path
        texture.set_editor_property('lod_group', u.TextureGroup.TEXTUREGROUP_UI)
        texture.set_editor_property('compression_settings', u.TextureCompressionSettings.TC_EDITOR_ICON)
        texture.set_editor_property('compression_no_alpha', False)
        texture.set_editor_property('mip_gen_settings', u.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        texture.set_editor_property('max_texture_size', 256)
        assert u.EditorAssetLibrary.save_loaded_asset(texture)
        assert str(item.get_editor_property('icon')) == before
        export = u.AssetExportTask()
        for key, value in dict(object=texture, filename=str(OUT/('T_Icon_'+name+'.png')), automated=True,
                               prompt=False, replace_identical=True, exporter=u.TextureExporterPNG()).items():
            export.set_editor_property(key, value)
        assert u.Exporter.run_asset_export_task(export), name
        report['icons'].append(dict(name=name, texture=original_path, item_reference_unchanged=True,
                                    compression_no_alpha=texture.get_editor_property('compression_no_alpha'),
                                    maximum_size=texture.get_editor_property('max_texture_size')))
    report['success'] = True
except Exception as exc:
    report['error'] = repr(exc)
    raise
finally:
    (OUT/'ImportResult.json').write_text(json.dumps(report, indent=2))
    u.SystemLibrary.quit_editor()
