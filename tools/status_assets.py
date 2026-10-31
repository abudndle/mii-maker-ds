#!/usr/bin/env python3
"""Extract actual 3DS profile status icons with their original pane tint."""
from pathlib import Path
import struct
from PIL import Image
from layouts import render
root=Path(__file__).resolve().parents[1];source=root/'assets/decoded/layout/Editor.arc.files/blyt/Profile.bclyt'
for pane,name in [('I_MyMii','StatusPersonal'),('I_Favorite','StatusFavorite')]:
 im,_,_=render(source,multi_texture=True,only_prefixes=(pane,));box=im.getbbox();assert box
 im=im.crop(box);im=im.resize((min(32,round(im.width*.8)),min(32,round(im.height*.8))),Image.Resampling.LANCZOS)
 data=b''.join(struct.pack('<H',(r>>3)|((g>>3)<<5)|((b>>3)<<10)|(0x8000 if a>=128 else 0)) for r,g,b,a in im.get_flattened_data())
 (root/'nitrofiles/art'/f'{name}.bin').write_bytes(struct.pack('<HH',*im.size)+data)
 im.save(root/'assets/ui'/f'{name}.png')
 print(pane,im.size)
