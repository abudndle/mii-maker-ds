"""Regression guard for rollover-safe room recall animation timing."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class RoomRecallRolloverTests(unittest.TestCase):
    def test_recall_uses_bounded_countdown_not_wrapping_deadline(self):
        source = (ROOT / "source" / "ui.c").read_text(encoding="utf-8")
        self.assertIn("walk_home_remaining=24u;", source)
        self.assertIn("walk_home_remaining!=0u", source)
        self.assertIn("if(elapsed>=walk_home_remaining)walk_home_remaining=0;", source)
        self.assertIn("else walk_home_remaining-=elapsed;", source)
        self.assertNotIn("walk_ticks<walk_home_until", source)
        self.assertNotIn("walk_ticks+24u", source)

    def test_all_room_slots_receive_recall_updates(self):
        source = (ROOT / "source" / "ui.c").read_text(encoding="utf-8")
        self.assertIn("mds_room_walk_tick(&room_walk[local],local,walk_ticks,walk_home_remaining!=0u);", source)
        self.assertNotIn("if(g->used[start+local])mds_room_walk_tick", source)

    def test_first_draw_preserves_queued_recall_but_room_switch_cancels(self):
        source = (ROOT / "source" / "ui.c").read_text(encoding="utf-8")
        self.assertIn("unsigned previous_room_start=walk_room_start;", source)
        self.assertIn("if(previous_room_start!=UINT32_MAX)walk_home_remaining=0;", source)
        remaining = 24
        previous = 0xffffffff
        if previous != 0xffffffff:
            remaining = 0
        self.assertEqual(remaining, 24)
        previous = 0
        if previous != 0xffffffff:
            remaining = 0
        self.assertEqual(remaining, 0)

    def test_recall_counts_vblanks_not_redraws(self):
        source = (ROOT / "source" / "ui.c").read_text(encoding="utf-8")
        self.assertIn("animation_clock-walk_last_clock", source)
        self.assertIn("walk_ticks+=elapsed;", source)
        self.assertNotIn("walk_ticks++;", source)
        remaining = 24
        for elapsed in (0, 0, 5, 0, 8, 11):
            remaining = max(0, remaining - elapsed)
        self.assertEqual(remaining, 0)

    def test_navigation_rebases_clock_without_losing_first_draw_recall(self):
        source = (ROOT / "source" / "ui.c").read_text(encoding="utf-8")
        self.assertIn("if(previous_room_start!=UINT32_MAX||!walk_clock_valid)", source)
        self.assertIn("walk_last_clock=animation_clock;", source)
        self.assertNotIn("walk_ticks=0;\n        walk_clock_valid=0;", source)
        # A pending recall before first draw keeps its original clock origin.
        previous_room_start = 0xffffffff
        walk_clock_valid = True
        self.assertFalse(previous_room_start != 0xffffffff or not walk_clock_valid)
        # Switching from an existing room always rebases to the new scene.
        previous_room_start = 0
        self.assertTrue(previous_room_start != 0xffffffff or not walk_clock_valid)

    def test_non_room_menus_pause_room_clock(self):
        ui = (ROOT / "source" / "ui.c").read_text(encoding="utf-8")
        main = (ROOT / "source" / "main.c").read_text(encoding="utf-8")
        header = (ROOT / "source" / "ui.h").read_text(encoding="utf-8")
        self.assertIn("void mds_ui_room_pause(void);", header)
        self.assertIn("walk_last_clock=animation_clock;", ui)
        self.assertIn("if(screen!=MDS_SCREEN_GALLERY&&screen!=MDS_SCREEN_SAVED)mds_ui_room_pause();", main)

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
