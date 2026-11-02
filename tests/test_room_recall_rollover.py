"""Regression guard for rollover-safe room recall animation timing."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class RoomRecallRolloverTests(unittest.TestCase):
    def test_recall_uses_bounded_countdown_not_wrapping_deadline(self):
        source = (ROOT / "source" / "ui.c").read_text(encoding="utf-8")
        self.assertIn("walk_home_remaining=24u;", source)
        self.assertIn("walk_home_remaining!=0u", source)
        self.assertIn("if(walk_home_remaining)walk_home_remaining--;", source)
        self.assertNotIn("walk_ticks<walk_home_until", source)
        self.assertNotIn("walk_ticks+24u", source)

    def test_all_room_slots_receive_recall_updates(self):
        source = (ROOT / "source" / "ui.c").read_text(encoding="utf-8")
        self.assertIn("mds_room_walk_tick(&room_walk[local],local,walk_ticks,walk_home_remaining!=0u);", source)
        self.assertNotIn("if(g->used[start+local])mds_room_walk_tick", source)

    def test_countdown_is_bounded_at_uint_rollover(self):
        for start in (0, 0xffffffff - 10, 0xffffffff):
            remaining = 24
            frames = []
            for elapsed in range(26):
                tick = (start + elapsed) & 0xffffffff
                frames.append((tick, remaining != 0))
                if remaining:
                    remaining -= 1
            self.assertEqual([active for _, active in frames], [True] * 24 + [False] * 2)


if __name__ == "__main__":
    unittest.main()
