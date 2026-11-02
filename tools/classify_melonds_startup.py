#!/usr/bin/env python3
"""Classify private melonDS startup failures without disclosing emulator logs.

The owner-private runner may contain ROM paths or other private information in
stderr. Only emit fixed diagnostic categories, never a matched line or path.
"""
import sys
from pathlib import Path

# Order matters: prefer actionable failures over generic abort messages.
SIGNATURES = (
    ("qt-platform-plugin", (
        "could not load the qt platform plugin",
        "no qt platform plugin could be initialized",
        "could not find the qt platform plugin",
        "qt.qpa.plugin:",
    )),
    ("x11-display", (
        "could not connect to display",
        "cannot connect to x server",
        "qt.qpa.xcb:",
        "authorization required, but no authorization protocol specified",
    )),
    ("missing-shared-library", (
        "error while loading shared libraries",
        "cannot open shared object file",
    )),
    ("existing-emulator-instance", (
        "another instance is already running",
        "already running",
    )),
    ("appimage-runtime", (
        "cannot mount appimage",
        "appimage extraction failed",
        "fusermount",
        "fuse: device not found",
    )),
    ("process-abort", (
        "assertion failed",
        "terminate called after throwing",
        "aborted (core dumped)",
    )),
)


def classify(raw: str) -> str:
    lowered = raw.lower()
    for category, signatures in SIGNATURES:
        if any(signature in lowered for signature in signatures):
            return category
    return "unclassified"


def main() -> int:
    if len(sys.argv) != 2:
        print("melonDS startup category: unavailable")
        return 2
    try:
        # Bound private log reads; do not echo paths or log content.
        with Path(sys.argv[1]).open("rb") as handle:
            raw = handle.read(1_048_576).decode("utf-8", "replace")
    except OSError:
        print("melonDS startup category: unavailable")
        return 0
    print("melonDS startup category: " + classify(raw))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
