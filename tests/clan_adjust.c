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
 assert(fx.active&&fx.phase==MDS_CLAN_ADJUST_RELEASE);
 assert(mds_clan_adjust_style(&fx,109,&style));
 assert(style.offset_y==0&&style.tint_rgb555==(uint16_t)(0x8000u|(175u>>3)|((229u>>3)<<5)|((178u>>3)<<10)));
 assert(mds_clan_adjust_tick(&fx,113));
 assert(!fx.active);
 assert(!mds_clan_adjust_tick(&fx,114));
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
 assert(fx.phase==MDS_CLAN_ADJUST_RELEASE&&fx.active);
 assert(mds_clan_adjust_style(&fx,209,&cue));
 assert(cue.tint_rgb555==(uint16_t)(0x8000u|(150u>>3)|((200u>>3)<<5)|((172u>>3)<<10)));
 assert(mds_clan_adjust_style(&fx,211,&cue));
 assert(cue.tint_rgb555==0xffff);
 assert(mds_clan_adjust_tick(&fx,213));
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
 assert(fx.active&&fx.phase==MDS_CLAN_ADJUST_RELEASE);
 assert(mds_clan_adjust_style(&fx,6,&cue));
 assert(mds_clan_adjust_tick(&fx,10));
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
static void explicit_release(void)
{
 MdsClanAdjust fx={0};
 MdsClanAdjustStyle cue;
 mds_clan_adjust_begin(&fx,100,MDS_CLAN_ADJUST_ARROW,4,134,2,29,19);
 assert(mds_clan_adjust_style(&fx,100,&cue));
 mds_clan_adjust_release(&fx,101);
 assert(fx.phase==MDS_CLAN_ADJUST_RELEASE&&!fx.painted);
 assert(mds_clan_adjust_style(&fx,101,&cue));
 assert(cue.tint_rgb555==(uint16_t)(0x8000u|(150u>>3)|((200u>>3)<<5)|((172u>>3)<<10)));
 assert(mds_clan_adjust_style(&fx,103,&cue));
 assert(cue.tint_rgb555==0xffff);
 mds_clan_adjust_release(&fx,104); /* Repeated release is ignored. */
 assert(fx.started==101);
 assert(mds_clan_adjust_tick(&fx,105));
 assert(!fx.active);
 mds_clan_adjust_release(&fx,106);
 assert(!fx.active);
}
static void invalid_feedback(void)
{
 MdsClanAdjust fx={0};
 MdsClanAdjustStyle cue;
 mds_clan_adjust_invalid(&fx,10,MDS_CLAN_ADJUST_CHANGE,4,194,22,30,22);
 assert(fx.active&&fx.phase==MDS_CLAN_ADJUST_INVALID);
 assert(mds_clan_adjust_style(&fx,11,&cue));
 assert(cue.offset_y==0);
 assert(cue.opacity==80);
 assert(cue.tint_rgb555==(uint16_t)(0x8000u|(228u>>3)|((230u>>3)<<5)|((228u>>3)<<10)));
 mds_clan_adjust_release(&fx,12);
 assert(fx.phase==MDS_CLAN_ADJUST_INVALID);
 assert(mds_clan_adjust_tick(&fx,31));
 assert(!fx.active);
 mds_clan_adjust_invalid(&fx,UINT32_MAX-1,MDS_CLAN_ADJUST_ARROW,5,0,0,20,20);
 assert(mds_clan_adjust_style(&fx,UINT32_MAX-1,&cue));
 assert(cue.tint_rgb555==0xffff);
 assert(cue.opacity==80);
 assert(mds_clan_adjust_tick(&fx,19));
 assert(!fx.active);
 mds_clan_adjust_invalid(&fx,0,0,0,0,0,1,1);
 assert(!fx.active);
 mds_clan_adjust_invalid(NULL,0,MDS_CLAN_ADJUST_ARROW,0,0,0,1,1);
}
int main(void)
{
 change_press();arrow_press();wrap_and_guards();
 explicit_release();invalid_feedback();
 puts("PASS: original editor Decide/UnDecide/Invalid, release, rollover and validation");
 return 0;
}
