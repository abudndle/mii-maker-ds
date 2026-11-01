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
int mds_original_gallery_box_border_tinted(uint16_t *canvas,int width,int height,
                                           int x,int y,int w,int h,uint16_t tint);
/* Source Select.arc BtnScrollShadow.bclim, 16x16 original texture.
 * Apply the actual ScrollL/ScrollR CLVC shadow alpha (0..200) by
 * per-channel RGB555 interpolation against the existing backdrop.
 * Missing or malformed private NitroFS art must leave pixels unchanged. */
int mds_original_gallery_arrow_shadow(uint16_t *canvas,int width,int height,
                                      int x,int y,int w,int h,unsigned alpha);
int mds_original_gallery_room_tab(uint16_t *canvas,int width,int height,
                                  int x,int y,int w,int h,int selected);
/* CLMC tint is a per-channel source color multiplier, not a fabricated overlay. */
int mds_original_gallery_room_tab_tinted(uint16_t *canvas,int width,int height,
                                         int x,int y,int w,int h,int selected,uint16_t tint);
/* Action 1=Favorite/Personal, 2=Copy, 3=Edit/Open.
 * Missing private original art returns 0 without modifying the framebuffer. */
int mds_original_gallery_action_icon(uint16_t *canvas,int width,int height,
                                     int x,int y,int w,int h,
                                     int action,int personal);
#endif
