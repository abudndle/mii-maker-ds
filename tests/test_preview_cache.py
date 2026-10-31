#!/usr/bin/env python3
"""Guard Mii preview cache invalidation and failed-render recovery in DS UI."""
from pathlib import Path

source = (Path(__file__).resolve().parents[1] / "source" / "ui.c").read_text()
start = source.index("static int preview(")
end = source.index("static void paint_head(", start)
preview = source[start:end]

def require(fragment, message):
    if fragment not in preview:
        raise SystemExit("FAIL: " + message)

require("if(!a||!cfl.data||mode<0||mode>2)return 0;",
        "preview null/resource/mode guard is missing")
require("if(gender>=2)return 0;", "invalid avatar gender is not rejected")
require("memcmp(a->value,head_avatars[mode].value,sizeof a->value)",
        "not all appearance fields invalidate the preview cache")
require("if(!motion_cached[gender]||motion_cached_key[gender]!=key)",
        "skeletal pose is not retried on a cache miss")
require("if(motion_cached[gender])motion_cached_key[gender]=key;",
        "failed skeletal motion read is being marked as cached")
require("if(!result){", "failed Mii render is not handled")
fail_start = preview.index("if(!result){")
fail_end = preview.index("\n  }", fail_start)
failure = preview[fail_start:fail_end]
if "preview_cached[mode]=0;" not in failure or "return 0;" not in failure:
    raise SystemExit("FAIL: unsuccessful preview render is permanently cached")
success = preview.index("preview_cached[mode]=1;", fail_end)
if success < fail_end:
    raise SystemExit("FAIL: success cache flag occurs in the render failure branch")
print("PASS: preview input guards, 62-field cache, skeletal retry and render retry")
