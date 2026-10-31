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
require("if(result<0){", "cancelled preview renders are not handled")
cancel_start = preview.index("if(result<0){")
cancel_end = preview.index("\n  }", cancel_start)
cancel_branch = preview[cancel_start:cancel_end]
if ("preview_cached[mode]" not in cancel_branch or
        "memcmp(a->value,head_avatars[mode].value,sizeof a->value)" not in cancel_branch or
        "(!mode||preview_pose[mode]==pose_index)" not in cancel_branch or
        "preview_ready[mode]:0" not in cancel_branch):
    raise SystemExit("FAIL: interrupted render may display a different Mii or stale animation frame")
require("if(!result){", "failed Mii render is not handled")
fail_start = preview.index("if(!result){")
fail_end = preview.index("\n  }", fail_start)
failure = preview[fail_start:fail_end]
if "preview_cached[mode]=0;" not in failure or "return 0;" not in failure:
    raise SystemExit("FAIL: unsuccessful preview render is permanently cached")
# The success marker must occur only after the failed-render branch closes.
# A misplaced marker inside the branch would poison the cache on failure.
success_markers = [i for i in range(len(preview))
                   if preview.startswith("preview_cached[mode]=1;", i)]
if len(success_markers) != 1 or success_markers[0] <= fail_end:
    raise SystemExit("FAIL: successful-render cache marker has unsafe placement")
if preview.index("memcpy(head_pixels,render_pixels", fail_end) > success_markers[0]:
    raise SystemExit("FAIL: preview marked cached before copying rendered pixels")
print("PASS: preview input guards, 62-field cache, skeletal retry and render retry")
