# Birch Wood six-view prompts
Status: prompts prepared; images pending unless generation.json explicitly records actual files.
Reference sample, not a new inventory item or approved gameplay asset.

## Shared identity — repeat verbatim
Short birch timber section with pale fine-grained cut end and white papery bark with dark lenticels. The same exact object and markings across views. Photorealistic material reference, neutral plain background, even diffuse lighting, full sample visible, no scenery, labels, text, people or watermark. No icon replacement.

## Camera suffixes
- front.png: strict orthographic front elevation, full sample visible. Preserve exact specimen identity.
- back.png: strict orthographic rear elevation, full sample visible. Preserve exact specimen identity.
- left.png: strict orthographic left end/profile, full sample visible. Preserve exact specimen identity.
- right.png: strict orthographic right end/profile, full sample visible. Preserve exact specimen identity.
- top.png: strict orthographic direct overhead, full sample visible. Preserve exact specimen identity.
- underside.png: strict orthographic direct view from below, full sample visible. Preserve exact specimen identity.

## Production check
Inspect against the selected source specimen, not six independent variants. Flat/transparent material views require the carrier/sample convention stated above. No environment textures or scenery composition. All counts, IDs and harvesting behavior remain separate code/data work.

## Code-built six views (Claude, 2026-10-25) — proposal
- Files: `front.png back.png left.png right.png top.png underside.png` (768 px) and `SixView-Sheet-v2.png`. Built by `python Scripts/Art/render_timber_sixview.py birch <folder> 768` (numpy + Pillow, no AI service): one short round timber section (bark on the side, sawn ends with the species' end grain: rings, checks, pores or fibre dots), ray-marched from six exact orthographic directions, so every view is the same piece. Left and right are the two sawn ends; front/back/top/underside show the bark.
- Reads stylised, not photographic; the bark relief is subtle. Concept reference only: not a mesh, texture or icon replacement; generic Wood stays one inventory identity.
