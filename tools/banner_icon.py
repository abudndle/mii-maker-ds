"""Convert the user's original 48x48 SMDH icon to the DS 16-color banner."""
from pathlib import Path
from PIL import Image
import struct,json,hashlib
root=Path(__file__).resolve().parents[1];p=root/'assets/exefs/icon';b=p.read_bytes();assert b[:4]==b'SMDH' and len(b)==0x36c0
im=Image.new('RGB',(48,48))
for y in range(48):
 for x in range(48):
  m=sum(((x>>k)&1)<<(2*k)|((y>>k)&1)<<(2*k+1) for k in range(3));i=((y//8)*6+x//8)*64+m;v=struct.unpack_from('<H',b,0x24c0+i*2)[0];im.putpixel((x,y),((v>>11)*255//31,((v>>5)&63)*255//63,(v&31)*255//31))
im.save(root/'assets/ui/original-icon.png');im.resize((32,32),Image.Resampling.LANCZOS).quantize(colors=16).save(root/'assets/ui/original-icon.gif')
(root/'reference/banner-icon.json').write_text(json.dumps(dict(source=str(p.relative_to(root)),sha256=hashlib.sha256(b).hexdigest(),icon_offset='0x24c0',source_size=[48,48],ds_size=[32,32],colors=16),indent=2)+'\n')
