"""Unpack the supplied DS reference; preserve raw code and ROM offsets.
Usage: python3 tools/unpack_ds_reference.py /path/reference.nds /path/output
"""
from pathlib import Path
import struct,json,hashlib,re,sys
src=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True);d=src.read_bytes();rows=[]
def u32(o):return struct.unpack_from('<I',d,o)[0]
def save(name,b,offset):
 p=out/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);rows.append(dict(path=name,offset=offset,size=len(b),sha256=hashlib.sha256(b).hexdigest()))
def blz(b):
 # ARM overlays use backwards-LZ with a footer at the end of the payload.
 if len(b)<8:return None
 word,extra=struct.unpack_from('<II',b,len(b)-8);size=word&0xffffff;header=word>>24
 if not(8<=header<=11 and header<=size<=len(b) and 0<extra<16*1024*1024):return None
 x=bytearray(b)+bytearray(extra);i=len(b)-header;start=len(b)-size;o=len(x)
 try:
  while i>start:
   i-=1;flags=x[i]
   for bit in range(7,-1,-1):
    if i<=start:break
    if flags&(1<<bit):
     i-=2;v=x[i]|x[i+1]<<8;n=(v>>12)+3;dist=(v&4095)+3
     for _ in range(n):o-=1;x[o]=x[o+dist]
    else:i-=1;o-=1;x[o]=x[i]
  assert o==start,(o,start)
 except (IndexError,AssertionError):return None
 return bytes(x)
save('header.bin',d[:512],0)
for name,at in [('arm9',0x20),('arm7',0x30)]:
 off,entry,ram,size=struct.unpack_from('<4I',d,at);b=d[off:off+size];save(name+'.bin',b,off);print(name,hex(off),hex(ram),size,'entry',hex(entry),'footer',b[-16:].hex())
 dec=blz(b)
 if dec:save(name+'.decoded.bin',dec,off);print(name,'BLZ decoded',len(dec))
for name,at in [('fnt',0x40),('fat',0x48),('a9ovr',0x50),('a7ovr',0x58)]:
 off,size=struct.unpack_from('<II',d,at);save(name+'.bin',d[off:off+size],off)
fat=u32(0x48);overlay=[]
for cpu,at in [('arm9',0x50),('arm7',0x58)]:
 off,size=struct.unpack_from('<II',d,at)
 for i in range(size//32):
  oid,ram,rams,bss,sinit,einit,fid,flags=struct.unpack_from('<8I',d,off+i*32);a,b=struct.unpack_from('<II',d,fat+fid*8);raw=d[a:b];dec=blz(raw) if flags>>24&1 else raw
  name=f'overlays/{cpu}_{oid:03}.bin';save(name,raw,a)
  if dec is not None and dec!=raw:save(name+'.decoded',dec,a)
  item=dict(cpu=cpu,id=oid,ram=ram,ram_size=rams,bss_size=bss,file_id=fid,flags=hex(flags),path=name,decoded_size=len(dec) if dec else None)
  overlay.append(item)
(out/'overlays.json').write_text(json.dumps(overlay,indent=2));(out/'manifest.json').write_text(json.dumps(dict(input_sha256=hashlib.sha256(d).hexdigest(),files=rows),indent=2))
strings=[]
for p in sorted(out.rglob('*.bin*')):
 if p.name in ['fnt.bin','fat.bin','header.bin','a9ovr.bin','a7ovr.bin']:continue
 b=p.read_bytes()
 for m in re.finditer(rb'[ -~]{5,}',b):
  s=m.group().decode()
  if re.search(r'wii|nfl|rfl|mii|channel|beacon|wmb|wfs|wm_|nwc|wireless|tushin|connect|receive|send',s,re.I):strings.append(dict(file=str(p.relative_to(out)),offset=hex(m.start()),text=s))
(out/'transfer-strings.json').write_text(json.dumps(strings,indent=2))
print('overlays',len(overlay),'strings',len(strings))
for a in strings[:65]:print(a)
