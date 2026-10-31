"""Partial CLYT static renderer: pane hierarchy, transforms, picture UVs,
vertex colors and first texture. Does not emulate TEV stages, fonts or CLAN.
Format notes: https://docs.mikage.app/CLYT_format/
"""
from pathlib import Path
from PIL import Image,ImageDraw
import struct,json,math
root=Path(__file__).resolve().parents[1];base=root/'assets/decoded/layout';converted=root/'assets/converted/layout';out=root/'assets/ui';out.mkdir(parents=True,exist_ok=True)
u16=lambda d,o:struct.unpack_from('<H',d,o)[0]
u32=lambda d,o:struct.unpack_from('<I',d,o)[0]
def parse(p):
 d=p.read_bytes();assert d[:4]==b'CLYT';o=u16(d,6);sections=[]
 while o<len(d):
  n=u32(d,o+4);assert n>=8 and o+n<=len(d);sections.append(d[o:o+n]);o+=n
 assert len(sections)==u16(d,16)
 textures=[];mats=[];panes=[];stack=[];last=None;canvas=(320,240)
 for b in sections:
  tag=b[:4]
  if tag==b'lyt1':canvas=struct.unpack_from('<ff',b,12)
  elif tag==b'txl1':
   for i in range(u32(b,8)):
    off=12+u32(b,12+4*i);textures.append(b[off:b.index(0,off)].decode())
  elif tag==b'mat1':
   for i in range(u32(b,8)):
    off=u32(b,12+4*i);flags=u32(b,off+48);ti=u16(b,off+52) if flags&3 else None
    mats.append(dict(name=b[off:off+20].split(b'\0')[0].decode(),base=list(b[off+20:off+24]),constant=list(b[off+24:off+28]),flags=flags,texture=textures[ti] if ti is not None else None,texture_maps=[textures[u16(b,off+52+j*4)] for j in range(flags&3)],constants=[list(b[off+24+j*4:off+28+j*4]) for j in range(6)],texture_srt=[list(struct.unpack_from('<5f',b,off+52+(flags&3)*4+j*20)) for j in range((flags>>2)&3)],texture_wrap=[(b[off+54+j*4]&3,b[off+55+j*4]&3) for j in range(flags&3)]))
  elif tag==b'pas1':stack.append(last)
  elif tag==b'pae1':stack.pop()
  elif tag in [b'pan1',b'pic1',b'bnd1',b'txt1',b'wnd1']:
   name=b[12:28].split(b'\0')[0].decode();v=struct.unpack_from('<10f',b,36)
   par=stack[-1] if stack else dict(x=0,y=0,sx=1,sy=1,visible=True,alpha=255)
   pane=dict(name=name,type=tag.decode(),x=par['x']+v[0]*par['sx'],y=par['y']+v[1]*par['sy'],sx=par['sx']*v[6],sy=par['sy']*v[7],w=v[8],h=v[9],rotation=v[5],origin=b[9],alpha=b[10],visible=bool(b[8]&1) and par['visible'])
   if b[8]&2:pane['alpha']=pane['alpha']*par['alpha']//255
   if tag==b'pic1':pane.update(material=mats[u16(b,92)],colors=[list(b[a:a+4]) for a in [76,80,84,88]],uv=list(struct.unpack_from('<8f',b,96)) if u16(b,94) else [0,0,1,0,0,1,1,1])
   panes.append(pane);last=pane
 return dict(canvas=canvas,panes=panes,textures=textures,materials=mats)
def sample_map(im,u,v,mat,index):
 transforms=mat.get('texture_srt',[])
 if index<len(transforms):
  tx,ty,angle,sx,sy=transforms[index];x=(u-.5)*sx;y=(v-.5)*sy;r=math.radians(angle)
  u=x*math.cos(r)-y*math.sin(r)+.5+tx;v=x*math.sin(r)+y*math.cos(r)+.5+ty
 def wrap(x,mode):
  if mode==1:return x%1
  if mode==2:
   z=x%2;return z if z<=1 else 2-z
  return min(1,max(0,x))
 modes=mat.get('texture_wrap',[(0,0)]*(index+1));u=wrap(u,modes[index][0]);v=wrap(v,modes[index][1])
 return im.getpixel((min(im.width-1,int(u*im.width)),min(im.height-1,int(v*im.height))))

