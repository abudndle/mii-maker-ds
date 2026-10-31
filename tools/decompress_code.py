"""Decompress this ROM's backwards-LZ code and audit face resource paths."""
from pathlib import Path
import struct,re,json
root=Path(__file__).resolve().parents[1];p=root/'assets/exefs/.code';d=bytearray(p.read_bytes());bottom=struct.unpack_from('<I',d,len(d)-8)[0];extra=struct.unpack_from('<I',d,len(d)-4)[0];start=len(d)-(bottom&0xffffff);index=len(d)-(bottom>>24);out=len(d)+extra;d.extend(b'\0'*extra)
while index>start:
 index-=1;flags=d[index]
 for bit in range(7,-1,-1):
  if index<=start:break
  if flags&(1<<bit):
   index-=2;val=d[index]|d[index+1]<<8;length=(val>>12)+3;offset=(val&0xfff)+3
   for _ in range(length):out-=1;d[out]=d[out+offset]
  else:index-=1;out-=1;d[out]=d[index]
(root/'assets/exefs/code-decompressed.bin').write_bytes(d)
rows=[]
for m in re.finditer(rb'[ -~]{6,}',d):
 text=m.group().decode()
 if re.search(r'CFL|FFL|face|Face|/.*\.dat|rom:|shared',text):rows.append(dict(offset=hex(m.start()),text=text))
(root/'assets/exefs/face-resource-strings.json').write_text(json.dumps(rows,indent=2))
print('Code decompressed',len(d),'bytes');print(json.dumps(rows[:70],indent=2))
