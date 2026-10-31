"""Extract the supplied original number BCFNT (two A8 sheets, sparse CMAP)."""
from pathlib import Path
from PIL import Image
import struct,json
root=Path(__file__).resolve().parents[1];p=root/'assets/decoded/font/nintendo_NTLG_DB_001_40px_number.bcfnt';b=p.read_bytes()
t=b.index(b'TGLP');cw,ch,baseline,_=struct.unpack_from('<4B',b,t+8);sheet_size=struct.unpack_from('<I',b,t+12)[0];count,fmt,cols,rows,w,h=struct.unpack_from('<6H',b,t+16);at=struct.unpack_from('<I',b,t+28)[0]
assert fmt==8 and sheet_size==w*h and at+count*sheet_size<=len(b)
d=b.index(b'CWDH');first,last=struct.unpack_from('<HH',b,d+8);c=b.index(b'CMAP');assert struct.unpack_from('<H',b,c+12)[0]==2;n=struct.unpack_from('<H',b,c+20)[0]
glyphs=[];metrics=[];codes=[]
for i in range(n):
 code,index=struct.unpack_from('<HH',b,c+22+i*4);left,width,advance=struct.unpack_from('<bBB',b,d+16+(index-first)*3);sheet=index//(cols*rows);slot=index%(cols*rows);ox=slot%cols*(cw+1)+1;oy=slot//cols*(ch+1)+1;im=Image.new('L',(cw,ch))
 for y in range(ch):
  for x in range(cw):
   px=ox+x;py=oy+y;m=sum(((px>>k)&1)<<(k*2)|((py>>k)&1)<<(k*2+1) for k in range(3));offset=((py//8)*(w//8)+px//8)*64+m
   im.putpixel((x,y),b[at+sheet*sheet_size+offset])
 codes.append(code);metrics.append((left,width,advance));glyphs.append(im.tobytes())
output=root/'nitrofiles/font';output.mkdir(parents=True,exist_ok=True);(output/'number.bin').write_bytes(struct.pack('<4sHHH',b'NUM1',cw,ch,n)+bytes(codes)+b''.join(struct.pack('<bBB',*m) for m in metrics)+b''.join(glyphs));(root/'reference/number-font.json').write_text(json.dumps(dict(source=str(p.relative_to(root)),cell=[cw,ch],characters=''.join(chr(c) for c in codes),sheets=count,format='A8 Morton tiles'),indent=2)+'\n')
print('Extracted original numeral glyphs:', ''.join(chr(c) for c in codes))
