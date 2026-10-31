#include "clan_home.h"
#include "clan_curve.h"
#include "clan_home_generated.h"
#include <stddef.h>
#define NKEYS(a) (sizeof(a)/sizeof((a)[0]))
static int channel8(const MdsClanKey *keys,size_t count,int32_t frame)
{
 int64_t scaled=mds_clan_curve_eval(keys,count,frame);
 if(scaled<=0)return 0;
 if(scaled>=255LL*65536)return 255;
 return (int)((scaled+32768)/65536);
}
int mds_clan_home_running(uint32_t now,uint32_t started)
{
 return (uint32_t)(now-started)<=2;
}
int mds_clan_home_offset(int focus,uint32_t now,uint32_t started)
{
 if(focus<0||focus>3||!mds_clan_home_running(now,started))return 0;
 const MdsClanKey *keys=home_y0;
 size_t count=NKEYS(home_y0);
 int32_t end=home_y0[NKEYS(home_y0)-1].value;
 if(focus==1){keys=home_y1;count=NKEYS(home_y1);end=home_y1[NKEYS(home_y1)-1].value;}
 if(focus==2){keys=home_y2;count=NKEYS(home_y2);end=home_y2[NKEYS(home_y2)-1].value;}
 if(focus==3){keys=home_y3;count=NKEYS(home_y3);end=home_y3[NKEYS(home_y3)-1].value;}
 int32_t value=mds_clan_curve_eval(keys,count,(int32_t)((uint32_t)(now-started)*32768u));
 int64_t diff=(int64_t)value-end;
 if(diff>=0)return (int)((diff+32768)/65536);
 return (int)(-((-diff+32768)/65536));
}
int mds_clan_home_style(int focus,uint32_t now,uint32_t started,MdsClanHomeStyle *out)
{
 if(!out)return 0;
 out->offset_y=0;out->color_rgb555=0x8000;out->alpha=0;out->shadow_alpha=0;
 if(focus<0||focus>3||!mds_clan_home_running(now,started))return 0;
 int32_t frame=(int32_t)((uint32_t)(now-started)*32768u);
 int r=channel8(home_red,NKEYS(home_red),frame);
 int g=channel8(home_green,NKEYS(home_green),frame);
 int b=channel8(home_blue,NKEYS(home_blue),frame);
 out->color_rgb555=(uint16_t)(0x8000u|(r>>3)|((g>>3)<<5)|((b>>3)<<10));
 out->alpha=(uint8_t)channel8(home_alpha,NKEYS(home_alpha),frame);
 out->shadow_alpha=(uint8_t)channel8(home_shadow,NKEYS(home_shadow),frame);
 out->offset_y=mds_clan_home_offset(focus,now,started);
 return 1;
}
