#include "gallery_balloon_clan.h"
#include "clan_curve.h"
#include <stddef.h>

/* Original private Select.arc SelectBalloonButton BCLAN numeric tracks.
 * No source BCLAN, images or other Nintendo payloads are embedded. The
 * provisional DS strip remains fixed until runtime pane anchoring is proven.
 * Unselect/Decide/UnDecide clip playback is ready but original scene event
 * bindings are not yet verified. */
#define Q(n) ((int32_t)((n)*65536))
#define N(a) (sizeof(a)/sizeof((a)[0]))
#define SELECT_TICKS 22u
#define SHORT_TICKS 12u
static const MdsClanKey balloon_alpha[]={{0,0,0},{Q(5),Q(255),0}};
static const MdsClanKey favorite_scale[]={{0,Q(1),0},{Q(5),85197,0},
    {Q(6),85197,0},{Q(10),Q(1),0}};
static const MdsClanKey favorite_parent_scale[]={{0,Q(1),0},{Q(1),78643,0},
    {Q(4),78643,0},{Q(5),Q(1),0}};
static const MdsClanKey touch_y[]={{0,Q(37),-Q(1)},
    {Q(2),Q(35),-Q(1)},{Q(2),Q(35),Q(2)},
    {Q(3),Q(37),Q(2)},{Q(3),Q(37),43691}};
/* Original Unselect fades I_Favorite and N_Balloon together. UnDecide
 * fades only I_Favorite; Decide holds I_Favorite at 255. */
static const MdsClanKey fade_out[]={{0,Q(255),0},{Q(5),0,0}};

static unsigned duration(const MdsGalleryBalloonClan *state)
{
    return state->clip==MDS_BALLOON_SELECT?SELECT_TICKS:SHORT_TICKS;
}

void mds_gallery_balloon_clan_reset(MdsGalleryBalloonClan *state)
{
    if(state){state->active=0;state->started=0;state->clip=MDS_BALLOON_SELECT;}
}
void mds_gallery_balloon_clan_play(MdsGalleryBalloonClan *state,
                                   MdsGalleryBalloonClip clip,uint32_t now)
{
    if(!state||clip<MDS_BALLOON_SELECT||clip>MDS_BALLOON_UNDECIDE)return;
    state->active=1;state->started=now;state->clip=(uint8_t)clip;
}
void mds_gallery_balloon_clan_select(MdsGalleryBalloonClan *state,uint32_t now)
{
    mds_gallery_balloon_clan_play(state,MDS_BALLOON_SELECT,now);
}
int mds_gallery_balloon_clan_active(const MdsGalleryBalloonClan *state,uint32_t now)
{
    return state&&state->active&&(uint32_t)(now-state->started)<duration(state);
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
    if(!mds_gallery_balloon_clan_active(state,now)){
        /* Non-looping clips hold their final source CLVC opacity until the
         * next clip starts; otherwise the icon flashes at clip completion. */
        if(state&&state->active&&
           (uint32_t)(now-state->started)>=duration(state)){
            if(state->clip==MDS_BALLOON_UNSELECT){
                out->balloon_alpha=0u;out->favorite_alpha=0u;
            }else if(state->clip==MDS_BALLOON_UNDECIDE){
                out->favorite_alpha=0u;
            }
        }
        return 0;
    }
    int32_t frame=(int32_t)((uint32_t)(now-state->started)*32768u);
    if(state->clip==MDS_BALLOON_UNSELECT){
        out->balloon_alpha=alpha8(fade_out,N(fade_out),frame);
        out->favorite_alpha=out->balloon_alpha;
        return 1;
    }
    if(state->clip==MDS_BALLOON_UNDECIDE){
        out->favorite_alpha=alpha8(fade_out,N(fade_out),frame);
        return 1;
    }
    if(state->clip==MDS_BALLOON_DECIDE)return 1;
    int32_t icon=mds_clan_curve_eval(favorite_scale,N(favorite_scale),frame);
    int32_t parent=mds_clan_curve_eval(favorite_parent_scale,N(favorite_parent_scale),frame);
    int64_t combined=(int64_t)icon*parent/65536;
    if(combined>=65536&&combined<=102400)
        out->favorite_scale_q16=(uint32_t)combined;
    out->balloon_alpha=alpha8(balloon_alpha,N(balloon_alpha),frame);
    /* Select contains no I_Favorite CLVC track; its alpha stays 255. */
    out->touch_offset_y_q16=mds_clan_curve_eval(touch_y,N(touch_y),frame)-Q(37);
    return 1;
}

int mds_gallery_balloon_clan_actions_visible(const MdsGalleryBalloonClan *state,uint32_t now)
{
    MdsGalleryBalloonStyle style;
    mds_gallery_balloon_clan_style(state,now,&style);
    /* Select/Unselect parent transparency gates the entire action strip.
     * UnDecide fades only I_Favorite; Copy/Edit must remain usable. */
    return style.balloon_alpha>0u;
}
