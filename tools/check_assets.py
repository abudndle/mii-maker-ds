#!/usr/bin/env python3
"""Fail clearly before packing a ROM without valid locally supplied resources."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
required = ["nitrofiles/models/MaleBody.msp","nitrofiles/models/FemaleBody.msp","nitrofiles/cfl/CFL_Res.dat","nitrofiles/models/MaleBody.bin","nitrofiles/models/FemaleBody.bin","nitrofiles/models/MaleBody.ani","nitrofiles/models/FemaleBody.ani","nitrofiles/ui/EditBody.rgb555","nitrofiles/ui/home-bottom.rgb555","nitrofiles/ui/profile.rgb555","nitrofiles/ui/import-bottom.rgb555","nitrofiles/ui/qr-menu-ds.rgb555","nitrofiles/ui/qr-menu-dsi.rgb555","nitrofiles/ui/photo-select.rgb555","nitrofiles/art/StatusPersonal.bin","nitrofiles/art/StatusFavorite.bin","nitrofiles/art/Select/IconFavorite.bin","nitrofiles/art/Select/IconMyMii.bin","nitrofiles/art/Select/IconCopyB.bin","nitrofiles/art/Select/IconOpen.bin","nitrofiles/font/number.bin","assets/ui/original-icon.gif","source/ui_generated.h","source/ui_hits.h","source/menu_generated.h","source/profile_generated.h","source/ui_font.h"]

def validate(root=ROOT, allow_test_import=False):
    errors = []
    for relative in required:
        path = Path(root) / relative
        if path.is_symlink():
            errors.append(f"{relative}: must be a regular private file, not a symlink")
        elif not path.is_file():
            errors.append(f"{relative}: missing or not a regular file")
        elif path.stat().st_size == 0:
            errors.append(f"{relative}: file is empty")
    fixture = Path(root) / "nitrofiles/test-import"
    if fixture.exists() and not allow_test_import:
        errors.append("Move the test-import fixture folder outside nitrofiles before a production build.")
    return errors

def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    errors = validate(allow_test_import="--allow-test-import" in argv)
    if errors:
        print("Required local Mii Maker resources failed integrity checks:", file=sys.stderr)
        for error in errors:
            print("  " + error, file=sys.stderr)
        print("Supply authorized original resources or regenerate project headers. CFL_DB.dat is not used.", file=sys.stderr)
        return 1
    print(f"PASS: {len(required)} required private resources are regular, non-empty files.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
