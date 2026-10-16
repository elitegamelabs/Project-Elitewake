# ELITEWAKE Ship Hulls and Removable Sail Attachments
Date: 2026-10-15
Status: CONFIRMED owner direction

## Core design decision
Ships should be authored and represented with their sails absent by default. Sails are separate, attachable ship modules, not permanently built into the hull mesh.

## Sail attachment assembly
A sail attachment should include the complete rigging assembly intended to be installed as one module:
- The appropriate mast/poles and supporting pole structure for that sail module.
- The flag(s) already mounted on the poles as part of the attachment.
- The sail cloth itself as a separate component within the attachment assembly, so the ship can be shown or used without sails and sails can be installed/removed through the attachment system.
- Any necessary attachment points, sockets, rigging, and visual connection details.

Do not interpret “ships without sails” as removing masts/poles and flags from the sail attachment. The default ship hull has no permanently integrated sails; the attachable sail assembly supplies its poles and pre-mounted flags, along with the sail component.

## Asset and implementation requirements
- Keep hull meshes, sail attachment assemblies, sail cloth, flags, and rigging modular where practical.
- Create distinct attachment assets compatible with the existing ship/module system and ship classes.
- Preserve ship class constraints, module compatibility, gameplay balance, and existing sailing behavior; do not change those systems merely to satisfy the visual separation.
- Support the intended attach/remove workflow and ensure installed attachments align correctly with each compatible hull.
- Keep flags attached to their poles when the sail assembly is moved, installed, removed, or displayed in previews.
- Produce concept/reference images and actual 3D models as separate deliverables. Track meshes, materials, rigging, animations if needed, Unreal Engine 5.8 integration, and in-game validation independently.
- Do not replace existing UI inventory or crafting icons as part of this asset work.

## Acceptance criteria
1. Base ship hull assets do not have permanently integrated sails.
2. Sail attachments contain their poles and flags already mounted on those poles.
3. Sail cloth belongs to the removable/attachable sail module, not the base hull.
4. Attachments fit the intended ship classes and can be installed/removed without visual misalignment.
5. The implementation is tested in Unreal Engine 5.8 and existing ship controls and sailing systems remain functional.
