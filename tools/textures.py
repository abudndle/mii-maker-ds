"""Decode observed uncompressed BCLIM formats; output PNG and DS RGB555+A1.
Format facts: https://github.com/kwsch/png2bclim/blob/master/png2bclim/BCLIM.cs
Independent implementation; no external decoder code copied.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import struct,json,collections
root=Path(__file__).resolve().parents[1];out=root/'assets/converted';rows=[]
def expand(v,n):return v*255//((1<<n)-1)
def decode(p):
 d=p.read_bytes();assert d[-40:-36]==b'CLIM';w,h,f,n=struct.unpack_from('<HHII',d,len(d)-12);assert n==len(d)-40
 bits={0:8,1:8,2:8,3:16,5:16,7:16,8:16,12:4,13:4}[f]
 sw=max(8,1<<(w-1).bit_length());sh=max(8,1<<(h-1).bit_length());assert sw*sh*bits//8==n,(p,w,h,n)
 im=Image.new('RGBA',(w,h));pix=im.load()
 for y in range(h):
  for x in range(w):
   morton=sum(((x>>b)&1)<<(2*b) | ((y>>b)&1)<<(2*b+1) for b in range(3));i=((y//8)*(sw//8)+x//8)*64+morton
   if bits==4:v=(d[i//2]>>((i%2)*4))&15
   elif bits==8:v=d[i]
   else:v=struct.unpack_from('<H',d,i*2)[0]
   if f==0:c=(v,v,v,255)
   elif f==1:c=(255,255,255,v)
   elif f==2:c=((v>>4)*17,)*3+((v&15)*17,)
   elif f==3:c=(v>>8,)*3+(v&255,)
   elif f==5:c=(expand(v>>11,5),expand((v>>5)&63,6),expand(v&31,5),255)
   elif f==7:c=(expand(v>>11,5),expand((v>>6)&31,5),expand((v>>1)&31,5),(v&1)*255)
   elif f==8:c=((v>>12)*17,((v>>8)&15)*17,((v>>4)&15)*17,(v&15)*17)
   elif f==12:c=(v*17,)*3+(255,)
   else:c=(255,255,255,v*17)
   pix[x,y]=c
 return im,f
for p in (root/'assets/decoded').rglob('*.bclim'):
 im,f=decode(p);rel=p.relative_to(root/'assets/decoded');q=out/rel;q.parent.mkdir(parents=True,exist_ok=True);im.save(str(q)+'.png')
 data=bytearray()
 for r,g,b,a in im.getdata():data+=struct.pack('<H',(r>>3)|((g>>3)<<5)|((b>>3)<<10)|(0x8000 if a>=128 else 0))
 Path(str(q)+'.rgb555').write_bytes(data);rows.append(dict(path=str(rel),width=im.width,height=im.height,format=f))
(out/'textures.json').write_text(json.dumps(rows,indent=2))
# Human QA: original feature art, not a game screenshot.
chosen=list((out/'layout/Editor.arc.files/timg').glob('IconHair0*.png'))[:24]+list((out/'layout/Editor.arc.files/timg').glob('IconEye0*.png'))[:12]
sheet=Image.new('RGB',(800,((len(chosen)+7)//8)*84),'#d8d8d8');draw=ImageDraw.Draw(sheet)
for i,p in enumerate(chosen):
 im=Image.open(p);x=(i%8)*100;y=(i//8)*84;sheet.paste(im,(x+(100-im.width)//2,y+4),im);draw.text((x+3,y+58),p.name.replace('.bclim.png',''),fill='black')
sheet.save(out/'original-feature-contact-sheet.png')
print('Converted',len(rows),'BCLIM textures',collections.Counter(x['format'] for x in rows))
