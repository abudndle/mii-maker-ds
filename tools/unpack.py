import pathlib,struct,json

def lz11(d):
 n=int.from_bytes(d[1:4],'little');i=4
 if not n:n=int.from_bytes(d[4:8],'little');i=8
 out=bytearray()
 while len(out)<n:
  flags=d[i];i+=1
  for bit in range(7,-1,-1):
   if len(out)>=n:break
   if not flags&(1<<bit):out.append(d[i]);i+=1;continue
   a=d[i];b=d[i+1];i+=2;t=a>>4
   if t==0:
    c=d[i];i+=1;length=((a&15)<<4 | b>>4)+17;dist=((b&15)<<8|c)+1
   elif t==1:
    c,e=d[i:i+2];i+=2;length=((a&15)<<12|b<<4|c>>4)+273;dist=((c&15)<<8|e)+1
   else:length=t+1;dist=((a&15)<<8|b)+1
   assert dist<=len(out)
   for _ in range(length):out.append(out[-dist])
 assert len(out)==n
 return bytes(out)
root=pathlib.Path(__file__).resolve().parents[1];dest=root/'assets/decoded';rows=[]
for p in (root/'assets/romfs').rglob('*'):
 if not p.is_file():continue
 d=p.read_bytes();rel=p.relative_to(root/'assets/romfs')
 if d[0]==17:d=lz11(d)
 target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(d)
 if d[:4]!=b'darc':continue
 table,size=struct.unpack_from('<II',d,16);count=struct.unpack_from('<I',d,table+8)[0];names=table+count*12;stack=[]
 for i in range(count):
  no,off,end=struct.unpack_from('<III',d,table+i*12);isdir=no>>24;pos=names+(no&0xffffff);stop=pos
  while d[stop:stop+2]!=b'\0\0':stop+=2
  name=d[pos:stop].decode('utf-16le')
  while stack and i>=stack[-1][0]:stack.pop()
  if i==0:stack.append((end,pathlib.Path()));continue
  path=(stack[-1][1] if stack else pathlib.Path())/name
  assert not path.is_absolute() and '..' not in path.parts
  if isdir:stack.append((end,path));continue
  assert off+end<=len(d)
  q=dest/(str(rel)+'.files')/path;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(d[off:off+end]);rows.append({'archive':str(rel),'file':str(path),'size':end,'magic':d[off:off+4].decode('ascii',errors='replace')})
(dest/'inventory.json').write_text(json.dumps(rows,indent=2));print('Archive members:',len(rows));from collections import Counter;print(Counter(x['magic'] for x in rows))