def render(p,replace_icons=None,multi_texture=False,skip_prefixes=(),only_prefixes=()):
 info=parse(p);cw,ch=map(int,info['canvas']);im=Image.new('RGBA',(cw,ch));hits=[]
 for a in info['panes']:
  if not a['visible']:continue
  if a['type']=='pic1' and (a['name'].startswith(skip_prefixes) or (only_prefixes and not a['name'].startswith(only_prefixes))):continue
  w=max(1,round(abs(a['w']*a['sx'])));h=max(1,round(abs(a['h']*a['sy'])))
  # Pane origin is a 3x3 grid: 4=center. Coordinates use Y up.
  ox=(a['origin']%3)/2;oy=(a['origin']//3)/2
  if a['sx']<0:ox=1-ox
  if a['sy']<0:oy=1-oy
  x=round(cw/2+a['x']-ox*w);y=round(ch/2-a['y']-(1-oy)*h)
  if a['type']=='bnd1':hits.append(dict(name=a['name'],rect=[x,y,w,h]));continue
  if a['type']!='pic1':continue
  if globals().get('hide_parts') and a['name'].startswith('I_Part_'):continue
  if multi_texture and a['name'] in ['P_Select','P_Make']:continue
  mat=a['material'];tex=mat['texture'];dynamic=False
  if replace_icons and a['name'].startswith('I_Part_'):
   ix=int(a['name'].rsplit('_',1)[1]);prefix,digits,start=replace_icons;tex=f'{prefix}{start+ix:0{digits}d}.bclim';dynamic=True
  if tex:
   tp=converted/p.parent.parent.name/'timg'/(tex+'.png')
   if not tp.exists():continue
   ti=Image.open(tp).convert('RGBA')
  else:ti=Image.new('RGBA',(1,1),(255,255,255,255))
  extrema=ti.getextrema();alpha_only=multi_texture and all(e==(255,255) for e in extrema[:3]) and extrema[3][0]!=extrema[3][1]
  extra=[]
  if multi_texture and tex and tex.startswith('Btn'):
   for t in mat.get('texture_maps',[])[1:]:
    q=converted/p.parent.parent.name/'timg'/(t+'.png');extra.append(Image.open(q).convert('RGBA') if q.exists() else None)
  patch=Image.new('RGBA',(w,h));pp=patch.load();uv=a['uv'];bc=mat['base'];cc=mat['constant'];cols=a['colors']
  for j in range(h):
   fy=(j+.5)/h
   for i in range(w):
    fx=(i+.5)/w
    if dynamic:u,v=fx,fy
    else:
     u=(1-fy)*((1-fx)*uv[0]+fx*uv[2])+fy*((1-fx)*uv[4]+fx*uv[6]);v=(1-fy)*((1-fx)*uv[1]+fx*uv[3])+fy*((1-fx)*uv[5]+fx*uv[7])
    tx=min(ti.width-1,max(0,int(u*ti.width)));ty=min(ti.height-1,max(0,int(v*ti.height)));c=sample_map(ti,u,v,mat,0) if multi_texture else ti.getpixel((tx,ty))
    vertex=[(1-fy)*((1-fx)*cols[0][k]+fx*cols[1][k])+fy*((1-fx)*cols[2][k]+fx*cols[3][k]) for k in range(4)]
    rgb=[int((bc[k]+(cc[k]-bc[k])*c[k]/255)*vertex[k]/255) for k in range(3)]
    if alpha_only:rgb=[int(bc[k]*vertex[k]/255) for k in range(3)]
    alpha=c[3]
    if extra and extra[0] is not None:
     line=extra[0];lc=sample_map(line,u,v,mat,1)
     color=mat['constants'][1];coverage=lc[3]/255
     rgb=[round(rgb[k]*(1-coverage)+color[k]*coverage) for k in range(3)]
    if len(extra)>1 and extra[1] is not None:
     mask=extra[1];mc=sample_map(mask,u,v,mat,2)
     alpha=alpha*mc[3]//255
    if dynamic:rgb=list(c[:3])
    pp[i,j]=tuple(rgb)+(int(alpha*vertex[3]/255*a['alpha']/255),)
  if a['sx']<0:patch=patch.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
  if a['sy']<0:patch=patch.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
  if a['rotation']:patch=patch.rotate(a['rotation'],resample=Image.Resampling.BICUBIC,expand=False)
  im.alpha_composite(patch,(x,y))
 return im,info,hits
if __name__=='__main__':
 catalog=[]
 for p in sorted(base.rglob('*.bclyt')):
  info=parse(p);rel=p.relative_to(base);q=out/rel;q.parent.mkdir(parents=True,exist_ok=True);q.with_suffix('.json').write_text(json.dumps(info,indent=2));catalog.append(dict(path=str(rel),canvas=info['canvas'],panes=len(info['panes'])))
 (out/'layouts.json').write_text(json.dumps(catalog,indent=2))
 # Reconstruct an editor state from original layered layouts.
 bottom=Image.new('RGBA',(320,240),(235,245,240,255));allhits=[]
 layers=[('EDITCommon','EditBG',None),('Editor','EditorCommon',None),('Editor','EditHair',('IconHair',3,0))]
 for archive,name,swap in layers:
  p=base/(archive+'.arc.files')/'blyt'/(name+'.bclyt');im,info,hits=render(p,swap,multi_texture=True);bottom.alpha_composite(im);allhits.extend(dict(layer=name,**h) for h in hits)
 bottom.save(out/'editor-hair-320x240.png');bottom.resize((256,192),Image.Resampling.LANCZOS).save(out/'editor-hair-ds.png')
 (out/'editor-hair-hits.json').write_text(json.dumps(allhits,indent=2))
 top=Image.new('RGBA',(400,240),(235,245,240,255))
 for archive,name in [('EDITCommon','CmnBg_Up'),('Editor','Edit_up')]:
  im,_,_=render(base/(archive+'.arc.files')/'blyt'/(name+'.bclyt'),multi_texture=True);top.alpha_composite(im)
 top.resize((256,192),Image.Resampling.LANCZOS).save(out/'editor-top-ds.png')
 preview=Image.new('RGB',(512,804),'#202524');draw=ImageDraw.Draw(preview);draw.text((12,5),'Original ROM layout reconstruction - static layers',fill='white')
 preview.paste(top.resize((512,384)),(0,24));preview.paste(bottom.resize((512,384)),(0,420));preview.save(out/'ds-ui-reconstruction.png')
 print('Parsed',len(catalog),'layouts; rendered original layered hair editor')
 # Native DS assets and real layout hitboxes, embedded with NitroFS.
 nitro=root/'nitrofiles/ui';nitro.mkdir(parents=True,exist_ok=True)
 categories=[('EditFace','IconFaceline',2,2),('EditFaceTLine','IconFaceT_line',2,3),('EditFaceTMake','IconFaceT_make',2,4),('EditHair','IconHair',3,5),('EditEye','IconEye',2,8),('EditEyebrow','IconEyebrow',2,15),('EditNose','IconNose',2,22),('EditMouth','IconMouth',2,25),('EditGlasses','IconGlass',2,30),('EditMustache','IconMustache',2,34),('EditBeard','IconBeard',2,35),('EditMole','IconMole',2,39),('EditBody',None,2,43)]
 def raw(im):
  return b''.join(struct.pack('<H',(r>>3)|((g>>3)<<5)|((b>>3)<<10)|0x8000) for r,g,b in im.convert('RGB').getdata())
 (nitro/'top.rgb555').write_bytes(raw(top.resize((256,192),Image.Resampling.LANCZOS)))
 header=['/* Generated from supplied ROM CLYT layouts. */','typedef struct {int x,y,w,h;} UiRect;','typedef struct {const char *layout,*prefix;int digits,field,count;UiRect slots[12];} UiCategory;','static const UiCategory ui_categories[]={']
 for name,prefix,digits,field in categories:
  p=base/'Editor.arc.files/blyt'/(name+'.bclyt');inf=parse(p)
  # Omit placeholder icon picture panes, retain original frames and controls.
  original_render=render
  # Render uses a per-call omission list through an optional module flag.
  globals()['hide_parts']=True
  layer,_,hits=render(p,multi_texture=True,skip_prefixes=('P_SlideShadow_','P_Slide_') if name=='EditBody' else ())
  globals()['hide_parts']=False
  bg=Image.new('RGBA',(320,240),(235,245,240,255))
  for archive,nm in [('EDITCommon','EditBG'),('Editor','EditorCommon')]:bg.alpha_composite(render(base/(archive+'.arc.files')/'blyt'/(nm+'.bclyt'),multi_texture=True)[0])
  bg.alpha_composite(layer)
  if name in ['EditFace','EditFaceTLine','EditFaceTMake']:bg.alpha_composite(render(base/'Editor.arc.files/blyt/EditFaceTab.bclyt',multi_texture=True)[0])
  bg=bg.resize((256,192),Image.Resampling.LANCZOS);(nitro/(name+'.rgb555')).write_bytes(raw(bg))
  slots=[]
  for a in inf['panes']:
   if a['name'].startswith('I_Part_'):
    w=a['w']*a['sx'];h=a['h']*a['sy'];slots.append((int(a['name'].rsplit('_',1)[1]),[round((160+a['x']-w/2)*.8),round((120-a['y']-h/2)*.8),round(w*.8),round(h*.8)]))
  slots=[v for i,v in sorted(slots)][:12]
  header.append('{"%s",%s,%d,%d,%d,{%s}},'%(name,'"'+prefix+'"' if prefix else 'NULL',digits,field,len(slots),','.join('{'+','.join(map(str,v))+'}' for v in slots)))
  if prefix:
   for tex in (converted/'Editor.arc.files/timg').glob(prefix+'*.bclim.png'):
    import re
    if not re.fullmatch(re.escape(prefix)+r'\d+\.bclim.png',tex.name):continue
    im=Image.open(tex).convert('RGBA');dest=root/'nitrofiles/art';dest.mkdir(exist_ok=True)
    data=b''.join(struct.pack('<H',(r>>3)|((g>>3)<<5)|((b>>3)<<10)|(0x8000 if a>=128 else 0)) for r,g,b,a in im.getdata())
    stem=tex.name.replace('.bclim.png','');(dest/(stem+'.bin')).write_bytes(struct.pack('<HH',im.width,im.height)+data)
 slider,_,_=render(base/'Editor.arc.files/blyt/EditBody.bclyt',multi_texture=True,only_prefixes=('P_SlideShadow_00','P_Slide_00'))
 bbox=slider.getbbox();slider=slider.crop(bbox);slider=slider.resize((round(slider.width*.8),round(slider.height*.8)),Image.Resampling.LANCZOS)
 data=b''.join(struct.pack('<H',(r>>3)|((g>>3)<<5)|((b>>3)<<10)|(0x8000 if a>=128 else 0)) for r,g,b,a in slider.getdata())
 (root/'nitrofiles/art/BodySlider0.bin').write_bytes(struct.pack('<HH',slider.width,slider.height)+data)
 header+=['};',f'#define UI_BODY_SLIDER_W {slider.width}',f'#define UI_BODY_SLIDER_H {slider.height}','#define UI_CATEGORY_COUNT (sizeof(ui_categories)/sizeof(ui_categories[0]))']
 (root/'source/ui_generated.h').write_text('\n'.join(header)+'\n')
 print('Generated',len(categories),'NitroFS UI pages and embedded original feature icons')
