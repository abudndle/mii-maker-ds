#include "clan_curve.h"
#include <limits.h>
#define ONE ((int64_t)65536)
static int32_t narrow(int64_t n)
{
 if(n>INT32_MAX)return INT32_MAX;
 if(n<INT32_MIN)return INT32_MIN;
 return (int32_t)n;
}
static size_t locate(const MdsClanKey *keys,size_t count,int32_t frame)
{
 size_t lo=0,hi=count;
 while(lo<hi){
  size_t mid=lo+(hi-lo)/2;
  if(keys[mid].frame<=frame)lo=mid+1;else hi=mid;
 }
 return lo?lo-1:0;
}
int32_t mds_clan_visibility_eval(const MdsClanKey *keys,size_t count,int32_t frame)
{
 if(!keys||!count)return 0;
 return keys[locate(keys,count,frame)].value;
}
int32_t mds_clan_curve_eval(const MdsClanKey *keys,size_t count,int32_t frame)
{
 if(!keys||!count)return 0;
 size_t i=locate(keys,count,frame);
 if(frame<=keys[0].frame)return keys[0].value;
 if(i+1>=count)return keys[i].value;
 const MdsClanKey *a=&keys[i],*b=&keys[i+1];
 int64_t dt=(int64_t)b->frame-a->frame;
 if(dt<=0)return b->value;
 int64_t t=((int64_t)frame-a->frame)*ONE/dt;
 if(t<0)t=0;
 if(t>ONE)t=ONE;
 int64_t t2=t*t/ONE,t3=t2*t/ONE;
 int64_t h00=2*t3-3*t2+ONE,h10=t3-2*t2+t;
 int64_t h01=-2*t3+3*t2,h11=t3-t2;
 int64_t m0=dt*a->tangent/ONE,m1=dt*b->tangent/ONE;
 return narrow((h00*a->value+h10*m0+h01*b->value+h11*m1)/ONE);
}
