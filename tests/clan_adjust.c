#include "clan_adjust.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
static void change_press(void)
{
 MdsClanAdjust fx={0};
 MdsClanAdjustStyle style={0};
 assert(!mds_clan_adjust_tick(&fx,100));
 assert(!mds_clan_adjust_style(&fx,100,&style));
 assert(style.offset_y==0&&style.tint_rgb555==0x8000u);
 mds_clan_adjust_begin(&fx,100,MDS_CLAN_ADJUST_CHANGE,4,194,23,30,22);
 assert(fx.active&&!fx.painted);
 assert(mds_clan_adjust_tick(&fx,101));
 assert(mds_clan_adjust_style(&fx,101,&style));
 assert(fx.painted&&fx.started==101);
 assert(style.offset_y==0);
 assert(style.tint_rgb555==(uint16_t)(0x8000u|(175u>>3)|((229u>>3)<<5)|((178u>>3)<<10)));
 assert(mds_clan_adjust_style(&fx,103,&style));
 assert(style.offset_y==-2);
 assert(style.tint_rgb555==(uint16_t)(0x8000u|(75u>>3)|((151u>>3)<<5)|((78u>>3)<<10)));
 assert(mds_clan_adjust_style(&fx,107,&style));
 assert(style.offset_y==0);
 assert(mds_clan_adjust_tick(&fx,109));
 assert(!fx.active);
 assert(!mds_clan_adjust_tick(&fx,110));
}
static void arrow_press(void)
{
 MdsClanAdjust fx={0};
 MdsClanAdjustStyle cue;
 mds_clan_adjust_begin(&fx,200,MDS_CLAN_ADJUST_ARROW,4,134,2,29,19);
 assert(mds_clan_adjust_style(&fx,205,&cue));
 assert(fx.started==205&&cue.offset_y==-2);
 assert(cue.tint_rgb555==(uint16_t)(0x8000u|(150u>>3)|((200u>>3)<<5)|((172u>>3)<<10)));
 assert(mds_clan_adjust_style(&fx,207,&cue)&&cue.offset_y==0);
 assert(mds_clan_adjust_tick(&fx,209));
 assert(!fx.active);
 mds_clan_adjust_begin(&fx,300,MDS_CLAN_ADJUST_ARROW,3,42,2,29,19);
 assert(mds_clan_adjust_style(&fx,300,&cue)&&cue.offset_y==-2);
 assert(mds_clan_adjust_style(&fx,302,&cue)&&cue.offset_y==0);
}
static void wrap_and_guards(void)
{
 MdsClanAdjust fx={0};MdsClanAdjustStyle cue;
 mds_clan_adjust_begin(&fx,UINT32_MAX-1,MDS_CLAN_ADJUST_CHANGE,5,0,0,25,25);
 assert(mds_clan_adjust_style(&fx,UINT32_MAX-1,&cue));
 assert(mds_clan_adjust_style(&fx,1,&cue)&&cue.offset_y<=0);
 assert(mds_clan_adjust_tick(&fx,6));
 assert(!fx.active);
 mds_clan_adjust_begin(&fx,1,0,5,1,1,10,10);
 assert(!fx.active);
 mds_clan_adjust_begin(&fx,1,MDS_CLAN_ADJUST_ARROW,13,1,1,10,10);
 assert(!fx.active);
 mds_clan_adjust_begin(&fx,1,MDS_CLAN_ADJUST_ARROW,5,1,1,0,10);
 assert(!fx.active);
 mds_clan_adjust_begin(NULL,1,MDS_CLAN_ADJUST_ARROW,5,1,1,10,10);
 mds_clan_adjust_begin(&fx,1,MDS_CLAN_ADJUST_ARROW,5,1,1,10,10);
 assert(!mds_clan_adjust_style(&fx,1,NULL));
 mds_clan_adjust_reset(&fx);
 assert(!mds_clan_adjust_tick(&fx,1));
 mds_clan_adjust_reset(NULL);
}
int main(void)
{
 change_press();arrow_press();wrap_and_guards();
 puts("PASS: original arrow and adjustment CLAN tracks, first-paint timing, VBlank wrap and reset");
 return 0;
}
