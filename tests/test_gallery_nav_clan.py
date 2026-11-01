#!/usr/bin/env python3
"""Host-execute source-derived 3DS room navigation and confirmation keyframes.

No Nintendo assets are copied into the repository; tests use the numeric
metadata ported from the user's verified original Select.arc BCLAN clips.
"""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

root=Path(__file__).resolve().parents[1]
harness=r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include "gallery_nav_clan.h"
#define RGB15(r,g,b) ((uint16_t)(0x8000u|(r)|((g)<<5)|((b)<<10)))
int main(void){
    MdsGalleryNavClan n={0};
    MdsGalleryNavStyle s;
    assert(!mds_gallery_nav_clan_active(&n,0));
    assert(!mds_gallery_nav_clan_style(NULL,0,&s));
    assert(!s.left_arrow_dx&&!s.right_arrow_dx&&s.shadow_alpha==200);
    assert(!mds_gallery_nav_clan_style(&n,0,NULL));
    mds_gallery_nav_clan_invalid(&n,-1);
    assert(n.invalid_edges==1 && !mds_gallery_nav_clan_active(&n,0));
    mds_gallery_nav_clan_invalid(&n,0);
    assert(n.invalid_edges==1);
    mds_gallery_nav_clan_navigate(&n,-1,100);
    assert(mds_gallery_nav_clan_active(&n,100));
    assert(mds_gallery_nav_clan_style(&n,100,&s));
    assert(s.left_arrow_dx==0 && s.right_arrow_dx==0);
    assert(s.shadow_alpha==200 && s.navigation_visible);
    assert(mds_gallery_nav_clan_style(&n,101,&s));
    assert(s.shadow_alpha==100);
    assert(mds_gallery_nav_clan_style(&n,102,&s));
    assert(s.left_arrow_dx==-2 && s.right_arrow_dx==2);
    assert(s.shadow_alpha==0);
    assert(!mds_gallery_nav_clan_active(&n,103));
    assert(!mds_gallery_nav_clan_style(&n,103,&s));
    assert(s.left_arrow_dx==-2 && s.right_arrow_dx==2); /* held endpoint */
    assert(s.shadow_alpha==0);
    mds_gallery_nav_clan_navigate(&n,1,200);
    assert(mds_gallery_nav_clan_style(&n,200,&s));
    assert(s.left_arrow_dx==-2 && s.right_arrow_dx==2);
    assert(s.shadow_alpha==0);
    assert(mds_gallery_nav_clan_style(&n,202,&s));
    assert(s.left_arrow_dx==0 && s.right_arrow_dx==0 && s.shadow_alpha==200);
    assert(!mds_gallery_nav_clan_active(&n,203));
    mds_gallery_nav_clan_confirm(&n,300);
    assert(mds_gallery_nav_clan_active(&n,300));
    assert(mds_gallery_nav_clan_style(&n,300,&s));
    assert(s.confirm_visible && s.confirm_tint==RGB15(31,24,23));
    assert(mds_gallery_nav_clan_style(&n,302,&s));
    assert(s.confirm_visible && s.confirm_tint==RGB15(27,29,26));
    assert(!mds_gallery_nav_clan_active(&n,303));
    assert(!mds_gallery_nav_clan_style(&n,303,&s));
    assert(!s.confirm_visible && s.confirm_tint==0xffff);
    mds_gallery_nav_clan_reset(&n);
    assert(!n.navigation_direction && !n.confirm_valid && !n.invalid_edges);
    mds_gallery_nav_clan_navigate(&n,-1,0xfffffffeu);
    assert(mds_gallery_nav_clan_style(&n,0u,&s)); /* tick rollover */
    assert(s.left_arrow_dx==-2 && s.shadow_alpha==0);
    puts("PASS: source CLPA navigation, shadow CLVC, Mii CLMC confirmation and invalid boundaries");
    return 0;
}
'''
with tempfile.TemporaryDirectory() as d:
    d=Path(d)
    file=d/"main.c"
    file.write_text(harness)
    exe=d/"gallery_nav_test"
    cc=os.environ.get("CC","cc")
    if not shutil.which(cc):raise SystemExit("FAIL: CC not available")
    subprocess.run([cc,"-std=c11","-pedantic","-Wall","-Wextra","-Werror","-O2",
                    "-I",str(root/"source"),str(root/"source/gallery_nav_clan.c"),
                    str(root/"source/clan_curve.c"),str(file),"-o",str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
