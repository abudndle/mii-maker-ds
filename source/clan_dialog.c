#include "clan_dialog.h"
#include "clan_curve.h"
#include "clan_dialog_generated.h"
#include <string.h>
int mds_clan_dialog_active(uint32_t now,uint32_t started)
{
 return (uint32_t)(now-started)<MDS_CLAN_DIALOG_VBLANKS;
}
int mds_clan_dialog_y(uint32_t now,uint32_t started)
{
 uint32_t elapsed=(uint32_t)(now-started);
 if(elapsed>=MDS_CLAN_DIALOG_VBLANKS)return 0;
 int32_t frame=(int32_t)(elapsed*32768u);
 int32_t source=mds_clan_curve_eval(dialog_in_y,
   sizeof dialog_in_y/sizeof dialog_in_y[0],frame);
 /* Scale 240px 3DS pane coordinates to 192px DS bottom display. */
 int64_t scaled=(int64_t)source*192;
 int64_t divisor=240LL*65536;
 int64_t pixels=scaled<0?-((-scaled+divisor/2)/divisor):
                          (scaled+divisor/2)/divisor;
 if(pixels>192)pixels=192;
 if(pixels< -192)pixels= -192;
 return (int)pixels;
}
void mds_clan_dialog_translate(uint16_t *screen,int offset,uint16_t background)
{
 if(!screen||offset==0)return;
 if(offset>192)offset=192;
 if(offset< -192)offset= -192;
 if(offset<0){
  unsigned lines=(unsigned)(-offset),keep=192u-lines;
  memmove(screen,screen+lines*256u,keep*256u*sizeof *screen);
  for(unsigned i=keep*256u;i<192u*256u;i++)screen[i]=background;
 }else{
  unsigned lines=(unsigned)offset,keep=192u-lines;
  memmove(screen+lines*256u,screen,keep*256u*sizeof *screen);
  for(unsigned i=0;i<lines*256u;i++)screen[i]=background;
 }
}
