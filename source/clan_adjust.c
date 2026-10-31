#include "clan_adjust.h"
#include "clan_adjust_generated.h"
#include "clan_curve.h"
#include <stddef.h>
#define COUNT(a) (sizeof(a)/sizeof(a[0]))
static unsigned duration(const MdsClanAdjust *fx)
{
 if(fx->phase==MDS_CLAN_ADJUST_INVALID)return 20u; /* 11-frame source clip */
 if(fx->phase==MDS_CLAN_ADJUST_RELEASE)return 4u;
 return fx->kind==MDS_CLAN_ADJUST_ARROW?4u:8u;
}
void mds_clan_adjust_reset(MdsClanAdjust *fx)
{
 if(fx)fx->active=0;
}
void mds_clan_adjust_begin(MdsClanAdjust *fx,uint32_t now,unsigned kind,
                           unsigned category,int x,int y,int w,int h)
{
 if(!fx)return;
 fx->active=0;
 if((kind!=MDS_CLAN_ADJUST_CHANGE&&kind!=MDS_CLAN_ADJUST_ARROW)||
    w<=0||h<=0||category>=13u)return;
 fx->started=now;
 fx->x=x;fx->y=y;fx->w=w;fx->h=h;
 fx->kind=(uint8_t)kind;
 fx->category=(uint8_t)category;
 fx->active=1;fx->painted=0;fx->phase=MDS_CLAN_ADJUST_PRESS;
}
void mds_clan_adjust_release(MdsClanAdjust *fx,uint32_t now)
{
 if(!fx||!fx->active||fx->phase!=MDS_CLAN_ADJUST_PRESS)return;
 fx->started=now;fx->painted=0;fx->phase=MDS_CLAN_ADJUST_RELEASE;
}
void mds_clan_adjust_invalid(MdsClanAdjust *fx,uint32_t now,unsigned kind,
                             unsigned category,int x,int y,int w,int h)
{
 mds_clan_adjust_begin(fx,now,kind,category,x,y,w,h);
 if(fx&&fx->active)fx->phase=MDS_CLAN_ADJUST_INVALID;
}
int mds_clan_adjust_tick(MdsClanAdjust *fx,uint32_t now)
{
 if(!fx||!fx->active)return 0;
 if(!fx->painted)return 1;
 if((uint32_t)(now-fx->started)>=duration(fx)){
  if(fx->phase==MDS_CLAN_ADJUST_PRESS)
   mds_clan_adjust_release(fx,now);
  else fx->active=0;
  return 1; /* Advance phase or restore original bitmap on completion. */
 }
 return 1;
}
static unsigned value8(const MdsClanKey *keys,size_t count,int32_t frame)
{
 int32_t v=mds_clan_curve_eval(keys,count,frame);
 if(v<=0)return 0;
 if(v>=255*65536)return 255;
 return (unsigned)((v+32768)/65536);
}
int mds_clan_adjust_style(MdsClanAdjust *fx,uint32_t now,MdsClanAdjustStyle *out)
{
 if(!out)return 0;
 out->offset_y=0;out->tint_rgb555=0x8000u;out->opacity=255;
 if(!fx||!fx->active)return 0;
 if(!fx->painted){fx->started=now;fx->painted=1;}
 uint32_t elapsed=(uint32_t)(now-fx->started);
 if(elapsed>=duration(fx))return 0;
 int32_t frame=(int32_t)(elapsed*32768u);
 const MdsClanKey *y=adjust_change_y,*r=adjust_change_r,*g=adjust_change_g,*b=adjust_change_b;
 size_t yn=COUNT(adjust_change_y),rn=COUNT(adjust_change_r),gn=COUNT(adjust_change_g),bn=COUNT(adjust_change_b);
 if(fx->kind==MDS_CLAN_ADJUST_ARROW){
  y=(fx->category==4)?adjust_arrow_y:adjust_arrow_hair_y;
  yn=fx->category==4?COUNT(adjust_arrow_y):COUNT(adjust_arrow_hair_y);
  r=adjust_arrow_r;g=adjust_arrow_g;b=adjust_arrow_b;
  rn=COUNT(adjust_arrow_r);gn=COUNT(adjust_arrow_g);bn=COUNT(adjust_arrow_b);
 }
 if(fx->phase==MDS_CLAN_ADJUST_RELEASE){
  y=adjust_release_y;yn=COUNT(adjust_release_y);
  if(fx->kind==MDS_CLAN_ADJUST_ARROW){
   r=adjust_release_arrow_r;g=adjust_release_arrow_g;b=adjust_release_arrow_b;
   rn=COUNT(adjust_release_arrow_r);gn=COUNT(adjust_release_arrow_g);bn=COUNT(adjust_release_arrow_b);
  }else{
   r=adjust_release_change_r;g=adjust_release_change_g;b=adjust_release_change_b;
   rn=COUNT(adjust_release_change_r);gn=COUNT(adjust_release_change_g);bn=COUNT(adjust_release_change_b);
  }
 }else if(fx->phase==MDS_CLAN_ADJUST_INVALID){
  y=adjust_release_y;yn=COUNT(adjust_release_y);
  if(fx->kind==MDS_CLAN_ADJUST_ARROW){
   r=adjust_invalid_arrow;g=adjust_invalid_arrow;b=adjust_invalid_arrow;
   rn=gn=bn=COUNT(adjust_invalid_arrow);
  }else{
   r=adjust_invalid_change_r;g=adjust_invalid_change_g;b=adjust_invalid_change_b;
   rn=COUNT(adjust_invalid_change_r);gn=COUNT(adjust_invalid_change_g);bn=COUNT(adjust_invalid_change_b);
  }
  /* Invalid CLAN entries provide a held opacity value, not an
   * animated error fade. Use that source value with a DS hold. */
  out->opacity=(uint8_t)value8(adjust_invalid_alpha,COUNT(adjust_invalid_alpha),frame);
 }
 int64_t raw=mds_clan_curve_eval(y,yn,frame);
 int64_t scaled=raw*4,divisor=5*65536LL;
 out->offset_y=scaled<0?(int)(-((-scaled+divisor/2)/divisor)):
                             (int)((scaled+divisor/2)/divisor);
 unsigned cr=value8(r,rn,frame),cg=value8(g,gn,frame),cb=value8(b,bn,frame);
 out->tint_rgb555=(uint16_t)(0x8000u|(cr>>3)|((cg>>3)<<5)|((cb>>3)<<10));
 return 1;
}
