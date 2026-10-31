"""Proportional substitute UI font. Original shared NTLG font is not supplied."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parents[1];font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',10)
lines=['/* Generated DejaVu Sans substitute, not Nintendo shared NTLG. */','static const unsigned char ui_font_width[95]={'+','.join(str(round(font.getlength(chr(c)))) for c in range(32,127))+'};','static const unsigned char ui_font_alpha[95][14][12]={']
for c in range(32,127):
 im=Image.new('L',(12,14));ImageDraw.Draw(im).text((0,-1),chr(c),font=font,fill=255)
 lines.append('{'+','.join('{'+','.join(str(im.getpixel((x,y))//17) for x in range(12))+'}' for y in range(14))+'},')
lines.append('};');(root/'source/ui_font.h').write_text('\n'.join(lines)+'\n')
