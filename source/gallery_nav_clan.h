#ifndef MDS_GALLERY_NAV_CLAN_H
#define MDS_GALLERY_NAV_CLAN_H
#include <stdint.h>
/* 3DS EDITSelectBase scroll and SelectMii confirmation. Timed at the
 * provisional 2 DS VBlank ticks per source frame used by other CLAN ports. */
typedef struct {
    uint32_t navigation_started,confirm_started;
    int navigation_direction; /* -1 = ScrollL, 1 = ScrollR, 0 = not started */
    int confirm_valid;
    unsigned invalid_edges; /* diagnostic only: Invalid source has no motion */
} MdsGalleryNavClan;
typedef struct {
    int left_arrow_dx,right_arrow_dx; /* source CLPA x converted 320 -> 256 */
    unsigned shadow_alpha;           /* original CLVC, 0..200 */
    uint16_t confirm_tint;           /* original SelectMii CLMC RGB */
    int confirm_visible;
    int navigation_visible;          /* a source-keyframed nav update */
} MdsGalleryNavStyle;
void mds_gallery_nav_clan_reset(MdsGalleryNavClan *state);
void mds_gallery_nav_clan_navigate(MdsGalleryNavClan *state,int direction,uint32_t now);
void mds_gallery_nav_clan_confirm(MdsGalleryNavClan *state,uint32_t now);
void mds_gallery_nav_clan_invalid(MdsGalleryNavClan *state,int direction);
int mds_gallery_nav_clan_active(const MdsGalleryNavClan *state,uint32_t now);
int mds_gallery_nav_clan_style(const MdsGalleryNavClan *state,uint32_t now,MdsGalleryNavStyle *out);
#endif
