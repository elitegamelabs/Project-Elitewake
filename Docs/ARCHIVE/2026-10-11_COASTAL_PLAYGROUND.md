# Coastal playable slice

The next connected milestone is beach resources → Port introduction → starter
tools → first two-hardpoint sloop → nearby island. The first saved world slice is
`/Game/Elitewake/Maps/Lvl_CoastalPlayground`.

## Play it

Open `Content/Elitewake/Maps/Lvl_CoastalPlayground` in the Content Browser and
press Play. It is currently open in the active editor. Startup settings still
point to ThirdPerson, so reopen this map when testing the coastal slice later.

- Beach landing: loose Wood and Stone ahead; look close to each stack and press E.
- Inland grove: fiber and Azren shrubs use E. Trees require an equipped axe;
  stone nodes require an equipped pickaxe and the normal attack input.
- Freshwater spring: inland at approximately X −17 m, Y 15 m. Look at its surface
  and press E when hydration is below full.
- Dock: extends from the beach over the swimmable sea. Nearby islet establishes
  the destination for the coming sailing slice.
- I opens inventory/crafting; M opens the existing surrounding-map preview.

All gathering uses the existing authoritative actors and finite replicated
pools. This scene grants no items or recipes. Starter tools remain locked until
the innkeeper introduction; that production mission is not wired yet. Existing
test item weights/yields remain provisional and are not approved ecology tuning.

## Boundaries and next dependency

The coast now has an original irregular sloped shoreline, generated sand and
weathered dock timber textures, a brush-backed ocean swimming volume, a seabed,
and animated reflective water with small visual waves. Move with the existing
movement keys; look down and move forward to dive, and hold Jump/Space to ascend.
Look up toward the beach and swim forward to return through the shallows.

The visual waves displace the surface slightly; swimming uses the static mean
waterline at Z -65 cm.
The owner sets maximum ocean depth to **500 meters below the mean surface**.
The prototype swimming volume and flat deep seabed now reach Z -50065 cm;
regional basins, seabed slopes and shelves remain to be authored.
Vessel buoyancy and storm simulation remain unbuilt. Swimming animations, underwater effects,
audio, oxygen/drowning and approved swimming survival tuning remain open.
Vegetation/rocks and the interior remain blockout geometry. Wildlife, NPCs, inn,
ship repair, production introductions and world persistence remain outstanding.

Next connect a controllable first-sloop prototype and boarding to this same
map, retaining two cannon hardpoints. Wildlife should follow as real moving
actors with appropriate habitat and authority, rather than decorative markers.
Final terrain, foliage, HUD art and ship assets need a separate visual pass.

`Scripts/Setup/upgrade_coastal_water.py` authors the volume/materials and imports
the original sources from `Art/Environment`; `shape_coastal_shore.py` authors the
shore mesh. Both require Play stopped and saved maps. These scripts target their
owned upgrade assets; do not run them over artist-edited versions without review.
Original generated texture prompts and source hashes are in
`Art/Environment/generation.json`. They are base-color textures, not scanned PBR sets.

`Scripts/Verification/verify_coastal_swimming_play.py` checks the actual saved
water volume, owning-client movement/diving/ascent and shoreline return. It
arranges positions only in Play and does not grant items or recipes. Evidence
is in `Saved/CoastalSwimmingResult.json`; scene authoring evidence is in
`Saved/CoastalWaterUpgradeResult.json` and `Saved/CoastalShoreResult.json`.

`Scripts/Setup/create_coastal_playground.py` creates the scene once and refuses
to overwrite an existing map or leave a dirty level. Continue editing the saved
map instead of regenerating it. It preserves the original maps and startup
configuration.

`Scripts/Verification/verify_coastal_play.py` checks two-player in-process
listen/client spawning, an actual saved Wood source, the spring, dock collision
and unchanged recipe locks. It arranges pawn positions and a hydration deficit
only in Play. Results are written to `Saved/CoastalPlayResult.json`.
