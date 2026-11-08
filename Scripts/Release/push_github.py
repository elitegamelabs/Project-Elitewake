"""Push main to GitHub (owner, November 7). Run from the repository root:
    python Scripts/Release/push_github.py

The project keeps every file as an ordinary Git file: no Git LFS (the GitHub account's LFS allowance is full), and the
history was started afresh on November 7. GitHub refuses a file of 100 MB or more and a single push of more than 2 GB,
so this stops on any file of 95 MB or more in the commits to push, and pushes commit by commit when the whole would be
too large. It never force-pushes.
"""
import subprocess
import sys

LIMIT = 95 * 1000 * 1000
PUSH_LIMIT = 1_500_000_000      # under GitHub's 2 GB per push, with room


def git(*args, check=True):
    result = subprocess.run(['git', *args], capture_output=True, text=True)
    if check and result.returncode:
        sys.exit(f'git {" ".join(args)} failed:\n{result.stdout}{result.stderr}')
    return result.stdout


def added_bytes(commit):
    """Size of the files a commit adds or changes, and any too large for GitHub."""
    total, too_big = 0, []
    listing = git('diff-tree', '-r', '--root', '--no-renames', '--no-commit-id', commit)
    for line in listing.splitlines():
        if not line.startswith(':'):
            continue
        meta, path = line.split('\t', 1)
        blob = meta.split()[3]
        if set(blob) == {'0'}:
            continue                                   # deleted
        size = int(git('cat-file', '-s', blob))
        total += size
        if size >= LIMIT:
            too_big.append((size, path))
    return total, too_big


def main():
    if git('status', '--porcelain', '--untracked-files=no').strip():
        sys.exit('Commit or set aside the changes in the work tree first.')
    remote = git('ls-remote', 'origin', 'refs/heads/main').split()
    base = remote[0] if remote else None
    if base and subprocess.run(['git', 'merge-base', '--is-ancestor', base, 'main']).returncode:
        sys.exit('origin/main is not an ancestor of main: refusing (this script never force-pushes).')
    commits = git('rev-list', '--reverse', 'main' if not base else f'{base}..main').split()
    if not commits:
        print('Nothing to push.')
        return
    sizes = []
    for commit in commits:
        total, too_big = added_bytes(commit)
        if too_big:
            sys.exit('Too large for GitHub (keep local or split):\n' + '\n'.join(f'  {s / 1e6:.0f} MB  {p}' for s, p in too_big))
        sizes.append(total)
    batches, current, running = [], [], 0
    for commit, size in zip(commits, sizes):
        if current and running + size > PUSH_LIMIT:
            batches.append(current[-1])
            current, running = [], 0
        current.append(commit)
        running += size
    batches.append(current[-1])
    for i, tip in enumerate(batches, 1):
        ref = 'main' if tip == commits[-1] else tip
        print(f'push {i}/{len(batches)}: up to {tip[:8]}')
        out = subprocess.run(['git', 'push', 'origin', f'{ref}:refs/heads/main'], capture_output=True, text=True)
        print(out.stdout + out.stderr)
        if out.returncode:
            sys.exit(out.returncode)


if __name__ == '__main__':
    main()
