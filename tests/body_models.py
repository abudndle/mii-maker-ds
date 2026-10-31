import pathlib,sys,struct
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from body_models import pose_data,extract
pose,_=pose_data();assert len(pose)==17 and abs(pose['skl_root'][8]-67.658699)<.0001
for name,vertices in [('MaleBody',1428),('FemaleBody',1440)]:
 p=ROOT/'nitrofiles/models'/f'{name}.bin';before=p.read_bytes();model=extract(name,pose)
 assert before==p.read_bytes(), 'Conversion not reproducible'
 assert model['vertices']==vertices and len(model['bones'])==18
 assert len(before)==56+vertices*12 and before[:4]==b'BOD2'
 assert abs(model['head_anchor'][1]-108.658309)<.0001
 for group in model['groups']:
  assert group['vertex_data_bytes']%group['vertex_stride']==0
  assert group['skinning'] in [0,1]
  assert group['triangles']>0 and group['index_streams']
print('PASS: original CGFX geometry/rig/Wait00 sample and reproducible bounded native conversion')
