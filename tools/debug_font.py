"""Generate a small development-status font; not an original Nintendo font."""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',9);rows=[]
for c in range(32,127):
 im=Image.new('1',(6,11));ImageDraw.Draw(im).text((0,-2),chr(c),font=font,fill=1)
 rows.append([sum(int(im.getpixel((x,y)))<<x for x in range(6)) for y in range(11)])
p=Path(__file__).resolve().parents[1]/'source/debug_font.h';p.write_text('/* Development overlay only: Pillow default font. */\nstatic const unsigned char debug_font[95][11]={\n'+',\n'.join('{'+','.join(map(str,r))+'}' for r in rows)+'\n};\n')
