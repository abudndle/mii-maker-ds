#include "gallery_nav_clan.h"
#include "gallery_nav_clan_generated.h"
#include "clan_curve.h"
#include <stddef.h>
#include <string.h>

#define COUNT(a) (sizeof(a)/sizeof((a)[0]))
#define Q16_FRAME_PER_VBLANK 32768
#define VISIBLE_TICKS 3u /* source frames zero, half and one */

static int32_t eval(const MdsClanKey *keys,size_t count,uint32_t elapsed)
{
    return mds_clan_curve_eval(keys,count,
                              (int32_t)(elapsed*Q16_FRAME_PER_VBLANK));
}
static int source_pixels_to_ds(int32_t q16)
{
    /* 320x240 -> 256x192: exact rational 4/5, rounded away from zero
     * at half pixels. Inputs are the verified +/-3 source-unit tracks. */
    int64_t scaled=(int64_t)q16*4;
    int64_t divisor=5LL*65536LL;
    if(scaled>=0)return (int)((scaled+divisor/2)/divisor);
    return (int)(-((-scaled+divisor/2)/divisor));
}
static unsigned alpha8(int32_t q16)
{
    if(q16<=0)return 0;
    if(q16>=255*65536)return 255;
    return (unsigned)(((int64_t)q16+32768)/65536);
}
static uint16_t color(int32_t r,int32_t g,int32_t b)
{
    unsigned red=alpha8(r),green=alpha8(g),blue=alpha8(b);
    return (uint16_t)(0x8000u|(red>>3)|((green>>3)<<5)|((blue>>3)<<10));
}
void mds_gallery_nav_clan_reset(MdsGalleryNavClan *state)
{
    if(state)memset(state,0,sizeof(*state));
}
void mds_gallery_nav_clan_navigate(MdsGalleryNavClan *state,
                                   int direction,uint32_t now)
{
    if(!state||(direction!=-1&&direction!=1))return;
    state->navigation_started=now;
    state->navigation_direction=direction;
}
void mds_gallery_nav_clan_confirm(MdsGalleryNavClan *state,uint32_t now)
{
    if(!state)return;
    state->confirm_started=now;
    state->confirm_valid=1;
}
void mds_gallery_nav_clan_invalid(MdsGalleryNavClan *state,int direction)
{
    if(!state||(direction!=-1&&direction!=1))return;
    /* EDITSelectBase_Invalid is 11 source frames but its P_ArrowL/R
     * CLPA X tracks are single constant-zero values. Record the action;
     * do not manufacture an unsupported bounce animation. */
    if(mds_clan_curve_eval(gallery_nav_invalid_arrow_x,
                          COUNT(gallery_nav_invalid_arrow_x),0)==0)
        state->invalid_edges++;
}
int mds_gallery_nav_clan_active(const MdsGalleryNavClan *state,uint32_t now)
{
    if(!state)return 0;
    int navigation=state->navigation_direction!=0&&
        (uint32_t)(now-state->navigation_started)<VISIBLE_TICKS;
    int confirm=state->confirm_valid&&
        (uint32_t)(now-state->confirm_started)<VISIBLE_TICKS;
    return navigation||confirm;
}
int mds_gallery_nav_clan_style(const MdsGalleryNavClan *state,
                               uint32_t now,MdsGalleryNavStyle *out)
{
    if(!out)return 0;
    out->left_arrow_dx=0;out->right_arrow_dx=0;
    out->shadow_alpha=200;
    out->confirm_tint=0xffffu;
    out->confirm_visible=0;out->navigation_visible=0;
    if(!state)return 0;
    if(state->navigation_direction){
        uint32_t elapsed=(uint32_t)(now-state->navigation_started);
        int visible=elapsed<VISIBLE_TICKS;
        /* Persist the endpoint of the source scroll after its last
         * keyframe instead of snapping both arrows back arbitrarily. */
        if(!visible)elapsed=2u;
        const MdsClanKey *left,*right,*shadow;
        if(state->navigation_direction==-1){
            left=gallery_nav_left_l_x;
            right=gallery_nav_left_r_x;
            shadow=gallery_nav_left_shadow_alpha;
        }else{
            left=gallery_nav_right_l_x;
            right=gallery_nav_right_r_x;
            shadow=gallery_nav_right_shadow_alpha;
        }
        out->left_arrow_dx=source_pixels_to_ds(eval(left,2,elapsed));
        out->right_arrow_dx=source_pixels_to_ds(eval(right,2,elapsed));
        out->shadow_alpha=alpha8(eval(shadow,2,elapsed));
        out->navigation_visible=visible;
    }
    if(state->confirm_valid){
        uint32_t elapsed=(uint32_t)(now-state->confirm_started);
        if(elapsed<VISIBLE_TICKS){
            out->confirm_tint=color(
                eval(gallery_confirm_red,COUNT(gallery_confirm_red),elapsed),
                eval(gallery_confirm_green,COUNT(gallery_confirm_green),elapsed),
                eval(gallery_confirm_blue,COUNT(gallery_confirm_blue),elapsed));
            out->confirm_visible=1;
        }
    }
    return out->navigation_visible||out->confirm_visible;
}
