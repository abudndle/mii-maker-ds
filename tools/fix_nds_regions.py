#!/usr/bin/env python3
"""Align a BlocksDS homebrew DSi region for retail-style cartridge readers.
melonDS's CartRetail blocks DS reads >= header[0x92] * 0x80000. A custom
(non-####) game code makes a zero boundary hide the entire filesystem.
No ARM instructions or NitroFS file data is changed. DSi payloads move together.
The reserved secure-area prefix receives the standard decrypted-ROM marker.
"""
import argparse, pathlib, struct

def crc16(data):
    c=0xffff
    for b in data:
        c ^= b
        for _ in range(8): c=(c>>1) ^ (0xa001 if c&1 else 0)
    return c

def fix(data):
    b=bytearray(data)
    if len(b)<0x1000 or b[0x12]!=2: raise ValueError('Expected DS/DSi-enhanced ROM')
    read=lambda o:struct.unpack_from('<I',b,o)[0]
    start=read(0x1c0);arm7=read(0x1d0);end=read(0x210)
    if start<0x8000 or start>arm7 or arm7+read(0x1dc)>len(b) or end>len(b):
        raise ValueError('Invalid DSi payload offsets')
    # Digest/hash tables need their own relocation; this homebrew has none.
    if any(read(o) for o in range(0x1e0,0x208,4)):
        raise ValueError('Unsupported digest tables; refusing to move them')
    aligned=(start+0x7ffff)&~0x7ffff;delta=aligned-start
    if delta:b[start:start]=bytes([255])*delta
    struct.pack_into('<H',b,0x92,aligned//0x80000)
    struct.pack_into('<I',b,0x80,aligned)
    struct.pack_into('<I',b,0x1c0,aligned)
    struct.pack_into('<I',b,0x1d0,arm7+delta)
    struct.pack_into('<I',b,0x210,end+delta)
    # Device capacity is in powers of two, beginning at 128 KiB.
    capacity=0
    while (128*1024<<capacity)<len(b):capacity+=1
    b[0x14]=capacity
    arm9=read(0x20)
    if 0x4000<=arm9<0x8000:
        marker=struct.pack('<II',0xe7ffdeff,0xe7ffdeff)
        if bytes(b[arm9:arm9+8]) not in (bytes(8),marker):
            raise ValueError('Unexpected secure-area prefix; refusing to overwrite it')
        if read(0x24)-read(0x28)<0x800:
            raise ValueError('ARM9 entry overlaps reserved secure area')
        b[arm9:arm9+8]=marker
        struct.pack_into('<H',b,0x6c,crc16(b[arm9:arm9+0x4000]))
    # BlocksDS defaults this header to HOMEBREW even with GAME_TITLE set.
    # The 12-byte game title must match the intended cartridge identity.
    if b[0x0c:0x10]!=b'MDSD': raise ValueError('Unexpected game code; refusing to rename cartridge')
    b[:12]=b'Mii Maker DS'
    struct.pack_into('<H',b,0x15e,crc16(b[:0x15e]))
    return bytes(b)

def main():
    p=argparse.ArgumentParser();p.add_argument('rom',type=pathlib.Path);a=p.parse_args()
    try:
        old=a.rom.read_bytes();new=fix(old)
        if old!=new:a.rom.write_bytes(new)
    except (OSError,ValueError) as e:p.exit(2,f'ROM region fix: {e}\n')
    boundary=struct.unpack_from('<H',new,0x92)[0]*0x80000
    print(f'DS/DSi cartridge boundary: 0x{boundary:x}; header CRC verified')
if __name__=='__main__':main()
