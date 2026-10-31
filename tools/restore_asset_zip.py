#!/usr/bin/env python3
"""Validate and restore privately supplied original game resources."""
import argparse
import shutil
from pathlib import Path, PurePosixPath
from zipfile import ZipFile, BadZipFile

REQUIRED = [
    "nitrofiles/models/MaleBody.msp", "nitrofiles/models/FemaleBody.msp",
    "nitrofiles/cfl/CFL_Res.dat", "nitrofiles/models/MaleBody.bin",
    "nitrofiles/models/FemaleBody.bin", "nitrofiles/models/MaleBody.ani",
    "nitrofiles/models/FemaleBody.ani", "nitrofiles/ui/EditBody.rgb555",
    "nitrofiles/ui/home-bottom.rgb555", "nitrofiles/ui/profile.rgb555",
    "nitrofiles/ui/import-bottom.rgb555", "nitrofiles/ui/qr-menu-ds.rgb555",
    "nitrofiles/ui/qr-menu-dsi.rgb555", "nitrofiles/ui/photo-select.rgb555",
    "nitrofiles/art/StatusPersonal.bin", "nitrofiles/art/StatusFavorite.bin",
    "nitrofiles/font/number.bin", "assets/ui/original-icon.gif",
]

def validate(archive, destination=None):
    try:
        with ZipFile(archive) as z:
            items = {}
            for entry in z.infolist():
                name = entry.filename
                path = PurePosixPath(name)
                mode = entry.external_attr >> 16
                if (path.is_absolute() or ".." in path.parts or "\\" in name or
                        (mode & 0o170000) == 0o120000):
                    raise ValueError("Unsafe ZIP entry: " + name)
                if entry.is_dir():
                    continue
                if name in items:
                    raise ValueError("Duplicate ZIP entry: " + name)
                items[name] = entry
            missing = [name for name in REQUIRED if name not in items or not items[name].file_size]
            if missing:
                raise ValueError("Missing or empty required resources: " + ", ".join(missing))
            invalid = z.testzip()
            if invalid:
                raise ValueError("ZIP CRC mismatch: " + invalid)
            if destination:
                root = Path(destination).absolute()
                if root.is_symlink():
                    raise ValueError("Unsafe resource destination: symbolic link")
                for name, entry in items.items():
                    if not name.startswith(("nitrofiles/", "assets/")):
                        continue
                    parts = PurePosixPath(name).parts
                    parent = root
                    # A pre-existing symbolic-link directory can escape the
                    # source tree even when every ZIP member name is safe.
                    for component in parts[:-1]:
                        parent = parent / component
                        if parent.is_symlink():
                            raise ValueError("Unsafe resource destination link: " + str(parent))
                        parent.mkdir(exist_ok=True)
                    out = parent / parts[-1]
                    if out.is_symlink():
                        raise ValueError("Unsafe resource destination link: " + str(out))
                    with z.open(entry) as inp, out.open("wb") as dest:
                        shutil.copyfileobj(inp, dest)
            print(f"PASS: {len(items)} files, {len(REQUIRED)} required resource paths")
            return 0
    except (OSError, BadZipFile, ValueError) as error:
        print("FAIL:", error)
        return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--extract-to", type=Path)
    args = parser.parse_args()
    raise SystemExit(validate(args.archive, args.extract_to))
