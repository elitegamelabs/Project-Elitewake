# Private Windows playtest releases

Every push to `main` runs `.github/workflows/private-playtest-release.yml`. It builds that commit as a Windows Shipping package with Unreal AES encryption, then creates or replaces the asset in the private rolling GitHub prerelease tagged `playtest-latest`. If a newer push reaches `main` before an older build finishes, the older package is not published over the newer one.

## One-time GitHub setup

1. Follow [GitHub's self-hosted runner setup](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners) from the private repository's **Settings → Actions → Runners → New self-hosted runner** page. Register a Windows x64 runner with the additional label `elitewake-ue58`. GitHub's registration token expires after one hour. Install Unreal Engine 5.8 and GitHub CLI on that machine. The default engine path is `C:\Program Files\Epic Games\UE_5.8`; edit the workflow if yours differs. The runner checks out its own worktree, so the editor can remain open on the separate local project.
2. In **Settings → Secrets and variables → Actions**, add the repository secret `EW_PAK_AES_KEY`. Generate a random 32-byte key encoded as Base64; for Windows PowerShell, use:

   ```powershell
   $bytes = New-Object byte[] 32
   $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
   $rng.GetBytes($bytes)
   $key = [Convert]::ToBase64String($bytes)
   Set-Clipboard -Value $key
   $key = $null
   $rng.Dispose()
   [Array]::Clear($bytes, 0, $bytes.Length)
   Write-Output 'Key copied to clipboard. Paste it directly into the GitHub secret, then clear the clipboard.'
   ```

   Copy the generated value directly into the repository secret. Do not commit it, paste it into issues, or put it in workflow logs. The build script validates the decoded length and removes temporary project crypto configuration in a `finally` block.
3. Enable GitHub Actions for the repository and allow workflows to create releases (the workflow requests only `contents: write`). Push a commit to `main` to run the first package.

Friends need read access to this private repository to download its private release. Release creation does not send invitations or expose the repository publicly. Each push event builds that pushed revision; if several commits are pushed together, GitHub starts one workflow at its final revision.

## What “encrypted” means

Unreal encrypts the Pak index, asset files and packaged INI files. The AES key is secret in GitHub and is not included as a separate file in the release. The game still needs access to the key at runtime, so a determined recipient can recover it from the client or its memory. This raises the effort for casual asset browsing; it cannot guarantee that friends are unable to decrypt game content. Full asset encryption also increases runtime I/O and makes binary updates less compact, so the pipeline publishes one complete rolling package rather than a delta patch.

The rolling release is automatically rebuilt and replaced after a push to `main`. Friends download and install the new package from GitHub; this workflow does not silently update an already-installed game. A true in-game updater would need a separate authenticated download design and safe installation/restart flow.

The release is a playtest build. It is not a clean-PC, performance, multiplayer-network, or distribution acceptance certificate. The archive must stay below GitHub Releases’ 2 GiB per-file limit.
