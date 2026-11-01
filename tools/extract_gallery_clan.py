#!/usr/bin/env python3
"""Recover only numeric gallery UI CLAN keyframes from a PRIVATE 3DS RomFS.

This script has no original Nintendo assets; never commit source .bclan files.
Expected input is the unpacked Select.arc/anim directory from the user's game.
"""
from pathlib import Path
import argparse
import hashlib
import math
import struct

WANTED={
    'SelectMii_Select':{'P_Mii_00':('CLPA',(0x600,0x700))},
    'EDITSelectBase_Select':{'P_Room_00':('CLMC',(0x400,0x500,0x600))},
    'EDITSelectBase_Unselect':{'P_Room_00':('CLMC',(0x400,0x500,0x600))},
}

def u16(data,pos):
    if pos<0 or pos+2>len(data):raise ValueError("truncated BCLAN")
    return struct.unpack_from('<H',data,pos)[0]

def u32(data,pos):
    if pos<0 or pos+4>len(data):raise ValueError("truncated BCLAN")
    return struct.unpack_from('<I',data,pos)[0]

def check(data,pos,length):
    if pos<0 or length<0 or pos+length>len(data):
        raise ValueError("BCLAN offset out of bounds")

def parse(data):
    if len(data)<40 or data[:4]!=b'CLAN' or u16(data,4)!=0xfeff or \
       u16(data,6)!=20 or u32(data,12)!=len(data):
        raise ValueError("invalid CLAN header")
    pos=20;pai=None
    for _ in range(u16(data,16)):
        check(data,pos,8)
        size=u32(data,pos+4)
        if size<8:raise ValueError("invalid CLAN section")
        check(data,pos,size)
        if data[pos:pos+4]==b'pai1':pai=pos
        pos+=size
    if pos!=len(data) or pai is None:raise ValueError("missing or trailing pai1")
    frames=u16(data,pai+8);num=u16(data,pai+14)
    if frames>4096 or num>512 or u32(data,pai+16)!=20:
        raise ValueError("unreasonable pai1 table")
    check(data,pai+20,num*4)
    tracks={}
    for i in range(num):
        entry=pai+u32(data,pai+20+i*4)
        check(data,entry,24)
        name=data[entry:entry+20].split(b'\0')[0].decode('ascii')
        count=data[entry+20]
        category=data[entry+21]
        if count>32:raise ValueError("invalid CLAN track count")
        check(data,entry+24,count*4)
        channels={}
        for t in range(count):
            block=entry+u32(data,entry+24+t*4)
            check(data,block,8)
            tag=data[block:block+4].decode('ascii')
            channel_count=u32(data,block+4)
            if channel_count>256:raise ValueError("invalid CLAN channel count")
            check(data,block+8,channel_count*4)
            for j in range(channel_count):
                info=block+u32(data,block+8+4*j)
                check(data,info,12)
                kind,mode,nkeys,_,keys_offset=struct.unpack_from('<HHHHI',data,info)
                if nkeys>512:raise ValueError("too many CLAN keys")
                if mode!=2:continue
                values=[]
                for k in range(nkeys):
                    offset=info+keys_offset+12*k
                    check(data,offset,12)
                    key=struct.unpack_from('<fff',data,offset)
                    if not all(math.isfinite(v) for v in key):
                        raise ValueError("nonfinite keyframes")
                    values.append(key)
                channels[tag,kind]=values
        tracks[name,category]=channels
    return frames,tracks

def q16(v):
    n=round(v*65536)
    if not -(2**31)<=n<2**31:raise ValueError("Q16 overflow")
    return n

def extract(directory):
    output={}
    for clip,panes in WANTED.items():
        payload=(directory/(clip+'.bclan')).read_bytes()
        frames,tracks=parse(payload)
        items={}
        for pane,(tag,kinds) in panes.items():
            hits=[channels for (name,_),channels in tracks.items()
                  if name==pane and all((tag,kind) in channels for kind in kinds)]
            if len(hits)!=1:raise ValueError(f"{clip}: ambiguous {pane} channels")
            for kind in kinds:
                keys=hits[0][tag,kind]
                if not keys:raise ValueError(f"{clip}: empty {tag} keys")
                items[tag,kind]=[(q16(f),q16(v),q16(t)) for f,v,t in keys]
        output[clip]={'frames':frames,'hash':hashlib.sha256(payload).hexdigest(),
                      'keys':items}
    return output

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('private_anim_directory',type=Path)
    p.add_argument('--report',type=Path,help="write numeric metadata report")
    args=p.parse_args()
    result=extract(args.private_anim_directory)
    for clip,r in result.items():
        print(f"{clip}: {r['frames']} source frames; SHA256 {r['hash']}")
        for (tag,kind),keys in r['keys'].items():
            print(f"  {tag}/{kind:#04x}: {keys}")
    if args.report:
        lines=[f"{clip},{r['frames']},{r['hash']}" for clip,r in result.items()]
        args.report.write_text('\n'.join(lines)+'\n')

if __name__=='__main__':
    main()
