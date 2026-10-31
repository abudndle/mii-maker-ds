#include "clan_editor.h"
#include "clan_curve.h"
#include "clan_editor_generated.h"
#include <stddef.h>
#define COUNT(a) (sizeof(a)/sizeof((a)[0]))
unsigned mds_clan_editor_tab(unsigned category)
{
 static const uint8_t map[13]={0,0,0,1,3,2,4,5,6,6,6,6,7};
 return category<COUNT(map)?map[category]:8;
}
void mds_clan_editor_begin(MdsClanEditorAnim *a,uint32_t now,
                           unsigned category,unsigned part,int changed)
{
 if(!a)return;
 a->started=now;a->category=category;a->selected=part;
 a->tab=mds_clan_editor_tab(category);
 a->tab_changed=changed!=0;
 a->duration=(category<=2||category==10)?MDS_CLAN_EDITOR_PART_TICKS:6u;
 if(a->tab_changed&&a->duration<MDS_CLAN_EDITOR_TAB_TICKS)a->duration=MDS_CLAN_EDITOR_TAB_TICKS;
 a->active=1;a->painted=0;
}
int mds_clan_editor_tick(MdsClanEditorAnim *a,uint32_t now)
{
 if(!a||!a->active)return 0;
 if(!a->painted)return 1;
 if((uint32_t)(now-a->started)>=a->duration){
  a->active=0;
  return 1;
 }
 return 1;
}
static int color(const MdsClanKey *a,size_t n,int32_t frame)
{
 int32_t value=mds_clan_curve_eval(a,n,frame);
 if(value<=0)return 0;
 if(value>=255*65536)return 255;
 return (value+32768)/65536;
}
int mds_clan_editor_style(MdsClanEditorAnim *a,uint32_t now,MdsClanEditorStyle *out)
{
 if(!out)return 0;
 out->part_scale_q16=65536;
 out->tab_pane_rgb555=0x8000;
 out->tab_icon_rgb555=0x8000;
 out->tab_active=0;
 if(!a||!a->active)return 0;
 if(!a->painted){a->started=now;a->painted=1;}
 uint32_t elapsed=(uint32_t)(now-a->started);
 if(elapsed>=a->duration)return 0;
 int32_t frame=(int32_t)(elapsed*32768u);
 const MdsClanKey *scale=(a->category<=2||a->category==10)?editor_part_110:editor_part_108;
 size_t count=(a->category<=2||a->category==10)?COUNT(editor_part_110):COUNT(editor_part_108);
 out->part_scale_q16=mds_clan_curve_eval(scale,count,frame);
 if(a->tab_changed&&elapsed<MDS_CLAN_EDITOR_TAB_TICKS){
  int r=color(editor_pane_r,COUNT(editor_pane_r),frame),g=color(editor_pane_g,COUNT(editor_pane_g),frame),b=color(editor_pane_b,COUNT(editor_pane_b),frame);
  out->tab_pane_rgb555=(uint16_t)(0x8000u|(r>>3)|((g>>3)<<5)|((b>>3)<<10));
  r=color(editor_icon_r,COUNT(editor_icon_r),frame);
  g=color(editor_icon_g,COUNT(editor_icon_g),frame);
  b=color(editor_icon_b,COUNT(editor_icon_b),frame);
  out->tab_icon_rgb555=(uint16_t)(0x8000u|(r>>3)|((g>>3)<<5)|((b>>3)<<10));
  out->tab_active=1;
 }
 return 1;
}
