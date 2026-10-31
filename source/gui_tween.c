#include "gui_tween.h"
#include <limits.h>
void mds_gui_tween_start(MdsGuiTween *t,uint32_t now,uint16_t duration,int16_t from,int16_t to){
 if(!t)return;
 t->started=now;t->duration=duration;t->from=from;t->to=to;t->active=1;
}
int mds_gui_tween_done(const MdsGuiTween *t,uint32_t now){
 return !t||!t->active||!t->duration||(uint32_t)(now-t->started)>=t->duration;
}
int16_t mds_gui_tween_value(const MdsGuiTween *t,uint32_t now){
 if(!t)return 0;
 if(!t->active)return t->to;
 if(!t->duration)return t->to;
 uint32_t elapsed=(uint32_t)(now-t->started);
 if(elapsed>=t->duration)return t->to;
 /* Signed difference is at most 65535; multiply by duration <=65535 in int64. */
 int64_t delta=(int64_t)t->to-t->from;
 int64_t scaled=delta*(int64_t)elapsed;
 int64_t offset=scaled/(int64_t)t->duration;
 int64_t value=(int64_t)t->from+offset;
 if(value>INT16_MAX)value=INT16_MAX;
 if(value<INT16_MIN)value=INT16_MIN;
 return (int16_t)value;
}

uint16_t mds_gui_fade_rgb555(uint16_t pixel,unsigned brightness)
{
 if(brightness>16)brightness=16;
 unsigned r=(pixel&31)*brightness/16;
 unsigned g=((pixel>>5)&31)*brightness/16;
 unsigned b=((pixel>>10)&31)*brightness/16;
 return (uint16_t)((pixel&0x8000u)|r|(g<<5)|(b<<10));
}
