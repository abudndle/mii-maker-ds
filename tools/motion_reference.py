#!/usr/bin/env python3
"""Full geometry conversion oracle, separate from the runtime delta transform."""
from body_models import ROOT,Reader,pose_data,extract
import struct
clips=sorted((ROOT/'assets/decoded/models/MiiAnim.arc.files').glob('*.bcskla'))
with (ROOT/'validation/motion-reference.bin').open('wb') as out:
 for gender,name in enumerate(('MaleBody','FemaleBody')):
  for index,p in enumerate(clips):
   r=Reader(p);count=int(r.f(r.data.index(b'CANM')+20))+1
   for frame in sorted({0,count//2,count-1}):
    data=extract(name,pose_data(frame,p.stem)[0],False,wide=True)
    out.write(struct.pack('<4I',gender,index,frame,len(data)));out.write(data)
   print(name,p.stem,flush=True)
