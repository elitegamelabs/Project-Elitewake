# Project Structure

## Content Convention

All new Elitewake-specific assets should be created under `Content/Elitewake/` and grouped by gameplay domain rather than by individual developer.

Planned top-level domains include:

- `Characters`
- `Core`
- `Input`
- `Interaction`
- `Inventory`
- `Items`
- `Missions`
- `Ships`
- `Survival`
- `UI`
- `World`

Do not create every planned directory before it is needed. Add each domain with the first real asset that belongs there.

## C++ Convention

The runtime module remains `EW`. New classes should be grouped beneath `Source/EW/` by gameplay domain. Public headers and implementation files should remain close together until module growth justifies a separate public and private layout.

Recommended initial domains are:

- `Character`
- `Core`
- `Input`
- `Interaction`
- `Inventory`
- `Ships`
- `Survival`
- `UI`

Do not move or rename the existing template classes until their Blueprint dependencies have been reviewed in Unreal Editor.

## Naming

- C++ classes use Unreal prefixes and `EW` in the class name where it improves project identity.
- Blueprints use `BP_`.
- Actor Components use `AC_` for asset names.
- Input Actions use `IA_`.
- Input Mapping Contexts use `IMC_`.
- Widgets use `WBP_`.
- Data Assets use `DA_`.
- Data Tables use `DT_`.
- Enums use `E_` for assets and `E` for C++ types.
- Structures use `ST_` for assets and `F` for C++ types.

Prefer descriptive names. Avoid names tied to the temporary product title when a neutral system name will remain valid after rebranding.

