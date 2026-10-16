# ELITEWAKE Safe Storage-Cleanup Policy for AI Agents

Owner goal: reclaim local disk space without damaging the Unreal Engine project or losing valuable work. This is a cleanup and audit policy, not permission to delete files blindly.

## Mandatory workflow
1. Inspect before changing anything. Identify the actual project root, Unreal Engine version (currently UE 5.8), source-control status, large directories/files, file purpose, and last-modified context. Report the biggest safe candidates and estimated space savings.
2. Prefer reversible cleanup. Use the engine's supported cleanup tools or move candidate files to a clearly named quarantine/review folder outside the project before permanent deletion, where practical. Never empty the Recycle Bin or permanently purge backups without explicit owner approval.
3. Check Git status and backups before touching tracked files. Never overwrite or discard user changes. Do not run broad recursive delete commands, wildcard deletion, or scripts that delete files without an explicit, reviewed candidate list.
4. Before any deletion, present a short plan listing exact paths, why each item is believed safe to remove, expected space recovered, and risks. If a file's purpose or regenerability is uncertain, leave it alone and ask.
5. After approved cleanup, verify the project still opens/builds as applicable, source control changes are expected, and no required content is missing. Report exactly what was removed, what was retained, and measured space recovered. Do not claim cleanup succeeded until verified.

## Usually safer candidates (verify locally first)
- Re-creatable caches such as project-local DerivedDataCache and temporary shader/build caches, after confirming Unreal is closed and the cache can be regenerated.
- Re-creatable intermediate build output, generated binaries, logs, crash reports, and temporary exports that are not needed for diagnosis or release packaging.
- Duplicate downloads, obsolete temporary renders, and intermediate files only after confirming a canonical source/approved version exists elsewhere.
- Old packaged builds/installer archives only after confirming they are not the sole copy needed for testing, distribution, or rollback.

## High-risk paths and content: do not delete without explicit owner approval
- `Content/`, source art, meshes, textures, materials, animations, audio, maps/levels, Blueprints, source code, plugins, configuration, project files, or any assets referenced by the game.
- `Config/`, `Source/`, `Plugins/`, `.uproject`, project/build scripts, input settings, asset registries, and repository documentation.
- `Saved/SaveGames`, user saves, settings, autosaves, screenshots, recordings, crash dumps needed for debugging, and test evidence.
- Git history, branches, uncommitted changes, source assets, unique concept art, generated assets not yet backed up, and any file that may be the only copy.
- Anything outside the known ELITEWAKE project root or in another project/user folder.

## Unreal-specific caution
- `Binaries/`, `Intermediate/`, and `DerivedDataCache/` are often regenerable, but inspect the exact project and local workflow first. Regeneration costs time and can require toolchains; generated binaries may be needed by a non-programmer or a current build.
- `Saved/` is mixed-use. It can contain disposable logs/cache as well as valuable save games, autosaves, screenshots, crash diagnostics, and local configuration. Never delete the whole directory.
- Never delete `Content/` or source art to save space just because assets are large. Instead identify unused assets through reference/dependency checks and ask the owner before removal.
- Do not commit local caches or temporary files to Git as part of cleanup. Do not remove tracked files from the repository merely to reclaim local disk space; first distinguish local-only generated files from shared project content.

## Scope and permissions
- AI agents may audit, measure, explain, and propose cleanup candidates without approval.
- No permanent deletion of uncertain files, tracked project content, unique assets, saves, backups, or anything outside the project root without explicit owner approval.
- If the user has not approved specific deletions, stop after producing a ranked cleanup proposal; do not treat “clean up space” as blanket permission to remove files.
- Respect the existing file ownership/delegation rules and do not run competing Unreal Editor/build operations.
