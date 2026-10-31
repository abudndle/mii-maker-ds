#ifndef MDS_CLAN_ADJUST_H
#define MDS_CLAN_ADJUST_H
#include <stdint.h>
enum { MDS_CLAN_ADJUST_CHANGE=1, MDS_CLAN_ADJUST_ARROW=2 };
enum { MDS_CLAN_ADJUST_PRESS=0, MDS_CLAN_ADJUST_RELEASE=1,
       MDS_CLAN_ADJUST_INVALID=2 };
typedef struct {
 uint32_t started;
 int x,y,w,h;
 uint8_t active,painted,kind,category,phase;
} MdsClanAdjust;
typedef struct {
 int offset_y;
 uint16_t tint_rgb555;
 uint8_t opacity;
} MdsClanAdjustStyle;
void mds_clan_adjust_begin(MdsClanAdjust *,uint32_t now,unsigned kind,
                           unsigned category,int x,int y,int w,int h);
/* Press release uses the original EditEye_UnDecide arrow material keys.
 * Invalid uses original EditEye_Invalid static colors and opacity; the
 * visible hold is a DS adaptation because these keys are not timed. */
void mds_clan_adjust_release(MdsClanAdjust *,uint32_t now);
void mds_clan_adjust_invalid(MdsClanAdjust *,uint32_t now,unsigned kind,
                             unsigned category,int x,int y,int w,int h);
void mds_clan_adjust_reset(MdsClanAdjust *);
int mds_clan_adjust_tick(MdsClanAdjust *,uint32_t now);
int mds_clan_adjust_style(MdsClanAdjust *,uint32_t now,MdsClanAdjustStyle *);
#endif
