#!/usr/bin/env python3
"""Convert user-owned 3DS Mii Maker CLIM textures to private DS RGB555A1 sprites.

No Nintendo data is embedded here. Run this on privately extracted timg files.
CLIM format ids differ from the PICA hardware texture-format enumeration.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct

FORMAT_BPP={0:8,1:8,2:8,3:16,5:16,7:16,8:16,12:4,13:4}
FORMAT_NAMES={0:'L8',1:'A8',2:'LA4',3:'LA8',5:'RGB565',
              7:'RGBA5551',8:'RGBA4444',12:'L4',13:'A4'}
FOOTER=struct.Struct('<4sHHIIHH4sIHHII')

def next_power_of_two(value:int)->int:
    return max(8,1<<(value-1).bit_length())

def parse_bclim(data:bytes)->dict:
    if len(data)<FOOTER.size:raise ValueError('truncated CLIM footer')
    magic,bom,hlen,version,total,blocks,reserved,imag,ilen,w,h,format_word,bytes_count=FOOTER.unpack_from(data,len(data)-FOOTER.size)
    fmt=format_word&0xff
    if (magic,bom,hlen,imag,ilen,blocks)!=(b'CLIM',0xfeff,0x14,b'imag',0x10,1):
        raise ValueError('invalid CLIM footer fields')
    if total!=len(data) or bytes_count!=len(data)-40:
        raise ValueError('CLIM declared size does not match file size')
    if w<1 or h<1 or w>4096 or h>4096:
        raise ValueError('invalid CLIM dimensions')
    if fmt not in FORMAT_BPP:
        raise ValueError('unsupported CLIM format %d'%fmt)
    pw=next_power_of_two(w)
    ph=next_power_of_two(h)
    expected=pw*ph*FORMAT_BPP[fmt]//8
    if expected!=bytes_count:
        raise ValueError('CLIM tiled-data size mismatch (%d versus %d)'%(bytes_count,expected))
    return dict(width=w,height=h,padded_width=pw,padded_height=ph,
                format=fmt,format_name=FORMAT_NAMES[fmt],version=version,
                pixel_bytes=bytes_count,format_word=format_word)

def morton8(x:int,y:int)->int:
    return (x&1)|((y&1)<<1)|((x&2)<<1)|((y&2)<<2)|((x&4)<<2)|((y&4)<<3)

def _rgba(payload:bytes, idx:int,fmt:int)->tuple[int,int,int,int]:
    if fmt==0:
        l=payload[idx];return l,l,l,255
    if fmt==1:return 255,255,255,payload[idx]
    if fmt==2:
        z=payload[idx];l=(z&15)*17;return l,l,l,(z>>4)*17
    if fmt==3:
        i=idx*2;l=payload[i];return l,l,l,payload[i+1]
    if fmt in (5,7,8):
        v=struct.unpack_from('<H',payload,idx*2)[0]
        if fmt==5:return (v&31)*255//31,((v>>5)&63)*255//63,((v>>11)&31)*255//31,255
        if fmt==7:return (v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31,255 if v&0x8000 else 0
        return (v&15)*17,((v>>4)&15)*17,((v>>8)&15)*17,((v>>12)&15)*17
    n=(payload[idx//2]>>((idx%2)*4))&15
    if fmt==12:return n*17,n*17,n*17,255
    if fmt==13:return 255,255,255,n*17
    raise AssertionError(fmt)

def decode_bclim(data:bytes,alpha_cutoff:int=128)->tuple[dict,bytes]:
    h=parse_bclim(data)
    w,height,pw=h['width'],h['height'],h['padded_width']
    fmt=h['format'];cols=pw//8;payload=data[:-40]
    result=bytearray(w*height*2)
    for y in range(height):
        for x in range(w):
            idx=((y//8)*cols+(x//8))*64+morton8(x%8,y%8)
            r,g,b,a=_rgba(payload,idx,fmt)
            word=(0x8000 if a>=alpha_cutoff else 0)|((b>>3)<<10)|((g>>3)<<5)|(r>>3)
            struct.pack_into('<H',result,(y*w+x)*2,word)
    return h,bytes(result)

def convert_file(src:Path,dst:Path,alpha_cutoff:int=128)->dict:
    data=src.read_bytes();h,pixels=decode_bclim(data,alpha_cutoff)
    dst.parent.mkdir(parents=True,exist_ok=True)
    # NitroFS sprite format: little-endian width/height, then 16-bit RGB555A1 pixels.
    dst.write_bytes(struct.pack('<HH',h['width'],h['height'])+pixels)
    return dict(source=src.as_posix(),output=dst.as_posix(),format=h['format_name'],
                width=h['width'],height=h['height'],bytes=len(pixels)+4,
                sha256=hashlib.sha256(data).hexdigest())

def convert_tree(srcroot:Path,dstroot:Path,selection_only:bool=False)->list[dict]:
    files=sorted(srcroot.rglob('*.bclim'))
    if selection_only:
        files=[f for f in files if f.parent.name=='timg' and f.parent.parent.name=='Select']
    if not files:raise ValueError('no matching original BCLIM files')
    rows=[]
    for f in files:
        rel=f.relative_to(srcroot)
        rows.append(convert_file(f,dstroot/rel.with_suffix('.bin')))
    dstroot.mkdir(parents=True,exist_ok=True)
    (dstroot/'_manifest.json').write_text(json.dumps(rows,indent=2))
    return rows

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input',type=Path,help='private original timg directory or .bclim')
    p.add_argument('output',type=Path,help='private destination directory or .bin')
    p.add_argument('--selection-only',action='store_true',
                   help='only extracted layout/Select/timg textures')
    args=p.parse_args()
    if args.input.is_file():
        print(json.dumps(convert_file(args.input,args.output),indent=2))
    else:
        rows=convert_tree(args.input,args.output,args.selection_only)
        print(json.dumps({'files':len(rows),'format_counts':{
            n:sum(1 for row in rows if row['format']==n)
            for n in sorted({row['format'] for row in rows})},'destination':str(args.output)},indent=2))
if __name__=='__main__':main()
