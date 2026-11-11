#!/usr/bin/env python3
"""Host-only milestone issue queue and untrusted metadata regressions."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from select_bot_milestone import select

items = [
    {"number": 402, "title": "Bot milestone [face]: Fix face framing edge boundary"},
    {"number": 403, "title": "Bot milestone [tween]: Fix GUI tween rollover boundary"},
]
assert select(items, 0) == {"focus": "face", "issue": 402, "source": "issue"}
assert select(items, 1) == {"focus": "face", "issue": 402, "source": "issue"}
assert select(list(reversed(items)), 999)["issue"] == 402
assert select(items[1:], 2) == {"focus": "tween", "issue": 403, "source": "issue"}
assert select([], 0) == {"focus": "tween", "issue": 0, "source": "rotation"}
assert select([], 1) == {"focus": "face", "issue": 0, "source": "rotation"}
assert select([], 2) == {"focus": "tween", "issue": 0, "source": "rotation"}
assert select([{"number": 1, "title": "Bot milestone [gpu]: Leak private game files"}], 0)["issue"] == 0
assert select([{"number": 1, "title": "Bot milestone [face]: $(rm -rf /)"}], 0)["issue"] == 0
assert select([{"number": 1, "title": "Bot milestone [face]: valid; malicious"}], 0)["issue"] == 0
assert select([{"number": 1, "title": "Bot milestone [face]: valid\nunsafe"}], 0)["issue"] == 0
assert select([{"number": 1, "title": "Bot milestone [face]: valid message", "state": "closed"}], 0)["issue"] == 1  # caller supplies only open issues
assert select([{"number": "5", "title": "Bot milestone [face]: valid message"}], 0)["issue"] == 0
for issues, slot in [([], -1), ({}, 0), ([], 2.5)]:
    try:
        select(issues, slot)
        raise AssertionError("Invalid queue accepted")
    except ValueError:
        pass
print("PASS: oldest explicit bot milestone wins, invalid/untrusted metadata rejected and rotation fallback works")
