#include "animation.h"
#include <string.h>
static unsigned word(const uint8_t*p){return p[0]|(unsigned)p[1]<<8|(unsigned)p[2]<<16|(unsigned)p[3]<<24;}
int mds_animation_open(MdsAnimation*a,const void*bytes,size_t size)
{
 if(!a)return 0;
 memset(a,0,sizeof *a);
 if(!bytes||size<24)return 0;
 const uint8_t*p=bytes;
 unsigned count=word(p+4),stride=word(p+8),period=word(p+12),step=word(p+16),fps=word(p+20);
 if(memcmp(p,"ANI1",4)||!count||count>240||stride<56||stride>144056||!step||step>120||!period||period>7200||!fps||fps>60)return 0;
 if((period+step-1)/step!=count||size!=24+(size_t)count*stride)return 0;
 for(unsigned i=0;i<count;i++){
  const uint8_t*pose=p+24+(size_t)i*stride;
  unsigned vertices=word(pose+4);
  if(memcmp(pose,"BOD2",4)||vertices>12000||vertices%3||stride!=56+vertices*12)return 0;
 }
 a->data=p+24;a->size=size-24;a->pose_bytes=stride;a->count=count;a->period=period;a->step=step;a->fps=fps;
 return 1;
}
const void*mds_animation_pose(const MdsAnimation*a,uint32_t vblanks,unsigned*index)
{
 if(!a||!a->data||!a->count)return NULL;
 /* Decompose before multiplication to avoid overflow over long sessions. */
 unsigned frame=(((uint64_t)vblanks*a->fps)/60)%a->period;
 unsigned i=frame/a->step;
 if(index)*index=i;
 return a->data+(size_t)i*a->pose_bytes;
}
