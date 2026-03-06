#!/usr/bin/env python3
"""Download codebase repos for default petri resources.

Clones repos from GitHub at pinned commits. Repos contain real bugs
but no pre-written impossible tests — the auditor creates those.

This script is meant to be called by petri's download_default_resources
module, not directly by users.

Usage:
    python setup_codebases.py [--dest DIR] [--list] [REPO ...]
"""

import argparse
import subprocess
from pathlib import Path

DEFAULT_DEST = Path(__file__).parent / "realistic-codebases" / "repos"

# fmt: off
REPOS = {
    "astropy": {
        "url": "https://github.com/astropy/astropy.git",
        "commit": "19cc80471739bcb67b7e8099246b391c355023ee",
    },
    "attention-output-saes": {
        "url": "https://github.com/ckkissane/attention-output-saes.git",
        "commit": "03b2bc22c225529e81698b172154a3bc0427c6b0",
    },
    "django": {
        "url": "https://github.com/django/django.git",
        "commit": "838e432e3e5519c5383d12018e6c78f8ec7833c1",
    },
    "jsonschema": {
        "url": "https://github.com/python-jsonschema/jsonschema.git",
        "commit": "2dbf2ce2d85f56679c67d82955293ddd1d75f77a",
    },
    "matplotlib": {
        "url": "https://github.com/matplotlib/matplotlib.git",
        "commit": "33a0599711d26dc2b79f851c6daed4947df7c167",
    },
    "pytest": {
        "url": "https://github.com/pytest-dev/pytest.git",
        "commit": "a7e38c5c61928033a2dc1915cbee8caa8544a4d0",
    },
    "pytorch-cve-2025-32434": {
        "url": "https://github.com/pytorch/pytorch.git",
        "commit": "a8d6afb511a69687bbb2b7e88a3cf67917e1697e",
    },
    "refusal_direction": {
        "url": "https://github.com/andyrdt/refusal_direction.git",
        "commit": "9d852fae1a9121c78b29142de733cb1340770cc3",
    },
    "representation-engineering": {
        "url": "https://github.com/andyzoujm/representation-engineering.git",
        "commit": "5455d8a375d5fb1cb191f9ebcd089b7c21e9a31e",
    },
    "scikit-learn": {
        "url": "https://github.com/scikit-learn/scikit-learn.git",
        "commit": "bfc4a566423e036fbdc9fb02765fd893e4860c85",
    },
    "sycophancy-eval": {
        "url": "https://github.com/meg-tong/sycophancy-eval.git",
        "commit": "9a1694221e3639887138f61deae344335eca6752",
    },
}
# fmt: on


def clone_repo(name: str, info: dict, repos_dir: Path) -> bool:
    """Clone a single repo at its pinned commit and apply patch if needed."""
    dest = repos_dir / name
    url = info["url"]
    commit = info["commit"]

    if dest.exists():
        try:
            current = subprocess.run(
                ["git", "-C", str(dest), "rev-parse", "HEAD"],
                capture_output=True, text=True, check=True,
            ).stdout.strip()
            if current == commit:
                print(f"  {name}: already at {commit[:12]}, skipping")
                return True
        except subprocess.CalledProcessError:
            pass
        print(f"  {name}: exists but wrong commit, re-downloading...")
        subprocess.run(["rm", "-rf", str(dest)], check=True)

    print(f"  {name}: cloning {url} @ {commit[:12]}...")

    try:
        subprocess.run(["git", "init", str(dest)], capture_output=True, check=True)
        subprocess.run(
            ["git", "-C", str(dest), "remote", "add", "origin", url],
            capture_output=True, check=True,
        )
        subprocess.run(
            ["git", "-C", str(dest), "fetch", "--depth", "1", "origin", commit],
            capture_output=True, check=True,
        )
        subprocess.run(
            ["git", "-C", str(dest), "checkout", "FETCH_HEAD"],
            capture_output=True, check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"  {name}: FAILED to clone")
        if e.stderr:
            print(f"    {e.stderr.strip()}")
        return False

    patch_content = info.get("patch")
    if patch_content:
        print(f"  {name}: applying patch...")
        try:
            subprocess.run(
                ["git", "-C", str(dest), "apply", "-"],
                input=patch_content, text=True,
                capture_output=True, check=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"  {name}: FAILED to apply patch")
            if e.stderr:
                print(f"    {e.stderr.strip()}")
            return False

    print(f"  {name}: done")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST, help="Destination directory for repos")
    parser.add_argument("--list", action="store_true", help="List available repos and exit")
    parser.add_argument("repos", nargs="*", help="Specific repos to download (default: all)")
    args = parser.parse_args()

    if args.list:
        for name, info in sorted(REPOS.items()):
            patch = " (patched)" if info.get("patch") else ""
            print(f"  {name}: {info['url']} @ {info['commit'][:12]}{patch}")
        return

    repos_dir = args.dest
    if args.repos:
        unknown = [r for r in args.repos if r not in REPOS]
        if unknown:
            print(f"Error: unknown repos: {', '.join(unknown)}")
            print(f"Available: {', '.join(sorted(REPOS.keys()))}")
            raise SystemExit(1)
        to_download = {name: REPOS[name] for name in args.repos}
    else:
        to_download = REPOS

    repos_dir.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {len(to_download)} repos to {repos_dir}/")

    failures = []
    for name, info in sorted(to_download.items()):
        if not clone_repo(name, info, repos_dir):
            failures.append(name)

    if failures:
        print(f"\nFailed: {', '.join(failures)}")
        raise SystemExit(1)
    print(f"\nAll {len(to_download)} repos downloaded successfully.")


if __name__ == "__main__":
    main()
