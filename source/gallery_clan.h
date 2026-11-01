#ifndef MDS_GALLERY_CLAN_H
#define MDS_GALLERY_CLAN_H
#include <stdint.h>
/* Portable original 3DS BCLAN numeric selection/room-tab curves. 2 DS
 * VBlanks per original CLAN frame is provisional until measured on hardware. */
typedef struct {
    unsigned page,selected,previous_page;
    uint32_t started;
    uint8_t initialized,active,page_changed;
} MdsGalleryClan;
typedef struct {
    uint32_t scale_x_q16,scale_y_q16;
    uint16_t selected_room_tint,previous_room_tint;
    unsigned previous_page;
    int room_transition;
} MdsGalleryClanStyle;
void mds_gallery_clan_reset(MdsGalleryClan *state);
int mds_gallery_clan_update(MdsGalleryClan *state,unsigned page,unsigned selected,uint32_t now);
int mds_gallery_clan_active(const MdsGalleryClan *state,uint32_t now);
int mds_gallery_clan_style(const MdsGalleryClan *state,uint32_t now,MdsGalleryClanStyle *out);
#endif
