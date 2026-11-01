#!/usr/bin/env python3
"""Inspect synthetic emulator cartridge save placement without exposing Mii data.

Only use this on synthetic CI fixtures. No source Nintendo assets are accessed.
"""
import argparse
import hashlib
from pathlib import Path
import struct
import zlib

SAVE_SIZE=65536
BANK_SIZE=32768
BODY=24+100*135

def inspect(path):
    path=Path(path)
    b=path.read_bytes()
    if len(b)!=SAVE_SIZE:raise ValueError("unexpected cartridge save size")
    banks=[]
    for off in (0,BANK_SIZE):
        p=b[off:off+BANK_SIZE]
        magic=p[:4]
        valid=(magic==b"MDSV" and struct.unpack_from("<I",p,4)[0]==1 and
               struct.unpack_from("<I",p,12)[0]==BODY and
               struct.unpack_from("<I",p,BODY)[0]==zlib.crc32(p[:BODY]))
        occupied=sum(p[24+i*135]==1 for i in range(100)) if valid else 0
        banks.append({"valid":valid,"used":occupied})
    return {"size":len(b),"sha256":hashlib.sha256(b).hexdigest(),"banks":banks}

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("save",type=Path)
    x=a.parse_args()
    result=inspect(x.save)
    print("CI synthetic save:", x.save.name, "bytes:",result["size"],
          "valid banks:",sum(k["valid"] for k in result["banks"]),
          "saved Miis:",max(k["used"] for k in result["banks"]),
          "SHA256:",result["sha256"][:16])
if __name__=="__main__":main()
