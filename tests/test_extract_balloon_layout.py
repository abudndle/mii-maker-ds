#!/usr/bin/env python3
"""Synthetic CLYT fixtures: no Nintendo layout bytes or textures."""
import math
import struct
import sys
import tempfile
import subprocess
import json
from zipfile import ZipFile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from extract_balloon_layout import extract, PRIVATE_MEMBER


def section(tag, body=b""):
    return tag + struct.pack("<I", len(body)+8) + body


def pane(name, x=0, y=0, angle=0, sx=1, sy=1, w=10, h=10, origin=4,
         visible=True, tag=b"pan1"):
    buf = bytearray(68)
    buf[0] = 1 if visible else 0
    buf[1] = origin
    buf[2] = 255
    encoded = name.encode("ascii")
    buf[4:4+len(encoded)] = encoded
    struct.pack_into("<10f", buf, 28, x, y, 0, 0, 0, angle, sx, sy, w, h)
    return section(tag, buf)


def fixture(parent_rotation=0, parent_scale=1, hide=False):
    parts = [section(b"lyt1", b"\0"*4+struct.pack("<ff", 320, 240)),
             pane("Root", x=40, y=20, angle=parent_rotation,
                  sx=parent_scale, sy=parent_scale, visible=not hide),
             section(b"pas1"),
             pane("B_Favorite", x=20, y=0, w=20, h=20, tag=b"bnd1"),
             pane("I_Favorite", x=20, y=0, tag=b"pic1"),
             pane("I_MyMii", x=20, y=0, tag=b"pic1"),
             pane("I_MiiCopy", x=40, y=0, tag=b"pic1"),
             pane("I_MiiOpen", x=60, y=0, tag=b"pic1"),
             section(b"pae1")]
    content = b"".join(parts)
    header = bytearray(20)
    header[:4] = b"CLYT"
    struct.pack_into("<HHIIH", header, 4, 0xfeff, 20, 0, 20+len(content), len(parts))
    return bytes(header)+content


def fail(data, fragment):
    try:
        extract(data)
    except ValueError as exc:
        assert fragment in str(exc), (fragment, str(exc))
    else:
        raise AssertionError("accepted " + fragment)


base = extract(fixture())
assert base["runtime_anchor_verified"] is False
assert base["source_canvas"] == [320.0, 240.0]
assert len(base["panes"]) == 6
favorite = next(p for p in base["panes"] if p["name"] == "B_Favorite")
assert favorite["parent"] == "Root" and favorite["ancestors"] == ["Root"]
assert favorite["ds_bounds"] == [168.0, 72.0, 16.0, 16.0], favorite
assert favorite["visible"] is True and favorite["alpha"] == 255
# CLYT traversal determines the painter's order. Group and boundary panes
# occupy the hierarchy but must not consume a drawable layer.
assert [p["pane_order"] for p in base["panes"]] == list(range(6))
assert [p["paint_order"] for p in base["panes"]] == [None, None, 0, 1, 2, 3]
assert [p["depth"] for p in base["panes"]] == [0, 1, 1, 1, 1, 1]
# A nested group cannot reorder overlapping source icons. After the nested
# subtree ends, subsequent siblings must paint over earlier children.
nested_parts = [
    section(b"lyt1", b"\0"*4 + struct.pack("<ff", 320, 240)),
    pane("Root"), section(b"pas1"),
    pane("B_Favorite", tag=b"bnd1"),
    pane("Group"), section(b"pas1"),
    pane("I_Favorite", tag=b"pic1"),
    section(b"pae1"),
    pane("I_MyMii", tag=b"pic1"),
    pane("I_MiiCopy", tag=b"pic1"),
    pane("I_MiiOpen", tag=b"pic1"),
    section(b"pae1"),
]
nested_content = b"".join(nested_parts)
nested_header = bytearray(20)
nested_header[:4] = b"CLYT"
struct.pack_into("<HHIIH", nested_header, 4, 0xfeff, 20, 0,
                 20 + len(nested_content), len(nested_parts))
