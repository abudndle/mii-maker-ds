#include "clan_editor.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
static void mappings(void)
{
 const unsigned expected[]={0,0,0,1,3,2,4,5,6,6,6,6,7};
 for(unsigned i=0;i<13;i++)assert(mds_clan_editor_tab(i)==expected[i]);
 assert(mds_clan_editor_tab(13)==8);
}
static void timeline(void)
{
 MdsClanEditorAnim a={0};MdsClanEditorStyle s;
 mds_clan_editor_begin(&a,100,3,5,1);
 assert(mds_clan_editor_tick(&a,100));
 assert(mds_clan_editor_style(&a,100,&s));
 assert(s.tab_active&&s.part_scale_q16==65536);
 assert(s.tab_icon_rgb555==(0x8000u|(18u>>3)|((50u>>3)<<5)|((25u>>3)<<10)));
 assert(s.tab_pane_rgb555==(0x8000u|(220u>>3)|((255u>>3)<<5)|((230u>>3)<<10)));
 assert(mds_clan_editor_style(&a,101,&s));
 assert(s.part_scale_q16>65536&&s.tab_active);
 assert(mds_clan_editor_style(&a,102,&s));
 assert(s.part_scale_q16>=70778&&s.part_scale_q16<=70780&&!s.tab_active);
 assert(mds_clan_editor_style(&a,104,&s));
 assert(s.part_scale_q16>65536);
 assert(mds_clan_editor_tick(&a,106));
 assert(!a.active);
 assert(!mds_clan_editor_tick(&a,107));
 mds_clan_editor_begin(&a,1000,0,1,1);
 assert(mds_clan_editor_style(&a,1000,&s));
 assert(mds_clan_editor_style(&a,1002,&s));
 assert(s.part_scale_q16>=72089&&s.part_scale_q16<=72091);
 assert(mds_clan_editor_style(&a,1008,&s));
 assert(s.part_scale_q16>=72089&&s.part_scale_q16<=72091);
 assert(mds_clan_editor_tick(&a,1010));
 assert(!a.active);
}
static void wrap_and_reset(void)
{
 MdsClanEditorAnim a={0};MdsClanEditorStyle s;
 assert(!mds_clan_editor_tick(NULL,0));
 assert(!mds_clan_editor_style(NULL,0,&s));
 assert(!mds_clan_editor_style(&a,0,NULL));
 mds_clan_editor_begin(&a,UINT32_MAX-1,12,0,1);
 assert(mds_clan_editor_style(&a,UINT32_MAX-1,&s));
 assert(mds_clan_editor_style(&a,0,&s));
 assert(mds_clan_editor_tick(&a,4));
 assert(!a.active);
 assert(!mds_clan_editor_tick(&a,5));
 mds_clan_editor_begin(&a,1,4,2,0);
 assert(mds_clan_editor_style(&a,1,&s)&&!s.tab_active);
 assert(s.part_scale_q16==65536);
 mds_clan_editor_begin(NULL,1,4,2,0);
}
int main(void)
{
 mappings();timeline();wrap_and_reset();
 puts("PASS: original editor tab RGB, selected-thumbnail scale, category mapping, VBlank wrap");
 return 0;
}
