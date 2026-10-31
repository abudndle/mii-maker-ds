#!/usr/bin/env python3
"""Create UNPLAYABLE, fictional compile-only NitroFS inputs in GitHub Actions.

This helper must never be used to produce a playable release. Its purpose is
only to test the real BlocksDS compiler/linker and the ROM packing toolchain
without obtaining or exposing any original Nintendo files.
"""
import base64
import os
from pathlib import Path

from restore_asset_zip import REQUIRED
from verify_runtime_assets import source_paths

ROOT = Path(__file__).resolve().parents[1]
# Fictional 32x32 monochrome GIF for ndstool banner input.
CI_ICON = ("R0lGODdhIAAgAIEAAAAAAP///wAAAAAAACwAAAAAIAAgAEAIgQABCBxIsKDBgwgDBEDIcKDChAsTNnx4kGJDiBAVatzIsaPFgh8dbsRYMeLFkidTqlzJUmDIlS9dmmwZE0BNmxNnErypE2RPmS1FZvRItGPQo0iTKt1ZtOlIlEdr3rwo9WfKqgytAoVaMSfJrlmt8vTKlaZYrVTPIq3q1OnSt0kDAgA7")
PREFIX = b"CI FIXTURE / NOT NINTENDO DATA / NOT PLAYABLE\0"


def generate(root=ROOT, environ=None):
    env = os.environ if environ is None else environ
    if env.get("CI") != "true" or env.get("MDS_SYNTHETIC_COMPILE_ONLY") != "yes":
        raise ValueError("Synthetic resources restricted to explicit CI compile smoke")
    root = Path(root)
    paths, _ = source_paths(root)
    paths.update(p[len("nitrofiles/"):] for p in REQUIRED if p.startswith("nitrofiles/"))
    source = root / "nitrofiles"
    if source.exists() and any(source.iterdir()):
        raise ValueError("refusing to overwrite existing/private NitroFS directory")
    icon = root / "assets/ui/original-icon.gif"
    if icon.exists():
        raise ValueError("refusing to overwrite existing/private game icon")
    if (root / "mii-ds.nds").exists():
        raise ValueError("refusing to overwrite an existing ROM")
    for name in sorted(paths):
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if name.startswith("ui/") and name.endswith(".rgb555"):
            payload = b"\0" * (256 * 192 * 2)
        elif name.startswith("art/") and name.endswith(".bin"):
            payload = b"\x01\x00\x01\x00\x00\x80"  # 1x1 RGB555 icon
        else:
            payload = PREFIX + name.encode("ascii")
        path.write_bytes(payload)
    icon.parent.mkdir(parents=True, exist_ok=True)
    icon.write_bytes(base64.b64decode(CI_ICON))
    return len(paths)


if __name__ == "__main__":
    try:
        count = generate()
    except (OSError, ValueError) as exc:
        raise SystemExit(f"FAIL: fictional compile inputs: {exc}")
    print(f"FIXTURE ONLY: {count} synthetic NitroFS entries; resulting .nds is NOT playable")