nested = extract(bytes(nested_header) + nested_content)["panes"]
assert [p["paint_order"] for p in nested] == [None, None, None, 0, 1, 2, 3]
assert next(p for p in nested if p["name"] == "I_Favorite")["depth"] == 2
assert next(p for p in nested if p["name"] == "I_MyMii")["depth"] == 1
rotated = extract(fixture(parent_rotation=90, parent_scale=2))
favorite_rot = next(p for p in rotated["panes"] if p["name"] == "B_Favorite")
assert favorite_rot["ds_bounds"] == [144.0, 32.0, 32.0, 32.0], favorite_rot
assert next(p for p in extract(fixture(hide=True))["panes"] if p["name"] == "B_Favorite")["visible"] is False
shifted = extract(fixture(), (5, -7))
shift = next(p for p in shifted["panes"] if p["name"] == "B_Favorite")
assert shift["ds_bounds"] == [173.0, 65.0, 16.0, 16.0]
# An enclosing scene can rotate/shear the local CLYT geometry. Transform all
# four corners before calculating bounds; transforming the AABB is incorrect.
turned = extract(fixture(), scene_affine=(0, -1, 256, 1, 0, 0))
assert turned["runtime_anchor_verified"] is False
assert turned["external_scene_affine_ds"] == [0, -1, 256, 1, 0, 0]
assert next(p for p in turned["panes"] if p["name"] == "B_Favorite")["ds_bounds"] == [168.0, 168.0, 16.0, 16.0]
sheared = extract(fixture(), scene_affine=(1, 0.5, 3, 0, 1, 4))
assert next(p for p in sheared["panes"] if p["name"] == "B_Favorite")["ds_bounds"] == [207.0, 76.0, 24.0, 16.0]
for bad in ((1, 0, 0, 0, 0, 0), (1, 0, 0, 0, 1, math.inf),
            (1, 0, 0, 0, 1), (17, 0, 0, 0, 1, 0)):
    try:
        extract(fixture(), scene_affine=bad)
    except ValueError:
        pass
    else:
        raise AssertionError("accepted invalid scene affine")
# A new hierarchy start after an end marker must have a new parent pane.
orphan = bytearray(fixture() + section(b"pas1"))
struct.pack_into("<I", orphan, 12, len(orphan))
struct.pack_into("<H", orphan, 16, struct.unpack_from("<H", orphan, 16)[0] + 1)
fail(bytes(orphan), "orphan pane hierarchy start")
fail(fixture()[:-1], "header size")
fail(fixture()+b"x", "header size")
fail(fixture().replace(b"I_MiiOpen", b"I_MiiOpeX"), "missing or ambiguous")
fail(fixture()[:-8]+section(b"pas1"), "unclosed")
fail(fixture()[:-8]+section(b"pae1")+section(b"pae1"), "header size")
fail(fixture().replace(b"I_MiiOpen", b"I_MiiCopy"), "missing or ambiguous")
fail(fixture().replace(b"pae1", b"paX1"), "unclosed")
invalid = bytearray(fixture())
invalid[4:6] = b"\xfe\xff"
fail(bytes(invalid), "byte order")
try:
    extract(fixture(), (math.inf, 0))
except ValueError:
    pass
else:
    raise AssertionError("accepted nonfinite scene offset")
with tempfile.TemporaryDirectory() as temp:
    archive = Path(temp) / "fictional.zip"
    report = Path(temp) / "local.json"
    with ZipFile(archive, "w") as z:
        z.writestr(PRIVATE_MEMBER, fixture())
    subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / "tools" / "extract_balloon_layout.py"),
                    str(archive), "--report", str(report)], check=True, capture_output=True)
    result = json.loads(report.read_text())
    assert result["runtime_anchor_verified"] is False
    assert result["source_sha256"] == base["source_sha256"]
    subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / "tools" / "extract_balloon_layout.py"),
                    str(archive), "--report", str(report), "--scene-affine",
                    "0", "-1", "256", "1", "0", "0"], check=True, capture_output=True)
    transformed = json.loads(report.read_text())
    assert transformed["runtime_anchor_verified"] is False
    assert transformed["external_scene_affine_ds"] == [0, -1, 256, 1, 0, 0]
    assert next(p for p in transformed["panes"] if p["name"] == "B_Favorite")["ds_bounds"] == [168.0, 168.0, 16.0, 16.0]
print("PASS: synthetic CLYT paint order, pane hierarchy, scene affine, rotation/scale, visibility, DS bounds and fail-closed parsing")
