#include "gui_tween.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
static void test_timing(void)
{
 MdsGuiTween t={0};
 mds_gui_tween_start(&t,100,10,0,100);
 assert(mds_gui_tween_value(&t,100)==0);
 assert(mds_gui_tween_value(&t,105)==50);
 assert(mds_gui_tween_value(&t,110)==100);
 assert(!mds_gui_tween_done(&t,109));
 assert(mds_gui_tween_done(&t,110));
 mds_gui_tween_start(&t,20,4,100,0);
 assert(mds_gui_tween_value(&t,22)==50);
 mds_gui_tween_start(&t,UINT32_MAX-1,6,-100,100);
 assert(mds_gui_tween_value(&t,1)==0);
 assert(mds_gui_tween_value(&t,4)==100);
 mds_gui_tween_start(&t,20,0,1,5);
 assert(mds_gui_tween_value(&t,20)==5);
 assert(mds_gui_tween_done(&t,20));
 mds_gui_tween_start(&t,0,65535,-32768,32767);
 assert(mds_gui_tween_value(&t,0)==-32768);
 assert(mds_gui_tween_value(&t,65535)==32767);
 assert(mds_gui_tween_done(NULL,0));
 assert(mds_gui_tween_value(NULL,0)==0);
}
static void test_rgb555(void)
{
 assert(mds_gui_fade_rgb555(0xffff,0)==0x8000);
 assert(mds_gui_fade_rgb555(0xffff,16)==0xffff);
 assert(mds_gui_fade_rgb555(0xffff,17)==0xffff);
 assert(mds_gui_fade_rgb555(0x7fff,8)==0x3def);
 assert(mds_gui_fade_rgb555(0x8000,8)==0x8000);
 for(unsigned channel=0;channel<3;channel++)
  for(unsigned value=0;value<32;value++){
   uint16_t color=(uint16_t)(0x8000u|(value<<(channel*5)));
   unsigned previous=0;
   for(unsigned light=0;light<=20;light++){
    uint16_t result=mds_gui_fade_rgb555(color,light);
    unsigned component=(result>>(channel*5))&31;
    unsigned expected=value*(light>16?16:light)/16;
    assert(component==expected);
    assert(component>=previous);
    assert((result&0x8000u)!=0);
    assert((result&~(uint16_t)(0x8000u|(31u<<(channel*5))))==0);
    previous=component;
   }
  }
}
int main(void)
{
 test_timing();test_rgb555();
 puts("PASS: GUI interpolation, wrap, and exhaustive RGB555 channels");
 return 0;
}
