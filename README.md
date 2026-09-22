# Project Elitewake

Project Elitewake is the working title for a ship-centered pirate survival sandbox developed by Elite Game Labs in Unreal Engine 5.8.

The ship is the center of the game: the player's transportation, home, storage, workshop, combat platform, crew headquarters, progression platform, and social space.

## Core Loop

Prepare -> Sail -> Discover -> Fight or Explore -> Loot -> Escape -> Upgrade -> Sail Farther

## Current Stage

The project is at its foundation stage. Development should proceed through small systems that can be built, tested, and committed independently. The first playable target is version 0.01, not the finished game.

## Development Rules

- Use Unreal Engine 5.8.
- Keep stable gameplay foundations in C++ and use Blueprints for content assembly and iteration.
- Use Enhanced Input for remappable controls.
- Design gameplay for eventual server-authoritative multiplayer.
- Prefer modular, data-driven systems that can expand without replacement.
- Do not modify unrelated systems during a focused implementation task.
- Build, test, and commit each working milestone before starting the next one.
- Treat other games as design references only; all shipped code, assets, names, UI, dialogue, and presentation must be original.

## Repository Layout

- `Config/` - Project and engine configuration.
- `Content/` - Unreal assets. New game-specific assets belong under `Content/Elitewake/`.
- `Source/EW/` - Runtime C++ module.
- `EW.uproject` - Unreal project descriptor.

Generated directories such as `Binaries/`, `DerivedDataCache/`, `Intermediate/`, and `Saved/` are intentionally excluded from Git.

## Opening the Project

1. Install Unreal Engine 5.8 and the Visual Studio C++ components required by Unreal.
2. Install Git LFS before cloning or pulling the project.
3. Clone the repository and run `git lfs pull` if needed.
4. Open `EW.uproject`.
5. Allow Unreal to rebuild the native module when prompted.

## Source Control

The `main` branch represents known-good project state. Commit focused changes with clear messages and avoid committing generated Unreal or IDE files.

