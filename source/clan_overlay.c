#include "clan_overlay.h"
#include <stdint.h>
uint16_t mds_clan_rgb555_mix(uint16_t base,uint16_t tint,unsigned opacity)
{
 if(opacity>255)opacity=255;
 unsigned out=(unsigned)base&0x8000u;
 for(unsigned shift=0;shift<=10;shift+=5){
  unsigned a=((unsigned)base>>shift)&31u,b=((unsigned)tint>>shift)&31u;
  unsigned v=(a*(255u-opacity)+b*opacity+127u)/255u;
  out|=v<<shift;
 }
 return (uint16_t)out;
}
static int clipped(int64_t x,int64_t len,int bound,int *lo,int *hi)
{
 if(bound<=0||len<=0)return 0;
 int64_t end=x+len;
 if(end<=0||x>=bound)return 0;
 *lo=x<0?0:(int)x;
 *hi=end>bound?bound:(int)end;
 return *hi>*lo;
}
void mds_clan_border_tint(uint16_t *frame,int width,int height,int x,int y,int w,int h,
                          uint16_t tint,unsigned opacity)
{
 if(!frame||opacity==0||w<=0||h<=0)return;
 int left,right,top,bottom;
 if(!clipped(x,w,width,&left,&right)||!clipped(y,h,height,&top,&bottom))return;
 int64_t rx=(int64_t)x+w,ry=(int64_t)y+h;
 for(int py=top;py<bottom;py++)for(int px=left;px<right;px++){
  if((int64_t)px>=x+2&&(int64_t)px<rx-2&&
     (int64_t)py>=y+2&&(int64_t)py<ry-2)continue;
  unsigned idx=(unsigned)py*(unsigned)width+(unsigned)px;
  frame[idx]=mds_clan_rgb555_mix(frame[idx],tint,opacity);
 }
}
void mds_clan_border_shadow(uint16_t *frame,int width,int height,int x,int y,int w,int h,
                            unsigned opacity)
{
 if(!frame||opacity==0||w<=0||h<=0||width<=0||height<=0)return;
 /* Source shadow opacity is used; shadow texture and geometry are provisional. */
 int left,right,top,bottom;
 const uint16_t dark=0x8000u|(3u)|(6u<<5)|(4u<<10);
 if(clipped((int64_t)x+1,w,width,&left,&right)&&
    clipped((int64_t)y+h,1,height,&top,&bottom))
  for(int px=left;px<right;px++){
   unsigned idx=(unsigned)top*(unsigned)width+(unsigned)px;
   frame[idx]=mds_clan_rgb555_mix(frame[idx],dark,opacity);
  }
 if(clipped((int64_t)x+w,1,width,&left,&right)&&
    clipped((int64_t)y+1,(int64_t)h-1,height,&top,&bottom))
  for(int py=top;py<bottom;py++){
   unsigned idx=(unsigned)py*(unsigned)width+(unsigned)left;
   frame[idx]=mds_clan_rgb555_mix(frame[idx],dark,opacity);
  }
}
