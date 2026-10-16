# ELITEWAKE — Directional swimming animations (UE 5.8)

Applies to **both first-person and third-person** swimming, without replacing the existing animations unnecessarily.

- **In water, stationary / no movement input:** play the **existing default water idle animation**; do not switch to a directional swimming cycle until movement begins.
- **Forward input (including forward-left and forward-right diagonals):** play the **forward-swimming animation**, oriented/blended appropriately to the player's travel direction. Forward-diagonal movement should visibly swim forward, not use the backward/default cycle.
- **Backward input:** retain the **existing default swimming animation** requested by the user; do not force the new forward-swim cycle. The user referred to an existing animation as the 'spinning animation'; inspect the current animation assets and confirm which animation they mean rather than guessing or deleting it.
- **Left/right without forward input:** preserve existing lateral behavior pending confirmation of whether lateral-only input should use forward-swim or another cycle. Do not invent a new asset requirement.
- **Transitions:** smooth blend between stationary, forward, diagonal, backward and any existing lateral states; prevent abrupt resets, unwanted rotation, or animations playing on land.
- **View modes:** implement the same input/state logic for first-person and third-person, while using the appropriate meshes/animation blueprints for each perspective. Verify transitions and movement with keyboard/mouse and controller.

Claude, Codex and other coding agents: inspect existing water locomotion blueprints, animation assets, blendspaces, and movement input before editing; reuse current animations where specified, avoid breaking land movement, and test in Unreal Engine 5.8. This is a specification only; no Unreal animation assets or blueprints have been modified by this commit.