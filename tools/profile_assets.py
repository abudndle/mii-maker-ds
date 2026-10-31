"""Map original profile/dialog/secondary-tab art, English text and hit bounds."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import struct,json
from layouts import parse,render,base,root
out=root/'nitrofiles/ui';messages={x['index']:x['text'] for x in json.loads((root/'assets/ui/english-messages.json').read_text())}
def p(ar,n):return base/(ar+'.arc.files/blyt')/(n+'.bclyt')
def texts(im,path,strings):
 info=parse(path);b=path.read_bytes();at=20;panes={x['name']:x for x in info['panes']};draw=ImageDraw.Draw(im)
 while at<len(b):
  n=struct.unpack_from('<I',b,at+4)[0];d=b[at:at+n];at+=n
  if d[:4]!=b'txt1':continue
  name=d[12:28].split(b'\0')[0].decode();text=strings.get(name)
  if text is None or not panes[name]['visible']:continue
  pane=panes[name];mat=info['materials'][struct.unpack_from('<H',d,80)[0]];size=struct.unpack_from('<f',d,100)[0];font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',max(10,round(size)))
  draw.multiline_text((160+pane['x'],120-pane['y']),text,font=font,anchor='mm',align='center',fill=tuple(mat['constant']))
 return im
profile_text={'T_Nickname':messages[45],'T_Favorite':messages[58],'T_Gender':messages[48],'T_Open':messages[62],'T_Color':messages[47],'T_Admission':messages[59],'T_Birthday':messages[51],'T_Makeup':messages[56]}
configs=[('profile','Editor','Profile',profile_text),('gender','Dialog','DialogGender',{'T_Gender':messages[6],'T_Male':messages[49],'T_Female':messages[50]}),('create-gender','Dialog','DialogFirstGender',{'T_Gender':messages[6],'T_Male':messages[49],'T_Female':messages[50]}),('birthday','Dialog','DialogBirthday',{'T_Birthday_00':messages[22],'T_Bgmonth':messages[23],'T_BgDay':messages[24],'Slash':'/'}),('shirt','Dialog','DialogColor',{'T_Color_00':messages[21]}),('sharing','Dialog','DialogOpen',{'T_Admission':'Allow this Mii to be shared?','T_BtnCommon_00':messages[60],'T_BtnCommon_01':messages[61]}),('copying','Dialog','DialogAdmission',{'T_Admission':'Allow this Mii to be copied?','T_BtnCommon_00':messages[60],'T_BtnCommon_01':messages[61]}),('confirm','Dialog','DialogBtnCommon02',{'T_BtnCommon_00':messages[73],'T_BtnCommon_01':messages[74]}),('accessories','Editor','EditEtcTab',{})]
header=['/* Original profile/dialog button bounds, scaled from 320x240. */','typedef struct {const char *name;int page,x,y,w,h;} ProfileHit;','static const ProfileHit profile_hits[]={'];inventory={}
for page,(name,ar,n,strings) in enumerate(configs):
 im=Image.new('RGBA',(320,240),(235,245,240,255));bg=render(p('EDITCommon','EditBG'),multi_texture=True)[0];im.alpha_composite(bg)
 if ar=='Dialog':im.alpha_composite(render(p('Dialog','DialogBase00'),multi_texture=True)[0])
 layer,info,hits=render(p(ar,n),multi_texture=True,skip_prefixes=('I_Favorite','I_MyMii','P_Color_') if name=='profile' else ());im.alpha_composite(layer);texts(im,p(ar,n),strings)
 ds=im.resize((256,192),Image.Resampling.LANCZOS);(root/'assets/ui'/f'{name}-native.png').parent.mkdir(exist_ok=True,parents=True);ds.save(root/'assets/ui'/f'{name}-native.png')
 data=b''.join(struct.pack('<H',(r>>3)|((g>>3)<<5)|((b>>3)<<10)|0x8000) for r,g,b in ds.convert('RGB').getdata());(out/(name+'.rgb555')).write_bytes(data)
 inventory[name]=dict(page=page,layout=f'{ar}/{n}',hits=hits)
 for h in hits:
  x,y,w,hg=[round(v*.8) for v in h['rect']];header.append('{%s,%d,%d,%d,%d,%d},'%(json.dumps(h['name']),page,x,y,w,hg))
button,_,_=render(p('Editor','Profile'),multi_texture=True,only_prefixes=('P_BtnL_00','P_BtnR_00'))
button=button.crop(button.getbbox());button=button.resize((round(button.width*.8),round(button.height*.8)),Image.Resampling.LANCZOS)
raw=b''.join(struct.pack('<H',(r>>3)|((g>>3)<<5)|((b>>3)<<10)|(0x8000 if a>=128 else 0)) for r,g,b,a in button.getdata())
(root/'nitrofiles/art/ProfileButton0.bin').write_bytes(struct.pack('<HH',button.width,button.height)+raw)
header+=['};','#define PROFILE_HIT_COUNT (sizeof(profile_hits)/sizeof(profile_hits[0]))'];(root/'source/profile_generated.h').write_text('\n'.join(header)+'\n');(root/'reference/profile-layouts.json').write_text(json.dumps(inventory,indent=2)+'\n')
print('Generated original profile, gender, birthday, color, permission, confirmation and accessory layouts')
