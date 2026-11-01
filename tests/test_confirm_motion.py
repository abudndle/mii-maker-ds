#!/usr/bin/env python3
"""Host-execute original 3DS DialogBase02 W_Dialog CLPA Y motion without assets."""
import os
from pathlib import Path
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
static uint16_t canvas[MDS_CONFIRM_WIDTH*MDS_CONFIRM_HEIGHT];
static uint16_t under[MDS_CONFIRM_WIDTH*MDS_CONFIRM_HEIGHT];
static uint16_t dialog[MDS_CONFIRM_WIDTH*MDS_CONFIRM_HEIGHT];
#define ROWWIDTH MDS_CONFIRM_WIDTH
static void fill(void)
{
    for(unsigned p=0;p<MDS_CONFIRM_WIDTH*MDS_CONFIRM_HEIGHT;p++){
        under[p]=0x801fu;dialog[p]=0xfc00u;canvas[p]=0;
    }
}
int main(void)
{
    MdsConfirmMotion m={0};
    assert(!mds_confirm_motion_tick(&m,100u));
    assert(!mds_confirm_motion_ready(&m,100u));
    assert(mds_confirm_motion_offset(&m,100u)==0);
    mds_confirm_motion_begin(&m,100u);
    assert(mds_confirm_motion_tick(&m,100u));
    assert(!mds_confirm_motion_tick(&m,100u)); /* once per VBlank */
    assert(mds_confirm_motion_offset(&m,100u)==-192);
    assert(!mds_confirm_motion_ready(&m,139u));
    assert(mds_confirm_motion_tick(&m,134u));
    assert(mds_confirm_motion_offset(&m,134u)==2); /* source frame17=+2 */
    assert(mds_confirm_motion_tick(&m,139u));
    assert(mds_confirm_motion_tick(&m,140u)); /* final unshifted frame */
    assert(mds_confirm_motion_offset(&m,140u)==0);
    assert(mds_confirm_motion_ready(&m,140u)); /* touch now visible */
    assert(!mds_confirm_motion_tick(&m,141u));

    fill();
    mds_confirm_motion_composite(canvas,under,dialog,-192);
    assert(canvas[0]==0x801fu);
    assert(canvas[191*ROWWIDTH+255]==0x801fu);
    mds_confirm_motion_composite(canvas,under,dialog,-100);
    /* A pane translated upwards by 100 pixels appears on screen
     * rows 0..91; rows 92..191 show the stationary gallery. */
    assert(canvas[0]==0xfc00u);
    assert(canvas[91*ROWWIDTH+99]==0xfc00u);
    assert(canvas[92*ROWWIDTH+99]==0x801fu);
    assert(canvas[191*ROWWIDTH+255]==0x801fu);
    mds_confirm_motion_composite(canvas,under,dialog,0);
    assert(canvas[0]==0xfc00u && canvas[191*ROWWIDTH+255]==0xfc00u);
    mds_confirm_motion_composite(canvas,under,dialog,192);
    assert(canvas[0]==0x801fu && canvas[191*ROWWIDTH+255]==0x801fu);
    mds_confirm_motion_composite(canvas,under,dialog,191);
    assert(canvas[190*ROWWIDTH+100]==0x801fu);
    assert(canvas[191*ROWWIDTH+100]==0xfc00u);
    mds_confirm_motion_composite(NULL,under,dialog,0);
    mds_confirm_motion_composite(canvas,NULL,dialog,0);
    mds_confirm_motion_composite(canvas,under,NULL,0);

    mds_confirm_motion_reset(&m);
    assert(!m.begun && !mds_confirm_motion_ready(&m,141u));
    mds_confirm_motion_begin(&m,0xfffffffeu);
    assert(mds_confirm_motion_tick(&m,0u)); /* VBlank wrap */
    assert(!mds_confirm_motion_ready(&m,0u));
    assert(mds_confirm_motion_ready(&m,0x26u)); /* 40 ticks across wrap */
    assert(mds_confirm_motion_tick(&m,0x26u));
    assert(!mds_confirm_motion_tick(&m,0x27u));
    puts("PASS: original 3DS 21-frame DialogBase02 motion, input gating, framebuffer restoration and clipping");
    return 0;
}
'''
def run():
    cc=os.environ.get('CC','cc')
    if not shutil.which(cc):
        raise SystemExit('FAIL: host C compiler not found')
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp)
        src=root/'confirm_test.c';src.write_text(HARNESS)
        exe=root/'confirm_test'
        subprocess.run([cc,'-std=c11','-O2','-Wall','-Wextra','-Werror','-pedantic',
                        '-I',str(ROOT/'source'),
                        str(ROOT/'source/confirm_motion.c'),
                        str(ROOT/'source/clan_dialog.c'),
                        str(ROOT/'source/clan_curve.c'),
                        str(src),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
if __name__=='__main__':
    run()
