#!/usr/bin/env python3
"""Host-execute original DialogBase02 exit motion without game assets."""
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
#include "clan_dialog.h"
static uint16_t screen[MDS_CONFIRM_WIDTH*MDS_CONFIRM_HEIGHT];
static uint16_t backdrop[MDS_CONFIRM_WIDTH*MDS_CONFIRM_HEIGHT];
static uint16_t window[MDS_CONFIRM_WIDTH*MDS_CONFIRM_HEIGHT];
int main(void)
{
    MdsConfirmMotion m={0};
    assert(!mds_confirm_motion_request_exit(&m,0));
    assert(!mds_confirm_motion_exit_done(&m,99u));
    mds_confirm_motion_begin(&m,100u);
    assert(mds_confirm_motion_request_exit(&m,0));
    assert(!mds_confirm_motion_request_exit(&m,1));
    assert(!mds_confirm_motion_ready(&m,140u)); /* touch disabled */
    assert(mds_confirm_motion_tick(&m,139u));
    assert(!m.exiting);
    assert(!mds_confirm_motion_exit_done(&m,139u));
    assert(mds_confirm_motion_tick(&m,140u));
    assert(m.exiting && m.started==140u);
    assert(mds_confirm_motion_offset(&m,140u)==0);
    assert(mds_confirm_motion_tick(&m,142u));
    assert(mds_confirm_motion_offset(&m,142u)<0);
    assert(!mds_confirm_motion_exit_done(&m,179u));
    assert(mds_confirm_motion_tick(&m,180u));
    assert(mds_confirm_motion_exit_done(&m,180u));
    assert(mds_confirm_motion_offset(&m,180u)==-MDS_CONFIRM_HEIGHT);
    assert(!mds_confirm_motion_tick(&m,181u));

    for(unsigned i=0;i<MDS_CONFIRM_WIDTH*MDS_CONFIRM_HEIGHT;i++){
        backdrop[i]=0x801fu;
        window[i]=0xfc00u;
        screen[i]=0;
    }
    mds_confirm_motion_composite(screen,backdrop,window,
                                 mds_confirm_motion_offset(&m,180u));
    for(unsigned i=0;i<MDS_CONFIRM_WIDTH*MDS_CONFIRM_HEIGHT;i++)
        assert(screen[i]==backdrop[i]); /* complete original backdrop restoration */
    mds_confirm_motion_reset(&m);
    assert(!m.begun && !m.exit_requested);
    mds_confirm_motion_begin(&m,500u);
    assert(mds_confirm_motion_tick(&m,500u));
    assert(mds_confirm_motion_tick(&m,540u));
    assert(mds_confirm_motion_ready(&m,540u));
    assert(mds_confirm_motion_request_exit(&m,1));
    assert(!mds_confirm_motion_ready(&m,540u));
    assert(mds_confirm_motion_tick(&m,540u));
    assert(m.exiting && m.exit_up);
    assert(mds_confirm_motion_offset(&m,540u)==0);
    assert(mds_confirm_motion_tick(&m,580u));
    assert(mds_confirm_motion_exit_done(&m,580u));
    assert(mds_confirm_motion_offset(&m,580u)==MDS_CONFIRM_HEIGHT);
    mds_confirm_motion_composite(screen,backdrop,window,
                                 mds_confirm_motion_offset(&m,580u));
    assert(screen[0]==backdrop[0] && screen[49151]==backdrop[49151]);

    /* VBlank rollover must not make the 40-tick source clip hang. */
    mds_confirm_motion_reset(&m);
    mds_confirm_motion_begin(&m,0xfffffff0u);
    assert(mds_confirm_motion_request_exit(&m,0));
    assert(mds_confirm_motion_tick(&m,0x18u)); /* 40 ticks elapsed */
    assert(m.exiting && m.started==0x18u);
    assert(!mds_confirm_motion_exit_done(&m,0x3fu));
    assert(mds_confirm_motion_tick(&m,0x40u));
    assert(mds_confirm_motion_exit_done(&m,0x40u));
    puts("PASS: DialogBase02 source exit/down/up, early decision, locked input, backdrop, VBlank wrap");
    return 0;
}
'''

def run():
    cc=os.environ.get("CC","cc")
    if not shutil.which(cc):
        raise SystemExit("FAIL: host C compiler not found")
    with tempfile.TemporaryDirectory() as temp:
        harness=Path(temp)/"test.c"
        harness.write_text(HARNESS)
        exe=Path(temp)/"test"
        subprocess.run([cc,"-std=c11","-O2","-Wall","-Wextra","-Werror","-pedantic",
                        "-I",str(ROOT/"source"),
                        str(ROOT/"source/confirm_motion.c"),
                        str(ROOT/"source/clan_dialog.c"),
                        str(ROOT/"source/clan_curve.c"),
                        str(harness),"-o",str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
if __name__=="__main__":
    run()
