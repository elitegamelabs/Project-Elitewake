# Copy/Paste Prompt: Safe ELITEWAKE Disk-Space Audit

You are helping with the ELITEWAKE Unreal Engine 5.8 project. My local files are taking up too much disk space. Your job is to help reclaim storage safely, without damaging the project or losing unique work.

First, inspect the actual project root, current Git status/changes, and the largest folders/files. Identify what each candidate is for and whether it can safely be regenerated. Rank the candidates by likely space savings and risk. Give me the exact paths, approximate sizes, reason they may be removable, dependencies/risks, and expected savings.

Follow `Docs/SAFE_STORAGE_CLEANUP_POLICY.md` and the existing AI instructions:
- Do not delete anything during the initial audit.
- Do not use broad recursive deletion, wildcards, or unreviewed cleanup scripts.
- Do not delete Content, source code, Blueprints, maps, project/config files, plugins, source art, unique generated assets, or referenced assets just because they are large.
- Never delete the entire Saved folder. It may contain save games, autosaves, screenshots, diagnostics, and local settings.
- Treat Binaries, Intermediate, and DerivedDataCache as potentially regenerable only after checking the exact project and current workflow.
- Preserve uncommitted user work, Git history, backups, and any file that might be the only copy.
- Do not touch files outside the confirmed ELITEWAKE project root.
- Prefer reversible cleanup or quarantine where practical; do not empty the Recycle Bin or permanently purge backups.
- If a candidate's purpose or safety is uncertain, leave it untouched and explain what needs checking.
- Do not modify or delete tracked repository files merely to reclaim local disk space.

Stop after presenting the ranked cleanup proposal and wait for my approval of the exact paths before any deletion. After an approved cleanup, verify the project remains intact and report exactly what changed and how much space was actually recovered. Do not claim that you inspected local files unless you truly have access to them.
