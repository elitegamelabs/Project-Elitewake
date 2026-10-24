"""Write the playtest guides into the Journal (I, then JOURNAL). Safe to run again; it rewrites the pages.
Run in the editor, outside Play:
    UnrealEditor.exe EW.uproject -ExecCmds="py <this file>"

These are test guides for the coastal map's playtesters: how to get aboard a ship, raise the anchor, fit sails and
the wheel, steer, paddle the raft, find your way about a ship, and gather, swim and fight on the coast. The
Quartermaster's own guidance replaces them when the prologue is written. Keep them true to the controls.
"""
import json
from pathlib import Path
import unreal

FOLDER = '/Game/Elitewake/Journal'
NAME = 'DA_TestJournal'

PAGES = [
    ('Ships', 'Getting aboard', '''Swim up beside a ship. Its ladders are labelled "Ladder" on your screen; the one you are looking at is drawn larger. When "Climb the ladder" appears, press E once (X on a controller) to take hold.

On the ladder:
- Up arrow or W climbs; Down arrow or S climbs down (up and down on a controller's D-pad).
- At the top you step onto the deck by yourself.
- At the foot of the ladder, or with Space, you let go into the water.

The raft and the dinghy sit low in the water. Look at either side, press E, then Up to step aboard.

To leave a ship, walk to the rail and jump over the side.

Where the boats are:
- Sloop: off the end of the dock.
- Raft and dinghy: side by side next to the dock.'''),
    ('Ships', 'Raising and dropping the anchor', '''Every ship starts anchored, and an anchored ship cannot move.

1. Find the capstan: the round wooden drum on deck near the bow. On the raft it is the stone on its coil of rope at the front; on the dinghy, the grapnel in the bow.
2. Look at it and hold E. The prompt reads "Raise anchor" or "Drop anchor".

Drop the anchor before you leave a ship. Sails stay set when you leave the helm, so a ship left unanchored keeps sailing without you.

Dropping the anchor while under way brings the ship to a stop within a couple of seconds.'''),
    ('Ships', 'Fitting sails', '''Ships start as bare hulls. Each mast has sail mounts at its foot, sized Small, Medium or Large, and a mount takes only a sail of its own size.

1. Get the sails. On these test ships they are already in the ship's hold. Look at the cargo hatch, the opening in the middle of the deck, and hold E: the hold opens beside your inventory. Click a sail to move it into your inventory.
2. On deck, every mount is labelled on your screen with the size of sail it takes, for example "Medium sail mount". While you carry a sail that fits, its mount turns green and reads "Fit Medium sail here". Walk to it and look at it: the prompt reads "Install Medium Sail".
3. Hold E until the sail is fitted. It appears rolled up on its spars, ready to set.

To take a sail off, look at it and hold E ("Remove ..."); it goes back into your inventory.

Which sail goes where:
- Sloop: Medium on the mast, Small at the bow.
- Dinghy: one Small on its mast.
- Raft: no sail. It is paddled.'''),
    ('Ships', 'Fitting the wheel', '''A ship cannot be steered until its wheel is fitted.

The wheel is in the hold with the sails. Its mount is on the sloop's deck near the stern.

Its mount is labelled "Wheel mount" on your screen, and turns green ("Fit the wheel here") while you carry the wheel. Look at it and hold E: "Install Ship's Wheel".

The raft's paddles and the dinghy's tiller are part of those boats and are always there.'''),
    ('Ships', 'Sailing and steering', '''With the wheel fitted and the anchor up:

1. Look at the wheel and hold E: "Take the helm". The view pulls back so you can see the whole ship.
2. W sets more sail: furled, then half, then full. S takes sail in again.
3. Hold A or D to put the rudder over to port or starboard. Let go and it comes back to the middle.
4. Hold E to leave the helm. The sails stay as they are: take them in or drop the anchor first.

Trimming the sails to the wind:
- The compass across the top of the screen shows where you are facing and marks the WIND where it blows from.
- At the helm, the SAILS bar under the compass shows where your sails are swung, from port to starboard. The green band is where they would catch the wind best.
- Hold Shift and press A or D to swing the sails toward port or starboard. Bring the marker into the green band; the readout says "Sails drawing well".
- When you change course, the best angle changes too: trim again.
- Badly trimmed sails still move you, but slowly.

Good to know:
- Fit at least one sail, or the ship will not move.
- With the wind behind you, swing the sails right out to one side. With it across the ship, about half way out. Heading into the wind, keep them close in. You are slowest heading into it.
- The more sails you fit, the faster she goes. A heavy hold slows her down.
- The rudder still turns a little when you are stopped, so you can always swing away from a shore.'''),
    ('Ships', 'Paddling the raft', '''The raft has no mast or sail: you paddle it.

1. Climb aboard and raise its anchor: hold E at the stone on its rope coil at the front.
2. Look at the paddles resting on the side rails and hold E: "Take up the paddles".
3. W and S set the stroke: resting, easy, hard. A and D steer.
4. Hold E to put the paddles down. Drop the anchor before you leave.

Paddling ignores the wind, but a raft is slow: about 2.5 metres a second at a hard stroke.'''),
    ('Ships', 'Finding your way about a ship', '''You can walk about the deck while the ship sails; you ride along with it.

- Hatch stairs: the stairs in the sloop's hatch lead down to its hold.
- The hold: hold E at the cargo hatch to open it beside your inventory, then click a stack to move it across. Anyone aboard can use it.
- Load: everything in the hold plus the fitted sails and wheel is the ship's load. Past half its capacity she slows, and an overloaded ship is swamped after 60 seconds until you lighten her.'''),
    ('The coast', 'Gathering', '''- Fiber plants, piles of fallen sticks and berry bushes: look at one and press E to gather all of it.
- Trees: in this test build, equip the wooden axe (open your inventory with I, select it and choose Equip, or put it on the hotbar and press its number). Aim at the trunk and press Left Mouse (RT): Wood and Thatch. The approved design allows bare-hand tree harvesting, but that is not implemented in this build.
- Boulders: equip the wooden pickaxe the same way and strike a boulder with Left Mouse: Stone.
- The tool you equip is in your hand, and Left Mouse chops with it. The torch lights your way at night.

Nothing grows back yet, so share the island.'''),
    ('The coast', 'Swimming', '''Walk into the sea to swim. You float with your head out of the water.

- Look down and move forward to dive.
- Hold Space to rise.
- Let go and you drift back up to the surface.

The sea gets deep a short way past the sand, beyond a sharp edge where the water turns dark blue.'''),
    ('The coast', 'Water and food', '''- Fresh water: the spring is a pool inland, north-west of where you start. Look at it and press E while thirsty.
- Berries: eat them from your inventory while fresh. They stay fresh for 20 real minutes, then become an inedible toxic crafting resource.
- Watch the bars in the corner: health, stamina, hunger, thirst and the weight you carry.'''),
    ('The coast', 'Fighting', '''Left Mouse (RT) swings once a second. A swing that reaches another survivor or a sea creature within arm's length deals 10 damage, and they flinch.

You can swing while swimming, but not while lying prone, on a ladder or at a helm.'''),
    ('The coast', 'Sea creatures', '''The sea around the island has life in it. Swim out past the sand and look down.

Dangerous: they come for a swimmer who gets close, and keep at it while you stay in the water.
- Great white and hammerhead sharks, out in deep water. A bite takes a fifth to a quarter of your health.
- Manta rays sting with their tails.
- Squid lurk deepest of all and grab.
Climb out onto a boat or the shore and they give up.

Harvesting: strike a creature with Left Mouse until it dies. It floats up belly-first; look at it and press E to harvest Raw Fish. Raw food is for cooking, which is not in yet.

Bass, catfish and piranhas live in fresh water, which this coast does not have yet.'''),
]


def main():
    assert not unreal.EWEditorVerificationLibrary.get_play_worlds(), 'Stop Play first'
    journal = unreal.load_asset(f'{FOLDER}/{NAME}')
    if not journal:
        factory = unreal.DataAssetFactory()
        factory.set_editor_property('data_asset_class', unreal.EWJournalData)
        journal = unreal.AssetToolsHelpers.get_asset_tools().create_asset(NAME, FOLDER, unreal.EWJournalData, factory)
        assert journal, NAME
    entries = []
    for section, title, body in PAGES:
        entry = unreal.EWJournalEntry()
        entry.set_editor_property('section', section)
        entry.set_editor_property('title', title)
        entry.set_editor_property('body', body)
        entries.append(entry)
    journal.set_editor_property('entries', entries)
    assert unreal.EditorAssetLibrary.save_loaded_asset(journal)
    Path(unreal.Paths.project_saved_dir(), 'TestJournalResult.json').write_text(json.dumps({'success': True, 'pages': [p[1] for p in PAGES]}, indent=2))
    unreal.log(f'Test journal: {len(PAGES)} pages')


if __name__ == '__main__':
    main()
