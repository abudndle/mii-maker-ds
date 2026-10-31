#!/usr/bin/env python3
"""Original 3DS QR menu and face/entire-Mii selector, with generated touch bounds."""
from pathlib import Path
import struct,json
from PIL import Image
from layouts import render,parse
from profile_assets import texts,messages,p,root
out=root/'nitrofiles/ui';header=['/* Original QR and photo-selector touch bounds. */','typedef struct {int page,x,y,w,h,action;} MdsQrHit;','static const MdsQrHit qr_hits[]={'];records=[]
for name,archive,layout,labels,page in [('qr-menu','QR','BtnQR',{'T_BtnQr_00':messages[177],'T_BtnQr_01':messages[176],'T_BtnQr_02':messages[178]},0),('photo-select','Dialog','DialogPhotoSelect',{'T_Select':messages[178],'T_Face':messages[179],'T_Body':messages[180]},1)]:
 for variant in (['dsi','ds'] if not page else ['']):
  bg=render(p('EDITCommon','EditBG'),multi_texture=True)[0]
  if page:bg.alpha_composite(render(p('Dialog','DialogBase00'),multi_texture=True)[0])
  omit=tuple(x['name'] for x in parse(p(archive,layout))['panes'] if x['name'].endswith('_00')) if variant=='ds' else ()
  layer,_,hits=render(p(archive,layout),multi_texture=True,skip_prefixes=omit);bg.alpha_composite(layer)
  active={k:v for k,v in labels.items() if not(variant=='ds' and k.endswith('_00'))};texts(bg,p(archive,layout),active)
  im=bg.resize((256,192),Image.Resampling.LANCZOS).convert('RGB');suffix=('-'+variant) if variant else ''
  (out/(name+suffix+'.rgb555')).write_bytes(b''.join(struct.pack('<H',0x8000|(r>>3)|((g>>3)<<5)|((b>>3)<<10)) for r,g,b in im.get_flattened_data()))
  if variant=='ds':continue
  for h in hits:
   action={'B_BtnQr_00':4,'B_BtnQr_01':1,'B_BtnQr_02':2,'B_Face':3,'B_Body':2}.get(h['name'])
   if action:
    rect=[round(v*.8) for v in h['rect']];header.append('{%d,%s,%d},'%(page,','.join(map(str,rect)),action));records.append(dict(name=h['name'],page=page,rect=rect,action=action))
header+=['};','#define MDS_QR_HITS (sizeof(qr_hits)/sizeof(qr_hits[0]))'];(root/'source/qr_generated.h').write_text('\n'.join(header)+'\n');(root/'reference/qr-layouts.json').write_text(json.dumps(records,indent=2)+'\n')
