"""Reject stale ROMs when private build commands report success without writing output."""
from pathlib import Path


def clear_old_rom(path):
    path = Path(path)
    if path.is_symlink():
        raise ValueError("ROM output path must not be a symlink")
    if path.exists():
        if not path.is_file():
            raise ValueError("ROM output path must be a regular file")
        path.unlink()


def require_new_rom(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size == 0:
        raise ValueError("build did not produce a new nonempty regular ROM")
