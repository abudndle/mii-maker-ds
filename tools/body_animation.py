#!/usr/bin/env python3
"""Bake sampled original Wait00 poses without replacing original triangles."""
from body_models import ROOT,pose_data,extract
import struct,json,hashlib

def main():
 _,r=pose_data();c=r.data.index(b'CANM');last=r.f(c+20)
 if last!=119:raise ValueError('Unexpected original idle duration')
 samples=list(range(0,120,5));metadata={'source':str(r.path.relative_to(ROOT)),'source_sha256':hashlib.sha256(r.data).hexdigest(),'source_last_frame':last,'source_frames':samples,'source_fps_assumption':30,'quantization':'positions 1/128, normals 1/127; original rigid geometry and head bone per pose','format_reference':'https://github.com/gdkchan/SPICA','format_reference_commit':'82acbd63695e4ef8b95a92ce884f25ec1044788f','outputs':[]}
 streams={n:[] for n in ['MaleBody','FemaleBody']}
 for f in samples:
  pose,_=pose_data(f)
  for n in streams:streams[n].append(extract(n,pose,False))
 for n,poses in streams.items():
  assert len(set(map(len,poses)))==1
  base=(ROOT/'nitrofiles/models'/f'{n}.bin').read_bytes();assert poses[0]==base
  data=struct.pack('<4s5I',b'ANI1',len(poses),len(base),120,5,30)+b''.join(poses)
  out=ROOT/'nitrofiles/models'/f'{n}.ani';out.write_bytes(data)
  metadata['outputs'].append({'path':str(out.relative_to(ROOT)),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'distinct_poses':len(set(poses))})
  print(n,len(poses),'source poses',len(data),'bytes')
 (ROOT/'reference/body-animation.json').write_text(json.dumps(metadata,indent=2)+'\n')
if __name__=='__main__':main()
