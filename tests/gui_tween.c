#include "gui_tween.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
int main(void){MdsGuiTween t={0};mds_gui_tween_start(&t,100,10,0,100);assert(mds_gui_tween_value(&t,105)==50);assert(mds_gui_tween_value(&t,110)==100);assert(mds_gui_tween_done(&t,110));mds_gui_tween_start(&t,UINT32_MAX-1,6,-100,100);assert(mds_gui_tween_value(&t,1)==0);assert(mds_gui_tween_value(&t,4)==100);mds_gui_tween_start(&t,20,0,1,5);assert(mds_gui_tween_value(&t,20)==5);puts("PASS: GUI interpolation");return 0;}
