#include "motion.h"
#include <string.h>
#include <math.h>
#include <limits.h>
static uint32_t word(const uint8_t*p){return p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static int32_t integer(const uint8_t*p){uint32_t v=word(p);return v<=INT32_MAX?(int32_t)v:-1-(int32_t)(UINT32_MAX-v);}
static int16_t coord(const uint8_t*p){unsigned v=p[0]|(unsigned)p[1]<<8;return (int16_t)(v<32768?(int)v:(int)v-65536);}
static void putcoord(uint8_t*p,int v){for(unsigned k=0;k<4;k++)p[k]=(uint8_t)((uint32_t)v>>(k*8));}
int mds_motion_open(MdsMotion*m,FILE*f)
{
 if(!m)return 0;
 memset(m,0,sizeof *m);if(!f)return 0;
 uint8_t h[32];if(fseek(f,0,SEEK_END))return 0;
 long size=ftell(f);if(size<32||fseek(f,0,SEEK_SET)||fread(h,1,32,f)!=32)return 0;
 unsigned count=word(h+8),stride=word(h+16);
 if(memcmp(h,"MSP1",4)||word(h+4)!=1||!count||count>MDS_MOTION_CLIPS||word(h+12)!=MDS_MOTION_BONES||stride!=MDS_MOTION_FRAME_BYTES||word(h+20)!=32||word(h+24)!=(unsigned long)size||word(h+28))return 0;
 uint32_t next=32+count*40;
 for(unsigned i=0;i<count;i++){
  uint8_t e[40];if(fread(e,1,40,f)!=40)goto bad;
  MdsMotionClip*c=&m->clips[i];memcpy(c->name,e,24);
  if(!memchr(c->name,0,24)||!c->name[0])goto bad;
  for(unsigned k=0;c->name[k];k++)if(!((c->name[k]>='A'&&c->name[k]<='Z')||(c->name[k]>='a'&&c->name[k]<='z')||(c->name[k]>='0'&&c->name[k]<='9')||c->name[k]=='_'))goto bad;
  for(unsigned j=0;j<i;j++)if(!strcmp(c->name,m->clips[j].name))goto bad;
  c->offset=word(e+24);c->count=word(e+28);c->loop=word(e+32);c->fps=word(e+36);
  if(c->offset!=next||!c->count||c->count>7200||c->loop>1||!c->fps||c->fps>60)goto bad;
  uint64_t end=(uint64_t)next+(uint64_t)c->count*stride;if(end>(uint64_t)size)goto bad;
  next=(uint32_t)end;
 }
 if(next!=(unsigned long)size)goto bad;
 m->file=f;m->count=count;return 1;
bad:memset(m,0,sizeof *m);return 0;
}
int mds_motion_find(const MdsMotion*m,const char*name)
{
 if(!m||!m->file||!name)return -1;
 for(unsigned i=0;i<m->count;i++)if(!strcmp(name,m->clips[i].name))return (int)i;
 return -1;
}
int mds_motion_cycle(const MdsMotion*m,int current,int direction)
{
 if(!m||!m->file||!m->count||!direction)return -1;
 int count=(int)m->count;
 if(current<0||current>=count)return direction>0?0:count-1;
 return direction>0?(current+1)%count:(current+count-1)%count;
}
unsigned mds_motion_frame(const MdsMotionClip*c,uint32_t ticks,int*ended)
{
 if(ended)*ended=0;
 if(!c||!c->count||!c->fps)return 0;
 uint64_t f=(uint64_t)ticks*c->fps/60;
 if(c->loop)return (unsigned)(f%c->count);
 if(f>=c->count){if(ended)*ended=1;return c->count-1;}
 return (unsigned)f;
}
static unsigned root(unsigned n)
{
 unsigned result=0,bit=1u<<30;
 while(bit>n)bit>>=2;
 while(bit){if(n>=result+bit){n-=result+bit;result=(result>>1)+bit;}else result>>=1;bit>>=2;}
 return result;
}
int mds_motion_pose(MdsMotion*m,unsigned clip,unsigned frame,const void*base,size_t size,void*out,size_t capacity)
{
 if(!m||!m->file||clip>=m->count||frame>=m->clips[clip].count||!base||!out||base==out||size<56)return 0;
 const uint8_t*b=base;unsigned vertices=word(b+4);
 if(memcmp(b,"BOD2",4)||!vertices||vertices>12000||vertices%3||size!=56+(size_t)vertices*12||capacity<56+(size_t)vertices*18)return 0;
 uint8_t bytes[MDS_MOTION_FRAME_BYTES];
 uint32_t offset=m->clips[clip].offset+frame*MDS_MOTION_FRAME_BYTES;
 if(fseek(m->file,(long)offset,SEEK_SET)||fread(bytes,1,sizeof bytes,m->file)!=sizeof bytes)return 0;
 float head[12];memcpy(head,bytes,48);
 for(unsigned i=0;i<12;i++)if(!isfinite(head[i])||fabsf(head[i])>4096)return 0;
 int32_t matrices[MDS_MOTION_BONES][12];
 for(unsigned i=0;i<MDS_MOTION_BONES;i++)for(unsigned j=0;j<12;j++){
  int32_t v=integer(bytes+48+i*48+j*4);
  if(v>4096*65536||v< -4096*65536)return 0;
  matrices[i][j]=v;
 }
 /* Preflight all references before writing any result. */
 for(unsigned i=0;i<vertices;i++)if(b[56+i*12+10]>=MDS_MOTION_BONES)return 0;
 uint8_t*d=out;memcpy(d,b,8);memcpy(d,"BOD3",4);memcpy(d+8,bytes,48);
 for(unsigned i=0;i<vertices;i++){
  const uint8_t*s=b+56+i*12;uint8_t*t=d+56+i*18;const int32_t*a=matrices[s[10]];
  memcpy(t+15,s+9,3);
  int v[3]={coord(s),coord(s+2),coord(s+4)},n[3];
  for(unsigned k=0;k<3;k++){
   int64_t p=(int64_t)a[k*4]*v[0]+(int64_t)a[k*4+1]*v[1]+(int64_t)a[k*4+2]*v[2]+(int64_t)a[k*4+3]*128;
   p=p>=0?(p+32768)/65536:-((-p+32768)/65536);
   if(p< -524288||p>524288)return 0;
   putcoord(t+k*4,(int)p);
   int64_t q=(int64_t)a[k*4]*(int8_t)s[6]+(int64_t)a[k*4+1]*(int8_t)s[7]+(int64_t)a[k*4+2]*(int8_t)s[8];
   q/=4096;if(q< -30000||q>30000)return 0;n[k]=(int)q;
  }
  unsigned length=root((unsigned)(n[0]*n[0])+(unsigned)(n[1]*n[1])+(unsigned)(n[2]*n[2]));
  for(unsigned k=0;k<3;k++){int q=length?n[k]*127/(int)length:0;if(q>127)q=127;if(q< -127)q=-127;t[12+k]=(uint8_t)q;}
 }
 return 1;
}
