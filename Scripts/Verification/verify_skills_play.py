"""Play: the constellation skill tree (owner, October 22). The Skills section shows the stars; a star with recipes lists their materials; with no skill point nothing can
be lit; a level earns a point; Enter lights the picked star (the keyboard path of the controller's A), adding its recipe to the crafting menu and its bonus to the
survivor; the new recipe crafts. Listen-server plus one client (EW_PLAY_PLAYERS=2). Writes Saved/SkillsPlayResult.json."""
import unreal, json, time
from pathlib import Path
lib = unreal.EWEditorVerificationLibrary
worlds = lib.get_play_worlds()
pcs = [unreal.GameplayStatics.get_player_controller(w, 0) for w in worlds]
client = next(c for c in pcs if not c.has_authority())
server_world = next(w for w, c in zip(worlds, pcs) if c.has_authority())
client_world = worlds[pcs.index(client)]


def pid(p):
    return json.loads(unreal.ToolsetLibrary.get_object_properties(p.get_editor_property('PlayerState'), ['PlayerId']))['PlayerId']


owner = next(p for p in unreal.GameplayStatics.get_all_actors_of_class(server_world, unreal.EWCharacter) if pid(p) == pid(client.get_controlled_pawn()))
progress = owner.get_progression_component()
stats = owner.get_survival_component()
inv = owner.get_inventory_component()
remote_stats = client.get_controlled_pawn().get_survival_component()
remote_inv = client.get_controlled_pawn().get_inventory_component()
wood = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestWood')
stone = unreal.load_asset('/Game/Elitewake/Items/Testing/DA_TestStone')
hatchet_recipe = unreal.load_asset('/Game/Elitewake/Crafting/Testing/DA_RecipeHatchet')
assert wood and stone and hatchet_recipe
hatchet = hatchet_recipe.get_editor_property('output')
hatchet_recipe.set_editor_property('craft_seconds', 0.3)
phase = 0
next_at = time.monotonic() + 2
checks = []
handle = None
state = {}


def menu():
    return next(w for w in unreal.WidgetLibrary.get_all_widgets_of_class(client_world, unreal.EWInventoryWidget, False)
                if w.get_owning_player() == client and w.is_in_viewport())


def finish(error=None):
    unreal.unregister_slate_post_tick_callback(handle)
    client.set_inventory_open(False)
    Path(unreal.Paths.project_saved_dir(), 'SkillsPlayResult.json').write_text(json.dumps({'success': error is None, 'checks': checks, 'error': error}, indent=2))


def tick(delta):
    global phase, next_at
    if time.monotonic() < next_at:
        return
    next_at = time.monotonic() + 1.5
    try:
        if phase == 0:
            assert hatchet_recipe not in list(inv.get_available_recipes()), 'hatchet recipe known before the skill'
            state['carry'] = stats.get_max_carry_weight()
            state['health'] = stats.get_max_health()
            client.set_inventory_open(True)
        elif phase == 1:
            assert lib.send_verification_ui_key(client, 'PageDown') and lib.send_verification_ui_key(client, 'PageDown') and lib.send_verification_ui_key(client, 'PageDown')
        elif phase == 2:
            m = menu()
            assert m.get_selected_section() == 3, f'section {m.get_selected_section()}'
            tree = m.get_skills_panel()
            assert tree.get_node_count() == 9
            checks.append('Page keys reach the Skills section, which shows the nine-star constellation')
            tree.select_node(1)
            assert str(tree.get_selected_id()) == 'Gatherer'
        elif phase == 3:
            tree = menu().get_skills_panel()
            mats = str(tree.get_detail_materials())
            assert 'Hatchet' in mats and 'Wood' in mats and 'Stone' in mats, mats
            assert not tree.is_unlock_enabled(), 'unlock live with no skill point'
            checks.append('Hovering/picking a star lists its recipe and the materials; Unlock is off with no skill point')
            assert lib.send_verification_ui_key(client, 'Enter')
        elif phase == 4:
            assert not progress.is_skill_unlocked('Gatherer'), 'lit without a point'
            progress.grant_experience(progress.get_experience_for_next_level())
        elif phase == 5:
            assert progress.get_skill_points() == 1
            tree = menu().get_skills_panel()
            assert tree.is_unlock_enabled()
            assert lib.send_verification_ui_key(client, 'Gamepad_FaceButton_Bottom')
        elif phase == 6:
            assert progress.is_skill_unlocked('Gatherer') and progress.get_skill_points() == 0
            assert hatchet_recipe in list(inv.get_available_recipes()), 'recipe not added on the server'
            assert hatchet_recipe in list(remote_inv.get_available_recipes()), 'recipe not replicated to the client'
            assert stats.get_max_carry_weight() == state['carry'] + 5 and remote_stats.get_max_carry_weight() == state['carry'] + 5
            checks.append('A point lights Gatherer with A: the Hatchet recipe reaches the crafting menu on both machines, +5 kg carrying')
            progress.grant_experience(progress.get_experience_for_next_level())
        elif phase == 7:
            tree = menu().get_skills_panel()
            tree.select_node(3)
            assert str(tree.get_selected_id()) == 'Hardy'
            assert lib.send_verification_ui_key(client, 'Enter')
        elif phase == 8:
            assert progress.is_skill_unlocked('Hardy')
            assert stats.get_max_health() == state['health'] + 10 and remote_stats.get_max_health() == state['health'] + 10
            tree = menu().get_skills_panel()
            tree.select_node(7)
            assert str(tree.get_selected_id()) == 'Metalwork'
            assert not progress.can_unlock_skill('Metalwork'), 'Metalwork lit without its parent star'
            checks.append('A star needs the one it hangs from: Hardy gives +10 health; Metalwork stays locked')
            # Keyboard/d-pad movement among the stars.
            tree.select_node(0)
            assert lib.send_verification_ui_key(client, 'Gamepad_DPad_Up')
        elif phase == 9:
            sel = str(menu().get_skills_panel().get_selected_id())
            assert sel in ('Gatherer', 'Torchbearer', 'FieldRepair', 'SecondWind'), f'd-pad up from the root reached {sel}'
            checks.append('The d-pad moves from star to star')
            assert inv.add_item(wood, 15) == 15 and inv.add_item(stone, 10) == 10
            assert lib.send_verification_ui_key(client, 'PageUp') and lib.send_verification_ui_key(client, 'PageUp')
        elif phase == 10:
            m = menu()
            assert m.get_selected_section() == 1
            for _ in range(10):
                if menu().get_shown_recipe() == hatchet_recipe:
                    break
                assert lib.send_verification_ui_key(client, 'Down')
        elif phase == 11:
            assert menu().get_shown_recipe() == hatchet_recipe, 'the unlocked Hatchet is not selectable'
            assert menu().is_craft_action_enabled()
            assert lib.send_verification_ui_key(client, 'Enter')
        elif phase == 13:
            assert inv.get_item_count(hatchet) == 1 and inv.get_item_count(wood) == 0 and inv.get_item_count(stone) == 0
            checks.append('The skill-unlocked Hatchet crafts: 15 Wood and 10 Stone used, one Hatchet made')
            assert progress.get_experience() > 0
            finish()
            return
        phase += 1
    except Exception as exc:
        finish(f'Phase {phase}: {exc!r}')


handle = unreal.register_slate_post_tick_callback(tick)
