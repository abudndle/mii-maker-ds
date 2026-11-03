#!/usr/bin/env python3
"""Export source-extracted BOD2 body geometry to Nitro Engine DSMA input.

This converts original-resource triangles, not replacement primitives. The
18 source bone IDs and per-vertex positions survive conversion. BOD2 does not
contain UVs or an animation skeleton; these must be exported separately.
Keep source-derived input and generated MD5/DSM/DSA outside the public repo.
"""
import argparse
from pathlib import Path
import struct

BONE_COUNT = 18
MAX_VERTICES = 12000
HEADER = 56
VERTEX = struct.Struct("<3h3bBBx")


def decode(data):
    if len(data) < HEADER or data[:4] != b"BOD2":
        raise ValueError("Expected original-resource BOD2 body")
    count = struct.unpack_from("<I", data, 4)[0]
    if not count or count > MAX_VERTICES or count % 3:
        raise ValueError("Invalid triangle/vertex count")
    if len(data) != HEADER + count * VERTEX.size:
        raise ValueError("Invalid BOD2 byte length")
    vertices = []
    for i in range(count):
        x, y, z, nx, ny, nz, material, bone = VERTEX.unpack_from(
            data, HEADER + i * VERTEX.size)
        if material > 1 or bone >= BONE_COUNT:
            raise ValueError(f"Invalid material/bone at source vertex {i}")
        vertices.append(((x / 128, y / 128, z / 128), material, bone))
    return vertices


def emit_mesh(data, name="MiiBody"):
    if not name.isidentifier():
        raise ValueError("Model name must be an identifier")
    vertices = decode(data)
    # Each original triangle has a single source material. Splitting these
    # into separate MD5 meshes preserves source material boundaries.
    triangles = [vertices[i:i + 3] for i in range(0, len(vertices), 3)]
    if any(len({v[1] for v in tri}) != 1 for tri in triangles):
        raise ValueError("Source triangle spans different materials")
    parts = [(material, [v for tri in triangles if tri[0][1] == material
                         for v in tri]) for material in (0, 1)]
    parts = [(material, group) for material, group in parts if group]
    lines = ["MD5Version 10",
             'commandline "original BOD2 to DSMA geometry adapter"',
             f"numJoints {BONE_COUNT}", f"numMeshes {len(parts)}",
             "joints {"]
    for i in range(BONE_COUNT):
        lines.append(f'    "bone_{i:02d}" -1 ( 0 0 0 ) ( 0 0 0 )')
    lines.append("}")
    for material, group in parts:
        lines += ["mesh {", f'    shader "source_material_{material}"',
                  f"    numverts {len(group)}"]
        for i in range(len(group)):
            # This intermediate BOD2 format has no UVs. Never fabricate
            # coordinates or claim that the original textures are mapped.
            lines.append(f"    vert {i} ( 0 0 ) {i} 1")
        lines.append(f"    numtris {len(group) // 3}")
        for i in range(0, len(group), 3):
            # Nitro Engine's MD5 parser reverses triangle winding itself.
            lines.append(f"    tri {i // 3} {i + 2} {i + 1} {i}")
        lines.append(f"    numweights {len(group)}")
        for i, (pos, _, bone) in enumerate(group):
            lines.append(
                f"    weight {i} {bone} 1.0 "
                f"( {pos[0]:.8g} {pos[1]:.8g} {pos[2]:.8g} )")
        lines.append("}")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True,
                        help="Private source-extracted BOD2 binary")
    parser.add_argument("--output", type=Path, required=True,
                        help="Private MD5 staging directory")
    parser.add_argument("--name", default="MiiBody")
    args = parser.parse_args()
    mesh = emit_mesh(args.input.read_bytes(), args.name)
    args.output.mkdir(parents=True, exist_ok=True)
    output = args.output / (args.name + ".md5mesh")
    output.write_text(mesh, encoding="ascii")
    print(f"Exported {output}; original triangles and bone IDs retained. "
          "UVs, skeleton motion and runtime integration still pending.")


if __name__ == "__main__":
    main()
