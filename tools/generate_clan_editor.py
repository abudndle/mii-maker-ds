#!/usr/bin/env python3
"""Generate numeric DS editor selection curves from private original BCLAN metadata."""
import argparse
import json
import math
from pathlib import Path
TRACKS=(
 ('editor_icon_r','EditorCommon_Select','I_Tab_00','CLMC',0),
 ('editor_icon_g','EditorCommon_Select','I_Tab_00','CLMC',1),
 ('editor_icon_b','EditorCommon_Select','I_Tab_00','CLMC',2),
 ('editor_pane_r','EditorCommon_Select','P_Tab_00','CLMC',4),
 ('editor_pane_g','EditorCommon_Select','P_Tab_00','CLMC',5),
 ('editor_pane_b','EditorCommon_Select','P_Tab_00','CLMC',6),
 ('editor_part_108','EditHair_Select','P_Part_00','CLPA',6),
 ('editor_part_110','EditFace_Select','P_Part_00','CLPA',6))
def q16(v):
 if not isinstance(v,(int,float)) or not math.isfinite(v):raise ValueError('invalid source key')
 n=round(v*65536)
 if not -(2**31)<=n<2**31:raise ValueError('key outside Q16.16')
 return n
def generate(catalog):
 out=['/* Numeric-only original source curves; generated from private CLAN tracks. */',
 '#ifndef MDS_CLAN_EDITOR_GENERATED_H','#define MDS_CLAN_EDITOR_GENERATED_H','#include "clan_curve.h"']
 clips=catalog.get('clips',[])
 for name,clip_name,pane,kind,target in TRACKS:
  found=[c for c in clips if c.get('archive')=='Editor.arc.files' and c.get('clip')==clip_name]
  if len(found)!=1 or found[0].get('frames')!=6:raise ValueError('invalid original editor clip '+clip_name)
  tracks=[t for t in found[0]['tracks'] if (t['pane'],t['kind'],t['index'],t['target'],t['value_type'])==(pane,kind,0,target,2)]
  if len(tracks)!=1:raise ValueError('ambiguous CLAN channel '+name)
  keys=tracks[0]['keys']; count=4 if name.startswith('editor_part') else 2
  last=3 if name=='editor_part_108' else 5 if name=='editor_part_110' else 1
  if len(keys)!=count or keys[0][0]!=0 or keys[-1][0]!=last:raise ValueError('invalid source frame count '+name)
  previous=-1
  for key in keys:
   if len(key)!=3 or not all(math.isfinite(x) for x in key) or key[0]<previous:raise ValueError('invalid source key order '+name)
   previous=key[0]
  if name.startswith('editor_part') and (keys[0][1]!=1 or keys[-1][1]!=1):raise ValueError('unexpected scale baseline')
  out.append('static const MdsClanKey %s[]={%s};'%(name,','.join('{'+','.join(str(q16(x)) for x in key)+'}' for key in keys)))
 out.append('#endif')
 return '\n'.join(out)+'\n'
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('catalog',type=Path);p.add_argument('--output',required=True,type=Path)
 args=p.parse_args()
 args.output.write_text(generate(json.loads(args.catalog.read_text(encoding='utf-8'))),encoding='utf-8')
 print('PASS: original editor RGB and thumbnail scale source tracks')
