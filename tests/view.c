#include "view.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <limits.h>
static int absolute(int v){return v<0?-v:v;}
int main(void)
{
 assert(mds_view_step(0,1)==1);
 assert(mds_view_step(0,-1)==23);
 assert(mds_view_step(23,1)==0);
 assert(mds_view_step(24,1)==1);
 assert(mds_view_step(25,-1)==0);
 assert(mds_view_step(11,0)==11);
 assert(mds_view_step(0,INT_MIN)==23);
 assert(mds_view_step(0,INT_MAX)==1);
 int32_t x=1000,z=0;
 mds_view_rotate(&x,&z,0);assert(x==1000&&z==0);
 mds_view_rotate(&x,&z,6);assert(x==0&&z==-1000);
 mds_view_rotate(&x,&z,6);assert(x==-1000&&z==0);
 mds_view_rotate(&x,&z,6);assert(x==0&&z==1000);
 mds_view_rotate(&x,&z,6);assert(x==1000&&z==0);
 mds_view_rotate(&x,&z,24);assert(x==1000&&z==0);
 mds_view_rotate(NULL,&z,1);mds_view_rotate(&x,NULL,1);
 x=30000;z=-11000;
 mds_view_rotate(&x,&z,3);
 assert(absolute(x-13436)<4&&absolute(z+28991)<4);
 /* Source BOD3 vertices can approach 524288 units. Arithmetic must be
  * wide enough and not wrap like 32-bit intermediate multiplies. */
 x=524288;z=-524288;
 mds_view_rotate(&x,&z,3);
 assert(absolute(x)<100&&absolute(z+741455)<100);
 /* Saturate extreme model coordinates rather than wrapping. */
 x=INT32_MAX;z=INT32_MAX;
 mds_view_rotate(&x,&z,3);
 assert(x==INT32_MAX&&z==0);
 x=INT32_MIN;z=INT32_MIN;
 mds_view_rotate(&x,&z,3);
 assert(x==INT32_MIN&&z==0);
 puts("PASS: original Mii L/R preview camera steps, wrapping, 90-degree poses, wide coordinates");
}
