#!/usr/bin/env python3
"""Trace every supplied original motion to its source curves and DS binding."""
from body_models import ROOT,Reader,pose_data
import json,hashlib,math
records=[]
for p in sorted((ROOT/'assets/decoded/models/MiiAnim.arc.files').glob('*.bcskla')):
 r=Reader(p);at=r.data.index(b'CANM');last=r.f(at+20);record={'source':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(r.data).hexdigest(),'last_frame':last,'source_flags':r.u(at+16),'runtime_state':'Wait00 source-pose playback' if p.stem=='Wait00' else 'original asset retained; full scene binding not implemented'}
 try:
  samples=[]
  for frame in [0,last/2,last]:
   pose,_=pose_data(frame,p.stem)
   assert all(math.isfinite(v) for channels in pose.values() for v in channels.values())
   samples.append({'frame':frame,'bone_channels':pose})
  record['samples']=samples;record['curve_validation']='first/mid/last samples decoded'
 except (ValueError,KeyError,IndexError,AssertionError) as e:record['curve_validation']='unsupported';record['reason']=str(e)
 records.append(record)
result={'original_clips':len(records),'validated_clips':sum(r['curve_validation']!='unsupported' for r in records),'notice':'Decoded curve samples are source data, not evidence of complete runtime scene/animation parity.','clips':records}
gui=[]
for p in sorted((ROOT/'assets/decoded/layout').rglob('*.bclan')):
 b=p.read_bytes();gui.append({'source':str(p.relative_to(ROOT)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'magic':b[:4].decode('ascii',errors='replace'),'runtime_state':'original GUI motion retained; full track playback not implemented'})
result['gui_animation_tracks']=gui;result['gui_track_count']=len(gui)
(ROOT/'reference/animation-map.json').write_text(json.dumps(result,indent=2)+'\n');print(f"Validated {result['validated_clips']}/{len(records)} original animation clips")
for r in records:
 if r['curve_validation']=='unsupported':print(r['source'],r['reason'])
