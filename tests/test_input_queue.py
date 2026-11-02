#!/usr/bin/env python3
"""Check the DS VBlank FIFO never discards a fresh press in favor of repeats."""
from pathlib import Path
import re

source = (Path(__file__).resolve().parents[1] / "source/main.c").read_text()
start = source.index("static void animation_vblank(void)")
end = source.index("static MdsInput next_input(void)", start)
producer = source[start:end]
consumer_start = source.index("static MdsInput next_input(void)", end)
consumer_end = source.index("static uint32_t render_time(void)", consumer_start)
consumer = source[consumer_start:consumer_end]
if "live_held=keysHeld();" not in producer:
    raise SystemExit("FAIL: VBlank is not capturing held keys")
if ".held=live_held" not in consumer or "keysHeld()" in consumer:
    raise SystemExit("FAIL: main loop must consume VBlank-captured held state")
checks = [
    (r"if\s*\(!\(event\.down\|\|event\.up\)&&queued>=23\)return;", "reserve slots for presses and stylus release"),
    (r"if\s*\(next==input_read\)", "queue-full detection"),
    (r"if\s*\(!\(event\.down\|\|event\.up\)\)return;", "discard saturated repeat-only events"),
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
if ".up=keysUp()" not in producer:
    raise SystemExit("FAIL: stylus release must be queued in VBlank")
if "event.touch.px=live_touch_x;event.touch.py=live_touch_y;" not in producer:
    raise SystemExit("FAIL: stylus release must use last valid coordinates")
queue = [False] * 31
enqueue(queue, True)  # stylus release has the same priority as a new press
assert len(queue) == 31 and queue[-1]
# Compile the exact queue producer body extracted from main.c, rather than
# testing only a Python approximation of its ring-buffer behavior. This runs
# on a host compiler without Nintendo headers or a proprietary ROM.
import os
import subprocess
import tempfile

assert "while(drop!=input_write" in producer
assert "input_queue[drop]=input_queue[previous];" in producer
assert "unsigned previous=(drop+31)%32;" in producer
body_start = producer.index(" unsigned queued=")
body_end = producer.index(" input_write=next;", body_start) + len(" input_write=next;")
producer_body = producer[body_start:body_end]
harness = r"""
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef struct { int down, up, repeat, held, id; } MdsInput;
static MdsInput input_queue[32];
static unsigned input_read, input_write;
static void push(MdsInput event)
{
/* PRODUCER_BODY */
}
static void reset(void)
{
 memset(input_queue, 0, sizeof input_queue);
 input_read=0;
 input_write=0;
}
static void check(unsigned pos,int id)
{
 assert(input_queue[(input_read+pos)%32].id==id);
}
int main(void)
{
 reset();
 /* 23 repeats + eight press edges fill the ring. New touch release must
  * evict a repeat, never the oldest queued stylus/button press. */
 for(int i=0;i<23;i++)push((MdsInput){.repeat=1,.id=i});
 for(int i=23;i<31;i++)push((MdsInput){.down=1,.id=i});
 push((MdsInput){.up=1,.id=99});
 assert((input_write+32-input_read)%32==31);
 for(int i=0;i<22;i++)check((unsigned)i,i+1);
 for(int i=0;i<8;i++)check((unsigned)(22+i),i+23);
 check(30,99);

 /* The same operation must work when read/write wrap across index zero. */
 reset();
 for(int i=0;i<20;i++)push((MdsInput){.down=1,.id=i});
 input_read=(input_read+18)%32; /* consumer drained 18 events */
 for(int i=20;i<=40;i++)push((MdsInput){.repeat=1,.id=i});
 for(int i=50;i<58;i++)push((MdsInput){.down=1,.id=i});
 assert((input_write+32-input_read)%32==31);
 push((MdsInput){.down=1,.id=100});
 check(0,18);check(1,19);
 for(int i=0;i<20;i++)check((unsigned)(i+2),i+21);
 for(int i=0;i<8;i++)check((unsigned)(i+22),i+50);
 check(30,100);

 /* When all 31 entries are edges, the oldest edge is the unavoidable
  * fallback; repeat-only input must never displace any of them. */
 reset();
 for(int i=0;i<31;i++)push((MdsInput){.down=1,.id=i});
 push((MdsInput){.repeat=1,.id=500});
 for(int i=0;i<31;i++)check((unsigned)i,i);
 push((MdsInput){.down=1,.id=501});
 for(int i=0;i<30;i++)check((unsigned)i,i+1);
 check(30,501);
 puts("PASS: full and wrapped VBlank FIFO retains press/release edges ahead of repeats");
 return 0;
}
""".replace("/* PRODUCER_BODY */", producer_body)
with tempfile.TemporaryDirectory(prefix="mii-input-fifo-") as tmp:
    source_path = Path(tmp) / "input_fifo.c"
    exe_path = Path(tmp) / "input_fifo"
    source_path.write_text(harness)
    subprocess.run([os.environ.get("CC", "cc"), "-std=c11", "-Wall",
                    "-Wextra", "-Werror", str(source_path), "-o", str(exe_path)],
                   check=True)
    subprocess.run([str(exe_path)], check=True)
print("PASS: saturated VBlank queue protects touch presses and releases")

