# ELITEWAKE — Helm-mounted sail rotation controls

## Player requirement
When the player interacts with and mounts a ship's steering wheel (helm), enable controls to rotate the direction the attached sails face. This control is **available only while actively mounted at the helm**. Dismounting immediately disables the sail-rotation input and restores normal controls.

## Controls
- Keyboard: **Left Arrow** rotates sails left; **Right Arrow** rotates sails right.
- Controller: **LB** rotates sails left; **RB** rotates sails right.
- Implement via contextual Enhanced Input mapping active only in helm-mounted mode; prevent collisions with other helm controls.
- Provide responsive incremental rotation, smooth interpolation, and consistent operation for all eligible ship classes including Brigantine and Cavalier.

## Rotation behavior
- User requests **180-degree sail rotation** to change sail facing direction, described as spinning around the front. Support a 180-degree total rotation range for the sail attachment assembly, rather than rotating the entire ship hull.
- **Pivot clarification for implementation:** verify the existing sail module pivot/rig and whether the requested 180-degree arc is centered on the forward-facing orientation or extends from forward to aft. Do not invent the pivot axis or limits without inspecting the current ship setup.
- Rotate modular sail assemblies (mast/pole, attached flags, sail) in a physically plausible way; preserve attachment points and avoid clipping where possible. If the intended rotating part is only a boom/sail rather than the entire mast, verify with the user before implementing.
- Steering wheel mount state is authoritative: no sail rotation from these controls when unmounted, on foot, swimming, or operating unrelated interfaces.
- Multiplayer: validate helm ownership and replicate sail orientation if ships support multiplayer.

## Agent implementation and validation
Claude, Codex, ChatGPT, and other relevant agents: inspect current ship/helm interaction and sail attachment architecture in Unreal Engine 5.8 before modifying it. Implement and test keyboard and controller mappings, mounted/unmounted gating, rotation limits, smooth animation, and interactions with steering and existing modular sail designs. Preserve hull-without-sails design and existing game behavior. This is a design requirement; no Blueprint, model, or animation implementation is claimed by this document.
