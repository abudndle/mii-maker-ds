"""Extract plaintext NCCH ExeFS and IVFC RomFS; no keys or decryption."""
import struct, pathlib, hashlib, json, sys
src=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]); d=src.read_bytes()
assert d[256:260]==b'NCCH', 'Expected NCCH at offset zero'
u32=lambda b,o:struct.unpack_from('<I',b,o)[0]
records=[]
def save(name,data,offset):
 p=out/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 records.append(dict(path=name,size=len(data),rom_offset=offset,sha256=hashlib.sha256(data).hexdigest(),magic=data[:16].hex()))
e=u32(d,0x1a0)*512
for i in range(10):
 h=e+16*i;name=d[h:h+8].rstrip(b'\0').decode('ascii');off,size=struct.unpack_from('<II',d,h+8)
 if name:save('exefs/'+name,d[e+512+off:e+512+off+size],e+512+off)
r=u32(d,0x1b0)*512; assert d[r:r+4]==b'IVFC'
# RomFS level 3 starts at the next block boundary following IVFC master hash.
log=struct.unpack_from('<I',d,r+0x4c)[0]; block=1<<log
base=r+((0x60+u32(d,r+8)+block-1)//block)*block
assert u32(d,base)==0x28,hex(base)
_,dh,ds,dm,dms,fh,fs,fm,fms,fd=struct.unpack_from('<10I',d,base)
seen=set()
def directory(pos,parent):
 assert pos not in seen,'Cycle';seen.add(pos)
 at=base+dm+pos;par,sibling,child,files,hashnext,nlen=struct.unpack_from('<6I',d,at)
 name=d[at+24:at+24+nlen].decode('utf-16le');path=parent/name if name else parent
 assert name not in ['..','.'] and '/' not in name
 f=files
 while f!=0xffffffff:
  a=base+fm+f;pa,nxt,off,size,h,n=struct.unpack_from('<IIQQII',d,a);nm=d[a+32:a+32+n].decode('utf-16le')
  assert '/' not in nm and nm not in ['..','.']
  start=base+fd+off;assert start+size<=len(d)
  save(str(path/nm),d[start:start+size],start);f=nxt
 c=child
 while c!=0xffffffff:
  directory(c,path);c=u32(d,base+dm+c+4)
directory(0,pathlib.Path('romfs'))
out.mkdir(parents=True,exist_ok=True)
(out/'manifest.json').write_text(json.dumps(dict(input_sha256=hashlib.sha256(d).hexdigest(),product=d[0x150:0x160].rstrip(b'\0').decode(),romfs_level3=base,files=records),indent=2))
print('Extracted',len(records),'files; level3',hex(base))
for a in records:print(a['path'],a['size'])
