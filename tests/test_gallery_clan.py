#!/usr/bin/env python3
"""Host-executed tests of original 3DS Mii selection and room color keyframes."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
HARNESS=r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include "gallery_clan.h"

#define RGB15(r,g,b) ((uint16_t)(0x8000u|(r)|((g)<<5)|((b)<<10)))
int main(void)
{
    MdsGalleryClan fx={0};
    MdsGalleryClanStyle style;
    assert(!mds_gallery_clan_active(&fx,4));
    assert(!mds_gallery_clan_update(&fx,0,0,100)); /* first entry */
    assert(!mds_gallery_clan_style(&fx,100,&style));
    assert(style.scale_x_q16==65536u);
    assert(!mds_gallery_clan_update(&fx,0,0,101));
    assert(mds_gallery_clan_update(&fx,0,1,105)); /* different Mii */
    assert(mds_gallery_clan_active(&fx,105));
    assert(mds_gallery_clan_style(&fx,105,&style));
    assert(style.scale_x_q16==65536u);
    assert(style.room_transition==0);
    assert(mds_gallery_clan_style(&fx,107,&style));
    /* Source CLPA: frame 1 scale X/Y = 1.100006... */
    assert(style.scale_x_q16==72090u&&style.scale_y_q16==72090u);
    assert(mds_gallery_clan_style(&fx,109,&style));
    assert(style.scale_x_q16==65536u);
    assert(!mds_gallery_clan_active(&fx,110));
    assert(!mds_gallery_clan_style(&fx,110,&style));
    assert(style.scale_x_q16==65536u);
    assert(mds_gallery_clan_update(&fx,1,11,200)); /* new room */
    assert(mds_gallery_clan_style(&fx,200,&style));
    assert(style.room_transition && style.previous_page==0);
    /* EDITSelectBase Select source RGB 220/255/244; Unselect 50/118/80. */
    assert(style.selected_room_tint==RGB15(27,31,30));
    assert(style.previous_room_tint==RGB15(6,14,10));
    assert(mds_gallery_clan_style(&fx,201,&style));
    assert(style.room_transition);
    assert(!mds_gallery_clan_update(&fx,1,11,201));
    assert(mds_gallery_clan_style(&fx,202,&style));
    assert(!style.room_transition); /* 2 source ticks only */
    assert(!mds_gallery_clan_update(&fx,10,11,203)); /* out-of-range page */
    assert(!mds_gallery_clan_update(&fx,1,100,203)); /* out-of-range slot */
    assert(!mds_gallery_clan_style(&fx,205,&style));
    assert(!mds_gallery_clan_style(&fx,205,NULL));
    mds_gallery_clan_reset(&fx);
    assert(!mds_gallery_clan_active(&fx,206));
    /* 32-bit tick wrap is intentional; relative elapsed remains valid. */
    assert(!mds_gallery_clan_update(&fx,0,0,0xfffffffdu));
    assert(mds_gallery_clan_update(&fx,0,1,0xfffffffeu));
    assert(mds_gallery_clan_style(&fx,0u,&style));
    assert(style.scale_x_q16==72090u);
    puts("PASS: original 3DS source CLPA/CLMC gallery interpolation and state");
    return 0;
}
'''
def run():
    cc=os.environ.get('CC','cc')
    if not shutil.which(cc):
        raise SystemExit('FAIL: C compiler not found')
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory)
        test=root/'main.c';test.write_text(HARNESS)
        exe=root/'gallery_clan_test'
        subprocess.run([cc,'-std=c11','-Wall','-Wextra','-Werror','-pedantic',
                        '-O2','-I',str(ROOT/'source'),str(ROOT/'source/gallery_clan.c'),
                        str(ROOT/'source/clan_curve.c'),str(test),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
if __name__=='__main__':run()
