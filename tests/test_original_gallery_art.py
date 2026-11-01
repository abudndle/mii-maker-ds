#!/usr/bin/env python3
"""Portable runtime validation of private source-art rendering with SYNTHETIC files.

No extracted Nintendo game resource is used or checked into GitHub.
"""
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]

HARNESS = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "original_gallery_art.h"
static uint16_t canvas[256*192];
int main(int argc,char **argv)
{
    assert(argc==2);
    for(unsigned i=0;i<256u*192u;i++)canvas[i]=0x9111;
    int good=!strcmp(argv[1],"good");
    int base=mds_original_gallery_box_base(canvas,256,192,21,49,42,46);
    int frame=mds_original_gallery_box_border(canvas,256,192,21,49,42,46);
    int room=mds_original_gallery_room_tab(canvas,256,192,9,2,22,21,1);
    if(!good){
        assert(!base&&!frame&&!room);
        assert(canvas[49*256+21]==0x9111);
    }else{
        assert(base&&frame&&room);
        assert(canvas[2*256+9]==0x8033); /* selected-tab source pixel */
        assert(canvas[49*256+21]==0x8022); /* box border overlays fill */
        assert(canvas[49*256+22]==0x8022);
        assert(canvas[48*256+21]==0x9111); /* no overflow outside widget */
        assert(canvas[2*256+8]==0x9111);
        assert(mds_original_gallery_room_tab(canvas,256,192,
                33,2,22,21,0));
        assert(canvas[2*256+33]==0x8044); /* unselected original tab */
        /* Scaled blitter clips safely on screen edges. */
        assert(mds_original_gallery_box_base(canvas,256,192,-18,190,42,46));
        assert(canvas[190*256]==0x8011);
        assert(!mds_original_gallery_box_base(NULL,256,192,0,0,20,20));
        assert(!mds_original_gallery_box_base(canvas,0,192,0,0,20,20));
    }
    puts("PASS: original private gallery sprites, transparency, state, and clipping");
    return 0;
}
'''

def write_fake_sprite(path: Path,w:int,h:int,pixel:int,corrupt:bool=False)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    data=struct.pack("<HH",w,h)+struct.pack("<H",pixel)*(w*h)
    if corrupt:data=data[:-2]
    path.write_bytes(data)

def run() -> None:
    cc=os.environ.get("CC","cc")
    if not shutil.which(cc):
        raise SystemExit("FAIL: no C compiler found (CC or cc)")
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        src=root/"sprite_test.c"
        src.write_text(HARNESS)
        binary=root/"sprite_test"
        subprocess.run([cc,"-std=c11","-Wall","-Wextra","-Werror","-pedantic",
                        "-O2","-I",str(ROOT/"source"),
                        str(ROOT/"source"/"original_gallery_art.c"),
                        str(src),"-o",str(binary)],check=True)
        # Missing optional original resources must be safe.
        subprocess.run([str(binary),"missing"],cwd=root,check=True)
        private_dir=root/"nitro:"/"art"/"Select"
        # Corrupt header/payload must be rejected with unchanged fallback.
        write_fake_sprite(private_dir/"BtnMiiB.bin",54,60,0x8011,corrupt=True)
        write_fake_sprite(private_dir/"BtnMiiLine.bin",54,60,0x8022,corrupt=True)
        write_fake_sprite(private_dir/"BtnRoomEDITline01.bin",32,28,0x8033,corrupt=True)
        write_fake_sprite(private_dir/"BtnRoomEDITline.bin",32,28,0x8044,corrupt=True)
        subprocess.run([str(binary),"missing"],cwd=root,check=True)
        # Exact dimensions/source alpha are required.
        write_fake_sprite(private_dir/"BtnMiiB.bin",54,60,0x8011)
        write_fake_sprite(private_dir/"BtnMiiLine.bin",54,60,0x8022)
        write_fake_sprite(private_dir/"BtnRoomEDITline01.bin",32,28,0x8033)
        write_fake_sprite(private_dir/"BtnRoomEDITline.bin",32,28,0x8044)
        subprocess.run([str(binary),"good"],cwd=root,check=True)

if __name__=="__main__":
    run()
