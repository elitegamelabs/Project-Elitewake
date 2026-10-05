# M5C persisted inventory fixture

Verified October 5, 2026 in `C:\UnrealProjects\EW`, Unreal Engine 5.8.2. This slice adds real saved item content and an opt-in editor grant to verify the existing native inventory panel. It does not implement pickups, equipment, hotbar, save/load, production wood balance or multiplayer acceptance.

## Content and developer use

- Asset: `/Game/Elitewake/Items/Testing/DA_TestWood`, stable primary ID `EWItem:Test.Wood`.
- Display name: Wood (Test). Resource stack size 250 follows October Bible §30.17.
- Unit weight 0.1 kg is temporary fixture tuning. Ash/Oak/Birch gameplay definitions, icons and production weights remain pending.
- The asset is a native `UEWItemDefinition`, created and saved through Unreal-supported APIs. `Scripts/create_inventory_test_asset.py` preserves an existing asset rather than overwriting designer edits.
- `DefaultGame.ini` registers the EWItem scan under `/Game/Elitewake/Items`. It also supplies the required GameFeatureData scan/rule, resolving the existing startup configuration error.
- During Play, open the developer console and run `EWGrantTestWood 251`, then open inventory with I. Running `EWGrantTestWood 1` while the panel is open should refresh its counts/weight immediately.
- The command requires authority and positive quantity, has no client RPC, and its implementation is compiled only for editor builds. It never grants startup items. Inventory accepts only what fits its slots; displayed weight capacity is not yet enforced.
- To regenerate a missing fixture, run the editor PythonScript commandlet with `-EnablePlugins=PythonScriptPlugin -run=PythonScript -Script=<absolute path to Scripts/create_inventory_test_asset.py>`. Python is enabled for that invocation; no permanent project plugin addition is needed.

## Evidence

| Check | Result |
| --- | --- |
| EWEditor Win64 Development build | Succeeded after correcting a compiler-detected controller variable-name conflict |
| Supported asset creation | Saved .uasset; later idempotent commandlet run preserved it, exit 0, zero errors |
| `Elitewake.Inventory.StackingAndWeight` | Success |
| `Elitewake.Inventory.PersistedTestItem` | Success: asset-manager discovery and load, stable ID, 250 stack boundary, 251 split, weight synchronization, partial acceptance at full 24-slot capacity, excess rejection, removal and weight cleanup |
| Normal Play before granting | Empty inventory; Python assertions on used slots and screenshot inspection |
| Explicit controller grant 251 | Log: requested=251 added=251 total=251 slots=2 weight=25.1 kg; assertions match |
| Rendered panel through normal I input | Visible Wood (Test) x250 at 25.0 kg and x1 at 0.1 kg; Slots 2/24, total 25.1/50.0 kg |
| Grant 1 with panel already open | Visible second stack x2, total 25.2 kg; assertions confirm 252 items |
| Grant 0 and -1 | Rejected; quantity stays 252 |
| I close/reopen populated panel | Visually verified removal and correct returning 250/2 stacks |
| Stop/restart Play | Fresh session again Slots 0/24, Weight 0.0/50.0 kg, Inventory is empty |

Local evidence is ignored generated output: `Saved/Logs/M5CAssetCreation.log`, `M5CInventoryVerification.log`, `M5CPlayVerification.log`; screenshots `Saved/M5CPopulated.png`, `M5CLiveRefresh.png`, `M5CClosed.png`, `M5CReopened.png`, `M5CFreshEmpty.png`. Earlier Python verification-harness reflection errors remain in the Play log; the subsequent controller grant, assertions and actual I-driven visual checks succeeded. Do not mistake the early harness failures for a final gameplay failure.

## Remaining gates

Package/cook validation and multi-client item reference replication are pending. Controller Y/navigation, final UI layout/icons, long-list scrolling, item condition/rarity data, weight penalties, equipment and hotbar are not completed by this fixture. Next slice is server-validated pickup/interaction, preserving no-duplication and partial-capacity rules.
