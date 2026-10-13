# Project guide

## Local packaging

`Scripts/Verification/build_private_windows.ps1` builds a Windows Development package for local diagnostics. Close Unreal Editor and EW test games before using this local package script.

## Private release automation

`.github/workflows/private-playtest-release.yml` builds Windows Shipping packages and updates the private rolling GitHub prerelease on pushes to `main`. It requires a Windows x64 self-hosted runner labeled `elitewake-ue58`, Unreal Engine 5.8, GitHub CLI, Actions release permissions and the `EW_PAK_AES_KEY` repository secret. Setup and encryption limitations are documented in [PRIVATE_RELEASE_AUTOMATION.md](PRIVATE_RELEASE_AUTOMATION.md). This automation has not run yet. It does not silently update already installed copies; friends download each new release.

Never commit credentials or download keys. Friends need repository read access to download the private release.
