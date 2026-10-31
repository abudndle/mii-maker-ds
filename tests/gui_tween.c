#include "gui_tween.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
int main(void){MdsGuiTween t={0};mds_gui_tween_start(&t,100,10,0,100);assert(mds_gui_tween_value(&t,105)==50);assert(mds_gui_tween_value(&t,110)==100);assert(mds_gui_tween_done(&t,110));mds_gui_tween_start(&t,UINT32_MAX-1,6,-100,100);assert(mds_gui_tween_value(&t,1)==0);assert(mds_gui_tween_value(&t,4)==100);mds_gui_tween_start(&t,20,0,1,5);assert(mds_gui_tween_value(&t,20)==5);assert(mds_gui_fade_rgb555(0xffff,0)==0x8000);assert(mds_gui_fade_rgb555(0xffff,16)==0xffff);assert(mds_gui_fade_rgb555(0xffff,17)==0xffff);assert(mds_gui_fade_rgb555(0x7fff,8)==0x3def);assert(mds_gui_fade_rgb555(0x8000,8)==0x8000);puts("PASS: GUI interpolation and fades");return 0;}
