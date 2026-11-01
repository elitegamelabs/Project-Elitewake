"""Build the campfire and the first cooked dish (CLAUDE.md Phase 1, slice 3: minutes 10-15). Safe to run again.
Run in the editor outside Play, after build_first_resources.py (Source/EW/World/EWCampfire is the fire itself):
    UnrealEditor-Cmd.exe EW.uproject -unattended -nosplash -run=pythonscript -script=<this file>

  - SM_Campfire_v1: a ring of rough limestone round crossed oak logs on a bed of ash, about 1.1 m across; the fire's look, its
    placement ghost and (small) the item in hand.
  - DA_Campfire (Items/Building): carried, held in the main hand, laid with Left Mouse / the right trigger where its ghost shows
    blue (UEWItemDefinition::PlacedActor); icon Art/Items/Icons/Campfire-v1.png (Scripts/Art/make_campfire_icon.py).
  - DA_RecipeCampfire: 5 wood and 3 stones, 5 s. DA_RecipeCookedBerryDish: 3 Azren berries, 6 s, by a lit fire.
    The cooked fish and meat recipes need a lit fire too (the Torchbearer star's "a fire to cook by").
  - S_CampfireLoop_v1: the crackle (Scripts/Art/make_fire_sound.py), heard within about 15 m (import_audio.py, SA_Close_v1).
A survivor arriving on the Plains knows both new recipes (UEWArrivalComponent::FirstRecipes). Every amount is tuning.
"""
import json
import math
import random
import sys
from pathlib import Path
import unreal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import import_audio  # noqa: E402
from build_held_tools import GRIP  # noqa: E402
from ship_geometry import TIMBER_MATERIAL, Builder, make_timber_material, write_static_mesh  # noqa: E402

ROOT = Path(unreal.Paths.project_dir()).resolve()
MESHES = '/Game/Elitewake/World/Campfire'
ITEMS = '/Game/Elitewake/Items'
RECIPES = '/Game/Elitewake/Crafting/Testing'
ICONS = '/Game/Elitewake/UI/ItemIcons'
LIMESTONE = '/Game/Elitewake/World/Arrival/M_SpringStone_v1'
CAMPFIRE_COST = [('Testing/DA_TestWood', 5), ('Testing/DA_TestStone', 3)]
BERRY_DISH_COST = [('Testing/DA_TestAzulBerry', 3)]


def ring_mesh():
    """Stones (slot 0, limestone), logs (slot 1, the ship timber, tarred dark where charred) and an ash bed (slot 1, all tar)."""
    rng = random.Random(3103)
    b = Builder()
    b.slot = 0
    for k in range(10):
        a = 2 * math.pi * k / 10 + rng.uniform(-.1, .1)
        cx, cy = 48 * math.cos(a), 48 * math.sin(a)
        size, height = rng.uniform(11, 15), rng.uniform(9, 14)
        sides = 7
        radii = [size * rng.uniform(.8, 1.15) for _ in range(sides)]
        rings = [[b.vertex((cx + radii[j] * g * math.cos(2 * math.pi * j / sides), cy + radii[j] * g * math.sin(2 * math.pi * j / sides), -4 + height * s),
                           0, 0, dry) for j in range(sides)] for s, g, dry in ((0, .9, .2), (.5, 1.0, .6), (1.0, .5, 1.0))]
        top = b.vertex((cx, cy, -4 + height * 1.05), 0, 0, 1.0)
        for j in range(sides):
            n = (j + 1) % sides
            out = (math.cos(2 * math.pi * (j + .5) / sides), math.sin(2 * math.pi * (j + .5) / sides), .3)
            for lo, up in zip(rings, rings[1:]):
                b.quad(lo[j], lo[n], up[n], up[j], out)
            b.tri(rings[-1][j], rings[-1][n], top, (out[0], out[1], 2.0))
    b.slot = 1
    # The ash bed: a low dark disc inside the ring.
    centre = b.vertex((0, 0, 1.5), 1.0, 0, .2)
    rim = [b.vertex((38 * math.cos(t), 38 * math.sin(t), -1.0), 1.0, 0, .2) for t in [2 * math.pi * k / 16 for k in range(16)]]
    for k in range(16):
        b.tri(centre, rim[k], rim[(k + 1) % 16], (0, 0, 1))
    # Four logs crossed over it, their middles charred.
    for k, a in enumerate((.2, 1.75, .95, 2.55)):
        c, s = math.cos(a), math.sin(a)
        z = 6 + 4 * k
        path = [(-34 * c, -34 * s, z), (0, 0, z + 3), (34 * c, 34 * s, z)]
        start = len(b.verts)
        b.tube(path, lambda i: (4.5, 4.2, 4.5)[i], sides=7)
        for v in range(start, len(b.verts)):
            x, y, _ = b.verts[v]
            b.colours[v] = (min(1.0, 1.4 - math.hypot(x, y) / 30.0), 0.0, .5)   # tar (char) toward the middle
    return b


