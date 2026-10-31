"""Reconstruct main-menu layers and text placement from the supplied CLYT.
The shared Nintendo font is absent: DejaVu Sans is an explicit substitute.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import struct,json
from layouts import parse,render,base,root
out=root/'assets/ui/menu';out.mkdir(exist_ok=True);nitro=root/'nitrofiles/ui';messages={a['index']:a['text'] for a in json.loads((root/'assets/ui/english-messages.json').read_text())}
def path(a,n):return base/(a+'.arc.files/blyt')/(n+'.bclyt')
def layered(layers,canvas,color):
 im=Image.new('RGBA',canvas,color);hits=[]
 for a,n in layers:
  layer,_,hh=render(path(a,n),multi_texture=True);assert layer.size==canvas,(a,n,layer.size);im.alpha_composite(layer);hits+=hh
 return im,hits
def textlayer(im,p,strings):
 info=parse(p);d=p.read_bytes();o=20;byname={a['name']:a for a in info['panes']};draw=ImageDraw.Draw(im)
 while o<len(d):
  n=struct.unpack_from('<I',d,o+4)[0];b=d[o:o+n];o+=n
  if b[:4]!=b'txt1':continue
  name=b[12:28].split(b'\0')[0].decode();text=strings.get(name)
  if text is None:continue
  pane=byname[name]
  if not pane['visible']:continue
  material=info['materials'][struct.unpack_from('<I',b,80)[0]];size=struct.unpack_from('<f',b,100)[0];font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',round(size))
  x=im.width/2+pane['x'];y=im.height/2-pane['y'];draw.text((x,y),text,font=font,anchor='mm',fill=tuple(material['constant']))
 return im
bottom,hits=layered([('EDITCommon','CmnBg'),('Plaza','PlazaTop')],(320,240),(230,245,237,255))
strings={'T_HelpShadow':'?','T_Help_00':'?'}
for i,msg in enumerate([110,107,108,109]):
 strings['T_Top_%02d'%i]=messages[msg];strings['T_TopShadow_%02d'%i]=messages[msg]
textlayer(bottom,path('Plaza','PlazaTop'),strings)
top,_=layered([('Plaza','PlazaBG_Up')],(400,240),(235,245,240,255))
gallery,ghits=layered([('EDITCommon','CmnBg'),('Select','EDITSelectBase'),('Select','SelectMii')],(320,240),(235,245,240,255))
def output(name,im):
 ds=im.resize((256,192),Image.Resampling.LANCZOS);ds.save(out/(name+'.png'))
 data=b''.join(struct.pack('<H',(r>>3)|((g>>3)<<5)|((b>>3)<<10)|0x8000) for r,g,b in ds.convert('RGB').getdata());(nitro/(name+'.rgb555')).write_bytes(data)
output('home-bottom',bottom);output('home-top',top);output('gallery-bottom',gallery)
header=['/* Generated original CLYT menu bounds, uniformly scaled to DS. */','typedef struct {int x,y,w,h;int action;} MdsMenuHit;','static const MdsMenuHit home_hits[]={']
for h in hits:
 name=h['name'];action=int(name[-2:])+1 if name.startswith('B_Top_') else 5 if name=='B_Help' else 0
 if not action:continue
 r=[round(v*.8) for v in h['rect']];header.append('{%s,%d},'%(','.join(map(str,r)),action))
header+=['};','static const MdsMenuHit gallery_hits[]={']
for h in ghits:
 if not h['name'].startswith('B_Mii_'):continue
 r=[round(v*.8) for v in h['rect']];header.append('{%s,%d},'%(','.join(map(str,r)),int(h['name'][-2:])))
header+=['};'];(root/'source/menu_generated.h').write_text('\n'.join(header)+'\n')
(out/'hitboxes.json').write_text(json.dumps(dict(home=hits,gallery=ghits,text_source='Original English messages and original CLYT pane metrics',font_substitution='DejaVu Sans'),indent=2))
preview=Image.new('RGB',(256,392),(25,35,31));preview.paste(top.resize((256,192)),(0,0));preview.paste(bottom.resize((256,192)),(0,200));preview.save(out/'main-menu-reconstruction.png')
print('Generated original home menu and gallery assets; shared font substituted')
