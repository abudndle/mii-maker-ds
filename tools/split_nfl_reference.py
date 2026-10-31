"""Split observed NFL resource record tables; do not infer geometry semantics.
Reads the user-supplied Tomodachi extraction, not external resource downloads.
"""
from pathlib import Path
import json,struct,hashlib
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parents[1];src=root/'reference/tomodachi/selected-assets/Cmn/Nfl/NFL_Res_LZ.bin.decoded.files/000.bin';d=src.read_bytes();out=root/'reference/tomodachi/nfl-records';out.mkdir(parents=True,exist_ok=True)
n,version=struct.unpack_from('<HH',d);assert n==20;starts=list(struct.unpack_from('<20I',d,4))+[len(d)];catalog=[];previews=[]
for group,(a,b) in enumerate(zip(starts,starts[1:])):
 count,maximum=struct.unpack_from('<HH',d,a);offsets=list(struct.unpack_from('<'+'I'*count,d,a+4));data=a+4+count*4;assert offsets[0]==0;offsets+=[b-data];assert all(0<=x<=y<=b-data for x,y in zip(offsets,offsets[1:]));records=[]
 for i,(start,end) in enumerate(zip(offsets,offsets[1:])):
  raw=d[data+start:data+end];p=out/f'group-{group:02}'/f'{i:03}.bin';p.parent.mkdir(exist_ok=True);p.write_bytes(raw);records.append(dict(index=i,offset=data+start,size=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
  if len(raw)==512 and group in [2,3,10,13,14]:
   # Diagnostic alpha interpretation only, no claimed palette/geometry decode.
   im=Image.new('RGB',(32,32),'white');pix=im.load()
   for y in range(32):
    for x in range(32):
     k=y*32+x;v=(raw[k//2]>>(4*(k%2)))&15;v=255-v*17;pix[x,y]=(v,v,v)
   if i<12:previews.append((group,i,im))
 catalog.append(dict(group=group,offset=a,size=b-a,count=count,header_maximum=maximum,observed_maximum=max(r['size'] for r in records),records=records))
(out/'catalog.json').write_text(json.dumps(dict(version=hex(version),resource_sha256=hashlib.sha256(d).hexdigest(),groups=catalog),indent=2))
im=Image.new('RGB',(640,((len(previews)+11)//12)*64),'#eeeeee');draw=ImageDraw.Draw(im)
for j,(group,index,tile) in enumerate(previews):
 x=(j%12)*53;y=(j//12)*64;im.paste(tile,(x+10,y+2));draw.text((x+1,y+38),f'{group}:{index}',fill='black')
im.save(out/'alpha-interpretation-probe.png')
print('Split',sum(x['count'] for x in catalog),'records in',len(catalog),'groups')
print('Counts:',[x['count'] for x in catalog]);print('Header maximum matches:',sum(x['header_maximum']==x['observed_maximum'] for x in catalog),'of',len(catalog))
