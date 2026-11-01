#!/usr/bin/env python3
"""Host test the exact 3DS Select/BtnScrollShadow sprite format with SYNTHETIC pixels.

No Nintendo textures or animation binaries are included in this test.
"""
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
C_HARNESS=r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "original_gallery_art.h"

static uint16_t screen[256*192];
static void clear(void)
{
    for(unsigned i=0;i<256u*192u;i++)screen[i]=0x9111u;
}
static uint16_t expected(unsigned opacity)
{
    const unsigned base[3]={17u,8u,4u};
    unsigned rgb=0;
    for(unsigned i=0;i<3;i++){
        unsigned output=(base[i]*(255u-opacity)+31u*opacity+127u)/255u;
        rgb|=output<<(i*5);
    }
    return (uint16_t)(0x8000u|rgb);
}
int main(int argc,char **argv)
{
    assert(argc==2);
    int mode=!strcmp(argv[1],"valid");
    clear();
    assert(!mds_original_gallery_arrow_shadow(screen,256,192,3,89,13,13,0));
    assert(screen[90*256+4]==0x9111u);
    if(!mode){
        assert(!mds_original_gallery_arrow_shadow(screen,256,192,3,89,13,13,200));
        assert(screen[90*256+4]==0x9111u);
        puts("PASS: shadow absent / malformed asset preserves original screen");
        return 0;
    }
    /* Pixel 0 of the synthetic shadow is transparent; all others opaque. */
    assert(mds_original_gallery_arrow_shadow(screen,256,192,3,89,13,13,200));
    assert(screen[89*256+3]==0x9111u);  /* A1 transparent texel */
    assert(screen[90*256+4]==expected(200)); /* original CLVC 200 */
    assert(screen[88*256+4]==0x9111u);  /* clipped to original pane */
    assert(screen[90*256+2]==0x9111u);
    clear();
    assert(mds_original_gallery_arrow_shadow(screen,256,192,3,89,13,13,100));
    assert(screen[90*256+4]==expected(100));
    clear();
    assert(mds_original_gallery_arrow_shadow(screen,256,192,3,89,13,13,255));
    assert(screen[90*256+4]==0xffffu);
    clear();
    assert(mds_original_gallery_arrow_shadow(screen,256,192,3,89,13,13,999));
    assert(screen[90*256+4]==0xffffu); /* invalid alpha safely capped */
    clear();
    assert(mds_original_gallery_arrow_shadow(screen,256,192,-8,186,13,13,200));
    assert(screen[187*256+0]==expected(200)); /* clipped source stamp */
    assert(screen[185*256+0]==0x9111u);
    assert(!mds_original_gallery_arrow_shadow(NULL,256,192,0,0,16,16,200));
    assert(!mds_original_gallery_arrow_shadow(screen,0,192,0,0,16,16,200));
    assert(!mds_original_gallery_arrow_shadow(screen,256,192,0,0,0,16,200));
    /* After first validation the original source asset must stay cached. */
    assert(mds_original_gallery_arrow_shadow(screen,256,192,3,89,13,13,200));
    puts("PASS: source shadow texture and CLVC alpha blend, A1, clipping and caching");
    return 0;
}
'''

def fake_stamp(path:Path,mode:str)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    pixels=[0xffff]*256
    pixels[0]=0x0000  # transparent source pixel
    data=struct.pack('<HH',16,16)+struct.pack('<256H',*pixels)
    if mode=='truncated':data=data[:-2]
    if mode=='bad_dimensions':data=struct.pack('<HH',17,16)+data[4:]
    path.write_bytes(data)

def run()->None:
    cc=os.environ.get('CC','cc')
    if not shutil.which(cc):raise SystemExit('FAIL: C compiler unavailable')
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        source=root/'shadow_test.c';source.write_text(C_HARNESS)
        exe=root/'shadow_test'
        subprocess.run([cc,'-std=c11','-Wall','-Wextra','-Werror','-pedantic',
                        '-O2','-I',str(ROOT/'source'),
                        str(ROOT/'source/original_gallery_art.c'),str(source),
                        '-o',str(exe)],check=True)
        subprocess.run([str(exe),'missing'],check=True,cwd=root)
        path=root/'nitro:'/'art'/'Select'/'BtnScrollShadow.bin'
        for kind in ('truncated','bad_dimensions'):
            fake_stamp(path,kind)
            subprocess.run([str(exe),'missing'],check=True,cwd=root)
        fake_stamp(path,'valid')
        subprocess.run([str(exe),'valid'],check=True,cwd=root)
if __name__=='__main__':run()
