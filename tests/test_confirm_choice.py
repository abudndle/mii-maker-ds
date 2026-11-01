#!/usr/bin/env python3
"""Synthetic RGB555 confirmation button and true 3DS decision-timing regression."""
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
#include "confirm_motion.h"
#include "confirm_choice.h"
static uint16_t pixels[MDS_CONFIRM_WIDTH*MDS_CONFIRM_HEIGHT];
int main(void)
{
    MdsConfirmMotion m={0};
    assert(!mds_confirm_motion_choose(&m,1,1u));
    mds_confirm_motion_begin(&m,100u);
    assert(mds_confirm_motion_choose(&m,1,100u));
    assert(!mds_confirm_motion_choose(&m,0,101u));
    assert(!mds_confirm_motion_ready(&m,140u)); /* repeated touch locked */
    assert(mds_confirm_motion_tick(&m,111u));
    assert(m.choice_active && !m.exit_requested);
    assert(mds_confirm_motion_tick(&m,112u));
    assert(!m.choice_active && m.exit_requested);
    assert(!m.exiting); /* wait for original entrance */
    assert(mds_confirm_motion_tick(&m,140u));
    assert(m.exiting);
    assert(mds_confirm_motion_tick(&m,180u));
    assert(mds_confirm_motion_exit_done(&m,180u));

    /* Whole-screen original RGB555 buffer; only the selected CLYT button
     * bounds change. Color ratios derive from actual 3DS Select CLMC. */
    for(unsigned i=0;i<MDS_CONFIRM_WIDTH*MDS_CONFIRM_HEIGHT;i++)pixels[i]=0xffffu;
    mds_confirm_choice_tint(pixels,1);
    assert(pixels[71*MDS_CONFIRM_WIDTH+28]!=0xffffu);
    assert(pixels[102*MDS_CONFIRM_WIDTH+227]!=0xffffu);
    assert(pixels[103*MDS_CONFIRM_WIDTH+28]==0xffffu);
    assert(pixels[111*MDS_CONFIRM_WIDTH+28]==0xffffu);
    assert((pixels[71*MDS_CONFIRM_WIDTH+28]&0x8000u)==0x8000u);
    assert(pixels[0]==0xffffu);
    mds_confirm_choice_tint(pixels,0);
    assert(pixels[111*MDS_CONFIRM_WIDTH+28]!=0xffffu);
    assert(pixels[142*MDS_CONFIRM_WIDTH+227]!=0xffffu);
    assert(pixels[143*MDS_CONFIRM_WIDTH+28]==0xffffu);
    mds_confirm_choice_tint(NULL,0);

    mds_confirm_motion_reset(&m);
    mds_confirm_motion_begin(&m,200u);
    assert(mds_confirm_motion_tick(&m,240u));
    assert(mds_confirm_motion_choose(&m,0,240u));
    assert(mds_confirm_motion_tick(&m,252u));
    assert(m.exiting && !m.exit_up && m.started==252u);
    assert(mds_confirm_motion_tick(&m,292u));
    assert(mds_confirm_motion_exit_done(&m,292u));
    puts("PASS: original source six-frame Decide sequencing, both button tint panes and input locking");
}
'''
def run():
    cc=os.getenv("CC","cc")
    if not shutil.which(cc): raise SystemExit("FAIL: host C compiler unavailable")
    with tempfile.TemporaryDirectory() as temp:
        source=Path(temp)/"test.c";source.write_text(HARNESS)
        exe=Path(temp)/"test"
        subprocess.run([cc,"-std=c11","-Wall","-Wextra","-Werror","-pedantic","-O2",
                        "-I",str(ROOT/"source"),
                        str(ROOT/"source/confirm_choice.c"),
                        str(ROOT/"source/confirm_motion.c"),
                        str(ROOT/"source/clan_dialog.c"),
                        str(ROOT/"source/clan_curve.c"),str(source),"-o",str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
if __name__=="__main__":
    run()
