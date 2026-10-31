"""Independent bounded reader for the supplied CGFX scalar animation curves.
Quantization fields cross-checked against SPICA at 82acbd6 (format reference).
"""
import bisect,math

def sample(r,field,constant,frame):
 if constant:return r.f(field)
 g=r.ptr(field)
 if r.u(g+12)&2:return r.f(g+16)
 if r.u(g+16)!=1:raise ValueError('Multiple curve segments are unsupported')
 c=r.ptr(g+20);flags=r.u(c+8);fmt=flags>>5;count=r.u(c+12)
 if not 0<count<=4096:raise ValueError('Invalid key count')
 value_scale,value_offset,frame_scale=1.,0.,1.;p=c+20
 if fmt not in (0,3,6):value_scale,value_offset,frame_scale=r.unpack('3f',p);p+=12
 keys=[]
 def signed(v,bits):return v-(1<<bits) if v&(1<<(bits-1)) else v
 for _ in range(count):
  si=so=0.
  if fmt==0:t,v,si,so=r.unpack('4f',p);p+=16
  elif fmt==1:
   packed,si,so=r.unpack('Ihh',p);p+=8;t=packed&4095;v=packed>>12;si/=256;so/=256
  elif fmt==2:
   t=r.data[p];v=r.unpack('H',p+1)[0];packed=int.from_bytes(r.data[p+3:p+6],'little');p+=6
   si=signed(packed&4095,12)/32;so=signed(packed>>12,12)/32
  elif fmt==3:t,v,si=r.unpack('3f',p);so=si;p+=12
  elif fmt==4:t,v,si=r.unpack('HHh',p);t/=32;si/=256;so=si;p+=6
  elif fmt==5:
   packed=r.u(p);p+=4;t=packed&255;v=(packed>>8)&4095;si=signed(packed>>20,12)/32;so=si
  elif fmt==6:t,v=r.unpack('2f',p);p+=8
  elif fmt==7:packed=r.u(p);p+=4;t=packed&4095;v=packed>>12
  else:raise ValueError('Unknown scalar quantization')
  key=(t*frame_scale,v*value_scale+value_offset,si,so)
  if not all(math.isfinite(x) for x in key) or (keys and key[0]<=keys[-1][0]):raise ValueError('Invalid curve keys')
  keys.append(key)
 if frame<=keys[0][0]:return keys[0][1]
 if frame>=keys[-1][0]:return keys[-1][1]
 k=bisect.bisect_right([x[0] for x in keys],frame)-1
 a,b=keys[k:k+2];dt=b[0]-a[0];w=(frame-a[0])/dt
 if fmt>=6:return a[1]+(b[1]-a[1])*w if flags&4 else a[1]
 # Cubic Hermite interpolation with source per-frame tangents.
 return (2*w**3-3*w*w+1)*a[1]+(w**3-2*w*w+w)*dt*a[3]+(-2*w**3+3*w*w)*b[1]+(w**3-w*w)*dt*b[2]
