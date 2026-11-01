#ifndef MDS_ORIGINAL_GALLERY_ART_H
#define MDS_ORIGINAL_GALLERY_ART_H
#include <stdint.h>
/* Optional artwork recovered from the user's original Mii Maker 3DS RomFS.
 * These routines never generate or embed Nintendo assets, and failure to
 * locate a private NitroFS file leaves the existing background intact.
 * The canvas and clipped blitter are portable, so host tests need no DS SDK.
 */
int mds_original_gallery_box_base(uint16_t *canvas,int width,int height,
                                  int x,int y,int w,int h);
int mds_original_gallery_box_border(uint16_t *canvas,int width,int height,
                                    int x,int y,int w,int h);
int mds_original_gallery_room_tab(uint16_t *canvas,int width,int height,
                                  int x,int y,int w,int h,int selected);
/* CLMC tint is a per-channel source color multiplier, not a fabricated overlay. */
int mds_original_gallery_room_tab_tinted(uint16_t *canvas,int width,int height,
                                         int x,int y,int w,int h,int selected,uint16_t tint);
#endif
