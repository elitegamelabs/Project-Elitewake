# Inventory follow-up after the final slice

**Owner-reported functional issue, deferred:** Equipment is not accepted as working in the owner's normal play experience. Revisit actual equip/unequip, slot selection, appearance and persistence separately from visual polish. First verify the launch path and build: previous checks used the Development Editor and no updated packaged EXE was produced. Passing fixture checks do not close this issue. See Inventory-Slice-3-Review.md for the owner-review notation.

Recorded during the Slice 1 closeout review on November 12, 2026. The owner requested that these remaining visual differences be recorded so the functional slices can proceed.

- Headers and navigation use taller, more uniform wood bars than the reference. The selected tab has a simpler gold face and softer outline than the reference's sculpted tab.
- Inventory slots are shorter and wider than the illustrated slots. The live grid has six columns and four rows to display the actual 24-slot capacity. The reference illustrates three rows.
- The heading font is now Tinos Bold. Body text still mixes serif and outlined sans-serif treatments, with different proportions from the reference.
- Actual item icons are smaller and less polished than the reference illustrations. **Background cleanup completed November 12:** all nine original clothing icons now have transparent backgrounds, with original texture references retained and bright/dim 1080p/720p checks passed. See Clothing-Icon-Transparency-Review.md. Existing cropped fur artwork and the broader item-art quality differences remain.
- Character Stats uses simpler bars, outlines, and controls. The Oxygen, Fortitude, and Intelligence symbols differ from the reference, including the current FRT and INT text markers.
- Selection feedback is simpler than the reference's luminous beveled treatment.
- The live portrait displays the current Unreal survivor mesh and its equipment. The verified fixture uses SKM_Manny_Simple and placeholder cube, sphere, and cylinder equipment meshes. Finished survivor art is a separate asset dependency.
- Long Inventory item captions clip, including clothing names observed at both 1080p and 720p. The lower stat controls also have tight clearance above the pinned reset button. Keep these in the later readability pass.

The following differences reflect later owner decisions and should be retained.

- Warm panel backgrounds are 70% opaque in the left and center columns and 80% opaque in the portrait column, with the environment visible through them.
- The reset label is RESET STAT POINTS (5 GOLD). The reference image's 25-gold label is superseded.
- Header icons are optional.
- The separate center-column Recipe Details section was removed. Recipe inspection will live within the existing crafting tiles in the crafting slice.
- The right column displays the actual live survivor. The reference's illustrated pirate is a visual example.
