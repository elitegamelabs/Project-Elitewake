# Clothing icon transparency follow-up

November 12, 2026. This implements the explicitly queued post-Inventory clothing-icon background cleanup. The owner's equipment-functionality report remains unresolved and deferred.

## Changes

Removed the opaque rectangular backgrounds from the nine existing cloth, fur and metal clothing icons. These are background-extraction edits of the existing images, preserving their garment designs, colors and existing cropped extents. No new clothing designs, item definitions, recipes, equipment behavior or character models were introduced.

The existing Unreal texture package names remain unchanged under Content/Elitewake/UI/Icons/Armor. All nine item icon references still point to those same textures. The same images appear in Inventory and the existing recipe tiles.

The original PNGs, texture assets and old crop-generation script were copied before replacement into:

Saved/Recovery/ClothingIconAlpha-2026-11-12/Art, /Textures and /Scripts.

No recovery files, old concept sheets, player saves, world actors or intentionally removed documents were deleted or restored.

## Assets and workflow

- Final icon sources: Art/UI/Icons/Armor/T_Icon_ClothHeadWrap.png, T_Icon_ClothChest.png, T_Icon_ClothPants.png, T_Icon_FurHood.png, T_Icon_FurJacket.png, T_Icon_FurPants.png, T_Icon_MetalTricornHelmet.png, T_Icon_MetalCuirass.png and T_Icon_MetalPants.png.
- Curated source copies: Art/UI/Icons/Armor/Transparent/ with the same filenames.
- Edit mode and complete prompt set: [edit-manifest.json](C:/UnrealProjects/EW_CLEAN/Art/UI/Icons/Armor/Transparent/edit-manifest.json). Built-in image generation was used in background-extraction edit mode, with each original image as its edit target and transparent_background=true. No CLI fallback was used.
- Scripts/Art/make_armor_icons.py now validates and copies those curated RGBA cutouts without image manipulation. It no longer paints an RGB square behind the garments. The original crop table remains as provenance.
- Scripts/Setup/reimport_armor_icons_alpha.py reimports only the nine existing texture assets, preserves alpha, sets UI/no-mipmap compression settings and a 256-pixel texture limit, then exports each imported asset for an independent alpha audit.
- Scripts/Verification/verify_clothing_icon_alpha_play.py checks actual Inventory references and captures bright shoreline and dim ship-deck views at 1920×1080 and 1280×720.

## Verification

All nine final sources are RGBA with alpha ranging from 0 to 255 and fully transparent corners. Exports from the resulting Unreal texture assets also passed those alpha checks; the audit is Saved/ClothingIconAlpha/ExportAlphaAudit.json. Import/reference results are Saved/ClothingIconAlpha/ImportResult.json.

The final Play pass passed all **23 checks**. All nine runtime textures are **156×156**, within the configured 256-pixel UI limit. The four real Play captures were visually inspected: the dark rectangles are absent around Inventory and recipe icons on both backgrounds. Results are in Saved/ClothingIconAlphaPlayResult.json; the combined report is Saved/ClothingIconAlphaReviewSummary.json.

The views use temporary PIE inventories, teleports and scene-light settings, with original light values restored before closing. No normal survivor save, equipment transaction or persistent map change is involved. No renderer memory-budget setting was changed.

Python syntax and scoped whitespace checks passed. No gameplay C++ was edited or rebuilt for this asset-only task.

## Remaining differences

The original Fur Hood, Fur Jacket and Fur Pants crops already cut off portions of their source artwork. Those same crop boundaries remain; missing parts were not invented. These edits are not a claim of pixel-identical foregrounds or finished production garment art.

Long Inventory item captions still clip, including some clothing names at 1080p and 720p. Full recipe names remain on the recipe tiles. This is a separate readability follow-up; no layout, header or typography redesign was included here.

Equipment remains unapproved in the owner's normal play experience. The separate packaged EXE has not been updated. Nothing was committed or published.
