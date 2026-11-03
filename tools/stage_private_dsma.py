#!/usr/bin/env python3
"""Stage private DSMA artifacts for the isolated Nitro Engine test ROM.

No original assets are stored in Git. DSM/DSA remain private; this tool only
copies user-provided converted artifacts into the gitignored NitroFS directory.
"""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "hardware3d" / "nitrofiles" / "models"
MAX_BYTES = 8 * 1024 * 1024
NAMES = ("MiiBody_dsm.bin", "MiiBody_dsa.bin")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def stage(model, animation, target=TARGET):
    """Copy two nonempty, bounded private artifacts, refusing unsafe targets."""
    target = Path(target)
    allowed = (ROOT / "hardware3d" / "nitrofiles").resolve()
    # The destination may not escape the private NitroFS subtree via symlinks.
    if not target.resolve().is_relative_to(allowed):
        raise ValueError("Refusing to stage outside ignored hardware3d/nitrofiles")
    sources = (Path(model), Path(animation))
    payloads = []
    for path in sources:
        if path.is_symlink() or not path.is_file():
            raise ValueError("Source must be a regular, non-symlink file")
        size = path.stat().st_size
        if not 0 < size <= MAX_BYTES:
            raise ValueError("Private DSMA artifact must be nonempty and <= 8 MiB")
        payload = path.read_bytes()
        if len(payload) != size:
            raise ValueError("Source changed while being read")
        payloads.append(payload)
    if target.exists() and target.is_symlink():
        raise ValueError("Symlink destination is forbidden")
    target.mkdir(parents=True, exist_ok=True, mode=0o700)
    for name, payload in zip(NAMES, payloads):
        destination = target / name
        if destination.is_symlink():
            raise ValueError("Destination file symlink is forbidden")
        if destination.exists() and not destination.is_file():
            raise ValueError("Destination is not a regular file")
        with tempfile.NamedTemporaryFile(dir=target, prefix=".staging-",
                                         delete=False) as out:
            temp = Path(out.name)
            try:
                os.chmod(temp, 0o600)
                out.write(payload)
                out.flush()
                os.fsync(out.fileno())
            except BaseException:
                temp.unlink(missing_ok=True)
                raise
        try:
            os.replace(temp, destination)
        finally:
            temp.unlink(missing_ok=True)
    return [(name, digest(data)) for name, data in zip(NAMES, payloads)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True,
                        help="Private md5_to_dsma DSM output")
    parser.add_argument("--animation", type=Path, required=True,
                        help="Private md5_to_dsma DSA output")
    args = parser.parse_args()
    for name, sha in stage(args.model, args.animation):
        print(f"Staged {name} SHA-256 {sha}")
    print("Private files are ignored by Git; run make nitro-3d-preview locally.")
    print("Staging does not verify original UVs, animation fidelity or hardware.")


if __name__ == "__main__":
    main()