def import_icon():
    task = unreal.AssetImportTask()
    for k, v in {'filename': str(ROOT / 'Art/Items/Icons/Campfire-v1.png'), 'destination_path': ICONS, 'destination_name': 'T_Icon_Campfire_v1',
                 'automated': True, 'replace_existing': True, 'save': True}.items():
        task.set_editor_property(k, v)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.load_asset(f'{ICONS}/T_Icon_Campfire_v1')
    texture.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    texture.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
    texture.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    texture.set_editor_property('srgb', True)
    assert unreal.EditorAssetLibrary.save_loaded_asset(texture)
    return texture


def data_asset(path, cls):
    folder, name = path.rsplit('/', 1)
    asset = unreal.load_asset(path)
    if not asset:
        factory = unreal.DataAssetFactory()
        factory.set_editor_property('data_asset_class', cls)
        asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, cls, factory)
    assert asset, path
    return asset


def recipe(name, output, costs, seconds, needs_fire):
    r = data_asset(f'{RECIPES}/{name}', unreal.EWCraftingRecipe)
    ingredients = []
    for item_path, quantity in costs:
        ingredient = unreal.EWCraftingIngredient()
        ingredient.set_editor_property('item', unreal.load_asset(f'{ITEMS}/{item_path}'))
        ingredient.set_editor_property('quantity', quantity)
        ingredients.append(ingredient)
    r.set_editor_property('ingredients', ingredients)
    r.set_editor_property('output', output)
    r.set_editor_property('craft_seconds', seconds)
    r.set_editor_property('needs_fire', needs_fire)
    assert unreal.EditorAssetLibrary.save_loaded_asset(r)
    return r


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    timber = unreal.load_asset(TIMBER_MATERIAL) or make_timber_material()
    limestone = unreal.load_asset(LIMESTONE)
    assert limestone, 'run build_arrival.py first'
    ring = write_static_mesh(ring_mesh(), f'{MESHES}/SM_Campfire_v1', [limestone, timber], 40.0)

    item = data_asset(f'{ITEMS}/Building/DA_Campfire', unreal.EWItemDefinition)
    held = unreal.Transform(location=GRIP.translation, rotation=GRIP.rotation.rotator(), scale=unreal.Vector(.3, .3, .3))
    for prop, value in {'item_id': 'Item.Campfire', 'display_name': 'Campfire',
                        'description': 'Stones and wood for a fire. Hold it and press Left Mouse where the ground shows blue to lay it. Cook on it; feed it wood to keep it burning.',
                        'category': unreal.EWItemCategory.TOOL, 'max_stack_size': 5, 'unit_weight': 4.0,
                        'equipment_slot': unreal.EWEquipmentSlot.MAIN_HAND, 'held_mesh': ring, 'held_mesh_transform': held,
                        'icon': import_icon(), 'placed_actor': unreal.EWCampfire.static_class()}.items():
        item.set_editor_property(prop, value)
    assert unreal.EditorAssetLibrary.save_loaded_asset(item)

    report = {'recipes': {}}
    berry_dish = unreal.load_asset(f'{ITEMS}/Food/DA_CookedBerryDish')
    assert berry_dish
    for name, output, costs, seconds, fire in (('DA_RecipeCampfire', item, CAMPFIRE_COST, 5.0, False),
                                                ('DA_RecipeCookedBerryDish', berry_dish, BERRY_DISH_COST, 6.0, True)):
        recipe(name, output, costs, seconds, fire)
        report['recipes'][name] = {'costs': costs, 'seconds': seconds, 'needs_fire': fire}
    for name in ('DA_RecipeCookedFish', 'DA_RecipeCookedMeat'):
        r = unreal.load_asset(f'{RECIPES}/{name}')
        r.set_editor_property('needs_fire', True)
        assert unreal.EditorAssetLibrary.save_loaded_asset(r)
        report['recipes'][name] = {'needs_fire': True}

    falloffs = {'SA_Close_v1': import_audio.attenuation('SA_Close_v1')}
    wave = import_audio.import_sound('World/AMB_CampfireLoop-v1.wav', 'S_CampfireLoop_v1', .9, 'closeloop', falloffs)
    report['sound'] = {'name': wave.get_name(), 'seconds': round(wave.get_editor_property('duration'), 2)}
    report['success'] = True
    (ROOT / 'Saved/CampfireResult.json').write_text(json.dumps(report, indent=2))
    unreal.log('Campfire built')


if __name__ == '__main__':
    main()
