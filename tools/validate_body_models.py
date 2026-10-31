#!/usr/bin/env python3
"""Validate original Mii body mesh conversion before packaging a DS ROM."""
import argparse
import math
import struct
from pathlib import Path

BONES = 18
MAX_VERTICES = 12000

def inspect_bytes(data: bytes, name: str = 'body mesh') -> tuple[int, int]:
    path = name
    if len(data) < 56 or data[:4] != b'BOD2':
        raise ValueError(f'{path}: expected BOD2 original body mesh')
    count = struct.unpack_from('<I', data, 4)[0]
    if not 0 < count <= MAX_VERTICES or count % 3 or len(data) != 56 + count * 12:
        raise ValueError(f'{path}: invalid triangle count or mesh length')
    matrix = struct.unpack_from('<12f', data, 8)
    if not all(math.isfinite(x) and abs(x) <= 4096 for x in matrix):
        raise ValueError(f'{path}: invalid head-bone transform')
    for index in range(count):
        start = 56 + index * 12
        material, bone = data[start + 9], data[start + 10]
        if bone >= BONES:
            raise ValueError(f'{path}: vertex {index} references missing bone {bone}')
        if material > 1:
            raise ValueError(f'{path}: vertex {index} references unknown material {material}')
    return count, count // 3


def inspect(path: Path) -> tuple[int, int]:
    return inspect_bytes(path.read_bytes(), str(path))

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        for gender in ('Male', 'Female'):
            path = args.root / 'nitrofiles' / 'models' / (gender + 'Body.bin')
            vertices, triangles = inspect(path)
            print(f'PASS: {gender} original body: {vertices} vertices / {triangles} triangles / {BONES} bones supported')
    except (OSError, ValueError, struct.error) as error:
        parser.exit(1, f'FAIL: {error}\n')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
