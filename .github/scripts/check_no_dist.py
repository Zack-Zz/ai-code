"""Reject tracked temporary distribution output, including force-added files."""

import argparse
from pathlib import Path
import subprocess


def check(root):
    result = subprocess.run(["git", "ls-files", "-z", "--", "dist"], cwd=root,
                            capture_output=True, check=True)
    if result.stdout:
        raise ValueError("dist/ must not contain tracked files")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        check(args.root)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"tracked dist check failed: {exc}")
        return 1
    print("no tracked dist/ files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
