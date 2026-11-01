#ifndef MDS_GALLERY_BALLOON_CLAN_H
#define MDS_GALLERY_BALLOON_CLAN_H
#include <stdint.h>
typedef struct {uint32_t started;uint8_t active;} MdsGalleryBalloonClan;
typedef struct {
    uint32_t favorite_scale_q16;
    unsigned balloon_alpha,favorite_alpha;
    int32_t touch_offset_y_q16;
} MdsGalleryBalloonStyle;
void mds_gallery_balloon_clan_reset(MdsGalleryBalloonClan *state);
void mds_gallery_balloon_clan_select(MdsGalleryBalloonClan *state,uint32_t now);
int mds_gallery_balloon_clan_active(const MdsGalleryBalloonClan *state,uint32_t now);
int mds_gallery_balloon_clan_style(const MdsGalleryBalloonClan *state,uint32_t now,MdsGalleryBalloonStyle *out);
#endif
