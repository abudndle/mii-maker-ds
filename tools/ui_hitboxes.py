"""Generate original CLYT control bounds for native touch interaction."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1];names=['EditFace','EditFaceTLine','EditFaceTMake','EditHair','EditEye','EditEyebrow','EditNose','EditMouth','EditGlasses','EditMustache','EditBeard','EditMole','EditBody'];lines=['/* Original CLYT button bounds, scaled uniformly by 0.8. */','typedef struct {const char *name;unsigned category;UiRect rect;} UiHit;','static const UiHit ui_hits[]={']
for i,n in enumerate(names):
 data=json.loads((root/'assets/ui/Editor.arc.files/blyt'/(n+'.json')).read_text())
 if i in [0,1,2]:data['panes']+=json.loads((root/'assets/ui/Editor.arc.files/blyt/EditFaceTab.json').read_text())['panes']
 for p in data['panes']:
  if p['type']!='bnd1':continue
  w=p['w']*p['sx'];h=p['h']*p['sy'];r=[round((160+p['x']-w/2)*.8),round((120-p['y']-h/2)*.8),round(w*.8),round(h*.8)]
  lines.append('{%s,%d,{%s}},'%(json.dumps(p['name']),i,','.join(map(str,r))))
lines+=['};','#define UI_HIT_COUNT (sizeof(ui_hits)/sizeof(ui_hits[0]))'];(root/'source/ui_hits.h').write_text('\n'.join(lines)+'\n')
