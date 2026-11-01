#include "gallery_balloon_clan.h"
#include "clan_curve.h"
#include <stddef.h>

/* Original private Select.arc SelectBalloonButton_Select BCLAN numeric tracks.
 * No source BCLAN, images or other Nintendo payloads are embedded. The
 * provisional DS strip remains fixed until runtime pane anchoring is proven. */
#define Q(n) ((int32_t)((n)*65536))
#define N(a) (sizeof(a)/sizeof((a)[0]))
#define TICKS 22u
static const MdsClanKey balloon_alpha[]={{0,0,0},{Q(5),Q(255),0}};
static const MdsClanKey favorite_alpha[]={{0,0,0},{Q(6),Q(255),0}};
static const MdsClanKey favorite_scale[]={{0,Q(1),0},{Q(5),85197,0},
    {Q(6),85197,0},{Q(10),Q(1),0}};
static const MdsClanKey favorite_parent_scale[]={{0,Q(1),0},{Q(1),78643,0},
    {Q(4),78643,0},{Q(5),Q(1),0}};
static const MdsClanKey touch_y[]={{0,Q(37),-Q(1)},
    {Q(2),Q(35),-Q(1)},{Q(2),Q(35),Q(2)},
    {Q(3),Q(37),Q(2)},{Q(3),Q(37),43691}};

void mds_gallery_balloon_clan_reset(MdsGalleryBalloonClan *state)
{
    if(state){state->active=0;state->started=0;}
}
void mds_gallery_balloon_clan_select(MdsGalleryBalloonClan *state,uint32_t now)
{
    if(state){state->active=1;state->started=now;}
}
int mds_gallery_balloon_clan_active(const MdsGalleryBalloonClan *state,uint32_t now)
{
    return state&&state->active&&(uint32_t)(now-state->started)<TICKS;
}
static unsigned alpha8(const MdsClanKey *keys,size_t count,int32_t frame)
{
    int32_t v=mds_clan_curve_eval(keys,count,frame);
    if(v<=0)return 0;
    if(v>=Q(255))return 255;
    return (unsigned)((v+32768)/65536);
}
int mds_gallery_balloon_clan_style(const MdsGalleryBalloonClan *state,
                                    uint32_t now,MdsGalleryBalloonStyle *out)
{
    if(!out)return 0;
    out->favorite_scale_q16=65536u;
    out->balloon_alpha=255u;
    out->favorite_alpha=255u;
    out->touch_offset_y_q16=0;
    if(!mds_gallery_balloon_clan_active(state,now))return 0;
    int32_t frame=(int32_t)((uint32_t)(now-state->started)*32768u);
    int32_t icon=mds_clan_curve_eval(favorite_scale,N(favorite_scale),frame);
    int32_t parent=mds_clan_curve_eval(favorite_parent_scale,N(favorite_parent_scale),frame);
    int64_t combined=(int64_t)icon*parent/65536;
    if(combined>=65536&&combined<=102400)
        out->favorite_scale_q16=(uint32_t)combined;
    out->balloon_alpha=alpha8(balloon_alpha,N(balloon_alpha),frame);
    out->favorite_alpha=alpha8(favorite_alpha,N(favorite_alpha),frame);
    out->touch_offset_y_q16=mds_clan_curve_eval(touch_y,N(touch_y),frame)-Q(37);
    return 1;
}
