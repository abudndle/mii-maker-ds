#ifndef MDS_CLAN_ADJUST_H
#define MDS_CLAN_ADJUST_H
#include <stdint.h>
enum { MDS_CLAN_ADJUST_CHANGE=1, MDS_CLAN_ADJUST_ARROW=2 };
typedef struct {
 uint32_t started;
 int x,y,w,h;
 uint8_t active,painted,kind,category;
} MdsClanAdjust;
typedef struct {
 int offset_y;
 uint16_t tint_rgb555;
} MdsClanAdjustStyle;
/* Play original per-widget Decide keyframes on the reconstructed editor.
 * The 3DS clip keeps neutral values after its keyed press. */
void mds_clan_adjust_begin(MdsClanAdjust *,uint32_t now,unsigned kind,
                           unsigned category,int x,int y,int w,int h);
void mds_clan_adjust_reset(MdsClanAdjust *);
int mds_clan_adjust_tick(MdsClanAdjust *,uint32_t now);
int mds_clan_adjust_style(MdsClanAdjust *,uint32_t now,MdsClanAdjustStyle *);
#endif
