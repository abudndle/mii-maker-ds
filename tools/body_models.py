#!/usr/bin/env python3
"""Independent bounded CGFX body/rig reader, plus sampled original Wait00 pose.
Format field observations cross-checked against gdkchan/SPICA (not vendored).
Exports original geometry; does not substitute hand-built body shapes.
"""
from pathlib import Path
import struct,json,hashlib,math
import numpy as np
from animation_curves import sample
ROOT=Path(__file__).resolve().parents[1]
class Reader:
 def __init__(self,p):self.data=p.read_bytes();self.path=p
 def unpack(self,fmt,o):
  n=struct.calcsize('<'+fmt)
  if o<0 or o+n>len(self.data):raise ValueError(f'{self.path}: bounds at {o:x}')
  return struct.unpack_from('<'+fmt,self.data,o)
 def u(self,o):return self.unpack('I',o)[0]
 def f(self,o):return self.unpack('f',o)[0]
 def ptr(self,o):
  v=self.unpack('i',o)[0]
  if not v:return None
  p=o+v
  if not 0<=p<len(self.data):raise ValueError('Pointer out of bounds')
  return p
 def string(self,p):
  end=self.data.index(0,p);return self.data[p:end].decode()
 def dictionary(self,p):
  if self.data[p:p+4]!=b'DICT':raise ValueError('Expected dictionary')
  count=self.u(p+8)
  if count>1000:raise ValueError('Dictionary count')
  return [self.ptr(p+28+i*16+12) for i in range(count)]
 def pointers(self,n,p):
  if n>1000 or (n and p is None):raise ValueError('Pointer-table count')
  return [self.ptr(p+4*i) for i in range(n)]
def pose_data(frame=0):
 r=Reader(ROOT/'assets/decoded/models/MiiAnim.arc.files/Wait00.bcskla');canm=r.data.index(b'CANM');d=r.ptr(canm+28)
 # CANM: magic/revision/name/group/loop/frames + dictionary count/pointer.
 result={}
 for p in r.dictionary(d):
  name=r.string(r.ptr(p+4));flags=r.u(p);kind=r.u(p+16)
  if kind!=5:raise ValueError('Expected scalar transform animation')
  channels={}
  for j in range(10):
   if not(flags&(1<<(16+j))):channels[j]=sample(r,p+20+j*4,bool(flags&(1<<(6+j))),frame)
  result[name]=channels
 return result,r

def matrix(scale,rotation,translation):
 x,y,z=rotation;cx,sx=math.cos(x),math.sin(x);cy,sy=math.cos(y),math.sin(y);cz,sz=math.cos(z),math.sin(z)
 rx=np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
 ry=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])
 rz=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
 out=np.eye(4);out[:3,:3]=rz@ry@rx@np.diag(scale);out[:3,3]=translation;return out

