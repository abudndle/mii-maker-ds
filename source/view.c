#include "view.h"
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
void mds_view_rotate(int32_t *x,int32_t *z,unsigned step)
{
 if(!x||!z)return;
 step%=MDS_VIEW_STEPS;
 if(!step)return;
 int32_t sine=sine_q14[step],cosine=sine_q14[(step+6)%MDS_VIEW_STEPS];
 int64_t ox=*x,oz=*z;
 *x=(int32_t)((ox*cosine+oz*sine)/16384);
 *z=(int32_t)((oz*cosine-ox*sine)/16384);
}
