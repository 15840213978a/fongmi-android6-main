#!/usr/bin/env python3
"""Import the pinned upstream tree once, preserving reviewed repository overlays."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

SOURCE_COMMIT = "0b9835bd0c5350f47476c05377545d6e9134614c"
ROOT = Path(__file__).resolve().parents[1]
MARKER = ROOT / ".upstream-568"


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root)


def main():
    if MARKER.exists():
        if MARKER.read_text().strip() != SOURCE_COMMIT:
            raise SystemExit("Unexpected upstream marker; refusing another import")
        print("Pinned 5.6.8 source is already imported")
        return
    source = Path(sys.argv[1]).resolve()
    if git(source, "rev-parse", "HEAD").decode().strip() != SOURCE_COMMIT:
        raise SystemExit("Upstream commit does not match the reviewed revision")
    keep = set(json.loads((ROOT / ".upgrade-overlays.json").read_text()))
    keep.update({"scripts/import_568.py", ".upgrade-overlays.json",
                 "scripts/verify_upgrade_apks.py", "UPGRADE-5.6.8.md"})

    def preserved(path):
        return path in keep or path.startswith(".github/workflows/") or path.startswith("docs/superpowers/")

    old = git(ROOT, "ls-files", "-z").decode().split("\0")
    for name in filter(None, old):
        if not preserved(name):
            (ROOT / name).unlink(missing_ok=True)
    imported = []
    entries = git(source, "ls-tree", "-rz", "HEAD").decode().split("\0")
    for entry in filter(None, entries):
        meta, name = entry.split("\t", 1)
        mode, kind, sha = meta.split()
        if preserved(name):
            continue
        if kind != "blob":
            raise SystemExit(f"Unsupported upstream entry: {name}")
        target = ROOT / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if mode == "120000":
            target.symlink_to(os.readlink(source / name))
        else:
            shutil.copyfile(source / name, target)
            target.chmod(0o755 if mode == "100755" else 0o644)
        imported.append(name)
    # Explicit source paths ensure all tracked Gradle properties and native libs
    # are retained even if a repository ignore pattern would otherwise hide them.
    subprocess.run(["git", "add", "-f", "--pathspec-from-file=-", "--pathspec-file-nul"],
                   cwd=ROOT, input="\0".join(imported).encode() + b"\0", check=True)
    subprocess.run(["git", "add", "-u"], cwd=ROOT, check=True)
    MARKER.write_text(SOURCE_COMMIT + "\n")
    subprocess.run(["git", "add", ".upstream-568"], cwd=ROOT, check=True)
    print(f"Imported {len(imported)} paths from {SOURCE_COMMIT}")


if __name__ == "__main__":
    main()
