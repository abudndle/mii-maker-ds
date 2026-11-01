#ifndef MDS_GALLERY_BALLOON_CLAN_H
#define MDS_GALLERY_BALLOON_CLAN_H
#include <stdint.h>
/* Source SelectBalloonButton CLAN clips. Playback is independent of
 * unverified original scene event bindings and screen anchor. */
typedef enum {
    MDS_BALLOON_SELECT=0,
    MDS_BALLOON_UNSELECT=1,
    MDS_BALLOON_DECIDE=2,
    MDS_BALLOON_UNDECIDE=3
} MdsGalleryBalloonClip;
typedef struct {uint32_t started;uint8_t active,clip;} MdsGalleryBalloonClan;
typedef struct {
    uint32_t favorite_scale_q16;
    unsigned balloon_alpha,favorite_alpha;
    int32_t touch_offset_y_q16;
} MdsGalleryBalloonStyle;
void mds_gallery_balloon_clan_reset(MdsGalleryBalloonClan *state);
void mds_gallery_balloon_clan_select(MdsGalleryBalloonClan *state,uint32_t now);
/* Exact numeric CLVC playback; call sites for new clips need scene validation. */
void mds_gallery_balloon_clan_play(MdsGalleryBalloonClan *state,
                                   MdsGalleryBalloonClip clip,uint32_t now);
int mds_gallery_balloon_clan_active(const MdsGalleryBalloonClan *state,uint32_t now);
int mds_gallery_balloon_clan_style(const MdsGalleryBalloonClan *state,uint32_t now,MdsGalleryBalloonStyle *out);
/* Do not dispatch a touch command while its original balloon icon is invisible. */
int mds_gallery_balloon_clan_actions_visible(const MdsGalleryBalloonClan *state,uint32_t now);
#endif
