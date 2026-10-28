"""Turns on tree pushing for the elephant definition (owner, October 16: elephants push down trees). Same value build_animals.py now writes."""
import unreal
da = unreal.EditorAssetLibrary.load_asset('/Game/Elitewake/Wildlife/Animals/DA_Animal_Elephant')
da.set_editor_property('pushes_trees', True)
assert unreal.EditorAssetLibrary.save_loaded_asset(da)
unreal.log('EWSETUP elephant pushes_trees=%s' % da.get_editor_property('pushes_trees'))
