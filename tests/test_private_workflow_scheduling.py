#!/usr/bin/env python3
"""Fail closed if trusted private-ROM acceptance stops following main.

This is a source-only test: it never retrieves assets or invokes melonDS.
"""
from pathlib import Path
import re
import unittest

WORKFLOW = (Path(__file__).resolve().parents[1] /
            ".github/workflows/private-original-rom-build.yml").read_text()


class PrivateWorkflowScheduleTests(unittest.TestCase):
    def test_trusted_main_and_daily_dispatch(self):
        self.assertRegex(WORKFLOW, r"(?m)^  schedule:\s*\n    - cron: '30 14 \* \* \*'$")
        self.assertRegex(WORKFLOW, r"(?m)^  push:\s*\n    branches:\s*\n      - main$")
        self.assertRegex(WORKFLOW, r"(?m)^  workflow_dispatch:$")
        self.assertNotRegex(WORKFLOW, r"(?m)^  pull_request(?:_target)?:")
        self.assertRegex(WORKFLOW, r"(?m)^concurrency:\s*\n  group: private-original-rom-")
        self.assertRegex(WORKFLOW, r"(?m)^  cancel-in-progress: true$")

    def test_private_build_is_not_a_synthetic_substitute(self):
        for required in (
            "secrets.MII_ASSETS_URL",
            "tools/verify_private_clan.py",
            "tools/verify_runtime_assets.py",
            "tools/test_original_render.py",
            "skylyrac/blocksds:slim-latest",
            "tests/rom_nitrofs_assets.py",
            "tests/rom_motion_packs.py",
            "tests/rom_arm_sections.py",
            "tools/run_melonds_headless.sh",
        ):
            with self.subTest(required=required):
                self.assertIn(required, WORKFLOW)

    def test_only_encrypted_rom_and_frames_can_be_uploaded(self):
        upload = WORKFLOW.split(
            "      - name: Upload encrypted ROM and diagnostic screenshots", 1
        )[1].split("      - name:", 1)[0]
        self.assertIn("mii-ds.nds.gpg", upload)
        self.assertIn("melonds-boot.png.gpg", upload)
        self.assertIn("melonds-gallery-ten.png.gpg", upload)
        self.assertNotRegex(upload, r"(?m)^\s+(?:mii-ds\.nds|.*\.png)\s*$")
        self.assertIn("tools/private_rom_recipient.asc", WORKFLOW)
        self.assertIn("gpg --batch --yes --trust-model always", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
