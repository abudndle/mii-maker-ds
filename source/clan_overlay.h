#ifndef MDS_CLAN_OVERLAY_H
#define MDS_CLAN_OVERLAY_H
#include <stdint.h>
/* Clip-safe compositing into a DS RGB555 frame, with no heap/NDK calls.
 * Tint changes only two-pixel border; shadow changes outside right/bottom. */
uint16_t mds_clan_rgb555_mix(uint16_t base,uint16_t tint,unsigned opacity);
void mds_clan_border_tint(uint16_t *frame,int width,int height,int x,int y,int w,int h,
                          uint16_t tint,unsigned opacity);
void mds_clan_border_shadow(uint16_t *frame,int width,int height,int x,int y,int w,int h,
                            unsigned opacity);
#endif
