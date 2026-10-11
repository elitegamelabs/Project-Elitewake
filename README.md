# Elitewake

An open-world PvP and PvE pirate survival sandbox by **Elite Game Labs**, built in **Unreal Engine 5.8**. Set in the mid-1700s across four regions of islands and open ocean, players survive, gather, craft, sail, explore, hunt treasure, tame animals, trade and fight. They grow from castaway to captain to pirate legend.

Ships are the center of the game. They start as bare hulls that players fit out and upgrade. Land bases are possible but temporary and raidable. The core loop is **Prepare → Sail → Discover → Fight or Explore → Loot → Escape → Upgrade → Sail Farther.**

## Status

Early development. Movement, survival stats, inventory, equipment, interaction, gathering, food, crafting, objectives and private multiplayer testing work as tested foundations. One connected test map, a coast you can swim from, exists locally. Sailing, combat, wildlife, the prologue, save/load and final art are not built yet. See the [project guide](Docs/PROJECT_GUIDE.md) for details and known problems.

## Documentation

- [Design reference](Docs/DESIGN_REFERENCE.md): what the game is meant to be, by topic, with open questions.
- [Project guide](Docs/PROJECT_GUIDE.md): what is built, what is broken, next work, building and testing, conventions.
- [Verification](Docs/VERIFICATION.md): what has been tested and what has not.
- [Archive](Docs/ARCHIVE/README.md): earlier reviews and full dated logs.

The design guides themselves (Shared Design Authority, Development & Systems, Creative & World, Ecology) are maintained outside this repository by the owner.

## Getting started

1. Install Unreal Engine **5.8.3**, Visual Studio with the Unreal C++ workload, and **Git LFS**.
2. Clone the repository and run `git lfs pull`.
3. Open `EW.uproject` and let it build the C++ modules.
4. Open `Content/Elitewake/Maps/Lvl_CoastalPlayground` (the default startup map is still the Unreal template map).

Work from a folder outside OneDrive or other sync services. The team's working copy is `C:\UnrealProjects\EW`; a OneDrive copy is only a backup, and opening it by mistake shows outdated work.

## Repository layout

| Path | Contents |
| --- | --- |
| `Source/EW/` | Gameplay C++ and native tests |
| `Source/EWEditor/` | Editor-only test helpers |
| `Content/Elitewake/` | Elitewake assets and maps |
| `Art/` | Source images for placeholder art, with generation records |
| `Scripts/` | Unreal Python and PowerShell setup and verification scripts |
| `Docs/` | Project documentation |