def extract(name,pose,write=True):
 r=Reader(ROOT/'assets/decoded/models'/f'{name}.bcmdl')
 objs=[i-4 for i in range(4,len(r.data)-4) if r.data[i:i+4]==b'SOBJ']
 skeleton=next(p for p in objs if r.u(p)==0x02000000);bones={}
 for p in r.dictionary(r.ptr(skeleton+28)):
  nm=r.string(r.ptr(p));index,parent=r.unpack('ii',p+8);s=list(r.unpack('3f',p+32));rot=list(r.unpack('3f',p+44));t=list(r.unpack('3f',p+56))
  for j,v in pose.get(nm,{}).items():
   if j<3:s[j]=v
   elif j<6:rot[j-3]=v
   elif j>=7:t[j-7]=v
  bones[index]=dict(name=nm,parent=parent,scale=s,rotation=rot,translation=t)
 world={}
 def bone_world(i):
  if i in world:return world[i]
  b=bones[i];m=matrix(b['scale'],b['rotation'],b['translation'])
  if b['parent']>=0:m=bone_world(b['parent'])@m
  world[i]=m;return m
 for i in bones:bone_world(i)
 meshes=[p for p in objs if r.u(p)==0x01000000];shapes=[p for p in objs if r.u(p)==0x10000001]
 groups=[];flat=[]
 for mesh in meshes:
  si,mi=r.unpack('II',mesh+24);shape=shapes[si];shape_offset=np.array(r.unpack('3f',shape+32))
  submeshes=r.pointers(r.u(shape+44),r.ptr(shape+48));buffers=r.pointers(r.u(shape+56),r.ptr(shape+60))
  inter=next((p for p in buffers if r.u(p)==0x40000002),None)
  if inter is None:raise ValueError('No interleaved data')
  length=r.u(inter+20);data=r.ptr(inter+24);stride=r.u(inter+36)
  if not stride or length%stride:raise ValueError('Bad vertex length')
  attributes=[]
  for p in r.pointers(r.u(inter+40),r.ptr(inter+44)):
   attributes.append((r.u(p+4),*r.unpack('IIfI',p+36)))
  fixed={}
  for p in buffers:
   if r.u(p)==0x80000000:
    sem=r.u(p+4);n=r.u(p+16);fixed[sem]=r.unpack(str(n)+'f',r.ptr(p+28)) if n else ()
  def vertex(i,palette,skinning):
   if i>=length//stride:raise ValueError('Index exceeds vertex count')
   values=dict(fixed)
   for sem,typ,n,scale,off in attributes:
    fmt={0x1400:'b',0x1401:'B',0x1402:'h',0x1406:'f'}[typ]
    values[sem]=[v*scale for v in r.unpack(str(n)+fmt,data+i*stride+off)]
   pos=np.array(values[0][:3])+shape_offset;norm=np.array(values.get(1,(0,0,1))[:3])
   bi=int(values.get(7,(0,))[0]);bone=palette[bi] if palette else 0
   if skinning==1:
    m=world[bone];pos=(m@np.append(pos,1))[:3];norm=m[:3,:3]@norm
   elif skinning!=0:raise ValueError('Smooth skinning not implemented')
   norm/=max(np.linalg.norm(norm),1e-9)
   return [*pos.tolist(),*norm.tolist(),mi,bone]
  for sub in submeshes:
   pal=list(r.unpack(str(r.u(sub))+'I',r.ptr(sub+4)));skin=r.u(sub+8)
   faces=r.pointers(r.u(sub+12),r.ptr(sub+16));start=len(flat);streams=[]
   for face in faces:
    for desc in r.pointers(r.u(face),r.ptr(face+4)):
     typ=r.u(desc);mode=r.data[desc+4];ln=r.u(desc+8);idx=r.ptr(desc+12)
     if mode!=0:raise ValueError('Not triangle topology')
     fmt='H' if typ==0x1403 else 'B' if typ==0x1401 else None
     if not fmt:raise ValueError('Unsupported index format')
     streams.append(dict(descriptor_offset=hex(desc),raw_index_offset=hex(idx),raw_index_bytes=ln,index_format=hex(typ)))
     indices=r.unpack(str(ln//struct.calcsize(fmt))+fmt,idx)
     if len(indices)%3:raise ValueError('Triangle alignment')
     flat.extend(vertex(i,pal,skin) for i in indices)
   groups.append(dict(shape=si,original_shape_offset=hex(shape),original_submesh_offset=hex(sub),vertex_buffer_offset=hex(inter),vertex_data_offset=hex(data),vertex_data_bytes=length,vertex_stride=stride,attributes=[dict(semantic=sem,data_type=hex(typ),components=n,scale=scale,offset=off) for sem,typ,n,scale,off in attributes],index_streams=streams,material=mi,skinning=skin,bone_palette=pal,triangles=(len(flat)-start)//3,flat_vertex_range=[start,len(flat)]))
 out=ROOT/'nitrofiles/models';out.mkdir(parents=True,exist_ok=True)
 # Remove the original shadow-only material. Runtime supplies its own projected shadow.
 visible=[v for v in flat if v[6]!=2]
 binary=bytearray(struct.pack('<4sI12f',b'BOD2',len(visible),*world[10][:3,:].ravel()))
 for v in visible:
  coords=[round(c*128) for c in v[:3]]
  if any(abs(c)>32767 for c in coords):raise ValueError('Body coordinate range')
  binary+=struct.pack('<3h3bBBx',*coords,*[max(-127,min(127,round(c*127))) for c in v[3:6]],v[6],v[7])
 if write:(out/(name+'.bin')).write_bytes(binary)
 else:return bytes(binary)
 mins=np.min(np.array(visible)[:,:3],axis=0).tolist();maxs=np.max(np.array(visible)[:,:3],axis=0).tolist()
 return dict(source=str(r.path.relative_to(ROOT)),source_sha256=hashlib.sha256(r.data).hexdigest(),bones=bones,groups=groups,vertices=len(visible),bounds=[mins,maxs],head_anchor=world[10][:3,3].tolist(),output=str((out/(name+'.bin')).relative_to(ROOT)))
def main():
 pose,r=pose_data();models=[extract(n,pose) for n in ['MaleBody','FemaleBody']]
 out=ROOT/'reference/body-models.json';out.write_text(json.dumps(dict(animation=str(r.path.relative_to(ROOT)),animation_sha256=hashlib.sha256(r.data).hexdigest(),frame=0,pose_channels=pose,models=models),indent=2)+'\n')
 for m in models:print(m['source'],m['vertices'],'vertices; bounds',m['bounds'],'head',m['head_anchor'])
if __name__=='__main__':main()
