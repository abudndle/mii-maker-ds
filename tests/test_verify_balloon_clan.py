#!/usr/bin/env python3
"""Synthetic source-CLAN parity tests; no private Nintendo files needed."""
import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from verify_balloon_clan import CLIPS, parse_balloon_tables, verify_balloon_clips
from private_validation_cache import fingerprint


class TestBalloonSourceParity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source_dir = self.root / "source"
        self.source_dir.mkdir()
        self.source = self.source_dir / "gallery_balloon_clan.c"
        self.source.write_text((ROOT / "source/gallery_balloon_clan.c").read_text())
        tables = parse_balloon_tables(self.source.read_text())
        self.catalog = {"clips": []}
        for clip, (frames, specs) in CLIPS.items():
            tracks = []
            for pane, kind, index, target, table in specs:
                keys = tables[table] if table else [(0, 255 * 65536, 0)]
                tracks.append({"pane": pane, "kind": kind, "index": index,
                               "target": target, "value_type": 2,
                               "keys": [[v / 65536 for v in key] for key in keys]})
            self.catalog["clips"].append({"archive": "Select.arc.files",
                                          "clip": clip, "frames": frames,
                                          "loop_flag": 0, "tracks": tracks})

    def test_all_four_clips(self):
        report = verify_balloon_clips(self.catalog, self.source_dir)
        self.assertEqual((report["clips"], report["channels"]), (4, 10))

    def test_missing_clip(self):
        self.catalog["clips"].pop()
        with self.assertRaisesRegex(ValueError, "missing or duplicate"):
            verify_balloon_clips(self.catalog, self.source_dir)

    def test_changed_duration(self):
        self.catalog["clips"][0]["frames"] += 1
        with self.assertRaisesRegex(ValueError, "duration"):
            verify_balloon_clips(self.catalog, self.source_dir)

    def test_tampered_private_track(self):
        self.catalog["clips"][0]["tracks"][0]["keys"][0][1] += 0.25
        with self.assertRaisesRegex(ValueError, "key mismatch"):
            verify_balloon_clips(self.catalog, self.source_dir)

    def test_extra_channel(self):
        self.catalog["clips"][0]["tracks"].append(
            copy.deepcopy(self.catalog["clips"][0]["tracks"][0]))
        with self.assertRaisesRegex(ValueError, "channels"):
            verify_balloon_clips(self.catalog, self.source_dir)

    def test_wrong_source_table(self):
        self.source.write_text(self.source.read_text().replace("85197", "85198"))
        with self.assertRaisesRegex(ValueError, "key mismatch"):
            verify_balloon_clips(self.catalog, self.source_dir)

    def test_no_invented_select_favorite_alpha(self):
        with self.source.open("a") as out:
            out.write("\nstatic const MdsClanKey favorite_alpha[]={{0,0,0}};\n")
        with self.assertRaisesRegex(ValueError, "missing or unexpected"):
            verify_balloon_clips(self.catalog, self.source_dir)

    def test_discrete_track_rejected(self):
        self.catalog["clips"][0]["tracks"][0]["value_type"] = 1
        with self.assertRaisesRegex(ValueError, "discrete"):
            verify_balloon_clips(self.catalog, self.source_dir)

    def test_nonfinite_rejected(self):
        self.catalog["clips"][0]["tracks"][0]["keys"][0][1] = float("nan")
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            verify_balloon_clips(self.catalog, self.source_dir)

    def test_private_cache_tracks_balloon_source(self):
        archive = self.root / "synthetic.zip"
        archive.write_bytes(b"fictional archive only")
        before = fingerprint(self.root, archive)
        self.source.write_text(self.source.read_text() + "\n/* modified */\n")
        after = fingerprint(self.root, archive)
        self.assertNotEqual(before["source_sha256"], after["source_sha256"])


if __name__ == "__main__":
    unittest.main()
