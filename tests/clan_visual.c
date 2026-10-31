#include "clan_home.h"
#include "clan_overlay.h"
#include <assert.h>
#include <stdint.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
static void original_channels(void)
{
 MdsClanHomeStyle s;
 for(int f=0;f<4;f++){
  assert(mds_clan_home_style(f,100,100,&s));
  assert(s.offset_y==(f<2?2:3));
  assert(s.color_rgb555==0xffff);
  assert(s.alpha==255&&s.shadow_alpha==255);
  assert(mds_clan_home_style(f,101,100,&s));
  assert(s.alpha>=127&&s.alpha<=128);
  assert(s.shadow_alpha>=127&&s.shadow_alpha<=128);
  assert(mds_clan_home_style(f,102,100,&s));
  assert(s.offset_y==0&&s.alpha==0&&s.shadow_alpha==0);
  assert(!mds_clan_home_style(f,103,100,&s));
  assert(s.alpha==0&&s.offset_y==0);
 }
 assert(!mds_clan_home_style(-1,100,100,&s));
 assert(!mds_clan_home_style(4,100,100,&s));
 assert(!mds_clan_home_style(0,100,100,NULL));
 assert(mds_clan_home_style(0,0,UINT32_MAX,&s));
 assert(s.alpha>=127&&s.alpha<=128);
 assert(!mds_clan_home_style(0,3,UINT32_MAX,&s));
}
static void compositing(void)
{
 assert(mds_clan_rgb555_mix(0x8000,0xffff,0)==0x8000);
 assert(mds_clan_rgb555_mix(0x8000,0xffff,255)==0xffff);
 assert(mds_clan_rgb555_mix(0x8000,0xffff,256)==0xffff);
 assert(mds_clan_rgb555_mix(0x0000,0x7fff,128)==0x4210);
 enum {W=12,H=9};
 uint16_t guarded[W*H+2];guarded[0]=0x1234;guarded[W*H+1]=0x5678;
 uint16_t *image=guarded+1;
 for(int i=0;i<W*H;i++)image[i]=0x8000;
 mds_clan_border_tint(image,W,H,2,2,6,5,0xffff,255);
 assert(image[2*W+2]==0xffff);
 assert(image[4*W+4]==0x8000);
 assert(image[6*W+7]==0xffff);
 mds_clan_border_shadow(image,W,H,2,2,6,5,255);
 assert(image[7*W+3]!=0x8000);
 assert(image[3*W+8]!=0x8000);
 for(int i=0;i<100;i++){
  mds_clan_border_tint(image,W,H,-500+i,3,1000,3,0xffff,128);
  mds_clan_border_shadow(image,W,H,1000+i,-9,5,1000,255);
 }
 mds_clan_border_tint(image,W,H,INT_MIN,INT_MAX,INT_MAX,INT_MAX,0xffff,255);
 mds_clan_border_shadow(image,W,H,INT_MAX,INT_MAX,INT_MAX,INT_MAX,255);
 assert(guarded[0]==0x1234&&guarded[W*H+1]==0x5678);
 uint16_t copy[W*H];memcpy(copy,image,sizeof copy);
 mds_clan_border_tint(image,W,H,0,0,W,H,0xffff,0);
 mds_clan_border_shadow(image,W,H,0,0,W,H,0);
 assert(!memcmp(copy,image,sizeof copy));
}
int main(void)
{
 original_channels();compositing();
 puts("PASS: original CLAN color/alpha, VBlank wrap, clipped RGB555 borders");
 return 0;
}
