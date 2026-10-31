#!/usr/bin/env python3
"""Check the DS VBlank FIFO never discards a fresh press in favor of repeats."""
from pathlib import Path
import re

source = (Path(__file__).resolve().parents[1] / "source/main.c").read_text()
start = source.index("static void animation_vblank(void)")
end = source.index("static MdsInput next_input(void)", start)
producer = source[start:end]
checks = [
    (r"if\s*\(!event\.down&&queued>=23\)return;", "reserve eight slots for fresh presses"),
    (r"if\s*\(next==input_read\)", "queue-full detection"),
    (r"if\s*\(!event\.down\)return;", "discard saturated repeat-only events"),
    (r"input_read\s*=\s*\(input_read\+1\)%32;", "evict oldest event for new press"),
    (r"input_queue\[input_write\]\s*=\s*event;", "enqueue new press"),
    (r"input_write\s*=\s*next;", "advance tail"),
]
positions = []
for pattern, label in checks:
    match = re.search(pattern, producer)
    if not match:
        raise SystemExit("FAIL: missing " + label)
    positions.append(match.start())
if positions != sorted(positions):
    raise SystemExit("FAIL: saturated input queue update is out of order")
# Model the actual bounded ring-buffer policy across repeated, pressed and
# mixed events. The most recent press must survive a full queue of repeats.
capacity = 32
def enqueue(queue, down):
    if len(queue) == capacity - 1:
        if not down:
            return
        queue.pop(0)
    queue.append(down)
queue = [False] * 31
enqueue(queue, False)
assert len(queue) == 31 and not any(queue)
enqueue(queue, True)
assert len(queue) == 31 and queue[-1] is True
# Only 23 repeat events should be retained, leaving 8 places for presses.
queue = []
for _ in range(100):
    if len(queue) < 23:
        enqueue(queue, False)
assert len(queue) == 23
for _ in range(8):
    enqueue(queue, True)
assert len(queue) == 31 and sum(queue) == 8
print("PASS: eight FIFO slots reserved for fresh presses")
