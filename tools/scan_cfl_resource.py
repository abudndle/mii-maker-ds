"""Search extracted Mii Maker bytes for embedded CFL-style archive tables.
Structural scan only; false positives are not treated as original assets.
"""
import struct,re,json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1];seen=set();files=0;total=0;hits=[]
for p in (root/'assets').rglob('*'):
 if not p.is_file() or p.suffix in ['.png','.json','.rgb555','.txt']:continue
 d=p.read_bytes();sha=hashlib.sha256(d).digest()
 if sha in seen:continue
 seen.add(sha);files+=1;total+=len(d)
 for m in re.finditer(b'\x14\x00',d):
  base=m.start()
  if len(d)-base<84:continue
  offsets=struct.unpack_from('<20I',d,base+4)
  if any(o<84 or o>len(d)-base-8 for o in offsets):continue
  if list(offsets)!=sorted(offsets) or len(set(offsets))!=20:continue
  valid=True;counts=[]
  for i,o in enumerate(offsets):
   end=offsets[i+1] if i<19 else len(d)-base;count=struct.unpack_from('<H',d,base+o)[0];counts.append(count)
   if 4+(count+1)*4>end-o:valid=False;break
  if valid:hits.append(dict(file=str(p.relative_to(root)),offset=base,section_counts=counts,classification='structural candidate only'))
plausible=[h for h in hits if all(h['section_counts'][s]>0 for s in [2,5,10,17])]
for h in hits:h['rejection_reason']='No face/hair/eye/mouth records' if h not in plausible else 'Requires item/geometry validation'
result=dict(unique_files=files,bytes_scanned=total,candidates=hits,plausible_head_archives=plausible,scope='Supplied Mii Maker extraction and decoded assets; no external system archive',genuine_resource_found=None if plausible else False)
(root/'validation/cfl-resource-scan.json').write_text(json.dumps(result,indent=2));print('Scanned',files,'unique files;',len(hits),'structural candidates')
