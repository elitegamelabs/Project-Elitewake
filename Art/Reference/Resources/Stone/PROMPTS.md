# Stone six-view prompts
Status: prompts prepared; images pending unless generation.json explicitly records actual files.
Reference sample, not a new inventory item or approved gameplay asset.

## Shared identity — repeat verbatim
One small isolated harvested stone material sample, matching existing approved source art and natural surface structure. No new species, resource tier or gameplay effect. The same exact object and markings across views. Photorealistic material reference, neutral plain background, even diffuse lighting, full sample visible, no scenery, labels, text, people or watermark. No icon replacement.

## Camera suffixes
- front.png: strict orthographic front elevation, full sample visible. Preserve exact specimen identity.
- back.png: strict orthographic rear elevation, full sample visible. Preserve exact specimen identity.
- left.png: strict orthographic left end/profile, full sample visible. Preserve exact specimen identity.
- right.png: strict orthographic right end/profile, full sample visible. Preserve exact specimen identity.
- top.png: strict orthographic direct overhead, full sample visible. Preserve exact specimen identity.
- underside.png: strict orthographic direct view from below, full sample visible. Preserve exact specimen identity.

## Production check
Inspect against the selected source specimen, not six independent variants. Flat/transparent material views require the carrier/sample convention stated above. No environment textures or scenery composition. All counts, IDs and harvesting behavior remain separate code/data work.

## Pilot sheet (Claude, 2026-10-25) — proposal only, not an approved reference
- File: `SixView-Sheet-v1.png` (2400x1600, one 3x2 sheet). Model `model_openai-gpt-image-2-5-flare`, quality high, 2 CU, Scenario asset `asset_Q7Pby6optQ3VK5ZnF7NUkMX2`. Prompt: the shared identity above plus "six strict orthographic views of the SAME stone in a 3x2 grid: front, back, left, right, top, underside".
- What it shows: six photoreal views of rough gray granite-like stone, speckled dark gray and pale grain with tan staining, chipped edges, a few hairline cracks, on mid-gray ground. Surface quality is good for a material reference.
- Defects: the six cells are NOT one exact stone seen from six sides. Outlines differ per cell (blocky, rounded, tall and narrow), and the views are three-quarter, not orthographic. Do not use it as a modeling turnaround. Use only as a surface/colour reference.
- Status: concept proposal; not imported, no gameplay or icon change.

## Code-built six views (Claude, 2026-10-25) — proposal, replaces the pilot sheet above
- Files: `front.png back.png left.png right.png top.png underside.png` (1024 px each) and `SixView-Sheet-v2.png` (3x2 contact sheet). Built by `Scripts/Art/render_rock_sixview.py <preset>` (numpy + Pillow, no AI service, free, repeatable): one signed-distance rock ray-marched from six exact orthographic directions, so all views are the same object.
- Shape: a long, low pebble (about 1 : 0.74 : 0.55) with nine flat chip facets and slightly rounded edges, plus low-frequency lumps. Surface: speckled gray granite grain (pale and dark flecks), faint warm tan staining, mid-gray background, light from the camera's upper left in every view.
- Limits: reads smoother and more stylised than a photograph; no cracks or fine pitting yet. Concept reference only, not a mesh, texture or icon replacement.
- The two Scenario pilot images (hero front and back, 4 CU extra, `asset_QubWoezEYKzsbQHebeb2GRKM`, `asset_iedJ9vcEh4Br8syoiKcNJ66i`) were not used.
