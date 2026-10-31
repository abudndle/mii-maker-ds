"""Inventory DS NitroFS and unpack selected Mii/communication reference assets.
Usage: python3 tools/reference_assets.py reference.nds reference/tomodachi
"""
from pathlib import Path
import struct,json,hashlib,sys
src=Path(sys.argv[1]);out=Path(sys.argv[2]);data=src.read_bytes();fnt,fnts,fat,fats=struct.unpack_from('<4I',data,0x40);rows=[];visited=set()
def walk(dirid,parent):
 assert dirid not in visited;visited.add(dirid)
 off,fid,par=struct.unpack_from('<IHH',data,fnt+(dirid&4095)*8);p=fnt+off
 while data[p]:
  kind=data[p];p+=1;n=kind&127;name=data[p:p+n].decode('ascii');p+=n;assert name not in ['.','..'] and '/' not in name
  path=parent/name
  if kind&128:sub=struct.unpack_from('<H',data,p)[0];p+=2;walk(sub,path)
  else:
   a,b=struct.unpack_from('<II',data,fat+fid*8);assert a<=b<=len(data);rows.append(dict(path=str(path),id=fid,offset=a,size=b-a,magic=data[a:a+16].hex()));fid+=1
walk(0xf000,Path());out.mkdir(parents=True,exist_ok=True)
(out/'nitrofs-inventory.json').write_text(json.dumps(dict(input_sha256=hashlib.sha256(data).hexdigest(),files=rows),indent=2))
def lz10(d):
 assert d[0]==16;n=int.from_bytes(d[1:4],'little');i=4;b=bytearray()
 while len(b)<n:
  flag=d[i];i+=1
  for bit in range(7,-1,-1):
   if len(b)>=n:break
   if flag&(1<<bit):
    a,c=d[i:i+2];i+=2;length=(a>>4)+3;dist=((a&15)<<8|c)+1;assert dist<=len(b)
    for _ in range(min(length,n-len(b))):b.append(b[-dist])
   else:b.append(d[i]);i+=1
 return bytes(b)
selected=0;wii=[];warnings=[]
for row in rows:
 name=row['path']
 if not(name.startswith('Msg/') or name=='Cmn/Nfl/NFL_Res_LZ.bin' or any(n in name for n in ['SceneMiiEdit2','SceneTestDrawMii','SceneTushin','List_TushinList','List_TushinItemList'])):continue
 selected+=1;raw=data[row['offset']:row['offset']+row['size']];p=out/'selected-assets'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);d=lz10(raw);Path(str(p)+'.decoded').write_bytes(d)
 if name.startswith('Msg/'):
  for needle in ['Portrait Channel','Connect to DS','WiiConnect24']:
   start=0
   while True:
    at=d.find(needle.encode('utf-16le'),start)
    if at<0:break
    a=max(0,at-64);a+=(at-a)%2;b=min(len(d),at+400);b-=(b-a)%2
    wii.append(dict(path=name,offset=at,text=d[a:b].decode('utf-16le',errors='replace')));start=at+2
 if d[:4]!=b'NARC':continue
 o=16;records=None;members=[]
 while o<len(d):
  if len(d)-o<8:
   warnings.append(dict(path=name,section_offset=o,error='short section header'));break
  n=struct.unpack_from('<I',d,o+4)[0]
  if n<8:
   warnings.append(dict(path=name,section_offset=o,error='invalid section size'));break
  if o+n>len(d):
   warnings.append(dict(path=name,section_offset=o,declared_size=n,available=len(d)-o));n=len(d)-o
  if d[o:o+4]==b'BTAF':count=struct.unpack_from('<H',d,o+8)[0];records=[struct.unpack_from('<II',d,o+12+8*i) for i in range(count)]
  if d[o:o+4]==b'GMIF':
   dest=Path(str(p)+'.decoded.files');dest.mkdir(exist_ok=True)
   for i,(a,b) in enumerate(records):
    if not 0<=a<=b<=n-8:
     warnings.append(dict(path=name,member=i,declared_start=a,declared_end=b,available=n-8));continue
    blob=d[o+8+a:o+8+b];(dest/f'{i:03}.bin').write_bytes(blob);members.append(dict(index=i,size=len(blob),magic=blob[:16].hex(),sha256=hashlib.sha256(blob).hexdigest()))
  o+=n
 Path(str(p)+'.decoded.json').write_text(json.dumps(members,indent=2))
(out/'archive-boundary-warnings.json').write_text(json.dumps(warnings,indent=2))
(out/'wii-message-evidence.json').write_text(json.dumps(wii,ensure_ascii=False,indent=2))
print('Inventoried',len(rows),'files; extracted',selected,'Mii/communication assets; Wii message hits',len(wii),'boundary warnings',len(warnings))
