# Sandstone six-view prompts
Status: prompts prepared; images pending unless generation.json explicitly records actual files.
Reference sample, not a new inventory item or approved gameplay asset.

## Shared identity — repeat verbatim
One small isolated harvested sandstone material sample, matching existing approved source art and natural surface structure. No new species, resource tier or gameplay effect. The same exact object and markings across views. Photorealistic material reference, neutral plain background, even diffuse lighting, full sample visible, no scenery, labels, text, people or watermark. No icon replacement.

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
- Files: `front.png back.png left.png right.png top.png underside.png` (768 px) and `SixView-Sheet-v2.png`. Built by `python Scripts/Art/render_rock_sixview.py sandstone <folder> 768` (numpy + Pillow, no AI service): one chipped rock shape ray-marched from six exact orthographic directions, so every view is the same specimen. Mid-gray background, light from the camera's upper left.
- Colouring follows the shared identity above (preset `sandstone` in the script). Reads stylised rather than photographic; no fine cracks or pitting. Concept reference only: not a mesh, texture or icon replacement, and no gameplay rule is implied.
