#!/usr/bin/env python3
"""Streamable, full source-frame rigid transforms for every original body clip.

Geometry stays in the original Wait00 frame-zero BOD2; source world matrices
are converted to deltas from that reference. No replacement mesh or motion.
The source framerate is still assumed to be 30 Hz, pending executable mapping.
"""
from body_models import ROOT, Reader, pose_data, skeleton
import numpy as np
import struct, json, hashlib

HEADER=32
ENTRY=40
BONES=18
STRIDE=48+BONES*48

def main():
 clips=[]
 for p in sorted((ROOT/'assets/decoded/models/MiiAnim.arc.files').glob('*.bcskla')):
  r=Reader(p); at=r.data.index(b'CANM'); last=r.f(at+20)
  if not last.is_integer() or not 0<=last<7200:raise ValueError('Source duration')
  clips.append((p.stem,int(last)+1,r.u(at+16)&1,p))
 if len(clips)!=53:raise ValueError('Expected complete supplied clip inventory')
 report={'format':'MSP1','source_fps_assumption':30,'frames_per_sample':1,'bones':BONES,'frame_bytes':STRIDE,'outputs':[],'clips':[]}
 for name in ('MaleBody','FemaleBody'):
  _,base=skeleton(name,pose_data()[0]); inv={i:np.linalg.inv(base[i]) for i in base}
  if set(base)!=set(range(BONES)):raise ValueError('Unexpected skeleton indices')
  start=HEADER+ENTRY*len(clips); entries=[]
  for clip,count,loop,p in clips:
   entries.append(struct.pack('<24s4I',clip.encode(),start,count,loop,30));start+=count*STRIDE
  out=ROOT/'nitrofiles/models'/(name+'.msp')
  with out.open('wb') as f:
   f.write(struct.pack('<4s7I',b'MSP1',1,len(clips),BONES,STRIDE,HEADER,start,0));f.write(b''.join(entries))
   for clip,count,loop,p in clips:
    for frame in range(count):
     _,world=skeleton(name,pose_data(frame,clip)[0])
     f.write(struct.pack('<12f',*world[10][:3,:].ravel()))
     for i in range(BONES):
      mat=(world[i]@inv[i])[:3,:]
      q=np.rint(mat*65536).astype(np.int64)
      if not np.isfinite(mat).all() or np.max(np.abs(q))>0x7fffffff:raise ValueError('Transform range')
      f.write(struct.pack('<12i',*q.ravel()))
    print(name,clip,count,'frames',flush=True)
  assert out.stat().st_size==start
  report['outputs'].append({'path':str(out.relative_to(ROOT)),'bytes':start,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
 for clip,count,loop,p in clips:
  report['clips'].append({'name':clip,'source':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'frames':count,'source_loop':bool(loop)})
 (ROOT/'reference/motion-pack.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
