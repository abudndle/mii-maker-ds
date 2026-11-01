#include "view.h"
#include <limits.h>
static const int16_t sine_q14[MDS_VIEW_STEPS]={
 0,4240,8192,11585,14189,15826,16384,15826,14189,11585,8192,4240,
 0,-4240,-8192,-11585,-14189,-15826,-16384,-15826,-14189,-11585,-8192,-4240
};
unsigned mds_view_step(unsigned current,int direction)
{
 current%=MDS_VIEW_STEPS;
 if(!direction)return current;
 return (current+(direction>0?1:MDS_VIEW_STEPS-1))%MDS_VIEW_STEPS;
}
static int32_t clamp_coordinate(int64_t value)
{
 if(value>INT32_MAX)return INT32_MAX;
 if(value<INT32_MIN)return INT32_MIN;
 return (int32_t)value;
}
void mds_view_rotate(int32_t *x,int32_t *z,unsigned step)
{
 if(!x||!z)return;
 step%=MDS_VIEW_STEPS;
 if(!step)return;
 int32_t sine=sine_q14[step],cosine=sine_q14[(step+6)%MDS_VIEW_STEPS];
 int64_t ox=*x,oz=*z;
 *x=clamp_coordinate((ox*cosine+oz*sine)/16384);
 *z=clamp_coordinate((oz*cosine-ox*sine)/16384);
}
